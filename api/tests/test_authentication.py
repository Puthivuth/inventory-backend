"""
Comprehensive tests for authentication endpoints
Tests cover login, registration, token generation, and related functionality
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from api.models import User, ActivityLog


class LoginViewTest(TestCase):
    """Test login endpoint functionality"""
    
    def setUp(self):
        """Setup test client and users"""
        self.client = APIClient()
        
        # Clean up existing users
        User.objects.filter(username__in=['testuser', 'admin', 'testmanager']).delete()
        
        # Create standard user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            role='staff'
        )
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='administrator'
        )
        
        self.login_url = '/api/login/'
    
    def test_login_success(self):
        """Test successful login returns token"""
        data = {
            'username': 'testuser',
            'password': 'password123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['role'], 'staff')
    
    def test_login_admin_success(self):
        """Test successful admin login"""
        data = {
            'username': 'admin',
            'password': 'admin123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'admin')
        self.assertEqual(response.data['role'], 'administrator')
    
    def test_login_invalid_credentials(self):
        """Test login fails with invalid password"""
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)
    
    def test_login_nonexistent_user(self):
        """Test login fails for non-existent user"""
        data = {
            'username': 'nonexistent',
            'password': 'password'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)
    
    def test_login_missing_username(self):
        """Test login fails without username"""
        data = {
            'password': 'password123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)
    
    def test_login_missing_password(self):
        """Test login fails without password"""
        data = {
            'username': 'testuser'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)
    
    def test_login_creates_activity_log(self):
        """Test login creates activity log entry"""
        data = {
            'username': 'testuser',
            'password': 'password123'
        }
        initial_logs = ActivityLog.objects.count()
        self.client.post(self.login_url, data, format='json')
        self.assertEqual(ActivityLog.objects.count(), initial_logs + 1)
        
        log = ActivityLog.objects.latest('createdAt')
        self.assertEqual(log.actionType, 'USER_LOGIN')
        self.assertEqual(log.user, self.user)
    
    def test_login_token_persistence(self):
        """Test token persists across multiple logins"""
        data = {
            'username': 'testuser',
            'password': 'password123'
        }
        response1 = self.client.post(self.login_url, data, format='json')
        token1 = response1.data['token']
        
        response2 = self.client.post(self.login_url, data, format='json')
        token2 = response2.data['token']
        
        # Same token should be returned
        self.assertEqual(token1, token2)
    
    def test_login_returns_user_role(self):
        """Test login response includes user role for manager"""
        # Create manager user
        User.objects.filter(username='testmanager').delete()
        User.objects.create_user(
            username='testmanager',
            password='password007',
            role='manager'
        )
        data = {
            'username': 'testmanager',
            'password': 'password007'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'manager')
