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
        
        try:
        
            # Check if QRZ credentials are configured if not throw an error
            if not self.username or not self.password:
                raise Exception(
                    'QRZ.com credentials not configured. Please set QRZ_USERNAME and QRZ_PASSWORD environment variables.'
                )
                
            
            # Authenticate if we don't have a client
            if not self.qrz_client and not self._authenticate():
                    raise Exception(
                        'QRZ.com authentication failed. Please check your credentials.'
                    )

            # Lookup the callsign using callsignlookuptools       
            result = self.qrz_client.search(callsign)
            
            # If no results found
            if not result:
                raise Exception(f'No QRZ.com profile found for callsign {callsign}')

            # Extract grid/coordinates information
            grid_info = self._extract_grid_info(result)

            response = {
                'callsign': callsign,
                'name': result.name.formatted_name,
                'address': self._format_address(result.address),
                'dxcc_name': result.dxcc.name if hasattr(result, 'dxcc') and result.dxcc else None,
                'image': result.image.url if hasattr(result, 'image') and result.image else None,
                'grid': grid_info,
                'error': None
            }
            return response
            
        except Exception as e:
            print(f"QRZ lookup error for {callsign}: {e}")
            return {
                'callsign': callsign,
                'name': None,
                'address': None,
                'dxcc_name': None,
                'grid': {
                    'lat': None,
                    'long': None,
                    'grid': None
                },
                'error': str(e)
            }
    
    def _extract_grid_info(self, result) -> Dict[str, Optional[str]]:
        """Extract grid and coordinate information from QRZ result"""
        grid_info = {
            'lat': None,
            'long': None,
            'grid': None
        }
        
        try:
            # Extract grid square (Maidenhead locator)
            if hasattr(result, 'grid') and result.grid:
                # Handle Grid object or string
                if hasattr(result.grid, 'grid'):
                    # It's a Grid object, extract the grid string
                    grid_info['grid'] = str(result.grid.grid)
                else:
                    # It's already a string
                    grid_info['grid'] = str(result.grid)
            
            # Extract latitude and longitude
            if hasattr(result, 'latlong') and result.latlong:
                if hasattr(result.latlong, 'lat') and result.latlong.lat is not None:
                    grid_info['lat'] = float(result.latlong.lat)
                if hasattr(result.latlong, 'long') and result.latlong.long is not None:
                    grid_info['long'] = float(result.latlong.long)
                    
        except (ValueError, TypeError, AttributeError) as e:
            print(f"Warning: Could not extract grid info: {e}")
            
        return grid_info

    def _format_address(self, address) -> Optional[str]:
        """Format address from QRZ data"""
        addr = address.line1
        addr2 = address.line2
        state = address.state
        city = address.city
        country = address.country
        zip_code = address.zip

        parts = []
        if addr:
            parts.append(addr)
        if addr2:
            parts.append(addr2)
        if city:
            parts.append(city)
        if country:
            parts.append(country)
        if state:
            parts.append(state)
        if zip_code:
            parts.append(zip_code)
            
        return ', '.join(parts) if parts else None


# Global instance
qrz_service = QRZService()