#!/usr/bin/env python3
"""
Ecwid to Shiprocket Integration Tool
Pulls orders from Ecwid and mass uploads to Shiprocket
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import argparse
from dotenv import load_dotenv

from ecwid_client import EcwidClient
from shiprocket_client import ShiprocketClient
from database import OrderDatabase
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EcwidShiprocketIntegrator:
    """Main integration class"""
    
    def __init__(self, config_path: str = 'config.json'):
        load_dotenv()
        self.config = Config(config_path)
        self.ecwid = EcwidClient(
            store_id=self.config.ecwid_store_id,
            api_token=self.config.ecwid_api_token
        )
        self.shiprocket = ShiprocketClient(
            email=self.config.shiprocket_email,
            password=self.config.shiprocket_password
        )
        self.db = OrderDatabase('orders.db')
        
    def sync_orders(self, hours: int = 24, force: bool = False) -> Dict:
        """
        Sync orders from Ecwid to Shiprocket
        
        Args:
            hours: Number of hours to look back for new orders
            force: Force re-upload of already processed orders
        """
        result = {
            'fetched': 0,
            'uploaded': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        try:
            # Get orders from Ecwid
            logger.info(f"Fetching orders from past {hours} hours...")
            orders = self.ecwid.get_orders(hours=hours)
            result['fetched'] = len(orders)
            logger.info(f"Found {len(orders)} new orders")
            
            for order in orders:
                try:
                    order_id = order['id']
                    
                    # Check if already processed
                    if self.db.order_exists(order_id) and not force:
                        logger.info(f"Order {order_id} already processed, skipping")
                        result['skipped'] += 1
                        continue
                    
                    # Transform order for Shiprocket
                    shiprocket_order = self._transform_order(order)
                    
                    # Upload to Shiprocket
                    logger.info(f"Uploading order {order_id} to Shiprocket...")
                    response = self.shiprocket.create_order(shiprocket_order)
                    
                    if response.get('success'):
                        shiprocket_id = response.get('order_id')
                        self.db.save_order(order_id, shiprocket_id, 'success')
                        result['uploaded'] += 1
                        logger.info(f"✓ Order {order_id} uploaded successfully (Shiprocket ID: {shiprocket_id})")
                    else:
                        error_msg = response.get('message', 'Unknown error')
                        self.db.save_order(order_id, None, 'failed', error_msg)
                        result['failed'] += 1
                        result['errors'].append(f"Order {order_id}: {error_msg}")
                        logger.error(f"✗ Order {order_id} upload failed: {error_msg}")
                        
                except Exception as e:
                    logger.error(f"Error processing order {order.get('id')}: {str(e)}")
                    result['failed'] += 1
                    result['errors'].append(str(e))
            
            logger.info(f"\n=== Sync Complete ===")
            logger.info(f"Fetched: {result['fetched']}")
            logger.info(f"Uploaded: {result['uploaded']}")
            logger.info(f"Failed: {result['failed']}")
            logger.info(f"Skipped: {result['skipped']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Critical error during sync: {str(e)}")
            raise
    
    def _transform_order(self, ecwid_order: Dict) -> Dict:
        """Transform Ecwid order format to Shiprocket format"""
        
        items = []
        for product in ecwid_order.get('items', []):
            items.append({
                'name': product.get('productName'),
                'sku': product.get('productId'),
                'units': product.get('quantity'),
                'selling_price': float(product.get('price', 0))
            })
        
        customer = ecwid_order.get('customer', {})
        shipping = ecwid_order.get('shippingPerson', customer)
        
        shiprocket_order = {
            'order_id': str(ecwid_order.get('id')),
            'order_date': ecwid_order.get('createDate', '').split('T')[0],
            'pickup_location_id': self.config.shiprocket_pickup_location_id,
            'channel_id': self.config.shiprocket_channel_id,
            'billing_customer_name': customer.get('customerName', 'N/A'),
            'billing_email': customer.get('email', ''),
            'billing_phone': customer.get('phone', ''),
            'billing_address': customer.get('shippingStreet', ''),
            'billing_city': customer.get('shippingCity', ''),
            'billing_state': customer.get('shippingStateCode', ''),
            'billing_pincode': customer.get('shippingPostalCode', ''),
            'shipping_customer_name': shipping.get('customerName', 'N/A'),
            'shipping_email': shipping.get('email', ''),
            'shipping_phone': shipping.get('phone', ''),
            'shipping_address': shipping.get('shippingStreet', ''),
            'shipping_city': shipping.get('shippingCity', ''),
            'shipping_state': shipping.get('shippingStateCode', ''),
            'shipping_pincode': shipping.get('shippingPostalCode', ''),
            'order_items': items,
            'payment_method': ecwid_order.get('paymentStatus', 'unknown'),
            'shipping_method': ecwid_order.get('shippingMethod', 'standard'),
            'total_discount': float(ecwid_order.get('discount', 0)),
            'sub_total': float(ecwid_order.get('subtotal', 0)),
            'length': self.config.default_package_length,
            'breadth': self.config.default_package_breadth,
            'height': self.config.default_package_height,
            'weight': self.config.default_package_weight,
        }
        
        return shiprocket_order
    
    def get_sync_status(self) -> Dict:
        """Get current synchronization status"""
        stats = self.db.get_statistics()
        return {
            'total_orders': stats['total'],
            'successful': stats['success'],
            'failed': stats['failed'],
            'pending': stats['pending'],
            'last_sync': stats['last_sync']
        }
    
    def retry_failed_orders(self) -> Dict:
        """Retry uploading failed orders"""
        failed_orders = self.db.get_failed_orders()
        logger.info(f"Retrying {len(failed_orders)} failed orders...")
        
        result = {
            'retried': 0,
            'fixed': 0,
            'still_failed': 0
        }
        
        for order_id, ecwid_id in failed_orders:
            try:
                ecwid_order = self.ecwid.get_order(ecwid_id)
                shiprocket_order = self._transform_order(ecwid_order)
                response = self.shiprocket.create_order(shiprocket_order)
                
                if response.get('success'):
                    shiprocket_id = response.get('order_id')
                    self.db.update_order_status(ecwid_id, shiprocket_id, 'success')
                    result['fixed'] += 1
                    logger.info(f"✓ Fixed order {ecwid_id}")
                else:
                    result['still_failed'] += 1
                    logger.warning(f"✗ Order {ecwid_id} still failing")
                
                result['retried'] += 1
                
            except Exception as e:
                logger.error(f"Error retrying order {ecwid_id}: {str(e)}")
                result['still_failed'] += 1
        
        return result


def main():
    parser = argparse.ArgumentParser(
        description='Ecwid to Shiprocket Order Integration Tool'
    )
    parser.add_argument(
        'command',
        choices=['sync', 'status', 'retry', 'webui'],
        help='Command to execute'
    )
    parser.add_argument(
        '--hours',
        type=int,
        default=24,
        help='Number of hours to look back for new orders (default: 24)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-upload of already processed orders'
    )
    parser.add_argument(
        '--config',
        default='config.json',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port for web UI (default: 5000)'
    )
    
    args = parser.parse_args()
    
    try:
        integrator = EcwidShiprocketIntegrator(args.config)
        
        if args.command == 'sync':
            result = integrator.sync_orders(hours=args.hours, force=args.force)
            print(json.dumps(result, indent=2))
            
        elif args.command == 'status':
            status = integrator.get_sync_status()
            print(json.dumps(status, indent=2))
            
        elif args.command == 'retry':
            result = integrator.retry_failed_orders()
            print(json.dumps(result, indent=2))
            
        elif args.command == 'webui':
            from webui import create_app
            app = create_app(integrator)
            print(f"Starting web UI on http://localhost:{args.port}")
            app.run(debug=True, port=args.port)
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
