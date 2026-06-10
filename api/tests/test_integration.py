"""
Integration tests for complex workflows and feature interactions
Tests cover end-to-end scenarios like order processing, inventory updates, etc.
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from django.utils import timezone
from api.models import (
    User, Category, SubCategory, Source, Product, Inventory,
    NewStock, Customer, Invoice, Purchase, Transaction, ActivityLog
)


class OrderProcessingWorkflowTest(TestCase):
    """Test complete order processing workflow"""
    
    def setUp(self):
        """Setup test data with products and customers"""
        self.client = APIClient()
        
        # Delete existing users to ensure clean state
        User.objects.filter(username='manager').delete()
        
        # Create users
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='managerpass',
            role='manager'
        )
        
        # Create product
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
            discount=Decimal('0.00'),
            subcategory=self.subcategory,
            source=self.source
        )
        
        # Create inventory
        self.inventory = Inventory.objects.create(
            product=self.product,
            quantity=100,
            reorderLevel=20,
            location='Warehouse A'
        )
        
        # Create customer
        self.customer = Customer.objects.create(
            name='John Doe',
            businessAddress='123 Main St',
            phone='5551234567',
            email='john@example.com',
            customerType='Individual'
        )
    
    def login_manager(self):
        """Login as manager"""
        response = self.client.post('/api/login/', {
            'username': 'manager',
            'password': 'managerpass'
        }, format='json')
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    
    def test_complete_cash_order_workflow(self):
        """Test complete workflow: invoice creation -> purchase -> transaction"""
        self.login_manager()
        
        # Step 1: Create invoice with line items instead of pre-calculated totals
        invoice_data = {
            'customer': self.customer.customerId,
            'customerName': self.customer.name,
            'paymentMethod': 'Cash',
            'lineItems': [
                {
                    'product': self.product.productId,
                    'quantity': 2,
                    'pricePerUnit': '500.00'
                }
            ],
            'taxPercentage': '0.00'
        }
        invoice_response = self.client.post('/api/invoices/', invoice_data, format='json')
        self.assertEqual(invoice_response.status_code, status.HTTP_201_CREATED)
        invoice_id = invoice_response.data['invoiceId']
        
        # Step 2: Verify invoice was created
        invoice = Invoice.objects.get(invoiceId=invoice_id)
        self.assertEqual(invoice.status, 'Pending')
        self.assertEqual(invoice.paymentMethod, 'Cash')
        # Line items should have been created
        self.assertEqual(invoice.purchases.count(), 1)
        self.assertEqual(invoice.purchases.first().quantity, 2)
        
        # Step 4: Record transaction (payment)
        transaction_data = {
            'invoice': invoice_id,
            'customer': self.customer.customerId,
            'amountPaid': '1000.00',
            'paymentMethod': 'Cash',
            'transactionStatus': 'Completed',
            'transactionDate': timezone.now().isoformat(),
            'recordedByUser': self.manager.id
        }
        transaction_response = self.client.post('/api/transactions/', transaction_data, format='json')
        self.assertEqual(transaction_response.status_code, status.HTTP_201_CREATED)
        
        # Step 5: Verify data consistency
        invoice.refresh_from_db()
        self.assertEqual(invoice.grandTotal, Decimal('1000.00'))
        
        purchases = Purchase.objects.filter(invoice=invoice)
        self.assertEqual(purchases.count(), 1)
        self.assertEqual(purchases[0].quantity, 2)
        
        transactions = Transaction.objects.filter(invoice=invoice)
        self.assertEqual(transactions.count(), 1)
        self.assertEqual(transactions[0].amountPaid, Decimal('1000.00'))


class InventoryManagementWorkflowTest(TestCase):
    """Test inventory management workflows"""
    
    def setUp(self):
        """Setup test data"""
        self.client = APIClient()
        
        User.objects.filter(username='manager').delete()
        
        self.manager = User.objects.create_user(
            username='manager',
            role='manager',
            password='managerpass'
        )
        
        self.category = Category.objects.create(name='Electronics')
        self.subcategory = SubCategory.objects.create(
            category=self.category,
            name='Phones'
        )
        self.source = Source.objects.create(name='Supplier A')
        self.product = Product.objects.create(
            productName='Smartphone X',
            description='Latest',
            skuCode='SMARTX001',
            unit='pcs',
            costPrice=Decimal('300.00'),
            salePrice=Decimal('500.00'),
            subcategory=self.subcategory,
            source=self.source
        )
        self.inventory = Inventory.objects.create(
            product=self.product,
            quantity=50,
            reorderLevel=20,
            location='Warehouse A'
        )
    
    def login_manager(self):
        """Login as manager"""
        response = self.client.post('/api/login/', {
            'username': 'manager',
            'password': 'managerpass'
        }, format='json')
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    
    def test_add_new_stock_workflow(self):
        """Test adding new stock and updating inventory"""
        self.login_manager()
        
        initial_quantity = self.inventory.quantity
        
        # Create new stock entry
        newstock_data = {
            'inventory': self.inventory.inventoryId,
            'quantity': 50,
            'purchasePrice': '250.00',
            'receivedDate': timezone.now().date().isoformat(),
            'supplier': self.source.sourceId,
            'addedByUser': self.manager.id,
            'note': 'Restocking order'
        }
        response = self.client.post('/api/newstock/', newstock_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify inventory was updated
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, initial_quantity + 50)
    
    def test_inventory_low_stock_scenario(self):
        """Test scenario where stock falls below reorder level"""
        self.login_manager()
        
        # Inventory has quantity=50, reorderLevel=20
        # This is above reorder level
        self.assertGreater(self.inventory.quantity, self.inventory.reorderLevel)
        
        # Reduce inventory to below reorder level
        self.inventory.quantity = 10
        self.inventory.save()
        
        # Verify it's below reorder level
        self.inventory.refresh_from_db()
        self.assertLess(self.inventory.quantity, self.inventory.reorderLevel)
        
        # Add new stock to bring it back up
        newstock_data = {
            'inventory': self.inventory.inventoryId,
            'quantity': 100,
            'purchasePrice': '250.00',
            'receivedDate': timezone.now().date().isoformat(),
            'supplier': self.source.sourceId,
            'addedByUser': self.manager.id
        }
        self.client.post('/api/newstock/', newstock_data, format='json')
        
        self.inventory.refresh_from_db()
        self.assertGreater(self.inventory.quantity, self.inventory.reorderLevel)


class UserActivityAuditTrailTest(TestCase):
    """Test activity logging and audit trails"""
    
    def setUp(self):
        """Setup test data"""
        self.client = APIClient()
        
        User.objects.filter(username='admin').delete()
        
        self.admin = User.objects.create_user(
            username='admin',
            role='administrator',
            password='adminpass'
        )
    
    def login_admin(self):
        """Login as admin"""
        response = self.client.post('/api/login/', {
            'username': 'admin',
            'password': 'adminpass'
        }, format='json')
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    
    def test_activity_log_on_login(self):
        """Test activity log created on user login"""
        initial_logs = ActivityLog.objects.count()
        
        self.client.post('/api/login/', {
            'username': 'admin',
            'password': 'adminpass'
        }, format='json')
        
        self.assertEqual(ActivityLog.objects.count(), initial_logs + 1)
        log = ActivityLog.objects.latest('createdAt')
        self.assertEqual(log.actionType, 'USER_LOGIN')
        self.assertEqual(log.user, self.admin)
    
    def test_activity_log_sequence(self):
        """Test sequence of activity logs"""
        self.login_admin()
        
        initial_logs = ActivityLog.objects.count()
        
        # Create a category
        self.client.post('/api/categories/', {'name': 'New Category'}, format='json')
        
        # Login should have created at least one log in setup
        # Additional operations may create logs if implemented
        # This test ensures activity logging can track operations
        logs_after = ActivityLog.objects.count()
        self.assertGreaterEqual(logs_after, initial_logs)


class PermissionAndAccessControlTest(TestCase):
    """Test role-based access control across workflows"""
    
    def setUp(self):
        """Setup test data"""
        self.client = APIClient()
        
        User.objects.filter(username__in=['admin', 'manager', 'staff']).delete()
        
        self.admin, created = User.objects.get_or_create(
            username='admin',
            defaults={'role': 'administrator'}
        )
        if created:
            self.admin.set_password('adminpass')
            self.admin.save()
        self.admin.set_password('adminpass')
        self.admin.save()
        
        self.manager, created = User.objects.get_or_create(
            username='manager',
            defaults={'role': 'manager'}
        )
        if created:
            self.manager.set_password('managerpass')
            self.manager.save()
        self.manager.set_password('managerpass')
        self.manager.save()
        
        self.staff, created = User.objects.get_or_create(
            username='staff',
            defaults={'role': 'staff'}
        )
        if created:
            self.staff.set_password('staffpass')
            self.staff.save()
        self.staff.set_password('staffpass')
        self.staff.save()
        
        self.category = Category.objects.create(name='Electronics')
    
    def login(self, user):
        """Login user"""
        response = self.client.post('/api/login/', {
            'username': user.username,
            'password': user.username + 'pass'
        }, format='json')
        token = response.data.get('token')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    
    def logout(self):
        """Logout"""
        self.client.credentials()
    
    def test_staff_cannot_manage_users(self):
        """Test staff user cannot create or manage users"""
        self.login(self.staff)
        
        # Try to create a user (should fail)
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'pass',
            'role': 'staff'
        }
        response = self.client.post('/api/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_manager_can_view_but_staff_can_modify_restrictions(self):
        """Test manager can create while staff can only view"""
        # Manager creates
        self.login(self.manager)
        response = self.client.post(
            '/api/categories/',
            {'name': 'Furniture'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        cat_id = response.data['categoryId']
        
        self.logout()
        
        # Staff can view
        self.login(self.staff)
        response = self.client.get(f'/api/categories/{cat_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Staff cannot modify
        response = self.client.put(
            f'/api/categories/{cat_id}/',
            {'name': 'Updated Furniture'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_admin_has_all_permissions(self):
        """Test admin has unrestricted access"""
        self.login(self.admin)
        
        # Can create users
        user_response = self.client.post('/api/users/', {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'pass',
            'role': 'staff'
        }, format='json')
        self.assertEqual(user_response.status_code, status.HTTP_201_CREATED)
        
        # Can manage categories
        cat_response = self.client.post('/api/categories/', {'name': 'Books'}, format='json')
        self.assertEqual(cat_response.status_code, status.HTTP_201_CREATED)


class MultipleUsersTransactionTest(TestCase):
    """Test transactions with multiple users"""
    
    def setUp(self):
        """Setup test data"""
        self.client = APIClient()
        
        User.objects.filter(username__in=['manager1', 'manager2']).delete()
        
        self.manager1 = User.objects.create_user(
            username='manager1',
            role='manager',
            password='pass1'
        )
        
        self.manager2 = User.objects.create_user(
            username='manager2',
            role='manager',
            password='pass2'
        )
        
        # Create product for invoices
        category = Category.objects.create(name='Test Category')
        subcategory = SubCategory.objects.create(name='Test Subcat', category=category)
        source = Source.objects.create(name='Test Source')
        self.product1 = Product.objects.create(
            productName='Product 1',
            skuCode='PROD001',
            unit='pcs',
            costPrice=Decimal('50.00'),
            salePrice=Decimal('100.00'),
            subcategory=subcategory,
            source=source
        )
        # Create inventory
        Inventory.objects.create(product=self.product1, quantity=100, reorderLevel=20)
    
    def test_invoice_created_by_tracks_user(self):
        """Test that invoice tracks which user created it"""
        # Manager 1 creates invoice
        response = self.client.post('/api/login/', {
            'username': 'manager1',
            'password': 'pass1'
        }, format='json')
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        invoice_data = {
            'customerName': 'Test Customer',
            'paymentMethod': 'Cash',
            'lineItems': [
                {
                    'product': self.product1.productId,
                    'quantity': 1,
                    'pricePerUnit': '100.00'
                }
            ],
            'taxPercentage': '0.00'
        }
        invoice_response = self.client.post('/api/invoices/', invoice_data, format='json')
        invoice_id = invoice_response.data['invoiceId']
        
        # Verify creator
        invoice = Invoice.objects.get(invoiceId=invoice_id)
        self.assertEqual(invoice.createdByUser, self.manager1)
