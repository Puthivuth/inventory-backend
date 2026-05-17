#!/usr/bin/env python
import os
import sys
import django
from decimal import Decimal

sys.path.insert(0, 'D:\\Class\\Year_03\\MAD_Class\\inventory-backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

django.setup()

from api.models import Product, Inventory, Category, SubCategory, Source

print("🗑️  Deleting all existing products...")
deleted_count, _ = Product.objects.all().delete()
print(f"✅ Deleted {deleted_count} product(s)")

print("\n📝 Creating categories and subcategories...")

# Create categories and subcategories
categories_data = {
    'Power Tools': ['Drills', 'Saws', 'Sanders'],
    'Hand Tools': ['Hammers', 'Wrenches', 'Screwdrivers'],
    'Safety Equipment': ['Gloves', 'Eye Protection', 'Respirators'],
    'Measuring Tools': ['Tape Measures', 'Levels', 'Squares'],
    'Electrical': ['Cables', 'Connectors', 'Batteries'],
}

categories = {}
for cat_name, subcats in categories_data.items():
    try:
        cat = Category.objects.get(name=cat_name)
    except Category.DoesNotExist:
        cat = Category.objects.create(name=cat_name)
    
    categories[cat_name] = cat
    print(f"✓ Category: {cat_name}")
    
    for subcat_name in subcats:
        try:
            subcat = SubCategory.objects.get(name=subcat_name)
        except SubCategory.DoesNotExist:
            subcat = SubCategory.objects.create(
                category=cat,
                name=subcat_name
            )
        print(f"  └─ Subcategory: {subcat_name}")

print("\n📝 Creating suppliers...")

# Create suppliers
suppliers_data = [
    {'name': 'ABC Suppliers', 'contactPerson': 'John Smith', 'email': 'john@abcsuppliers.com', 'phone': '555-1234', 'address': '123 Business St'},
    {'name': 'XYZ Distributors', 'contactPerson': 'Jane Doe', 'email': 'jane@xyzdist.com', 'phone': '555-5678', 'address': '456 Trade Ave'},
    {'name': 'Global Tools Inc', 'contactPerson': 'Bob Johnson', 'email': 'bob@globaltools.com', 'phone': '555-9999', 'address': '789 Industrial Blvd'},
]

suppliers = {}
for sup_data in suppliers_data:
    try:
        supplier = Source.objects.get(name=sup_data['name'])
    except Source.DoesNotExist:
        supplier = Source.objects.create(**sup_data)
    suppliers[sup_data['name']] = supplier
    print(f"✓ Supplier: {sup_data['name']}")

print("\n📝 Creating sample products with inventory...")

# Sample products with detailed inventory
products_data = [
    # Power Tools - Drills
    {
        'name': 'DeWalt 20V Cordless Drill',
        'sku': 'DWL-001',
        'description': 'Professional grade cordless drill with 20V battery',
        'category': 'Drills',
        'cost_price': 89.99,
        'sale_price': 129.99,
        'unit': 'pcs',
        'supplier': 'Global Tools Inc',
        'quantity': 15,
        'reorder_level': 5,
        'location': 'Aisle A1'
    },
    {
        'name': 'Makita Impact Driver',
        'sku': 'MAK-002',
        'description': '18V brushless impact driver',
        'category': 'Drills',
        'cost_price': 129.00,
        'sale_price': 199.99,
        'unit': 'pcs',
        'supplier': 'ABC Suppliers',
        'quantity': 8,
        'reorder_level': 3,
        'location': 'Aisle A2'
    },
    # Power Tools - Saws
    {
        'name': 'Circular Saw Pro 7.25"',
        'sku': 'SAW-001',
        'description': '15 amp circular saw with laser guide',
        'category': 'Saws',
        'cost_price': 59.99,
        'sale_price': 99.99,
        'unit': 'pcs',
        'supplier': 'XYZ Distributors',
        'quantity': 12,
        'reorder_level': 4,
        'location': 'Aisle B1'
    },
    {
        'name': 'Reciprocating Saw',
        'sku': 'SAW-002',
        'description': 'Cordless reciprocating saw 20V',
        'category': 'Saws',
        'cost_price': 74.50,
        'sale_price': 119.99,
        'unit': 'pcs',
        'supplier': 'Global Tools Inc',
        'quantity': 6,
        'reorder_level': 2,
        'location': 'Aisle B2'
    },
    # Hand Tools - Hammers
    {
        'name': 'Claw Hammer 16oz',
        'sku': 'HAM-001',
        'description': 'Steel claw hammer with ergonomic grip',
        'category': 'Hammers',
        'cost_price': 12.99,
        'sale_price': 19.99,
        'unit': 'pcs',
        'supplier': 'ABC Suppliers',
        'quantity': 45,
        'reorder_level': 15,
        'location': 'Aisle C1'
    },
    {
        'name': 'Sledge Hammer 10lb',
        'sku': 'HAM-002',
        'description': 'Heavy duty sledge hammer',
        'category': 'Hammers',
        'cost_price': 34.99,
        'sale_price': 49.99,
        'unit': 'pcs',
        'supplier': 'XYZ Distributors',
        'quantity': 18,
        'reorder_level': 6,
        'location': 'Aisle C2'
    },
    # Hand Tools - Wrenches
    {
        'name': 'Adjustable Wrench Set 12pcs',
        'sku': 'WRN-001',
        'description': 'Chrome plated wrench set',
        'category': 'Wrenches',
        'cost_price': 24.99,
        'sale_price': 39.99,
        'unit': 'set',
        'supplier': 'ABC Suppliers',
        'quantity': 25,
        'reorder_level': 8,
        'location': 'Aisle D1'
    },
    # Safety Equipment
    {
        'name': 'Nitrile Gloves Latex-Free (100 pack)',
        'sku': 'GLV-001',
        'description': 'Disposable nitrile gloves',
        'category': 'Gloves',
        'cost_price': 8.99,
        'sale_price': 14.99,
        'unit': 'box',
        'supplier': 'Global Tools Inc',
        'quantity': 120,
        'reorder_level': 30,
        'location': 'Aisle E1'
    },
    {
        'name': 'Safety Glasses Anti-Fog',
        'sku': 'EYE-001',
        'description': 'Anti-fog protective safety glasses',
        'category': 'Eye Protection',
        'cost_price': 7.50,
        'sale_price': 12.99,
        'unit': 'pcs',
        'supplier': 'XYZ Distributors',
        'quantity': 85,
        'reorder_level': 25,
        'location': 'Aisle E2'
    },
    # Measuring Tools
    {
        'name': 'Tape Measure 25ft',
        'sku': 'TAP-001',
        'description': 'Steel tape measure with auto-lock',
        'category': 'Tape Measures',
        'cost_price': 9.99,
        'sale_price': 15.99,
        'unit': 'pcs',
        'supplier': 'ABC Suppliers',
        'quantity': 32,
        'reorder_level': 10,
        'location': 'Aisle F1'
    },
    {
        'name': 'Spirit Level 48"',
        'sku': 'LEV-001',
        'description': 'Aluminum spirit level with bubble',
        'category': 'Levels',
        'cost_price': 19.99,
        'sale_price': 29.99,
        'unit': 'pcs',
        'supplier': 'Global Tools Inc',
        'quantity': 14,
        'reorder_level': 4,
        'location': 'Aisle F2'
    },
    # Electrical
    {
        'name': 'Extension Cord 50ft',
        'sku': 'CAB-001',
        'description': '12 AWG outdoor extension cord',
        'category': 'Cables',
        'cost_price': 22.50,
        'sale_price': 34.99,
        'unit': 'pcs',
        'supplier': 'XYZ Distributors',
        'quantity': 28,
        'reorder_level': 8,
        'location': 'Aisle G1'
    },
    {
        'name': 'AA Alkaline Batteries (24 pack)',
        'sku': 'BAT-001',
        'description': 'High performance AA batteries',
        'category': 'Batteries',
        'cost_price': 8.99,
        'sale_price': 13.99,
        'unit': 'box',
        'supplier': 'ABC Suppliers',
        'quantity': 95,
        'reorder_level': 30,
        'location': 'Aisle G2'
    },
]

created_count = 0
for prod_data in products_data:
    try:
        # Get the subcategory
        subcat = SubCategory.objects.get(name=prod_data['category'])
        supplier = suppliers.get(prod_data['supplier'])
        
        # Create product
        product = Product.objects.create(
            productName=prod_data['name'],
            description=prod_data['description'],
            skuCode=prod_data['sku'],
            unit=prod_data['unit'],
            costPrice=Decimal(str(prod_data['cost_price'])),
            salePrice=Decimal(str(prod_data['sale_price'])),
            subcategory=subcat,
            source=supplier,
            status='Active'
        )
        
        # Create inventory record
        Inventory.objects.create(
            product=product,
            quantity=prod_data['quantity'],
            reorderLevel=prod_data['reorder_level'],
            location=prod_data['location']
        )
        
        print(f"✓ {product.productName} ({product.skuCode})")
        print(f"  └─ Qty: {prod_data['quantity']}, Cost: ${prod_data['cost_price']}, Sale: ${prod_data['sale_price']}")
        created_count += 1
    except Exception as e:
        print(f"✗ Error creating {prod_data['name']}: {e}")

print("\n" + "="*60)
print(f"✨ Successfully created {created_count} products with inventory!")
print("="*60)
