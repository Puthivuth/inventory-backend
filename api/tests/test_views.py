"""
Comprehensive API endpoint tests for all ViewSets
Tests cover CRUD operations, permissions, filtering, and custom actions
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from api.models import (
    User, Category, SubCategory, Source, Product, Inventory,
    NewStock, Customer, Invoice, Purchase, Transaction, ActivityLog
)


class APITestBase(TestCase):
    """Base test class with common setup"""
    
    def setUp(self):
        """Setup test client and users with different roles"""
        self.client = APIClient()
        
        # Delete users if they exist to ensure clean state
        User.objects.filter(username__in=['admin', 'manager', 'staff']).delete()
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='administrator'
        )
        
        # Create manager user
        self.manager_user = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='manager123',
            role='manager'
        )
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='staff123',
            role='staff'
        )
    
    def login(self, user):
        """Helper to login a user"""
        response = self.client.post('/api/login/', {
            'username': user.username,
            'password': user.username + '123'  # Password pattern from setUp
        }, format='json')
        if response.status_code == 200:
            token = response.data.get('token')
            self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        return response
    
    def logout(self):
        """Helper to logout"""
        self.client.credentials()


class UserViewSetTest(APITestBase):
    """Test User CRUD endpoints"""
    
    def test_list_users_admin(self):
        """Test admin can list all users"""
        self.login(self.admin_user)
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check data is list or paginated
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertGreaterEqual(len(response.data['results']), 3)
        else:
            self.assertGreaterEqual(len(response.data), 3)
    
    def test_list_users_unauthenticated(self):
        """Test unauthenticated user cannot list users"""
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_user_admin(self):
        """Test admin can create user"""
        self.login(self.admin_user)
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'role': 'manager'
        }
        response = self.client.post('/api/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'newuser')
    
    def test_create_user_staff_forbidden(self):
        """Test staff user cannot create other users"""
        self.login(self.staff_user)
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newuser123',
            'role': 'staff'
        }
        response = self.client.post('/api/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CategoryViewSetTest(APITestBase):
    """Test Category CRUD endpoints"""
    
    def setUp(self):
        """Setup with test data"""
        super().setUp()
        self.category = Category.objects.create(name='Electronics')
    
    def test_list_categories(self):
        """Test listing categories"""
        self.login(self.staff_user)
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check data is list or paginated
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertGreater(len(response.data['results']), 0)
        else:
            self.assertGreater(len(response.data), 0)
    
    def test_create_category_manager(self):
        """Test manager can create category"""
        self.login(self.manager_user)
        data = {'name': 'New Category'}
        response = self.client.post('/api/categories/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_create_category_staff_forbidden(self):
        """Test staff cannot create category"""
        self.login(self.staff_user)
        data = {'name': 'New Category'}
        response = self.client.post('/api/categories/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_retrieve_category(self):
        """Test retrieving single category"""
        self.login(self.staff_user)
        response = self.client.get(f'/api/categories/{self.category.categoryId}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Electronics')
    
    def test_update_category_manager(self):
        """Test manager can update category"""
        self.login(self.manager_user)
        data = {'name': 'Updated Electronics'}
        response = self.client.put(
            f'/api/categories/{self.category.categoryId}/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'Updated Electronics')
    
    def test_delete_category_manager(self):
        """Test manager can delete category"""
        self.login(self.manager_user)
        response = self.client.delete(f'/api/categories/{self.category.categoryId}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(categoryId=self.category.categoryId).exists())


class ProductViewSetTest(APITestBase):
    """Test Product CRUD endpoints"""
    
    def setUp(self):
        """Setup with test data"""
        super().setUp()
        self.category = Category.objects.create(name='Electronics')
        self.subcategory = SubCategory.objects.create(
            category=self.category,
            name='Phones'
        )
        self.source = Source.objects.create(name='Supplier A')
        self.product = Product.objects.create(
            productName='Smartphone X',
            description='Latest model',
            skuCode='SMARTX001',
            unit='pcs',
            costPrice=Decimal('300.00'),
            salePrice=Decimal('500.00'),
            subcategory=self.subcategory,
            source=self.source
        )
    
    def test_list_products(self):
        """Test listing products"""
        self.login(self.staff_user)
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check data is list or paginated
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertGreater(len(response.data['results']), 0)
        else:
            self.assertGreater(len(response.data), 0)
    
    def test_create_product_manager(self):
        """Test manager can create product"""
        self.login(self.manager_user)
        data = {
            'productName': 'Laptop',
            'description': 'Gaming laptop',
            'skuCode': 'LAPTOP001',
            'unit': 'pcs',
            'costPrice': '800.00',
            'salePrice': '1200.00',
            'subcategory': self.subcategory.subcategoryId,
            'source': self.source.sourceId
        }
        response = self.client.post('/api/products/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_retrieve_product_staff(self):
        """Test staff can retrieve product"""
        self.login(self.staff_user)
        response = self.client.get(f'/api/products/{self.product.productId}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['productName'], 'Smartphone X')
    
    def test_product_cost_price_hidden_from_staff(self):
        """Test cost price is hidden from staff"""
        self.login(self.staff_user)
        response = self.client.get(f'/api/products/{self.product.productId}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('costPrice', response.data)
    
    def test_product_cost_price_visible_to_manager(self):
        """Test cost price is visible to manager"""
        self.login(self.manager_user)
        response = self.client.get(f'/api/products/{self.product.productId}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('costPrice', response.data)


class InventoryViewSetTest(APITestBase):
    """Test Inventory endpoints"""
    
    def setUp(self):
        """Setup with test data"""
        super().setUp()
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
        self.inventory = Inventory.objects.create(
            product=self.product,
            quantity=100,
            reorderLevel=20,
            location='Warehouse A'
        )
    
    def test_list_inventory(self):
        """Test listing inventory"""
        self.login(self.staff_user)
        response = self.client.get('/api/inventory/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_update_inventory_manager(self):
        """Test manager can update inventory"""
        self.login(self.manager_user)
        data = {
            'product': self.product.productId,
            'quantity': 150,
            'reorderLevel': 25,
            'location': 'Warehouse B'
        }
        response = self.client.put(
            f'/api/inventory/{self.inventory.inventoryId}/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 150)


class CustomerViewSetTest(APITestBase):
    """Test Customer endpoints"""
    
    def setUp(self):
        """Setup with test data"""
        super().setUp()
        self.customer = Customer.objects.create(
            name='John Doe',
            businessAddress='123 Main St',
            phone='5551234567',
            customerType='Individual'
        )
    
    def test_list_customers(self):
        """Test listing customers"""
        self.login(self.staff_user)
        response = self.client.get('/api/customers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_customer_manager(self):
        """Test manager can create customer"""
        self.login(self.manager_user)
        data = {
            'name': 'Jane Smith',
            'businessAddress': '456 Oak Ave',
            'phone': '5559876543',
            'customerType': 'Business'
        }
        response = self.client.post('/api/customers/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_retrieve_customer(self):
        """Test retrieving single customer"""
        self.login(self.staff_user)
        response = self.client.get(f'/api/customers/{self.customer.customerId}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'John Doe')


class InvoiceViewSetTest(APITestBase):
    """Test Invoice endpoints"""
    
    def setUp(self):
        """Setup with test data"""
        super().setUp()
        self.customer = Customer.objects.create(
            name='John Doe',
            businessAddress='123 Main St',
            phone='555',
            customerType='Individual'
        )
        # Add product and inventory for invoice line items
        self.category = Category.objects.create(name='Electronics')
        self.subcategory = SubCategory.objects.create(name='Phones', category=self.category)
        self.source = Source.objects.create(name='Supplier A')
        self.product = Product.objects.create(
            productName='Smartphone',
            skuCode='PHONE001',
            unit='pcs',
            costPrice=Decimal('300.00'),
            salePrice=Decimal('500.00'),
            subcategory=self.subcategory,
            source=self.source
        )
        # Create inventory for the product
        Inventory.objects.create(product=self.product, quantity=100, reorderLevel=20)
        
        # Create KHQR invoice for mark_as_paid testing
        self.invoice = Invoice.objects.create(
            customer=self.customer,
            customerName='John Doe',
            totalBeforeDiscount=Decimal('1000.00'),
            discount=Decimal('100.00'),
            grandTotal=Decimal('900.00'),
            paymentMethod='KHQR',  # Use KHQR for mark_as_paid test
            createdByUser=self.admin_user
        )
    
    def test_list_invoices(self):
        """Test listing invoices"""
        self.login(self.staff_user)
        response = self.client.get('/api/invoices/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_invoice_manager(self):
        """Test manager can create invoice"""
        self.login(self.manager_user)
        data = {
            'customer': self.customer.customerId,
            'customerName': 'Jane Doe',
            'paymentMethod': 'Cash',
            'lineItems': [
                {
                    'product': self.product.productId,
                    'quantity': 2,
                    'pricePerUnit': '250.00'
                }
            ],
            'taxPercentage': '10.00'
        }
        response = self.client.post('/api/invoices/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_retrieve_invoice(self):
        """Test retrieving single invoice"""
        self.login(self.staff_user)
        response = self.client.get(f'/api/invoices/{self.invoice.invoiceId}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['customerName'], 'John Doe')
    
    def test_mark_invoice_as_paid(self):
        """Test marking invoice as paid"""
        self.login(self.manager_user)
        response = self.client.post(
            f'/api/invoices/{self.invoice.invoiceId}/mark_as_paid/',
            {},
            format='json'
        )
        # Should work for Cash invoices too
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TransactionViewSetTest(APITestBase):
    """Test Transaction endpoints"""
    
    def setUp(self):
        """Setup with test data"""
        super().setUp()
        from django.utils import timezone
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
            grandTotal=Decimal('1000.00'),
            paymentMethod='Cash',
            createdByUser=self.admin_user
        )
        self.transaction = Transaction.objects.create(
            invoice=self.invoice,
            customer=self.customer,
            amountPaid=Decimal('1000.00'),
            paymentMethod='Cash',
            transactionStatus='Completed',
            transactionDate=timezone.now(),
            recordedByUser=self.admin_user
        )
    
    def test_list_transactions(self):
        """Test listing transactions"""
        self.login(self.staff_user)
        response = self.client.get('/api/transactions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_retrieve_transaction(self):
        """Test retrieving single transaction"""
        self.login(self.staff_user)
        response = self.client.get(f'/api/transactions/{self.transaction.transactionId}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['transactionStatus'], 'Completed')


class ActivityLogViewSetTest(APITestBase):
    """Test ActivityLog endpoints"""
    
    def setUp(self):
        """Setup with test data"""
        super().setUp()
        self.log = ActivityLog.objects.create(
            user=self.admin_user,
            actionType='USER_LOGIN',
            description='User logged in'
        )
    
    def test_list_logs_admin(self):
        """Test admin can list activity logs"""
        self.login(self.admin_user)
        response = self.client.get('/api/activitylogs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_list_logs_staff_forbidden(self):
        """Test staff cannot list activity logs"""
        self.login(self.staff_user)
        response = self.client.get('/api/activitylogs/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
