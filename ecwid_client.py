"""
Ecwid API Client - DEBUG VERSION
Shows raw API response structure
"""

import requests
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class EcwidClient:
    """Client for Ecwid REST API"""
    
    BASE_URL = 'https://app.ecwid.com/api/v3'
    
    def __init__(self, store_id: str, api_token: str):
        """
        Initialize Ecwid client
        
        Args:
            store_id: Ecwid store ID
            api_token: Ecwid API token
        """
        self.store_id = store_id
        self.api_token = api_token
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict:
        """Make HTTP request to Ecwid API"""
        url = f'{self.BASE_URL}/{self.store_id}{endpoint}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data, params=params, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, headers=self.headers, json=data, params=params, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ecwid API request failed: {str(e)}")
            raise
    
    def get_orders(
        self,
        hours: int = 24,
        limit: int = 100,
        offset: int = 0,
        status: str = 'AWAITING_PROCESSING'
    ) -> List[Dict]:
        """
        Get orders from Ecwid
        """
        from_date = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        params = {
            'limit': limit,
            'offset': offset,
            'updatedFrom': from_date
        }
        
        if status:
            params['statuses'] = status
        
        logger.info(f"Fetching orders from Ecwid (status={status}, hours={hours})")
        
        response = self._make_request('GET', '/orders', params=params)
        
        orders = response.get('items', [])
        total = response.get('total', 0)
        
        logger.info(f"Fetched {len(orders)} orders out of {total}")
        
        if len(orders) < total:
            remaining_orders = self.get_orders(
                hours=hours,
                limit=limit,
                offset=offset + limit,
                status=status
            )
            orders.extend(remaining_orders)
        
        return orders
    
    def get_order(self, order_id: int) -> Dict:
        """Get specific order details"""
        logger.info(f"Fetching order {order_id} from Ecwid")
        order = self._make_request('GET', f'/orders/{order_id}')
        
        # DEBUG: Log the full order structure
        logger.info(f"DEBUG - Raw Ecwid order {order_id} response: {json.dumps(order, indent=2)}")
        
        return order
    
    def update_order_status(self, order_id: int, status: str) -> Dict:
        """Update order status in Ecwid"""
        logger.info(f"Updating order {order_id} status to {status}")
        return self._make_request(
            'PUT',
            f'/orders/{order_id}',
            data={'orderStatus': status}
        )
    
    def add_order_comment(self, order_id: int, comment: str) -> Dict:
        """Add comment to order"""
        logger.info(f"Adding comment to order {order_id}")
        return self._make_request(
            'POST',
            f'/orders/{order_id}/comments',
            data={'text': comment}
        )
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            response = self._make_request('GET', '/profile')
            logger.info("Ecwid API connection successful")
            return True
        except Exception as e:
            logger.error(f"Ecwid API connection failed: {str(e)}")
            return False
