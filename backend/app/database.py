"""Database module for MongoDB operations"""
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)


class QueueDatabase:
    """MongoDB database operations for queue management"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.collection: Optional[Collection] = None
        self.status_collection: Optional[Collection] = None
        self.currentqso_collection: Optional[Collection] = None
        self._connect()
    
    def _connect(self):
        """Initialize MongoDB connection"""
        try:
            mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/pileup_buster')
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            # Extract database name from URI or use default
            if 'pileup_buster' in mongo_uri:
                db_name = 'pileup_buster'
            else:
                db_name = 'pileup_buster'
            
            self.db = self.client[db_name]
            self.collection = self.db.queue
            self.status_collection = self.db.status
            self.currentqso_collection = self.db.currentqso
            
            # Test connection with short timeout
            self.client.admin.command('ping')
            
        except PyMongoError as e:
            print(f"MongoDB connection error: {e}")
            print("Note: In production, ensure MongoDB is accessible via MONGO_URI environment variable")
            # For development/demo, fall back to None and let individual operations handle it
            self.client = None
            self.db = None
            self.collection = None
            self.status_collection = None
            self.currentqso_collection = None
    
    def register_callsign(self, callsign: str, qrz_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Register a callsign in the queue with optional QRZ information"""
        if self.collection is None:
            raise Exception("Database connection not available")
        
        # Check if system is active
        if not self.is_system_active():
            raise ValueError("System is currently inactive. Registration is not available.")
        
        # Check if callsign already exists
        existing = self.collection.find_one({"callsign": callsign})
        if existing:
            raise ValueError("Callsign already in queue")
        
        # Get current queue count and check against limit
        current_count = self.collection.count_documents({})
        max_queue_size = int(os.getenv('MAX_QUEUE_SIZE', '4'))
        
        if current_count >= max_queue_size:
            raise ValueError(f"Queue is full. Maximum queue size is {max_queue_size}")
        
        # Get current position (count + 1)
        position = current_count + 1
        
        # Create entry with QRZ information
        entry = {
            'callsign': callsign,
            'timestamp': datetime.utcnow().isoformat(),
            'position': position,
            'qrz': qrz_info or {
                'callsign': callsign,
                'name': None,
                'address': None,
                'dxcc_name': None,
                'image': None,
                'error': 'QRZ information not available'
            }
        }
        
        # Insert into database
        self.collection.insert_one(entry)
        # Remove MongoDB ObjectId from response
        if '_id' in entry:
            del entry['_id']
        
        return entry
    
    def find_callsign(self, callsign: str) -> Optional[Dict[str, Any]]:
        """Find a callsign in the queue and return with updated position"""
        if self.collection is None:
            raise Exception("Database connection not available")
        
        # Find the entry
        entry = self.collection.find_one({"callsign": callsign})
        if not entry:
            return None
        
        # Calculate current position based on timestamp order
        position = self.collection.count_documents({
            "timestamp": {"$lt": entry["timestamp"]}
        }) + 1
        
        # Update position in the returned entry (but not in database)
        entry['position'] = position
        if '_id' in entry:
            del entry['_id']  # Remove MongoDB ObjectId from response
            
        return entry
    
    def get_queue_list(self) -> List[Dict[str, Any]]:
        """Get the complete queue list with updated positions"""
        if self.collection is None:
            raise Exception("Database connection not available")
        
        # Get all entries sorted by timestamp (FIFO order)
        entries = list(self.collection.find({}).sort("timestamp", 1))
        
        # Update positions and remove MongoDB ObjectIds
        queue_list = []
        for i, entry in enumerate(entries):
            entry['position'] = i + 1
            if '_id' in entry:
                del entry['_id']
            queue_list.append(entry)
        
        return queue_list
    
    def get_queue_list_with_time(self) -> List[Dict[str, Any]]:
        """Get the complete queue list with updated positions and time_in_queue"""
        queue_list = self.get_queue_list()
        
        # Add time_in_queue for each entry
        for entry in queue_list:
            if 'timestamp' in entry:
                try:
                    # Parse the timestamp
                    if isinstance(entry['timestamp'], str):
                        entry_time = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                    else:
                        entry_time = entry['timestamp']
                    
                    # Calculate time in queue (seconds)
                    time_in_queue = (datetime.now(entry_time.tzinfo) - entry_time).total_seconds()
                    entry['time_in_queue'] = round(time_in_queue, 1)
                except Exception as e:
                    logger.warning(f"Could not calculate time_in_queue for {entry.get('callsign', 'unknown')}: {e}")
                    entry['time_in_queue'] = 0.0
            else:
                entry['time_in_queue'] = 0.0
        
        return queue_list
    
    def remove_callsign(self, callsign: str) -> Optional[Dict[str, Any]]:
        """Remove a callsign from the queue"""
        if self.collection is None:
            raise Exception("Database connection not available")
        
        # Find and remove the entry
        entry = self.collection.find_one_and_delete({"callsign": callsign})
        if entry and '_id' in entry:
            del entry['_id']
        
        return entry
    
    def clear_queue(self) -> int:
        """Clear the entire queue and return count of removed entries"""
        if self.collection is None:
            raise Exception("Database connection not available")
        
        count = self.collection.count_documents({})
        self.collection.delete_many({})
        return count
    
    def get_next_callsign(self) -> Optional[Dict[str, Any]]:
        """Get and remove the next callsign in queue (FIFO)"""
        if self.collection is None:
            raise Exception("Database connection not available")
        
        # Find and remove the oldest entry (by timestamp)
        entry = self.collection.find_one_and_delete(
            {},
            sort=[("timestamp", 1)]
        )
        
        if entry and '_id' in entry:
            del entry['_id']
        
        return entry
    
    def get_queue_count(self) -> int:
        """Get the total count of entries in queue"""
        if self.collection is None:
            return 0
        
        return self.collection.count_documents({})
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get the current system status (active/inactive)"""
        if self.status_collection is None:
            raise Exception("Database connection not available")
        
        # Try to find existing status document
        status_doc = self.status_collection.find_one({"_id": "system_status"})
        
        if not status_doc:
            # If no status document exists, create one with default inactive state
            default_status = {
                "_id": "system_status",
                "active": False,
                "last_updated": datetime.utcnow().isoformat(),
                "updated_by": "system"
            }
            self.status_collection.insert_one(default_status)
            return {
                "active": False,
                "last_updated": default_status["last_updated"],
                "updated_by": "system"
            }
        
        # Remove MongoDB ObjectId from response
        result = {
            "active": status_doc.get("active", False),
            "last_updated": status_doc.get("last_updated"),
            "updated_by": status_doc.get("updated_by")
        }
        
        return result
    
    def set_system_status(self, active: bool, updated_by: str = "admin") -> Dict[str, Any]:
        """Set the system status (active/inactive) and clear queue when changing status"""
        if self.status_collection is None:
            raise Exception("Database connection not available")
        
        # Clear the queue whenever the system status changes (activate or deactivate)
        cleared_count = self.clear_queue()
        
        # Also clear any current QSO when changing system status
        cleared_qso = self.clear_current_qso()
        qso_cleared = cleared_qso is not None
        
        # Update or create status document
        status_update = {
            "_id": "system_status",
            "active": active,
            "last_updated": datetime.utcnow().isoformat(),
            "updated_by": updated_by
        }
        
        self.status_collection.replace_one(
            {"_id": "system_status"},
            status_update,
            upsert=True
        )
        
        result = {
            "active": active,
            "last_updated": status_update["last_updated"],
            "updated_by": updated_by,
            "queue_cleared": True,
            "cleared_count": cleared_count,
            "qso_cleared": qso_cleared
        }
        
        return result
    
    def get_current_qso(self) -> Optional[Dict[str, Any]]:
        """Get the current callsign in QSO"""
        if self.currentqso_collection is None:
            raise Exception("Database connection not available")
        
        # Find the current QSO entry (should be only one)
        entry = self.currentqso_collection.find_one({"_id": "current_qso"})
        if not entry:
            return None
        
        # Debug logging to see what's in the database
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 DATABASE DEBUG: Raw entry from DB: {entry}")
        
        # Remove MongoDB ObjectId from response
        result = {
            "callsign": entry.get("callsign"),
            "timestamp": entry.get("timestamp"),
            "qrz": entry.get("qrz", {
                'callsign': entry.get("callsign"),
                'name': None,
                'address': None,
                'dxcc_name': None,
                'image': None,
                'error': 'QRZ information not available'
            }),
            "metadata": entry.get("metadata", {})
        }
        
        logger.info(f"🔍 DATABASE DEBUG: Returning result: {result}")
        
        return result
    
    def set_current_qso(self, callsign: str, qrz_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Set the current callsign in QSO with QRZ information"""
        if self.currentqso_collection is None:
            raise Exception("Database connection not available")
        
        # Create QSO entry with QRZ information
        qso_entry = {
            "_id": "current_qso",
            "callsign": callsign,
            "timestamp": datetime.utcnow().isoformat(),
            "qrz": qrz_info or {
                'callsign': callsign,
                'name': None,
                'address': None,
                'dxcc_name': None,
                'image': None,
                'error': 'QRZ information not available'
            }
        }
        
        # Use replace_one with upsert to ensure only one QSO entry exists
        self.currentqso_collection.replace_one(
            {"_id": "current_qso"},
            qso_entry,
            upsert=True
        )
        
        return {
            "callsign": callsign,
            "timestamp": qso_entry["timestamp"],
            "qrz": qso_entry["qrz"]
        }
    
    def set_current_qso_with_metadata(self, callsign: str, qrz_info: Dict[str, Any] = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Set the current callsign in QSO with QRZ information and bridge metadata"""
        if self.currentqso_collection is None:
            raise Exception("Database connection not available")
        
        # Create enhanced QSO entry with metadata
        qso_entry = {
            "_id": "current_qso",
            "callsign": callsign,
            "timestamp": datetime.utcnow().isoformat(),
            "qrz": qrz_info or {
                'callsign': callsign,
                'name': None,
                'address': None,
                'dxcc_name': None,
                'image': None,
                'error': 'QRZ information not available'
            },
            "metadata": metadata or {}
        }
        
        # Use replace_one with upsert to ensure only one QSO entry exists
        self.currentqso_collection.replace_one(
            {"_id": "current_qso"},
            qso_entry,
            upsert=True
        )
        
        return {
            "callsign": callsign,
            "timestamp": qso_entry["timestamp"],
            "qrz": qso_entry["qrz"],
            "metadata": qso_entry["metadata"]
        }
    
    def clear_current_qso(self) -> Optional[Dict[str, Any]]:
        """Clear the current QSO"""
        if self.currentqso_collection is None:
            raise Exception("Database connection not available")
        
        # Find and delete the current QSO entry
        entry = self.currentqso_collection.find_one_and_delete({"_id": "current_qso"})
        if not entry:
            return None
        
        return {
            "callsign": entry.get("callsign"),
            "timestamp": entry.get("timestamp"),
            "metadata": entry.get("metadata", {}),  # Include metadata to check source
            "qrz": entry.get("qrz", {
                'callsign': entry.get("callsign"),
                'name': None,
                'address': None,
                'dxcc_name': None,
                'image': None,
                'error': 'QRZ information not available'
            })
        }
    
    def get_frequency(self) -> Optional[Dict[str, Any]]:
        """Get the current transmission frequency"""
        if self.status_collection is None:
            raise Exception("Database connection not available")
        
        # Find the frequency document
        freq_doc = self.status_collection.find_one({"_id": "frequency"})
        
        if not freq_doc:
            return None
        
        return {
            "frequency": freq_doc.get("frequency"),
            "last_updated": freq_doc.get("last_updated"),
            "updated_by": freq_doc.get("updated_by")
        }
    
    def set_frequency(self, frequency: str, updated_by: str = "admin") -> Dict[str, Any]:
        """Set the current transmission frequency"""
        if self.status_collection is None:
            raise Exception("Database connection not available")
        
        # Create frequency document
        freq_update = {
            "_id": "frequency",
            "frequency": frequency,
            "last_updated": datetime.utcnow().isoformat(),
            "updated_by": updated_by
        }
        
        # Update or create frequency document
        self.status_collection.replace_one(
            {"_id": "frequency"},
            freq_update,
            upsert=True
        )
        
        return {
            "frequency": frequency,
            "last_updated": freq_update["last_updated"],
            "updated_by": updated_by
        }
    
    def clear_frequency(self, updated_by: str = "admin") -> Dict[str, Any]:
        """Clear the current transmission frequency"""
        if self.status_collection is None:
            raise Exception("Database connection not available")
        
        # Remove frequency document
        result = self.status_collection.delete_one({"_id": "frequency"})
        
        return {
            "frequency": None,
            "last_updated": datetime.utcnow().isoformat(),
            "updated_by": updated_by,
            "cleared": result.deleted_count > 0
        }
    
    def is_system_active(self) -> bool:
        """Check if the system is currently active"""
        try:
            status = self.get_system_status()
            return status.get("active", False)
        except Exception:
            # If we can't check status, default to inactive for safety
            return False

    def get_split(self) -> Optional[Dict[str, Any]]:
        """Get the current split value"""
        if self.status_collection is None:
            raise Exception("Database connection not available")
        
        # Find the split document
        split_doc = self.status_collection.find_one({"_id": "split"})
        
        if not split_doc:
            return None
        
        return {
            "split": split_doc.get("split"),
            "last_updated": split_doc.get("last_updated"),
            "updated_by": split_doc.get("updated_by")
        }
    
    def set_split(self, split: str, updated_by: str = "admin") -> Dict[str, Any]:
        """Set the current split value"""
        if self.status_collection is None:
            raise Exception("Database connection not available")
        
        # Create split document
        split_update = {
            "_id": "split",
            "split": split,
            "last_updated": datetime.utcnow().isoformat(),
            "updated_by": updated_by
        }
        
        # Update or create split document
        self.status_collection.replace_one(
            {"_id": "split"},
            split_update,
            upsert=True
        )
        
        return {
            "split": split,
            "last_updated": split_update["last_updated"],
            "updated_by": updated_by
        }

    def clear_split(self, updated_by: str = "admin") -> Dict[str, Any]:
        """Clear the current split value"""
        if self.status_collection is None:
            raise Exception("Database connection not available")
        
        # Delete the split document
        self.status_collection.delete_one({"_id": "split"})
        
        return {
            "split": None,
            "last_updated": datetime.utcnow().isoformat(),
            "updated_by": updated_by
        }

    def get_logger_integration(self) -> Dict[str, Any]:
        """Get the logger integration settings"""
        if self.status_collection is None:
            raise Exception("Database connection not available")
        
        # Find the logger integration document
        logger_doc = self.status_collection.find_one({"_id": "logger_integration"})
        
        if not logger_doc:
            return {
                "enabled": False,
                "last_updated": None,
                "updated_by": None
            }
        
        return {
            "enabled": logger_doc.get("enabled", False),
            "last_updated": logger_doc.get("last_updated"),
            "updated_by": logger_doc.get("updated_by")
        }

    def set_logger_integration(self, enabled: bool, updated_by: str = "admin") -> Dict[str, Any]:
        """Set the logger integration status"""
        if self.status_collection is None:
            raise Exception("Database connection not available")
        
        # Create logger integration document
        logger_update = {
            "_id": "logger_integration",
            "enabled": enabled,
            "last_updated": datetime.utcnow().isoformat(),
            "updated_by": updated_by
        }
        
        # Update or create logger integration document
        self.status_collection.replace_one(
            {"_id": "logger_integration"},
            logger_update,
            upsert=True
        )
        
        return {
            "enabled": enabled,
            "last_updated": logger_update["last_updated"],
            "updated_by": updated_by
        }


# Global database instance
queue_db = QueueDatabase()