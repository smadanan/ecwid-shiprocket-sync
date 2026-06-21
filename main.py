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
            logger.info(f"========== SYNC START ==========")
            logger.info(f"Fetching orders from past {hours} hours...")
            logger.info(f"Force mode: {force}")
            
            orders = self.ecwid.get_orders(hours=hours)
            result['fetched'] = len(orders)
            logger.info(f"Found {len(orders)} new orders")
            
            for order in orders:
                try:
                    order_id = order['id']
                    
                    # Check if order already exists in database
                    if self.db.order_exists(order_id):
                        logger.info(f"✅ Order {order_id} already processed - SKIPPING (duplicate prevention)")
                        result['skipped'] += 1
                        continue
                    
                    # Fetch FULL order details
                    logger.info(f"Fetching full details for order {order_id}")
                    full_order = self.ecwid.get_order(order_id)
                    
                    shiprocket_order = self._transform_order(full_order)
                    
                    logger.info(f"Uploading order {order_id} to Shiprocket...")
                    logger.info(f"PAYLOAD: {json.dumps(shiprocket_order, indent=2)}")
                    response = self.shiprocket.create_order(shiprocket_order)
                    logger.info(f"RESPONSE: {json.dumps(response, indent=2)}")
                    
                    # Shiprocket returns order_id on success (not 'success' field)
                    if response.get('order_id') or response.get('success'):
                        shiprocket_id = response.get('order_id')
                        shipment_id = response.get('shipment_id')
                        self.db.save_order(order_id, shiprocket_id, 'success')
                        result['uploaded'] += 1
                        logger.info(f"✅ Order {order_id} uploaded successfully!")
                        logger.info(f"   Shiprocket Order ID: {shiprocket_id}")
                        logger.info(f"   Shipment ID: {shipment_id}")
                        logger.info(f"   Status: {response.get('status', 'N/A')}")
                    else:
                        error_msg = response.get('message', 'Unknown error')
                        errors_dict = response.get('errors', {})
                        self.db.save_order(order_id, None, 'failed', error_msg)
                        result['failed'] += 1
                        result['errors'].append(f"Order {order_id}: {error_msg}")
                        logger.error(f"❌ Order {order_id} upload failed!")
                        logger.error(f"   Message: {error_msg}")
                        if errors_dict:
                            for field, errors in errors_dict.items():
                                logger.error(f"   {field}: {errors}")
                        
                except Exception as e:
                    order_id = order.get('id', 'UNKNOWN')
                    logger.error(f"❌ ERROR processing order {order_id}: {str(e)}", exc_info=True)
                    result['failed'] += 1
                    result['errors'].append(f"Order {order_id}: {str(e)}")
            
            logger.info(f"Sync Complete - Fetched: {result['fetched']}, Uploaded: {result['uploaded']}, Failed: {result['failed']}, Skipped: {result['skipped']}")
            logger.info(f"========== SYNC END ==========")
            return result
            
        except Exception as e:
            logger.critical(f"CRITICAL ERROR during sync: {str(e)}", exc_info=True)
            raise
    
    def _get_state_full_name(self, state_code: str) -> str:
        """Convert state code to full name (RJ -> Rajasthan)"""
        state_map = {
            'AN': 'Andaman and Nicobar Islands',
            'AP': 'Andhra Pradesh',
            'AR': 'Arunachal Pradesh',
            'AS': 'Assam',
            'BR': 'Bihar',
            'CG': 'Chhattisgarh',
            'CH': 'Chandigarh',
            'CT': 'Chhattisgarh',
            'DD': 'Daman and Diu',
            'DL': 'Delhi',
            'DN': 'Dadra and Nagar Haveli',
            'GA': 'Goa',
            'GJ': 'Gujarat',
            'HR': 'Haryana',
            'HP': 'Himachal Pradesh',
            'JK': 'Jammu and Kashmir',
            'JH': 'Jharkhand',
            'KA': 'Karnataka',
            'KL': 'Kerala',
            'LA': 'Ladakh',
            'LD': 'Lakshadweep',
            'MP': 'Madhya Pradesh',
            'MH': 'Maharashtra',
            'MN': 'Manipur',
            'ML': 'Meghalaya',
            'MZ': 'Mizoram',
            'NL': 'Nagaland',
            'OR': 'Odisha',
            'OD': 'Odisha',
            'PB': 'Punjab',
            'PY': 'Puducherry',
            'RJ': 'Rajasthan',
            'SK': 'Sikkim',
            'TN': 'Tamil Nadu',
            'TG': 'Telangana',
            'TR': 'Tripura',
            'UP': 'Uttar Pradesh',
            'UT': 'Uttarakhand',
            'WB': 'West Bengal',
        }
        return state_map.get(state_code.upper(), state_code)
    
    def _clean_phone(self, phone: str) -> str:
        """Clean phone number - remove +91, spaces, dashes"""
        if not phone:
            return ''
        # Remove +91, +, spaces, dashes
        phone = phone.replace('+91', '').replace('+', '').replace(' ', '').replace('-', '')
        # Keep only digits
        phone = ''.join(c for c in phone if c.isdigit())
        # Return last 10 digits (Indian mobile)
        return phone[-10:] if len(phone) >= 10 else phone
    
    def _format_order_date(self, date_str: str) -> str:
        """Convert order date to dd-mm-yyyy hh:MM format"""
        try:
            # Ecwid format: "2026-06-15 08:21:52 +0000"
            if 'T' in date_str:
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                date_obj = datetime.strptime(date_str.split('+')[0].strip(), '%Y-%m-%d %H:%M:%S')
            return date_obj.strftime('%d-%m-%Y %H:%M')
        except:
            return ''
    
    def _calculate_package_dimensions(self, items: List[Dict]) -> Dict:
        total_weight = 0.0
        max_length = self.config.default_package_length
        max_breadth = self.config.default_package_breadth
        max_height = self.config.default_package_height
        
        for item in items:
            weight = item.get('weight')
            if weight:
                try:
                    total_weight += float(weight) * item.get('quantity', 1)
                except (ValueError, TypeError):
                    pass
            
            length = item.get('length')
            breadth = item.get('breadth')
            height = item.get('height')
            
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
        
        if total_weight == 0:
            total_weight = self.config.default_package_weight * len(items) if items else self.config.default_package_weight
        
        logger.info(f"Package dimensions: L:{max_length}cm, B:{max_breadth}cm, H:{max_height}cm, W:{total_weight}kg")
        
        return {
            'length': int(max_length),
            'breadth': int(max_breadth),
            'height': int(max_height),
            'weight': round(total_weight, 2),
        }
    
    def _transform_order(self, ecwid_order: Dict) -> Dict:
        try:
            order_id = ecwid_order.get('id', 'UNKNOWN')
            logger.info(f"[ORDER {order_id}] Starting transformation...")
            
            items = []
            for idx, product in enumerate(ecwid_order.get('items', [])):
                try:
                    item = {
                        'name': product.get('name', 'Product'),
                        'sku': product.get('sku', ''),
                        'units': product.get('quantity', 1),
                        'selling_price': float(product.get('price', 0)),
                    }
                    items.append(item)
                    logger.debug(f"[ORDER {order_id}] Item {idx}: {item['name']} x{item['units']} @ Rs.{item['selling_price']}")
                except Exception as e:
                    logger.error(f"[ORDER {order_id}] Error processing item {idx}: {str(e)}")
                    raise
            
            # Get billing info
            billing = ecwid_order.get('billingPerson', {})
            billing_name = billing.get('name', 'Customer').strip()
            billing_first_name = billing.get('firstName', 'Customer').strip()
            billing_last_name = billing.get('lastName', 'Customer').strip()
            billing_phone = self._clean_phone(billing.get('phone', ''))
            billing_address = billing.get('street', '').strip()
            billing_city = billing.get('city', '').strip()
            billing_state = self._get_state_full_name(billing.get('stateOrProvinceCode', ''))
            billing_pincode = billing.get('postalCode', '').strip()
            
            logger.debug(f"[ORDER {order_id}] Billing: {billing_name} ({billing_phone}) @ {billing_address}, {billing_city}, {billing_state} {billing_pincode}")
            
            # Validate billing info
            if not billing_name or billing_name == 'Customer':
                logger.warning(f"[ORDER {order_id}] WARNING: Billing name is empty or default")
            if not billing_phone:
                logger.warning(f"[ORDER {order_id}] WARNING: Billing phone is empty")
            if not billing_address:
                logger.warning(f"[ORDER {order_id}] WARNING: Billing address is empty")
            if not billing_city:
                logger.warning(f"[ORDER {order_id}] WARNING: Billing city is empty")
            if not billing_state:
                logger.warning(f"[ORDER {order_id}] WARNING: Billing state is empty")
            if not billing_pincode:
                logger.warning(f"[ORDER {order_id}] WARNING: Billing pincode is empty")
            
            # Get shipping info
            shipping = ecwid_order.get('shippingPerson', billing)
            shipping_name = shipping.get('name', 'Customer').strip()
            shipping_phone = self._clean_phone(shipping.get('phone', ''))
            shipping_address = shipping.get('street', '').strip()
            shipping_city = shipping.get('city', '').strip()
            shipping_state = self._get_state_full_name(shipping.get('stateOrProvinceCode', ''))
            shipping_pincode = shipping.get('postalCode', '').strip()
            
            logger.debug(f"[ORDER {order_id}] Shipping: {shipping_name} ({shipping_phone}) @ {shipping_address}, {shipping_city}, {shipping_state} {shipping_pincode}")
            
            # Check if shipping is same as billing
            shipping_is_billing = (
                billing_address == shipping_address and
                billing_city == shipping_city and
                billing_pincode == shipping_pincode and
                billing_state == shipping_state
            )
            logger.debug(f"[ORDER {order_id}] Shipping is billing: {shipping_is_billing}")
            
            package_dims = self._calculate_package_dimensions(items)
            
        except Exception as e:
            logger.error(f"[ORDER {order_id}] ERROR during field extraction: {str(e)}", exc_info=True)
            raise
        
        # Get first product for SKU and name
        first_item = items[0] if items else {'name': 'Product', 'sku': 'SKU', 'quantity': 1, 'selling_price': 0}
        
        # Build order in Shiprocket's exact format
        shiprocket_order = {
            'order_id': str(ecwid_order.get('id', '')),
            'order_date': self._format_order_date(ecwid_order.get('createDate', '')),
            'pickup_location_id': int(self.config.shiprocket_pickup_location_id),
            'channel_id': int(self.config.shiprocket_channel_id),
            'payment_method': 'Prepaid',
            'shipping_is_billing': shipping_is_billing,
            'billing_customer_name': billing_name,
            'billing_first_name': billing_first_name,
            'billing_last_name': billing_last_name,
            'billing_email': ecwid_order.get('email', '').strip(),
            'billing_phone': billing_phone,
            'billing_address': billing_address,
            'billing_address_2': '',
            'billing_city': billing_city,
            'billing_pincode': billing_pincode,
            'billing_state': billing_state,
            'billing_country': 'India',
            'shipping_customer_name': shipping_name,
            'shipping_email': ecwid_order.get('email', '').strip(),
            'shipping_phone': shipping_phone,
            'shipping_address': shipping_address,
            'shipping_address_2': '',
            'shipping_city': shipping_city,
            'shipping_pincode': shipping_pincode,
            'shipping_state': shipping_state,
            'shipping_country': 'India',
            'order_items': items,
            'shipping_charges': 0,
            'giftwrap_charges': 0,
            'transaction_charges': 0,
            'total_discount': float(ecwid_order.get('discount', 0)),
            'sub_total': float(ecwid_order.get('subtotal', 0)),
            'length': package_dims['length'],
            'breadth': package_dims['breadth'],
            'height': package_dims['height'],
            'weight': package_dims['weight'],
            'comment': 'Order synced from Ecwid',
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
                
                # Shiprocket returns order_id on success
                if response.get('order_id') or response.get('success'):
                    shiprocket_id = response.get('order_id')
                    self.db.update_order_status(ecwid_id, shiprocket_id, 'success')
                    result['fixed'] += 1
                    logger.info(f"✅ Fixed order {ecwid_id}")
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
