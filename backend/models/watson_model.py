import json
import logging
import os
import requests
from .base_model import BaseModel
from backend.utils.ibm_cloud_account_auth import Authentication, ResourceService, AccountInfo
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.foundation_models.utils.enums import DecodingMethods
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

logger = logging.getLogger(__name__)

LIBRARY_PATH = "data/library.json"

class WatsonModel(BaseModel):
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.model = None  # Placeholder for the actual model instance
        self.auth = Authentication()
        self.resource_service = ResourceService()
        self.account_info = AccountInfo()
        self.model_inference = None

    @staticmethod
    def download(model_id: str, model_info: dict):
        try:
            logger.info(f"Creating library entry for Watson model {model_id}")
            system_prompt = """You are Granite Chat, created by IBM. You're designed to assist with information and answer questions. You don't have feelings or emotions, so you don't experience happiness or sadness. You're here to help make the user's day more productive or enjoyable. Always respond in a helpful and informative manner. Provide a single, concise response to each query without continuing the conversation. Do not add 'Human:' or any other conversation continuation at the end of your response."""
            new_entry = {
                "base_model": model_id,
                "is_customised": False,
                "is_online": model_info["is_online"],
                "model_source": model_info["model_source"],
                "model_class": model_info["model_class"],
                "tags": model_info["tags"],
                "prompt": {
                    "system_prompt": system_prompt,
                    "example_conversation": ""
                },
                "parameters": {
                    "temperature": 0.7,
                    "top_p": 1.0,
                    "top_k": 50,
                    "max_new_tokens": 1000,
                    "min_new_tokens": 1,
                    "repetition_penalty": 1.0,
                    "random_seed": 42,
                    "stop_sequences": [],
                    "project_id": "",
                    "use_dataset": False,
                    "dataset_name": None
                }
            }
            return new_entry
        except Exception as e:
            logger.error(f"Error adding model {model_id}: {str(e)}")
            return None

    def load(self, model_path: str, device: str, required_classes=None):
        # Validate API key
        api_key = os.getenv("IBM_CLOUD_API_KEY")
        if not api_key:
            logger.error("IBM_CLOUD_API_KEY not found in environment variables")
            return False

        valid = self.auth._validate_api_key(api_key)
        if not valid:
            logger.error("Invalid IBM Cloud API key")
            return False

        # Validate project ID and model ID
        iam_token = self.account_info.get_iam_token()
        projects = self.account_info.list_projects(iam_token)
        project_ids = [project["metadata"]["guid"] for project in projects]
        if self.model_id not in project_ids:
            logger.error(f"Project ID {self.model_id} not found in IBM Cloud projects")
            return False



        logger.info(f"Connecting to Watson WML model with ID {self.model_id}")
        self.model_inference = ModelInference(
            model_id=self.model_id,
            credentials=self.account_info.credentials,
            project_id=self.model_id
        )
        logger.info(f"Connected to Watson WML model {self.model_id}")
        return True

    def process_text(self, text: str):
        try:
            #dataset_management = DatasetManagement()

            with open(LIBRARY_PATH, "r") as file:
                library = json.load(file)
                model_info = library.get(self.model_id, {})
                prompt_info = model_info.get("prompt", {})
                parameters = model_info.get("parameters", {})

            full_prompt = ""
            if prompt_info.get("system_prompt"):
                full_prompt += f"{prompt_info['system_prompt']}\n\n"
            if prompt_info.get("example_conversation"):
                full_prompt += f"{prompt_info['example_conversation']}\n\n"
            
            # if parameters.get("use_dataset"):
            #     dataset_name = parameters.get("dataset_name")
            #     relevant_entries = dataset_management.find_relevant_entries(text, dataset_name)
            #     if relevant_entries:
            #         full_prompt += "Relevant information:\n"
            #         for entry in relevant_entries:
            #             full_prompt += f"- {entry}\n"
            #         full_prompt += "\n"
            
            full_prompt += f"Human: {text}\n\nAI:"
            
            params = {
                GenParams.DECODING_METHOD: DecodingMethods.SAMPLE,
                GenParams.TEMPERATURE: parameters.get("temperature"),
                GenParams.TOP_K: parameters.get("top_k"),
                GenParams.TOP_P: parameters.get("top_p"),
                GenParams.MAX_NEW_TOKENS: parameters.get("max_new_tokens"),
                GenParams.MIN_NEW_TOKENS: parameters.get("min_new_tokens"),
                GenParams.REPETITION_PENALTY: parameters.get("repetition_penalty"),
                GenParams.RANDOM_SEED: parameters.get("random_seed"),
                GenParams.STOP_SEQUENCES: parameters.get("stop_sequences")
            }
            
            result = self.model_inference.generate_text(prompt=full_prompt, params=params)
            
            for stop_seq in parameters.get("stop_sequences", []):
                if stop_seq in result:
                    result = result.split(stop_seq)[0]
            
            return {"result": result.strip()}

        except Exception as e:
            logger.error(f"Error: {e}")
            return {"result": str(e)}

    def process_request(self, payload: dict):
        # Implement the logic to process a prediction request
        logger.info(f"Processing request with payload: {json.dumps(payload)}")
        # ... prediction logic ...
        prediction = {"result": "prediction"}  # Placeholder for the actual prediction result
        return prediction

    def predict(self, text: str):
        # Implement the logic for sentiment prediction
        logger.info(f"Predicting sentiment for text: {text}")
        # ... sentiment prediction logic ...
        sentiment = {"sentiment": "positive"}  # Placeholder for the actual sentiment result
        return sentiment