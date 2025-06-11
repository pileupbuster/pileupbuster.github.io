"""Database module for MongoDB operations"""
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError


class QueueDatabase:
    """MongoDB database operations for queue management"""

    def __init__(self):
        self.client = None
        self.db = None
        self.collection: Optional[Collection] = None
        self._connect()

    def _connect(self):
        """Initialize MongoDB connection"""
        try:
            mongo_uri = os.getenv(
                "MONGO_URI", "mongodb://localhost:27017/pileup_buster"
            )
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            # Extract database name from URI or use default
            if "pileup_buster" in mongo_uri:
                db_name = "pileup_buster"
            else:
                db_name = "pileup_buster"

            self.db = self.client[db_name]
            self.collection = self.db.queue

            # Test connection with short timeout
            self.client.admin.command("ping")

        except PyMongoError as e:
            print(f"MongoDB connection error: {e}")
            print(
                "Note: In production, ensure MongoDB is accessible "
                "via MONGO_URI environment variable"
            )
            # For development/demo, fall back to None and let individual
            # operations handle it
            self.client = None
            self.db = None
            self.collection = None

    def register_callsign(self, callsign: str) -> Dict[str, Any]:
        """Register a callsign in the queue"""
        if self.collection is None:
            raise Exception("Database connection not available")

        # Check if callsign already exists
        existing = self.collection.find_one({"callsign": callsign})
        if existing:
            raise ValueError("Callsign already in queue")

        # Get current queue count and check against limit
        current_count = self.collection.count_documents({})
        max_queue_size = int(os.getenv("MAX_QUEUE_SIZE", "4"))

        if current_count >= max_queue_size:
            raise ValueError(
                "Queue is full. Maximum queue size is " + str(max_queue_size)
            )

        # Get current position (count + 1)
        position = current_count + 1

        # Create entry
        entry = {
            "callsign": callsign,
            "timestamp": datetime.utcnow().isoformat(),
            "position": position,
        }

        # Insert into database
        self.collection.insert_one(entry)
        # Remove MongoDB ObjectId from response
        if "_id" in entry:
            del entry["_id"]

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
        position = (
            self.collection.count_documents({"timestamp": {"$lt": entry["timestamp"]}})
            + 1
        )

        # Update position in the returned entry (but not in database)
        entry["position"] = position
        if "_id" in entry:
            del entry["_id"]  # Remove MongoDB ObjectId from response

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
            entry["position"] = i + 1
            if "_id" in entry:
                del entry["_id"]
            queue_list.append(entry)

        return queue_list

    def remove_callsign(self, callsign: str) -> Optional[Dict[str, Any]]:
        """Remove a callsign from the queue"""
        if self.collection is None:
            raise Exception("Database connection not available")

        # Find and remove the entry
        entry = self.collection.find_one_and_delete({"callsign": callsign})
        if entry and "_id" in entry:
            del entry["_id"]

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
        entry = self.collection.find_one_and_delete({}, sort=[("timestamp", 1)])

        if entry and "_id" in entry:
            del entry["_id"]

        return entry

    def get_queue_count(self) -> int:
        """Get the total count of entries in queue"""
        if self.collection is None:
            return 0

        return self.collection.count_documents({})


# Global database instance
queue_db = QueueDatabase()
