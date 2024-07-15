from backend.models.transformer_model import TransformerModel
from backend.models.ultralytics_model import UltralyticsModel
from backend.models.watson_model import WatsonModel
import multiprocessing
import json
from backend.data_utils.json_handler import JSONHandler
from backend.core.config import MODEL_INDEX_PATH, DOWNLOADED_MODELS_PATH
from backend.models.base_model import BaseModel
import logging
import os
import time
import gc
from backend.settings.settings import get_hardware_preference, set_hardware_preference
import torch
import transformers

logger = logging.getLogger(__name__)

class ModelControl:
    def __init__(self):
        self.models = {}
        self.hardware_preference = get_hardware_preference()  # Default wil be CPU
        
    def set_hardware_preference(self, device: str):
        set_hardware_preference(device)
        self.hardware_preference = device
    
    @staticmethod
    def _download_process(model_class, model_id, model_dir, model_info):
        logger.info(f"Starting download for model {model_id}")
        start_time = time.time()
        model_class.download(model_id, model_dir, model_info)
        end_time = time.time()
        logger.info(f"Completed download for model {model_id} in {end_time - start_time:.2f} seconds")
            
    @staticmethod
    def _load_process(model_class, model_path, conn, model_id, device, required_classes=None, pipeline_tag=None):
        # instantiate the model class with model_id
        model = model_class(model_id=model_id)
        if required_classes:
            # if extra classes are needed to load the model (transformers)
            model.load(model_path, device, required_classes, pipeline_tag)
        else:
            # if no extra classes are needed to load the model (ultralytics)
            model.load(model_path, device)
        conn.send("Model loaded")
        while True:
            msg = conn.recv()
            if msg == "terminate":
                conn.send("Terminating")
                break
            elif msg.startswith("predict:"):
                payload = json.loads(msg.split(":", 1)[1])
                prediction = model.process_request(payload)
                conn.send(prediction)
            elif msg.startswith("sentimentPredict"):
                prediction = model.predict(msg.split(":", 1)[1])
                conn.send(prediction)

    def _get_model_info_library(self, model_id: str):
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

    def _get_model_class(self, model_source: str):
        if model_source == 'transformers':
            return TransformerModel
        elif model_source == 'ultralytics':
            return UltralyticsModel
        elif model_source == 'watson':
            return WatsonModel
        else:
            raise ValueError(f"Unknown model source: {model_source}")
        
    def _get_model_info_index(self, model_id: str):
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
    
    def download_model(self, model_id: str):
        model_info = self._get_model_info_index(model_id)
        if not model_info:
            logger.error(f"Model info not found for {model_id}")
            return False
    
        if model_info.get('is_online', False):
            logger.info(f"Model {model_id} is online and does not require downloading.")
            return True
    
        model_class = self._get_model_class(model_info['model_source'])
    
        process = multiprocessing.Process(target=self._download_process, args=(model_class, model_id, model_info))
        process.start()
        process.join()
        return True

    def load_model(self, model_id: str):
        model_info = self._get_model_info_library(model_id)
        if not model_info:
            logger.error(f"Model info not found for {model_id}")
            return False

        model_class = self._get_model_class(model_info['model_source'])
        model_dir = model_info['dir']
        # if required classes are not provided, set it to None
        required_classes = model_info.get('required_classes', None)
        pipeline_tag = model_info.get('pipeline_tag', None)
        
        if not os.path.exists(model_dir):
            logger.error(f"Model file not found: {model_dir}")
            return False
        
        # Use the user-defined hardware preference
        device = torch.device("cuda" if self.hardware_preference == "gpu" and torch.cuda.is_available() else "cpu")

        parent_conn, child_conn = multiprocessing.Pipe()
        process = multiprocessing.Process(target=self._load_process, args=(model_class, model_dir, child_conn, model_id, device, required_classes, pipeline_tag))
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
        return None
    
    def delete_model(self, model_id: str):
        model_info = self._get_model_info_library(model_id)
        if not model_info:
            logger.error(f"Model info not found for {model_id}")
            return False

        library = JSONHandler.read_json(DOWNLOADED_MODELS_PATH)
        library = library.pop(model_id, None)
        JSONHandler.write_json(DOWNLOADED_MODELS_PATH, library)
        logger.info(f"Model {model_id} deleted from library.")
        return True
    
    # Ben: I guess this method requires further modification in order to work with all kinds of models
    def predict(self, model_id: str, request_payload: dict):
        active_model = self.get_active_model(model_id)
        if not active_model:
            raise ValueError(f"Model {model_id} is not loaded")

        conn = active_model['conn']
        conn.send(json.dumps(request_payload))
        return conn.recv()
    