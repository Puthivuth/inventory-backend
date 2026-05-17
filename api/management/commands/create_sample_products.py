#!/usr/bin/env python
"""
Django management command to create sample products
Usage: python manage.py create_sample_products
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from api.models import Product, SubCategory, Source, Category
import os
import django

# Disable image search to avoid CLIP model download during product creation
os.environ['DISABLE_IMAGE_SEARCH'] = '1'

class Command(BaseCommand):
    help = 'Create 10 sample products in the database'

    def handle(self, *args, **options):
        self.stdout.write("🔧 Creating sample products...\n")
        
        # Get or create default category
        category, _ = Category.objects.get_or_create(name='General')
        self.stdout.write(f"Using Category: {category.name} (ID: {category.categoryId})")
        
        # Get or create default subcategory
        subcategory, created = SubCategory.objects.get_or_create(
            name='Power Tools',
            defaults={'category': category}
        )
        self.stdout.write(f"Using SubCategory: {subcategory.name} (ID: {subcategory.subcategoryId})")
        
        # Get or create default source (supplier)
        source, created = Source.objects.get_or_create(
            name='ProTools Supply Co.'
        )
        self.stdout.write(f"Using Source: {source.name} (ID: {source.sourceId})")
        
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
        
        with transaction.atomic():
            for product_data in products_data:
                sku = product_data['skuCode']
                
                # Check if product already exists
                if Product.objects.filter(skuCode=sku).exists():
                    self.stdout.write(f"⏭️  Skipping {product_data['productName']} - SKU {sku} already exists")
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
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Created: {product.productName} (ID: {product.productId}, SKU: {product.skuCode})"
                    )
                )
                created_count += 1
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write("📊 Summary:")
        self.stdout.write(f"   Created: {created_count} products")
        self.stdout.write(f"   Skipped: {skipped_count} products (already exist)")
        self.stdout.write(f"   Total: {created_count + skipped_count} products")
        self.stdout.write("="*60 + "\n")
        
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS("✨ Products created successfully! You can now view them in your app.")
            )
        else:
            self.stdout.write(
                self.style.WARNING("⚠️  All products already exist in the database.")
            )
