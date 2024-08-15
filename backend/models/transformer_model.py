import os
import torch
import transformers

from backend.utils.process_audio_out import process_audio_output
from backend.utils.process_vis_out import process_vision_output
from .base_model import BaseModel
import logging
from huggingface_hub import snapshot_download
from backend.data_utils.json_handler import JSONHandler
from backend.core.config import DOWNLOADED_MODELS_PATH
from backend.data_utils.speaker_embedding_generator import get_speaker_embedding
import importlib
from accelerate import Accelerator
from PIL import Image
from backend.utils.process_vis_out import _ensure_json_serializable

logger = logging.getLogger(__name__)

class TransformerModel(BaseModel):
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.pipeline_args = {}
        self.pipeline = None
        self.config = None
        self.device = None
        self.languages = {}
        self.accelerator = None
        self.model_instance_data = []

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
                
                if auth_token:
                    obj_config['use_auth_token'] = auth_token
                
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
            #Get the model directory
            model_dir = model_info['dir']
            if not os.path.exists(model_dir):
                raise FileNotFoundError(f"Model directory not found: {model_dir}")
            
            logger.info(f"Loading model from {model_dir}")
            logger.info(f"Model info: {model_info}")
            
            # Getting the model config and loading required variables for model loading
            self.config = model_info.get('config', {})
            model_config = self.config.get('model_config', {})
            requirements = model_info.get('requirements', {})
            required_classes = requirements.get('required_classes', {})
            pipeline_tag = model_info.get('pipeline_tag')
            translation_config = self.config.get('translation_config', {})
            
            # getting the device configurations and setting up the accelerator accordingly
            if model_info.get('device_config', {}):
                USE_CPU = model_info.get('device_config', {}).get('device') == "cpu"
            else:
                USE_CPU = device == "cpu"
            self.accelerator = Accelerator(cpu=USE_CPU)
            
            # getting the quantization configurations and setting up the model config accordingly
            if self.config.get("quantization_config", {}):
                current_mode = self.config["quantization_config"].get("current_mode")
                if current_mode != "bfloat16" and self.config["quantization_config"]:
                    bnb_config = transformers.BitsAndBytesConfig(**self.config["quantization_config_options"].get(current_mode,{}))
                    model_config["quantization_config"] = bnb_config
                else:
                    model_config["torch_dtype"] = torch.bfloat16
            
            
            
            
            if self.config.get("device_config", {}).get("device"):
                self.device = self.config["device_config"]["device"]
            else:
                self.device = device
            logger.info(f"Using device: {self.device}")
            
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
                logger.info(f"succesfully loaded {class_type} from {model_dir}")


            self.pipeline_args["model"] = self.accelerator.prepare(self.pipeline_args["model"])
            
            # for those translation models that require pipeline task = "translation_XX_to_YY"
            # it will set the pipeline task to be "translation_{src}_to_{tgt}"
            if translation_config:
                pipeline_tag = self._get_translation_pipeline_task(translation_config.get('src_lang'), translation_config.get('tgt_lang'))
            
            self.pipeline = self._construct_pipeline(pipeline_tag)
            logger.info(f"Pipeline created successfully for task: {pipeline_tag}")
            logger.info(f"Model loaded successfully from {model_dir}")
            
            if self.pipeline.task in ['text-generation'] and self.config.get("system_prompt"):
                self.model_instance_data.append(self.config.get("system_prompt"))
                if self.config.get("example_conversation"):
                    self.model_instance_data += self.config.get("example_conversation")
        except Exception as e:
            logger.error(f"Error loading model from {model_dir}: {str(e)}")
            raise  # Re-raise the exception to be caught by the caller
    
    def inference(self, data: dict):
        try:
            # if the api request contains pipeline_config, it will be passed to the pipeline for single-use only
            pipeline_config = data.get("pipeline_config", {})
            visualize = data.get("visualize", False)
            print("data payload: ", data["payload"])

            # for zero shot tasks, both image and text must be passed
            if self.pipeline.task in ['zero-shot-object-detection']:
                image_path = data["payload"].get("image")
                text = data["payload"].get("text")
                if not image_path or not text:
                    raise KeyError("'image' and 'text' must be provided in the request data for zero-shot tasks")
                try:
                    print(f"Opening image from path: {image_path}")
                    with Image.open(image_path) as image:
                        print(f"Image opened successfully: {image}")
                        print(f"Text: {text}")
                        output = self.pipeline(image=image, candidate_labels=text, **pipeline_config)
                        print(f"Pipeline output: {output}")
                        if output is None:
                            raise ValueError("Pipeline output is None")
                        

                except FileNotFoundError:
                    raise FileNotFoundError(f"Image file not found: {image_path}")
                except Exception as e:
                    raise e
            
            
            elif self.pipeline.task in ['image-segmentation', 'object-detection', 'instance-segmentation']:
                with Image.open(data["payload"]) as image:
                    output = self.pipeline(data["payload"], **pipeline_config)
                    output = _ensure_json_serializable(output)
                    
            
            # For text-to-speech tasks, if speaker_embedding_config exists in self.config, the model will need speaker embedding to generate speech
            elif self.pipeline.task in ["text-to-audio", "text-to-speech"]:
                if self.config.get("speaker_embedding_config"):
                    print("successfully got speaker embedding config")
                    # get the speaker embedding config from the request data and the default speaker embedding config from the model config
                    speaker_embedding_config = data.get("speaker_embedding_config")
                    default_speaker_embedding_config = self.config.get("speaker_embedding_config")
                    # get the speaker embedding tensor, if speaker_embedding_config is not provided, it will use the default speaker embedding config
                    speaker_embedding = get_speaker_embedding(speaker_embedding_config, default_speaker_embedding_config)
                    pipeline_config.update({"forward_params": {"speaker_embeddings": speaker_embedding}})
                output = self.pipeline(data["payload"], **pipeline_config)
                output = process_audio_output(output)
            # For some translation models, if the api request contains translation_config, it will set the pipeline task to be "translation_{src}_to_{tgt}"
            # the new pipeline is single-use only
            elif data.get("translation_config"):
                pipeline_tag = self._get_translation_pipeline_task(data["translation_config"]["src_lang"], data["translation_config"]["tgt_lang"])
                temp_pipeline = self._construct_pipeline(pipeline_tag)
                output = temp_pipeline(data["payload"], **pipeline_config)
            
            # For other tasks, the pipeline will be called with the payload
            
            elif self.pipeline.task in ['text-generation'] and self.config.get("system_prompt"):
                
                user_prompt = self.config.get("user_prompt").copy()
                for key in user_prompt:
                    if user_prompt.get(key) == "[USER]":
                        user_prompt.update({key: data["payload"]})
                        print("user_prompt: ", user_prompt)
                
                if self.config.get("chat_history"):
                    self.model_instance_data.append(user_prompt)
                    output = self.pipeline(self.model_instance_data, **pipeline_config)
                    self.model_instance_data.append(output[0]["generated_text"][-1])
                    output = output[0]["generated_text"][-1].get("content")
                    print("model_instance_data: ", self.model_instance_data)
                else:
                    output = self.pipeline(self.model_instance_data + [user_prompt], **pipeline_config)
                    output = output[0]["generated_text"][-1].get("content")
            else:
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
        pipe = transformers.pipeline(task=pipeline_tag, **self.pipeline_args, **pipeline_config)
        
        return self.accelerator.prepare(pipe)
    
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
        