#!/usr/bin/env python
import os
import sys
import django

sys.path.insert(0, 'D:\\Class\\Year_03\\MAD_Class\\inventory-backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

django.setup()

from api.models import User

print("🗑️  Deleting all existing users...")
deleted_count, _ = User.objects.all().delete()
print(f"✅ Deleted {deleted_count} user(s)")

print("\n📝 Creating new users...")

# Create manager user
try:
    manager = User.objects.create_user(
        username='manager',
        email='manager@example.com',
        password='manager123',
        role='manager',
        is_staff=False,
        is_superuser=False
    )
    print(f"✅ Created manager user:")
    print(f"   Username: manager")
    print(f"   Email: manager@example.com")
    print(f"   Password: manager123")
    print(f"   Role: manager")
except Exception as e:
    print(f"❌ Error creating manager user: {e}")

# Create normal user (staff)
try:
    staff_user = User.objects.create_user(
        username='user',
        email='user@example.com',
        password='user123',
        role='staff',
        is_staff=False,
        is_superuser=False
    )
    print(f"\n✅ Created normal user:")
    print(f"   Username: user")
    print(f"   Email: user@example.com")
    print(f"   Password: user123")
    print(f"   Role: staff")
except Exception as e:
    print(f"❌ Error creating normal user: {e}")

print("\n" + "="*50)
print("✨ Users recreated successfully!")
print("="*50)
print("\nYou can now login with:")
print("\n📋 Manager User:")
print("   - Username: manager")
print("   - Password: manager123")
print("   - Role: Manager (can create/edit products & inventory)")
print("\n👤 Normal User:")
print("   - Username: user")
print("   - Password: user123")
print("   - Role: Staff (can only view products)")
print("="*50)
