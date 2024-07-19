import os
from tempfile import TemporaryDirectory
from ultralytics import YOLO
from backend.core.config import ROOT_DIR, DOWNLOADED_MODELS_PATH
from backend.data_utils.json_handler import JSONHandler
from .base_model import BaseModel
import logging
import cv2
import numpy as np
import torch
from backend.settings.settings import get_hardware_preference
from backend.controlers.library_control import LibraryControl

logger = logging.getLogger(__name__)

class UltralyticsModel(BaseModel):
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.model = None
        self.library_control = LibraryControl()
        self.model_info = self.library_control.get_model_info_index(model_id)
        self.model_type = self.model_info['requirements']['required_classes']['model']
    
    @staticmethod
    def download(model_id: str, model_info: dict):
        try:
            model_dir = os.path.join('data', 'downloads', 'ultralytics')
            if not os.path.exists(model_dir):
                os.makedirs(model_dir, exist_ok=True)

            model_type = model_info['requirements']['required_classes']['model']
            model_file_name = f'{model_id}.pt' if not model_id.endswith('.pt') else model_id
            model_path = os.path.abspath(os.path.join(model_dir, model_file_name))
            if model_type == 'YOLO':
                model = YOLO(model_id)
                model.save(model_path)
            else:
                raise ValueError(f"Unsupported model type: {model_type}")

            print(f"Model {model_id} downloaded and saved to {model_path}")

            root_model_path = os.path.join(ROOT_DIR, model_file_name)
            if os.path.exists(root_model_path):
                os.remove(root_model_path)
                print(f"Deleted model file from root directory: {root_model_path}")

            model_info.update({
                "base_model": model_id,
                "dir": model_dir,
                "is_customised": False,
                "config": {}
            })
            return model_info
        except Exception as e:
            print(f"Error downloading model {model_id}: {str(e)}")
            return None
            
    def load(self, model_path: str, device: torch.device):
        try:
            # Retrieve model info from the library
            model_info = self.library_control.get_model_info_library(self.model_id)

            if not model_info:
                raise FileNotFoundError(f"Model info not found for {self.model_id}")

            # Get the path of the model file
            model_file_name = f"{self.model_id}.pt"
            model_path = os.path.join(model_info['dir'], model_file_name)

            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found: {model_path}")

            if self.model_type == "YOLO":
                self.model = YOLO(model_path)  # Load the YOLO model from the specified path
            else:
                raise ValueError(f"Unsupported model type: {self.model_type}")
        
            logger.info(f"Model loaded from {model_path}")

            # Set device based on user preference
            self.model.to(device)
        
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
    
    def inference(self, request_payload: dict):
        print("Running inference function")
        
        if self.model is None:
            raise ValueError("Model is not loaded")
        if "image_path" in request_payload:
            print("Running image inference")
            return self.predict_image(request_payload["image_path"])
        elif "video_frame" in request_payload:
            print("Running video inference")
            return self.predict_video(request_payload["video_frame"])
        else:
            return {"error": "Invalid request payload"}
    
    """# process request should be merged into inference
    def process_request(self, request_payload: dict):
        print("runned yolo inference function")
        if "image_path" in request_payload:
            print("runned yolo inference")
            return self.predict_image(request_payload["image_path"])
        elif "video_frame" in request_payload:
            return self.predict_video(request_payload["video_frame"])
        else:
            return {"error": "Invalid request payload"}"""

    def predict_image(self, image_path: str):
        try:
            if self.model is None:
                raise ValueError("Model is not loaded")
            
            results = self.model.predict(image_path)
            predictions = []
            class_names = self.model.names
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = box.conf[0].item()
                    coords = box.xyxy[0].tolist()
                    predictions.append({
                        "class": class_names[cls],
                        "confidence": conf,
                        "coordinates": coords
                    })
            return predictions
        except Exception as e:
            print(f"Error predicting image {image_path}: {str(e)}")
            return {"error": str(e)}
        
    def predict_video(self, frame: list):
        try:
            if self.model is None:
                raise ValueError("Model is not loaded")
        
            print("Starting prediction on video frame")  
        
            frame = np.array(frame, dtype=np.uint8)
            results = self.model.predict(frame)
            predictions = []
            class_names = self.model.names
        
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = box.conf[0].item()
                    coords = box.xyxy[0].tolist()
                    predictions.append({
                        "class": class_names[cls],
                        "confidence": conf,
                        "coordinates": coords
                    })

            print("Prediction on frame completed")  
            return predictions
        except Exception as e:
            print(f"Error predicting video frame: {str(e)}")
            return {"error": str(e)}

    def train(self, training_params: dict):
        try:
            if self.model is None:
                raise ValueError("Model is not loaded")

            data_path = training_params['data']
            epochs = training_params.get('epochs', 10)
            batch_size = training_params.get('batch_size', 16)
            learning_rate = training_params.get('learning_rate', 0.001)
            imgsz = training_params.get('imgsz', 640)  

            logger.info(f"Starting training with parameters: epochs={epochs}, batch_size={batch_size}, learning_rate={learning_rate}, imgsz={imgsz}")
            self.model.train(data=data_path, epochs=epochs, imgsz=imgsz, lr0=learning_rate, batch=batch_size)
            logger.info(f"Actual image size used for training: {self.model.args.imgsz}")
            logger.info("Training completed")
            
            i = 1
            while os.path.exists(os.path.join('data', 'downloads', 'ultralytics', f"{self.model_id}_{i}.pt")):
                i += 1
            
            trained_model_name = f"{self.model_id}_{i}.pt"
            trained_model_path = os.path.join('data', 'downloads', 'ultralytics', trained_model_name)
            self.model.save(trained_model_path)

            logger.info(f"Model trained on {data_path} for {epochs} epochs with batch size {batch_size}, learning rate {learning_rate}, and image size {imgsz}. Model saved to {trained_model_path}")
        
            new_entry = {
                "dir": os.path.dirname(trained_model_path),
                "model_desc": f"Fine-tuned {self.model_id} model",
            }
            new_model_id = self.library_control.add_fine_tuned_model(self.model_id, new_entry)

            return {"message": "Training completed successfully", "trained_model_path": trained_model_path, "new_model_id": new_model_id}
        except Exception as e:
            logger.error(f"Error training model on data {data_path}: {str(e)}")
            return {"error": str(e)}