#!/usr/bin/env python3
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
        result = {
            'fetched': 0,
            'uploaded': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        try:
            logger.info(f"Fetching orders from past {hours} hours...")
            orders = self.ecwid.get_orders(hours=hours)
            result['fetched'] = len(orders)
            logger.info(f"Found {len(orders)} new orders")
            
            for order in orders:
                try:
                    order_id = order['id']
                    
                    if self.db.order_exists(order_id) and not force:
                        logger.info(f"Order {order_id} already processed, skipping")
                        result['skipped'] += 1
                        continue
                    
                    shiprocket_order = self._transform_order(order)
                    logger.info(f"Uploading order {order_id} to Shiprocket...")
                    response = self.shiprocket.create_order(shiprocket_order)
                    
                    if response.get('success'):
                        shiprocket_id = response.get('order_id')
                        self.db.save_order(order_id, shiprocket_id, 'success')
                        result['uploaded'] += 1
                        logger.info(f"Order {order_id} uploaded successfully")
                    else:
                        error_msg = response.get('message', 'Unknown error')
                        self.db.save_order(order_id, None, 'failed', error_msg)
                        result['failed'] += 1
                        result['errors'].append(f"Order {order_id}: {error_msg}")
                        logger.error(f"Order {order_id} upload failed: {error_msg}")
                        
                except Exception as e:
                    logger.error(f"Error processing order {order.get('id')}: {str(e)}")
                    result['failed'] += 1
                    result['errors'].append(str(e))
            
            logger.info(f"Sync Complete - Fetched: {result['fetched']}, Uploaded: {result['uploaded']}, Failed: {result['failed']}")
            return result
            
        except Exception as e:
            logger.error(f"Critical error during sync: {str(e)}")
            raise
    
    def _calculate_package_dimensions(self, items: List[Dict]) -> Dict:
        """
        Calculate package dimensions from order items
        
        Returns dict with:
        - length, breadth, height (in cm)
        - weight (in kg)
        """
        
        total_weight = 0.0
        max_length = self.config.default_package_length
        max_breadth = self.config.default_package_breadth
        max_height = self.config.default_package_height
        
        # Try to get actual dimensions from products
        for item in items:
            # Get weight from item
            weight = item.get('weight')
            if weight:
                try:
                    # Weight might be string or number
                    total_weight += float(weight) * item.get('quantity', 1)
                except (ValueError, TypeError):
                    pass
            
            # Get dimensions from item
            length = item.get('length')
            breadth = item.get('breadth')
            height = item.get('height')
            
            # Use maximum dimensions found
            if length:
                try:
                    max_length = max(max_length, float(length))
                except (ValueError, TypeError):
                    pass
            
            if breadth:
                try:
                    max_breadth = max(max_breadth, float(breadth))
                except (ValueError, TypeError):
                    pass
            
            if height:
                try:
                    max_height = max(max_height, float(height))
                except (ValueError, TypeError):
                    pass
        
        # If no weight calculated, use default
        if total_weight == 0:
            total_weight = self.config.default_package_weight * len(items) if items else self.config.default_package_weight
        
        logger.info(f"Package dimensions calculated - L:{max_length}cm, B:{max_breadth}cm, H:{max_height}cm, W:{total_weight}kg")
        
        return {
            'length': max_length,
            'breadth': max_breadth,
            'height': max_height,
            'weight': total_weight
        }
    
    def _transform_order(self, ecwid_order: Dict) -> Dict:
        items = []
        for product in ecwid_order.get('items', []):
            items.append({
                'name': product.get('productName'),
                'sku': product.get('productId'),
                'units': product.get('quantity'),
                'selling_price': float(product.get('price', 0)),
                'weight': product.get('weight', 0),
                'length': product.get('length'),
                'breadth': product.get('breadth'),
                'height': product.get('height'),
            })
        
        customer = ecwid_order.get('customer', {})
        shipping = ecwid_order.get('shippingPerson', customer)
        
        # Calculate actual package dimensions from items
        package_dims = self._calculate_package_dimensions(items)
        
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
            'length': package_dims['length'],
            'breadth': package_dims['breadth'],
            'height': package_dims['height'],
            'weight': package_dims['weight'],
        }
        
        return shiprocket_order
    
    def get_sync_status(self) -> Dict:
        stats = self.db.get_statistics()
        return {
            'total_orders': stats['total'],
            'successful': stats['success'],
            'failed': stats['failed'],
            'pending': stats['pending'],
            'last_sync': stats['last_sync']
        }
    
    def retry_failed_orders(self) -> Dict:
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
                    logger.info(f"Fixed order {ecwid_id}")
                else:
                    result['still_failed'] += 1
                    logger.warning(f"Order {ecwid_id} still failing")
                
                result['retried'] += 1
                
            except Exception as e:
                logger.error(f"Error retrying order {ecwid_id}: {str(e)}")
                result['still_failed'] += 1
        
        return result


def main():
    parser = argparse.ArgumentParser(description='Ecwid to Shiprocket Order Integration')
    parser.add_argument('command', choices=['sync', 'status', 'retry', 'webui'])
    parser.add_argument('--hours', type=int, default=24)
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--config', default='config.json')
    parser.add_argument('--port', type=int, default=5000)
    
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
            from webui import run_app
            print(f"Starting web UI on port {args.port}")
            run_app(integrator, port=args.port)
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
