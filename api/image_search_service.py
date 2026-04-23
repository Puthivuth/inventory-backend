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
_is_auto_indexing = False  # Guard against recursive auto-indexing
_skip_auto_index = False   # Used by management command to skip auto-indexing

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
        try:
            import clip
        except ImportError as e:
            print(f"ERROR: Failed to import CLIP: {e}")
            print("Make sure you have: pip install openai-clip torch torchvision")
            raise
        
        device = _get_device()
        try:
            print(f"DEBUG: Loading CLIP model on {device}...")
            _clip_model, _clip_preprocess = clip.load("ViT-B/32", device=device)
            print(f"DEBUG: CLIP model loaded successfully")
        except Exception as e:
            print(f"ERROR: Failed to load CLIP model: {e}")
            print(f"DEBUG: Error details: {type(e).__name__}: {str(e)}")
            raise
    return _clip_model, _clip_preprocess

def _cleanup_lock_files():
    """Remove lock files that might be blocking Qdrant"""
    try:
        # Remove lock files more aggressively
        import shutil
        
        # Check for .lock file in main qdrant path
        lock_file = os.path.join(QDRANT_PATH, ".lock")
        if os.path.exists(lock_file):
            print(f"DEBUG: Removing lock file: {lock_file}")
            try:
                os.remove(lock_file)
            except:
                pass
        
        # Look for lock files in subdirectories
        lock_patterns = [
            os.path.join(QDRANT_PATH, "*.lock"),
            os.path.join(QDRANT_PATH, "**/*.lock"),
        ]
        for pattern in lock_patterns:
            for lock_file in glob.glob(pattern, recursive=True):
                try:
                    print(f"DEBUG: Removing lock file: {lock_file}")
                    os.remove(lock_file)
                except Exception as e:
                    print(f"DEBUG: Could not remove lock file {lock_file}: {e}")
        
        time.sleep(0.5)  # Brief delay to ensure locks are released
    except Exception as e:
        print(f"DEBUG: Error cleaning up lock files: {e}")

def _ensure_qdrant_ready():
    """Ensure Qdrant storage is accessible and not locked"""
    try:
        # Remove any lock files
        _cleanup_lock_files()
        
        # Verify directory exists
        os.makedirs(QDRANT_PATH, exist_ok=True)
        
        # Check if collection files are intact
        collection_dir = os.path.join(QDRANT_PATH, "collection")
        if os.path.exists(collection_dir):
            print(f"DEBUG: Collection directory found with {len(os.listdir(collection_dir)) if os.path.isdir(collection_dir) else 0} items")
        
        return True
    except Exception as e:
        print(f"ERROR: Failed to ensure Qdrant is ready: {e}")
        return False

def initialize_qdrant(auto_index=True):
    """Initialize Qdrant client and create collection if needed.
    
    Args:
        auto_index: If True and collection is empty, auto-index products from database
    """
    global _client_instance, _is_auto_indexing, _skip_auto_index
    
    try:
        # Ensure Qdrant storage is ready and clean
        _ensure_qdrant_ready()
        
        # Create or reuse client
        if _client_instance is None:
            _client_instance = QdrantClient(path=QDRANT_PATH)
        
        try:
            # Check if collection exists and how many points it has
            collection_info = _client_instance.get_collection(COLLECTION_NAME)
            points_count = collection_info.points_count if hasattr(collection_info, 'points_count') else 0
            
            # If collection is empty, auto-index (unless disabled)
            if auto_index and not _skip_auto_index and points_count == 0 and not _is_auto_indexing:
                print(f"INFO: Collection '{COLLECTION_NAME}' is empty. Auto-indexing products from database...")
                _is_auto_indexing = True
                try:
                    _auto_index_products()
                finally:
                    _is_auto_indexing = False
                    
        except Exception as e:
            # Collection doesn't exist, create it
            if not _skip_auto_index:
                print(f"Creating new collection: {str(e)}")
            from qdrant_client.models import VectorParams, Distance
            _client_instance.recreate_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=VECTOR_SIZE,
                    distance=Distance.COSINE
                )
            )
            # Auto-index after creation if enabled and not already doing so
            if auto_index and not _skip_auto_index and not _is_auto_indexing:
                print(f"New collection created. Auto-indexing products from database...")
                _is_auto_indexing = True
                try:
                    _auto_index_products()
                finally:
                    _is_auto_indexing = False
        
        return _client_instance
    except Exception as e:
        raise Exception(f"Failed to initialize Qdrant: {str(e)}")

def _auto_index_products():
    """Automatically index all products with images from the database"""
    try:
        from api.models import Product
        
        products = Product.objects.filter(image__isnull=False).exclude(image="")
        count = 0
        for product in products:
            try:
                if index_product_image(
                    product.productId,
                    product.image,
                    product.productName,
                    product.skuCode
                ):
                    count += 1
            except Exception as e:
                print(f"Failed to index {product.productName}: {str(e)}")
        
        print(f"Auto-indexed {count} products from database")
    except Exception as e:
        print(f"Error during auto-indexing: {str(e)}")

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
            # First check if it's a media path (from database)
            if image_source.startswith('/media/'):
                # Handle relative media paths - convert to absolute file path
                media_path = os.path.join(settings.BASE_DIR, image_source.lstrip('/'))
                if not os.path.exists(media_path):
                    # Try alternate path
                    media_path = os.path.join(settings.BASE_DIR, '..', 'backend', image_source.lstrip('/'))
                if os.path.exists(media_path):
                    image = Image.open(media_path)
                else:
                    raise FileNotFoundError(f"Media file not found: {media_path}")
            elif image_source.startswith(('http://', 'https://')):
                # Download from URL (only if it's a real HTTP URL, not localhost)
                if 'localhost' in image_source or '127.0.0.1' in image_source:
                    # Try to convert localhost URL to file path
                    path = image_source.replace('http://localhost:8000', '').replace('http://127.0.0.1:8000', '')
                    if path.startswith('/'):
                        media_path = os.path.join(settings.BASE_DIR, path.lstrip('/'))
                        if os.path.exists(media_path):
                            image = Image.open(media_path)
                        else:
                            raise FileNotFoundError(f"Media file not found: {media_path}")
                    else:
                        raise FileNotFoundError(f"Could not convert localhost URL to file path: {image_source}")
                else:
                    response = requests.get(image_source, timeout=10)
                    image = Image.open(io.BytesIO(response.content))
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

def _search_qdrant(client, query_vector, top_k, score_threshold):
    """
    Search in Qdrant collection.
    
    Args:
        client: QdrantClient instance
        query_vector: Query embedding as list
        top_k: Number of results
        score_threshold: Minimum similarity score
    
    Returns:
        List of ScoredPoint objects with payload
    """
    try:
        # Use the correct search method for qdrant-client
        # Handle both older and newer API versions
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k,
            score_threshold=score_threshold,
            with_payload=True,
        )
        return results if results else []
        
    except AttributeError as e:
        # Fallback for older versions - try alternative method
        print(f"DEBUG: Standard search method not available, trying alternative approach: {str(e)}")
        try:
            # Some versions might use search_batch or similar
            from qdrant_client.models import NamedVector
            results = client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_vector,
                limit=top_k,
                with_payload=True,
            )
            return results if results else []
        except Exception as e2:
            print(f"Error searching Qdrant (both methods failed): {str(e2)}")
            return []
    except Exception as e:
        print(f"Error searching Qdrant: {str(e)}")
        return []

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
        
        # Debug: Check collection state
        try:
            collection_info = client.get_collection(COLLECTION_NAME)
            print(f"DEBUG: Collection '{COLLECTION_NAME}' has {collection_info.points_count} points")
        except Exception as e:
            print(f"DEBUG: Error checking collection: {e}")
        
        # Get query embedding
        query_embedding = get_image_embedding(image_source)
        
        # Search using adaptive method
        search_points = _search_qdrant(client, query_embedding.tolist(), top_k, score_threshold)
        print(f"DEBUG: Search returned {len(search_points) if search_points else 0} results")
        
        # Import Product model here to avoid circular imports
        from api.models import Product
        
        # Format results and enrich with product data
        results = []
        
        for point in search_points:
            # Safely extract payload - it can be dict or None
            if point.payload is None:
                payload = {}
            elif isinstance(point.payload, dict):
                payload = point.payload
            elif hasattr(point.payload, '__dict__'):
                # Convert object to dict if needed
                payload = point.payload.__dict__
            else:
                payload = {}
            
            # Safely extract score
            score = point.score if hasattr(point, 'score') else 0
            
            result_data = {
                "product_id": payload.get("product_id") if isinstance(payload, dict) else None,
                "product_name": payload.get("product_name") if isinstance(payload, dict) else None,
                "sku_code": payload.get("sku_code") if isinstance(payload, dict) else None,
                "image_url": payload.get("image_url") if isinstance(payload, dict) else None,
                "similarity_score": score,
            }
            
            # Try to enrich with product data from database
            try:
                product_id = payload.get("product_id") if isinstance(payload, dict) else None
                if product_id:
                    product = Product.objects.get(productId=product_id)
                    result_data["sale_price"] = float(product.salePrice)
                    result_data["cost_price"] = float(product.costPrice)
                else:
                    result_data["sale_price"] = 0.0
                    result_data["cost_price"] = 0.0
            except Product.DoesNotExist:
                # If product not in database, use default values
                result_data["sale_price"] = 0.0
                result_data["cost_price"] = 0.0
            except Exception as e:
                # Log error but don't fail the search
                product_id = payload.get("product_id") if isinstance(payload, dict) else None
                if product_id:
                    print(f"Warning: Could not fetch product data for ID {product_id}: {e}")
                result_data["sale_price"] = 0.0
                result_data["cost_price"] = 0.0
            
            results.append(result_data)
        
        print(f"DEBUG: Returning {len(results)} formatted results")
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
