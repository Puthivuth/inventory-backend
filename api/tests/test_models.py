"""
Comprehensive tests for all Django models in the API application
Tests cover model creation, validation, relationships, and string representations
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from datetime import date, datetime
from api.models import (
    User, UserProfile, Category, SubCategory, Source, Product, Inventory,
    NewStock, Customer, Invoice, Purchase, Transaction, ActivityLog
)


class UserModelTest(TestCase):
    """Test User (custom AbstractUser model) functionality"""
    
    def setUp(self):
        """Create test user"""
        # Delete if exists to ensure clean state
        User.objects.filter(username='testuser').delete()
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='administrator'
        )
    
    def test_user_creation(self):
        """Test user is created with correct fields"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.role, 'administrator')
        self.assertTrue(self.user.is_active)
    
    def test_user_role_choices(self):
        """Test all user role choices work correctly"""
        roles = ['administrator', 'manager', 'staff']
        for role in roles:
            user = User.objects.create_user(
                username=f'user_{role}',
                email=f'{role}@example.com',
                password='pass',
                role=role
            )
            self.assertEqual(user.role, role)
    
    def test_user_string_representation(self):
        """Test User __str__ method"""
        expected = f"testuser (administrator)"
        self.assertEqual(str(self.user), expected)
    
    def test_user_password_hashing(self):
        """Test that password is hashed, not stored in plain text"""
        self.assertNotEqual(self.user.password, 'testpass123')
        self.assertTrue(self.user.check_password('testpass123'))


class UserProfileModelTest(TestCase):
    """Test UserProfile model functionality"""
    
    def setUp(self):
        """Create test user and profile"""
        self.user = User.objects.create_user(
            username='profileuser',
            email='profile@example.com',
            password='pass'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            businessName='Test Business',
            businessAddress='123 Test St',
            businessPhone='8555551234',
            businessEmail='business@example.com',
            taxId='TAX123'
        )
    
    def test_profile_creation(self):
        """Test profile is created with correct fields"""
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.businessName, 'Test Business')
        self.assertEqual(self.profile.businessPhone, '8555551234')
    
    def test_profile_one_to_one_relationship(self):
        """Test one-to-one relationship between User and UserProfile"""
        self.assertEqual(self.user.profile, self.profile)
    
    def test_profile_string_representation(self):
        """Test UserProfile __str__ method"""
        expected = f"Profile of {self.user.username}"
        self.assertEqual(str(self.profile), expected)
    
    def test_profile_auto_update_timestamp(self):
        """Test that updatedAt auto-updates"""
        first_update = self.profile.updatedAt
        import time
        time.sleep(0.01)  # Small delay to ensure timestamp difference
        self.profile.businessName = 'Updated Business'
        self.profile.save()
        self.profile.refresh_from_db()
        self.assertGreaterEqual(self.profile.updatedAt, first_update)


class CategoryModelTest(TestCase):
    """Test Category model functionality"""
    
    def test_category_creation(self):
        """Test category is created correctly"""
        category = Category.objects.create(name='Electronics')
        self.assertEqual(category.name, 'Electronics')
        self.assertIsNotNone(category.createdAt)
    
    def test_category_string_representation(self):
        """Test Category __str__ method"""
        category = Category.objects.create(name='Electronics')
        self.assertEqual(str(category), 'Electronics')


class SubCategoryModelTest(TestCase):
    """Test SubCategory model functionality"""
    
    def setUp(self):
        """Create test category and subcategory"""
        self.category = Category.objects.create(name='Electronics')
        self.subcategory = SubCategory.objects.create(
            category=self.category,
            name='Phones'
        )
    
    def test_subcategory_creation(self):
        """Test subcategory is created with correct fields"""
        self.assertEqual(self.subcategory.name, 'Phones')
        self.assertEqual(self.subcategory.category, self.category)
    
    def test_subcategory_foreign_key(self):
        """Test FK relationship with Category"""
        self.assertEqual(self.subcategory.category.name, 'Electronics')
    
    def test_subcategory_string_representation(self):
        """Test SubCategory __str__ method includes category name"""
        expected = f"Phones → Electronics"
        self.assertEqual(str(self.subcategory), expected)


class SourceModelTest(TestCase):
    """Test Source (supplier) model functionality"""
    
    def test_source_creation(self):
        """Test source is created with all fields"""
        source = Source.objects.create(
            name='Supplier A',
            sourceUrl='https://supplier.com',
            contactPerson='John Doe',
            phone='8555551234',
            email='contact@supplier.com',
            address='456 Supplier Way'
        )
        self.assertEqual(source.name, 'Supplier A')
        self.assertEqual(source.contactPerson, 'John Doe')
    
    def test_source_string_representation(self):
        """Test Source __str__ method"""
        source = Source.objects.create(name='Supplier A')
        self.assertEqual(str(source), 'Supplier A')


class ProductModelTest(TestCase):
    """Test Product model functionality"""
    
    def setUp(self):
        """Create test category, subcategory, source, and product"""
        self.category = Category.objects.create(name='Electronics')
        self.subcategory = SubCategory.objects.create(category=self.category, name='Phones')
        self.source = Source.objects.create(name='Supplier A')
        self.product = Product.objects.create(
            productName='Smartphone X',
            description='Latest model smartphone',
            skuCode='SMARTX001',
            unit='pcs',
            costPrice=Decimal('300.00'),
            salePrice=Decimal('500.00'),
            discount=Decimal('10.00'),
            subcategory=self.subcategory,
            source=self.source
        )
    
    def test_product_creation(self):
        """Test product is created correctly"""
        self.assertEqual(self.product.productName, 'Smartphone X')
        self.assertEqual(self.product.costPrice, Decimal('300.00'))
        self.assertEqual(self.product.salePrice, Decimal('500.00'))
    
    def test_product_sku_unique(self):
        """Test SKU code is unique"""
        with self.assertRaises(Exception):  # IntegrityError
            Product.objects.create(
                productName='Different Phone',
                description='Another phone',
                skuCode='SMARTX001',
                unit='pcs',
                subcategory=self.subcategory
            )
    
    def test_product_status_choices(self):
        """Test product status choices work correctly"""
        statuses = ['Active', 'Inactive', 'Discontinued']
        for status in statuses:
            product = Product.objects.create(
                productName=f'Product {status}',
                description='Test',
                skuCode=f'SKU{status}',
                unit='pcs',
                subcategory=self.subcategory,
                status=status
            )
            self.assertEqual(product.status, status)
    
    def test_product_string_representation(self):
        """Test Product __str__ method"""
        expected = f"Smartphone X (SMARTX001)"
        self.assertEqual(str(self.product), expected)


class InventoryModelTest(TestCase):
    """Test Inventory model functionality"""
    
    def setUp(self):
        """Create test product and inventory"""
        self.category = Category.objects.create(name='Electronics')
        self.subcategory = SubCategory.objects.create(category=self.category, name='Phones')
        self.product = Product.objects.create(
            productName='Smartphone X',
            description='Latest model',
            skuCode='SMARTX001',
            unit='pcs',
            subcategory=self.subcategory
        )
        self.inventory = Inventory.objects.create(
            product=self.product,
            quantity=100,
            reorderLevel=20,
            location='Warehouse A'
        )
    
    def test_inventory_creation(self):
        """Test inventory is created correctly"""
        self.assertEqual(self.inventory.quantity, 100)
        self.assertEqual(self.inventory.reorderLevel, 20)
        self.assertEqual(self.inventory.location, 'Warehouse A')
    
    def test_inventory_quantity_update(self):
        """Test inventory quantity can be updated"""
        self.inventory.quantity = 75
        self.inventory.save()
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 75)
    
    def test_inventory_string_representation(self):
        """Test Inventory __str__ method"""
        expected = f"Smartphone X @ Warehouse A — 100 units"
        self.assertEqual(str(self.inventory), expected)


class NewStockModelTest(TestCase):
    """Test NewStock (stock receiving) model functionality"""
    
    def setUp(self):
        """Create test data for NewStock"""
        self.user = User.objects.create_user(username='stockuser', password='pass')
        self.category = Category.objects.create(name='Electronics')
        self.subcategory = SubCategory.objects.create(category=self.category, name='Phones')
        self.product = Product.objects.create(
            productName='Smartphone X',
            description='Latest',
            skuCode='SMARTX001',
            unit='pcs',
            subcategory=self.subcategory
        )
        self.inventory = Inventory.objects.create(
            product=self.product,
            quantity=100,
            reorderLevel=20,
            location='Warehouse A'
        )
        self.source = Source.objects.create(name='Supplier A')
        self.newstock = NewStock.objects.create(
            inventory=self.inventory,
            quantity=50,
            purchasePrice=Decimal('250.00'),
            receivedDate=date.today(),
            supplier=self.source,
            addedByUser=self.user
        )
    
    def test_newstock_creation(self):
        """Test new stock entry is created correctly"""
        self.assertEqual(self.newstock.quantity, 50)
        self.assertEqual(self.newstock.purchasePrice, Decimal('250.00'))
    
    def test_newstock_string_representation(self):
        """Test NewStock __str__ method"""
        expected = f"Stock +50 → Smartphone X on {date.today()}"
        self.assertEqual(str(self.newstock), expected)


class CustomerModelTest(TestCase):
    """Test Customer model functionality"""
    
    def test_customer_creation(self):
        """Test customer is created correctly"""
        customer = Customer.objects.create(
            name='John Doe',
            businessAddress='123 Main St',
            phone='8551234567',
            email='john@example.com',
            customerType='Individual'
        )
        self.assertEqual(customer.name, 'John Doe')
        self.assertEqual(customer.customerType, 'Individual')
    
    def test_customer_type_choices(self):
        """Test customer type choices work correctly"""
        types = ['Individual', 'Business']
        for ctype in types:
            customer = Customer.objects.create(
                name=f'Customer {ctype}',
                businessAddress='Test',
                phone='5551234567',
                customerType=ctype
            )
            self.assertEqual(customer.customerType, ctype)
    
    def test_customer_string_representation(self):
        """Test Customer __str__ method"""
        customer = Customer.objects.create(
            name='John Doe',
            businessAddress='123 Main St',
            phone='555',
            customerType='Individual'
        )
        expected = f"John Doe (Individual)"
        self.assertEqual(str(customer), expected)


class InvoiceModelTest(TestCase):
    """Test Invoice model functionality"""
    
    def setUp(self):
        """Create test data for Invoice"""
        self.user = User.objects.create_user(username='seller', password='pass')
        self.customer = Customer.objects.create(
            name='John Doe',
            businessAddress='123 Main St',
            phone='555',
            customerType='Individual'
        )
        self.invoice = Invoice.objects.create(
            customer=self.customer,
            customerName='John Doe',
            createdByUser=self.user,
            totalBeforeDiscount=Decimal('1000.00'),
            discount=Decimal('100.00'),
            tax=Decimal('50.00'),
            grandTotal=Decimal('950.00'),
            paymentMethod='Cash'
        )
    
    def test_invoice_creation(self):
        """Test invoice is created correctly"""
        self.assertEqual(self.invoice.customerName, 'John Doe')
        self.assertEqual(self.invoice.grandTotal, Decimal('950.00'))
        self.assertEqual(self.invoice.status, 'Pending')
    
    def test_invoice_payment_method_choices(self):
        """Test payment method choices"""
        methods = ['Cash', 'KHQR']
        for method in methods:
            invoice = Invoice.objects.create(
                customerName='Test',
                totalBeforeDiscount=Decimal('100'),
                grandTotal=Decimal('100'),
                paymentMethod=method,
                createdByUser=self.user
            )
            self.assertEqual(invoice.paymentMethod, method)
    
    def test_invoice_status_choices(self):
        """Test invoice status choices"""
        statuses = ['Pending', 'Paid', 'Cancelled']
        for status in statuses:
            invoice = Invoice.objects.create(
                customerName='Test',
                totalBeforeDiscount=Decimal('100'),
                grandTotal=Decimal('100'),
                paymentMethod='Cash',
                status=status,
                createdByUser=self.user
            )
            self.assertEqual(invoice.status, status)
    
    def test_invoice_string_representation(self):
        """Test Invoice __str__ method"""
        expected = f"Invoice {self.invoice.invoiceNumber} — John Doe — Pending"
        self.assertEqual(str(self.invoice), expected)
    
    def test_invoice_khqr_fields(self):
        """Test KHQR-specific fields"""
        self.assertIsNone(self.invoice.khqrCodeString)
        self.assertIsNone(self.invoice.khqrMd5)
        self.assertEqual(self.invoice.paymentMethod, 'Cash')


class PurchaseModelTest(TestCase):
    """Test Purchase (invoice line item) model functionality"""
    
    def setUp(self):
        """Create test data for Purchase"""
        self.user = User.objects.create_user(username='seller', password='pass')
        self.category = Category.objects.create(name='Electronics')
        self.subcategory = SubCategory.objects.create(category=self.category, name='Phones')
        self.product = Product.objects.create(
            productName='Smartphone X',
            description='Latest',
            skuCode='SMARTX001',
            unit='pcs',
            salePrice=Decimal('500.00'),
            subcategory=self.subcategory
        )
        self.invoice = Invoice.objects.create(
            customerName='John Doe',
            totalBeforeDiscount=Decimal('1000.00'),
            grandTotal=Decimal('950.00'),
            paymentMethod='Cash',
            createdByUser=self.user
        )
        self.purchase = Purchase.objects.create(
            invoice=self.invoice,
            product=self.product,
            quantity=2,
            pricePerUnit=Decimal('500.00'),
            discount=Decimal('0.00'),
            subtotal=Decimal('1000.00')
        )
    
    def test_purchase_creation(self):
        """Test purchase is created correctly"""
        self.assertEqual(self.purchase.quantity, 2)
        self.assertEqual(self.purchase.pricePerUnit, Decimal('500.00'))
        self.assertEqual(self.purchase.subtotal, Decimal('1000.00'))
    
    def test_purchase_string_representation(self):
        """Test Purchase __str__ method"""
        expected = f"2 × Smartphone X → Invoice #{self.invoice.invoiceId}"
        self.assertEqual(str(self.purchase), expected)


class TransactionModelTest(TestCase):
    """Test Transaction (payment) model functionality"""
    
    def setUp(self):
        """Create test data for Transaction"""
        self.user = User.objects.create_user(username='cashier', password='pass')
        self.customer = Customer.objects.create(
            name='John Doe',
            businessAddress='123 Main St',
            phone='555',
            customerType='Individual'
        )
        self.invoice = Invoice.objects.create(
            customer=self.customer,
            customerName='John Doe',
            totalBeforeDiscount=Decimal('1000.00'),
            grandTotal=Decimal('950.00'),
            paymentMethod='Cash',
            createdByUser=self.user
        )
        self.transaction = Transaction.objects.create(
            invoice=self.invoice,
            customer=self.customer,
            amountPaid=Decimal('950.00'),
            paymentMethod='Cash',
            transactionStatus='Completed',
            transactionDate=timezone.now(),
            recordedByUser=self.user
        )
    
    def test_transaction_creation(self):
        """Test transaction is created correctly"""
        self.assertEqual(self.transaction.amountPaid, Decimal('950.00'))
        self.assertEqual(self.transaction.transactionStatus, 'Completed')
    
    def test_transaction_method_choices(self):
        """Test payment method choices"""
        methods = ['Cash', 'Card', 'KHQR', 'BankTransfer', 'Other']
        for method in methods:
            txn = Transaction.objects.create(
                invoice=self.invoice,
                customer=self.customer,
                amountPaid=Decimal('100'),
                paymentMethod=method,
                transactionStatus='Completed',
                transactionDate=timezone.now(),
                recordedByUser=self.user
            )
            self.assertEqual(txn.paymentMethod, method)
    
    def test_transaction_status_choices(self):
        """Test transaction status choices"""
        statuses = ['Pending', 'Completed', 'Failed', 'Refunded']
        for status in statuses:
            txn = Transaction.objects.create(
                invoice=self.invoice,
                customer=self.customer,
                amountPaid=Decimal('100'),
                paymentMethod='Cash',
                transactionStatus=status,
                transactionDate=timezone.now(),
                recordedByUser=self.user
            )
            self.assertEqual(txn.transactionStatus, status)
    
    def test_transaction_string_representation(self):
        """Test Transaction __str__ method"""
        expected = f"Txn #{self.transaction.transactionId} — Completed ({self.transaction.amountPaid})"
        self.assertEqual(str(self.transaction), expected)


class ActivityLogModelTest(TestCase):
    """Test ActivityLog model functionality"""
    
    def setUp(self):
        """Create test activity log"""
        self.user, created = User.objects.get_or_create(
            username='testuser'
        )
        if created:
            self.user.set_password('pass')
            self.user.save()
        self.log = ActivityLog.objects.create(
            user=self.user,
            actionType='USER_LOGIN',
            description='User logged in successfully'
        )
    
    def test_activity_log_creation(self):
        """Test activity log is created correctly"""
        self.assertEqual(self.log.actionType, 'USER_LOGIN')
        self.assertEqual(self.log.user, self.user)
    
    def test_activity_log_string_representation(self):
        """Test ActivityLog __str__ method"""
        expected = f"USER_LOGIN by testuser"
        self.assertEqual(str(self.log), expected)
    
    def test_activity_log_timestamp(self):
        """Test activity log auto-creates timestamp"""
        self.assertIsNotNone(self.log.createdAt)
