from hmac import new
from backend.data_utils.json_handler import JSONHandler
from backend.core.config import MODEL_INDEX_PATH, DOWNLOADED_MODELS_PATH
import logging
import os
import json

logger = logging.getLogger(__name__)


class LibraryControl:
    def __init__(self):
        self.library = None

    def update_library(self, model_id: str, new_entry: dict):
        logger.debug(f"Updating library at: {DOWNLOADED_MODELS_PATH}")
        library = JSONHandler.read_json(DOWNLOADED_MODELS_PATH)
        
        if not isinstance(library, dict):
            library = {}
        
        if model_id in library:
            library[model_id].update(new_entry)
        else:
            library[model_id] = new_entry
        
        logger.debug(f"New library entry: {new_entry}")
        JSONHandler.write_json(DOWNLOADED_MODELS_PATH, library)
        logger.info(f"Library updated with new entry: {new_entry}")

    def get_model_info_library(self, model_id: str):
        logger.debug(f"Reading model library from: {DOWNLOADED_MODELS_PATH}")

        if not os.path.exists(DOWNLOADED_MODELS_PATH):
            logger.error(f"File not found: {DOWNLOADED_MODELS_PATH}")
            return None

        try:
            model_library = JSONHandler.read_json(DOWNLOADED_MODELS_PATH)
            logger.debug(f"Successfully read file content: {model_library}")

            model_info = model_library.get(model_id)
            if model_info:
                return model_info
            else:
                logger.error(f"Model info not found for {model_id}")
                return None
        except FileNotFoundError as e:
            logger.error(f"FileNotFoundError: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"JSONDecodeError: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        return None

    def get_model_info_index(self, model_id: str):
        logger.debug(f"Reading model index from: {MODEL_INDEX_PATH}")

        if not os.path.exists(MODEL_INDEX_PATH):
            logger.error(f"File not found: {MODEL_INDEX_PATH}")
            return None

        try:
            model_index = JSONHandler.read_json(MODEL_INDEX_PATH)
            logger.debug(f"Successfully read model index file")

            model_info = model_index[model_id]
            return model_info
        except FileNotFoundError as e:
            logger.error(f"FileNotFoundError: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"JSONDecodeError: {e}")
        except KeyError as e:
            logger.error(f"Model info not found for {model_id}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        return None

    def delete_model(self, model_id: str):
        model_info = self.get_model_info_library(model_id)
        if not model_info:
            logger.error(f"Model info not found for {model_id}")
            return False

        library = JSONHandler.read_json(DOWNLOADED_MODELS_PATH)
        library.pop(model_id, None)
        JSONHandler.write_json(DOWNLOADED_MODELS_PATH, library)
        logger.info(f"Model {model_id} deleted from library.")
        return {"message": f"Model {model_id} deleted from library."}

    def add_fine_tuned_model(self, new_entry: dict):
        library = JSONHandler.read_json(DOWNLOADED_MODELS_PATH)
        base_model_id = new_entry['base_model']
    
        new_model_id = new_entry['model_id']
    
        # Adding new entry to the library
        library[new_model_id] = new_entry

        JSONHandler.write_json(DOWNLOADED_MODELS_PATH, library)
        logger.info(f"New fine-tuned model {new_model_id} added to library")
        return new_model_id
    
    def update_model_config(self, model_id: str, new_config: dict):
        logger.info(f"Attempting to update configuration for model {model_id}")
        try:
            model_info = self.get_model_info_library(model_id)
            if not model_info:
                logger.error(f"Model info not found for {model_id}")
                return None

            library = JSONHandler.read_json(DOWNLOADED_MODELS_PATH)
            if model_id in library:
                library[model_id]['config'] = self._merge_configs(library[model_id]['config'], new_config)
                JSONHandler.write_json(DOWNLOADED_MODELS_PATH, library)
                logger.info(f"Configuration updated for model {model_id}")
                return library[model_id]['config']
            else:
                logger.error(f"Model {model_id} not found in library")
                return None
        except Exception as e:
            logger.error(f"Error updating configuration for model {model_id}: {str(e)}")
            return None

    def _merge_configs(self, original_config: dict, new_config: dict) -> dict:
        for key, value in new_config.items():
            if isinstance(value, dict) and key in original_config:
                original_config[key] = self._merge_configs(original_config[key], value)
            else:
                original_config[key] = value
        return original_config

    def save_new_model(self, model_id: str, new_model_id: str, new_config: dict):
        logger.info(f"Attempting to save new model {new_model_id} based on {model_id}")
        try:
            model_info = self.get_model_info_library(model_id)
            if not model_info:
                logger.error(f"Model info not found for {model_id}")
                return None
            self.update_library(new_model_id, model_info)
            updated_config = self.update_model_config(new_model_id, new_config)
            if updated_config:
                logger.info(f"New model {new_model_id} saved successfully")
                return new_model_id
            else:
                logger.error(f"Failed to update configuration for new model {new_model_id}")
                return None
        except Exception as e:
            logger.error(f"Error saving new model {new_model_id}: {str(e)}")
            return None

    def update_model_id(self, model_id: str, new_model_id: str):
        logger.info(f"Attempting to update model ID from {model_id} to {new_model_id}")
        try:
            model_info = self.get_model_info_library(model_id)
            if not model_info:
                logger.error(f"Model info not found for {model_id}")
                return None
            self.update_library(new_model_id, model_info)
            if self.delete_model(model_id):
                logger.info(f"Model ID updated from {model_id} to {new_model_id}")
                return new_model_id
            else:
                logger.error(f"Failed to delete old model {model_id}")
                return None
        except Exception as e:
            logger.error(f"Error updating model ID from {model_id} to {new_model_id}: {str(e)}")
            return None
        