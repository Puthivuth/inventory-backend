#!/usr/bin/env python
import os
import sys
import django

sys.path.insert(0, 'D:\\Class\\Year_03\\MAD_Class\\inventory-backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

django.setup()

from api.models import User
from django.contrib.auth.models import Group

# Create test user
try:
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        role='staff'
    )
    print(f"✅ Created test user: {user.username}")
    print(f"   Username: testuser")
    print(f"   Email: test@example.com")
    print(f"   Password: testpass123")
except Exception as e:
    print(f"User might already exist or error: {e}")

# Create admin user if not exists
try:
    admin_user = User.objects.create_user(
        username='admin',
        email='admin@example.com',
        password='admin123',
        role='admin',
        is_staff=True,
        is_superuser=True
    )
    print(f"✅ Created admin user: {admin_user.username}")
    print(f"   Username: admin")
    print(f"   Email: admin@example.com")
    print(f"   Password: admin123")
except Exception as e:
    print(f"Admin user might already exist or error: {e}")

print("\n✨ Test users created successfully!")
print("\nYou can now login with:")
print("  - Username: testuser, Password: testpass123")
print("  - Username: admin, Password: admin123")
