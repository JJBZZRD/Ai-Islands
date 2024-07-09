from backend.models.transformer_model import TransformerModel
from backend.models.ultralytics_model import UltralyticsModel
from backend.models.watson_model import WatsonModel
import multiprocessing
import json
from backend.data_utils.json_handler import JSONHandler
from backend.core.config import MODEL_INDEX_PATH, DOWNLOADED_MODELS_PATH
import logging
import os
import time
import gc

logger = logging.getLogger(__name__)

class ModelControl:
    def __init__(self):
        self.models = []
        self.json_handler = JSONHandler()
    
    @staticmethod
    def download_process(model_class, model_id, model_dir):
        logger.info(f"Starting download for model {model_id}")
        start_time = time.time()
        model = model_class()
        model.download(model_id)
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
            logger.info(f"Created directory: {model_dir}")
        model_path = os.path.join(model_dir, f"{model_id}.pt")
        # Assuming the model class has a `save` method to save the model to the specified path
        model.save(model_path)
        end_time = time.time()
        logger.info(f"Completed download for model {model_id} in {end_time - start_time:.2f} seconds")
        logger.info(f"Model saved at {model_path}")

    @staticmethod
    def load_process(model_class, model_path, return_dict, model_id):
        model = model_class()
        model.load(model_path)
        return_dict[model_id] = model
    
    def download_model(self, model_id: str):
        model_info = self._get_model_info_index(model_id)
        if not model_info:
            logger.error(f"Model info not found for {model_id}")
            return False
        
        if model_info.get('online', False):
            logger.info(f"Model {model_id} is online and does not require downloading.")
            return True
        
        model_class = self._get_model_class_download(model_info['model_source'])
        
        if model_info['model_source'] == 'ultralytics':
            model_dir = os.path.join('venv', 'models', 'ultralytics')
        elif model_info['model_source'] == 'transformers':
            model_dir = os.path.join('venv', 'models', 'transformers')
        else:
            model_dir = os.path.join('venv', 'models', 'others')
        
        process = multiprocessing.Process(target=self.download_process, args=(model_class, model_id, model_dir))
        logger.info(f"Starting download process for model {model_id}")
        process.start()
        process.join()
        logger.info(f"Download process for model {model_id} completed")
        self._update_library(model_id, model_info, model_dir)
        return True
    
    def _update_library(self, model_id: str, model_info: dict, model_dir: str):
        logger.debug(f"Updating library at: {DOWNLOADED_MODELS_PATH}")
        library = self.json_handler.read_json(DOWNLOADED_MODELS_PATH)
        
        library = [model for model in library if model['model_id'] != model_id]

        new_entry = {
            "model_id": model_id,
            "dir": model_dir,
            "customised": False,
            "online": model_info["online"],
            "tags": model_info["tags"],
            "model_desc": model_info.get("model_desc", ""),
            "model_card_url": model_info["model_card_url"],
            "required_classes": model_info["required_classes"]
        }
        library.append(new_entry)
        
        logger.debug(f"New library entry: {new_entry}")
        self.json_handler.write_json(DOWNLOADED_MODELS_PATH, library)
        logger.info(f"Library updated with new entry: {new_entry}")

    def load_model(self, model_id: str):
        model_info = self._get_model_info_library(model_id)
        if not model_info:
            logger.error(f"Model info not found for {model_id}")
            return False

        model_class = self._get_model_class_load(model_info['required_classes'][0])
        model_path = os.path.join(model_info['dir'], f"{model_id}.pt")
        manager = multiprocessing.Manager()
        return_dict = manager.dict()
        process = multiprocessing.Process(target=self.load_process, args=(model_class, model_path, return_dict, model_id))
        logger.info(f"Starting load process for model {model_id}")
        process.start()
        process.join()
        if model_id in return_dict:
            self.models.append({'model_id': model_id, 'model': return_dict[model_id], 'process': process})
            logger.info(f"Model {model_id} load process completed and model added to the active models list.")
            return True
        else:
            logger.error(f"Model {model_id} could not be loaded.")
            return False
    
    def unload_model(self, model_id: str):
        if model_id in self.models:
            del self.models[model_id]  # Remove the model from the dictionary
            gc.collect()  # Force garbage collection to free memory
            logger.info(f"Model {model_id} unloaded and memory freed.")
            return True
        return False
    
    def list_active_models(self):
        return [model['model_id'] for model in self.models]
    
    def delete_model(self, model_id: str):
        model_info = self._get_model_info_library(model_id)
        if not model_info:
            logger.error(f"Model info not found for {model_id}")
            return False

        library = self.json_handler.read_json(DOWNLOADED_MODELS_PATH)
        library = [model for model in library if model['model_id'] != model_id]
        self.json_handler.write_json(DOWNLOADED_MODELS_PATH, library)
        logger.info(f"Model {model_id} deleted from library.")
        return True
    
    def _get_model_info_index(self, model_id: str):
        logger.debug(f"Reading model index from: {MODEL_INDEX_PATH}")

        if not os.path.exists(MODEL_INDEX_PATH):
            logger.error(f"File not found: {MODEL_INDEX_PATH}")
            return None

        try:
            model_index = self.json_handler.read_json(MODEL_INDEX_PATH)
            logger.debug(f"Successfully read file content: {model_index}")
            return next((model for model in model_index["models"] if model['model_id'] == model_id), None)
        except FileNotFoundError as e:
            logger.error(f"FileNotFoundError: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"JSONDecodeError: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        return None
    
    def _get_model_info_library(self, model_id: str):
        logger.debug(f"Reading model library from: {DOWNLOADED_MODELS_PATH}")

        if not os.path.exists(DOWNLOADED_MODELS_PATH):
            logger.error(f"File not found: {DOWNLOADED_MODELS_PATH}")
            return None

        try:
            model_library = self.json_handler.read_json(DOWNLOADED_MODELS_PATH)
            logger.debug(f"Successfully read file content: {model_library}")
            return next((model for model in model_library if model['model_id'] == model_id), None)
        except FileNotFoundError as e:
            logger.error(f"FileNotFoundError: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"JSONDecodeError: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        return None

    def _get_model_class_download(self, model_source: str):
        if model_source == 'transformers':
            return TransformerModel
        elif model_source == 'ultralytics':
            return UltralyticsModel
        elif model_source == 'watson':
            return WatsonModel
        else:
            raise ValueError(f"Unknown model source: {model_source}")
    
    def _get_model_class_load(self, required_class: str):
        if required_class == 'YOLO':
            return UltralyticsModel
        else:
            return TransformerModel