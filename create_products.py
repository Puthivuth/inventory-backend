#!/usr/bin/env python
"""
Bulk insert 10 sample products into the inventory database
Usage: python create_products.py
"""

import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import Product, SubCategory, Source

def create_sample_products():
    """Create 10 sample products"""
    
    # Get or create default subcategory
    subcategory, created = SubCategory.objects.get_or_create(
        name='Power Tools',
        defaults={'description': 'Power tools and equipment'}
    )
    print(f"Using SubCategory: {subcategory.name} (ID: {subcategory.subcategoryId})")
    
    # Get or create default source (supplier)
    source, created = Source.objects.get_or_create(
        name='ProTools Supply Co.',
        defaults={'contactInfo': 'Contact ProTools'}
    )
    print(f"Using Source: {source.name} (ID: {source.sourceId})")
    
    # Sample products data
    products_data = [
        {
            'productName': 'DeWalt 20V Cordless Drill',
            'description': 'Powerful cordless drill with 20V lithium-ion battery',
            'skuCode': 'DW-DCD771C2',
            'unit': 'pcs',
            'costPrice': Decimal('89.50'),
            'salePrice': Decimal('149.99'),
            'discount': Decimal('0'),
            'image': 'https://images.unsplash.com/photo-1572981779307-38b8cabb2407',
        },
        {
            'productName': 'Stanley FatMax Tape Measure 25ft',
            'description': 'Heavy-duty tape measure with 25-foot length',
            'skuCode': 'ST-FMHT33865',
            'unit': 'pcs',
            'costPrice': Decimal('12.40'),
            'salePrice': Decimal('24.99'),
            'discount': Decimal('0'),
            'image': 'https://images.unsplash.com/photo-1706101426222-feb156e9c7fe',
        },
        {
            'productName': 'Makita Angle Grinder 4.5"',
            'description': 'Compact angle grinder for cutting and grinding',
            'skuCode': 'MK-9557PBX1',
            'unit': 'pcs',
            'costPrice': Decimal('54.00'),
            'salePrice': Decimal('99.95'),
            'discount': Decimal('0'),
            'image': 'https://img.rocket.new/generatedImages/rocket_gen_img_1da2285a0-1773143783458.png',
        },
        {
            'productName': 'Bosch 18V Circular Saw',
            'description': 'Professional circular saw for wood cutting',
            'skuCode': 'BS-CCS180B',
            'unit': 'pcs',
            'costPrice': Decimal('112.00'),
            'salePrice': Decimal('199.99'),
            'discount': Decimal('5'),
            'image': 'https://images.unsplash.com/photo-1587210019033-d2c0cf35fde2',
        },
        {
            'productName': '3M Safety Glasses',
            'description': 'Clear protective safety glasses for eye protection',
            'skuCode': '3M-90966-80025',
            'unit': 'pcs',
            'costPrice': Decimal('1.20'),
            'salePrice': Decimal('2.50'),
            'discount': Decimal('0'),
            'image': '',
        },
        {
            'productName': 'Work Gloves Leather',
            'description': 'Durable leather work gloves for heavy-duty work',
            'skuCode': 'WG-LEATHER-LG',
            'unit': 'pair',
            'costPrice': Decimal('3.50'),
            'salePrice': Decimal('8.99'),
            'discount': Decimal('0'),
            'image': '',
        },
        {
            'productName': 'Milwaukee Impact Driver',
            'description': 'Compact impact driver with high torque',
            'skuCode': 'MW-2804-20',
            'unit': 'pcs',
            'costPrice': Decimal('95.00'),
            'salePrice': Decimal('169.99'),
            'discount': Decimal('10'),
            'image': 'https://images.unsplash.com/photo-1530124566582-a618bc2615dc',
        },
        {
            'productName': 'Ryobi Jigsaw',
            'description': 'Precision jigsaw for curved cuts',
            'skuCode': 'RY-JS1800',
            'unit': 'pcs',
            'costPrice': Decimal('45.00'),
            'salePrice': Decimal('79.99'),
            'discount': Decimal('0'),
            'image': 'https://images.unsplash.com/photo-1532012197267-da84d127e765',
        },
        {
            'productName': 'Hammer Claw 16oz',
            'description': 'Precision-balanced claw hammer',
            'skuCode': 'HM-CLAW-16',
            'unit': 'pcs',
            'costPrice': Decimal('12.00'),
            'salePrice': Decimal('19.99'),
            'discount': Decimal('0'),
            'image': '',
        },
        {
            'productName': 'Adjustable Wrench Set',
            'description': 'Set of 4 adjustable wrenches',
            'skuCode': 'WR-ADJ-SET-4',
            'unit': 'set',
            'costPrice': Decimal('18.00'),
            'salePrice': Decimal('34.99'),
            'discount': Decimal('0'),
            'image': 'https://images.unsplash.com/photo-1546874177-7663c60ff82f',
        },
    ]
    
    # Create products
    created_count = 0
    skipped_count = 0
    
    for product_data in products_data:
        sku = product_data['skuCode']
        
        # Check if product already exists
        if Product.objects.filter(skuCode=sku).exists():
            print(f"⏭️  Skipping {product_data['productName']} - SKU {sku} already exists")
            skipped_count += 1
            continue
        
        # Create product
        product = Product.objects.create(
            productName=product_data['productName'],
            description=product_data['description'],
            skuCode=product_data['skuCode'],
            unit=product_data['unit'],
            costPrice=product_data['costPrice'],
            salePrice=product_data['salePrice'],
            discount=product_data['discount'],
            image=product_data['image'],
            subcategory=subcategory,
            source=source,
            status='Active'
        )
        
        print(f"✅ Created: {product.productName} (ID: {product.productId}, SKU: {product.skuCode})")
        created_count += 1
    
    print(f"\n{'='*60}")
    print(f"📊 Summary:")
    print(f"   Created: {created_count} products")
    print(f"   Skipped: {skipped_count} products (already exist)")
    print(f"   Total: {created_count + skipped_count} products")
    print(f"{'='*60}\n")
    
    return created_count > 0

if __name__ == '__main__':
    print("🔧 Creating sample products...\n")
    success = create_sample_products()
    
    if success:
        print("✨ Products created successfully! You can now view them in your app.")
    else:
        print("⚠️  All products already exist in the database.")
