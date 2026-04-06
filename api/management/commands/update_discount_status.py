from django.core.management.base import BaseCommand
from api.models import Product


class Command(BaseCommand):
    help = 'Update all products with discount > 0 to have status="Discount"'

    def handle(self, *args, **options):
        # Get all products with discount > 0 and status != 'Discount'
        products_to_update = Product.objects.filter(
            discount__gt=0
        ).exclude(status='Discount')
        
        count = products_to_update.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('No products need updating - all discounted products already have "Discount" status')
            )
            return
        
        # Update each product (this will trigger the save() method)
        for product in products_to_update:
            old_status = product.status
            product.save()  # This triggers the save() method which sets status='Discount'
            self.stdout.write(
                f'Updated: {product.productName} (SKU: {product.skuCode}) - Status changed from "{old_status}" to "Discount"'
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully updated {count} product(s) with discount status!')
        )
