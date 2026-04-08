"""
Django management command to test image search functionality
Usage: python manage.py test_image_search
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test image search service health and functionality'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--health',
            action='store_true',
            help='Only test health check'
        )
        parser.add_argument(
            '--preload',
            action='store_true',
            help='Preload models'
        )
        parser.add_argument(
            '--index-all',
            action='store_true',
            help='Index all products with images'
        )
    
    def handle(self, *args, **options):
        """Handle the command"""
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("Image Search Service Test"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        
        # Test health
        if options['health'] or not any([options['preload'], options['index_all']]):
            self.test_health()
        
        # Preload models
        if options['preload']:
            self.preload_models()
        
        # Index all products
        if options['index_all']:
            self.index_all_products()
        
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
        self.stdout.write(self.style.SUCCESS("Test Complete"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
    
    def test_health(self):
        """Test image search health"""
        self.stdout.write("\n[1/3] Testing Image Search Health...")
        try:
            from api.image_search import get_service
            
            service = get_service()
            info = service.get_collection_info()
            
            self.stdout.write(self.style.SUCCESS("✓ Service initialized successfully"))
            self.stdout.write(f"  Collection: {info.get('name')}")
            self.stdout.write(f"  Vectors: {info.get('vectors_count')}")
            self.stdout.write(f"  Points: {info.get('points_count')}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Failed: {str(e)}"))
    
    def preload_models(self):
        """Preload YOLO and CLIP models"""
        self.stdout.write("\n[2/3] Preloading Models...")
        try:
            from django.conf import settings
            from api.image_search.model_loader import preload_models
            
            yolo_model = getattr(settings, 'IMAGE_SEARCH_YOLO_MODEL', 'yolov8n.pt')
            embedding_model = getattr(settings, 'IMAGE_SEARCH_EMBEDDING_MODEL', 'clip-ViT-B-32')
            
            results = preload_models(yolo_model, embedding_model)
            
            if results['yolo_success'] and results['clip_success']:
                self.stdout.write(self.style.SUCCESS("✓ All models preloaded successfully"))
            else:
                self.stdout.write(self.style.WARNING("⚠ Some models failed to load"))
                if not results['yolo_success']:
                    self.stdout.write(self.style.ERROR("  - YOLO failed"))
                if not results['clip_success']:
                    self.stdout.write(self.style.ERROR("  - CLIP failed"))
            
            self.stdout.write(f"  GPU Available: {results['gpu_available']}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Failed: {str(e)}"))
    
    def index_all_products(self):
        """Index all products with images"""
        self.stdout.write("\n[3/3] Batch Indexing Products...")
        try:
            from api.models import Product
            from api.image_search import get_service
            
            # Get products with images
            products = Product.objects.filter(image__isnull=False).exclude(image='')
            
            if not products.exists():
                self.stdout.write(self.style.WARNING("  No products with images found"))
                return
            
            service = get_service()
            batch_data = []
            
            for product in products:
                batch_data.append({
                    'product_id': product.productId,
                    'image_source': product.image,
                    'metadata': {
                        'product_name': product.productName,
                        'sku_code': product.skuCode,
                        'description': product.description,
                    }
                })
            
            self.stdout.write(f"  Indexing {len(batch_data)} products...")
            result = service.batch_index_products(batch_data)
            
            self.stdout.write(self.style.SUCCESS(f"✓ Batch indexing complete"))
            self.stdout.write(f"  Total: {result.get('total')}")
            self.stdout.write(f"  Successful: {result.get('successful')}")
            self.stdout.write(f"  Failed: {result.get('failed')}")
            
            if result.get('errors'):
                self.stdout.write(self.style.WARNING("\n  Errors:"))
                for error in result.get('errors', [])[:5]:  # Show first 5 errors
                    self.stdout.write(f"    - Product {error.get('product_id')}: {error.get('error')}")
                if len(result.get('errors', [])) > 5:
                    self.stdout.write(f"    ... and {len(result.get('errors')) - 5} more")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Failed: {str(e)}"))
