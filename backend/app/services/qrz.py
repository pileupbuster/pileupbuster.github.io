import os
from typing import Dict, Optional
from callsignlookuptools import QrzSyncClient


class QRZService:
    """Service for interacting with QRZ.com API using callsignlookuptools"""
    
    def __init__(self):
        self.username = os.getenv('QRZ_USERNAME')
        self.password = os.getenv('QRZ_PASSWORD')
        self.qrz_client = None
    
    def _authenticate(self) -> bool:
        """Authenticate with QRZ.com"""
        if not self.username or not self.password:
            return False
            
        try:
            self.qrz_client = QrzSyncClient(username=self.username, password=self.password)
            return True
        except Exception as e:
            print(f"QRZ authentication error: {e}")
            return False
    
    def lookup_callsign(self, callsign: str) -> Dict[str, Optional[str]]:
        """
        Look up callsign information from QRZ.com
        
        Returns:
            Dict with callsign info or error placeholder
        """
        # Default response for when QRZ lookup fails or user not found
        default_response = {
            'qrz_found': False,
            'name': None,
            'address': None,
            'bio': 'QRZ.com profile not found or unavailable',
            'email': None,
            'country': None,
            'grid': None,
            'license_class': None
        }
        
        # Check if QRZ credentials are configured
        if not self.username or not self.password:
            default_response['bio'] = 'QRZ.com integration not configured'
            return default_response
        
        # Authenticate if we don't have a client
        if not self.qrz_client and not self._authenticate():
            default_response['bio'] = 'QRZ.com authentication failed'
            return default_response
        
        try:
            # Lookup the callsign using callsignlookuptools
            result = self.qrz_client.search(callsign)
            
            # If no results found
            if not result:
                return default_response
            
            # Extract and format available fields
            qrz_info = {
                'qrz_found': True,
                'name': result.get('fname') or result.get('name'),
                'address': self._format_address(result),
                'bio': result.get('bio') or 'No biography available',
                'email': result.get('email'),
                'country': result.get('country'),
                'grid': result.get('grid'),
                'license_class': result.get('class')
            }
            
            return qrz_info
            
        except Exception as e:
            print(f"QRZ lookup error for {callsign}: {e}")
            default_response['bio'] = 'QRZ.com lookup failed'
            return default_response
    
    def _format_address(self, callsign_data) -> Optional[str]:
        """Format address from QRZ data"""
        addr = callsign_data.get('addr1')
        addr2 = callsign_data.get('addr2')
        state = callsign_data.get('state')
        zip_code = callsign_data.get('zip')
        
        parts = []
        if addr:
            parts.append(addr)
        if addr2:
            parts.append(addr2)
        if state:
            parts.append(state)
        if zip_code:
            parts.append(zip_code)
            
        return ', '.join(parts) if parts else None


# Global instance
qrz_service = QRZService()