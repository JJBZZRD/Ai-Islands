import os
import torch
import transformers
from .base_model import BaseModel
import logging
from huggingface_hub import snapshot_download
from backend.data_utils.json_handler import JSONHandler
from backend.core.config import DOWNLOADED_MODELS_PATH
import importlib

logger = logging.getLogger(__name__)

class TransformerModel(BaseModel):
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.model = None
        self.tokenizer = None
        self.processor = None
        self.pipeline = None

    @staticmethod
    def download(model_id: str, model_info: dict):
        try:
            model_dir = os.path.join('data', 'downloads', 'transformers', model_id)
            if not os.path.exists(model_dir):
                os.makedirs(model_dir, exist_ok=True)
            
            required_classes = model_info.get('required_classes', {})
            
            for class_type, class_name in required_classes.items():
                if class_type == "model":
                    # Dynamically import the correct model class
                    module = importlib.import_module('transformers')
                    ModelClass = getattr(module, class_name)
                    ModelClass.from_pretrained(model_id, cache_dir=model_dir, force_download=True)
                elif class_type == "tokenizer":
                    transformers.AutoTokenizer.from_pretrained(model_id, cache_dir=model_dir, force_download=True)
                elif class_type == "processor":
                    ProcessorClass = getattr(transformers, class_name)
                    ProcessorClass.from_pretrained(model_id, cache_dir=model_dir, force_download=True)
            
            model_info.update({
                "base_model": model_id,
                "dir": model_dir,
                "is_customised": False,
                "config":{}
            })
            return model_info
        except Exception as e:
            logger.error(f"Error downloading model {model_id}: {str(e)}")
            return None

    def load(self, model_dir: str, device: torch.device, required_classes: dict, pipeline_tag: str = None):
        try:
            if not os.path.exists(model_dir):
                raise FileNotFoundError(f"Model directory not found: {model_dir}")
            
            logger.info(f"Loading model from {model_dir}")
            logger.info(f"Required classes: {required_classes}")
            
            for class_type, class_name in required_classes.items():
                # Dynamically load the class from the transformers library
                class_ = getattr(transformers, class_name)
                
                if class_type == "model":
                    logger.info(f"Loading model with {class_name}")
                    self.model = class_.from_pretrained(self.model_id, cache_dir=model_dir, local_files_only=True)
                elif class_type == "tokenizer":
                    logger.info(f"Loading tokenizer with {class_name}")
                    self.tokenizer = class_.from_pretrained(self.model_id, cache_dir=model_dir, local_files_only=True)
                elif class_type == "processor":
                    logger.info(f"Loading processor with {class_name}")
                    self.processor = class_.from_pretrained(self.model_id, cache_dir=model_dir, local_files_only=True)
                # Add additional elif statements for other class types as needed
            
            if pipeline_tag:
                logger.info(f"Creating pipeline with tag: {pipeline_tag}")
                self.pipeline = transformers.pipeline(
                    task=pipeline_tag,
                    model=self.model,
                    tokenizer=self.tokenizer,
                    device=device
                )
            
            logger.info(f"Model loaded successfully from {model_dir}")
        except Exception as e:
            logger.error(f"Error loading model from {model_dir}: {str(e)}")
            raise  # Re-raise the exception to be caught by the caller
    
    # This is a method to test model predict
    # This method needs further modification to work with different types of models
    def inference(self, data: dict):
        try:
            print(data["payload"])
            print(self.pipeline)
            output = self.pipeline(data["payload"])
            print("output")
            print(output)
            return output
        except Exception as e:
            logger.error(f"Error during inference: {str(e)}")
            return {"error": str(e)}

    def train(self, data_path: str, epochs: int = 3):
        logger.warning("Training method not implemented for TransformerModel")
        
    # def process_request(self, request_payload: dict):
    #     if self.pipeline:
    #         if "text" in request_payload:
    #             return self.pipeline(request_payload["text"])
    #         elif "image" in request_payload:
    #             return self.pipeline(request_payload["image"])
    #     else:
    #         # Fallback to existing methods if pipeline is not available
    #         if "prompt" in request_payload:
    #             return self.generate(request_payload["prompt"])
    #         elif "image" in request_payload:
    #             return self.process_image(request_payload["image"])
        
    #     return {"error": "Invalid request payload or unsupported operation"}

    # def generate(self, prompt: str, max_length: int = 50):
    #     try:
    #         if self.model is None or self.tokenizer is None:
    #             raise ValueError("Model or tokenizer not loaded. Please load a model first.")
            
    #         inputs = self.tokenizer(prompt, return_tensors="pt")
    #         outputs = self.model.generate(**inputs, max_length=max_length)
    #         generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
    #         return {"generated_text": generated_text}
    #     except Exception as e:
    #         logger.error(f"Error during text generation: {str(e)}")
    #         return {"error": str(e)}

    # def process_image(self, image_path: str):
    #     try:
    #         if self.model is None or self.processor is None:
    #             raise ValueError("Model or processor not loaded. Please load a model first.")
            
    #         # Implement image processing logic here
    #         # This is a placeholder and should be adapted based on the specific model's requirements
    #         return {"message": "Image processing not implemented for this model"}
    #     except Exception as e:
    #         logger.error(f"Error during image processing: {str(e)}")
    #         return {"error": str(e)}
        