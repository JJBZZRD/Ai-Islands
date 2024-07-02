import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), 'data')
MODEL_INDEX_PATH = os.path.join(DATA_DIR, 'model_index.json')
DOWNLOADED_MODELS_PATH = os.path.join(DATA_DIR, 'downloaded_models.json')
