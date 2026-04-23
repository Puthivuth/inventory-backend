"""
Management command to fix image search issues:
- Removes lock files
- Clears and reinitializes Qdrant collection
- Re-indexes products from database

Usage:
    python manage.py fix_image_search            # Safe cleanup
    python manage.py fix_image_search --hard     # Hard reset (clears all data)
    python manage.py fix_image_search --index    # Just re-index products
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import shutil
import time
import glob


class Command(BaseCommand):
    help = 'Fix image search issues by cleaning up lock files and reinitializing Qdrant'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hard',
            action='store_true',
            help='Perform a hard reset (clears all Qdrant data)'
        )
        parser.add_argument(
            '--index',
            action='store_true',
            help='Only re-index products without clearing data'
        )

    def handle(self, *args, **options):
        QDRANT_PATH = os.path.join(settings.BASE_DIR, "qdrant_storage")
        
        try:
            if options['hard']:
                self.stdout.write(self.style.WARNING('Performing HARD RESET...'))
                self._hard_reset(QDRANT_PATH)
            elif options['index']:
                self.stdout.write('Re-indexing products...')
                self._reindex_products()
            else:
                self.stdout.write('Performing safe cleanup...')
                self._safe_cleanup(QDRANT_PATH)
            
            self.stdout.write(self.style.SUCCESS('✓ Image search has been fixed!'))
            self.stdout.write(self.style.SUCCESS('✓ Restart your server: python manage.py runserver'))
            
        except Exception as e:
            raise CommandError(f'Error fixing image search: {str(e)}')

    def _safe_cleanup(self, qdrant_path):
        """Remove lock files safely"""
        self.stdout.write('Removing lock files...')
        
        # Remove main lock file
        lock_file = os.path.join(qdrant_path, ".lock")
        if os.path.exists(lock_file):
            os.remove(lock_file)
            self.stdout.write(f'  ✓ Removed {lock_file}')
        
        # Remove any other lock files
        lock_patterns = [
            os.path.join(qdrant_path, "*.lock"),
            os.path.join(qdrant_path, "**/*.lock"),
        ]
        for pattern in lock_patterns:
            for lock_file in glob.glob(pattern, recursive=True):
                try:
                    os.remove(lock_file)
                    self.stdout.write(f'  ✓ Removed {lock_file}')
                except Exception as e:
                    self.stdout.write(f'  ⚠ Could not remove {lock_file}: {e}')
        
        time.sleep(1)
        self.stdout.write(self.style.SUCCESS('✓ Lock files cleaned'))

    def _hard_reset(self, qdrant_path):
        """Completely reset Qdrant database"""
        if os.path.exists(qdrant_path):
            self.stdout.write(f'Removing entire Qdrant storage at {qdrant_path}')
            try:
                shutil.rmtree(qdrant_path)
                self.stdout.write(self.style.SUCCESS('✓ Qdrant storage cleared'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Warning: Could not remove directory: {e}'))
        
        time.sleep(1)
        
        # Reinitialize
        self.stdout.write('Reinitializing Qdrant...')
        try:
            from api.image_search_service import initialize_qdrant
            initialize_qdrant(auto_index=True)
            self.stdout.write(self.style.SUCCESS('✓ Qdrant reinitialized and auto-indexed'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Warning during reinitialization: {e}'))

    def _reindex_products(self):
        """Re-index all products with images"""
        try:
            from api.models import Product
            from api.image_search_service import initialize_qdrant, index_product_image
            
            # Initialize first
            client = initialize_qdrant(auto_index=False)
            
            # Clear the collection
            try:
                from qdrant_client.models import Distance, VectorParams
                COLLECTION_NAME = "product_images"
                VECTOR_SIZE = 512
                
                client.recreate_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
                )
                self.stdout.write('✓ Collection cleared')
            except Exception as e:
                self.stdout.write(f'  Info: {e}')
            
            # Re-index all products
            products = Product.objects.filter(image__isnull=False).exclude(image="")
            count = 0
            
            self.stdout.write(f'Found {products.count()} products to index...')
            
            for product in products:
                try:
                    if index_product_image(
                        product.productId,
                        product.image,
                        product.productName,
                        product.skuCode
                    ):
                        count += 1
                        self.stdout.write(f'  ✓ {product.productName}')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  ✗ {product.productName}: {e}'))
            
            self.stdout.write(self.style.SUCCESS(f'✓ Re-indexed {count} products'))
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Warning: {e}'))
