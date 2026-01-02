# Inventory Management System - Backend

Django REST API backend for the Inventory Management System with KHQR payment integration.

## Features

- RESTful API with Django REST Framework
- JWT Authentication
- PostgreSQL Database
- KHQR (Bakong) Payment Integration
- Invoice Generation
- Purchase Order Management
- Supplier Management
- User Management with Role-Based Access Control

## Tech Stack

- **Framework**: Django 5.2.1
- **API**: Django REST Framework
- **Database**: PostgreSQL (Production), SQLite (Development)
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Payment**: KHQR Bakong API
- **Server**: Gunicorn
- **Static Files**: WhiteNoise

## Setup Instructions

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 14 or higher
- pip and virtualenv

### Installation

1. **Clone the repository**
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv env
   # Windows
   .\env\Scripts\activate
   # Linux/Mac
   source env/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Copy `.env.production.example` to `.env` and update with your values:
   ```bash
   cp .env.production.example .env
   ```

   Required environment variables:
   - `SECRET_KEY`: Django secret key (generate a secure one)
   - `DEBUG`: Set to `False` in production
   - `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: PostgreSQL credentials
   - `ALLOWED_HOSTS`: Your domain(s)
   - `CORS_ALLOWED_ORIGINS`: Your frontend URL(s)
   - `KHQR_*`: Bakong payment credentials

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Collect static files**
   ```bash
   python manage.py collectstatic --noinput
   ```

8. **Run development server**
   ```bash
   python manage.py runserver
   ```

## Production Deployment

### Using Gunicorn

1. **Set environment to production**
   ```bash
   export DJANGO_SETTINGS_MODULE=core.settings.production
   ```

2. **Run Gunicorn**
   ```bash
   gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4
   ```

### Docker Deployment (Recommended)

Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

Build and run:
```bash
docker build -t inventory-backend .
docker run -p 8000:8000 --env-file .env inventory-backend
```

### Environment Variables for Production

Ensure these are set in your production environment:

```bash
SECRET_KEY=your-secure-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
DB_NAME=inventory_prod
DB_USER=your_db_user
DB_PASSWORD=your_secure_password
DB_HOST=your_db_host
DB_PORT=5432
```

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login
- `POST /api/auth/token/refresh/` - Refresh JWT token
- `GET /api/auth/user/` - Get current user

### Inventory
- `GET /api/inventory/` - List all inventory items
- `POST /api/inventory/` - Create inventory item
- `GET /api/inventory/{id}/` - Get specific item
- `PUT /api/inventory/{id}/` - Update item
- `DELETE /api/inventory/{id}/` - Delete item

### Invoices
- `GET /api/invoices/` - List invoices
- `POST /api/invoices/` - Create invoice
- `GET /api/invoices/{id}/` - Get invoice details
- `POST /api/invoices/{id}/generate-khqr/` - Generate KHQR payment

### Suppliers
- `GET /api/suppliers/` - List suppliers
- `POST /api/suppliers/` - Create supplier
- `PUT /api/suppliers/{id}/` - Update supplier
- `DELETE /api/suppliers/{id}/` - Delete supplier

### Purchase Orders
- `GET /api/purchase-orders/` - List purchase orders
- `POST /api/purchase-orders/` - Create purchase order
- `GET /api/purchase-orders/{id}/` - Get purchase order

## Project Structure

```
backend/
├── api/                    # Main API application
│   ├── models.py          # Database models
│   ├── views.py           # API views
│   ├── serializers.py     # DRF serializers
│   ├── permissions.py     # Custom permissions
│   └── khqr_service.py    # KHQR integration
├── core/                   # Project settings
│   ├── settings/
│   │   ├── base.py        # Base settings
│   │   ├── development.py # Dev settings
│   │   └── production.py  # Production settings
│   ├── urls.py
│   └── wsgi.py
├── media/                  # User uploaded files
├── staticfiles/           # Collected static files
├── logs/                  # Application logs
├── manage.py
└── requirements.txt
```

## Database Schema

### Key Models
- **User**: Extended Django user with roles
- **Product**: Inventory products
- **Supplier**: Supplier information
- **PurchaseOrder**: Purchase orders with items
- **Invoice**: Sales invoices with KHQR payment
- **Transaction**: Transaction history

## Security

- JWT authentication for API access
- HTTPS enforced in production
- CORS configured for frontend domain
- SQL injection protection via Django ORM
- XSS protection enabled
- CSRF protection for non-API endpoints

## Troubleshooting

### Common Issues

1. **Database connection errors**
   - Verify PostgreSQL is running
   - Check database credentials in `.env`
   - Ensure database exists

2. **Static files not loading**
   - Run `python manage.py collectstatic`
   - Check `STATIC_ROOT` in settings

3. **CORS errors**
   - Add frontend URL to `CORS_ALLOWED_ORIGINS`
   - Ensure credentials are allowed

## Support

For issues and questions, please check the main project README or contact the development team.
