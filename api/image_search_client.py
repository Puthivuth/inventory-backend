"""
Client for Image Search Service
Provides methods to communicate with the image search microservice
"""

import requests
import logging
from typing import List, Dict, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class ImageSearchClient:
    """Client for communicating with the image search microservice"""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the client
        
        Args:
            base_url: Base URL of the image search service (e.g., http://localhost:8001)
        """
        self.base_url = base_url or getattr(
            settings, 
            'IMAGE_SEARCH_SERVICE_URL', 
            'http://localhost:8001'
        )
        self.timeout = 30  # seconds
    
    def health_check(self) -> Dict:
        """
        Check if the image search service is healthy
        
        Returns:
            Health status dictionary
        """
        try:
            response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    def index_product(self, product_id: int, image_url: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Index a product image in the vector database
        
        Args:
            product_id: Unique product identifier
            image_url: URL to the product image
            metadata: Additional metadata (product name, SKU, etc.)
            
        Returns:
            Indexing result dictionary
        """
        try:
            data = {
                "product_id": product_id,
                "image_url": image_url,
                "metadata": metadata or {}
            }
            
            response = requests.post(
                f"{self.base_url}/index/product",
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Successfully indexed product {product_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to index product {product_id}: {e}")
            return {
                "success": False,
                "product_id": product_id,
                "error": str(e)
            }
    
    def index_product_file(self, product_id: int, image_file, metadata: Optional[Dict] = None) -> Dict:
        """
        Index a product by uploading an image file
        
        Args:
            product_id: Unique product identifier
            image_file: File object or bytes
            metadata: Additional metadata
            
        Returns:
            Indexing result dictionary
        """
        try:
            files = {'file': image_file}
            data = {'product_id': product_id}
            
            if metadata:
                import json
                data['metadata'] = json.dumps(metadata)
            
            response = requests.post(
                f"{self.base_url}/index/upload",
                files=files,
                data=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Successfully indexed product {product_id} via upload")
            return result
            
        except Exception as e:
            logger.error(f"Failed to index product {product_id} via upload: {e}")
            return {
                "success": False,
                "product_id": product_id,
                "error": str(e)
            }
    
    def batch_index_products(self, products: List[Dict]) -> Dict:
        """
        Index multiple products in batch
        
        Args:
            products: List of product dictionaries with product_id and image_source
            
        Returns:
            Batch indexing summary
        """
        try:
            data = {"products": products}
            
            response = requests.post(
                f"{self.base_url}/index/batch",
                json=data,
                timeout=300  # 5 minutes for batch
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(
                f"Batch indexing complete: {result['successful']} successful, "
                f"{result['failed']} failed"
            )
            return result
            
        except Exception as e:
            logger.error(f"Batch indexing failed: {e}")
            return {
                "total": len(products),
                "successful": 0,
                "failed": len(products),
                "errors": [{"error": str(e)}]
            }
    
    def search_by_url(self, 
                     image_url: str, 
                     top_k: int = 10, 
                     score_threshold: float = 0.5) -> List[Dict]:
        """
        Search for similar products using an image URL
        
        Args:
            image_url: URL to the query image
            top_k: Number of results to return
            score_threshold: Minimum similarity score
            
        Returns:
            List of similar products with scores
        """
        try:
            params = {
                "image_url": image_url,
                "top_k": top_k,
                "score_threshold": score_threshold
            }
            
            response = requests.get(
                f"{self.base_url}/search/url",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            results = response.json()
            logger.info(f"Found {len(results)} similar products")
            return results
            
        except Exception as e:
            logger.error(f"Search by URL failed: {e}")
            return []
    
    def search_by_upload(self, 
                        image_file, 
                        top_k: int = 10, 
                        score_threshold: float = 0.5) -> List[Dict]:
        """
        Search for similar products by uploading an image
        
        Args:
            image_file: File object or bytes
            top_k: Number of results to return
            score_threshold: Minimum similarity score
            
        Returns:
            List of similar products with scores
        """
        try:
            files = {'file': image_file}
            params = {
                "top_k": top_k,
                "score_threshold": score_threshold
            }
            
            response = requests.post(
                f"{self.base_url}/search/upload",
                files=files,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            results = response.json()
            logger.info(f"Found {len(results)} similar products via upload")
            return results
            
        except Exception as e:
            logger.error(f"Search by upload failed: {e}")
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
            response = requests.delete(
                f"{self.base_url}/product/{product_id}",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            logger.info(f"Successfully deleted product {product_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete product {product_id}: {e}")
            return False
    
    def get_collection_info(self) -> Dict:
        """
        Get information about the vector database collection
        
        Returns:
            Collection information dictionary
        """
        try:
            response = requests.get(
                f"{self.base_url}/collection/info",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {}


# Singleton instance
_client_instance = None


def get_image_search_client() -> ImageSearchClient:
    """Get or create the singleton client instance"""
    global _client_instance
    if _client_instance is None:
        _client_instance = ImageSearchClient()
    return _client_instance
