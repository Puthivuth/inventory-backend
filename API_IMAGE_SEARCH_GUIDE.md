# Image Search Implementation Guide

## Overview

This document explains how to set up and use the image search feature using CLIP embeddings and Qdrant vector database.

## Architecture

### Components

1. **CLIP Model** - OpenAI's vision-language model for generating image embeddings
2. **Qdrant** - Vector database for storing and searching embeddings
3. **Django Views** - API endpoints for search operations
4. **Frontend** - React/Next.js UI for uploading and searching images

### How It Works

1. **Image Upload** - User uploads an image through the frontend
2. **Embedding Generation** - CLIP model converts the image to a 512-dimensional vector
3. **Vector Search** - Query vector is compared against stored vectors using cosine similarity
4. **Results** - Top matching products are returned with similarity scores

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

The requirements include:

- `qdrant-client==2.7.0` - Qdrant client library
- `clip==1.0` - CLIP model
- `torch==2.1.0` - PyTorch (for CLIP)
- `torchvision==0.16.0` - Vision utilities

### 2. Initialize Qdrant Vector Database

Run the initialization script:

```bash
python manage.py shell
```

Then in the shell:

```python
from api.scripts.initialize_image_search import initialize_image_search, index_local_images, index_product_database_images

# Initialize Qdrant
initialize_image_search()

# Index images from the /Images directory
index_local_images()

# Option: Also index product images from database
# index_product_database_images()
```

Or use the Django management command:

```bash
python manage.py initialize_image_search
```

Options:

```bash
python manage.py initialize_image_search --local-only      # Only local images
python manage.py initialize_image_search --database-only   # Only database images
```

### 3. Verify Setup

```python
from api.image_search_service import get_collection_info

info = get_collection_info()
print(f"Collection: {info['collection_name']}")
print(f"Points: {info['points_count']}")  # Should show number of indexed images
```

## API Endpoints

### 1. Search by Image Upload

**POST** `/api/search-products/`

Upload an image file to search for similar products.

```javascript
const formData = new FormData();
formData.append("file", imageFile);
formData.append("top_k", 10);
formData.append("score_threshold", 0.5);

const response = await fetch("/api/search-products/", {
  method: "POST",
  headers: {
    Authorization: `Token ${token}`,
  },
  body: formData,
});

const data = await response.json();
// Returns: { success: true, results: [...], count: N }
```

### 2. Search by Image URL

**GET** `/api/search-products-url/`

Search using an image URL.

```javascript
const params = new URLSearchParams({
  image_url: "https://example.com/image.jpg",
  top_k: 10,
  score_threshold: 0.5,
});

const response = await fetch(`/api/search-products-url/?${params}`, {
  headers: {
    Authorization: `Token ${token}`,
  },
});

const data = await response.json();
```

### 3. Index Product Images

**POST** `/api/index-product-images/`

Index or reindex a product image.

Single product:

```javascript
const response = await fetch("/api/index-product-images/", {
  method: "POST",
  headers: {
    Authorization: `Token ${token}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    product_id: 123,
    image_url: "https://example.com/product.jpg",
    product_name: "Product Name",
    sku_code: "SKU-123",
  }),
});
```

Batch indexing:

```javascript
const response = await fetch("/api/index-product-images/", {
  method: "POST",
  headers: {
    Authorization: `Token ${token}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    mode: "batch",
    products: [
      {
        product_id: 1,
        image_url: "url1",
        product_name: "P1",
        sku_code: "SKU1",
      },
      {
        product_id: 2,
        image_url: "url2",
        product_name: "P2",
        sku_code: "SKU2",
      },
    ],
  }),
});
```

## Response Format

### Search Results

```json
{
  "success": true,
  "results": [
    {
      "product_id": 123,
      "product_name": "Mercedes AMG F1",
      "sku_code": "SKU-F1-001",
      "image_url": "/path/to/image.jpg",
      "similarity_score": 0.85
    },
    ...
  ],
  "count": 5,
  "parameters": {
    "top_k": 10,
    "score_threshold": 0.5
  }
}
```

## Configuration Parameters

### top_k

- **Description**: Number of top results to return
- **Default**: 10
- **Range**: 1-50

### score_threshold

- **Description**: Minimum similarity score (cosine similarity)
- **Default**: 0.5
- **Range**: 0.0-1.0
- **Lower value** = More results but lower quality
- **Higher value** = Fewer results but higher quality

## Troubleshooting

### Issue: CUDA out of memory

**Solution**: Change device to CPU in `image_search_service.py`:

```python
device = "cpu"  # Instead of "cuda"
```

### Issue: Qdrant connection error

**Solution**: Ensure Qdrant storage directory exists:

```bash
mkdir -p backend/qdrant_storage
```

### Issue: Missing images during indexing

**Solution**: Verify image paths and formats:

```python
from api.scripts.initialize_image_search import index_local_images
import os

# Check images directory
IMAGES_DIR = '/path/to/Images'
print(os.listdir(IMAGES_DIR))
```

### Issue: Slow initial indexing

This is normal for the first run as CLIP downloads model (~350MB) and processes all images.
Subsequent searches will be much faster.

## Performance Notes

- **First boot**: CLIP model download (~350MB) + initial indexing time
- **Search time**: ~100-500ms depending on number of indexed images
- **Disk space**: ~1GB for Qdrant + ~350MB for CLIP model
- **Memory**: ~2GB during indexing, ~500MB during searches

## Frontend Integration

The frontend already has the UI ready. Just ensure:

1. Authentication token is set correctly
2. API endpoints match the backend URLs
3. Image upload form uses multipart/form-data

The `ImageSearchDialog` component in `frontend/components/inventory/image-search/image-search-dialog.tsx` handles:

- Image file upload
- URL-based search
- Parameter adjustment (top_k, score_threshold)
- Result display with similarity scores

## Next Steps

1. Install requirements in backend: `pip install -r requirements.txt`
2. Initialize the vector database using the management command
3. Test the endpoints using curl or Postman
4. The frontend will automatically work once the backend is running

```bash
# Terminal 1: Backend
cd backend
python manage.py runserver

# Terminal 2: Frontend
cd frontend
npm run dev
```

Then navigate to the inventory page and click "Search by Image" button.

---

For questions or issues, refer to the inline code documentation or check the logs at `/backend/logs/image_search.log`
