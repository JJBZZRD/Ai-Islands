import os
import torch
import transformers
import evaluate
import shutil
import numpy as np

from transformers import DataCollatorWithPadding, Trainer, TrainingArguments
from backend.utils.process_audio_out import process_audio_output
from backend.utils.process_vis_out import process_vision_output
from .base_model import BaseModel
from backend.utils.helpers import get_next_suffix
import logging
from backend.core.config import ROOT_DIR
from backend.data_utils.speaker_embedding_generator import get_speaker_embedding
from accelerate import Accelerator
from PIL import Image
from datasets import load_dataset


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
            model_dir = model_info['dir']
            if not os.path.exists(model_dir):
                raise FileNotFoundError(f"Model directory not found: {model_dir}")
            
            self.model_dir = model_dir
            
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
            # if the api request contains pipeline_config, it will be passed to the pipeline for single-use only
            pipeline_config = data.get("pipeline_config", {})
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
            
            # For image-based tasks, we need to pass the original image, output needs to be processde again into serialised format to avoid error
            elif self.pipeline.task in ['image-segmentation', 'object-detection', 'instance-segmentation']:
                with Image.open(data["payload"]) as image:
                    output = self.pipeline(data["payload"], **pipeline_config)
                    output = process_vision_output(image, output, self.pipeline.task)
            
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

    def train(self, data: dict):
        dataset_path = data.get("data")
        tokenizer_args = data.get("tokenizer_args", {})
        training_args = data.get("training_args", {})
        
        if not dataset_path:
            return {"error": "Dataset path not provided in the request data"}
        
        dataset = load_dataset('csv', data_files=dataset_path)
        dataset = dataset["train"]
        
        model = self.pipeline_args.get("model")
        tokenizer = self.pipeline_args.get("tokenizer")
        
        def _preprocess_function(data_entry):
            tokenizer_params = {
                "padding": "max_length",
                "truncation": True,
                "max_length": 128
            }
            tokenizer_params.update(tokenizer_args)
            return tokenizer(data_entry['text'], **tokenizer_params)
        
        dataset = dataset.map(_preprocess_function)
        
        dataset = dataset.train_test_split(test_size=0.2)

        data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

        accuracy = evaluate.load("accuracy")

        def compute_metrics(eval_pred):
            predictions, labels = eval_pred
            predictions = np.argmax(predictions, axis=1)
            return accuracy.compute(predictions=predictions, references=labels)
        
        suffix = get_next_suffix(self.model_id)
        trained_model_dir = os.path.join(f"{self.model_dir}_{suffix}")
        temp_output_dir = os.path.join(ROOT_DIR, "temp")
        
        os.makedirs(temp_output_dir, exist_ok=True)
        
        default_training_args = {
            "output_dir": temp_output_dir,
            "save_only_model": True,
            "learning_rate": 1e-7,
            "num_train_epochs": 5,
            "weight_decay": 0.01,
            "eval_strategy": "epoch",
            "save_strategy": "epoch",
            "save_total_limit": 3,
            "load_best_model_at_end": True
        }
        
        default_training_args.update(training_args)
        
        training_args = TrainingArguments(
            **default_training_args
        )

        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=dataset["train"],
            eval_dataset=dataset["test"],
            tokenizer=tokenizer,
            data_collator=data_collator,
            compute_metrics=compute_metrics,
        )

        trainer.train()
        trainer.save_model(trained_model_dir)
        
        shutil.rmtree(temp_output_dir, ignore_errors=True)
        
        new_model_info = {
            "model_id": f"{self.model_id}_{suffix}",
            "base_model": f"{self.model_id}_{suffix}",
            "dir": trained_model_dir,
            "model_desc": f"Fine-tuned {self.model_id} model",
            "is_customised": True
        }
        
        return {
                "message": "Training completed successfully",
                "trained_model_path": trained_model_dir,
                "new_model_info": new_model_info
                }
    
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
        