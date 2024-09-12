from backend.data_utils.json_handler import JSONHandler
from backend.core.config import MODEL_INDEX_PATH, DOWNLOADED_MODELS_PATH
import logging
import os
from backend.core.exceptions import FileReadError, FileWriteError
from typing import List

logger = logging.getLogger(__name__)


class LibraryControl:
    """
    The LibraryControl class provides methods to manage a library of models.
    It allows updating, retrieving, deleting, and initializing models in the library.
    """

    def __init__(self):
        """
        Initializes the LibraryControl instance.
        """
        self.library = None

    def get_models_by_base_model(self, base_model: str) -> List[str]:
        logger.debug(f"Searching for models with base_model: {base_model}")
        library = JSONHandler.read_json(DOWNLOADED_MODELS_PATH)
        matching_models = [
            model_id for model_id, model_info in library.items()
            if model_info.get('base_model') == base_model
        ]
        logger.info(f"Found {len(matching_models)} models with base_model {base_model}")
        return matching_models

    def update_library(self, model_id: str, new_entry: dict):
        """
        Updates the library with a new entry for a given model ID.

        Args:
            model_id (str): The ID of the model to update.
            new_entry (dict): The new entry to add or update in the library.

        Raises:
            FileReadError: If there is an error reading the library file.
            FileWriteError: If there is an error writing to the library file.
        """
        logger.debug(f"Updating library at: {DOWNLOADED_MODELS_PATH}")
        library = JSONHandler.read_json(DOWNLOADED_MODELS_PATH)
        
        if model_id not in library:
            logger.debug(f"Model {model_id} not found in library, adding new entry")
            library[model_id] = new_entry
        else:
            logger.debug(f"Model {model_id} found in library, updating entry")
            library[model_id].update(new_entry)
        
        logger.debug(f"New library entry: {new_entry}")
        JSONHandler.write_json(DOWNLOADED_MODELS_PATH, library)
        logger.info(f"Library updated with new entry: {new_entry}")

    def get_model_info_library(self, model_id: str):
        """
        Retrieves model information from the library for a given model ID.

        Args:
            model_id (str): The ID of the model to retrieve information for.

        Returns:
            dict: The model information if found, otherwise None.

        Raises:
            FileReadError: If there is an error reading the library file.
        """
        logger.debug(f"Reading model library from: {DOWNLOADED_MODELS_PATH}")

        model_library = JSONHandler.read_json(DOWNLOADED_MODELS_PATH)
        logger.debug(f"Successfully read file content: {model_library}")

        model_info = model_library.get(model_id)
        if model_info:
            return model_info
        else:
            logger.error(f"Model info not found for {model_id}")
            raise KeyError(f"Model info not found for {model_id}")

    def get_model_info_index(self, model_id: str):
        """
        Retrieves model information from the index for a given model ID.

        Args:
            model_id (str): The ID of the model to retrieve information for.

        Returns:
            dict: The model information if found, otherwise None.

        Raises:
            FileReadError: If there is an error reading the index file.
        """
        logger.debug(f"Reading model index from: {MODEL_INDEX_PATH}")

        model_index = JSONHandler.read_json(MODEL_INDEX_PATH)
        logger.debug("Successfully read model index file")

        model_info = model_index.get(model_id)
        if model_info:
            return model_info
        else:
            logger.error(f"Model info not found for {model_id}")
            raise KeyError(f"Model info not found for {model_id}")

    def delete_model(self, model_id: str):
        """
        Deletes a model from the library for a given model ID.

        Args:
            model_id (str): The ID of the model to delete.

        Returns:
            dict: A message indicating the result of the deletion.

        Raises:
            FileReadError: If there is an error reading the library file.
            FileWriteError: If there is an error writing to the library file.
        """
        model_info = self.get_model_info_library(model_id)
        if not model_info:
            logger.info(f"Model {model_id} does not exist in library.")
            return {"message": f"Model {model_id} does not exist in library."}

        library = JSONHandler.read_json(DOWNLOADED_MODELS_PATH)
        library.pop(model_id, None)
        JSONHandler.write_json(DOWNLOADED_MODELS_PATH, library)
        logger.info(f"Model {model_id} deleted from library.")
        return {"message": f"Model {model_id} deleted from library."}

    def add_fine_tuned_model(self, new_entry: dict):
        """
        Adds a new fine-tuned model to the library.

        Args:
            new_entry (dict): The new entry to add to the library.

        Returns:
            str: The ID of the new fine-tuned model.

        Raises:
            FileReadError: If there is an error reading the library file.
            FileWriteError: If there is an error writing to the library file.
        """
        try:
            library = JSONHandler.read_json(DOWNLOADED_MODELS_PATH)

            new_model_id = new_entry.pop('model_id')

            # Adding new entry to the library
            library[new_model_id] = new_entry

            JSONHandler.write_json(DOWNLOADED_MODELS_PATH, library)
            logger.info(f"New fine-tuned model {new_model_id} added to library")
            return new_model_id
        except Exception as e:
            logger.error(str(e))
            raise e
    
    def update_model_config(self, model_id: str, new_config: dict):
        """
        Updates the configuration of a model in the library.

        Args:
            model_id (str): The ID of the model to update.
            new_config (dict): The new configuration to apply.

        Returns:
            dict: The updated configuration if successful, otherwise None.

        Raises:
            FileReadError: If there is an error reading the library file.
            FileWriteError: If there is an error writing to the library file.
        """
        library = JSONHandler.read_json(DOWNLOADED_MODELS_PATH)
        if model_id in library:
            library[model_id]['config'] = self._merge_configs(library[model_id]['config'], new_config)
            base_model_id = library[model_id]['base_model']
            
            # Check if the new config is the same as the default config
            default_config = self.get_model_info_index(base_model_id)
            if library[model_id]['config'] == default_config['config']:
                library[model_id]['is_customised'] = False
            else:
                library[model_id]['is_customised'] = True
            
            # Update the library
            JSONHandler.write_json(DOWNLOADED_MODELS_PATH, library)
            logger.info(f"Configuration updated for model {model_id}")
            
            return library[model_id]['config']
        else:
            logger.error(f"Model {model_id} not found in library")
            raise KeyError(f"Model {model_id} not found in library")

    def save_new_model(self, model_id: str, new_model_id: str, new_config: dict):
        """
        Saves a new model based on an existing model with a new configuration.

        Args:
            model_id (str): The ID of the existing model.
            new_model_id (str): The ID of the new model.
            new_config (dict): The new configuration to apply.

        Returns:
            str: The ID of the new model if successful, otherwise None.

        Raises:
            FileReadError: If there is an error reading the library file.
            FileWriteError: If there is an error writing to the library file.
        """
        logger.info(f"Attempting to save new model {new_model_id} based on {model_id}")

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

    def update_model_id(self, model_id: str, new_model_id: str):
        """
        Updates the ID of an existing model in the library.

        Args:
            model_id (str): The current ID of the model.
            new_model_id (str): The new ID to assign to the model.

        Returns:
            str: The new model ID if successful, otherwise None.

        Raises:
            FileReadError: If there is an error reading the library file.
            FileWriteError: If there is an error writing to the library file.
        """
        logger.info(f"Attempting to update model ID from {model_id} to {new_model_id}")
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

    def _merge_configs(self, original_config: dict, new_config: dict) -> dict:
        for key, value in new_config.items():
            if value is not None:  # Skip None values
                if isinstance(value, dict) and key in original_config:
                    original_config[key] = self._merge_configs(original_config[key], value)
                else:
                    if isinstance(value, str) and value.lower() == "null":
                        logger.info(f"Setting {key} to None")
                        value = None
                    original_config[key] = value
        return original_config
    
    def _initialise_library(self):
        """
        Initializes the library by creating an empty JSON file if it does not exist.

        Returns:
            bool: True if the operation is successful.

        Raises:
            FileWriteError: If there is an error writing to the library file.
        """
        if not os.path.exists(DOWNLOADED_MODELS_PATH):
            logger.info(f"Creating new library at: {DOWNLOADED_MODELS_PATH}")
            JSONHandler.write_json(DOWNLOADED_MODELS_PATH, {})
            logger.info("Library initialised successfully")
        else:
            logger.info(f"Library already exists at: {DOWNLOADED_MODELS_PATH}")
            try:
                data = JSONHandler.read_json(DOWNLOADED_MODELS_PATH)
            except FileReadError:
                data = {}
                try:
                    JSONHandler.write_json(DOWNLOADED_MODELS_PATH, data)
                    logger.info("Library was empty, reinitialised successfully")
                    logger.info("Library initialised successfully")
                except FileWriteError as e:
                    logger.error(f"Error reinitialising library: {e}")
                    raise e
        return True

    def reset_model_config(self, model_id: str):
        logger.info(f"Attempting to reset configuration for model {model_id}")
        # Get the current model info from the library
        library_model_info = self.get_model_info_library(model_id)
        if not library_model_info:
            logger.error(f"Model info not found in library for {model_id}")
            return None

        base_model_id = library_model_info['base_model']

        # Get the model info from the index
        index_model_info = self.get_model_info_index(base_model_id)
        if not index_model_info:
            logger.error(f"Model info not found in index for {base_model_id}")
            return None

        # Extract the config from the index model info
        index_config = index_model_info.get('config', {})

        # Update the library model info with the index config
        library_model_info['config'] = index_config
        # Reset the customisation flag
        library_model_info['is_customised'] = False

        # Update the library
        library = JSONHandler.read_json(DOWNLOADED_MODELS_PATH)
        library[model_id] = library_model_info
        JSONHandler.write_json(DOWNLOADED_MODELS_PATH, library)

        logger.info(f"Configuration reset for model {model_id}")
        return index_config
