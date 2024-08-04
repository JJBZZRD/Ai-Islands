import os
import json
import logging
from backend.controlers.library_control import LibraryControl
from backend.controlers.runtime_control import RuntimeControl
from backend.core.config import PLAYGROUND_JSON_PATH
from backend.data_utils.json_handler import JSONHandler
from backend.playground.playground import Playground
from backend.core.exceptions import PlaygroundError, PlaygroundAlreadyExistsError, ChainNotCompatibleError, FileReadError, FileWriteError

logger = logging.getLogger(__name__)

class PlaygroundControl:
    """
    The PlaygroundControl class manages the creation, initialization, updating, and deletion of playgrounds.
    It interacts with JSON files to persist playground data and handles models within each playground.
    """

    def __init__(self, model_control):
        """
        Initializes the PlaygroundControl instance.

        Args:
            model_control: The model control instance to manage models.

        Raises:
            FileReadError: If there is an error reading the playground data.
            FileWriteError: If there is an error writing the playground data.
        """
        self.model_control = model_control
        self.library_control = LibraryControl()
        self.playgrounds = {}
        self._initialise_playground_data_directory()
        self._initialise_all_playgrounds()

    def create_playground(self, playground_id: str = None, description: str = None):
        """
        Creates a new playground.

        Args:
            playground_id (str, optional): The ID of the playground. Defaults to None.
            description (str, optional): The description of the playground. Defaults to None.

        Returns:
            dict: The data of the created playground.

        Raises:
            PlaygroundAlreadyExistsError: If the playground already exists.
            FileWriteError: If there is an error writing the playground data.
        """
        if not playground_id:
            playground_id = f"new_playground_{len(self.playgrounds) + 1}"
        elif playground_id in self.playgrounds:
            logger.error(f"Playground {playground_id} already exists.")
            raise PlaygroundAlreadyExistsError(playground_id)

        new_playground = Playground(playground_id, description=description)
        self.playgrounds[playground_id] = new_playground

        try:
            self._write_playgrounds_to_json()
        except FileWriteError as e:
            logger.error("Error writing new playground data to JSON file")
            raise e

        logger.info(f"Created new playground with ID: {playground_id}")

        data = {"playground_id": playground_id, "playground": new_playground.to_dict()}
        return data

    def update_playround_info(self, playground_id: str, new_playground_id: str = None, description: str = None):
        """
        Updates the information of an existing playground.

        Args:
            playground_id (str): The ID of the playground to update.
            new_playground_id (str, optional): The new ID of the playground. Defaults to None.
            description (str, optional): The new description of the playground. Defaults to None.

        Returns:
            dict: The updated playground data.

        Raises:
            KeyError: If the playground does not exist.
            FileWriteError: If there is an error writing the playground data.
        """
        if playground_id not in self.playgrounds:
            logger.error(f"Playground {playground_id} does not exist.")
            raise KeyError(f"Playground {playground_id} does not exist.")

        if description is not None:
            self.playgrounds[playground_id].description = description

        if new_playground_id is not None:
            playground = self.playgrounds.pop(playground_id)
            self.playgrounds[new_playground_id] = playground

        try:
            self._write_playgrounds_to_json()
        except FileWriteError as e:
            logger.error("Error writing updated playground data to JSON file")
            raise e
        return {"playground_id": playground_id, "playground": self.playgrounds[playground_id].to_dict()}

    def delete_playground(self, playground_id: str):
        """
        Deletes an existing playground.

        Args:
            playground_id (str): The ID of the playground to delete.

        Returns:
            bool: True if the operation is successful.

        Raises:
            KeyError: If the playground does not exist.
            PlaygroundError: If the playground's chain is active.
            FileWriteError: If there is an error writing the playground data.
        """
        if playground_id not in self.playgrounds:
            logger.error(f"Playground {playground_id} does not exist.")
            raise KeyError(f"Playground {playground_id} does not exist.")

        playground = self.playgrounds[playground_id]
        if playground.active_chain:
            logger.error(f"Playground {playground_id} is running a chain, please stop it before deleting.")
            raise PlaygroundError(f"Playground {playground_id} is running a chain, please stop it before deleting.")

        del self.playgrounds[playground_id]
        try:
            self._write_playgrounds_to_json()
        except FileWriteError as e:
            logger.error("Error writing updated playground data to JSON file after playground deletion")
            raise e

        logger.info(f"Deleted playground with ID: {playground_id}")
        return True

    def add_model_to_playground(self, playground_id: str, model_id: str):
        """
        Adds a model to a playground.

        Args:
            playground_id (str): The ID of the playground.
            model_id (str): The ID of the model to add.

        Returns:
            dict: The updated models in the playground.

        Raises:
            KeyError: If the playground or model does not exist.
            FileWriteError: If there is an error writing the playground data.
        """
        playground = self.playgrounds.get(playground_id)

        if not playground:
            logger.error(f"Playground {playground_id} not found")
            raise KeyError(f"Playground {playground_id} not found")

        if model_id in playground.models:
            logger.info(f"Model {model_id} already in playground {playground_id}")
            return {"playground_id": playground_id, "models": playground.models}

        if not self.library_control.get_model_info_library(model_id):
            logger.error(f"Model {model_id} not in library")
            raise KeyError(f"Model {model_id} not in library")

        playground.models[model_id] = self.library_control.get_model_info_library(model_id).get("mapping")

        try:
            self._write_playgrounds_to_json()
        except FileWriteError as e:
            logger.error("Error writing updated playground data to JSON file after adding model")
            raise e

        logger.info(f"Added model {model_id} to playground {playground_id}")
        return {"playground_id": playground_id, "models": playground.models}

    def remove_model_from_playground(self, playground_id: str, model_id: str):
        """
        Removes a model from a playground.

        Args:
            playground_id (str): The ID of the playground.
            model_id (str): The ID of the model to remove.

        Returns:
            bool: True if the operation is successful.

        Raises:
            KeyError: If the playground does not exist.
            FileWriteError: If there is an error writing the playground data.
        """
        playground = self.playgrounds.get(playground_id)

        if not playground:
            logger.error(f"Playground {playground_id} not found")
            raise KeyError(f"Playground {playground_id} not found")

        if model_id not in playground.models:
            logger.info(f"Model {model_id} not in playground {playground_id}")
            return {"playground_id": playground_id, "models": playground.models}

        playground.models.pop(model_id)

        try:
            self._write_playgrounds_to_json()
        except FileWriteError as e:
            logger.error("Error writing updated playground data to JSON file after removing model")
            raise e

        logger.info(f"Removed model {model_id} from playground {playground_id}")
        return True

    def list_playgrounds(self):
        """
        Lists all playgrounds.

        Returns:
            dict: A dictionary of all playgrounds.
        """
        result = {}
        for playground_id in self.playgrounds:
            playground = self.playgrounds[playground_id]
            result[playground_id] = playground.to_dict()
        return result

    def get_playground_info(self, playground_id: str):
        """
        Retrieves information about a specific playground.

        Args:
            playground_id (str): The ID of the playground.

        Returns:
            dict: The playground information.
        """
        if playground_id not in self.playgrounds:
            logger.info(f"Playground {playground_id} not found")
            return {}
        return self.playgrounds[playground_id].to_dict()

    def configure_chain(self, playground_id: str, chain: list):
        """
        Configures the chain of models for a playground.

        Args:
            playground_id (str): The ID of the playground.
            chain (list): The list of model IDs to configure in the chain.

        Returns:
            dict: The updated chain configuration.

        Raises:
            PlaygroundError: If the chain is already running or if the models are not compatible.
            KeyError: If a model is not found in the playground.
            FileWriteError: If there is an error writing the playground data.
        """
        playground = self.playgrounds[playground_id]

        if playground.active_chain:
            raise PlaygroundError(f"Playground {playground_id} is already running a chain, please stop it before configuring.")

        prev_output_type = None

        for model_id in chain:
            if model_id not in playground.models:
                raise KeyError(f"Model {model_id} not found in playground {playground_id}")

            input_type = playground.models.get(model_id).get("input")
            output_type = playground.models.get(model_id).get("output")
            if input_type != prev_output_type and prev_output_type is not None:
                raise ChainNotCompatibleError(f"Model {model_id}'s input type is not compatible with the previous model's output type")
            prev_output_type = output_type

        playground.chain = chain

        try:
            self._write_playgrounds_to_json()
        except FileWriteError as e:
            logger.error("Error writing updated playground data to JSON file after configuring chain")
            raise e

        return {"playground_id": playground_id, "chain": chain}

    def load_playground_chain(self, playground_id: str):
        """
        Loads the chain of models for a playground.

        Args:
            playground_id (str): The ID of the playground.

        Returns:
            dict: The loaded chain configuration.

        Raises:
            KeyError: If the playground does not exist.
            FileReadError: If there is an error reading the runtime data.
            FileWriteError: If there is an error writing the runtime data.
        """
        if playground_id not in self.playgrounds:
            raise KeyError(f"Playground {playground_id} not found")
        playground = self.playgrounds[playground_id]
        logger.info(f"Loading chain for playground {playground_id}")

        for model_id in playground.chain:
            self.model_control.load_model(model_id)
            logger.info(f"Model {model_id} loaded")

        playground.active_chain = True

        runtime_data = RuntimeControl.get_runtime_data("playground")
        for model_id in playground.chain:
            if runtime_data.get(model_id):
                runtime_data[model_id]["active"] = True
            else:
                runtime_data[model_id] = {"active": True}

        try:
            RuntimeControl.update_runtime_data("playground", runtime_data)
        except (FileReadError, FileWriteError) as e:
            logger.error(f"Error updating runtime data: {e}")
            raise e

        return {"playground_id": playground_id, "chain": playground.chain}

    def stop_playground_chain(self, playground_id: str):
        """
        Stops the chain of models for a playground.

        Args:
            playground_id (str): The ID of the playground.

        Returns:
            bool: True if the operation is successful.

        Raises:
            KeyError: If the playground does not exist.
            FileReadError: If there is an error reading the runtime data.
            FileWriteError: If there is an error writing the runtime data.
        """
        playground = self.playgrounds[playground_id]

        try:
            runtime_data = RuntimeControl.get_runtime_data("playground")
        except FileReadError as e:
            logger.error(f"Error reading runtime data: {e}")
            raise e

        for model_id in playground.chain:
            if model_id in runtime_data:
                runtime_data[model_id]["active"] = False

        try:
            RuntimeControl.update_runtime_data("playground", runtime_data)
        except (FileReadError, FileWriteError) as e:
            logger.error(f"Error updating runtime data: {e}")
            raise e

        for model_id in playground.chain:
            self.model_control.unload_model(model_id)
            logger.info(f"Model {model_id} unloaded")

        playground.active_chain = False

        return True

    def inference(self, inference_request):
        """
        Executes inference on a playground's chain of models.

        Args:
            inference_request (dict): The inference request containing the playground ID and data.

        Returns:
            dict: The inference result.

        Raises:
            KeyError: If the playground does not exist.
        """
        playground_id = inference_request.get("playground_id")
        data = inference_request.get("data")

        if playground_id not in self.playgrounds:
            logger.error(f"Playground {playground_id} not found")
            raise KeyError(f"Playground {playground_id} not found")
        playground = self.playgrounds[playground_id]

        inference_result = data
        for model_id in playground.chain:
            inference_result = self.model_control.inference(model_id, inference_result)

        return inference_result

    def _initialise_playground(self, playground_id: str):
        """
        Initialise a single playground by loading its data from the JSON file.

        Args:
            playground_id (str): The ID of the playground to initialise.

        Returns:
            bool: True if the playground is successfully initialised.

        Raises:
            FileReadError: If there is an error reading the playground data.
        """
        try:
            playground_info = self._get_playground_json_data(playground_id)
        except FileReadError as e:
            logger.error("Error reading playground data during initialisation")
            raise e
        description = playground_info.get("description", "")
        models = playground_info.get("models", {})
        chain = playground_info.get("chain", [])
        playground = Playground(playground_id, description, models, chain)
        self.playgrounds[playground_id] = playground

        return True

    def _initialise_all_playgrounds(self):
        """
        Initialise all playgrounds by loading their data from the JSON file.

        Returns:
            dict: A dictionary with the status and message of the operation.

        Raises:
            Exception: If there is an error listing the playgrounds.
        """
        try:
            playgrounds = JSONHandler.read_json(PLAYGROUND_JSON_PATH)
            for playground_id in playgrounds:
                self._initialise_playground(playground_id)
            return {"status": "success", "message": "Playgrounds initialised"}
        except Exception as e:
            logger.error(f"Error listing playgrounds: {str(e)}")
            raise

    def _initialise_playground_data_directory(self):
        """
        Ensure that the playground data directory exists and create an empty JSON file if it does not.

        Returns:
            bool: True if the directory and file are successfully created.
        """
        if not os.path.exists(PLAYGROUND_JSON_PATH):
            with open(PLAYGROUND_JSON_PATH, "w") as f:
                json.dump({}, f)
        return True

    def _get_playground_json_data(self, playground_id: str):
        """
        Retrieve the JSON data for a specific playground.

        Args:
            playground_id (str): The ID of the playground to retrieve data for.

        Returns:
            dict: The JSON data of the playground.

        Raises:
            FileReadError: If there is an error reading the playground data.
        """
        try:
            playgrounds = JSONHandler.read_json(PLAYGROUND_JSON_PATH)
            return playgrounds[playground_id]
        except FileReadError as e:
            logger.error(f"Error reading playground data: {str(e)}")
            raise e

    def _write_playgrounds_to_json(self):
        """
        Write the current playground data to the JSON file.

        Returns:
            bool: True if the data is successfully written.

        Raises:
            FileWriteError: If there is an error writing the playground data.
        """
        playground_dict = self.list_playgrounds()
        try:
            JSONHandler.write_json(PLAYGROUND_JSON_PATH, playground_dict)
        except FileWriteError as e:
            logger.error("Error writing playgrounds data to playground.json")
            raise e
        return True
