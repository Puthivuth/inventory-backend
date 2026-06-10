"""
Pytest configuration and shared fixtures for all tests
Provides common test utilities and database fixtures
"""

import pytest
from django.contrib.auth.models import User as DjangoUser
from api.models import (
    User, Category, SubCategory, Source, Product, Inventory,
    NewStock, Customer, Invoice, Purchase, Transaction, ActivityLog
)
from rest_framework.test import APIClient
from decimal import Decimal
from django.utils import timezone


@pytest.fixture
def api_client():
    """Provide API client for requests"""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Create and return admin user"""
    return User.objects.create_user(
        username='admin',
        email='admin@example.com',
        password='adminpass',
        role='administrator'
    )


@pytest.fixture
def manager_user(db):
    """Create and return manager user"""
    return User.objects.create_user(
        username='manager',
        email='manager@example.com',
        password='managerpass',
        role='manager'
    )


@pytest.fixture
def staff_user(db):
    """Create and return staff user"""
    return User.objects.create_user(
        username='staff',
        email='staff@example.com',
        password='staffpass',
        role='staff'
    )


@pytest.fixture
def authenticated_client(api_client, admin_user):
    """Provide API client authenticated as admin"""
    client = api_client
    response = client.post('/api/login/', {
        'username': 'admin',
        'password': 'adminpass'
    }, format='json')
    token = response.data['token']
    client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    return client


@pytest.fixture
def category(db):
    """Create and return test category"""
    return Category.objects.create(name='Electronics')


@pytest.fixture
def subcategory(db, category):
    """Create and return test subcategory"""
    return SubCategory.objects.create(category=category, name='Phones')


@pytest.fixture
def source(db):
    """Create and return test source/supplier"""
    return Source.objects.create(name='Supplier A')


@pytest.fixture
def product(db, subcategory, source):
    """Create and return test product"""
    return Product.objects.create(
        productName='Smartphone X',
        description='Latest model smartphone',
        skuCode='SMARTX001',
        unit='pcs',
        costPrice=Decimal('300.00'),
        salePrice=Decimal('500.00'),
        discount=Decimal('0.00'),
        subcategory=subcategory,
        source=source
    )


@pytest.fixture
def inventory(db, product):
    """Create and return test inventory"""
    return Inventory.objects.create(
        product=product,
        quantity=100,
        reorderLevel=20,
        location='Warehouse A'
    )


@pytest.fixture
def customer(db):
    """Create and return test customer"""
    return Customer.objects.create(
        name='John Doe',
        businessAddress='123 Main St',
        phone='5551234567',
        email='john@example.com',
        customerType='Individual'
    )


@pytest.fixture
def invoice(db, customer, admin_user):
    """Create and return test invoice"""
    return Invoice.objects.create(
        customer=customer,
        customerName=customer.name,
        totalBeforeDiscount=Decimal('1000.00'),
        discount=Decimal('100.00'),
        tax=Decimal('0.00'),
        grandTotal=Decimal('900.00'),
        paymentMethod='Cash',
        createdByUser=admin_user
    )


@pytest.fixture
def authenticated_manager_client(api_client, manager_user):
    """Provide API client authenticated as manager"""
    client = api_client
    response = client.post('/api/login/', {
        'username': 'manager',
        'password': 'managerpass'
    }, format='json')
    token = response.data['token']
    client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    return client


@pytest.fixture
def authenticated_staff_client(api_client, staff_user):
    """Provide API client authenticated as staff"""
    client = api_client
    response = client.post('/api/login/', {
        'username': 'staff',
        'password': 'staffpass'
    }, format='json')
    token = response.data['token']
    client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    return client


# Database setup
@pytest.fixture(scope='session')
def django_db_setup():
    """Override Django test database setup"""
    pass


# Custom markers
def pytest_configure(config):
    """Register custom pytest markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as authentication related"
    )
    config.addinivalue_line(
        "markers", "api: mark test as API endpoint test"
    )
