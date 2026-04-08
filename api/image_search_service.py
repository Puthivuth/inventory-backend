"""
Image Search Service using CLIP and Qdrant Vector Database
"""
import os
import io
import numpy as np
from PIL import Image
import torch
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
import requests
from typing import List, Dict, Any
import time
import glob
import atexit
import sys

# Configuration
QDRANT_PATH = os.path.join(settings.BASE_DIR, "qdrant_storage")
COLLECTION_NAME = "product_images"
VECTOR_SIZE = 512  # CLIP embedding size

# Global instances (lazy-initialized)
_client_instance = None
_clip_model = None
_clip_preprocess = None
_device = None

def _cleanup_client():
    """Properly close Qdrant client on shutdown"""
    global _client_instance
    try:
        if _client_instance is not None and hasattr(_client_instance, 'close'):
            _client_instance.close()
    except:
        pass
    _client_instance = None

# Register cleanup on exit
atexit.register(_cleanup_client)

def _get_device():
    """Get the device for PyTorch (lazy-initialized)"""
    global _device
    if _device is None:
        _device = "cuda" if torch.cuda.is_available() else "cpu"
    return _device

def _get_clip_model():
    """Get CLIP model (lazy-initialized)"""
    global _clip_model, _clip_preprocess
    if _clip_model is None:
        import clip
        device = _get_device()
        _clip_model, _clip_preprocess = clip.load("ViT-B/32", device=device)
    return _clip_model, _clip_preprocess

def _cleanup_lock_files():
    """Remove lock files that might be blocking Qdrant"""
    try:
        # Remove lock files
        lock_patterns = [
            os.path.join(QDRANT_PATH, "*.lock"),
            os.path.join(QDRANT_PATH, "**/*.lock"),
        ]
        for pattern in lock_patterns:
            for lock_file in glob.glob(pattern, recursive=True):
                try:
                    os.remove(lock_file)
                except:
                    pass
        time.sleep(0.5)  # Brief delay to ensure locks are released
    except:
        pass

def initialize_qdrant():
    """Initialize Qdrant client and create collection if needed"""
    global _client_instance
    
    try:
        os.makedirs(QDRANT_PATH, exist_ok=True)
        
        # Clean up any lock files
        _cleanup_lock_files()
        
        # Create or reuse client
        if _client_instance is None:
            _client_instance = QdrantClient(path=QDRANT_PATH)
        
        try:
            # Check if collection exists
            _client_instance.get_collection(COLLECTION_NAME)
        except Exception:
            # Create collection if it doesn't exist
            from qdrant_client.models import VectorParams, Distance
            _client_instance.recreate_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=VECTOR_SIZE,
                    distance=Distance.COSINE
                ),
            )
        
        return _client_instance
    except Exception as e:
        raise Exception(f"Failed to initialize Qdrant: {str(e)}")

def get_image_embedding(image_source):
    """
    Generate embedding for an image
    
    Args:
        image_source: PIL Image, file path, or URL
    
    Returns:
        numpy array of embedding
    """
    try:
        # Handle different image sources
        if isinstance(image_source, str):
            if image_source.startswith(('http://', 'https://')):
                # Download from URL
                response = requests.get(image_source, timeout=10)
                image = Image.open(io.BytesIO(response.content))
            elif image_source.startswith('/media/'):
                # Handle relative media paths - convert to absolute file path
                media_path = os.path.join(settings.BASE_DIR, '..', 'backend', image_source.lstrip('/'))
                if not os.path.exists(media_path):
                    # Try alternate path
                    media_path = os.path.join(settings.BASE_DIR, image_source.lstrip('/'))
                if os.path.exists(media_path):
                    image = Image.open(media_path)
                else:
                    raise FileNotFoundError(f"Media file not found: {media_path}")
            else:
                # Load from file path
                if os.path.exists(image_source):
                    image = Image.open(image_source)
                else:
                    raise FileNotFoundError(f"Image file not found: {image_source}")
        elif isinstance(image_source, UploadedFile):
            # Handle Django uploaded file
            image = Image.open(image_source)
        elif isinstance(image_source, Image.Image):
            # Already a PIL Image
            image = image_source
        else:
            raise ValueError("Invalid image source type")
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Get lazy-loaded CLIP model
        model, preprocess = _get_clip_model()
        device = _get_device()
        
        # Preprocess and get embedding
        image_tensor = preprocess(image).unsqueeze(0).to(device)
        
        with torch.no_grad():
            embedding = model.encode_image(image_tensor)
        
        # Normalize embedding
        embedding = embedding / embedding.norm(dim=-1, keepdim=True)
        return embedding[0].cpu().numpy().astype(np.float32)
    
    except Exception as e:
        print(f"Error generating embedding: {str(e)}")
        raise

def index_product_image(product_id: int, image_url: str, product_name: str = "", sku_code: str = ""):
    """
    Add or update a product image in the vector database
    
    Args:
        product_id: Unique product ID
        image_url: URL or path to image
        product_name: Product name
        sku_code: Product SKU
    """
    try:
        client = initialize_qdrant()
        
        # Get embedding
        embedding = get_image_embedding(image_url)
        
        # Create point with metadata
        point = PointStruct(
            id=product_id,
            vector=embedding.tolist(),
            payload={
                "product_id": product_id,
                "image_url": image_url,
                "product_name": product_name,
                "sku_code": sku_code,
            }
        )
        
        # Upsert point (insert or update)
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[point]
        )
        
        return True
    except Exception as e:
        print(f"Error indexing product image: {str(e)}")
        return False

def search_similar_images(
    image_source,
    top_k: int = 10,
    score_threshold: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Search for similar products based on image
    
    Args:
        image_source: Image to search by
        top_k: Number of top results to return
        score_threshold: Minimum similarity score (0-1)
    
    Returns:
        List of matching products with similarity scores
    """
    try:
        client = initialize_qdrant()
        
        # Get query embedding
        query_embedding = get_image_embedding(image_source)
        
        # Search in Qdrant using query_points
        search_result = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding.tolist(),
            limit=top_k,
            score_threshold=score_threshold,
        )
        
        # Import Product model here to avoid circular imports
        from api.models import Product
        
        # Format results and enrich with product data
        results = []
        for point in search_result.points:
            result_data = {
                "product_id": point.payload.get("product_id"),
                "product_name": point.payload.get("product_name"),
                "sku_code": point.payload.get("sku_code"),
                "image_url": point.payload.get("image_url"),
                "similarity_score": point.score,
            }
            
            # Try to enrich with product data from database
            try:
                product_id = point.payload.get("product_id")
                product = Product.objects.get(productId=product_id)
                result_data["sale_price"] = float(product.salePrice)
                result_data["cost_price"] = float(product.costPrice)
            except Product.DoesNotExist:
                # If product not in database, use default values
                result_data["sale_price"] = 0.0
                result_data["cost_price"] = 0.0
            except Exception as e:
                # Log error but don't fail the search
                print(f"Warning: Could not fetch product data for ID {point.payload.get('product_id')}: {e}")
                result_data["sale_price"] = 0.0
                result_data["cost_price"] = 0.0
            
            results.append(result_data)
        
        return results
    
    except Exception as e:
        print(f"Error searching images: {str(e)}")
        return []

def get_collection_info():
    """Get information about the vector collection"""
    try:
        client = initialize_qdrant()
        info = client.get_collection(COLLECTION_NAME)
        return {
            "collection_name": COLLECTION_NAME,
            "vector_size": VECTOR_SIZE,
            "points_count": info.points_count,
        }
    except Exception as e:
        print(f"Error getting collection info: {str(e)}")
        return None
