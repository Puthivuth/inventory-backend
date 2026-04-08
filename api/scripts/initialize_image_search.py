"""
Script to initialize and populate the Qdrant vector database with product images.

Usage:
    python manage.py shell
    >>> from api.scripts.initialize_image_search import initialize_image_search, index_local_images
    >>> initialize_image_search()
    >>> index_local_images()
"""

import os
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from api.models import Product, Inventory
from api.image_search_service import index_product_image, initialize_qdrant, get_collection_info
import logging

logger = logging.getLogger(__name__)

# Path to images directory
IMAGES_DIR = os.path.join(settings.BASE_DIR, '..', 'Images')

def initialize_image_search():
    """Initialize the Qdrant vector database"""
    try:
        logger.info("Initializing Qdrant vector database...")
        client = initialize_qdrant()
        info = get_collection_info()
        if info:
            logger.info(f"✓ Qdrant initialized. Collection: {info['collection_name']}, Points: {info['points_count']}")
            return True
        return False
    except Exception as e:
        logger.error(f"✗ Failed to initialize Qdrant: {str(e)}")
        return False

def index_local_images():
    """
    Index all local images from the Images directory.
    Creates associations between images and products based on content matching.
    """
    try:
        if not os.path.exists(IMAGES_DIR):
            logger.error(f"✗ Images directory not found: {IMAGES_DIR}")
            return
        
        logger.info(f"Indexing images from: {IMAGES_DIR}")
        
        # Get all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        image_files = [f for f in os.listdir(IMAGES_DIR) 
                      if os.path.splitext(f)[1].lower() in image_extensions]
        
        logger.info(f"Found {len(image_files)} images to index")
        
        indexed_count = 0
        errors = []
        
        # Index each image with a unique ID based on filename
        for idx, image_file in enumerate(image_files, 1):
            try:
                image_path = os.path.join(IMAGES_DIR, image_file)
                image_name = os.path.splitext(image_file)[0]
                
                # Use index as product_id (ensuring uniqueness)
                product_id = 10000 + idx  # Offset to avoid collision with real product IDs
                
                # Try to find matching product by name or keywords
                product_name = image_name
                sku_code = image_file
                
                # Attempt to match with existing products
                matching_product = None
                try:
                    # Search for products with similar names
                    matching_products = Product.objects.filter(
                        productName__icontains=image_name
                    ) or Product.objects.filter(
                        description__icontains=image_name
                    )
                    if matching_products.exists():
                        matching_product = matching_products.first()
                        product_id = int(matching_product.productId)
                        product_name = matching_product.productName
                        sku_code = matching_product.skuCode
                except:
                    pass
                
                # Index the image
                success = index_product_image(
                    product_id=product_id,
                    image_url=image_path,
                    product_name=product_name,
                    sku_code=sku_code
                )
                
                if success:
                    indexed_count += 1
                    logger.info(f"  [{idx}/{len(image_files)}] ✓ Indexed: {image_file} (ID: {product_id})")
                else:
                    errors.append(f"Failed to index {image_file}")
                    logger.warning(f"  [{idx}/{len(image_files)}] ✗ Failed: {image_file}")
            
            except Exception as e:
                error_msg = f"Error indexing {image_file}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"  ✗ {error_msg}")
        
        # Print summary
        logger.info(f"\n{'='*60}")
        logger.info(f"Indexing Summary:")
        logger.info(f"  Total images: {len(image_files)}")
        logger.info(f"  Successfully indexed: {indexed_count}")
        logger.info(f"  Failed: {len(errors)}")
        
        if errors:
            logger.info(f"\nErrors:")
            for error in errors:
                logger.info(f"  - {error}")
        
        # Get final collection info
        info = get_collection_info()
        if info:
            logger.info(f"\nCollection Status:")
            logger.info(f"  Name: {info['collection_name']}")
            logger.info(f"  Vector size: {info['vector_size']}")
            logger.info(f"  Total points: {info['points_count']}")
        
        logger.info(f"{'='*60}")
    
    except Exception as e:
        logger.error(f"✗ Error indexing local images: {str(e)}")

def index_product_database_images():
    """
    Index all product images from the database.
    This indexes images that are already uploaded and stored in product records.
    """
    try:
        logger.info("Indexing product database images...")
        
        # Get all products with images
        products_with_images = Product.objects.exclude(image__isnull=True).exclude(image='')
        
        logger.info(f"Found {products_with_images.count()} products with images")
        
        indexed_count = 0
        errors = []
        
        for product in products_with_images:
            try:
                success = index_product_image(
                    product_id=int(product.productId),
                    image_url=product.image.url if hasattr(product.image, 'url') else str(product.image),
                    product_name=product.productName,
                    sku_code=product.skuCode
                )
                
                if success:
                    indexed_count += 1
                    logger.info(f"  ✓ Indexed: {product.productName} (ID: {product.productId})")
                else:
                    errors.append(f"Failed to index {product.productName}")
            
            except Exception as e:
                error_msg = f"Error indexing {product.productName}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"  ✗ {error_msg}")
        
        logger.info(f"\nProduct database indexing complete: {indexed_count}/{products_with_images.count()} indexed")
        
        if errors:
            logger.warning(f"Errors during indexing: {len(errors)}")
            for error in errors:
                logger.warning(f"  - {error}")
    
    except Exception as e:
        logger.error(f"✗ Error indexing product database images: {str(e)}")

# Django management command
class Command(BaseCommand):
    help = 'Initialize Qdrant vector database and index product images'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--local-only',
            action='store_true',
            help='Only index local image files'
        )
        parser.add_argument(
            '--database-only',
            action='store_true',
            help='Only index database product images'
        )
    
    def handle(self, *args, **options):
        try:
            # Initialize Qdrant
            if initialize_image_search():
                self.stdout.write(self.style.SUCCESS('✓ Qdrant initialized successfully'))
            else:
                self.stdout.write(self.style.ERROR('✗ Failed to initialize Qdrant'))
                return
            
            # Index images based on options
            if options['database_only']:
                index_product_database_images()
            elif options['local_only']:
                index_local_images()
            else:
                # Index both
                self.stdout.write('\n--- Indexing Local Images ---')
                index_local_images()
                self.stdout.write('\n--- Indexing Database Product Images ---')
                index_product_database_images()
            
            self.stdout.write(self.style.SUCCESS('\n✓ Image search initialization complete!'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}'))
