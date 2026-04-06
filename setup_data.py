import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import Category, SubCategory, Product

# Create categories if they don't exist
general_category, _ = Category.objects.get_or_create(name="General")

# Create subcategories
subcategories = [
    ("Drink", general_category),
    ("Bread", general_category),
    ("Racing Car", general_category),
]

subcategory_map = {}
for subcategory_name, category in subcategories:
    subcat, _ = SubCategory.objects.get_or_create(
        name=subcategory_name,
        defaults={"category": category}
    )
    subcategory_map[subcategory_name] = subcat
    print(f"✓ Subcategory created/found: {subcategory_name} (ID: {subcat.subcategoryId})")

# Assign subcategories to products
# Product 1 -> Drink, Product 2 -> Bread, Product 4 -> Racing Car
product_assignments = [
    (1, "Drink"),
    (2, "Bread"),
    (4, "Racing Car"),
]

for product_id, subcategory_name in product_assignments:
    try:
        product = Product.objects.get(productId=product_id)
        product.subcategory = subcategory_map[subcategory_name]
        product.save()
        print(f"✓ Product {product_id} ({product.productName}) assigned to {subcategory_name}")
    except Product.DoesNotExist:
        print(f"✗ Product {product_id} not found")

print("\n✓ Data setup complete!")

# Show all products with their subcategories
print("\nAll products and their subcategories:")
products = Product.objects.select_related('subcategory').all()
for product in products:
    subcat_name = product.subcategory.name if product.subcategory else "None"
    print(f"  Product {product.productId}: {product.productName} -> {subcat_name}")
