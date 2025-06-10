import os
import httpx
import xml.etree.ElementTree as ET
from typing import Dict, Optional


class QRZService:
    """Service for interacting with QRZ.com XML API"""
    
    def __init__(self):
        self.username = os.getenv('QRZ_USERNAME')
        self.password = os.getenv('QRZ_PASSWORD')
        self.base_url = "https://xmldata.qrz.com/xml/1.34/"
        self.session_key = None
    
    def _authenticate(self) -> bool:
        """Authenticate with QRZ.com and get session key"""
        if not self.username or not self.password:
            return False
            
        try:
            params = {
                'username': self.username,
                'password': self.password
            }
            
            response = httpx.get(self.base_url, params=params, timeout=10.0)
            response.raise_for_status()
            
            root = ET.fromstring(response.text)
            session_element = root.find('.//Key')
            
            if session_element is not None:
                self.session_key = session_element.text
                return True
                
            return False
            
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
        
        # Authenticate if we don't have a session key
        if not self.session_key and not self._authenticate():
            default_response['bio'] = 'QRZ.com authentication failed'
            return default_response
        
        try:
            params = {
                's': self.session_key,
                'callsign': callsign.upper()
            }
            
            response = httpx.get(self.base_url, params=params, timeout=10.0)
            response.raise_for_status()
            
            root = ET.fromstring(response.text)
            
            # Check for errors
            error_element = root.find('.//Error')
            if error_element is not None:
                error_msg = error_element.text
                if 'not found' in error_msg.lower():
                    return default_response
                else:
                    default_response['bio'] = f'QRZ.com error: {error_msg}'
                    return default_response
            
            # Parse callsign data
            callsign_data = root.find('.//Callsign')
            if callsign_data is None:
                return default_response
            
            # Extract available fields
            qrz_info = {
                'qrz_found': True,
                'name': self._get_element_text(callsign_data, 'fname') or self._get_element_text(callsign_data, 'name'),
                'address': self._format_address(callsign_data),
                'bio': self._get_element_text(callsign_data, 'bio') or 'No biography available',
                'email': self._get_element_text(callsign_data, 'email'),
                'country': self._get_element_text(callsign_data, 'country'),
                'grid': self._get_element_text(callsign_data, 'grid'),
                'license_class': self._get_element_text(callsign_data, 'class')
            }
            
            return qrz_info
            
        except httpx.TimeoutException:
            default_response['bio'] = 'QRZ.com request timed out'
            return default_response
        except Exception as e:
            print(f"QRZ lookup error for {callsign}: {e}")
            default_response['bio'] = 'QRZ.com lookup failed'
            return default_response
    
    def _get_element_text(self, parent, tag: str) -> Optional[str]:
        """Safely get text from XML element"""
        element = parent.find(tag)
        return element.text if element is not None and element.text else None
    
    def _format_address(self, callsign_data) -> Optional[str]:
        """Format address from QRZ data"""
        addr = self._get_element_text(callsign_data, 'addr1')
        addr2 = self._get_element_text(callsign_data, 'addr2')
        state = self._get_element_text(callsign_data, 'state')
        zip_code = self._get_element_text(callsign_data, 'zip')
        
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