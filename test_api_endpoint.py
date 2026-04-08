"""
Test the image search API endpoint directly
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.conf import settings
import json

User = get_user_model()

print("=" * 60)
print("API ENDPOINT TEST")
print("=" * 60)

# Get or create test user
try:
    user = User.objects.get(username='testuser')
except User.DoesNotExist:
    user = User.objects.create_user(username='testuser', password='testpass')
    print(f"✓ Created test user: testuser")

# Get auth token
from rest_framework.authtoken.models import Token
token, created = Token.objects.get_or_create(user=user)
print(f"✓ Using token: {token.key[:20]}...")

# Initialize client
client = APIClient()
client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

# Get first image
IMAGES_DIR = os.path.join(settings.BASE_DIR, '..', 'Images')
image_files = [f for f in os.listdir(IMAGES_DIR) 
               if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'))]

if image_files:
    test_image = image_files[0]
    test_image_path = os.path.join(IMAGES_DIR, test_image)
    
    print(f"\n[TEST] Uploading image: {test_image}")
    
    with open(test_image_path, 'rb') as f:
        response = client.post(
            '/api/search-products/',
            {'file': f, 'top_k': 10, 'score_threshold': 0.3},
            format='multipart'
        )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('results'):
            print(f"\n✓ SUCCESS: Found {len(data['results'])} similar products")
        else:
            print(f"\n⚠ Empty results: {data}")
else:
    print("✗ No images found")

print("\n" + "=" * 60)
