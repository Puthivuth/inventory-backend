from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Category, SubCategory, Source, Product, Inventory, Purchase, Customer, Invoice
from decimal import Decimal
from datetime import datetime

User = get_user_model()  # ensures your custom user model is used

class InventoryUpdateTest(TestCase):

    def setUp(self):
        # Create a user using the proper Django method
        self.user = User.objects.create_user(
            email='test@example.com',  # or username if your model uses that
            password='TestPassword123!',
            role='Admin'
        )

        # The rest of your setup remains the same...
        self.category = Category.objects.create(
            name='Electronics',
            description='Electronic devices'
        )

        self.subcategory = SubCategory.objects.create(
            category=self.category,
            name='Phones',
            description='Mobile phones'
        )

        self.source = Source.objects.create(
            name='Supplier A',
            email='supplier@example.com'
        )

        self.product = Product.objects.create(
            productName='Smartphone X',
            description='Latest model smartphone',
            skuCode='SMARTX001',
            unit='pcs',
            subcategory=self.subcategory,
            source=self.source
        )

        self.initial_quantity = 100
        self.inventory = Inventory.objects.create(
            product=self.product,
            quantity=self.initial_quantity,
            costPrice=Decimal('500.00'),
            reorderLevel=20,
            location='Warehouse A'
        )

        self.customer = Customer.objects.create(
            name='Test Customer',
            businessAddress='123 Test St',
            phone='123-456-7890',
            email='customer@example.com',
            customerType='Individual'
        )

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
