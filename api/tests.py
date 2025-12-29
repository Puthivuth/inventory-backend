from django.test import TestCase
from .models import User, Category, SubCategory, Source, Product, Inventory, Purchase, Customer, Invoice
from decimal import Decimal
from datetime import datetime

class InventoryUpdateTest(TestCase):

    def setUp(self):
        # Create a user
        self.user = User.objects.create(
            name='Test User',
            email='test@example.com',
            passwordHash='hashedpassword',
            role='Admin'
        )

        # Create a category
        self.category = Category.objects.create(
            name='Electronics',
            description='Electronic devices'
        )

        # Create a subcategory
        self.subcategory = SubCategory.objects.create(
            category=self.category,
            name='Phones',
            description='Mobile phones'
        )

        # Create a source
        self.source = Source.objects.create(
            name='Supplier A',
            email='supplier@example.com'
        )

        # Create a product
        self.product = Product.objects.create(
            productName='Smartphone X',
            description='Latest model smartphone',
            skuCode='SMARTX001',
            unit='pcs',
            subcategory=self.subcategory,
            source=self.source
        )

        # Create an initial inventory record
        self.initial_quantity = 100
        self.inventory = Inventory.objects.create(
            product=self.product,
            quantity=self.initial_quantity,
            costPrice=Decimal('500.00'),
            reorderLevel=20,
            location='Warehouse A'
        )

        # Create a customer
        self.customer = Customer.objects.create(
            name='Test Customer',
            businessAddress='123 Test St',
            phone='123-456-7890',
            email='customer@example.com',
            customerType='Individual'
        )

        # Create an invoice
        self.invoice = Invoice.objects.create(
            customer=self.customer,
            createdByUser=self.user,
            totalBeforeDiscount=Decimal('1000.00'),
            discount=Decimal('0.00'),
            tax=Decimal('0.00'),
            grandTotal=Decimal('1000.00'),
            paymentMethod='Cash',
            invoiceDate=datetime.now(),
            status='Draft'
        )

    def test_inventory_decreases_on_purchase(self):
        # Define purchase quantity
        purchase_quantity = 10

        # Create a purchase
        Purchase.objects.create(
            invoice=self.invoice,
            product=self.product,
            quantity=purchase_quantity,
            pricePerUnit=Decimal('600.00'),
            discount=Decimal('0.00'),
            subtotal=Decimal('6000.00')
        )

        # Refresh the inventory instance from the database to get the updated quantity
        self.inventory.refresh_from_db()

        # Assert that the inventory quantity has decreased correctly
        expected_quantity = self.initial_quantity - purchase_quantity
        self.assertEqual(self.inventory.quantity, expected_quantity)

    def test_inventory_not_affected_by_non_purchase_save(self):
        # Change a field on the inventory directly and save, ensure no signal trigger
        original_quantity = self.inventory.quantity
        self.inventory.location = 'Warehouse B'
        self.inventory.save()
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, original_quantity)

        # Create a purchase, but then update it (should not trigger signal again)
        purchase = Purchase.objects.create(
            invoice=self.invoice,
            product=self.product,
            quantity=5,
            pricePerUnit=Decimal('600.00'),
            discount=Decimal('0.00'),
            subtotal=Decimal('3000.00')
        )
        self.inventory.refresh_from_db()
        quantity_after_first_purchase = self.inventory.quantity

        purchase.quantity = 7 # Update the purchase quantity
        purchase.save()
        self.inventory.refresh_from_db()
        # The quantity should not change again because the signal only fires on `created=True`
        self.assertEqual(self.inventory.quantity, quantity_after_first_purchase)