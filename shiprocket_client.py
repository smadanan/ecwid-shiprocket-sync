"""
Shiprocket API Client
Handles communication with Shiprocket REST API
"""

import requests
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ShiprocketClient:
    """Client for Shiprocket REST API"""
    
    BASE_URL = 'https://apiv2.shiprocket.in/v1/external'
    AUTH_URL = 'https://apiv2.shiprocket.in/v1/users/login'
    
    def __init__(self, email: str, password: str):
        """
        Initialize Shiprocket client
        
        Args:
            email: Shiprocket account email
            password: Shiprocket account password
        """
        self.email = email
        self.password = password
        self.token = None
        self.authenticate()
    
    def authenticate(self) -> bool:
        """Authenticate and get API token"""
        try:
            logger.info("Authenticating with Shiprocket...")
            response = requests.post(
                self.AUTH_URL,
                json={'email': self.email, 'password': self.password},
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            self.token = data.get('token')
            
            if self.token:
                logger.info("Shiprocket authentication successful")
                return True
            else:
                logger.error("Failed to get authentication token from Shiprocket")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Shiprocket authentication failed: {str(e)}")
            return False
    
    @property
    def headers(self) -> Dict:
        """Get request headers with authorization"""
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """Make HTTP request to Shiprocket API"""
        url = f'{self.BASE_URL}{endpoint}'
        
        try:
            if method == 'GET':
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=30
                )
            elif method == 'POST':
                response = requests.post(
                    url,
                    headers=self.headers,
                    json=data,
                    params=params,
                    timeout=30
                )
            elif method == 'PUT':
                response = requests.put(
                    url,
                    headers=self.headers,
                    json=data,
                    params=params,
                    timeout=30
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Shiprocket API request failed: {str(e)}")
            try:
                error_data = response.json()
                return {
                    'success': False,
                    'message': error_data.get('message', str(e)),
                    'errors': error_data.get('errors', {})
                }
            except:
                return {
                    'success': False,
                    'message': str(e)
                }
    
    def create_order(self, order_data: Dict) -> Dict:
        """
        Create new order in Shiprocket
        
        Args:
            order_data: Order details in Shiprocket format
        
        Returns:
            Response from Shiprocket API
        """
        logger.info(f"Creating order {order_data.get('order_id')} in Shiprocket")
        
        response = self._make_request(
            'POST',
            '/orders/create/adhoc',
            data=order_data
        )
        
        if response.get('success'):
            logger.info(f"Order created successfully. Shiprocket Order ID: {response.get('order_id')}")
        else:
            logger.warning(f"Order creation failed: {response.get('message')}")
        
        return response
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            logger.info("Testing Shiprocket connection...")
            # Try a simple endpoint that should work
            response = self._make_request('GET', '/settings/company/profile')
            
            if response.get('success'):
                logger.info("Shiprocket API connection successful")
                return True
            elif response.get('errors'):
                logger.error(f"Shiprocket API error: {response.get('errors')}")
                return False
            else:
                # If we get data back without 'success' key, it's still working
                if response and not response.get('message', '').startswith('failed'):
                    logger.info("Shiprocket API connection successful")
                    return True
                logger.error("Shiprocket API connection failed")
                return False
        except Exception as e:
            logger.error(f"Shiprocket API connection error: {str(e)}")
            return False
