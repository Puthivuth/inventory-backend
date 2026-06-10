"""
Comprehensive tests for permission classes
Tests cover role-based access control (RBAC) and view-level permissions
"""

from django.test import TestCase
from rest_framework.test import APIRequestFactory
from api.models import User
from api.permissions import (
    IsAdmin, IsManager, IsStaff, IsAdminOrManager, IsManagerOrReadOnly
)


class BasePermissionTest:
    """Base class for permission tests with common setup"""
    
    def setUp(self):
        """Setup test users with different roles"""
        self.factory = APIRequestFactory()
        
        self.admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={'role': 'administrator'}
        )
        if created:
            self.admin_user.set_password('pass')
            self.admin_user.save()
        
        self.manager_user, created = User.objects.get_or_create(
            username='manager',
            defaults={'role': 'manager'}
        )
        if created:
            self.manager_user.set_password('pass')
            self.manager_user.save()
        
        self.staff_user, created = User.objects.get_or_create(
            username='staff',
            defaults={'role': 'staff'}
        )
        if created:
            self.staff_user.set_password('pass')
            self.staff_user.save()


class IsAdminPermissionTest(BasePermissionTest, TestCase):
    """Test IsAdmin permission class"""
    
    def test_admin_has_permission(self):
        """Test admin user has permission"""
        permission = IsAdmin()
        request = self.factory.get('/')
        request.user = self.admin_user
        self.assertTrue(permission.has_permission(request, None))
    
    def test_manager_no_permission(self):
        """Test manager user does not have permission"""
        permission = IsAdmin()
        request = self.factory.get('/')
        request.user = self.manager_user
        self.assertFalse(permission.has_permission(request, None))
    
    def test_staff_no_permission(self):
        """Test staff user does not have permission"""
        permission = IsAdmin()
        request = self.factory.get('/')
        request.user = self.staff_user
        self.assertFalse(permission.has_permission(request, None))
    
    def test_unauthenticated_no_permission(self):
        """Test unauthenticated user has no permission"""
        permission = IsAdmin()
        request = self.factory.get('/')
        request.user = None
        self.assertFalse(permission.has_permission(request, None))


class IsManagerPermissionTest(BasePermissionTest, TestCase):
    """Test IsManager permission class"""
    
    def test_manager_has_permission(self):
        """Test manager user has permission"""
        permission = IsManager()
        request = self.factory.get('/')
        request.user = self.manager_user
        self.assertTrue(permission.has_permission(request, None))
    
    def test_admin_no_permission(self):
        """Test admin user does not have permission (role specific)"""
        permission = IsManager()
        request = self.factory.get('/')
        request.user = self.admin_user
        self.assertFalse(permission.has_permission(request, None))
    
    def test_staff_no_permission(self):
        """Test staff user does not have permission"""
        permission = IsManager()
        request = self.factory.get('/')
        request.user = self.staff_user
        self.assertFalse(permission.has_permission(request, None))


class IsStaffPermissionTest(BasePermissionTest, TestCase):
    """Test IsStaff permission class"""
    
    def test_staff_has_permission(self):
        """Test staff user has permission"""
        permission = IsStaff()
        request = self.factory.get('/')
        request.user = self.staff_user
        self.assertTrue(permission.has_permission(request, None))
    
    def test_manager_no_permission(self):
        """Test manager user does not have permission"""
        permission = IsStaff()
        request = self.factory.get('/')
        request.user = self.manager_user
        self.assertFalse(permission.has_permission(request, None))
    
    def test_admin_no_permission(self):
        """Test admin user does not have permission"""
        permission = IsStaff()
        request = self.factory.get('/')
        request.user = self.admin_user
        self.assertFalse(permission.has_permission(request, None))


class IsAdminOrManagerPermissionTest(BasePermissionTest, TestCase):
    """Test IsAdminOrManager permission class"""
    
    def test_admin_has_permission(self):
        """Test admin user has permission"""
        permission = IsAdminOrManager()
        request = self.factory.get('/')
        request.user = self.admin_user
        self.assertTrue(permission.has_permission(request, None))
    
    def test_manager_has_permission(self):
        """Test manager user has permission"""
        permission = IsAdminOrManager()
        request = self.factory.get('/')
        request.user = self.manager_user
        self.assertTrue(permission.has_permission(request, None))
    
    def test_staff_no_permission(self):
        """Test staff user does not have permission"""
        permission = IsAdminOrManager()
        request = self.factory.get('/')
        request.user = self.staff_user
        self.assertFalse(permission.has_permission(request, None))


class IsManagerOrReadOnlyPermissionTest(BasePermissionTest, TestCase):
    """Test IsManagerOrReadOnly permission class"""
    
    def test_manager_can_write(self):
        """Test manager can perform write operations"""
        permission = IsManagerOrReadOnly()
        request = self.factory.post('/')
        request.user = self.manager_user
        self.assertTrue(permission.has_permission(request, None))
    
    def test_admin_can_write(self):
        """Test admin can perform write operations"""
        permission = IsManagerOrReadOnly()
        request = self.factory.post('/')
        request.user = self.admin_user
        self.assertTrue(permission.has_permission(request, None))
    
    def test_staff_can_read_only(self):
        """Test staff can perform read operations"""
        permission = IsManagerOrReadOnly()
        request = self.factory.get('/')  # GET is a SAFE_METHOD
        request.user = self.staff_user
        self.assertTrue(permission.has_permission(request, None))
    
    def test_staff_cannot_write(self):
        """Test staff cannot write"""
        permission = IsManagerOrReadOnly()
        request = self.factory.post('/')
        request.user = self.staff_user
        self.assertFalse(permission.has_permission(request, None))
    
    def test_staff_cannot_delete(self):
        """Test staff cannot delete"""
        permission = IsManagerOrReadOnly()
        request = self.factory.delete('/')
        request.user = self.staff_user
        self.assertFalse(permission.has_permission(request, None))
    
    def test_staff_can_read_details(self):
        """Test staff can read details (GET request)"""
        permission = IsManagerOrReadOnly()
        request = self.factory.get('/detail/')
        request.user = self.staff_user
        self.assertTrue(permission.has_permission(request, None))
    
    def test_unauthenticated_cannot_read(self):
        """Test unauthenticated user cannot read"""
        permission = IsManagerOrReadOnly()
        request = self.factory.get('/')
        request.user = None
        self.assertFalse(permission.has_permission(request, None))
