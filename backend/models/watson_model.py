import json
import logging
import os
import requests
from .base_model import BaseModel
from backend.utils.ibm_cloud_account_auth import Authentication, ResourceService, AccountInfo, get_projects
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.foundation_models.utils.enums import DecodingMethods
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

logger = logging.getLogger(__name__)

LIBRARY_PATH = "data/library.json"



class WatsonModel(BaseModel):
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.project_id = None
        self.model = None
        self.auth = Authentication()
        self.resource_service = ResourceService()
        self.account_info = AccountInfo()
        self.model_inference = None

    @staticmethod
    def download(model_id: str, model_info: dict):
        try:
            logger.info(f"Attempting to download model: {model_id}")
            logger.info(f"Original model info: {json.dumps(model_info, indent=2)}")

            # Check if required services are available in the account
            account_info = AccountInfo()
            resources = account_info.get_resource_list()
            
            # Output resource list to JSON file
            resource_list_path = os.path.join('data', 'resource_list.json')
            with open(resource_list_path, 'w') as f:
                json.dump(resources, f, indent=4)
            logger.info(f"Resource list saved to {resource_list_path}")
            
            required_services = {
                'cloud_object_storage': False,
                'watson_studio': False,
                'watson_machine_learning': False
            }
            
            # ... in the download method:
            for resource in resources:
                resource_name = resource['name']
                if check_service(resource_name, 'cloud object storage'):
                    required_services['cloud_object_storage'] = True
                elif check_service(resource_name, 'watson studio'):
                    required_services['watson_studio'] = True
                elif check_service(resource_name, 'watson machine learning'):
                    required_services['watson_machine_learning'] = True
            logger.info(f"Detected services: {required_services}")
            
            missing_services = [service for service, available in required_services.items() if not available]
            if missing_services:
                logger.error(f"The following required services are missing: {', '.join(missing_services)}")
                logger.error(f"Available services: {[resource['name'] for resource in resources]}")
                return None
            
            # Create directory for the model
            model_dir = os.path.join('data', 'downloads', 'watson', model_id)
            os.makedirs(model_dir, exist_ok=True)

            # Save original model info to model_info.json in the model directory
            with open(os.path.join(model_dir, 'model_info.json'), 'w') as f:
                json.dump(model_info, f, indent=4)

            # Create the new entry for library.json
            logger.info(f"Creating library entry for Watson model {model_id}")

            system_prompt = """You are Granite Chat, created by IBM. You're designed to assist with information and answer questions. You don't have feelings or emotions, so you don't experience happiness or sadness. You're here to help make the user's day more productive or enjoyable. Always respond in a helpful and informative manner. Provide a single, concise response to each query without continuing the conversation. Do not add 'Human:' or any other conversation continuation at the end of your response."""
            new_entry = model_info.copy()
            new_entry.update({
                "base_model": model_id,
                "dir": model_dir,
                "is_customised": False,
                "config": {
                    "project_id": "",  # This will be set later when the user selects a project
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
                    },
                    "rag_settings": {
                        "use_dataset": False,
                        "dataset_name": None
                    }
                }
            })

            logger.info(f"New library entry: {json.dumps(new_entry, indent=2)}")
            return new_entry
        except Exception as e:
            logger.error(f"Error adding model {model_id}: {str(e)}")
            logger.exception("Full traceback:")
            return None

    def select_project(self):
        projects = get_projects()
        if not projects:
            logger.error("No projects available. Please create a project in IBM Watson Studio.")
            return False

        logger.info("Available projects:")
        for i, project in enumerate(projects):
            logger.info(f"{i+1}. ID: {project['id']}, Name: {project['name']}")

        # In a real application, you would prompt the user to select a project here
        # For now, we'll just use the first project
        selected_project = projects[0]
        self.project_id = selected_project["id"]
        logger.info(f"Selected project: {selected_project['name']} (ID: {self.project_id})")

        # Update the library with the selected project_id
        with open(LIBRARY_PATH, "r") as file:
            library = json.load(file)
        model_info = library.get(self.model_id, {})
        model_info['config']['project_id'] = self.project_id
        library[self.model_id] = model_info
        with open(LIBRARY_PATH, "w") as file:
            json.dump(library, file, indent=4)

        return True

    def load(self, model_path: str, device: str, required_classes=None, pipeline_tag: str = None):
        try:
            # Validate API key
            api_key = os.getenv("IBM_CLOUD_API_KEY")
            if not api_key:
                logger.error("IBM_CLOUD_API_KEY not found in environment variables")
                return False

            valid = self.auth._validate_api_key(api_key)
            if not valid:
                logger.error("Invalid IBM Cloud API key")
                return False

            # Load model info from library
            with open(LIBRARY_PATH, "r") as file:
                library = json.load(file)
                model_info = library.get(self.model_id, {})
                self.project_id = model_info.get("config", {}).get("project_id")

            if not self.project_id:
                if not self.select_project():
                    return False

            logger.info(f"Connecting to Watson WML model with ID {self.model_id}")

            # Set model ID, project ID, and credentials which are used to authenticate the model using api key and model URL
            self.model_inference = ModelInference(
                model_id=self.model_id,
                credentials=self.account_info.credentials,
                project_id=self.project_id
            )

            logger.info(f"Connected to Watson WML model {self.model_id}")
            return True
        except Exception as e:
            logger.error(f"Error loading model {self.model_id}: {str(e)}")
            return False

    def inference(self, data: dict):
        try:
            logger.info(f"Starting inference with data: {data}")
            payload = data.get("payload", "")
            if not payload:
                logger.error("No payload found in the input data")
                return {"error": "No payload found in the input data"}
            
            logger.info(f"Extracted payload: {payload}")

            with open(LIBRARY_PATH, "r") as file:
                library = json.load(file)
                model_info = library.get(self.model_id, {})
                config = model_info.get("config", {})
                
                prompt_info = config.get("prompt", {})
                parameters = config.get("parameters", {})
                rag_settings = config.get("rag_settings", {})

            full_prompt = ""
            if prompt_info.get("system_prompt"):
                full_prompt += f"{prompt_info['system_prompt']}\n\n"
            if prompt_info.get("example_conversation"):
                full_prompt += f"{prompt_info['example_conversation']}\n\n"
            
            if rag_settings.get("use_dataset"):
                dataset_name = rag_settings.get("dataset_name")
                # Implement dataset retrieval logic here
                # relevant_entries = dataset_management.find_relevant_entries(text, dataset_name)
                # if relevant_entries:
                #     full_prompt += "Relevant information:\n"
                #     for entry in relevant_entries:
                #         full_prompt += f"- {entry}\n"
                #     full_prompt += "\n"
            
            full_prompt += f"Human: {payload}\n\nAI:"
            
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
            
            logger.info(f"Sending prompt to model: {full_prompt}")
            logger.info(f"Using parameters: {params}")
            
            result = self.model_inference.generate_text(prompt=full_prompt, params=params)
            
            for stop_seq in parameters.get("stop_sequences", []):
                if stop_seq in result:
                    result = result.split(stop_seq)[0]
            
            final_result = {"result": result.strip()}
            logger.info(f"Final result: {final_result}")
            return final_result

        except Exception as e:
            logger.error(f"Error during inference: {e}", exc_info=True)
            return {"error": str(e)}

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



# ------------- LOCAL METHODS -------------

def check_service(resource_name, service_keyword):
    return service_keyword.lower().replace(' ', '') in resource_name.lower().replace(' ', '')