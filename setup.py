#!/usr/bin/env python3
"""Quick Start Setup Script"""

import json
import os
import sys

def get_input(prompt, default=None):
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    
    value = input(prompt).strip()
    if not value and default:
        return default
    return value

def main():
    print("\n" + "="*60)
    print("  Ecwid ↔ Shiprocket Integration Setup")
    print("="*60 + "\n")
    
    if os.path.exists('config.json'):
        response = input("config.json already exists. Overwrite? (y/N): ").strip().lower()
        if response != 'y':
            print("Setup cancelled.")
            return
    
    config = {}
    
    print("Ecwid Configuration\n")
    config['ecwid_store_id'] = get_input("Ecwid Store ID")
    config['ecwid_api_token'] = get_input("Ecwid API Token")
    
    print("\nShiprocket Configuration\n")
    config['shiprocket_email'] = get_input("Shiprocket Email")
    config['shiprocket_password'] = get_input("Shiprocket Password")
    config['shiprocket_pickup_location_id'] = int(get_input("Pickup Location ID", "1"))
    config['shiprocket_channel_id'] = int(get_input("Channel ID", "1"))
    
    print("\nDefault Package Dimensions\n")
    config['default_package_length'] = int(get_input("Length (cm)", "10"))
    config['default_package_breadth'] = int(get_input("Breadth (cm)", "10"))
    config['default_package_height'] = int(get_input("Height (cm)", "10"))
    config['default_package_weight'] = float(get_input("Weight (kg)", "0.5"))
    
    try:
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        print("\n✓ Configuration saved to config.json\n")
    except Exception as e:
        print(f"\n✗ Failed to save: {e}\n")
        return False

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(1)
