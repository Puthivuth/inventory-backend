from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Invoice, Product, ProductAssociation, Purchase
from collections import defaultdict
from itertools import combinations
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Runs Apriori-based product association analysis on historical invoice data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-support',
            type=int,
            default=2,
            help='Minimum number of times products must appear together (default: 2)'
        )
        parser.add_argument(
            '--min-confidence',
            type=float,
            default=1.0,
            help='Minimum confidence percentage for an association (default: 1.0)'
        )

    def handle(self, *args, **options):
        min_support = options['min_support']
        min_confidence = options['min_confidence']

        self.stdout.write(f"Starting product association analysis (min_support={min_support}, min_confidence={min_confidence}%)...")

        # 1. Fetch relevant invoices and their products
        # We only care about Paid or Pending invoices that have at least 2 products
        valid_invoices = Invoice.objects.filter(status__in=['Paid', 'Pending']).prefetch_related('purchases')
        
        transactions = []
        product_counts = defaultdict(int)
        
        for invoice in valid_invoices:
            # Get unique products in this invoice
            products = list(set(Purchase.objects.filter(invoice=invoice, product__isnull=False).values_list('product_id', flat=True)))
            
            if len(products) >= 1:
                transactions.append(products)
                for pid in products:
                    product_counts[pid] += 1

        total_transactions = len(transactions)
        self.stdout.write(f"Processing {total_transactions} transactions with {len(product_counts)} unique products.")

        if total_transactions == 0:
            self.stdout.write(self.style.WARNING("No valid transactions found. Exiting."))
            return

        # 2. Count frequent pairs (Apriori Step for k=2)
        pair_counts = defaultdict(int)
        for txn in transactions:
            if len(txn) < 2:
                continue
            # Sort to ensure (A, B) is same as (B, A) for counting
            txn.sort()
            for pair in combinations(txn, 2):
                pair_counts[pair] += 1

        # 3. Filter pairs by min_support
        frequent_pairs = {pair: count for pair, count in pair_counts.items() if count >= min_support}
        self.stdout.write(f"Found {len(frequent_pairs)} frequent pairs meeting min_support={min_support}.")

        # 4. Generate Association Rules and prepare for bulk creation
        new_associations = []
        processed_pairs = 0

        with transaction.atomic():
            # Clear existing associations to rebuild
            ProductAssociation.objects.all().delete()

            for (p1_id, p2_id), frequency in frequent_pairs.items():
                # Rule: p1 -> p2
                conf1 = (frequency / product_counts[p1_id]) * 100
                if conf1 >= min_confidence:
                    new_associations.append(ProductAssociation(
                        product1_id=p1_id,
                        product2_id=p2_id,
                        frequency=frequency,
                        totalProduct1Purchases=product_counts[p1_id],
                        associationPercentage=round(min(conf1, 100.0), 2)
                    ))

                # Rule: p2 -> p1
                conf2 = (frequency / product_counts[p2_id]) * 100
                if conf2 >= min_confidence:
                    new_associations.append(ProductAssociation(
                        product1_id=p2_id,
                        product2_id=p1_id,
                        frequency=frequency,
                        totalProduct1Purchases=product_counts[p2_id],
                        associationPercentage=round(min(conf2, 100.0), 2)
                    ))
                
                processed_pairs += 1
                if len(new_associations) >= 1000:
                    ProductAssociation.objects.bulk_create(new_associations)
                    new_associations = []

            # Final bulk create
            if new_associations:
                ProductAssociation.objects.bulk_create(new_associations)

        self.stdout.write(self.style.SUCCESS(f"Successfully updated Product Associations. Processed {processed_pairs} pairs."))
