import os
from tempfile import TemporaryDirectory
from ultralytics import YOLO
from backend.core.config import ROOT_DIR
from .base_model import BaseModel
import logging
import cv2
import numpy as np
import torch
from backend.settings.settings import get_hardware_preference

logger = logging.getLogger(__name__)

class UltralyticsModel:
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.model = None
    
    @staticmethod
    def download(model_id: str, save_dir: str):
        try:
            model = YOLO(model_id) 
            model_file_name = f'{model_id}.pt' if not model_id.endswith('.pt') else model_id
            # get the absolute path of the model file
            model_path = os.path.abspath(os.path.join(save_dir, model_file_name))
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            print(f"Saving model to: {model_path}")

            # Save the model to the specified path
            model.save(model_path)
            print(f"Model {model_id} downloaded and saved to {model_path}")
            
            # Checking whether the model file exists in the root directory and this will delete it so no copies
            root_model_path = os.path.join(ROOT_DIR, model_file_name)
            if os.path.exists(root_model_path):
                os.remove(root_model_path)
                print(f"Deleted model file from root directory: {root_model_path}")
        except Exception as e:
            print(f"Error downloading model {model_id}: {str(e)}")
    
    def load(self, model_path: str, device: torch.device):
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
            logger.error(f"Error loading model from {model_path}: {str(e)}")
    
    def process_request(self, request_payload: dict):
        if "image_path" in request_payload:
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


    def train(self, data_path: str, epochs: int = 20):
        try:
            if self.model is None:
                raise ValueError("Model is not loaded")
            
            self.model.train(data=data_path, epochs=epochs)
            logger.info(f"Model trained on {data_path} for {epochs} epochs")
        except Exception as e:
            logger.error(f"Error training model on data {data_path}: {str(e)}")
