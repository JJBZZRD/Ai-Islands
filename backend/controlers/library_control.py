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
        return True

    def add_fine_tuned_model(self, new_entry: dict):
        library = JSONHandler.read_json(DOWNLOADED_MODELS_PATH)
        base_model_id = new_entry['base_model']
        
        i = 1
        while f"{base_model_id}_{i}" in library:
            i += 1
        new_model_id = f"{base_model_id}_{i}"

        # Creating new entry 
        new_model_entry = new_entry.copy()
        new_model_entry["model_id"] = new_model_id

        # Adding new entry to the library
        library[new_model_id] = new_model_entry

        JSONHandler.write_json(DOWNLOADED_MODELS_PATH, library)
        logger.info(f"New fine-tuned model {new_model_id} added to library")
        return new_model_id