"""from ultralytics import YOLO
import os

class UltralyticsModel:
    def __init__(self):
        self.model = None
        self.model_path = None
    
    def download(self, model_id: str):
        try:
            self.model = YOLO(model_id) 
            model_file_name = f'{model_id}.pt' if not model_id.endswith('.pt') else model_id
            self.model_path = os.path.join(os.getcwd(), 'venv', 'models', 'ultralytics', model_file_name)
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            print(f"Saving model to: {self.model_path}")

            # Save the model to the specified path
            self.model.save(self.model_path)
            print(f"Model {model_id} downloaded and saved to {self.model_path}")
        except Exception as e:
            print(f"Error downloading model {model_id}: {str(e)}")
    
    def load(self, model_path: str):
        try:
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found: {model_path}")
            
            self.model = YOLO(model_path)
            print(f"Model loaded from {model_path}")
        except Exception as e:
            print(f"Error loading model from {model_path}: {str(e)}")
            
            
    def predict(self, image_path: str):
        try: 
            if self.model is None:
                raise ValueError("Model is not loaded")
            
            results = self.model.predict(image_path)
            return results
        except Exception as e:
            print(f"Error predicting image {image_path}: {str(e)}")
    
    def train(self, data_path: str, epochs: int = 20):
        try:
            if self.model is None:
                raise ValueError("Model is not loaded")
            
            self.model.train(data=data_path, epochs=epochs)
            print(f"Model trained on {data_path} for {epochs} epochs")
        except Exception as e:
            print(f"Error training model on data {data_path}: {str(e)}")"""
            
import os
from ultralytics import YOLO

class UltralyticsModel:
    def __init__(self):
        self.model = None
    
    def download(self, model_id: str):
        try:
            self.model = YOLO(model_id) 
            model_file_name = f'{model_id}.pt' if not model_id.endswith('.pt') else model_id
            self.model_path = os.path.join(os.getcwd(), 'venv', 'models', 'ultralytics', model_file_name)
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            print(f"Saving model to: {self.model_path}")

            # Save the model to the specified path
            self.model.save(self.model_path)
            print(f"Model {model_id} downloaded and saved to {self.model_path}")
        except Exception as e:
            print(f"Error downloading model {model_id}: {str(e)}")
    
    def load(self, model_path: str):
        try:
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found: {model_path}")
            
            self.model = YOLO(model_path)
            print(f"Model loaded from {model_path}")
        except Exception as e:
            print(f"Error loading model from {model_path}: {str(e)}")
            
    def predict(self, image_path: str):
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
            return None
            
    def train(self, data_path: str, epochs: int = 20):
        try:
            if self.model is None:
                raise ValueError("Model is not loaded")
            
            self.model.train(data=data_path, epochs=epochs)
            print(f"Model trained on {data_path} for {epochs} epochs")
        except Exception as e:
            print(f"Error training model on data {data_path}: {str(e)}")
