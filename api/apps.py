from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    
    def ready(self):
        import api.signals
        
        # Preload image search models on startup (only once)
        try:
            # Use environment variable to track if models are already loaded
            import os
            if not os.environ.get('IMAGE_SEARCH_MODELS_PRELOADED'):
                logger.info("Preloading image search models on startup...")
                from django.conf import settings
                from .image_search.model_loader import preload_models
                
                yolo_model = getattr(settings, 'IMAGE_SEARCH_YOLO_MODEL', 'yolov8n.pt')
                embedding_model = getattr(settings, 'IMAGE_SEARCH_EMBEDDING_MODEL', 'clip-ViT-B-32')
                
                preload_models(yolo_model, embedding_model)
                os.environ['IMAGE_SEARCH_MODELS_PRELOADED'] = '1'
        except Exception as e:
            logger.warning(f"Model preload failed (non-critical): {e}")

