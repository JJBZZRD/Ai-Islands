import multiprocessing
import json
import logging
import os
import time
import gc
from backend.settings.settings import get_hardware_preference, set_hardware_preference
from backend.controlers.library_control import LibraryControl
import torch
import importlib

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
        model.load(device, model_info)
        conn.send("Model loaded")
        while True:
            req = conn.recv()
            if req == "terminate":
                conn.send("Terminating")
                break
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

    def download_model(self, model_id: str, auth_token: str = None):
        model_info = self.library_control.get_model_info_index(model_id)
        if not model_info:
            logger.error(f"Model info not found for {model_id}")
            return False

        model_info.update({"auth_token": auth_token})

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

        model_class = self._get_model_class(model_id, "library")
        model_dir = model_info['dir']
        
        if not os.path.exists(model_dir):
            logger.error(f"Model directory not found: {model_dir}")
            return False
        
        device = torch.device("cuda" if self.hardware_preference == "gpu" and torch.cuda.is_available() else "cpu")

        parent_conn, child_conn = multiprocessing.Pipe()
        process = multiprocessing.Process(target=self._load_process, args=(model_class, child_conn, model_id, device, model_info))
        process.start()

        if parent_conn.recv() == "Model loaded":
            self.models[model_id] = {'process': process, 'conn': parent_conn, 'model': model_class}
            logger.info(f"Model {model_id} loaded and process started.")
            return True
        else:
            logger.error(f"Failed to load model {model_id}.")
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
        return self.library_control.delete_model(model_id)
    
    def inference(self, inference_request):
        try:
            print(inference_request)
            inference_request = inference_request
            active_model = self.get_active_model(inference_request['model_id'])
            conn = active_model['conn']
            req = inference_request
            req['task'] = "inference"
            conn.send(req)
            return conn.recv()
        except KeyError:
            return {"error": f"Model {inference_request['model_id']} is not loaded. Please load the model first"}
        
    def configure_model(self, model_id: str, config: dict):
        active_model = self.get_active_model(model_id)
        active_model['model'].configure(config)
            
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
            raise ValueError(f"Model info not found for {model_id}")
        
        model_class_name = model_info.get('model_class')
        if not model_class_name:
            raise ValueError(f"Model class not specified for {model_id}")
        
        try:
            module = importlib.import_module('backend.models')
            model_class = getattr(module, model_class_name)
            return model_class
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Failed to load model class {model_class_name}: {str(e)}")