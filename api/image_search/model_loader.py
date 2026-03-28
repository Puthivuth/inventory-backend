"""
Model loader and downloader for YOLO and CLIP models
Ensures models are downloaded before first use to avoid timeout
"""

import logging
import os
from pathlib import Path
from typing import Optional
import torch

logger = logging.getLogger(__name__)


def download_yolo_model(model_name: str = 'yolov8n.pt') -> bool:
    """
    Download YOLO model if not already present
    
    Args:
        model_name: Name of the YOLO model (e.g., 'yolov8n.pt')
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get the default YOLO cache directory
        yolo_cache_dir = Path.home() / '.cache' / 'ultralytics' / 'hub'
        model_path = yolo_cache_dir / model_name
        
        # Check if model already exists
        if model_path.exists():
            logger.info(f"YOLO model {model_name} already cached at {model_path}")
            return True
        
        logger.info(f"Downloading YOLO model {model_name}...")
        from ultralytics import YOLO
        
        # Loading the model triggers download
        model = YOLO(model_name)
        logger.info(f"✓ Successfully downloaded YOLO model {model_name}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to download YOLO model {model_name}: {e}")
        return False


def download_clip_model(model_name: str = 'clip-ViT-B-32') -> bool:
    """
    Download CLIP model if not already present
    
    Args:
        model_name: Name of the CLIP model (e.g., 'clip-ViT-B-32')
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Downloading CLIP model {model_name}...")
        from sentence_transformers import SentenceTransformer
        
        # Loading the model triggers download
        model = SentenceTransformer(model_name)
        logger.info(f"✓ Successfully downloaded CLIP model {model_name}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to download CLIP model {model_name}: {e}")
        return False


def check_gpu_available() -> bool:
    """
    Check if GPU is available for model inference
    
    Returns:
        True if GPU is available, False otherwise
    """
    is_available = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if is_available else "None"
    logger.info(f"GPU available: {is_available} ({gpu_name})")
    return is_available


def preload_models(yolo_model: str = 'yolov8n.pt', 
                   clip_model: str = 'clip-ViT-B-32') -> dict:
    """
    Preload both YOLO and CLIP models
    Should be called during Django startup
    
    Args:
        yolo_model: Name of YOLO model
        clip_model: Name of CLIP model
        
    Returns:
        Dictionary with status of each model download
    """
    logger.info("=" * 60)
    logger.info("Starting model preload...")
    logger.info("=" * 60)
    
    results = {
        'yolo_success': False,
        'clip_success': False,
        'gpu_available': False,
        'timestamp': None
    }
    
    # Check GPU
    results['gpu_available'] = check_gpu_available()
    
    # Download YOLO
    logger.info("\n[1/2] Downloading YOLO model...")
    results['yolo_success'] = download_yolo_model(yolo_model)
    
    # Download CLIP
    logger.info("\n[2/2] Downloading CLIP model...")
    results['clip_success'] = download_clip_model(clip_model)
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Model Preload Summary:")
    logger.info(f"  YOLO: {'✓ OK' if results['yolo_success'] else '✗ FAILED'}")
    logger.info(f"  CLIP: {'✓ OK' if results['clip_success'] else '✗ FAILED'}")
    logger.info(f"  GPU: {'✓ Available' if results['gpu_available'] else '✗ Not Available'}")
    logger.info("=" * 60 + "\n")
    
    return results
