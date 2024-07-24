import multiprocessing
import json
import logging
import os
import time
import gc
from backend.settings.settings import get_hardware_preference, set_hardware_preference
from backend.controlers.library_control import LibraryControl
from backend.utils.helpers import install_packages
import torch
import importlib
import shutil

logger = logging.getLogger(__name__)

class ModelControl:
    def __init__(self):
        self.models = {}
        self.hardware_preference = get_hardware_preference()  # Default will be CPU
        self.library_control = LibraryControl()
        
    def set_hardware_preference(self, device: str):
        set_hardware_preference(device)
        self.hardware_preference = device
    
    @staticmethod
    def _download_process(model_class, model_id, model_info, library_control):
        logger.info(f"Starting download for model {model_id}")
        start_time = time.time()
        try:
            new_entry = model_class.download(model_id, model_info)
            if new_entry:
                library_control.update_library(model_id, new_entry)
                end_time = time.time()
                logger.info(f"Completed download for model {model_id} in {end_time - start_time:.2f} seconds")
            else:
                logger.error(f"Failed to download model {model_id}: new_entry is None")
        except Exception as e:
            logger.error(f"Error downloading model {model_id}: {str(e)}")
            return False
        return True

    @staticmethod
    def _load_process(model_class, conn, model_id, device, model_info):
        # instantiate the model class with model_id
        model = model_class(model_id=model_id)
        model.load(device=device, model_info=model_info)
        conn.send("Model loaded")
        while True:
            req = conn.recv()
            if req == "terminate":
                conn.send("Terminating")
                break
            # the first if block is for backward compatibility
            # i.e. if type(req) == str and req.startswith("predict:")
            # pls remove this block after all models are updated
            # pls keep the second if block (req["task"] == "inference":)
            if type(req) == str and req.startswith("predict:"):
                payload = json.loads(req.split(":", 1)[1])
                prediction = model.process_request(payload)
                conn.send(prediction)
            elif req["task"] == "inference":
                print("running control inference")
                print("req data ", req["data"])
                prediction = model.inference(req["data"])
                print("prediction done")
                print(prediction)
                conn.send(prediction)
            elif req["task"] == "train":
                print("running control train")
                print("req data ", req["data"])
                prediction = model.train(req["data"])
                print("prediction done")
                print(prediction)
                conn.send(prediction)
            elif req["task"] == "configure":
                print("running control configure")
                print("req data ", req["data"])
                result = model.configure(req["data"])
                print("configure done")
                print(result)
                conn.send(result)

    def download_model(self, model_id: str, auth_token: str = None):
        model_info = self.library_control.get_model_info_index(model_id)
        if not model_info:
            logger.error(f"Model info not found for {model_id}")
            return False
        

        model_info.update({"auth_token": auth_token})

        # Install required packages
        install_packages(model_info.get('requirements', {}).get('required_packages', []))
        
        model_class = self._get_model_class(model_id, "index")

        process = multiprocessing.Process(target=self._download_process, args=(model_class, model_id, model_info, self.library_control))
        process.start()
        process.join()
        
        # Check if the download was successful
        return self.library_control.get_model_info_library(model_id) is not None
            
    def load_model(self, model_id: str):
        model_info = self.library_control.get_model_info_library(model_id)
        if not model_info:
            logger.error(f"Model info not found for {model_id}")
            return False

        logger.debug(f"Fetched model info: {model_info}")

        model_class = self._get_model_class(model_id, "library")
        model_dir = model_info['dir']
        is_online = model_info.get('is_online', False)


        if not os.path.exists(model_dir) and not is_online:
            logger.error(f"Model directory not found: {model_dir}")
            return False

        device = torch.device("cuda" if self.hardware_preference == "gpu" and torch.cuda.is_available() else "cpu")
        logger.debug(f"Using device: {device}")

        parent_conn, child_conn = multiprocessing.Pipe()
        process = multiprocessing.Process(target=self._load_process, args=(model_class, child_conn, model_id, device, model_info))
        process.start()

        response = parent_conn.recv()
        logger.debug(f"Received response from load process: {response}")

        if response == "Model loaded":
            self.models[model_id] = {'process': process, 'conn': parent_conn, 'model': model_class}
            logger.info(f"Model {model_id} loaded and process started.")
            return True
        else:
            logger.error(f"Failed to load model {model_id}. Response: {response}")
            return False

    def is_model_loaded(self, model_id: str):
        return model_id in self.models

    def unload_model(self, model_id: str):
        try:
            if model_id in self.models:
                conn = self.models[model_id]['conn']
                conn.send("terminate")
                self.models[model_id]['process'].join()
                del self.models[model_id]
                gc.collect()
                logger.info(f"Model {model_id} unloaded and memory freed.")
                return True
            logger.error(f"Model {model_id} not found in active models.")
            return False
        except Exception as e:
            logger.error(f"Error unloading model {model_id}: {e}")
            return False
        
    def list_active_models(self):
        active_models_info = [{"model_id": model, "process_alive": self.models[model]['process'].is_alive()} for model in self.models]
        logger.debug(f"Active models: {active_models_info}")
        return active_models_info
    
    def get_active_model(self, model_id: str):
        if model_id in self.models:
            return self.models[model_id]
        logger.error(f"Model {model_id} not found in active models.")
        raise KeyError(f"Model {model_id} not found in active models.")
    
    def delete_model(self, model_id: str):
        if self.is_model_loaded(model_id):
            self.unload_model(model_id)
        #use model info to extract dir and then delete model folder and contents from directory. if successfull library controll called to delete model from json
        model_info = self.library_control.get_model_info_library(model_id)
        if model_info:
            model_dir = model_info['dir']
            if os.path.exists(model_dir):
                shutil.rmtree(model_dir)
                logger.info(f"Model {model_id} directory deleted")

        self.library_control.delete_model(model_id)
        return {"message": f"Model {model_id} deleted"}
    
    def inference(self, inference_request):
        try:
            print(inference_request)
            model_id = inference_request['model_id']
            inference_request = inference_request
            active_model = self.get_active_model(model_id)
            conn = active_model['conn']
            req = inference_request
            req['task'] = "inference"
            conn.send(req)
            return conn.recv()
        except KeyError:
            return {"error": f"Model {inference_request['model_id']} is not loaded. Please load the model first"}
        
    def configure_model(self, configure_request):
        try:
            print(configure_request)
            model_id = configure_request['model_id']
            config_data = configure_request['data']
            
            model_info = self.library_control.get_model_info_library(model_id)
            is_online = model_info.get('is_online', False)  
            
            updated_config = self.library_control.update_model_config(model_id, config_data)
            
            if updated_config:
                if is_online:
                    active_model = self.get_active_model(model_id)
                    conn = active_model['conn']
                    req = config_data
                    req['task'] = "configure"
                    conn.send(req)
                    return conn.recv()
                else:
                    if self.is_model_loaded(model_id):
                        self.unload_model(model_id)
                        self.load_model(model_id)
                        
                return {"message": f"Model {model_id} configuration updated in library"}
            else:
                return {"error": f"Failed to update configuration for model {model_id}"}   
        except KeyError:
            return {"error": f"Model {configure_request['model_id']} not found in library"}
    
    def train_model(self, train_request):
        try:
            print(train_request)
            model_id = train_request['model_id']
            train_request = train_request
            active_model = self.get_active_model(model_id)
            conn = active_model['conn']
            req = train_request
            req['task'] = "train"
            conn.send(req)
            result = conn.recv()
            
            if "error" not in result:
                new_model_info = result["new_model_info"]
                new_model_id = new_model_info["model_id"]
            
                # Get the original model info
                original_model_info = self.library_control.get_model_info_library(model_id)
            
                # Create a new entry by copying the original model info and updating with new info
                updated_model_info = original_model_info.copy()
                updated_model_info.update(new_model_info)
            
                # Ensure that these fields are correctly set for the new model
                updated_model_info["is_customised"] = True
                updated_model_info["base_model"] = new_model_id  
            
                # Add the new model to the library
                self.library_control.add_fine_tuned_model(updated_model_info)
                logger.info(f"New fine-tuned model {new_model_id} added to library")
            return result
        except KeyError:
            return {"error": f"Model {train_request['model_id']} is not loaded. Please load the model first"}
    
    # def train_model(self, model_id: str, training_params: dict):
    #     active_model = self.get_active_model(model_id)
    #     if not active_model:
    #         raise ValueError(f"Model {model_id} is not loaded")
        
    #     conn = active_model['conn']
    #     conn.send({"task": "train", "data": training_params})
    #     result = conn.recv()

    #     if "error" not in result:
    #         new_model_info = result["new_model_info"]
    #         new_model_id = new_model_info["model_id"]
            
    #         # Get the original model info
    #         original_model_info = self.library_control.get_model_info_library(model_id)
            
    #         # Create a new entry by copying the original model info and updating with new info
    #         updated_model_info = original_model_info.copy()
    #         updated_model_info.update(new_model_info)
            
    #         # Ensure that these fields are correctly set for the new model
    #         updated_model_info["is_customised"] = True
    #         updated_model_info["base_model"] = new_model_id  
            
    #         # Add the new model to the library
    #         self.library_control.add_fine_tuned_model(updated_model_info)
    #         logger.info(f"New fine-tuned model {new_model_id} added to library")
    
    #     return result

    # this will be deprecated
    def predict(self, model_id: str, request_payload: dict):
        active_model = self.get_active_model(model_id)
        if not active_model:
            raise ValueError(f"Model {model_id} is not loaded")

        conn = active_model['conn']
        conn.send(json.dumps(request_payload))
        return conn.recv()

    def _get_model_class(self, model_id: str, source: str):
        if source == "library":
            model_info = self.library_control.get_model_info_library(model_id)
        elif source == "index":
            model_info = self.library_control.get_model_info_index(model_id)
        else:
            raise ValueError(f"Invalid source: {source}. Use 'library' or 'index'.")

        if not model_info:
            raise ValueError(f"Model info not found for {model_id} in {source}")
    
        model_class_name = model_info.get('model_class')
        if not model_class_name:
            raise ValueError(f"Model class not specified for {model_id}")

        try:
            module = importlib.import_module('backend.models')
            model_class = getattr(module, model_class_name)
            return model_class
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Failed to load model class {model_class_name}: {str(e)}")
