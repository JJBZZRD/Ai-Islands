import json
import logging
import os

from backend.controlers.library_control import LibraryControl
from backend.controlers.runtime_control import RuntimeControl
from backend.core.config import PLAYGROUND_JSON_PATH
from backend.data_utils.json_handler import JSONHandler
from backend.playground.playground import Playground

logger = logging.getLogger(__name__)


class PlaygroundControl:
    """
    PlaygroundControl class manages the creation, updating, deletion, and configuration of playgrounds.
    It also handles the addition and removal of models to/from playgrounds, and manages the execution of model chains.

    Attributes:
        model_control: An instance of the model control class.
        library_control: An instance of the LibraryControl class.
        playgrounds: A dictionary storing all playground instances.
    """

    def __init__(self, model_control):
        """
        Initializes the PlaygroundControl instance.

        Args:
            model_control: An instance of the model control class.
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
            playground_id: Optional; The ID of the playground.
            description: Optional; A description of the playground.

        Returns:
            A dictionary containing the playground ID and the playground details.
        """
        try:
            if not playground_id:
                playground_id = f"new_playground_{len(self.playgrounds) + 1}"

            new_playground = Playground(playground_id, description=description)
            self.playgrounds[playground_id] = new_playground
            self._write_playgrounds_to_json()

            logger.info(f"Created new playground with ID: {playground_id}")
            return {
                "playground_id": playground_id,
                "playground": new_playground.create_playground_dictionary(),
            }

        except Exception as e:
            logger.error(f"Error creating playground: {str(e)}")
            raise

    def update_playround_info(self, playground_id: str, new_playground_id: str = None, description: str = None):
        """
        Updates the information of an existing playground.

        Args:
            playground_id: The ID of the playground to update.
            new_playground_id: Optional; The new ID for the playground.
            description: Optional; The new description for the playground.

        Returns:
            A dictionary indicating the status of the update operation.
        """
        if playground_id not in self.playgrounds:
            logger.error(f"Playground {playground_id} does not exist.")
            return {"error": f"Playground {playground_id} does not exist."}

        if description is not None:
            self.playgrounds[playground_id].description = description

        if new_playground_id is not None:
            playground = self.playgrounds.pop(playground_id)
            self.playgrounds[new_playground_id] = playground

        self._write_playgrounds_to_json()
        return {"status": "success", "message": "Playground updated"}

    def delete_playground(self, playground_id: str):
        """
        Deletes an existing playground.

        Args:
            playground_id: The ID of the playground to delete.

        Returns:
            A dictionary indicating the status of the delete operation.
        """
        try:
            if playground_id not in self.playgrounds:
                logger.error(f"Playground {playground_id} does not exist.")
                return {"error": f"Playground {playground_id} does not exist."}

            playground = self.playgrounds[playground_id]
            if playground.active_chain:
                logger.error(f"Playground {playground_id} is running a chain, please stop it before deleting.")
                return {"error": f"Playground {playground_id} is running a chain, please stop it before deleting."}

            del self.playgrounds[playground_id]
            self._write_playgrounds_to_json()

            logger.info(f"Deleted playground with ID: {playground_id}")
            return {"playground_id": playground_id, "status": "deleted"}
        except Exception as e:
            logger.error(f"Error deleting playground: {str(e)}")
            raise

    def add_model_to_playground(self, playground_id: str, model_id: str):
        """
        Adds a model to a playground.

        Args:
            playground_id: The ID of the playground.
            model_id: The ID of the model to add.

        Returns:
            A dictionary containing the playground ID and the updated list of models.
        """
        try:
            playground = self.playgrounds.get(playground_id)

            if not playground:
                logger.error(f"Playground {playground_id} not found")
                return None

            if model_id in playground.models:
                logger.info(f"Model {model_id} already in playground {playground_id}")
                return {"playground_id": playground_id, "models": playground.models}

            if not self.library_control.get_model_info_library(model_id):
                logger.error(f"Model {model_id} not in library")
                return {"error": f"Model {model_id} not in library"}

            playground.models[model_id] = self.library_control.get_model_info_library(model_id).get("mapping")
            self._write_playgrounds_to_json()

            logger.info(f"Added model {model_id} to playground {playground_id}")
            return {"playground_id": playground_id, "models": playground.models}
        except Exception as e:
            logger.error(f"Error adding model to playground: {str(e)}")
            raise

    def remove_model_from_playground(self, playground_id: str, model_id: str):
        """
        Removes a model from a playground.

        Args:
            playground_id: The ID of the playground.
            model_id: The ID of the model to remove.

        Returns:
            A dictionary containing the playground ID and the updated list of models.
        """
        try:
            playground = self.playgrounds.get(playground_id)
            if not playground:
                logger.error(f"Playground {playground_id} not found")
                return None

            if model_id not in playground.models:
                logger.info(f"Model {model_id} not in playground {playground_id}")
                return {"playground_id": playground_id, "models": playground.models}

            playground.models.pop(model_id)
            self._write_playgrounds_to_json()

            logger.info(f"Removed model {model_id} from playground {playground_id}")
            return {"playground_id": playground_id, "models": playground.models}
        except Exception as e:
            logger.error(f"Error removing model from playground: {str(e)}")
            raise

    def list_playgrounds(self):
        """
        Lists all playgrounds.

        Returns:
            A dictionary containing all playgrounds and their details.
        """
        playground_dict = {}
        for playground_id in self.playgrounds:
            playground = self.playgrounds[playground_id]
            playground_dict[playground_id] = playground.create_playground_dictionary()
        return playground_dict

    def get_playground_info(self, playground_id: str):
        """
        Retrieves information about a specific playground.

        Args:
            playground_id: The ID of the playground.

        Returns:
            A dictionary containing the playground details.
        """
        return self.playgrounds[playground_id].create_playground_dictionary()

    def configure_chain(self, playground_id: str, chain: list):
        """
        Configures a chain of models for a playground.

        Args:
            playground_id: The ID of the playground.
            chain: A list of model IDs representing the chain.

        Returns:
            A dictionary indicating the status of the chain configuration.
        """
        playground = self.playgrounds[playground_id]

        if playground.active_chain:
            return {"error": f"Playground {playground_id} is already running a chain, please stop it before configuring."}

        prev_output_type = None

        for model_id in chain:
            if model_id not in playground.models:
                return {"error": f"Model {model_id} not in playground {playground_id}"}
            input_type = playground.models.get(model_id).get("input")
            output_type = playground.models.get(model_id).get("output")
            if input_type != prev_output_type and prev_output_type is not None:
                return {"error": f"Model {model_id} does not match the expected output of the previous model in the chain."}
            prev_output_type = output_type

        playground.chain = chain
        self._write_playgrounds_to_json()
        return {"playground_id": playground_id, "chain": chain}

    def load_playground_chain(self, playground_id: str):
        """
        Loads the chain of models for a playground.

        Args:
            playground_id: The ID of the playground.

        Returns:
            A boolean indicating the success of the operation.
        """
        if playground_id not in self.playgrounds:
            return {"error": f"Playground {playground_id} not found"}
        playground = self.playgrounds[playground_id]
        logger.info(f"Loading chain for playground {playground_id}")
        for model_id in playground.chain:
            self.model_control.load_model(model_id)
            logger.info(f"Model {model_id} loaded")

        playground.active_chain = True

        runtime_data = RuntimeControl.get_runtime_data("playground")
        for model_id in playground.chain:
            if runtime_data.get(model_id):
                runtime_data[model_id].append(playground_id)
            else:
                runtime_data.update({model_id: [playground_id]})
        RuntimeControl.update_runtime_data("playground", runtime_data)
        return True

    def stop_playground_chain(self, playground_id: str):
        """
        Stops the chain of models for a playground.

        Args:
            playground_id: The ID of the playground.

        Returns:
            A boolean indicating the success of the operation.
        """
        playground = self.playgrounds[playground_id]

        runtime_data = RuntimeControl.get_runtime_data("playground")

        for model_id in playground.chain:
            runtime_data[model_id].remove(playground_id)
            if len(runtime_data[model_id]) == 0:
                del runtime_data[model_id]

        RuntimeControl.update_runtime_data("playground", runtime_data)

        for model_id in playground.chain:
            if runtime_data.get(model_id) is None:
                self.model_control.unload_model(model_id)
                print("model unloaded", model_id)

        return True

    def _initialise_playground(self, playground_id: str):
        """
        Initializes a playground from JSON data.

        Args:
            playground_id: The ID of the playground.
        """
        playground_info = self._get_playground_json_data(playground_id)
        description = playground_info.get("description", "")
        models = playground_info.get("models", {})
        chain = playground_info.get("chain", [])
        playground = Playground(playground_id, description, models, chain)
        self.playgrounds[playground_id] = playground

    def _initialise_all_playgrounds(self):
        """
        Initializes all playgrounds from JSON data.

        Returns:
            A dictionary indicating the status of the initialization operation.
        """
        try:
            playgrounds = JSONHandler.read_json(PLAYGROUND_JSON_PATH)
            for playground_id in playgrounds:
                self._initialise_playground(playground_id)
            return {"status": "success", "message": "Playgrounds initialised"}
        except Exception as e:
            logger.error(f"Error listing playgrounds: {str(e)}")
            raise

    def inference(self, inference_request):
        """
        Performs inference on a playground's model chain.

        Args:
            inference_request: A dictionary containing the playground ID and the data for inference.

        Returns:
            The result of the inference.
        """
        playground_id = inference_request.get("playground_id")
        data = inference_request.get("data")
        playground = self.playgrounds[playground_id]

        for model_id in playground.chain:
            model_inference_request = {
                "model_id": model_id,
                "data": {"payload": str(data)},
            }
            inference_result = self.model_control.inference(model_inference_request)
            print("inference_result", inference_result)
            data = inference_result
        return inference_result

    def _initialise_playground_data_directory(self):
        """
        Creates the directory for playground data if it does not exist.

        Returns:
            A boolean indicating the success of the operation.
        """
        if not os.path.exists(PLAYGROUND_JSON_PATH):
            with open(PLAYGROUND_JSON_PATH, "w") as f:
                json.dump({}, f)
        return True

    def _get_playground_json_data(self, playground_id: str):
        """
        Retrieves JSON data for a specific playground.

        Args:
            playground_id: The ID of the playground.

        Returns:
            A dictionary containing the playground data.
        """
        try:
            playgrounds = JSONHandler.read_json(PLAYGROUND_JSON_PATH)
            return playgrounds[playground_id]
        except Exception as e:
            logger.error(f"Error getting playground info: {str(e)}")
            raise

    def _write_playgrounds_to_json(self):
        """
        Writes the current playground data to JSON.

        Returns:
            A boolean indicating the success of the operation.
        """
        playground_dict = self.list_playgrounds()
        JSONHandler.write_json(PLAYGROUND_JSON_PATH, playground_dict)
        return True