# Inventory Backend - Complete Documentation

**Project**: Inventory Management System  
**Framework**: Django + Django REST Framework  
**Database**: PostgreSQL  
**Vector DB**: Qdrant  
**ML Models**: OpenAI CLIP + YOLOv8  
**Payment Integration**: KHQR (Bakong)

---

## Table of Contents

1. [Project Dependencies](#1-project-dependencies)
2. [Django Settings & Configuration](#2-django-settings--configuration)
3. [Database Models](#3-database-models)
4. [API Views & Endpoints](#4-api-views--endpoints)
5. [URL Routing](#5-url-routing)
6. [Serializers](#6-serializers)
7. [Authentication & Permissions](#7-authentication--permissions)
8. [Image Search Functionality](#8-image-search-functionality)
9. [KHQR Payment Service](#9-khqr-payment-service)
10. [Management Commands](#10-management-commands)
11. [Signals & Business Logic](#11-signals--business-logic)
12. [Admin Interface](#12-admin-interface)
13. [Utilities & Services](#13-utilities--services)
14. [Deployment Architecture](#14-deployment-architecture)

---

## 1. Project Dependencies

### Core Web Framework
| Package | Version | Purpose |
|---------|---------|---------|
| Django | 5.2.1 | Web framework |
| djangorestframework | 3.16.0 | REST API framework |
| djangorestframework-simplejwt | 5.5.0 | JWT authentication |

### Database & ORM
| Package | Version | Purpose |
|---------|---------|---------|
| psycopg[binary] | 3.2.13 | PostgreSQL database driver |
| dj-database-url | 2.2.0 | Database URL parsing |

### Server & Middleware
| Package | Version | Purpose |
|---------|---------|---------|
| gunicorn | 23.0.0 | WSGI HTTP server |
| whitenoise | 6.9.0 | Static file serving |
| django-cors-headers | 4.7.0 | CORS support |
| django-grappelli | 3.0.10 | Admin UI enhancement |

### Configuration & Utilities
| Package | Version | Purpose |
|---------|---------|---------|
| python-dotenv | 1.1.0 | Environment variable management |
| requests | 2.32.5 | HTTP client |

### Payment Integration
| Package | Version | Purpose |
|---------|---------|---------|
| bakong-khqr | 0.1.0 | KHQR payment SDK |

### Image & ML
| Package | Version | Purpose |
|---------|---------|---------|
| qdrant-client | 1.17.1 | Vector DB client |
| openai-clip | 1.0.1 | Image embeddings (CLIP) |
| torch | 2.1.0 | PyTorch ML framework |
| torchvision | 0.16.0 | Computer vision models |
| pillow | 11.2.1 | Image processing |

### Document Generation
| Package | Version | Purpose |
|---------|---------|---------|
| reportlab | 4.4.2 | PDF generation |

### Data Processing
| Package | Version | Purpose |
|---------|---------|---------|
| numpy | 1.24.3 | Numerical computing |

---

## 2. Django Settings & Configuration

### Base Settings (core/settings/base.py)

#### Database Configuration
```python
Database: PostgreSQL
Custom User Model: api.User
Time Zone: Asia/Phnom_Penh
```

#### Installed Apps
```
grappelli
django.contrib.admin
djangorestframework
django-cors-headers
api (custom)
```

#### Middleware Stack
```
CorsMiddleware → SecurityMiddleware → WhiteNoiseMiddleware → 
SessionMiddleware → CSRFMiddleware → AuthenticationMiddleware
```

#### REST Framework Configuration
```python
Authentication: TokenAuthentication
Default Permission: IsAuthenticated
Feature: Auto-generates token upon user creation
```

#### Static & Media Files
```
Static Files: WhiteNoise-based compression (production)
Media Files: /media/ directory for uploads
Static Root: WhiteNoise configured
```

#### KHQR Payment Configuration
Environment Variables:
- `KHQR_BASE_URL` - Bakong API endpoint
- `KHQR_EMAIL` - Authentication email
- `KHQR_TOKEN` - Authentication token
- `KHQR_BAKONG_ACCOUNT_ID` - Merchant account ID
- `KHQR_MERCHANT_NAME` - Business name for QR
- `KHQR_MERCHANT_CITY` - Business location
- `KHQR_APP_ICON_URL` - App branding
- `KHQR_APP_NAME` - Application name

#### Image Search Configuration
Environment Variables:
- `IMAGE_SEARCH_QDRANT_PATH` - Vector DB storage location
- `IMAGE_SEARCH_COLLECTION_NAME` - Default: "inventory_products"
- `IMAGE_SEARCH_YOLO_MODEL` - Default: "yolov8n.pt"
- `IMAGE_SEARCH_EMBEDDING_MODEL` - Default: "clip-ViT-B-32"
- `IMAGE_SEARCH_DETECTION_CONFIDENCE` - Default: 0.25

### Development Settings (core/settings/development.py)
```python
DEBUG = True
CORS: Enabled for localhost:3000/3001 and ngrok domains
HTTPS: Disabled for local development
Email Backend: Console output
```

### Production Settings (core/settings/production.py)
```python
DEBUG = False (environment-driven)
HTTPS Required: SECURE_SSL_REDIRECT = True
HSTS Enabled: 31536000 seconds (1 year)
Security Headers: XSS filter, content-type sniffing prevention
Logging: File-based to logs/django.log
Email: SMTP configured from environment
```

---

## 3. Database Models

### Entity Relationship Overview

```
User (Custom AbstractUser)
  ├── UserProfile (1:1)
  ├── NewStock (1:N) - Stock receipts
  ├── Invoice (1:N) - Created by user
  └── ActivityLog (1:N) - User actions

Category (1:N)
  └── SubCategory (1:N)
       └── Product (1:N)
            ├── Inventory (1:1)
            │    └── NewStock (1:N)
            ├── Purchase (1:N) - Invoice line items
            ├── ProductAssociation (N:N) - Bought together
            └── Source (Supplier)

Customer (1:N)
  ├── Invoice (1:N)
  └── Transaction (1:N)

Invoice (1:N)
  ├── Purchase (1:N) - Line items
  └── Transaction (1:N) - Payments
```

### Core Models

#### 1. User (Custom)
**Extends**: `AbstractUser`
```python
Fields:
  - username (unique, from AbstractUser)
  - email (from AbstractUser)
  - first_name, last_name (from AbstractUser)
  - password (hashed, from AbstractUser)
  - role: Choice('administrator', 'manager', 'staff')
  - date_joined (from AbstractUser)
  - is_active (from AbstractUser)

Related:
  - UserProfile (1:1 reverse)
  - NewStock (1:N reverse: stock_added_by)
  - Invoice (1:N reverse: created_by_user)
  - ActivityLog (1:N reverse: user)
  - Token (1:1 reverse) - Auto-created on save
```

#### 2. UserProfile
**Purpose**: Extended user metadata for business information
```python
Fields:
  - user: ForeignKey(User, on_delete=CASCADE, unique=True)
  - qr_code_image: ImageField (optional)
  - business_name: CharField
  - address: CharField
  - phone: CharField
  - email: EmailField
  - tax_id: CharField

Meta:
  - Related name: user_profile
```

#### 3. Category
**Purpose**: Top-level product categorization
```python
Fields:
  - name: CharField (max_length=100, unique=True)
  - created_at: DateTimeField (auto_now_add=True)

Related:
  - SubCategory (reverse: subcategories)

Constraints:
  - Unique category names
```

#### 4. SubCategory
**Purpose**: Nested category hierarchy
```python
Fields:
  - category: ForeignKey(Category)
  - name: CharField (max_length=100)
  - created_at: DateTimeField (auto_now_add=True)

Related:
  - Category (reverse: subcategories)
  - Product (reverse: products)

Constraints:
  - Unique per category (name + category combination)
```

#### 5. Source (Supplier/Vendor)
**Purpose**: Supplier/vendor information
```python
Fields:
  - name: CharField
  - url: URLField (optional)
  - contact_person: CharField
  - phone: CharField
  - email: EmailField
  - address: CharField
  - district: CharField

Related:
  - Product (reverse: products)
  - NewStock (reverse: stock_supplied)
```

#### 6. Product
**Purpose**: Core inventory item
```python
Fields:
  - product_id: UUIDField (primary_key=True)
  - subcategory: ForeignKey(SubCategory)
  - source: ForeignKey(Source, null=True, blank=True)
  - name: CharField (max_length=100)
  - description: TextField
  - image: URLField (optional)
  - sku: CharField (unique)
  - unit: CharField (Box, Piece, Liter, Kg, etc.)
  - cost_price: DecimalField (Decimal, 10, 2)
  - sale_price: DecimalField (Decimal, 10, 2)
  - discount: FloatField (0-100, default=0)
  - status: Choice('Active', 'Inactive', 'Discount', default='Active')
  - created_at: DateTimeField (auto_now_add=True)
  - updated_at: DateTimeField (auto_now=True)

Auto-Logic:
  - If discount > 0: Sets status to 'Discount'

Related:
  - SubCategory (reverse: products)
  - Source (reverse: products)
  - Inventory (1:1 reverse)
  - Purchase (1:N reverse)
  - NewStock (reverse via Inventory)
  - ProductAssociation (N:N)

Signals:
  - post_save: Create ActivityLog (CREATE_PRODUCT / UPDATE_PRODUCT)
  - post_delete: Create ActivityLog (DELETE_PRODUCT)
```

#### 7. Inventory
**Purpose**: Stock level tracking per location
```python
Fields:
  - product: ForeignKey(Product, on_delete=CASCADE, unique=True)
  - quantity: IntegerField (default=0)
  - reorder_level: IntegerField (default=10)
  - location: CharField (max_length=100, optional)
  - last_updated: DateTimeField (auto_now=True)

Related:
  - Product (reverse: inventory)
  - NewStock (reverse: inventory_record)

Signals:
  - pre_save: Stores previous quantity for comparison
  - post_save: Logs CREATE_INVENTORY or UPDATE_INVENTORY with delta

Methods:
  - String representation shows product name + quantity
```

#### 8. NewStock
**Purpose**: Stock receipt records (audit trail)
```python
Fields:
  - inventory: ForeignKey(Inventory)
  - quantity: IntegerField (received quantity)
  - purchase_price: DecimalField (cost per unit)
  - received_date: DateTimeField
  - supplier: ForeignKey(Source, on_delete=SET_NULL, null=True)
  - added_by_user: ForeignKey(User, on_delete=SET_NULL, null=True)
  - note: TextField (optional)
  - created_at: DateTimeField (auto_now_add=True)

Related:
  - Inventory (reverse: stock_entries)
  - Source (reverse: stock_supplied)
  - User (reverse: stock_added_by)

Purpose:
  - Full audit trail of inventory receipts
  - Tracks cost history
  - Links suppliers to stock additions
```

#### 9. Customer
**Purpose**: Individual or business customers
```python
Fields:
  - customer_id: UUIDField (primary_key=True)
  - type: Choice('Individual', 'Business', default='Individual')
  - name: CharField (max_length=100)
  - address: CharField
  - phone: CharField
  - email: EmailField
  - first_purchase_date: DateTimeField (null=True, blank=True)
  - created_at: DateTimeField (auto_now_add=True)
  - updated_at: DateTimeField (auto_now=True)

Related:
  - Invoice (1:N reverse: invoices)
  - Transaction (1:N reverse: transactions)

Auto-Logic:
  - first_purchase_date auto-populated from earliest invoice
```

#### 10. Invoice
**Purpose**: Sales/transaction record with KHQR payment integration
```python
Fields:
  - invoice_id: UUIDField (primary_key=True)
  - invoiceNumber: CharField (auto-generated format: INV-YYYY-NNN)
  - customer: ForeignKey(Customer)
  - created_by_user: ForeignKey(User)
  - total_before_discount: DecimalField (auto-calculated)
  - discount: DecimalField (auto-calculated, default=0)
  - tax: DecimalField (auto-calculated, default=0)
  - grand_total: DecimalField (total = before_discount - discount + tax)
  - payment_method: Choice('Cash', 'KHQR')
  - status: Choice('Pending', 'Paid', 'Cancelled', default='Pending')
  - paid_at: DateTimeField (null=True, set when status='Paid')
  - created_at: DateTimeField (auto_now_add=True)
  - updated_at: DateTimeField (auto_now=True)

KHQR-Specific Fields (for payment verification):
  - khqr_code_string: TextField (Full QR payload, null=True)
  - khqr_md5: CharField (MD5 hash for verification, null=True)
  - khqr_transaction_hash: CharField (Full 64-char hash if paid, null=True)
  - khqr_short_hash: CharField (First 8 chars, null=True)
  - khqr_deeplink: URLField (Mobile payment link, null=True)
  - khqr_last_checked_at: DateTimeField (Last verification attempt, null=True)
  - khqr_payment_data: JSONField (Full KHQR API response, null=True)

Related:
  - Customer (reverse: invoices)
  - User (reverse: invoices_created_by)
  - Purchase (1:N reverse: purchase_set)
  - Transaction (1:N reverse: transactions)

Signals:
  - post_save: Triggers calculate_product_associations (if Paid/Pending)
  - Nested create: Triggers inventory reduction via Purchase signal
```

#### 11. Purchase
**Purpose**: Line items within invoices
```python
Fields:
  - purchase_id: UUIDField (primary_key=True)
  - invoice: ForeignKey(Invoice)
  - product: ForeignKey(Product)
  - quantity: IntegerField (items purchased)
  - price_per_unit: DecimalField (selling price per unit)
  - discount: DecimalField (line-level discount, optional)
  - subtotal: DecimalField (auto-calculated)
  - created_at: DateTimeField (auto_now_add=True)

Related:
  - Invoice (reverse: purchases)
  - Product (reverse: purchases)

Signals:
  - post_save: Triggers update_inventory_on_purchase
    - Reduces inventory.quantity by purchase.quantity

Calculation:
  - subtotal = (quantity * price_per_unit) - discount
```

#### 12. ProductAssociation
**Purpose**: "Frequently bought together" tracking
```python
Fields:
  - association_id: UUIDField (primary_key=True)
  - product1: ForeignKey(Product, related_name='associations_from')
  - product2: ForeignKey(Product, related_name='associations_to')
  - frequency: IntegerField (times bought together, default=0)
  - association_percentage: FloatField (0-100, auto-calculated)
  - total_product1_purchases: IntegerField (cached for calculation)
  - created_at: DateTimeField (auto_now_add=True)
  - updated_at: DateTimeField (auto_now=True)

Constraints:
  - Unique constraint: (product1, product2) - one per product pair
  - Prevents duplicate associations

Related:
  - Product (2 ForeignKeys)

Auto-Logic (via signals):
  - On invoice.post_save (Paid/Pending):
    - Extract unique product pairs
    - Increment frequency for each pair
    - Recalculate association percentages:
      ```
      percentage = min((frequency / total_product1_purchases) * 100, 100.0)
      ```

Bidirectional Maintenance:
  - Both (A→B) and (B→A) associations stored
  - Frequency consistent in both directions
```

#### 13. Transaction
**Purpose**: Payment records for invoices
```python
Fields:
  - transaction_id: UUIDField (primary_key=True)
  - invoice: ForeignKey(Invoice, null=True)
  - customer: ForeignKey(Customer)
  - amount: DecimalField (amount paid)
  - payment_method: Choice('Cash', 'Card', 'KHQR', 'BankTransfer', 'Other')
  - status: Choice('Pending', 'Completed', 'Failed', 'Refunded')
  - reference: CharField (Payment reference/receipt number, optional)
  - transaction_date: DateTimeField
  - recorded_by_user: ForeignKey(User)
  - note: TextField (optional)
  - created_at: DateTimeField (auto_now_add=True)

Related:
  - Invoice (reverse: transactions)
  - Customer (reverse: transactions)
  - User (reverse: transactions_recorded)

Purpose:
  - Track all payments for invoices
  - Support multiple payment methods
  - Audit trail of payment processing
```

#### 14. ActivityLog
**Purpose**: Audit trail for all data changes
```python
Fields:
  - id: AutoField (primary_key=True)
  - action_type: CharField (choices below)
  - description: TextField
  - timestamp: DateTimeField (auto_now_add=True)
  - user: ForeignKey(User, null=True, blank=True)

Action Types (examples):
  - USER_LOGIN: User authentication
  - USER_CREATED: New user registration
  - CREATE_PRODUCT: Product created
  - UPDATE_PRODUCT: Product modified (with before/after values)
  - DELETE_PRODUCT: Product removed
  - CREATE_INVENTORY: Inventory record created
  - UPDATE_INVENTORY: Stock level changed (with delta)
  - CREATE_CATEGORY: Category created
  - UPDATE_CATEGORY: Category modified
  - DELETE_CATEGORY: Category deleted

Related:
  - User (reverse: activity_logs)

Auto-Population:
  - Created via post_save/post_delete signal handlers
  - Triggered on: Product, Category, Inventory, Invoice

Usage:
  - Complete audit trail
  - Compliance/regulatory requirements
  - Debugging user actions
  - Historical data recovery
```

---

## 4. API Views & Endpoints

### ViewSet Architecture (14 Total)

#### Core Features
- **Framework**: Django REST Framework with DefaultRouter
- **Authentication**: Token-based (Authorization: Token <token>)
- **Default Permissions**: IsAuthenticated (most endpoints)
- **Pagination**: Applied to list views
- **Filtering**: Model-specific filters available

#### ViewSet Details

| ViewSet | Model | Permissions | Actions | Notes |
|---------|-------|-------------|---------|-------|
| UserViewSet | User | IsAuthenticated + IsAdmin | Full CRUD (admin only) | Create/update/delete users |
| UserProfileViewSet | UserProfile | IsAuthenticated | CRUD (own profile for non-admins) | Extended user info |
| CategoryViewSet | Category | IsManagerOrReadOnly | Managers edit, staff view | Product categories |
| SubCategoryViewSet | SubCategory | IsManagerOrReadOnly | Managers edit, staff view | Sub-categories |
| SourceViewSet | Source | IsManagerOrReadOnly | Managers edit, staff view | Suppliers |
| ProductViewSet | Product | IsManagerOrReadOnly | Full CRUD (filtered) | Hide cost_price from staff |
| InventoryViewSet | Inventory | IsManagerOrReadOnly | Managers adjust, staff view | Stock levels |
| NewStockViewSet | NewStock | IsAuthenticated | All users can add stock | Receipts audit trail |
| CustomerViewSet | Customer | IsManagerOrReadOnly | Managers manage, staff view | Customer records |
| InvoiceViewSet | Invoice | IsManagerOrReadOnly | **Complex - see below** | Advanced features |
| PurchaseViewSet | Purchase | IsManagerOrReadOnly | Read mostly | Line items |
| TransactionViewSet | Transaction | IsManagerOrReadOnly | Payment records | Payment tracking |
| ActivityLogViewSet | ActivityLog | IsAdminOrManager | Admin/manager audit view | Audit trail |
| ProductAssociationViewSet | ProductAssociation | IsAuthenticated | View "bought together" data | Recommendations |

### Advanced Features: Invoice ViewSet

#### Custom Actions

**1. Create Invoice** `POST /api/invoices/`
```json
Request Body:
{
  "customer": "uuid-string",
  "lineItems": [
    {
      "product": "uuid-string",
      "quantity": 5,
      "pricePerUnit": 25.50,
      "discount": 0.00
    }
  ],
  "paymentMethod": "KHQR",  // or "Cash"
  "taxPercentage": 10        // optional, default 0
}

Response:
{
  "invoiceId": "uuid-string",
  "invoiceNumber": "INV-2024-001",
  "customer": { ... },
  "lineItems": [ { product, quantity, price, subtotal }, ... ],
  "totalBeforeDiscount": 127.50,
  "tax": 12.75,
  "grandTotal": 140.25,
  "paymentMethod": "KHQR",
  "status": "Pending",
  "khqrCodeString": "...",
  "khqrMd5": "...",
  "khqrDeeplink": "..." // if API token available
}

Behavior:
  - Validates inventory availability for all items
  - Auto-calculates totals
  - Creates nested Purchase records
  - Generates KHQR code if paymentMethod='KHQR'
  - Triggers inventory reduction via Purchase signal
  - Triggers product association calculation
```

**2. Generate/Regenerate KHQR Code** `POST /api/invoices/{id}/generate_khqr/`
```json
Returns existing QR if already generated
- Converts amount: USD → KHR (1 USD = 4000 KHR)
- Generates MD5 hash for payment verification
- Generates mobile deeplink (if API token available)
- Updates khqr_code_string, khqr_md5, khqr_deeplink fields

Response:
{
  "success": true,
  "qrString": "00020101051100011D6...",
  "md5Hash": "a1b2c3d4e5f6...",
  "deeplink": "https://deeplink.khqr.io/...",
  "amount": 560000.00,
  "currency": "KHR"
}
```

**3. Check Payment Status** `POST /api/invoices/{id}/check_payment/`
```
Purpose: Verify KHQR payment via Bakong API
- Queries API using MD5 hash
- If payment found:
  - Updates invoice.status = 'Paid'
  - Sets invoice.paid_at = now()
  - Stores transaction data in khqr_payment_data
  - Creates Transaction record
  - Records ActivityLog

Response:
{
  "success": true,
  "paid": true,
  "invoiceId": "uuid-string",
  "invoiceStatus": "Paid",
  "paidAt": "2024-05-08T10:30:00Z",
  "paymentDetails": {
    "transactionHash": "a1b2c3d4...",
    "amount": 560000.00,
    "currency": "KHR",
    "fromAccountId": "...",
    "confirmedAt": "2024-05-08T10:25:00Z"
  }
}

Error Handling:
- If API unavailable: Returns 503 with graceful message
- If payment not found: Returns paid=false
- Null MD5 hash: Returns 400 (no payment method)
```

**4. Manual Payment Marking** `POST /api/invoices/{id}/mark_as_paid/`
```
Purpose: Mark KHQR invoice as paid when auto-verification unavailable
- Only works for KHQR payment method
- Sets status='Paid' and paid_at=now()
- Creates Transaction record
- Records ActivityLog

Request: Empty body
Response:
{
  "success": true,
  "invoiceId": "uuid-string",
  "status": "Paid",
  "paidAt": "2024-05-08T10:35:00Z"
}
```

**5. Batch Payment Verification** `POST /api/invoices/batch_check_payments/`
```
Purpose: Check all pending KHQR invoices in one request
- Finds all invoices with status='Pending', paymentMethod='KHQR', khqrMd5 not null
- Queries KHQR API for each MD5
- Updates status to 'Paid' for confirmed payments
- Creates Transaction records for updated invoices

Request: Empty body
Response:
{
  "success": true,
  "checked": 15,
  "paid": 5,
  "pendingInvoices": [
    {
      "invoiceId": "uuid-string",
      "invoiceNumber": "INV-2024-001",
      "paid": true,
      "status": "Paid",
      "paidAt": "2024-05-08T10:30:00Z"
    },
    ...
  ]
}
```

### Product Association ViewSet - Related Products

**Custom Action**: `GET /api/product-associations/by_product/?product_id=123`

```json
Response:
{
  "success": true,
  "product": {
    "productId": "uuid-string",
    "name": "Main Product",
    "sku": "SKU001"
  },
  "relatedProducts": [
    {
      "productId": "uuid-string",
      "productName": "Related Product 1",
      "sku": "SKU002",
      "image": "/media/products/...",
      "salePrice": 25.50,
      "frequency": 12,
      "associationPercentage": 92.3
    },
    ...
  ],
  "count": 5
}

Ordering: By associationPercentage descending
Purpose: Cross-sell recommendations
```

### Image Upload Endpoint

**`POST /api/upload/`** - Product Image Upload
```
Authentication: IsAuthenticated
Content-Type: multipart/form-data

Parameters:
  - file: Image file (required)
    - Accepted formats: .jpg, .jpeg, .png, .gif, .webp
    - Max size: 5MB
    - Validation: MIME type check

Response:
{
  "success": true,
  "filename": "550e8400-e29b-41d4-a716-446655440000.jpg",
  "url": "http://localhost:8000/media/products/550e8400-e29b-41d4-a716-446655440000.jpg",
  "size": 234567,
  "contentType": "image/jpeg"
}

File Handling:
  - Generated name: UUID + original extension
  - Location: /media/products/{uuid}.{ext}
  - Unique per upload (prevents overwrites)
```

---

## 5. URL Routing

### API Endpoint Structure ([api/urls.py](api/urls.py))

```
BASE: /api/

Authentication (AllowAny):
  POST    /login/                     User login
  POST    /register/                  New user registration

Upload:
  POST    /upload/                    Image upload

Image Search:
  POST    /search-products/           Search by uploaded file
  GET     /search-products-url/       Search by URL
  POST    /index-product-images/      Reindex products

CRUD Endpoints (via DefaultRouter):
  /users/                             User management
  /user-profiles/                     User profiles
  /categories/                        Product categories
  /subcategories/                     Product subcategories
  /sources/                           Suppliers/vendors
  /products/                          Products
  /inventory/                         Stock levels
  /newstock/                          Stock receipts
  /customers/                         Customers
  /invoices/                          Invoices + custom actions
  /purchases/                         Invoice line items
  /transactions/                      Payments
  /activitylogs/                      Audit logs
  /product-associations/              Product associations

Custom Actions:
  /invoices/{id}/generate_khqr/
  /invoices/{id}/check_payment/
  /invoices/{id}/mark_as_paid/
  /invoices/batch_check_payments/
  /product-associations/by_product/
```

### Router Configuration
```python
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'user-profiles', UserProfileViewSet, basename='user-profile')
# ... etc for all ViewSets
# Auto-generates:
#   GET    /endpoint/           - List
#   POST   /endpoint/           - Create
#   GET    /endpoint/{id}/      - Retrieve
#   PUT    /endpoint/{id}/      - Update
#   DELETE /endpoint/{id}/      - Destroy
```

### Authentication Header
```
Authorization: Token <token>
```

---

## 6. Serializers

### User Serializers

**1. UserSerializer**
```python
Fields:
  - id: IntegerField (read-only)
  - username: CharField (max_length=150)
  - email: EmailField
  - first_name: CharField (max_length=150)
  - last_name: CharField (max_length=150)
  - role: ChoiceField('administrator', 'manager', 'staff')
  - password: CharField (write-only)

Methods:
  - create(validated_data): Hashes password with set_password()
  - update(): Handles password update safely
```

**2. UserProfileSerializer**
```python
Fields: All UserProfile model fields
Purpose: Extended profile management
```

### Product Hierarchy Serializers

**1. CategorySerializer**
```python
Fields: id, name, createdAt
Purpose: List/create categories
```

**2. SubCategorySerializer**
```python
Fields: id, category (FK), name, createdAt
Enriched: categoryName (nested)
Purpose: Manage subcategories with parent reference
```

**3. SourceSerializer**
```python
Fields: All Source fields (contact info)
Purpose: Supplier management
```

### Inventory Serializers

**1. ProductSerializer**
```python
Fields:
  - productId: UUIDField
  - name, description, image, SKU, unit
  - costPrice, salePrice, discount
  - status, subcategoryId, sourceId
  - createdAt, updatedAt

Nested:
  - subcategoryName: SerializerMethodField
  - categoryId: SerializerMethodField

Security:
  - to_representation(): Hides costPrice from staff users
  - Only managers/admins see full pricing

Purpose: Product CRUD with role-based visibility
```

**2. InventorySerializer**
```python
Fields: quantity, reorderLevel, location, lastUpdated
Related: productId, productName
Purpose: Stock level management
```

**3. NewStockSerializer**
```python
Fields: quantity, purchasePrice, receivedDate, note
Enriched:
  - productName, productSku
  - supplierName
  - userName (added_by_user)

Purpose: Stock receipt history with audit trail
```

### Invoice Serializers

**1. InvoiceSerializer** (Complex)
```python
Read Fields:
  - invoiceId, invoiceNumber
  - customer (nested: name, type)
  - createdByUsername
  - lineItems (nested: product, quantity, prices)
  - totalBeforeDiscount, discount, tax, grandTotal
  - paymentMethod, status, paidAt
  - khqrCodeString, khqrMd5, khqrDeeplink
  - createdAt, updatedAt

Write Fields:
  - customerId
  - lineItems (nested write serializer)
  - paymentMethod
  - taxPercentage (input, converted to amount)

Custom Methods:
  - create(validated_data):
    - Validates inventory availability
    - Calculates totals automatically
    - Creates nested Purchase records
    - Generates KHQR code if needed
    - Triggers signals for inventory reduction
    - Triggers product association calculation

Purpose: Invoice creation/retrieval with complex validation
```

**2. PurchaseNestedSerializer** (Write)
```python
Fields: product, quantity, pricePerUnit, discount
Purpose: Writing line items in invoice creation
```

**3. PurchaseReadSerializer** (Read)
```python
Fields: Enriched with productName, productSku
Purpose: Reading line items with product details
```

### Other Serializers

**1. CustomerSerializer**
```python
Fields: customerId, type, name, address, phone, email
Auto-populate:
  - firstPurchaseDate: Earliest invoice date (read-only)
Purpose: Customer management
```

**2. TransactionSerializer**
```python
Fields: transactionId, invoiceId, amount, method, status, reference, date
Enriched: customerName, recordedByUsername
Purpose: Payment tracking
```

**3. ActivityLogSerializer**
```python
Fields: id, actionType, description, timestamp
Enriched: username (from user FK)
Purpose: Audit trail display
```

**4. ProductAssociationSerializer**
```python
Read Fields:
  - associationId
  - product1Name, product1Sku, product1Image, product1Id
  - product2Name, product2Sku, product2Image, product2Id
  - frequency, associationPercentage
  - createdAt, updatedAt

Read-only: All calculated/nested fields
Purpose: "Bought together" relationship display
```

**5. RelatedProductSerializer**
```python
Fields: Optimized for quick retrieval
  - productId, productName, sku
  - image, salePrice
  - frequency, associationPercentage
Purpose: Cross-sell recommendations
```

---

## 7. Authentication & Permissions

### Authentication Methods

#### LoginView (`POST /api/login/`)
```python
Permission: AllowAny
Request Body:
{
  "username": "user@example.com",
  "password": "password"
}

Response:
{
  "success": true,
  "token": "a1b2c3d4e5f6...",
  "userId": 1,
  "username": "user@example.com",
  "role": "manager",
  "email": "user@example.com"
}

Side Effects:
  - Creates ActivityLog entry with action=USER_LOGIN
  - Token reusable for subsequent requests
  - Token stored in database (django.contrib.auth.models.Token)
```

#### RegisterView (`POST /api/register/`)
```python
Permission: AllowAny
Request Body:
{
  "username": "newuser@example.com",
  "email": "newuser@example.com",
  "password": "secure_password"
}

Response:
{
  "success": true,
  "token": "a1b2c3d4e5f6...",
  "userId": 2,
  "username": "newuser@example.com",
  "email": "newuser@example.com",
  "role": "staff"  // Default role for new users
}

Behavior:
  - Creates User with role='staff' (default)
  - Auto-creates Token for immediate use
  - Validates username/email uniqueness
  - Hashes password securely

Side Effects:
  - Creates ActivityLog entry with action=USER_CREATED
  - Creates UserProfile (if signal configured)
```

### Permission Classes

#### 1. IsAdmin
```python
Requirement: user.role == 'administrator'
Applied to:
  - User management (full CRUD)
  - Sensitive admin functions
```

#### 2. IsManager
```python
Requirement: user.role == 'manager'
Applied to:
  - Management-level operations
```

#### 3. IsStaff
```python
Requirement: user.role == 'staff'
Applied to:
  - Staff-level operations
```

#### 4. IsAdminOrManager
```python
Requirement: user.role in ['administrator', 'manager']
Applied to:
  - Inventory management
  - Invoice management
  - Activity log viewing
```

#### 5. IsManagerOrReadOnly
```python
Behavior:
  - GET/HEAD/OPTIONS: Any authenticated user
  - POST/PUT/PATCH/DELETE: Requires admin or manager role

Applied to:
  - Product management
  - Inventory management
  - Customer management
  - Category/subcategory management

Purpose:
  - Staff can view, only managers can edit
```

### Token Authentication
```
Header Format: Authorization: Token <token>
Storage: django.contrib.auth.models.Token
Lifecycle:
  - Auto-created on user creation
  - Unique per user
  - No expiration (time-based JWT not used in basic setup)
  - Should be stored securely on client
```

---

## 8. Image Search Functionality

### Architecture Overview

**Components**:
1. **Embedding Model**: OpenAI CLIP (Vision-Language model)
2. **Vector Database**: Qdrant (local file-based storage)
3. **ML Framework**: PyTorch with GPU acceleration
4. **Object Detection**: YOLOv8n (nano model for lightweight detection)
5. **Image Processing**: Pillow

**Model Specifications**:
```
CLIP Model: ViT-B/32
- Vision encoder: 512-dimensional embeddings
- Normalized vectors (L2 norm)
- Input: 224x224 RGB images
- Inference: CPU or GPU

YOLOv8n: Ultra-lightweight object detector
- Input: Any size (auto-resized to 416x416)
- Confidence threshold: 0.25 (default)
- Purpose: Object localization (optional enhancement)

Qdrant: Vector search engine
- Collection: inventory_products
- Storage: File-based (default: ./qdrant_storage/)
- Vector dim: 512
- Distance metric: Cosine similarity
- Payload: Product metadata (id, name, sku, image, prices)
```

### Image Search Service ([api/image_search_service.py](api/image_search_service.py))

#### Core Functions

**1. `initialize_qdrant(auto_index=True) → QdrantClient`**
```python
Purpose: Initialize Qdrant vector database
Parameters:
  - auto_index: bool (default True)
    - If True: Auto-index all products if collection empty
    - Uses _is_auto_indexing flag to prevent recursion
    - Uses _skip_auto_index flag for manual commands

Returns: QdrantClient instance

Behavior:
  - Creates collection if doesn't exist
  - Handles lock file cleanup
  - Non-blocking on errors (warnings only)
```

**2. `get_image_embedding(image_source) → np.ndarray`**
```python
Purpose: Convert image to 512-d CLIP embedding
Parameters:
  - image_source: PIL.Image | str(path) | str(url) | UploadedFile
    - Auto-detects source type
    - Lazy-loads CLIP model on first call

Returns: Normalized numpy array (float32, shape: (512,))

Behavior:
  - Converts to RGB automatically
  - Resizes to 224x224 (CLIP requirement)
  - Normalizes with L2 norm
  - Uses GPU if available, falls back to CPU
  - Caches model after first load
```

**3. `index_product_image(product_id, image_url, product_name, sku_code) → bool`**
```python
Purpose: Add/update product in vector database
Parameters:
  - product_id: str (UUID)
  - image_url: str (full path or URL)
  - product_name: str
  - sku_code: str

Returns: True on success, False on error

Behavior:
  - Fetches image from URL/path
  - Generates CLIP embedding
  - Upserts PointStruct to Qdrant collection
  - Stores metadata payload:
    {
      "product_id": "uuid",
      "product_name": "...",
      "sku_code": "...",
      "image_url": "...",
      "cost_price": 15.00,
      "sale_price": 25.50
    }
  - Non-blocking on errors
```

**4. `search_similar_images(image_source, top_k=10, score_threshold=0.5) → List[Dict]`**
```python
Purpose: Find similar products by image
Parameters:
  - image_source: PIL.Image | path | url | UploadedFile
  - top_k: int (default 10, max 50)
  - score_threshold: float (0-1 scale, default 0.5)

Returns:
[
  {
    "product_id": "uuid-string",
    "product_name": "Product Name",
    "sku_code": "SKU001",
    "image_url": "/media/products/...",
    "similarity_score": 0.87,  # Cosine similarity
    "sale_price": 25.50,
    "cost_price": 15.00,
    "distance": 0.13  # 1 - similarity
  },
  ...
]

Behavior:
  - Generates embedding for query image
  - Searches Qdrant with cosine distance metric
  - Filters by threshold (default 0.3 in API)
  - Enriches with current product data from DB
  - Returns ordered by similarity (highest first)
```

**5. `get_collection_info() → Dict`**
```python
Purpose: Health check and status information
Returns:
{
  "collection_name": "inventory_products",
  "vector_size": 512,
  "points_count": 1247
}
```

### Image Search API Endpoints

#### Endpoint 1: Search by File Upload
**`POST /api/search-products/`**
```python
Permission: IsAuthenticated
Content-Type: multipart/form-data

Parameters:
  - file: Image file (required)
    - Formats: .jpg, .jpeg, .png, .gif, .webp
    - Max size: 5MB
  - top_k: int (optional, default 10, range 1-50)
  - score_threshold: float (optional, default 0.3, range 0-1)

Response:
{
  "success": true,
  "results": [
    {
      "productId": "uuid-string",
      "productName": "Coca Cola 330ml",
      "skuCode": "COCACOLA-330",
      "image": "/media/products/550e8400-e29b-41d4-a716-446655440000.jpg",
      "similarityScore": 0.92,
      "salePrice": 1.50,
      "costPrice": 0.80
    },
    ...
  ],
  "count": 5,
  "parameters": {
    "top_k": 10,
    "scoreThreshold": 0.3
  }
}

Validations:
  - File presence check
  - Image format validation
  - File pointer reset before search
```

#### Endpoint 2: Search by URL
**`GET /api/search-products-url/`**
```python
Permission: IsAuthenticated

Query Parameters:
  - image_url: str (required)
    - Full URL to image (http/https)
  - top_k: int (optional, default 10)
  - score_threshold: float (optional, default 0.5)

Response: Same structure as file upload
```

#### Endpoint 3: Batch Indexing
**`POST /api/index-product-images/`**
```python
Permission: IsAdminOrManager only
Content-Type: application/json

Single Mode (default):
{
  "product_id": "uuid-string",
  "image_url": "/media/products/image.jpg",
  "product_name": "Product Name",
  "sku_code": "SKU001"
}

Batch Mode:
{
  "mode": "batch",
  "products": [
    { "product_id": "...", "image_url": "...", ... },
    { "product_id": "...", "image_url": "...", ... },
    ...
  ]
}

Response:
{
  "success": true,
  "indexed": 5,
  "failed": 0,
  "message": "Successfully indexed 5 products"
}

Behavior:
  - Single: Indexes one product
  - Batch: Efficient bulk indexing
  - Non-blocking on individual failures
```

### Auto-Indexing & Initialization

**Startup Behavior** (api/apps.py - ApiConfig.ready()):
```python
On app load:
1. Import signals module
2. Check if image search enabled (via env var)
3. Lazy-load CLIP + YOLOv8 models (if enabled)
   - Loads to GPU if available
   - Falls back to CPU
   - Caches models for reuse
4. Non-critical failures (warning-level logging)
```

**Management Commands**:
```
index_inventory_images:
  - Index/reindex all products
  - Optional --reset flag to recreate collection

initialize_image_search:
  - Full setup: Qdrant + local images + DB products
  - Modes: --local-only, --database-only

test_image_search:
  - Health checks
  - Model loading tests
  - Batch indexing tests
```

---

## 9. KHQR Payment Service

### KHQR Overview

**KHQR** = Khmer Quick Response  
**Provider**: Bakong (Cambodia National Bank payment system)  
**Purpose**: Generate dynamic QR codes for merchant payments in Cambodian Riel (KHR)

### KHQR Service Implementation ([api/khqr_service.py](api/khqr_service.py))

#### Class: KHQRService

**Initialization**:
```python
KHQRService()
# Loads configuration from Django settings:
- KHQR_BASE_URL: Bakong API endpoint (e.g., https://api.bakong.com)
- KHQR_EMAIL: Merchant email
- KHQR_TOKEN: Merchant authentication token
- KHQR_BAKONG_ACCOUNT_ID: Merchant account ID (REQUIRED)
- KHQR_MERCHANT_NAME: Business name (for QR display)
- KHQR_MERCHANT_CITY: Business location
- KHQR_APP_ICON_URL: App/business logo URL (optional)
- KHQR_APP_NAME: Application name (optional)
- KHQR_APP_DEEPLINK_CALLBACK: Callback URL for deeplinks (optional)
```

#### Key Methods

**1. `get_access_token() → Optional[str]`**
```python
Purpose: Obtain API access token
Fallback chain:
  1. Return cached token if available
  2. Return configured KHQR_TOKEN
  3. Attempt API renewal: POST /v1/renew_token
     - Parameters: email, token
     - Returns: New access token

Returns: Token string or None (fails gracefully)
Used for: Deeplink generation and premium features
```

**2. `generate_qr_code(invoice_id, amount, currency='USD') → Optional[Dict]`**
```python
Purpose: Generate dynamic KHQR QR code for specific amount
Uses: bakong_khqr.KHQR.create_qr() SDK

Parameters:
  - invoice_id: str (invoice reference)
  - amount: float (selling price)
  - currency: 'USD' or 'KHR' (default USD)

Conversion:
  - If USD: Converts to KHR (1 USD = 4000 KHR)
  - Stored: amount (KHR), currency='KHR'

SDK Call:
KHQR.create_qr(
  bank_account=KHQR_BAKONG_ACCOUNT_ID,
  merchant_name=KHQR_MERCHANT_NAME,
  merchant_city=KHQR_MERCHANT_CITY,
  amount=khqr_amount,
  currency='KHR',
  store_label='Store Label',
  bill_number=invoice_id,
  static=False  # Dynamic (amount-specific)
)

Returns:
{
  "qr_string": "00020101051100011D6...",  # Full QR payload
  "md5_hash": "a1b2c3d4e5f6g7h8...",     # Hash for verification
  "amount": 560000.0,
  "currency": "KHR",
  "invoice_id": invoice_id
}

Behavior:
  - Prints to console for debugging
  - Non-blocking on errors (logs warning)
  - Returns None on failure
```

**3. `generate_deeplink(qr_string) → Optional[str]`**
```python
Purpose: Create mobile payment link from QR payload
Requirements: Valid access token

API Call:
POST /v1/generate_deeplink_by_qr
Parameters: qr_string

Returns: Shortened deeplink URL (e.g., https://deeplink.khqr.io/abcd1234)

Usage:
  - Send to customer for mobile QR scanners
  - Direct payment app integration
  - WhatsApp/SMS sharing

Behavior:
  - Optional feature (fails gracefully)
  - Requires KHQR_TOKEN configuration
  - Non-blocking on errors
```

**4. `check_transaction_by_md5(md5_hash) → Optional[Dict]`**
```python
Purpose: Verify payment status via Bakong API
Parameters: md5_hash from generated QR

API Call:
GET /v1/check_transaction_by_md5?md5=<hash>

Returns (if payment found):
{
  "hash": "a1b2c3d4...",
  "amount": 560000.0,
  "currency": "KHR",
  "fromAccountId": "bakong.com.kh/00000000001",
  "toAccountId": "bakong.com.kh/merchant001",
  "createdDateMs": 1234567890000,  # Unix timestamp
  "acknowledgedDateMs": 1234567891000,
  "status": "SUCCESS",
  "description": "Payment successful",
  "transactionRef": "TXN123456"
}

Returns: None if payment not found or error

Error Handling:
  - API unavailable: Returns None with warning
  - Invalid MD5: Returns None
  - Payment not found: Returns None (retry later)
```

**5. `batch_check_transactions_by_md5(md5_list) → List[Dict]`**
```python
Purpose: Verify multiple payments in one request
Parameters: List of MD5 hashes

Returns: List of transaction results
[
  {
    "hash": "...",
    "found": true,
    "transaction": { ... }  # If found
  },
  {
    "hash": "...",
    "found": false
  },
  ...
]

Behavior:
  - Efficient batch verification
  - Non-blocking on individual errors
```

### Integration with Invoice Model

**KHQR Fields in Invoice**:
```python
khqr_code_string: TextField     # Full QR payload (00020101...)
khqr_md5: CharField              # Hash for verification (32 chars)
khqr_transaction_hash: CharField # Full tx hash if paid (64 chars)
khqr_short_hash: CharField       # First 8 chars of tx hash
khqr_deeplink: URLField          # Mobile payment link
khqr_last_checked_at: DateTimeField # Last API check
khqr_payment_data: JSONField     # Full Bakong response
```

**Invoice Creation Workflow**:
```
1. User creates invoice with paymentMethod='KHQR'
2. InvoiceSerializer.create():
   - Validates inventory availability
   - Calculates totals
   - Creates Purchase records
   - Calls generate_qr_code()
   - Stores qr_string, md5_hash
   - Attempts deeplink generation
3. Returns invoice with KHQR data
```

**Payment Verification Workflow**:
```
1. Customer scans QR and pays via Bakong
2. Business initiates check_payment() endpoint
3. KHQRService.check_transaction_by_md5():
   - Queries Bakong API
   - If found: Returns transaction data
4. ViewSet.check_payment():
   - Updates invoice.status = 'Paid'
   - Sets invoice.paid_at = now()
   - Stores full response in khqr_payment_data
   - Creates Transaction record
   - Records ActivityLog
5. Returns success response
```

**Error Scenarios**:
```
1. KHQR API unavailable:
   - Returns 503 Service Unavailable
   - Invoice remains Pending
   - Supports manual mark_as_paid() fallback

2. Invalid merchant configuration:
   - QR generation fails
   - Returns error with missing field message
   - Falls back to Cash payment if needed

3. Payment not found:
   - Batch check returns paid=false
   - User can retry later
   - Manual marking available
```

---

## 10. Management Commands

### Command: index_inventory_images

**Location**: `api/management/commands/index_inventory_images.py`

**Usage**:
```bash
python manage.py index_inventory_images [--reset]

Options:
  --reset: Delete existing collection and recreate (full reindex)
```

**Purpose**:
- Index all products with image URLs into Qdrant
- Add/update products that have changed

**Output**:
```
Indexing products from database...
[1/50] ✓ Coca Cola 330ml
[2/50] ✓ Sprite 500ml
[3/50] ✗ Fanta (image URL invalid)
...
[50/50] ✓ Water Bottle 1L

Summary:
  Total products: 50
  Indexed: 49
  Failed: 1
  Time: 12.34s
```

**Behavior**:
- Iterates through all products with image URLs
- Non-blocking on individual failures
- Reports success/failure for each product
- Final summary statistics

### Command: initialize_image_search

**Location**: `api/management/commands/initialize_image_search.py`

**Usage**:
```bash
python manage.py initialize_image_search [--local-only|--database-only]

Options:
  --local-only: Index only from /Images/ directory
  --database-only: Index only from database products
  (default): Both local and database
```

**Purpose**:
- Complete setup of Qdrant vector database
- Initialize CLIP + YOLOv8 models
- Index products from multiple sources

**Features**:
```
1. Local Images:
   - Scans /Images/ directory
   - Matches images to products by filename
   - Creates entries for unmatched images

2. Database Products:
   - Indexes all products with image URLs
   - Enriches with current pricing

3. Model Loading:
   - Loads CLIP to GPU/CPU
   - Reports GPU availability
   - Non-critical failures
```

**Output**:
```
Initializing Qdrant...
✓ Qdrant service started

Loading CLIP model...
✓ CLIP loaded to cuda (GPU)

Loading YOLOv8n model...
✓ YOLOv8n loaded

Indexing local images from /Images/...
[1/10] ✓ product_001.jpg
...

Indexing database products...
[1/50] ✓ Coca Cola 330ml
...

Collection Info:
  Name: inventory_products
  Vector size: 512
  Points: 60
```

### Command: test_image_search

**Location**: `api/management/commands/test_image_search.py`

**Usage**:
```bash
python manage.py test_image_search [--health|--preload|--index-all]

Options:
  --health: Check Qdrant service status
  --preload: Load CLIP + YOLOv8 to GPU/CPU
  --index-all: Batch index all products
  (default): Run all tests
```

**Tests**:

**1. Health Check**:
```
Testing Qdrant connection...
✓ Qdrant service is running
  Collection: inventory_products
  Points: 1247
  Vector size: 512
```

**2. GPU Detection**:
```
Testing GPU availability...
GPU Device: NVIDIA GeForce RTX 3080
GPU Memory: 8GB
CUDA Version: 11.8
✓ GPU available for model inference
```

**3. Model Preloading**:
```
Preloading CLIP model...
✓ CLIP ViT-B/32 loaded to cuda (1.2GB)

Preloading YOLOv8n model...
✓ YOLOv8n loaded to cuda (0.3GB)
```

**4. Batch Indexing**:
```
Batch indexing all products...
[1/50] ✓ Product 1
[2/50] ✓ Product 2
...
[50/50] ✓ Product 50

Summary:
  Indexed: 50
  Failed: 0
  Time: 23.45s
```

### Command: update_discount_status

**Location**: `api/management/commands/update_discount_status.py`

**Usage**:
```bash
python manage.py update_discount_status
```

**Purpose**:
- Fix product status synchronization
- Find products with discount > 0 but status != 'Discount'
- Update status to 'Discount'

**Logic**:
```python
for product in Product.objects.filter(discount__gt=0):
    if product.status != 'Discount':
        product.status = 'Discount'
        product.save()  # Triggers signal logging
```

**Output**:
```
Updating product discount status...

Updated products:
1. Coca Cola (5% discount) - Active → Discount
2. Sprite (10% discount) - Active → Discount
3. Water (15% discount) - Inactive → Discount

Summary:
  Total updated: 3
  Total unchanged: 47
```

---

## 11. Signals & Business Logic

### Signal Handlers Location: [api/signals.py](api/signals.py)

#### 1. Product Association Calculation
```python
@receiver(post_save, sender=Invoice)
def calculate_product_associations(sender, instance, created, **kwargs)

Trigger: Invoice created or updated with status in ['Paid', 'Pending']

Logic:
  1. Extract unique products from invoice line items
  2. For each product pair (A, B):
     a. Get or create ProductAssociation(product1=A, product2=B)
     b. Increment frequency count
     c. Increment frequency for reverse (B, A)
  3. Recalculate association percentages:
     percentage = min((frequency / total_product1_purchases) * 100, 100.0)

Calculation Details:
  - total_product1_purchases = Number of invoices containing product1
  - frequency = Times product1 and product2 bought together
  - Capped at 100% (max percentage)
  - Bidirectional: Both A→B and B→A maintained

Purpose:
  - "Frequently bought together" recommendations
  - Cross-sell/upsell analytics
  - Product correlation insights
```

#### 2. Inventory Reduction on Purchase
```python
@receiver(post_save, sender=Purchase)
def update_inventory_on_purchase(sender, instance, created, **kwargs)

Trigger: Purchase record created (during invoice creation)

Logic:
  if created:
    inventory = Inventory.objects.get(product=instance.product)
    inventory.quantity -= instance.quantity
    inventory.save()

Validation:
  - Inventory availability checked in InvoiceSerializer
  - Does not block if inventory insufficient (already validated)

Purpose:
  - Real-time inventory reduction on sale
  - Prevents double-counting
  - Maintains accurate stock levels
```

#### 3. Product Activity Logging
```python
@receiver(post_save, sender=Product)
def log_product_activity(sender, instance, created, **kwargs)

Creates ActivityLog with:
  - action_type: 'CREATE_PRODUCT' if created else 'UPDATE_PRODUCT'
  - description: Product details (name, price, etc.)
  - user: Current user (if available)
  - timestamp: auto_now_add

@receiver(post_delete, sender=Product)
def log_product_deletion(sender, instance, **kwargs)

Creates ActivityLog with:
  - action_type: 'DELETE_PRODUCT'
  - description: Deleted product details
```

#### 4. Category Activity Logging
```python
@receiver(post_save, sender=Category)
def log_category_activity(sender, instance, created, **kwargs)

Creates ActivityLog for CREATE_CATEGORY or UPDATE_CATEGORY

@receiver(post_delete, sender=Category)
def log_category_deletion(sender, instance, **kwargs)

Creates ActivityLog for DELETE_CATEGORY
```

#### 5. Inventory Activity Logging
```python
@receiver(pre_save, sender=Inventory)
def store_previous_inventory_quantity(sender, instance, **kwargs)

Caches instance._old_quantity = previous value
Purpose: Detect if quantity changed

@receiver(post_save, sender=Inventory)
def log_inventory_activity(sender, instance, created, **kwargs)

On create:
  - action_type: 'CREATE_INVENTORY'
  - description: Initial quantity set

On update (if quantity changed):
  - action_type: 'UPDATE_INVENTORY'
  - description: Shows before → after quantities
  - Calculates delta (positive for restocking, negative for sales)
  - Includes location and reorder level changes if any
```

#### Association Percentage Calculation

```python
def update_association_percentages(product):
    """
    Recalculate association percentages for a product
    
    Formula:
      percentage = min((frequency / total_purchases) * 100, 100.0)
    
    Where:
      frequency = times this product pair bought together
      total_purchases = total invoices containing product1
    """
    
    total_purchases = Purchase.objects.filter(
        product=product,
        invoice__status__in=['Paid', 'Pending']
    ).count()
    
    for association in product.associations_from.all():
        if total_purchases > 0:
            percentage = (association.frequency / total_purchases) * 100
            association.association_percentage = min(percentage, 100.0)
            association.save()
```

---

## 12. Admin Interface

### Admin Configuration: [api/admin.py](api/admin.py)

**Overview**:
All 14 models registered in Django admin with:
- List display customization
- Search fields
- List filters
- Date hierarchy
- Read-only fields
- Inline editing
- Autocomplete fields

### Key Admin Classes

#### UserAdmin (extends DjangoUserAdmin)
```python
Display: username, email, first_name, role, is_staff, is_active
Search: username, email
Filters: role, is_staff, is_active
Read-only: date_joined, last_login
Additional: Password change form, permissions management
```

#### ProductAdmin
```python
Display: name, sku, subcategory, source, sale_price, status
Search: name, sku, description
Filters: status, subcategory, discount
Autocomplete: subcategory, source
List editable: status, discount
```

#### InvoiceAdmin
```python
Display: invoiceNumber, customer, grand_total, status, paid_at
Search: invoiceNumber, customer__name
Filters: status, payment_method, paid_at
Inlines: PurchaseInline (edit line items)
Read-only: invoiceNumber, created_by_user, grand_total
```

#### InventoryAdmin
```python
Display: product, quantity, reorder_level, location
Search: product__name
Filters: reorder_level
List editable: quantity, reorder_level
```

#### ActivityLogAdmin
```python
Display: action_type, user, timestamp
Search: action_type, description
Filters: action_type, timestamp, user
Date hierarchy: timestamp
Read-only: All fields (audit only)
```

#### ProductAssociationAdmin
```python
Display: product1, product2, frequency, association_percentage
Search: product1__name, product2__name
Filters: association_percentage
Read-only: association_percentage (calculated field)
```

---

## 13. Utilities & Services

### Image Search Client ([api/image_search_client.py](api/image_search_client.py))

**Purpose**: Python client for separate image search microservice

```python
class ImageSearchClient:
    def __init__(self, base_url: str):
        """Initialize with service URL"""
        self.base_url = base_url
    
    def health_check(self) -> bool:
        """Check service health"""
        # GET /health
    
    def index_product(self, product_data: Dict) -> bool:
        """Index product via API"""
        # POST /index
    
    def index_product_file(self, image_file) -> bool:
        """Index product with file upload"""
        # POST /index-file
    
    def search(self, image: Image, top_k=10) -> List[Dict]:
        """Search similar products"""
        # POST /search
```

**Use Cases**:
- Deployment as separate microservice
- Load balancing image search across multiple servers
- Independent scaling of image processing

### App Configuration ([api/apps.py](api/apps.py))

**ApiConfig.ready()**:
```python
def ready(self):
    # 1. Import signals on app load
    import api.signals
    
    # 2. Lazy-load ML models (if image search enabled)
    #    - CLIP model to GPU/CPU
    #    - YOLOv8 model to GPU/CPU
    #    - Cached for reuse
    
    # 3. Non-critical failures
    #    - Warnings only, doesn't block startup
    #    - App continues even if ML fails
```

### WSGI Application ([core/wsgi.py](core/wsgi.py))

```python
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
application = get_wsgi_application()
```

---

## 14. Deployment Architecture

### Technology Stack

**Server**:
```
Gunicorn (WSGI server)
  - Workers: 4-8 (based on CPU cores)
  - Threads: 2-4 per worker
  - Timeout: 120s
  - Restart: Auto-reload on code changes
```

**Reverse Proxy**:
```
Nginx (optional, recommended for production)
  - Load balancing across Gunicorn workers
  - SSL/TLS termination
  - Static file caching
  - Compression
```

**Database**:
```
PostgreSQL
  - Version: 12+ recommended
  - Connection pooling: pgBouncer (optional)
  - Backups: Daily snapshots recommended
  - Replication: Optional for HA
```

**Static Files**:
```
WhiteNoise (inline compression)
  - Compressed on first request
  - Cached in memory
  - No separate storage needed
```

**Media Files**:
```
File system storage (default)
  - Location: /media/ directory
  - Alternative: Cloud storage (S3, Azure Blob)
```

**Vector Database**:
```
Qdrant (embedded file-based)
  - Location: ./qdrant_storage/
  - Alternative: Qdrant server (separate deployment)
  - Backups: Include /qdrant_storage/ directory
```

**ML Models**:
```
CLIP + YOLOv8 (preloaded to GPU/CPU)
  - GPU: Recommended for production
  - CPU fallback: Supported but slower
  - Memory: ~2-4GB for both models
```

### Required Environment Variables (18 Total)

#### Django Configuration
```
SECRET_KEY                 # Django secret key (min 50 chars)
DEBUG                      # True/False (False in production)
ALLOWED_HOSTS              # Comma-separated domain list
CORS_ALLOWED_ORIGINS       # Frontend domain URLs
DATABASE_URL               # postgresql://user:pass@host:port/db
```

#### KHQR Payment
```
KHQR_BASE_URL              # Bakong API endpoint (required)
KHQR_EMAIL                 # Merchant email
KHQR_TOKEN                 # API token (optional, for deeplinks)
KHQR_BAKONG_ACCOUNT_ID     # Merchant account (REQUIRED)
KHQR_MERCHANT_NAME         # Business name (required for QR)
KHQR_MERCHANT_CITY         # Location (required for QR)
KHQR_APP_ICON_URL          # Logo URL (optional)
KHQR_APP_NAME              # App name (optional)
KHQR_APP_DEEPLINK_CALLBACK # Callback URL (optional)
```

#### Image Search
```
IMAGE_SEARCH_QDRANT_PATH        # ./qdrant_storage/
IMAGE_SEARCH_COLLECTION_NAME    # inventory_products
IMAGE_SEARCH_YOLO_MODEL         # yolov8n.pt
IMAGE_SEARCH_EMBEDDING_MODEL    # clip-ViT-B-32
IMAGE_SEARCH_DETECTION_CONFIDENCE # 0.25
```

### Deployment Steps

**1. Install Dependencies**:
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

**2. Initialize Image Search** (optional):
```bash
python manage.py initialize_image_search
```

**3. Run Gunicorn**:
```bash
gunicorn core.wsgi:application \
  --workers 4 \
  --threads 2 \
  --timeout 120 \
  --bind 0.0.0.0:8000
```

**4. Configure Nginx** (optional):
```nginx
upstream django {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://django;
    }
    
    location /static/ {
        alias /path/to/static/;
    }
    
    location /media/ {
        alias /path/to/media/;
    }
}
```

**5. Setup SSL** (Let's Encrypt):
```bash
certbot --nginx -d yourdomain.com
```

### Monitoring & Maintenance

**Health Checks**:
```bash
GET /api/
  - Check API is running
  - No authentication required

GET /api/health/
  - Database connectivity
  - Cache status
  - Vector DB status
```

**Backups**:
```
Database: Daily PostgreSQL dumps
Media: Daily sync to backup storage
Qdrant: Include ./qdrant_storage/ directory
Static files: Regenerate via collectstatic
```

**Logs**:
```
Location: logs/django.log
Level: INFO in production
Rotation: Daily (recommended with logrotate)
```

---

## Summary: Key Statistics

| Category | Count | Details |
|----------|-------|---------|
| **Database Models** | 14 | Comprehensive data structure |
| **ViewSets** | 14 | Full REST API coverage |
| **Serializers** | 14 | Custom validation & enrichment |
| **Permission Classes** | 5 | Role-based access control |
| **Signal Handlers** | 8+ | Automatic business logic |
| **API Endpoints** | 50+ | CRUD + custom actions |
| **Management Commands** | 4 | Admin utilities |
| **Authentication Methods** | 2 | Login, Registration |
| **Payment Integrations** | 1 | KHQR (Bakong) |
| **AI/ML Features** | 2 | Image search + object detection |
| **Code Lines** | ~5,000+ | Full-stack implementation |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                      │
│              (React + TypeScript + Tailwind)                │
└────────────────────────┬────────────────────────────────────┘
                         │
                    HTTP/REST
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Django REST API                           │
│  (djangorestframework + Token Authentication)               │
├─────────────────────────────────────────────────────────────┤
│  ViewSets (14):                                             │
│  User, Product, Inventory, Invoice, Customer, etc.         │
├─────────────────────────────────────────────────────────────┤
│  Services:                                                  │
│  - KHQR Payment (Bakong integration)                        │
│  - Image Search (CLIP + Qdrant)                             │
│  - Business Logic (Signals & Management Commands)           │
├─────────────────────────────────────────────────────────────┤
│  Admin Interface (Django Grappelli)                         │
└────────┬──────────────────┬──────────────┬──────────────────┘
         │                  │              │
         ▼                  ▼              ▼
    PostgreSQL          Qdrant         File System
   (Primary DB)    (Vector DB)      (Static/Media)
         │                  │              │
    Backups            Indexing       Uploads
```

---

## Getting Started Guide

### Prerequisites
- Python 3.9+
- PostgreSQL 12+
- Virtual environment (venv/conda)
- Git

### Installation
```bash
# Clone repository
git clone <repo-url>
cd inventory-backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Initialize image search (optional)
python manage.py initialize_image_search

# Run development server
python manage.py runserver
```

### API Documentation
- Interactive API: http://localhost:8000/api/
- Admin Interface: http://localhost:8000/admin/
- API Schema: http://localhost:8000/schema/

---

**Document Version**: 1.0  
**Last Updated**: May 2024  
**Maintained By**: Development Team
