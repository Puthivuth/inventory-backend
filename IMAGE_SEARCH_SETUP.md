# Image Search Setup Checklist

## Pre-Deployment Checklist

- [ ] **Verify Backend Files Exist**
  - [ ] `backend/api/image_search_service.py` (service layer with CLIP)
  - [ ] `backend/api/image_search_views.py` (API endpoints)
  - [ ] `backend/api/scripts/initialize_image_search.py` (init script)
  - [ ] `backend/api/urls.py` (updated with new routes)
  - [ ] `backend/requirements.txt` (updated with dependencies)

- [ ] **Verify Frontend Files Exist**
  - [ ] `frontend/components/inventory/image-search/image-search-dialog.tsx` (UI component)

- [ ] **Check Image Directory**
  - [ ] `E:\DSE-Y3-S2\PP\Images\` directory exists
  - [ ] Contains image files (JPEG, PNG, etc.)
  - [ ] Count images: `dir E:\DSE-Y3-S2\PP\Images\`

## Installation Steps

### Step 1: Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

⏱️ **Expected Time**: 10-15 minutes (first run downloads CLIP model ~350MB)

**Verify Installation:**

```bash
python -c "import clip; import torch; import qdrant_client; print('All packages installed!')"
```

### Step 2: Initialize Qdrant Vector Database

```bash
cd backend
python manage.py initialize_image_search
```

⏱️ **Expected Time**: 2-5 minutes (depends on number of images)

**Expected Output:**

```
Initializing Image Search...
✓ Qdrant collection created: product_images
✓ Indexed local images: X/33 images processed
✓ Vector database ready for search
```

**Verify Initialization:**

```bash
python manage.py shell
```

Then:

```python
from api.image_search_service import get_collection_info
info = get_collection_info()
print(f"Indexed vectors: {info['points_count']}")
```

### Step 3: Run Backend

```bash
python manage.py runserver
```

### Step 4: Run Frontend (in new terminal)

```bash
cd frontend
npm run dev
```

## Verification Tests

### Test 1: Endpoint Registration

```bash
curl -H "Authorization: Token YOUR_TOKEN" http://localhost:8000/api/search-products/
# Should give 405 Method Not Allowed (expected - need POST)
```

### Test 2: Search with Test Image

```bash
# Using curl to upload a test image
curl -X POST \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "file=@E:\DSE-Y3-S2\PP\Images\test.jpg" \
  -F "top_k=5" \
  http://localhost:8000/api/search-products/
```

### Test 3: Frontend UI

1. Navigate to `http://localhost:3000/inventory`
2. Click "Search by Image" button
3. Upload or paste image URL
4. Verify results display with similarity scores

## Deployment Issues & Solutions

| Issue                   | Solution                                                                 |
| ----------------------- | ------------------------------------------------------------------------ |
| CUDA Out of Memory      | Edit `image_search_service.py`: change `device="cuda"` to `device="cpu"` |
| Qdrant Connection Error | Create storage dir: `mkdir backend/qdrant_storage`                       |
| CLIP Download Fails     | Check internet connection, retry initialization                          |
| Images Not Found        | Verify path: `E:\DSE-Y3-S2\PP\Images\` exists and contains images        |
| Endpoints Return 404    | Restart backend server to reload URLs                                    |
| Slow Search             | Normal for first queries (~100-500ms) - CLIP is loading                  |

## Quick Start (TL;DR)

```bash
# Terminal 1: Installation
cd e:\DSE-Y3-S2\PP\backend
pip install -r requirements.txt
python manage.py initialize_image_search
python manage.py runserver

# Terminal 2: Frontend
cd e:\DSE-Y3-S2\PP\frontend
npm run dev

# Browser: Test
# Navigate to http://localhost:3000/inventory
# Click "Search by Image" button
```

## What Gets Initialized

### Vector Database

- **Location**: `backend/qdrant_storage/`
- **Collection**: `product_images`
- **Vectors**: 512-dimensional CLIP embeddings
- **Storage**: ~500MB-1GB depending on image count

### Indexed Images

- **Source**: `E:\DSE-Y3-S2\PP\Images\`
- **Count**: Up to 33 images (cars, milk, keyboards, etc.)
- **Metadata**: Product name, SKU, image path

### Model

- **Name**: CLIP (ViT-B/32)
- **Size**: ~350MB
- **Downloaded**: Automatically on first run
- **Location**: User cache directory

## Status After Setup

✅ = Complete and Ready

| Component         | Status | Notes                                                                                            |
| ----------------- | ------ | ------------------------------------------------------------------------------------------------ |
| Backend Endpoints | ✅     | 3 new routes: `/api/search-products/`, `/api/search-products-url/`, `/api/index-product-images/` |
| Frontend UI       | ✅     | ImageSearchDialog already integrated                                                             |
| CLIP Model        | ⏳     | Auto-downloads on first init (~350MB)                                                            |
| Vector Database   | ⏳     | Created on `initialize_image_search` command                                                     |
| Image Indexing    | ⏳     | Indexes images from `E:\DSE-Y3-S2\PP\Images\`                                                    |

## Performance Expectations

| Operation           | Time      | Notes                              |
| ------------------- | --------- | ---------------------------------- |
| Initial Setup       | 15 mins   | CLIP download + dependency install |
| Qdrant Init         | 2-5 mins  | Depends on image count             |
| Image Upload/Search | 100-500ms | CLIP embedding generation          |
| URL-based Search    | 100-500ms | Download + embed + search          |
| Similarity Search   | <10ms     | Vector DB lookup                   |

## Rollback Instructions

If you need to reset:

```bash
# Remove vector database
rm -r backend/qdrant_storage/

# Remove dependencies (optional)
pip uninstall qdrant-client clip torch torchvision numpy

# Reinstall from scratch
pip install -r requirements.txt
python manage.py initialize_image_search
```

---

**Ready?** Start with "Installation Steps" → "Step 1" above.

For detailed API documentation, see `API_IMAGE_SEARCH_GUIDE.md`
