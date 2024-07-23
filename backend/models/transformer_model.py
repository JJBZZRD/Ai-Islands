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
        self.model = None
        self.tokenizer = None
        self.processor = None
        self.pipeline = None
        self.config = None
        self.device = None
        self.languages = None

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
            model_config = config.get('model_config', {})
            tokenizer_config = config.get('tokenizer_config', {})
            processor_config = config.get('processor_config', {})

            for class_type, class_name in required_classes.items():
                if class_type == "model":
                    module = importlib.import_module('transformers')
                    ModelClass = getattr(module, class_name)
                    ModelClass.from_pretrained(
                        model_id, 
                        cache_dir=model_dir, 
                        force_download=True, 
                        use_auth_token=auth_token if requires_auth else None,
                        **model_config
                    )
                elif class_type == "tokenizer":
                    transformers.AutoTokenizer.from_pretrained(
                        model_id, 
                        cache_dir=model_dir, 
                        force_download=True, 
                        use_auth_token=auth_token if requires_auth else None,
                        **tokenizer_config
                    )
                elif class_type == "processor":
                    ProcessorClass = getattr(transformers, class_name)
                    ProcessorClass.from_pretrained(
                        model_id, 
                        cache_dir=model_dir, 
                        force_download=True, 
                        use_auth_token=auth_token if requires_auth else None,
                        **processor_config
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
            model_config = self.config.get('model_config', {})
            tokenizer_config = self.config.get('tokenizer_config', {})
            processor_config = self.config.get('processor_config', {})
            translation_config = self.config.get('translation_config', {})
            
            if self.config.get("device_config").get("device"):
                self.device = self.config["device_config"]["device"]
            else:
                self.device = device
            print("using device: ", self.device)
            # for translation models to check if the languages are supported
            self.languages = model_info.get('languages', {})
            
            for class_type, class_name in required_classes.items():
                class_ = getattr(transformers, class_name)
                
                if class_type == "model":
                    logger.info(f"Loading model with {class_name}")
                    self.model = class_.from_pretrained(
                        self.model_id,
                        cache_dir=model_dir,
                        local_files_only=True,
                        **model_config
                    )
                    if self.model is None:
                        raise ValueError(f"Failed to load model: {self.model_id}")
                elif class_type == "tokenizer":
                    logger.info(f"Loading tokenizer with {class_name}")
                    self.tokenizer = class_.from_pretrained(
                        self.model_id,
                        cache_dir=model_dir,
                        local_files_only=True,
                        **tokenizer_config
                    )
                    if self.tokenizer is None:
                        raise ValueError(f"Failed to load tokenizer: {self.model_id}")
                elif class_type == "processor":
                    logger.info(f"Loading processor with {class_name}")
                    self.processor = class_.from_pretrained(
                        self.model_id,
                        cache_dir=model_dir,
                        local_files_only=True,
                        **processor_config
                    )
                    if self.processor is None:
                        raise ValueError(f"Failed to load processor: {self.model_id}")

            # for those translation models that require pipeline task = "translation_XX_to_YY"
            # it will set the pipeline task to be "translation_{src}_to_{tgt}"
            if translation_config:
                pipeline_tag = self._get_translation_pipeline_task(translation_config.get('src_lang'), translation_config.get('tgt_lang'))
            
            self.pipeline = self._construct_pipeline(pipeline_tag)
            logger.info(f"Pipeline created successfully for task: {pipeline_tag}")
            logger.info(f"Model loaded successfully from {model_dir}")
            if self.model is not None:
                logger.info(f"Model device: {self.model.device}")
                logger.info(f"Model dtype: {self.model.dtype}")
            else:
                logger.warning("Model is None, unable to log device and dtype information")
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
        pipeline_args = {
            "task": pipeline_tag,
            "model": self.model,
            "tokenizer": self.tokenizer,
            "device": self.device
        }
        if self.processor:
            pipeline_args["processor"] = self.processor
        pipeline_config = self.config.get('pipeline_config', {})
        
        pipe = transformers.pipeline(**pipeline_args, **pipeline_config)
        
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
        