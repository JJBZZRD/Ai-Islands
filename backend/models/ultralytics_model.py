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
    
    @staticmethod
    def download(model_id: str, model_info: dict):
        try:
            model_dir = os.path.join('data', 'downloads', 'ultralytics')
            if not os.path.exists(model_dir):
                os.makedirs(model_dir, exist_ok=True)
            
            model = YOLO(model_id) 
            model_file_name = f'{model_id}.pt' if not model_id.endswith('.pt') else model_id
            model_path = os.path.abspath(os.path.join(model_dir, model_file_name))
            
            print(f"Saving model to: {model_path}")
            model.save(model_path)
            print(f"Model {model_id} downloaded and saved to {model_path}")
            
            root_model_path = os.path.join(ROOT_DIR, model_file_name)
            if os.path.exists(root_model_path):
                os.remove(root_model_path)
                print(f"Deleted model file from root directory: {root_model_path}")

            model_info.update({
                "base_model": model_id,
                "dir": model_dir,
                "is_customised": False,
                "config":{}
            })
            return model_info
        except Exception as e:
            print(f"Error downloading model {model_id}: {str(e)}")
            return None

    """def load(self, model_path: str, device: torch.device):
        try:
            # get the path of the model file
            model_path = os.path.join(model_path, f"{self.model_id}.pt")
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found: {model_path}")
            
            self.model = YOLO(model_path)  # Load the YOLO model from the specified path
            logger.info(f"Model loaded from {model_path}")
            
            # Set device based on user preference
            #device = get_hardware_preference()
            self.model.to(device)
        except Exception as e:
            logger.error(f"Error loading model from {model_path}: {str(e)}")"""
            
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
        
            self.model = YOLO(model_path)  # Load the YOLO model from the specified path
            logger.info(f"Model loaded from {model_path}")
        
            # Set device based on user preference
            self.model.to(device)
            
        except Exception as e:
            logger.error(f"Error loading model from {model_path}: {str(e)}")

    
    def inference(self, request_payload: dict):
        print("runned yolo inference function")
        if "image_path" in request_payload:
            print("runned yolo inference")
            return self.predict_image(request_payload["image_path"])
        elif "video_frame" in request_payload:
            return self.predict_video(request_payload["video_frame"])
        else:
            return {"error": "Invalid request payload"}
    
    # process request should be merged into inference
    def process_request(self, request_payload: dict):
        print("runned yolo inference function")
        if "image_path" in request_payload:
            print("runned yolo inference")
            return self.predict_image(request_payload["image_path"])
        elif "video_frame" in request_payload:
            return self.predict_video(request_payload["video_frame"])
        else:
            return {"error": "Invalid request payload"}

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
            print("runned yolo predict image")
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


    """def train(self, data_path: str, epochs: int = 20):
        try:
            if self.model is None:
                raise ValueError("Model is not loaded")
            
            self.model.train(data=data_path, epochs=epochs)
            logger.info(f"Model trained on {data_path} for {epochs} epochs")
        except Exception as e:
            logger.error(f"Error training model on data {data_path}: {str(e)}")"""
            
    def train(self, data_path: str, epochs: int = 10, batch_size: int = 16, learning_rate: float = 0.001):
        try:
            if self.model is None:
                raise ValueError("Model is not loaded")

            # Training the model
            self.model.train(data=data_path, epochs=epochs, imgsz=640, lr0=learning_rate, batch=batch_size)

            # Save the trained model with a different name
            trained_model_name = f"{self.model_id}_ft.pt"
            trained_model_path = os.path.join('data', 'downloads', 'ultralytics', trained_model_name)
            self.model.save(trained_model_path)

            logger.info(f"Model trained on {data_path} for {epochs} epochs with batch size {batch_size} and learning rate {learning_rate}. Model saved to {trained_model_path}")
        
           # Update the library with the updated model entry
            updated_entry = {
                "is_customised": True,
                "dir": os.path.dirname(trained_model_path),
                "model_desc": f"Fine-tuned {self.model_id} model",
            }
             # Save updated entry to the library (using a method from library control)
            self.library_control.update_library(self.model_id, updated_entry)

            return {"message": "Training completed successfully", "trained_model_path": trained_model_path}
        except Exception as e:
            logger.error(f"Error training model on data {data_path}: {str(e)}")
            return {"error": str(e)}

    def inference(self, *args):
        pass
