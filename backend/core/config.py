import os

# ROOT_DIR point to the root directory containing both 'backend' and 'data' directories
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BACKEND_DIR = os.path.join(ROOT_DIR, 'backend')

# Paths for the model index and downloaded models
MODEL_INDEX_PATH = os.path.join(ROOT_DIR, 'data', 'model_index.json')
DOWNLOADED_MODELS_PATH = os.path.join(ROOT_DIR, 'data', 'library.json')
RUNTIME_DATA_PATH = os.path.join(ROOT_DIR, 'data', 'runtime_data.json')
UPLOAD_IMAGE_DIR = os.path.join(ROOT_DIR, 'data', 'uploaded_images')
UPLOAD_VID_DIR= os.path.join(ROOT_DIR, 'data', 'uploaded_videos')
CONFIG_PATH = os.path.join(ROOT_DIR, 'data', 'settings.json')
UPLOAD_DATASET_DIR = os.path.join(ROOT_DIR, 'data', 'uploaded_dataset')
DATASETS_DIR =  os.path.join(ROOT_DIR, 'Datasets')
PLAYGROUND_JSON_PATH = os.path.join(ROOT_DIR, 'data', 'playground.json')
SPEAKER_EMBEDDING_PATH = os.path.join(ROOT_DIR, 'data', 'speaker_embeddings.json')

# Ensure the upload directory exists
if not os.path.exists(UPLOAD_IMAGE_DIR):
    os.makedirs(UPLOAD_IMAGE_DIR)
    
if not os.path.exists(UPLOAD_VID_DIR):
    os.makedirs(UPLOAD_VID_DIR)

if not os.path.exists(UPLOAD_DATASET_DIR):
    os.makedirs(UPLOAD_DATASET_DIR)
