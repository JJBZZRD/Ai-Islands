"""import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
UPLOAD_DIR = os.path.join(DATA_DIR, 'uploaded_images')
MODEL_INDEX_PATH = os.path.join(DATA_DIR, 'model_index.json')
DOWNLOADED_MODELS_PATH = os.path.join(DATA_DIR, 'library.json')
# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True) """

import os

# ROOT_DIR point to the root directory containing both 'backend' and 'data' directories
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BACKEND_DIR = os.path.join(ROOT_DIR, 'backend')

# Paths for the model index and downloaded models
MODEL_INDEX_PATH = os.path.join(ROOT_DIR, 'data', 'model_index.json')
DOWNLOADED_MODELS_PATH = os.path.join(ROOT_DIR, 'data', 'library.json')
UPLOAD_DIR = os.path.join(ROOT_DIR, 'data', 'uploaded_images')

# Ensure the upload directory exists
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

