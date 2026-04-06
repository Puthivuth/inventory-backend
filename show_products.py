import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import Product

print("All products in database:")
products = Product.objects.select_related('subcategory').all()
for p in products:
    subcat_name = p.subcategory.name if p.subcategory else "None"
    print(f"  Product ID {p.productId}: {p.productName} -> {subcat_name}")
