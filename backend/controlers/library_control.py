from backend.data_utils.json_handler import JsonHandler
from backend.core.config import DOWNLOADED_MODELS_PATH
import logging

logger = logging.getLogger(__name__)


class LibraryControl:
    def __init__(self):
        self.library = None

    def update_library(self, model_id: str, new_entry: dict):
        logger.debug(f"Updating library at: {DOWNLOADED_MODELS_PATH}")
        library = JsonHandler.read_json(DOWNLOADED_MODELS_PATH)
        
        if not isinstance(library, dict):
            library = {}
        
        library[model_id] = new_entry
        
        logger.debug(f"New library entry: {new_entry}")
        JsonHandler.write_json(DOWNLOADED_MODELS_PATH, library)
        logger.info(f"Library updated with new entry: {new_entry}")