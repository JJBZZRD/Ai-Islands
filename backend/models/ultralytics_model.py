import logging
import os
import shutil

import cv2
import numpy as np
import torch
from PIL import Image
from ultralytics import YOLO

from backend.core.config import DOWNLOADED_MODELS_PATH, ROOT_DIR, UPLOAD_DATASET_DIR
from backend.core.exceptions import ModelError
from backend.data_utils.file_utils import verify_file
from backend.data_utils.json_handler import JSONHandler
from backend.utils.process_vis_out import process_vision_output

from .base_model import BaseModel

logger = logging.getLogger(__name__)

class UltralyticsModel(BaseModel):
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.model = None
    
    @staticmethod
    def download(model_id: str, model_info: dict):
        try:
            base_dir = os.path.join('data', 'downloads', 'ultralytics')
            model_dir = os.path.join(base_dir, model_id)
            if not os.path.exists(model_dir):
                os.makedirs(model_dir, exist_ok=True)

            model_type = model_info['requirements']['required_classes']['model']
            model_file_name = f'{model_id}.pt' if not model_id.endswith('.pt') else model_id
            model_path = os.path.abspath(os.path.join(model_dir, model_file_name))
            if model_type == 'YOLO':
                model = YOLO(model_id)
                model.save(model_path)
            else:
                logger.error(f"Unsupported model type: {model_type}")
                raise ModelError(f"Unsupported model type: {model_type}")

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
            raise ModelError(f"Error downloading model {model_id}: {str(e)}")
            
    def load(self, device: torch.device, model_info: dict):
        try:
            # Retrieve model info from the library
            #model_info = self.library_control.get_model_info_library(self.model_id)

            #if not model_info:
                #raise FileNotFoundError(f"Model info not found for {self.model_id}")

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
            logger.error(f"Error loading model: {str(e)}")
    
    def inference(self, request_payload: dict):
        logger.info("Running inference function")
        
        if self.model is None:
            raise ValueError("Model is not loaded")
        
        visualize = request_payload.get("visualize", False)
        result = {}

        if "image_path" in request_payload:
            logger.info("Running image inference")
            image_path = request_payload["image_path"]
            predictions = self.predict_image(image_path)
            result["predictions"] = predictions

        elif "video_frame" in request_payload:
            logger.info("Running video inference")
            frame = request_payload["video_frame"]
            predictions = self.predict_video(frame)
            result["predictions"] = predictions

        else:
            logger.error("Invalid request payload")
            return {"error": "Invalid request payload"}

        logger.info(f"Inference result: {result}")
        return result

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
        
    def predict_video(self, frame):
        try:
            if self.model is None:
                raise ValueError("Model is not loaded")

            logger.info("Starting prediction on video frame")
            logger.info(f"Received frame type: {type(frame)}")

            if isinstance(frame, list):
                frame = np.array(frame, dtype=np.uint8)
            elif isinstance(frame, bytes):
                nparr = np.frombuffer(frame, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None or frame.size == 0:
                raise ValueError("Invalid frame data")

            logger.info(f"Frame shape: {frame.shape}")

            results = self.model.predict(frame)
            logger.info(f"Prediction results: {results}")
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

            logger.info(f"Processed predictions: {predictions}")
            return predictions
        except ValueError as ve:
            logger.error(f"ValueError in predict_video: {str(ve)}")
            return {"error": str(ve)}
        except Exception as e:
            logger.error(f"Error predicting video frame: {str(e)}")
            return {"error": str(e)}

    def train(self, data):
        try:
            if self.model is None:
                raise ValueError("Model is not loaded")

            training_params = self._handle_training_request(data)
            
            data_path = training_params['data']
            epochs = training_params.get('epochs', 10)
            batch_size = training_params.get('batch_size', 16)
            learning_rate = training_params.get('learning_rate', 0.001)
            imgsz = training_params.get('imgsz', 640)  

            logger.info(f"Starting training with parameters: epochs={epochs}, batch_size={batch_size}, learning_rate={learning_rate}, imgsz={imgsz}")
        
            if not os.path.exists(data_path):
                raise FileNotFoundError(f"Dataset path not found: {data_path}")
        
            self.model.train(data=data_path, epochs=epochs, imgsz=imgsz, lr0=learning_rate, batch=batch_size)
            logger.info("Training completed")

            # Finding the best.pt file in the runs/detect/train folder
            runs_folder = os.path.join('runs', 'detect', 'train')
            best_pt_path = None
            for root, dirs, files in os.walk(runs_folder):
                if 'best.pt' in files:
                    best_pt_path = os.path.join(root, 'best.pt')
                    break

            if not best_pt_path:
                raise FileNotFoundError("best.pt file not found after training")

            suffix = self.get_next_suffix(self.model_id)
            trained_model_name = f"{self.model_id}_{suffix}.pt"
            
            # Save thr trained model to the ultralytics folder
            base_dir = os.path.join('data', 'downloads', 'ultralytics')
            trained_model_dir = os.path.join(base_dir, f"{self.model_id}_{suffix}")
            os.makedirs(trained_model_dir, exist_ok=True)
            
            trained_model_path = os.path.join(trained_model_dir, trained_model_name)
            shutil.copy(best_pt_path, trained_model_path)

            logger.info(f"Model trained on {data_path} for {epochs} epochs with batch size {batch_size}, learning rate {learning_rate}, and image size {imgsz}. Model saved to {trained_model_path}")

            new_model_info = {
                "model_id": f"{self.model_id}_{suffix}",
                "base_model": f"{self.model_id}_{suffix}",
                "dir": trained_model_dir,
                "model_desc": f"Fine-tuned {self.model_id} model",
                "is_customised": True,
                "config": {
                    "epochs": epochs,
                    "batch_size": batch_size,
                    "learning_rate": learning_rate,
                    "imgsz": imgsz
                }
            }

            # Remove the extra pretrained model file
            pretrained_model_path = os.path.join(ROOT_DIR, f"{self.model_id}.pt")
            if os.path.exists(pretrained_model_path):
                os.remove(pretrained_model_path)
                logger.info(f"Deleted pretrained model file from root directory: {pretrained_model_path}")
                
            # Remove the runs folder
            runs_folder = os.path.join(ROOT_DIR, 'runs')
            if os.path.exists(runs_folder) and os.path.isdir(runs_folder):
                shutil.rmtree(runs_folder)
                logger.info(f"Deleted runs folder: {runs_folder}")

            return {
                "message": "Training completed successfully",
                "data": {
                    "trained_model_path": trained_model_path,
                    "new_model_info": new_model_info
                }
            }
        except Exception as e:
            logger.error(f"Error training model on data {data_path}: {str(e)}")
            return {"error": str(e)}
        
    def get_next_suffix(self, base_model_id):
        library = JSONHandler.read_json(DOWNLOADED_MODELS_PATH)
        i = 1
        while f"{base_model_id}_{i}" in library:
            i += 1
        return i

    def _handle_training_request(self, data):
        epochs = data['epochs']
        batch_size = data['batch_size']
        learning_rate = data['learning_rate']
        dataset_id = data['dataset_id']
        imgsz = data['imgsz']
        
        try:
            if epochs <= 0 or batch_size <= 0 or learning_rate <= 0:
                raise ValueError("Invalid training parameters")

            dataset_path = os.path.join(UPLOAD_DATASET_DIR, dataset_id)
            if not os.path.exists(dataset_path):
                raise FileNotFoundError("Dataset not found")

            yaml_path = os.path.join(dataset_path, f"{dataset_id}.yaml")
            if not os.path.exists(yaml_path):
                raise FileNotFoundError("YAML configuration file not found")

            train_txt_path = os.path.abspath(os.path.join(dataset_path, 'train.txt'))
            val_txt_path = os.path.abspath(os.path.join(dataset_path, 'val.txt'))

            # Log paths and YAML contents
            logger.debug(f"YAML Path: {yaml_path}")
            with open(yaml_path, 'r') as f:
                yaml_contents = f.read()
            logger.debug(f"YAML Contents: {yaml_contents}")
            
            # Log existence of train.txt and val.txt using absolute paths
            logger.debug(f"Checking paths: train.txt -> {train_txt_path}, val.txt -> {val_txt_path}")
            
            if not verify_file(train_txt_path) or not verify_file(val_txt_path):
                raise ValueError("train.txt or val.txt validation failed")

            # Log the current working directory
            current_working_dir = os.getcwd()
            logger.debug(f"Current working directory: {current_working_dir}")

            # Print directory listing
            dir_listing = os.listdir(dataset_path)
            logger.debug(f"Directory listing for {dataset_path}: {dir_listing}")

            training_params = {
                "data": yaml_path,
                "epochs": epochs,
                "batch_size": batch_size,
                "learning_rate": learning_rate,
                "imgsz": imgsz
            }
            return training_params
        except Exception as e:
            logger.error(f"Error during training: {str(e)}")
            raise