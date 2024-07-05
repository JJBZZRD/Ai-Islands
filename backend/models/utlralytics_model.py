from ultralytics import YOLO
import os

class UltralyticsModel:
    def __init__(self):
        self.model = None
        self.model_path = None

    def download(self, model_id: str):
        # Assuming model_id is a valid YOLO model name or path
        try:
            # Download the model
            self.model = YOLO(model_id)
            
            # Save the model to a local path
            self.model_path = os.path.join('data', 'downloaded_models', f'{model_id}.pt')
            self.model.save(self.model_path)
            
            print(f"Model {model_id} downloaded and saved to {self.model_path}")
        except Exception as e:
            print(f"Error downloading model {model_id}: {str(e)}")

    def load(self, model_id: str):
        # Assuming model_id is the name of a locally saved model
        try:
            self.model_path = os.path.join('data', 'downloaded_models', f'{model_id}.pt')
            
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model file not found: {self.model_path}")
            
            self.model = YOLO(self.model_path)
            print(f"Model {model_id} loaded from {self.model_path}")
        except Exception as e:
            print(f"Error loading model {model_id}: {str(e)}")

    def predict(self, image_path: str):
        if self.model is None:
            raise ValueError("Model not loaded. Please load a model first.")
        
        try:
            results = self.model(image_path)
            return results
        except Exception as e:
            print(f"Error during prediction: {str(e)}")
            return None

    def train(self, data_path: str, epochs: int = 100):
        if self.model is None:
            raise ValueError("Model not loaded. Please load a model first.")
        
        try:
            results = self.model.train(data=data_path, epochs=epochs)
            return results
        except Exception as e:
            print(f"Error during training: {str(e)}")
            return None
