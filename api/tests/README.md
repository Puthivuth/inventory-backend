# Inventory Backend - Comprehensive Test Suite

This directory contains a complete test suite for the inventory management backend API.

## Test Structure Overview

```
api/tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest configuration and shared fixtures
├── test_models.py              # Model unit tests (13 test classes)
├── test_serializers.py         # Serializer validation tests (13 test classes)
├── test_permissions.py         # Permission and access control tests (5 test classes)
├── test_authentication.py       # Login/Register endpoint tests (4 test classes)
├── test_views.py               # API endpoint tests (11 test classes)
└── test_integration.py          # End-to-end workflow tests (4 test classes)
```

## Test Coverage by Component

### 1. Model Tests (`test_models.py`)
Tests for all Django models with data validation and relationships.

**Model Test Classes:**
- `UserModelTest` - Custom user model with roles
- `UserProfileModelTest` - User profile and one-to-one relationships
- `CategoryModelTest` - Product categories
- `SubCategoryModelTest` - Sub-categories and FK relationships
- `SourceModelTest` - Supplier/source management
- `ProductModelTest` - Product creation and SKU uniqueness
- `InventoryModelTest` - Inventory quantity and location tracking
- `NewStockModelTest` - Stock receiving and additions
- `CustomerModelTest` - Customer management
- `InvoiceModelTest` - Invoice creation and KHQR fields
- `PurchaseModelTest` - Purchase/invoice line items
- `TransactionModelTest` - Payment transactions
- `ActivityLogModelTest` - Activity audit logs

**Total Tests:** ~50 unit tests

### 2. Serializer Tests (`test_serializers.py`)
Tests for DRF serializers including validation and permissions.

**Serializer Test Classes:**
- `UserSerializerTest` - User creation, password handling, updates
- `UserProfileSerializerTest` - Profile serialization
- `CategorySerializerTest` - Category serialization
- `SubCategorySerializerTest` - Sub-category serialization
- `SourceSerializerTest` - Source serialization
- `ProductSerializerTest` - Product serialization with cost-price visibility rules
- `InventorySerializerTest` - Inventory serialization
- `CustomerSerializerTest` - Customer serialization
- `InvoiceSerializerTest` - Invoice serialization
- `TransactionSerializerTest` - Transaction serialization
- `ActivityLogSerializerTest` - Activity log serialization

**Total Tests:** ~20 tests

### 3. Permission Tests (`test_permissions.py`)
Tests for role-based access control (RBAC).

**Permission Classes Tested:**
- `IsAdmin` - Administrator-only access
- `IsManager` - Manager-only access
- `IsStaff` - Staff-only access
- `IsAdminOrManager` - Admin or Manager access
- `IsManagerOrReadOnly` - Write for managers, read for all authenticated users

**Total Tests:** ~20 tests covering:
- Admin access
- Manager access
- Staff access
- Read-only restrictions
- Unauthenticated user restrictions

### 4. Authentication Tests (`test_authentication.py`)
Tests for login and registration endpoints.

**Test Classes:**
- `LoginViewTest` - Login functionality
  - Successful login with token
  - Invalid credentials
  - Non-existent user
  - Missing fields
  - Activity logging
  - Token persistence
  - Role in response

- `RegisterViewTest` - Registration functionality
  - Successful registration
  - Default staff role
  - Duplicate username prevention
  - Duplicate email prevention
  - Missing field validation
  - Activity logging
  - Token creation

- `AuthenticationIntegrationTest` - Auth workflows
  - Register and login workflow
  - Token usage in authenticated requests

**Total Tests:** ~25 tests

### 5. API Endpoint Tests (`test_views.py`)
Tests for all ViewSet endpoints (CRUD operations).

**ViewSet Test Classes:**
- `UserViewSetTest` - User CRUD endpoints
- `CategoryViewSetTest` - Category CRUD endpoints
- `ProductViewSetTest` - Product CRUD endpoints
- `InventoryViewSetTest` - Inventory endpoints
- `CustomerViewSetTest` - Customer endpoints
- `InvoiceViewSetTest` - Invoice endpoints
- `TransactionViewSetTest` - Transaction endpoints
- `ActivityLogViewSetTest` - Activity log endpoints

**Features Tested:**
- List endpoints
- Create endpoints (with role-based permissions)
- Retrieve single resource
- Update endpoints
- Delete endpoints
- Cost price visibility rules
- Permission enforcement
- Response structure

**Total Tests:** ~30 tests

### 6. Integration Tests (`test_integration.py`)
End-to-end workflow tests for complex scenarios.

**Test Classes:**
- `OrderProcessingWorkflowTest` - Complete order workflow:
  - Invoice creation
  - Purchase/line item addition
  - Transaction/payment recording
  - Data consistency verification

- `InventoryManagementWorkflowTest` - Stock management:
  - Adding new stock
  - Inventory quantity updates
  - Reorder level scenarios

- `UserActivityAuditTrailTest` - Activity logging:
  - Login activity tracking
  - Activity log sequences

- `PermissionAndAccessControlTest` - RBAC workflows:
  - Role-based restrictions
  - Multi-user scenarios
  - Permission enforcement

- `MultipleUsersTransactionTest` - User tracking:
  - Invoice creator tracking
  - Multi-user operations

**Total Tests:** ~20 tests

## Test Fixtures (conftest.py)

Common pytest fixtures available for all tests:

**User Fixtures:**
- `admin_user` - Admin user
- `manager_user` - Manager user
- `staff_user` - Staff user

**API Client Fixtures:**
- `api_client` - Unauthenticated API client
- `authenticated_client` - Client authenticated as admin
- `authenticated_manager_client` - Client authenticated as manager
- `authenticated_staff_client` - Client authenticated as staff

**Data Fixtures:**
- `category` - Test category
- `subcategory` - Test subcategory
- `source` - Test supplier/source
- `product` - Test product
- `inventory` - Test inventory
- `customer` - Test customer
- `invoice` - Test invoice

## Running the Tests

### Run All Tests
```bash
# Using Django test runner
python manage.py test api.tests

# Using pytest
pytest api/tests/

# Using pytest with verbose output
pytest api/tests/ -v
```

### Run Specific Test Modules
```bash
# Model tests only
python manage.py test api.tests.test_models
pytest api/tests/test_models.py

# API endpoint tests only
python manage.py test api.tests.test_views
pytest api/tests/test_views.py

# Authentication tests only
python manage.py test api.tests.test_authentication
pytest api/tests/test_authentication.py

# Integration tests only
python manage.py test api.tests.test_integration
pytest api/tests/test_integration.py
```

### Run Specific Test Class
```bash
# Django test runner
python manage.py test api.tests.test_models.UserModelTest

# Pytest
pytest api/tests/test_models.py::UserModelTest -v
```

### Run Specific Test Method
```bash
# Django test runner
python manage.py test api.tests.test_models.UserModelTest.test_user_creation

# Pytest
pytest api/tests/test_models.py::UserModelTest::test_user_creation -v
```

### Run Tests with Coverage
```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run --source='api' manage.py test api.tests
coverage report
coverage html  # Generate HTML report
```

### Run Tests by Marker (Pytest)
```bash
# Run only unit tests
pytest api/tests/ -m unit

# Run only integration tests
pytest api/tests/ -m integration

# Run authentication tests
pytest api/tests/ -m auth

# Run API tests
pytest api/tests/ -m api

# Skip slow tests
pytest api/tests/ -m "not slow"
```

## Test Statistics

### Total Test Coverage:
- **Unit Tests:** ~130 tests
- **Integration Tests:** ~20 tests
- **Total:** ~150+ tests

### Models Covered (13):
- User, UserProfile
- Category, SubCategory
- Source, Product
- Inventory, NewStock
- Customer, Invoice
- Purchase, Transaction, ActivityLog

### ViewSets Covered (13):
- UserViewSet
- UserProfileViewSet
- CategoryViewSet, SubCategoryViewSet
- SourceViewSet, ProductViewSet
- InventoryViewSet, NewStockViewSet
- CustomerViewSet, InvoiceViewSet
- PurchaseViewSet
- TransactionViewSet, ActivityLogViewSet

### Endpoints Covered:
- 5 authentication endpoints (login, register)
- 40+ REST API endpoints (CRUD for each ViewSet)
- 3+ custom actions (generate_khqr, check_payment, mark_as_paid, batch_check_payments)

### Permission Classes Tested (5):
- IsAdmin
- IsManager
- IsStaff
- IsAdminOrManager
- IsManagerOrReadOnly

## Key Testing Areas

### 1. Model Validation
- Field validation
- Unique constraints
- Foreign key relationships
- Choice fields
- Auto-generated fields (timestamps, IDs)

### 2. Serialization
- Data transformation
- Input validation
- Permission-based field visibility
- Read-only fields
- Nested serializers

### 3. Authentication
- User login
- User registration
- Token generation
- Activity logging
- Password hashing

### 4. Authorization
- Role-based access control
- Permission enforcement
- View-level permissions
- Method-level permissions
- Read-only access

### 5. API Endpoints
- CRUD operations
- List filtering
- Pagination
- Custom actions
- Response formats

### 6. Workflows
- Order processing
- Inventory management
- Payment tracking
- Activity auditing
- Multi-user scenarios

## Best Practices

### Writing New Tests
1. Use descriptive test names: `test_<what>_<scenario>`
2. Follow Arrange-Act-Assert pattern
3. Use fixtures for common setup
4. Keep tests focused and isolated
5. Test both success and failure cases

### Test Data
- Use fixtures from `conftest.py`
- Create minimal test data needed
- Use DRF test utilities for API testing
- Clean up after tests (automatic with Django TestCase)

### Assertions
- Be specific: `assertEqual` vs `assertTrue`
- Test edge cases
- Verify side effects (logs, database changes)
- Check response status codes
- Validate response data structure

## Troubleshooting

### Database Issues
```bash
# Reset test database
python manage.py migrate --run-syncdb
```

### Import Errors
```bash
# Ensure DJANGO_SETTINGS_MODULE is set
export DJANGO_SETTINGS_MODULE=core.settings.development
```

### Authentication Failures
- Verify password matches fixture setup
- Check user role assignments
- Verify token generation in login response

## CI/CD Integration

To integrate tests into CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        python manage.py test api.tests --verbosity=2
    - name: Generate coverage
      run: |
        coverage run --source='api' manage.py test api.tests
        coverage report
```

## Next Steps

1. Run the test suite to validate the setup
2. Add more tests as new features are developed
3. Maintain test coverage above 80%
4. Review failing tests and fix issues
5. Integrate tests into development workflow
