"""
Management command to index all product images from inventory into Qdrant vector database
"""
from django.core.management.base import BaseCommand
from api.models import Product, Inventory
from api.image_search_service import index_product_image, initialize_qdrant
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Index all product images from inventory into Qdrant vector database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Clear existing Qdrant collection before indexing",
        )

    def handle(self, *args, **options):
        try:
            # Initialize Qdrant (will reset if --reset flag is set)
            if options.get("reset"):
                from qdrant_client.models import Distance, VectorParams
                client = initialize_qdrant()
                collection_name = "product_images"
                
                # Recreate collection
                try:
                    client.delete_collection(collection_name=collection_name)
                except:
                    pass
                
                client.recreate_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=512, distance=Distance.COSINE),
                )
                self.stdout.write(self.style.SUCCESS("✓ Cleared and recreated Qdrant collection"))
            else:
                client = initialize_qdrant()
                self.stdout.write(self.style.SUCCESS("✓ Qdrant initialized"))

            # Get all products from inventory
            products = Product.objects.filter(image__isnull=False).exclude(image="")
            
            if not products.exists():
                self.stdout.write(self.style.WARNING("⚠ No products with images found in inventory"))
                return

            total = products.count()
            self.stdout.write(f"\nIndexing {total} product(s) from inventory...\n")

            indexed = 0
            failed = 0

            for idx, product in enumerate(products, 1):
                try:
                    if not product.image:
                        self.stdout.write(f"  [{idx}/{total}] ⊘ Skipped: {product.productName} (no image)")
                        continue

                    # Index the product
                    success = index_product_image(
                        product_id=product.productId,
                        image_url=product.image,
                        product_name=product.productName,
                        sku_code=product.skuCode if hasattr(product, 'skuCode') else "",
                    )

                    if success:
                        self.stdout.write(
                            self.style.SUCCESS(f"  [{idx}/{total}] ✓ {product.productName}")
                        )
                        indexed += 1
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"  [{idx}/{total}] ✗ Failed: {product.productName}")
                        )
                        failed += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"  [{idx}/{total}] ✗ Error: {product.productName} - {str(e)}")
                    )
                    failed += 1

            self.stdout.write("\n" + "=" * 70)
            self.stdout.write(self.style.SUCCESS(f"✓ Indexing complete!"))
            self.stdout.write(f"  ✓ Indexed: {indexed}")
            self.stdout.write(f"  ✗ Failed: {failed}")
            self.stdout.write(f"  Total: {total}")
            self.stdout.write("=" * 70)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error during indexing: {str(e)}")
            )
            import traceback
            traceback.print_exc()
