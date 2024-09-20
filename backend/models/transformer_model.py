import os
import torch
import transformers
import logging
import json
import shutil

from accelerate import Accelerator
from PIL import Image

from backend.core.config import ROOT_DIR
from backend.utils.helpers import get_next_suffix, execute_script
from backend.utils.process_audio_out import process_audio_output
from backend.utils.process_vis_out import process_vision_output
from .base_model import BaseModel
from backend.data_utils.speaker_embedding_manager import SpeakerEmbeddingManager
from backend.utils.process_vis_out import _ensure_json_serializable
from backend.core.exceptions import ModelError
from backend.utils.dataset_utility import DatasetManagement
from backend.controlers.runtime_control import RuntimeControl

logger = logging.getLogger(__name__)

class TransformerModel(BaseModel):
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.pipeline_args = {}
        self.pipeline = None
        self.config = None
        self.device = None
        self.model_dir = None
        self.languages = {}
        self.accelerator = None
        self.model_instance_data = []
        self.is_trained = False
        self.dataset_management = None

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
                raise ModelError(f"Auth token required for model {model_id} but not provided")

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
                _obj = class_.from_pretrained(
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
        except ModelError as e:
            logger.error(f"Transformer Model, error downloading model {model_id}: {str(e)}")
            raise ModelError(f"error downloading model {model_id}: \n\n{str(e)}")
        except Exception as e:
            logger.error(f"Transformer Model, unexpected error downloading model {model_id}: {str(e)}")
            raise ModelError(f"unexpected error downloading model {model_id}: \n\n{str(e)}")
    
    def load(self, device: torch.device, model_info: dict):
        try:
            # Get the model directory
            model_dir = model_info['dir']
            if not os.path.exists(model_dir):
                raise FileNotFoundError(f"Model directory not found: {model_dir}")
            
            self.model_dir = model_dir
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
            
            # for trained mode;s, they have to be loaded differently
            self.is_trained = model_info.get("is_trained", False)
            
            # Initialize RAG components if enabled
            rag_settings = self.config.get("rag_settings", {})
            if rag_settings.get("use_dataset"):
                embedding_model = rag_settings.get("embedding_model", "all-MiniLM-L6-v2")
                self.dataset_management = DatasetManagement(model_name=embedding_model)
            
            # for loop to load all the required classes
            for class_type, class_name in required_classes.items():
                
                print("class_type: ", class_type)
                print("class_name: ", class_name)
                
                # dynamically import the class from transformers library
                class_ = getattr(transformers, class_name)
                
                # read the corresponding config for the class_type
                obj_config = self.config.get(f'{class_type}_config', {})
                
                if not self.is_trained:
                    # load the class object from the local model directory
                    obj = class_.from_pretrained(
                        self.model_id,
                        cache_dir=model_dir,
                        local_files_only=True,
                        **obj_config
                    )
                else:
                    obj = class_.from_pretrained(
                        self.model_dir,
                        local_files_only=True,
                        **obj_config
                    ) 

                # store the class object in the pipeline_args dictionary
                self.pipeline_args.update({class_type: obj})
                logger.info(f"succesfully loaded {class_type} from {model_dir}")

            self.pipeline_args["model"] = self.accelerator.prepare(self.pipeline_args["model"])
            
            # for those translation models that require pipeline task = "translation_XX_to_YY"
            # it will set the pipeline task to be "translation_{src}_to_{tgt}"
            if translation_config and translation_config.get('src_lang') and translation_config.get('tgt_lang'):
                pipeline_tag = self._get_translation_pipeline_task(translation_config.get('src_lang'), translation_config.get('tgt_lang'))
            
            self.pipeline = self._construct_pipeline(pipeline_tag)
            logger.info(f"Pipeline created successfully for task: {pipeline_tag}")
            logger.info(f"Model loaded successfully from {model_dir}")
            
            if self.pipeline.task in ['text-generation'] :
                if self.config.get("system_prompt"):
                    self.model_instance_data.append(self.config.get("system_prompt"))
                if self.config.get("example_conversation"):
                    self.model_instance_data += self.config.get("example_conversation")
        except Exception as e:
            logger.error(f"Error loading model from {model_info['dir']}: {str(e)}")
            raise e # Re-raise the exception to be caught by the caller
    
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
                    speaker_embedding = SpeakerEmbeddingManager.get_speaker_embedding(speaker_embedding_config, default_speaker_embedding_config)
                    pipeline_config.update({"forward_params": {"speaker_embeddings": speaker_embedding}})
                output = self.pipeline(data["payload"], **pipeline_config)
                output = process_audio_output(output)
            # For some translation models, if the api request contains translation_config, it will set the pipeline task to be "translation_{src}_to_{tgt}"
            # the new pipeline is single-use only
            elif data.get("translation_config"):
                src_lang = data["translation_config"].get("src_lang")
                tgt_lang = data["translation_config"].get("tgt_lang")
                # taget language is used by google/madlad400-10b-mt which requires a token as sentence prefix
                target_language_token = data["translation_config"].get("target_language")
                
                if src_lang is not None and tgt_lang is not None:
                    pipeline_tag = self._get_translation_pipeline_task(data["translation_config"]["src_lang"], data["translation_config"]["tgt_lang"])
                    temp_pipeline = self._construct_pipeline(pipeline_tag)
                    output = temp_pipeline(data["payload"], **pipeline_config)
                elif target_language_token is not None:
                    data = self._append_language_token(data)
                    output = self.pipeline(data["payload"], **pipeline_config)
                    
            elif self.config.get("translation_config") and self.config.get("translation_config").get("target_language"):
                target_language_token = f"<2{self.config.get('translation_config').get('target_language')}>"
                if isinstance(data["payload"], str):
                    data["payload"] = target_language_token + data["payload"]
                elif isinstance(data["payload"], list):
                    data["payload"] = [target_language_token + c for c in data["payload"]]
                output = self.pipeline(data["payload"], **pipeline_config)
            # For other tasks, the pipeline will be called with the payload
            
            elif self.pipeline.task in ['text-generation']:
                rag_settings = self.config.get("rag_settings", {})
                full_prompt = ""
                
                if rag_settings.get("use_dataset"):
                    logger.info("RAG is enabled, attempting to find relevant entries")
                    dataset_name = rag_settings.get("dataset_name")
                    similarity_threshold = rag_settings.get("similarity_threshold", 0.5)
                    use_chunking = rag_settings.get("use_chunking", False)
                    
                    if dataset_name:
                        logger.info(f"Using dataset: {dataset_name}")
                        relevant_entries = self.dataset_management.find_relevant_entries(
                            data["payload"],
                            dataset_name,
                            use_chunking=use_chunking,
                            similarity_threshold=similarity_threshold
                        )
                        if relevant_entries:
                            logger.info(f"Found {len(relevant_entries)} relevant entries")
                            full_prompt += "Relevant information:\n"
                            for entry in relevant_entries:
                                full_prompt += f"- {entry}\n"
                            full_prompt += "\n"
                        else:
                            logger.info("No relevant entries found")
                    else:
                        logger.warning("RAG is enabled but no dataset name provided")
                
                full_prompt += data["payload"]
                
                user_prompt = self.config.get("user_prompt", {}).copy()
                for key in user_prompt:
                    if user_prompt.get(key) == "[USER]":
                        user_prompt[key] = full_prompt
                
                if self.config.get("chat_history"):
                    self.model_instance_data.append(user_prompt)
                    output = self.pipeline(self.model_instance_data, **pipeline_config)
                    self.model_instance_data.append(output[0]["generated_text"][-1])
                    output = output[0]["generated_text"][-1].get("content")
                else:
                    output = self.pipeline(self.model_instance_data + [user_prompt], **pipeline_config)
                    output = output[0]["generated_text"][-1].get("content")
            else:
                # call the pipeline with the payload and any extra pipeline_config provided in the request
                output = self.pipeline(data["payload"], **pipeline_config)
            
            return output
        except KeyError as e:
            logger.error(f"{str(e)} has to be provided in the request data")
            raise KeyError(f"{str(e)} has to be provided in the request data")
        except Exception as e:
            logger.error(f"Error during inference: {str(e)}")
            raise ModelError(f"Error during inference: {str(e)}")

    def train(self, data: dict):
        dataset_path = data.get("data")
        model_info = data.get("model_info")
        hardware_preference = str(data.get("hardware_preference"))
        
        tokenizer_args = data.get("tokenizer_args", {})
        training_args = data.get("training_args", {})

        if not dataset_path:
            return {"error": "Dataset path not provided in the request data"}

        suffix = get_next_suffix(self.model_id)
        model_dir = model_info.get("dir")
        trained_model_dir = os.path.join(f"{model_dir}_{suffix}")
        
        script_args = {
            "model_id": self.model_id,
            "hardware_preference": hardware_preference,
            "model_info": model_info,
            "dataset_path": dataset_path,
            "tokenizer_args": tokenizer_args,
            "training_args": training_args,
            "trained_model_dir": trained_model_dir
        }
        logger.info(script_args)
        script_path = os.path.join(ROOT_DIR, "backend", "utils", "train_transformer.py")
        
        with open("data/temp_train_args.json", 'w') as f:
                json.dump(script_args, f, indent=4)

        execute_script(script_path) 

        temp_output_dir = os.path.join(ROOT_DIR, "temp")
        
        # If the training script was terminated early due to an error, 
        # the temp_output_dir will not be deleted and the trained model will not be saved
        # In such cases, assess the temp_output_dir and return an error message
        if os.path.exists(temp_output_dir):
            shutil.rmtree(temp_output_dir, ignore_errors=True)
            raise ModelError("Training failed, please check the training datasets to ensure they are correctly formatted")
        
        new_model_info = {
            "model_id": f"{self.model_id}_{suffix}",
            "base_model": f"{self.model_id}_{suffix}",
            "dir": trained_model_dir,
            "model_desc": f"Fine-tuned {self.model_id} model",
            "is_customised": False,
            "is_trained": True
        }

        return {
            "message": "Training completed successfully",
            "data": {
                "trained_model_path": trained_model_dir,
                "new_model_info": new_model_info
            }
        }
    
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
        return lang in self.languages.values()
    
    def _append_language_token(self, data: dict):
        target_language_token = None
        
        # first it will check if the translation_config is provided in the request data
        if data.get("translation_config"):
            target_language_token = data["translation_config"].get("target_language")
        # if not, it will check if the model config contains translation_config
        elif self.config.get("translation_config") and self.config["translation_config"].get("target_language"):
            target_language_token = self.config["translation_config"].get("target_language")
        
        # if target_language_token is provided, it will append the token to the payload
        if target_language_token:
            target_language_token = f"<2{target_language_token}>"
            if isinstance(data["payload"], str):
                data["payload"] = target_language_token + data["payload"]
            elif isinstance(data["payload"], list):
                data["payload"] = [target_language_token + sentence for sentence in data["payload"]]
        
        return data
