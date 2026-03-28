"""
Image Search Service for Inventory Products
Handles object detection, embedding generation, and vector similarity search
Integrated directly into Django backend (no external microservice needed)
"""

import numpy as np
import cv2
from PIL import Image
import torch
from typing import List, Tuple, Dict, Optional
import logging
from pathlib import Path
import io
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from ultralytics import YOLO
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class ImageSearchService:
    """
    Service for image-based product search using:
    1. Object detection (YOLO)
    2. Image cropping
    3. Feature embedding (CLIP)
    4. Vector similarity search (Qdrant)
    """
    
    def __init__(self):
        """Initialize the image search service"""
        # Get settings from Django
        self.qdrant_path = getattr(settings, 'IMAGE_SEARCH_QDRANT_PATH', './qdrant_storage')
        self.collection_name = getattr(settings, 'IMAGE_SEARCH_COLLECTION_NAME', 'inventory_products')
        self.yolo_model = getattr(settings, 'IMAGE_SEARCH_YOLO_MODEL', 'yolov8n.pt')
        self.embedding_model_name = getattr(settings, 'IMAGE_SEARCH_EMBEDDING_MODEL', 'clip-ViT-B-32')
        self.detection_confidence = getattr(settings, 'IMAGE_SEARCH_DETECTION_CONFIDENCE', 0.25)
        
        # Initialize Qdrant client (local mode)
        try:
            self.qdrant_client = QdrantClient(path=self.qdrant_path)
            logger.info(f"Qdrant client initialized at {self.qdrant_path}")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            raise
        
        # Initialize YOLO for object detection
        try:
            self.detector = YOLO(self.yolo_model)
            logger.info(f"YOLO detector initialized with {self.yolo_model}")
        except Exception as e:
            logger.error(f"Failed to initialize YOLO detector: {e}")
            raise
        
        # Initialize CLIP model for embedding
        try:
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            self.embedding_dim = 512  # CLIP ViT-B/32 embedding dimension
            logger.info(f"CLIP embedding model initialized: {self.embedding_model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise
        
        # Create collection if it doesn't exist
        self._initialize_collection()
    
    def _initialize_collection(self):
        """Create Qdrant collection if it doesn't exist"""
        try:
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
            else:
                logger.info(f"Collection {self.collection_name} already exists")
        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            raise
    
    def detect_objects(self, image: np.ndarray, confidence_threshold: Optional[float] = None) -> List[Dict]:
        """
        Detect objects in the image using YOLO
        
        Args:
            image: Input image as numpy array (BGR format from cv2)
            confidence_threshold: Minimum confidence for detection
            
        Returns:
            List of detected objects with bounding boxes and confidence scores
        """
        if confidence_threshold is None:
            confidence_threshold = self.detection_confidence
            
        try:
            results = self.detector(image, conf=confidence_threshold, verbose=False)
            detections = []
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf[0].cpu().numpy())
                    class_id = int(box.cls[0].cpu().numpy())
                    class_name = result.names[class_id]
                    
                    detections.append({
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': confidence,
                        'class': class_name,
                        'class_id': class_id
                    })
            
            logger.info(f"Detected {len(detections)} objects")
            return detections
            
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            return []
    
    def crop_image(self, image: np.ndarray, bbox: List[int], padding: int = 10) -> np.ndarray:
        """
        Crop image based on bounding box
        
        Args:
            image: Input image as numpy array
            bbox: Bounding box [x1, y1, x2, y2]
            padding: Additional padding around the bbox
            
        Returns:
            Cropped image as numpy array
        """
        try:
            x1, y1, x2, y2 = bbox
            h, w = image.shape[:2]
            
            # Add padding while keeping within image bounds
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(w, x2 + padding)
            y2 = min(h, y2 + padding)
            
            cropped = image[y1:y2, x1:x2]
            return cropped
            
        except Exception as e:
            logger.error(f"Image cropping failed: {e}")
            return image
    
    def generate_embedding(self, image: np.ndarray) -> np.ndarray:
        """
        Generate embedding vector for an image
        
        Args:
            image: Input image as numpy array (BGR format)
            
        Returns:
            Embedding vector as numpy array
        """
        try:
            # Convert BGR to RGB if needed
            if len(image.shape) == 3 and image.shape[2] == 3:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image
            
            # Convert to PIL Image for the embedding model
            pil_image = Image.fromarray(image_rgb)
            
            # Generate embedding
            embedding = self.embedding_model.encode(pil_image, convert_to_numpy=True)
            
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    def load_image_from_url(self, url: str) -> Optional[np.ndarray]:
        """
        Load image from URL
        
        Args:
            url: Image URL
            
        Returns:
            Image as numpy array or None if failed
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            return image
        except Exception as e:
            logger.error(f"Failed to load image from URL {url}: {e}")
            return None
    
    def load_image_from_file(self, file_path: str) -> Optional[np.ndarray]:
        """
        Load image from file path
        
        Args:
            file_path: Path to image file
            
        Returns:
            Image as numpy array or None if failed
        """
        try:
            image = cv2.imread(file_path)
            return image
        except Exception as e:
            logger.error(f"Failed to load image from file {file_path}: {e}")
            return None
    
    def load_image_from_bytes(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """
        Load image from bytes
        
        Args:
            image_bytes: Image data as bytes
            
        Returns:
            Image as numpy array or None if failed
        """
        try:
            image_array = np.frombuffer(image_bytes, dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            return image
        except Exception as e:
            logger.error(f"Failed to load image from bytes: {e}")
            return None
    
    def index_product_image(self, 
                           product_id: int, 
                           image_source: str,
                           metadata: Optional[Dict] = None,
                           image_bytes: Optional[bytes] = None) -> Dict:
        """
        Index a product image in the vector database
        
        Args:
            product_id: Unique product identifier
            image_source: URL or file path to the product image
            metadata: Additional metadata to store with the vector
            image_bytes: Optional image data as bytes (overrides image_source)
            
        Returns:
            Result dictionary with status and details
        """
        try:
            # Load image
            if image_bytes:
                image = self.load_image_from_bytes(image_bytes)
            elif image_source.startswith('http'):
                image = self.load_image_from_url(image_source)
            else:
                image = self.load_image_from_file(image_source)
            
            if image is None:
                return {
                    'success': False,
                    'error': f'Failed to load image: {image_source}',
                    'product_id': product_id
                }
            
            # Detect objects
            detections = self.detect_objects(image)
            
            if not detections:
                # No objects detected, use full image
                logger.info(f"No objects detected for product {product_id}, using full image")
                embedding = self.generate_embedding(image)
                
                point = PointStruct(
                    id=product_id,
                    vector=embedding.tolist(),
                    payload={
                        'product_id': product_id,
                        'image_source': image_source,
                        'detection_type': 'full_image',
                        **(metadata or {})
                    }
                )
                
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=[point]
                )
                
                return {
                    'success': True,
                    'product_id': product_id,
                    'detection_type': 'full_image',
                    'detections_count': 0
                }
            else:
                # Use the first detected object (highest confidence)
                best_detection = max(detections, key=lambda x: x['confidence'])
                cropped_image = self.crop_image(image, best_detection['bbox'])
                embedding = self.generate_embedding(cropped_image)
                
                point = PointStruct(
                    id=product_id,
                    vector=embedding.tolist(),
                    payload={
                        'product_id': product_id,
                        'image_source': image_source,
                        'detection_type': 'object',
                        'detected_class': best_detection['class'],
                        'confidence': best_detection['confidence'],
                        'bbox': best_detection['bbox'],
                        **(metadata or {})
                    }
                )
                
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=[point]
                )
                
                return {
                    'success': True,
                    'product_id': product_id,
                    'detection_type': 'object',
                    'detected_class': best_detection['class'],
                    'confidence': best_detection['confidence'],
                    'detections_count': len(detections)
                }
            
        except Exception as e:
            logger.error(f"Failed to index product {product_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'product_id': product_id
            }
    
    def search_similar_products(self, 
                                query_image: np.ndarray, 
                                top_k: int = 10,
                                score_threshold: float = 0.5) -> List[Dict]:
        """
        Search for similar products using an image query
        
        Args:
            query_image: Query image as numpy array
            top_k: Number of top results to return
            score_threshold: Minimum similarity score threshold
            
        Returns:
            List of similar products with scores
        """
        try:
            # Detect objects in query image
            detections = self.detect_objects(query_image)
            
            if detections:
                # Use the best detection
                best_detection = max(detections, key=lambda x: x['confidence'])
                query_image = self.crop_image(query_image, best_detection['bbox'])
                logger.info(f"Using detected object for search: {best_detection['class']}")
            else:
                logger.info("No objects detected in query, using full image")
            
            # Generate embedding for query image
            query_embedding = self.generate_embedding(query_image)
            
            # Search in Qdrant
            search_response = self.qdrant_client.query_points(
                collection_name=self.collection_name,
                query=query_embedding.tolist(),
                limit=top_k,
                score_threshold=score_threshold
            )
            search_results = search_response.points

            # Format results
            results = []
            for result in search_results:
                results.append({
                    'product_id': result.payload['product_id'],
                    'similarity_score': result.score,
                    'image_source': result.payload.get('image_source'),
                    'detection_type': result.payload.get('detection_type'),
                    'detected_class': result.payload.get('detected_class'),
                    'metadata': {k: v for k, v in result.payload.items() 
                               if k not in ['product_id', 'image_source', 'detection_type', 'detected_class', 'confidence', 'bbox']}
                })
            
            logger.info(f"Found {len(results)} similar products")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def delete_product(self, product_id: int) -> bool:
        """
        Delete a product from the vector database
        
        Args:
            product_id: Product ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector=[product_id]
            )
            logger.info(f"Deleted product {product_id} from vector database")
            return True
        except Exception as e:
            logger.error(f"Failed to delete product {product_id}: {e}")
            return False
    
    def get_collection_info(self) -> Dict:
        """
        Get information about the collection
        
        Returns:
            Collection information
        """
        try:
            info = self.qdrant_client.get_collection(self.collection_name)
            return {
                'name': info.name,
                'vectors_count': info.vectors_count,
                'points_count': info.points_count,
                'status': info.status
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {}
    
    def batch_index_products(self, products: List[Dict]) -> Dict:
        """
        Index multiple products in batch
        
        Args:
            products: List of product dictionaries with 'product_id' and 'image_source'
            
        Returns:
            Summary of indexing results
        """
        results = {
            'total': len(products),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        for product in products:
            product_id = product.get('product_id')
            image_source = product.get('image_source')
            metadata = product.get('metadata', {})
            
            if not product_id or not image_source:
                results['failed'] += 1
                results['errors'].append({
                    'product_id': product_id,
                    'error': 'Missing product_id or image_source'
                })
                continue
            
            result = self.index_product_image(product_id, image_source, metadata)
            
            if result['success']:
                results['successful'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'product_id': product_id,
                    'error': result.get('error', 'Unknown error')
                })
        
        return results


# Singleton instance
_service_instance = None


def get_service() -> ImageSearchService:
    """Get or create the singleton service instance"""
    global _service_instance
    if _service_instance is None:
        logger.info("Initializing ImageSearchService...")
        _service_instance = ImageSearchService()
    return _service_instance
