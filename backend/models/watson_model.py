import json
import logging
import os
import requests
from .base_model import BaseModel
from backend.utils.ibm_cloud_account_auth import Authentication, ResourceService, AccountInfo, get_projects
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.foundation_models.utils.enums import DecodingMethods
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from langchain_ibm import WatsonxEmbeddings
from ibm_watsonx_ai.foundation_models.utils.enums import EmbeddingTypes
from backend.utils.dataset_utility import DatasetManagement
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LIBRARY_PATH = "data/library.json"

class WatsonModel(BaseModel):
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.project_id = None
        self.config = None
        self.auth = Authentication()
        self.resource_service = ResourceService()
        self.account_info = AccountInfo()
        self.model_inference = None
        self.embeddings = None
        self.is_loaded = False

    @staticmethod
    def download(model_id: str, model_info: dict):
        try:
            logger.info(f"Attempting to download model: {model_id}")
            logger.info(f"Original model info: {json.dumps(model_info, indent=2)}")

            # Check if required services are available in the account
            account_info = AccountInfo()
            resources = account_info.get_resource_list()
            
            # Output resource list to JSON file
            resource_list_path = os.path.join('data', 'downloads', 'watson', 'resource_list.json')
            with open(resource_list_path, 'w') as f:
                json.dump(resources, f, indent=4)
            logger.info(f"Resource list saved to {resource_list_path}")
            
            required_services = {
                'cloud_object_storage': False,
                'watson_studio': False,
                'watson_machine_learning': False
            }
            
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

            new_entry = model_info.copy()
            new_entry.update({
                "base_model": model_id,
                "dir": model_dir,
                "is_customised": False,
            })

            logger.info(f"New library entry: {json.dumps(new_entry, indent=2)}")
            return new_entry
        except Exception as e:
            logger.error(f"Error adding model {model_id}: {str(e)}")
            logger.exception("Full traceback:")
            return None

    def select_project(self):
        load_dotenv()  # Reload environment variables
        projects = get_projects()
        if not projects:
            logger.error("No projects available. Please create a project in IBM Watson Studio.")
            return False

        # Use the first project
        selected_project = projects[0]
        self.project_id = selected_project["id"]
        logger.info(f"Selected project: {selected_project['name']} (ID: {self.project_id})")

        # Update the .env file with the selected project ID
        env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
        self.update_env_file(env_path, "USER_PROJECT_ID", self.project_id)
        logger.info(f"Updated .env file with USER_PROJECT_ID={self.project_id}")

        return True

    def update_env_file(self, file_path, key, value):
        with open(file_path, 'r') as file:
            lines = file.readlines()

        with open(file_path, 'w') as file:
            updated = False
            for line in lines:
                if line.startswith(f"{key}="):
                    file.write(f"{key}={value}\n")
                    updated = True
                else:
                    file.write(line)
            if not updated:
                file.write(f"\n{key}={value}\n")
        load_dotenv()  # Reload environment variables after update

    def load(self, device: str, model_info: dict):
        try:
            # Validate API key
            api_key = os.getenv("IBM_CLOUD_API_KEY")
            if not api_key:
                raise ValueError("IBM_CLOUD_API_KEY not found in environment variables")

            # Validate API key using the Authentication class
            if not self.auth._validate_api_key(api_key):
                raise ValueError("Invalid IBM_CLOUD_API_KEY")

            # Get the URL from environment variable
            url = os.getenv("IBM_CLOUD_MODELS_URL")
            if not url:
                raise ValueError("IBM_CLOUD_MODELS_URL not found in environment variables")

            self.config = model_info.get("config", {})
            
            # Check for USER_PROJECT_ID in .env file
            self.project_id = os.getenv("USER_PROJECT_ID")
            if not self.project_id:
                logger.info("No USER_PROJECT_ID found or it's empty. Selecting a project...")
                if not self.select_project():
                    raise ValueError("Failed to select a project")
            else:
                logger.info(f"Using project ID from .env file: {self.project_id}")

            logger.info(f"Connecting to Watson WML model with ID {self.model_id}")
            logger.info(f"Using project ID: {self.project_id}")

            # Check if it's an embedding model
            if self.model_id in ["ibm/slate-30m-english-rtrvr", "ibm/slate-125m-english-rtrvr", 
                                 "sentence-transformers/all-minilm-l12-v2", "intfloat/multilingual-e5-large"]:
                embedding_type = self._get_embedding_type(self.model_id)
                logger.info(f"Initializing embedding model with type: {embedding_type}")
                
                self.embeddings = WatsonxEmbeddings(
                    model_id=embedding_type,
                    url=url,
                    apikey=api_key,
                    project_id=self.project_id
                )
                logger.info(f"Connected to Watson embedding model {self.model_id}")
                logger.info(f"Embedding dimensions: {self.config.get('embedding_dimensions')}")
                logger.info(f"Max input tokens: {self.config.get('max_input_tokens')}")
                self.is_loaded = True
            else:
                self.model_inference = ModelInference(
                    model_id=self.model_id,
                    credentials=self.account_info.credentials,
                    project_id=self.project_id
                )
                logger.info(f"Connected to Watson WML model {self.model_id}")
                logger.info(f"Model parameters: {self.config.get('parameters')}")
                self.is_loaded = True

            return True
        except AttributeError as e:
            logger.error(f"AttributeError while loading model {self.model_id}: {str(e)}")
            logger.exception("Full traceback:")
            self.is_loaded = False
            return False
        except Exception as e:
            logger.error(f"Error loading model {self.model_id}: {str(e)}")
            logger.exception("Full traceback:")
            self.is_loaded = False
            return False

    def _get_embedding_type(self, model_id):
        embedding_types = {
            "ibm/slate-30m-english-rtrvr": EmbeddingTypes.IBM_SLATE_30M_ENG.value,
            "ibm/slate-125m-english-rtrvr": EmbeddingTypes.IBM_SLATE_125M_ENG.value,
            "sentence-transformers/all-minilm-l12-v2": "sentence-transformers/all-minilm-l12-v2",
            "intfloat/multilingual-e5-large": "intfloat/multilingual-e5-large"
        }
        return embedding_types.get(model_id, EmbeddingTypes.IBM_SLATE_30M_ENG.value)

    def inference(self, data: dict):
        if not self.is_loaded:
            logger.error(f"Model {self.model_id} not initialized. Please call load() before inference.")
            return {"error": "Model not initialized. Please call load() before inference."}

        try:
            if self.embeddings:
                # We can change this to accept multiple inputs, and give multiple outputs - for analytics
                text = data.get('payload', '')
                if not text:
                    raise ValueError("Text is required for embedding generation")
                embedding = self.embeddings.embed_query(text)
                return {"embedding": embedding, "dimensions": len(embedding)}
            elif self.model_inference:
                logger.info(f"Starting inference with data: {data}")
                payload = data.get("payload", "")
                if not payload:
                    logger.error("No payload found in the input data")
                    return {"error": "No payload found in the input data"}
                
                logger.info(f"Extracted payload: {payload}")

                prompt_info = self.config.get("prompt", {})
                parameters = self.config.get("parameters", {})
                rag_settings = self.config.get("rag_settings", {})

                logger.info(f"Prompt info: {prompt_info}")
                logger.info(f"Parameters: {parameters}")
                logger.info(f"RAG settings: {rag_settings}")

                full_prompt = ""
                if prompt_info.get("system_prompt"):
                    full_prompt += f"{prompt_info['system_prompt']}\n\n"
                    logger.info(f"Added system prompt: {prompt_info['system_prompt']}")
                if prompt_info.get("example_conversation"):
                    full_prompt += f"{prompt_info['example_conversation']}\n\n"
                    logger.info(f"Added example conversation: {prompt_info['example_conversation']}")
                
                if rag_settings.get("use_dataset"):
                    logger.info("RAG is enabled, attempting to find relevant entries")
                    dataset_name = rag_settings.get("dataset_name")
                    similarity_threshold = rag_settings.get("similarity_threshold", 0.5)
                    if dataset_name:
                        logger.info(f"Using dataset: {dataset_name}")
                        dataset_management = DatasetManagement()
                        relevant_entries = dataset_management.find_relevant_entries(payload, dataset_name, similarity_threshold)
                        if relevant_entries:
                            logger.info(f"Found {len(relevant_entries)} relevant entries")
                            full_prompt += "Relevant information:\n"
                            for entry in relevant_entries:
                                full_prompt += f"- {entry}\n"
                            full_prompt += "\n"
                            logger.info(f"Added relevant entries to prompt: {relevant_entries}")
                        else:
                            logger.info("No relevant entries found")
                    else:
                        logger.warning("RAG is enabled but no dataset name provided")
                else:
                    logger.info("RAG is not enabled")
                
                full_prompt += f"Human: {payload}\n\nAI:"
                logger.info(f"Final full prompt: {full_prompt}")
                
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
                
                logger.info(f"Using parameters: {params}")
                
                result = self.model_inference.generate_text(prompt=full_prompt, params=params)
                logger.info(f"Raw result from model: {result}")
                
                for stop_seq in parameters.get("stop_sequences", []):
                    if stop_seq in result:
                        result = result.split(stop_seq)[0]
                        logger.info(f"Applied stop sequence: {stop_seq}")
                
                final_result = {"result": result.strip()}
                logger.info(f"Final result: {final_result}")
                return final_result
            else:
                raise ValueError("Neither embeddings nor model_inference is initialized.")
        except Exception as e:
            logger.error(f"Error during inference: {e}", exc_info=True)
            return {"error": str(e)}

    def process_request(self, payload: dict):
        return self.inference(payload)

    def predict(self, text: str):
        return self.inference({"payload": text})

# ------------- LOCAL METHODS -------------

def check_service(resource_name, service_keyword):
    return service_keyword.lower().replace(' ', '') in resource_name.lower().replace(' ', '')