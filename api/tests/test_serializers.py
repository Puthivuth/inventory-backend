"""
Comprehensive tests for Django REST Framework serializers
Tests cover serializer validation, data transformation, and permissions
"""

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from decimal import Decimal
from api.models import (
    User, UserProfile, Category, SubCategory, Source, Product, Inventory,
    NewStock, Customer, Invoice, Purchase, Transaction, ActivityLog
)
from api.serializers import (
    UserSerializer, UserProfileSerializer, CategorySerializer,
    SubCategorySerializer, SourceSerializer, ProductSerializer,
    InventorySerializer, NewStockSerializer, CustomerSerializer,
    InvoiceSerializer, TransactionSerializer, ActivityLogSerializer
)


class UserSerializerTest(TestCase):
    """Test UserSerializer functionality"""
    
    def setUp(self):
        """Setup test data"""
        # Clean up existing users
        User.objects.filter(username__in=['testuser', 'admin', 'testmanager', 'staffuser']).delete()
        
        self.factory = APIRequestFactory()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'first_name': 'John',
            'last_name': 'Doe',
            'role': 'administrator'
        }
    
    def test_user_serializer_create(self):
        """Test user creation through serializer"""
        serializer = UserSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('password123'))
    
    def test_user_serializer_password_write_only(self):
        """Test password is not returned in response"""
        serializer = UserSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        response = UserSerializer(user).data
        self.assertNotIn('password', response)
    
    def test_user_serializer_validation_missing_password(self):
        """Test serializer validation fails without password"""
        invalid_data = self.user_data.copy()
        del invalid_data['password']
        serializer = UserSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
    
    def test_user_serializer_update(self):
        """Test user update through serializer"""
        user = User.objects.create_user(**self.user_data)
        update_data = {'first_name': 'Jane', 'password': 'newpass456'}
        serializer = UserSerializer(user, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        self.assertEqual(updated_user.first_name, 'Jane')
        self.assertTrue(updated_user.check_password('newpass456'))


class UserProfileSerializerTest(TestCase):
    """Test UserProfileSerializer"""
    
    def setUp(self):
        """Setup test data"""
        User.objects.filter(username='testuser').delete()
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.profile_data = {
            'user': self.user.id,
            'businessName': 'Test Business',
            'businessAddress': '123 Main St',
            'businessPhone': '5551234567',
            'businessEmail': 'business@example.com',
            'taxId': 'TAX123'
        }
    
    def test_profile_serializer_create(self):
        """Test profile creation"""
        serializer = UserProfileSerializer(data=self.profile_data)
        self.assertTrue(serializer.is_valid())
        profile = serializer.save()
        self.assertEqual(profile.businessName, 'Test Business')
    
    def test_profile_serializer_all_fields(self):
        """Test serializer includes all fields"""
        profile = UserProfile.objects.create(user=self.user, businessName='Business')
        serializer = UserProfileSerializer(profile)
        self.assertIn('profileId', serializer.data)
        self.assertIn('user', serializer.data)
        self.assertIn('businessName', serializer.data)


class CategorySerializerTest(TestCase):
    """Test CategorySerializer"""
    
    def test_category_serializer_create(self):
        """Test category creation"""
        data = {'name': 'Electronics'}
        serializer = CategorySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        category = serializer.save()
        self.assertEqual(category.name, 'Electronics')
    
    def test_category_serializer_fields(self):
        """Test serializer has required fields"""
        category = Category.objects.create(name='Electronics')
        serializer = CategorySerializer(category)
        self.assertIn('categoryId', serializer.data)
        self.assertIn('name', serializer.data)
        self.assertIn('createdAt', serializer.data)


class SubCategorySerializerTest(TestCase):
    """Test SubCategorySerializer"""
    
    def setUp(self):
        """Setup test data"""
        self.category = Category.objects.create(name='Electronics')
        self.subcategory_data = {
            'category': self.category.categoryId,
            'name': 'Phones'
        }
    
    def test_subcategory_serializer_create(self):
        """Test subcategory creation"""
        serializer = SubCategorySerializer(data=self.subcategory_data)
        self.assertTrue(serializer.is_valid())
        subcategory = serializer.save()
        self.assertEqual(subcategory.name, 'Phones')
        self.assertEqual(subcategory.category, self.category)


class SourceSerializerTest(TestCase):
    """Test SourceSerializer"""
    
    def test_source_serializer_create(self):
        """Test source creation"""
        data = {
            'name': 'Supplier A',
            'sourceUrl': 'https://supplier.com',
            'contactPerson': 'John',
            'phone': '5551234567',
            'email': 'supplier@example.com'
        }
        serializer = SourceSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        source = serializer.save()
        self.assertEqual(source.name, 'Supplier A')


class ProductSerializerTest(TestCase):
    """Test ProductSerializer"""
    
    def setUp(self):
        """Setup test data"""
        # Clean up existing users
        User.objects.filter(username__in=['staffuser', 'testmanager', 'admin']).delete()
        
        self.category = Category.objects.create(name='Electronics')
        self.subcategory = SubCategory.objects.create(
            category=self.category,
            name='Phones'
        )
        self.source = Source.objects.create(name='Supplier A')
        self.product_data = {
            'productName': 'Smartphone X',
            'description': 'Latest model',
            'skuCode': 'SMARTX001',
            'unit': 'pcs',
            'costPrice': '300.00',
            'salePrice': '500.00',
            'discount': '10.00',
            'subcategory': self.subcategory.subcategoryId,
            'source': self.source.sourceId,
            'status': 'Active'
        }
    
    def test_product_serializer_create(self):
        """Test product creation"""
        serializer = ProductSerializer(data=self.product_data)
        self.assertTrue(serializer.is_valid())
        product = serializer.save()
        self.assertEqual(product.productName, 'Smartphone X')
        self.assertEqual(product.costPrice, Decimal('300.00'))
    
    def test_product_serializer_cost_price_hidden_for_staff(self):
        """Test costPrice is hidden from staff users"""
        product = Product.objects.create(
            productName='Smartphone X',
            description='Latest',
            skuCode='SMARTX001',
            unit='pcs',
            costPrice=Decimal('300.00'),
            salePrice=Decimal('500.00'),
            subcategory=self.subcategory
        )
        
        # Create staff user
        staff_user = User.objects.create_user(
            username='staffuser',
            password='password123',
            role='staff'
        )
        
        # Create request with staff user
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = staff_user
        
        serializer = ProductSerializer(product, context={'request': request})
        # costPrice should not be in response for staff
        self.assertNotIn('costPrice', serializer.data)
    
    def test_product_serializer_cost_price_visible_for_manager(self):
        """Test costPrice is visible to managers"""
        product = Product.objects.create(
            productName='Smartphone X',
            description='Latest',
            skuCode='SMARTX001',
            unit='pcs',
            costPrice=Decimal('300.00'),
            salePrice=Decimal('500.00'),
            subcategory=self.subcategory
        )
        
        # Create manager user
        manager = User.objects.create_user(
            username='testmanager',
            password='password007',
            role='manager'
        )
        
        # Create request with manager user
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = manager
        
        # Ensure user is recognized as authenticated and role is correct
        self.assertTrue(request.user.is_authenticated)
        self.assertEqual(request.user.role, 'manager')
        
        serializer = ProductSerializer(product, context={'request': request})
        # costPrice should be in response for manager
        self.assertIn('costPrice', serializer.data)
        self.assertEqual(Decimal(serializer.data['costPrice']), Decimal('300.00'))


class InventorySerializerTest(TestCase):
    """Test InventorySerializer"""
    
    def setUp(self):
        """Setup test data"""
        self.category = Category.objects.create(name='Electronics')
        self.subcategory = SubCategory.objects.create(
            category=self.category,
            name='Phones'
        )
        self.product = Product.objects.create(
            productName='Smartphone X',
            description='Latest',
            skuCode='SMARTX001',
            unit='pcs',
            subcategory=self.subcategory
        )
        self.inventory_data = {
            'product': self.product.productId,
            'quantity': 100,
            'reorderLevel': 20,
            'location': 'Warehouse A'
        }
    
    def test_inventory_serializer_create(self):
        """Test inventory creation"""
        serializer = InventorySerializer(data=self.inventory_data)
        self.assertTrue(serializer.is_valid())
        inventory = serializer.save()
        self.assertEqual(inventory.quantity, 100)


class CustomerSerializerTest(TestCase):
    """Test CustomerSerializer"""
    
    def test_customer_serializer_create(self):
        """Test customer creation"""
        data = {
            'name': 'John Doe',
            'businessAddress': '123 Main St',
            'phone': '5551234567',
            'email': 'john@example.com',
            'customerType': 'Individual'
        }
        serializer = CustomerSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        customer = serializer.save()
        self.assertEqual(customer.name, 'John Doe')
        self.assertEqual(customer.customerType, 'Individual')


class InvoiceSerializerTest(TestCase):
    """Test InvoiceSerializer"""
    
    def setUp(self):
        """Setup test data"""
        User.objects.filter(username='seller').delete()
        self.user = User.objects.create_user(username='seller', password='password123')
        self.customer = Customer.objects.create(
            name='John Doe',
            businessAddress='123 Main St',
            phone='555',
            customerType='Individual'
        )
        # Create product and inventory for line items
        category = Category.objects.create(name='Electronics')
        subcategory = SubCategory.objects.create(name='Phones', category=category)
        source = Source.objects.create(name='Supplier')
        product = Product.objects.create(
            productName='Phone',
            skuCode='PHONE001',
            unit='pcs',
            costPrice=Decimal('300.00'),
            salePrice=Decimal('500.00'),
            subcategory=subcategory,
            source=source
        )
        Inventory.objects.create(product=product, quantity=100, reorderLevel=20)
        
        self.invoice_data = {
            'customer': self.customer.customerId,
            'customerName': 'John Doe',
            'paymentMethod': 'Cash',
            'lineItems': [
                {
                    'product': product.productId,
                    'quantity': 2,
                    'pricePerUnit': '500.00'
                }
            ],
            'taxPercentage': '5.00'
        }
    
    def test_invoice_serializer_create(self):
        """Test invoice creation"""
        serializer = InvoiceSerializer(data=self.invoice_data)
        if not serializer.is_valid():
            print("Serializer errors:", serializer.errors)
        self.assertTrue(serializer.is_valid())
        invoice = serializer.save(createdByUser=self.user)
        self.assertEqual(invoice.customerName, 'John Doe')
        # Verify purchases were created
        self.assertEqual(invoice.purchases.count(), 1)
        # Verify the total was calculated
        self.assertGreater(invoice.grandTotal, Decimal('0.00'))


class TransactionSerializerTest(TestCase):
    """Test TransactionSerializer"""
    
    def setUp(self):
        """Setup test data"""
        from django.utils import timezone
        User.objects.filter(username='cashier').delete()
        self.user = User.objects.create_user(username='cashier', password='password123')
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
        self.transaction_data = {
            'invoice': self.invoice.invoiceId,
            'customer': self.customer.customerId,
            'amountPaid': '950.00',
            'paymentMethod': 'Cash',
            'transactionStatus': 'Completed',
            'transactionDate': timezone.now().isoformat(),
            'recordedByUser': self.user.id
        }
    
    def test_transaction_serializer_create(self):
        """Test transaction creation"""
        serializer = TransactionSerializer(data=self.transaction_data)
        self.assertTrue(serializer.is_valid())
        transaction = serializer.save()
        self.assertEqual(transaction.amountPaid, Decimal('950.00'))
        self.assertEqual(transaction.transactionStatus, 'Completed')


class ActivityLogSerializerTest(TestCase):
    """Test ActivityLogSerializer"""
    
    def setUp(self):
        """Setup test data"""
        User.objects.filter(username='loguser').delete()
        self.user = User.objects.create_user(
            username='loguser',
            password='password123'
        )
        self.log_data = {
            'user': self.user.id,
            'actionType': 'USER_LOGIN',
            'description': 'User logged in successfully'
        }
    
    def test_activitylog_serializer_create(self):
        """Test activity log creation"""
        serializer = ActivityLogSerializer(data=self.log_data)
        self.assertTrue(serializer.is_valid())
        log = serializer.save()
        self.assertEqual(log.actionType, 'USER_LOGIN')
