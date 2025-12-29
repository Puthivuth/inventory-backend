from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.permissions import AllowAny
from .models import ActivityLog, User
from .serializers import UserSerializer
import logging

logger = logging.getLogger(__name__)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        
        # Log successful login
        ActivityLog.objects.create(
            user=user,
            actionType='USER_LOGIN',
            description=f"User {user.username} logged in successfully"
        )
        
        return Response({
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
            'role': user.role
        }, status=status.HTTP_200_OK)

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Validate input data
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        
        # Basic validation
        if not username or not password or not email:
            return Response({
                'detail': 'Username, password, and email are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            return Response({
                'detail': 'Username already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return Response({
                'detail': 'Email already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create user using serializer
        serializer = UserSerializer(data={
            'username': username,
            'password': password,
            'email': email,
            'role': 'staff'  # Default role for new registrations (lowercase to match model choices)
        })
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Create auth token for the new user
            token, created = Token.objects.get_or_create(user=user)
            
            # Log successful registration
            ActivityLog.objects.create(
                user=user,
                actionType='USER_CREATED',
                description=f"New user {user.username} registered successfully"
            )
            
            return Response({
                'token': token.key,
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }, status=status.HTTP_201_CREATED)
        else:
            # Log validation errors for debugging
            logger.error(f"Registration validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)