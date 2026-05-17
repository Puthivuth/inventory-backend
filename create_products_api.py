#!/usr/bin/env python3
"""
Create 10 sample products by posting to Django REST API
Usage: python create_products_api.py
"""

import requests
import json
from decimal import Decimal

# Django API base URL
API_BASE_URL = "http://127.0.0.1:8000/api"

# Credentials for login
USERNAME = "admin"
PASSWORD = "admin123"  # Change this to your actual password

def get_auth_token():
    """Login and get authentication token"""
    print("🔐 Authenticating...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/login/",
            json={"username": USERNAME, "password": PASSWORD},
            timeout=10
        )
        
        if response.status_code == 200:
            token = response.json().get('token')
            print(f"✅ Authenticated as {USERNAME}")
            return token
        else:
            print(f"❌ Authentication failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None

def get_subcategory_id():
    """Get or return default subcategory ID"""
    # Assuming subcategory with ID 1 exists
    # You can modify this to fetch from API
    return 1

def get_source_id():
    """Get or return default source ID"""
    # Assuming source with ID 1 exists
    # You can modify this to fetch from API
    return 1

def create_products(token):
    """Create 10 sample products"""
    
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    # Sample products
    products = [
        {
            'productName': 'DeWalt 20V Cordless Drill',
            'description': 'Powerful cordless drill with 20V lithium-ion battery',
            'skuCode': 'DW-DCD771C2',
            'unit': 'pcs',
            'costPrice': 89.50,
            'salePrice': 149.99,
            'discount': 0,
            'image': 'https://images.unsplash.com/photo-1572981779307-38b8cabb2407',
        },
        {
            'productName': 'Stanley FatMax Tape Measure 25ft',
            'description': 'Heavy-duty tape measure with 25-foot length',
            'skuCode': 'ST-FMHT33865',
            'unit': 'pcs',
            'costPrice': 12.40,
            'salePrice': 24.99,
            'discount': 0,
            'image': 'https://images.unsplash.com/photo-1706101426222-feb156e9c7fe',
        },
        {
            'productName': 'Makita Angle Grinder 4.5"',
            'description': 'Compact angle grinder for cutting and grinding',
            'skuCode': 'MK-9557PBX1',
            'unit': 'pcs',
            'costPrice': 54.00,
            'salePrice': 99.95,
            'discount': 0,
            'image': 'https://img.rocket.new/generatedImages/rocket_gen_img_1da2285a0-1773143783458.png',
        },
        {
            'productName': 'Bosch 18V Circular Saw',
            'description': 'Professional circular saw for wood cutting',
            'skuCode': 'BS-CCS180B',
            'unit': 'pcs',
            'costPrice': 112.00,
            'salePrice': 199.99,
            'discount': 5,
            'image': 'https://images.unsplash.com/photo-1587210019033-d2c0cf35fde2',
        },
        {
            'productName': '3M Safety Glasses',
            'description': 'Clear protective safety glasses for eye protection',
            'skuCode': '3M-90966-80025',
            'unit': 'pcs',
            'costPrice': 1.20,
            'salePrice': 2.50,
            'discount': 0,
            'image': '',
        },
        {
            'productName': 'Work Gloves Leather',
            'description': 'Durable leather work gloves for heavy-duty work',
            'skuCode': 'WG-LEATHER-LG',
            'unit': 'pair',
            'costPrice': 3.50,
            'salePrice': 8.99,
            'discount': 0,
            'image': '',
        },
        {
            'productName': 'Milwaukee Impact Driver',
            'description': 'Compact impact driver with high torque',
            'skuCode': 'MW-2804-20',
            'unit': 'pcs',
            'costPrice': 95.00,
            'salePrice': 169.99,
            'discount': 10,
            'image': 'https://images.unsplash.com/photo-1530124566582-a618bc2615dc',
        },
        {
            'productName': 'Ryobi Jigsaw',
            'description': 'Precision jigsaw for curved cuts',
            'skuCode': 'RY-JS1800',
            'unit': 'pcs',
            'costPrice': 45.00,
            'salePrice': 79.99,
            'discount': 0,
            'image': 'https://images.unsplash.com/photo-1532012197267-da84d127e765',
        },
        {
            'productName': 'Hammer Claw 16oz',
            'description': 'Precision-balanced claw hammer',
            'skuCode': 'HM-CLAW-16',
            'unit': 'pcs',
            'costPrice': 12.00,
            'salePrice': 19.99,
            'discount': 0,
            'image': '',
        },
        {
            'productName': 'Adjustable Wrench Set',
            'description': 'Set of 4 adjustable wrenches',
            'skuCode': 'WR-ADJ-SET-4',
            'unit': 'set',
            'costPrice': 18.00,
            'salePrice': 34.99,
            'discount': 0,
            'image': 'https://images.unsplash.com/photo-1546874177-7663c60ff82f',
        },
    ]
    
    subcategory_id = get_subcategory_id()
    source_id = get_source_id()
    
    created = 0
    failed = 0
    
    print(f"\n📦 Creating {len(products)} products...\n")
    
    for product in products:
        payload = {
            **product,
            'subcategory': subcategory_id,
            'source': source_id,
            'status': 'Active'
        }
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/products/",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                created += 1
                result = response.json()
                print(f"✅ Created: {product['productName']} (ID: {result.get('productId')})")
            else:
                failed += 1
                print(f"❌ Failed: {product['productName']} - {response.status_code} {response.text[:100]}")
        except Exception as e:
            failed += 1
            print(f"❌ Error: {product['productName']} - {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"📊 Summary:")
    print(f"   Created: {created} products")
    print(f"   Failed: {failed} products")
    print(f"   Total: {len(products)} products")
    print(f"{'='*60}\n")
    
    return created > 0

if __name__ == '__main__':
    print("🔧 Creating sample products via API...\n")
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("Cannot proceed without authentication")
        exit(1)
    
    # Create products
    success = create_products(token)
    
    if success:
        print("✨ Products created successfully!")
        print("🌐 Open http://127.0.0.1:8000 to view the products in the admin panel")
    else:
        print("⚠️  Some products failed to create. Check your Django backend logs.")
