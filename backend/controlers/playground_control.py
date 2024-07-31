import uuid
from backend.data_utils.json_handler import JSONHandler
from backend.core.config import PLAYGROUND_JSON_PATH
from backend.playground.playground import Playground
from backend.controlers.library_control import LibraryControl
from backend.controlers.runtime_control import RuntimeControl
import logging

logger = logging.getLogger(__name__)


class PlaygroundControl:
    def __init__(self, model_control):
        self.model_control = model_control
        self.library_control = LibraryControl()
        self.playgrounds = {}
        self.initialise_all_playgrounds()
    
    def create_playground(self,playground_id: str = None, description: str = None ):
        try:
            # If no playground_id is provided, generate a new one
            if playground_id is None:
                playground_id = str(uuid.uuid4())

            # Create new playground entry
            new_playground = {
                "description": description or "New Playground",
                "models": [],
                "chain": []
            }

            # Read existing playgrounds
            try:
                playgrounds = JSONHandler.read_json(PLAYGROUND_JSON_PATH)
            except FileNotFoundError:
                playgrounds = {}

            # Add new playground
            playgrounds[playground_id] = new_playground

            # Write updated playgrounds back to file
            result = JSONHandler.write_json(PLAYGROUND_JSON_PATH, playgrounds)
            if result:
                self.load_playground(playground_id)
            logger.info(f"Created new playground with ID: {playground_id}")
            return {"playground_id": playground_id, "playground": new_playground}

        except Exception as e:
            logger.error(f"Error creating playground: {str(e)}")
            raise
    
    def delete_playground(self, playground_id: str):
        try:
            playgrounds = JSONHandler.read_json(PLAYGROUND_JSON_PATH)
            if playground_id not in playgrounds:
                logger.error(f"Playground {playground_id} not found")
                return None
            
            deleted_playground = playgrounds.pop(playground_id)
            JSONHandler.write_json(PLAYGROUND_JSON_PATH, playgrounds)
            
            logger.info(f"Deleted playground with ID: {playground_id}")
            return {"playground_id": playground_id, "deleted_playground": deleted_playground}
        except Exception as e:
            logger.error(f"Error deleting playground: {str(e)}")
            raise
    
    def update_playground(self, playground_id: str, updated_data: dict):
        try:
            playgrounds = JSONHandler.read_json(PLAYGROUND_JSON_PATH)
            if playground_id not in playgrounds:
                logger.error(f"Playground {playground_id} not found")
                return None
            
            playgrounds[playground_id].update(updated_data)
            JSONHandler.write_json(PLAYGROUND_JSON_PATH, playgrounds)
            
            logger.info(f"Updated playground with ID: {playground_id}")
            return {"playground_id": playground_id, "updated_playground": playgrounds[playground_id]}
        except Exception as e:
            logger.error(f"Error updating playground: {str(e)}")
            raise
    
    def list_playgrounds(self):
        try:
            playgrounds = JSONHandler.read_json(PLAYGROUND_JSON_PATH)
            return playgrounds
        except Exception as e:
            logger.error(f"Error listing playgrounds: {str(e)}")
            raise
    
    def add_model_to_playground(self, playground_id: str, model_id: str):
        try:
            playgrounds = JSONHandler.read_json(PLAYGROUND_JSON_PATH)
            if playground_id not in playgrounds:
                logger.error(f"Playground {playground_id} not found")
                return None
            
            if model_id not in playgrounds[playground_id]['models']:
                playgrounds[playground_id]['models'].append(model_id)
                JSONHandler.write_json(PLAYGROUND_JSON_PATH, playgrounds)
                logger.info(f"Added model {model_id} to playground {playground_id}")
            else:
                logger.info(f"Model {model_id} already in playground {playground_id}")
            
            return {"playground_id": playground_id, "models": playgrounds[playground_id]['models']}
        except Exception as e:
            logger.error(f"Error adding model to playground: {str(e)}")
            raise
    
    def remove_model_from_playground(self, playground_id: str, model_id: str):
        try:
            playgrounds = JSONHandler.read_json(PLAYGROUND_JSON_PATH)
            if playground_id not in playgrounds:
                logger.error(f"Playground {playground_id} not found")
                return None
            
            if model_id in playgrounds[playground_id]['models']:
                playgrounds[playground_id]['models'].remove(model_id)
                JSONHandler.write_json(PLAYGROUND_JSON_PATH, playgrounds)
                logger.info(f"Removed model {model_id} from playground {playground_id}")
            else:
                logger.info(f"Model {model_id} not in playground {playground_id}")
            
            return {"playground_id": playground_id, "models": playgrounds[playground_id]['models']}
        except Exception as e:
            logger.error(f"Error removing model from playground: {str(e)}")
            raise
        
    def get_playground_info(self, playground_id: str):
        try:
            playgrounds = JSONHandler.read_json(PLAYGROUND_JSON_PATH)
            return playgrounds[playground_id]
        except Exception as e:
            logger.error(f"Error getting playground info: {str(e)}")
            raise
    
    def load_playground_chain(self, playground_id: str):
        # call load_playground_chain on specific instance of playground. 
        # If succesfull, call library control to set active_in_chain to True for all models in the chain
        result = self.playgrounds[playground_id].load_playground_chain()
        if result:
            runtime_data = RuntimeControl.get_runtime_data("playground")
            for model_id in self.playgrounds[playground_id].chain:
                if runtime_data.get(model_id):
                    runtime_data[model_id].append(playground_id)
                else:
                    runtime_data.update({model_id: [playground_id]})
            RuntimeControl.update_runtime_data("playground", runtime_data)
        return result
    
    def stop_playground_chain(self, playground_id: str):
        result = self.playgrounds[playground_id].stop_playground_chain()

        runtime_data = RuntimeControl.get_runtime_data("playground")
        
        for model_id in self.playgrounds[playground_id].chain:
            runtime_data[model_id].remove(playground_id)
            if len(runtime_data[model_id]) == 0:
                self.playgrounds[playground_id].unload_model(model_id)
                del runtime_data[model_id]
        RuntimeControl.update_runtime_data("playground", runtime_data)
        return result
    
    def add_chain_to_playground(self):
        pass
    
    def remove_chain_from_playground(self):
        pass
    
    def load_playground(self, playground_id: str):
        self.playgrounds[playground_id] = Playground(playground_id, self.model_control)
        playground_info = self.get_playground_info(playground_id)
        self.playgrounds[playground_id].load_playground(playground_id, playground_info)
        
    def initialise_all_playgrounds(self):
        playgrounds = self.list_playgrounds()
        for playground_id in playgrounds:
            self.load_playground(playground_id)
    
    def save_playground(self):
        pass
    
    def inference(self, request: dict):
        pass