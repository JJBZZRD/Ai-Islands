"""from models.transformer_model import TransformerModel
from models.ultralytics_model import UltralyticsModel
from models.watson_model import WatsonModel
import multiprocessing
import json
from data_utils.json_handler import JSONHandler
from core.config import MODEL_INDEX_PATH, DOWNLOADED_MODELS_PATH

class ModelControl:
    def __init__(self):
        self.models = []
        self.json_handler = JSONHandler()
        
    # Creating child process to download model
    def download_model(self, model_id:str):
        model_info = self._get_model_info(model_id)
        if not model_info:
            return False
        
        if model_info.get('online', False):
            print(f"Model {model_id} is online and does not require downloading.")
            return True
        
        def download_process(model_class, model_id):
            model = model_class()
            model.download(model_id)
            self._update_library(model_id, model_info)
            
        model_class = self._get_model_class(model_info['model_source'])
        process = multiprocessing.Process(target=download_process, args=(model_class, model_id)) # Create and start the process
        process.start() # Start download in separate process
        process.join()  # Wait for download to finish
        return True
    
    def _update_library(self, model_id: str, model_info: dict):
        # Load the library JSON
        library = self.json_handler.read_json(DOWNLOADED_MODELS_PATH)
        
        # Remove any existing entry for the model_id
        library = [model for model in library if model['model_id'] != model_id]

        # Add the new model info to the library, copying metadata from model_info
        new_entry = {
            "model_id": model_id,
            "dir": model_info['model_source'],
            "customised": False,
            "online": model_info["online"],
            "tags": model_info["tags"],
            "model_desc": model_info["model_desc"],
            "model_card_url": model_info["model_card_url"],
            "required_classes": model_info["required_classes"]
        }
        library.append(new_entry)
        
        # Write the updated library back to the JSON file
        JSONHandler.write_json(DOWNLOADED_MODELS_PATH, library)
    

    # Creating child process to load model
    def load_model(self, model_id: str):
        model_info = self._get_model_info(model_id)
        if not model_info:
            return False

        def load_process(model_class, model_id):
            model = model_class()
            model.load(model_id)
            return model

        model_class = self._get_model_class(model_info['model_source'])
        process = multiprocessing.Process(target=load_process, args=(model_class, model_id))
        process.start()
        self.models.append({'model_id': model_id, 'process': process})
        return True
    
    # Creating child process to unload model
    def unload_model(self, model_id: str):
        for model in self.models:
            if model['model_id'] == model_id:
                model['process'].terminate()
                self.models.remove(model)
                return True
        return False
    
    # Providing list of active/currently loaded models
    def list_active_models(self):
        return [model['model_id'] for model in self.models]
    
    # Remove model information from library json file
    def delete_model(self, model_id: str):
        model_info = self._get_model_info(model_id)
        if not model_info:
            return False

        # Remove from downloaded models
        #downloaded_models = self.json_handler.read_json('data/library.json')
        #downloaded_models = [model for model in downloaded_models if model['model_id'] != model_id]
        #self.json_handler.write_json('data/library.json', downloaded_models)
        
        # Remove from model library
        library = self.json_handler.read_json('data/library.json')
        library = [model for model in library if model['model_id'] != model_id]
        self.json_handler.write_json('data/library.json', library)

        return True
    
    def _get_model_info(self, model_id: str):
        print(f"Reading model index from: {MODEL_INDEX_PATH}")  
        model_index = self.json_handler.read_json(MODEL_INDEX_PATH)
        return next((model for model in model_index if model['model_id'] == model_id), None)

    def _get_model_class(self, model_source: str):
        if model_source == 'transformers':
            return TransformerModel
        elif model_source == 'ultralytics':
            return UltralyticsModel
        elif model_source == 'watson':
            return WatsonModel
        else:
            raise ValueError(f"Unknown model source: {model_source}")"""
            
import logging
from backend.models.transformer_model import TransformerModel
from backend.models.ultralytics_model import UltralyticsModel
from backend.models.watson_model import WatsonModel
import multiprocessing
import os
import json
from backend.data_utils.json_handler import JSONHandler
from backend.core.config import MODEL_INDEX_PATH, DOWNLOADED_MODELS_PATH

logger = logging.getLogger(__name__)

class ModelControl:
    def __init__(self):
        self.models = []
        self.json_handler = JSONHandler()
        
    def download_model(self, model_id: str):
        model_info = self._get_model_info(model_id)
        if not model_info:
            logger.error(f"Model info not found for {model_id}")
            return False
        
        if model_info.get('online', False):
            logger.info(f"Model {model_id} is online and does not require downloading.")
            return True
        
        def download_process(model_class, model_id):
            model = model_class()
            model.download(model_id)
            self._update_library(model_id, model_info)
        
        model_class = self._get_model_class(model_info['model_source'])
        process = multiprocessing.Process(target=download_process, args=(model_class, model_id))
        process.start()
        process.join()
        logger.info(f"Model {model_id} download process completed.")
        return True
    
    def _update_library(self, model_id: str, model_info: dict):
        library_path = DOWNLOADED_MODELS_PATH
        logger.debug(f"Updating library at: {library_path}")

        library = self.json_handler.read_json(library_path)
        
        # Remove any existing entry for the model_id
        library = [model for model in library if model['model_id'] != model_id]

        new_entry = {
            "model_id": model_id,
            "dir": model_info['model_source'],
            "customised": False,
            "online": model_info["online"],
            "tags": model_info["tags"],
            "model_desc": model_info.get("model_desc", ""),
            "model_card_url": model_info["model_card_url"],
            "required_classes": model_info["required_classes"]
        }
        library.append(new_entry)
        
        logger.debug(f"New library entry: {new_entry}")
        self.json_handler.write_json(library_path, library)
        logger.info(f"Library updated with new entry: {new_entry}")

    def load_model(self, model_id: str):
        model_info = self._get_model_info(model_id)
        if not model_info:
            return False

        def load_process(model_class, model_id):
            model = model_class()
            model.load(model_id)
            return model

        model_class = self._get_model_class(model_info['model_source'])
        process = multiprocessing.Process(target=load_process, args=(model_class, model_id))
        process.start()
        self.models.append({'model_id': model_id, 'process': process})
        logger.info(f"Model {model_id} load process started.")
        return True
    
    def unload_model(self, model_id: str):
        for model in self.models:
            if model['model_id'] == model_id:
                model['process'].terminate()
                self.models.remove(model)
                logger.info(f"Model {model_id} unloaded.")
                return True
        return False
    
    def list_active_models(self):
        return [model['model_id'] for model in self.models]
    
    def delete_model(self, model_id: str):
        model_info = self._get_model_info(model_id)
        if not model_info:
            return False

        library = self.json_handler.read_json(DOWNLOADED_MODELS_PATH)
        library = [model for model in library if model['model_id'] != model_id]
        self.json_handler.write_json(DOWNLOADED_MODELS_PATH, library)
        logger.info(f"Model {model_id} deleted from library.")

        return True
    
    def _get_model_info(self, model_id: str):
        logger.debug(f"Reading model index from: {MODEL_INDEX_PATH}")

        if not os.path.exists(MODEL_INDEX_PATH):
            logger.error(f"File not found: {MODEL_INDEX_PATH}")
            return None

        try:
            with open(MODEL_INDEX_PATH, 'r') as f:
                data = f.read()
                logger.debug(f"Successfully read file content: {data[:100]}")  # Print the first 100 characters
                model_index = json.loads(data)
                logger.debug(f"Successfully parsed JSON: {model_index['models'][:1]}")  # Print the first item in the JSON array

                # Access the "models" list within the JSON
                models = model_index["models"]
                return next((model for model in models if model['model_id'] == model_id), None)
        except FileNotFoundError as e:
            logger.error(f"FileNotFoundError: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"JSONDecodeError: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

        return None

    def _get_model_class(self, model_source: str):
        if model_source == 'transformers':
            return TransformerModel
        elif model_source == 'ultralytics':
            return UltralyticsModel
        elif model_source == 'watson':
            return WatsonModel
        else:
            raise ValueError(f"Unknown model source: {model_source}")
