import os
import torch
import transformers
from .base_model import BaseModel
import logging
from huggingface_hub import snapshot_download
from backend.data_utils.json_handler import JSONHandler
from backend.core.config import DOWNLOADED_MODELS_PATH
import importlib
from accelerate import Accelerator

logger = logging.getLogger(__name__)

class TransformerModel(BaseModel):
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.pipeline_args = {}
        self.pipeline = None
        self.config = None
        self.device = None
        self.languages = {}

    @staticmethod
    def download(model_id: str, model_info: dict):
        try:
            model_dir = os.path.join('data', 'downloads', 'transformers', model_id)
            if not os.path.exists(model_dir):
                os.makedirs(model_dir, exist_ok=True)
            
            requirements = model_info.get('requirements', {})
            required_classes = requirements.get('required_classes', {})
            requires_auth = requirements.get('requires_auth', False)
            auth_token = model_info.get('auth_token', None)
            
            if requires_auth and not auth_token:
                logger.error(f"Auth token required for model {model_id} but not provided")
                return None

            config = model_info.get('config', {})

            # for loop to download all the required classes
            # exmaple: class_type = "model", class_name = "AutoModelForSeq2SeqLM"
            for class_type, class_name in required_classes.items():
            
                print("class_type: ", class_type)
                print("class_name: ", class_name)
                
                # dynamically import the class from transformers library, ex: AutoModelForSeq2SeqLM
                class_ = getattr(transformers, class_name)
                
                # read the corresponding config for the class_type
                # ex: obj_config = model_config/pipeline_config
                obj_config = config.get(f'{class_type}_config', {})
                
                # download the class object from huggingface transformers library
                obj = class_.from_pretrained(
                    model_id,
                    cache_dir=model_dir,
                    **obj_config
                )
            
            if requires_auth:
                config['auth_token'] = auth_token

            model_info.update({
                "base_model": model_id,
                "dir": model_dir,
                "is_customised": False,
                "config": config
            })
            return model_info
        except Exception as e:
            logger.error(f"Error downloading model {model_id}: {str(e)}")
            return None

    def load(self, device: torch.device, model_info: dict):
        try:
            model_dir = model_info['dir']
            if not os.path.exists(model_dir):
                raise FileNotFoundError(f"Model directory not found: {model_dir}")
            
            logger.info(f"Loading model from {model_dir}")
            logger.info(f"Model info: {model_info}")
            
            requirements = model_info.get('requirements', {})
            required_classes = requirements.get('required_classes', {})
            
            pipeline_tag = model_info.get('pipeline_tag')
            
            self.config = model_info.get('config', {})
            translation_config = self.config.get('translation_config', {})
            
            
            if self.config.get("device_config", {}).get("device"):
                self.device = self.config["device_config"]["device"]
            else:
                self.device = device
            print("using device: ", self.device)
            
            # for translation models to check if the languages are supported
            self.languages = model_info.get('languages', {})
            
            # for loop to load all the required classes
            for class_type, class_name in required_classes.items():
                
                print("class_type: ", class_type)
                print("class_name: ", class_name)
                
                # dynamically import the class from transformers library
                class_ = getattr(transformers, class_name)
                
                # read the corresponding config for the class_type
                obj_config = self.config.get(f'{class_type}_config', {})
                # load the class object from the local model directory
                obj = class_.from_pretrained(
                    self.model_id,
                    cache_dir=model_dir,
                    local_files_only=True,
                    **obj_config
                )
                
                # store the class object in the pipeline_args dictionary
                self.pipeline_args.update({class_type: obj})
                logger.info(f"created {class_type} object: {obj}")

            # for those translation models that require pipeline task = "translation_XX_to_YY"
            # it will set the pipeline task to be "translation_{src}_to_{tgt}"
            if translation_config:
                pipeline_tag = self._get_translation_pipeline_task(translation_config.get('src_lang'), translation_config.get('tgt_lang'))
            
            self.pipeline = self._construct_pipeline(pipeline_tag)
            logger.info(f"Pipeline created successfully for task: {pipeline_tag}")
            logger.info(f"Model loaded successfully from {model_dir}")
        except Exception as e:
            logger.error(f"Error loading model from {model_dir}: {str(e)}")
            raise  # Re-raise the exception to be caught by the caller
    
    def inference(self, data: dict):
        try:
            # if the api request contains translation_config, it will set the pipeline task to be "translation_{src}_to_{tgt}"
            if data.get("translation_config"):
                pipeline_tag = self._get_translation_pipeline_task(data["translation_config"]["src_lang"], data["translation_config"]["tgt_lang"])
                self.pipeline = self._construct_pipeline(pipeline_tag)
            
            pipeline_config = data.get("pipeline_config", {})
            
            print("data payload: ", data["payload"])
            # call the pipeline with the payload and any extra pipeline_config provided in the request
            output = self.pipeline(data["payload"], **pipeline_config)
            return output
        except KeyError as e:
            logger.error(f"{str(e)} has to be provided in the request data")
            return {"error": f"{str(e)} has to be provided in the request data"}
        except Exception as e:
            logger.error(f"Error during inference: {str(e)}")
            return {"error": str(e)}

    def configure(self, data: dict):
        pass

    def train(self, data_path: str, epochs: int = 3):
        logger.warning("Training method not implemented for TransformerModel")
    
    def _construct_pipeline(self, pipeline_tag: str):
        pipeline_config = self.config.get('pipeline_config', {})
        print("pipeline_args: ", self.pipeline_args)
        pipe = transformers.pipeline(task=pipeline_tag, device=self.device, **self.pipeline_args, **pipeline_config)
        accelerator = Accelerator()
        
        return accelerator.prepare(pipe)
    
    def _get_translation_pipeline_task(self, src: str, tgt: str):
        if self._is_languages_supported(src) and self._is_languages_supported(tgt):
            return f"translation_{src}_to_{tgt}"
        else:
            raise ValueError(f"Translation pipeline not available for {src} to {tgt}")
        
    def _is_languages_supported(self, lang: str):
        return lang in self.languages
        
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
        