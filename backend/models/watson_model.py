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
from backend.utils.watson_settings_manager import watson_settings

from backend.core.exceptions import ModelError
from ibm_watsonx_ai.wml_client_error import ApiRequestFailure

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LIBRARY_PATH = "data/library.json"

class WatsonModel(BaseModel):
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.config = None
        self.auth = None
        self.resource_service = None
        self.account_info = None
        self.model_inference = None
        self.embeddings = None
        self.is_loaded = False
        self.api_key = None
        self.project_id = None
        self.chat_history = []
        self.relevant_entries_count = 0
        self.total_entries_count = 0
        
        logger.info(f"Initialized WatsonModel with ID: {self.model_id}")

    def select_project(self):
        projects = get_projects()
        if not projects:
            logger.error("No projects available. Please create a project in IBM Watson Studio.")
            return False

        # Use the first project
        selected_project = projects[0]
        self.project_id = selected_project["id"]
        logger.info(f"Selected project: {selected_project['name']} (ID: {self.project_id})")

        # Update the USER_PROJECT_ID setting
        watson_settings.set("USER_PROJECT_ID", self.project_id)
        logger.info(f"Updated USER_PROJECT_ID={self.project_id}")

        return True

    @staticmethod
    def download(model_id: str, model_info: dict):
        try:
            logger.info(f"Attempting to download model: {model_id}")
            logger.info(f"Original model info: {json.dumps(model_info, indent=2)}")

            # Check if API key is available and valid
            api_key = watson_settings.get('IBM_CLOUD_API_KEY')
            if not api_key:
                raise ModelError("No IBM API key found.\n\nPlease set your key in Settings.")
            
            auth = Authentication()
            if not auth.validate_api_key():
                raise ModelError("Invalid IBM API key.\n\nPlease check your key in Settings.")

            # Check if required services are available in the account
            account_info = AccountInfo()
            resources = account_info.get_resource_list()
            
            # Output resource list to JSON file
            base_dir = os.path.join('data', 'downloads', 'watson')
            # Create the downloads directory if it doesn't exist
            os.makedirs(base_dir, exist_ok=True)
            resource_list_path = os.path.join(base_dir, 'resource_list.json')
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
                # formatted_missing_services = ", ".join(format_service_name(service) for service in missing_services)
                formatted_missing_services = format_service_name_to_list(missing_services)
                error_message = f"The following required services are missing from your IBM Cloud account resource list:\n\n{formatted_missing_services}"
                logger.error(error_message)
                logger.error(f"Available services: {[resource['name'] for resource in resources]}")
                raise ModelError(error_message)

            if api_key and auth.validate_api_key():
                # Create directory for the model
                model_dir = os.path.join(base_dir, model_id)
                os.makedirs(model_dir, exist_ok=True)
                logger.info(f"Created directory for model: {model_dir}")

                # Save original model info to model_info.json in the model directory
                model_info_path = os.path.join(model_dir, 'model_info.json')
                with open(model_info_path, 'w') as f:
                    json.dump(model_info, f, indent=4)
                logger.info(f"Saved model info to {model_info_path}")

                # Create the new entry for library.json
                logger.info(f"Creating library entry for Watson model {model_id}...")

                new_entry = model_info.copy()
                new_entry.update({
                    "base_model": model_id,
                    "dir": model_dir,
                    "is_customised": False,
                })

                logger.info(f"New library entry: {json.dumps(new_entry, indent=2)}")
                return new_entry
            else:
                error_message = f"No valid API key found. Skipping model download and library entry creation for model {model_id}"
                logger.warning(error_message)
                raise ModelError(error_message)

        except ModelError as e:
            logger.error(f"Error downloading model {model_id}: {str(e)}")
            logger.exception("Full traceback:")
            raise

        except Exception as e:
            logger.error(f"Unexpected error downloading model {model_id}: {str(e)}")
            logger.exception("Full traceback:")
            raise ModelError(f"Unexpected error occurred while downloading {model_id}. Please try again later.")

    def load(self, device: str, model_info: dict):
        try:
            self.api_key = watson_settings.get('IBM_CLOUD_API_KEY')
            self.project_id = watson_settings.get('USER_PROJECT_ID')

            if not self.api_key:
                raise ModelError("No IBM API key found.\n\nPlease set your key in Settings.")

            self.auth = Authentication()
            if not self.auth.validate_api_key():
                raise ModelError("Invalid IBM API key.\n\nPlease check your key in Settings.")

            url = watson_settings.get("IBM_CLOUD_MODELS_URL")
            if not url:
                raise ModelError("IBM_CLOUD_MODELS_URL not found in environment variables")

            self.config = model_info.get("config", {})
            
            if not self.project_id:
                logger.info("No USER_PROJECT_ID found or it's empty. Selecting a project...")
                if not self.select_project():
                    raise ModelError("Failed to select a project.\n\nGo to your IBM Cloud account and create a project in Watson Studio.")
            else:
                logger.info(f"Validating project ID: {self.project_id}")
                if not self.auth.validate_project(self.project_id):
                    raise ModelError(f"Invalid project ID:\n\n\t{self.project_id}\n\nPlease set another project in Settings.")

            logger.info(f"Using valid project ID: {self.project_id}")

            logger.info(f"Connecting to Watson WML model with ID {self.model_id}")
            logger.info(f"Using project ID: {self.project_id}")

            # Check if it's an embedding model
            if self.model_id in [
                "ibm/slate-30m-english-rtrvr",
                "ibm/slate-30m-english-rtrvr-v2",
                "ibm/slate-125m-english-rtrvr",
                "ibm/slate-125m-english-rtrvr-v2",
                "sentence-transformers/all-minilm-l12-v2",
                "intfloat/multilingual-e5-large",
                "cross-encoder/ms-marco-minilm-l-12-v2"
            ]:
                embedding_type = self._get_embedding_type(self.model_id)
                logger.info(f"Initializing embedding model with type: {embedding_type}")
                
                self.embeddings = WatsonxEmbeddings(
                    model_id=embedding_type,
                    url=url,
                    apikey=self.api_key,
                    project_id=self.project_id
                )
                logger.info(f"Connected to Watson embedding model {self.model_id}")
                logger.info(f"Embedding dimensions: {self.config.get('embedding_dimensions')}")
                logger.info(f"Max input tokens: {self.config.get('max_input_tokens')}")
                self.is_loaded = True
            else:
                self.account_info = AccountInfo()
                self.model_inference = ModelInference(
                    model_id=self.model_id,
                    credentials=self.account_info.credentials,
                    project_id=self.project_id
                )
                logger.info(f"Connected to Watson WML model {self.model_id}")
                logger.info(f"Model parameters: {self.config.get('parameters')}")
                self.is_loaded = True

            return True

        except ModelError as e:
            logger.error(f"Error loading model {self.model_id}: {str(e)}")
            self.is_loaded = False
            raise

        except Exception as e:
            logger.error(f"Unexpected error loading model {self.model_id}: {str(e)}")
            logger.exception("Full traceback:")
            self.is_loaded = False
            raise ModelError(f"Unexpected error occurred while downloading the model. Please try again later.")

    def _get_embedding_type(self, model_id):
        embedding_types = {
            "ibm/slate-30m-english-rtrvr": EmbeddingTypes.IBM_SLATE_30M_ENG.value,
            "ibm/slate-30m-english-rtrvr-v2": "ibm/slate-30m-english-rtrvr-v2",
            "ibm/slate-125m-english-rtrvr": EmbeddingTypes.IBM_SLATE_125M_ENG.value,
            "ibm/slate-125m-english-rtrvr-v2": "ibm/slate-125m-english-rtrvr-v2",
            "sentence-transformers/all-minilm-l12-v2": "sentence-transformers/all-minilm-l12-v2",
            "intfloat/multilingual-e5-large": "intfloat/multilingual-e5-large",
            "cross-encoder/ms-marco-minilm-l-12-v2": "cross-encoder/ms-marco-minilm-l-12-v2"
        }
        return embedding_types.get(model_id, EmbeddingTypes.IBM_SLATE_30M_ENG.value)

    def inference(self, data: dict):
        if not self.is_loaded:
            logger.error(f"Model {self.model_id} not initialized. Please call load() before inference.")
            raise ModelError("Model not initialized. Please call load() before inference.")

        try:
            if self.embeddings:
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
                    raise ModelError("No payload found in the input data")
                
                logger.info(f"Extracted payload: {payload}")

                prompt_info = self.config.get("prompt", {})
                parameters = self.config.get("parameters", {})
                rag_settings = self.config.get("rag_settings", {})
                use_chat_history = self.config.get("chat_history", False)

                logger.info(f"Prompt info: {prompt_info}")
                logger.info(f"Parameters: {parameters}")
                logger.info(f"RAG settings: {rag_settings}")
                logger.info(f"Use chat history: {use_chat_history}")

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
                    use_chunking = rag_settings.get("use_chunking", False)
                    logger.info(f"Chunking is {'enabled' if use_chunking else 'disabled'}")
                    if dataset_name:
                        logger.info(f"Using dataset: {dataset_name}")
                        dataset_management = DatasetManagement()
                        relevant_entries, self.relevant_entries_count, self.total_entries_count = dataset_management.find_relevant_entries(
                            payload, 
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
                            logger.info(f"Added relevant entries to prompt: {relevant_entries}")
                        else:
                            logger.info("No relevant entries found")
                    else:
                        logger.warning("RAG is enabled but no dataset name provided")
                else:
                    logger.info("RAG is not enabled")
                    self.relevant_entries_count = 0
                    self.total_entries_count = 0
                
                if use_chat_history:
                    for message in self.chat_history:
                        full_prompt += f"{message['role'].capitalize()}: {message['content']}\n"
                    logger.info(f"Added chat history to prompt")
                
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
                
                # result = self.model_inference.generate_text(prompt=full_prompt, params=params)

                try:
                    result = self.model_inference.generate_text(prompt=full_prompt, params=params)
                except ApiRequestFailure as e:
                    if "the number of input tokens" in str(e) and "cannot exceed the total tokens limit" in str(e):
                        raise ModelError(f"Input exceeds model's token limit. Please reduce the input size.")
                    raise ModelError(f"API request failed: {str(e)}")
                except ModelError:
                    raise
                except Exception as e:
                    raise ModelError(f"An unexpected error occurred during inference: {str(e)}")
                
                logger.info(f"Raw result from model: {result}")
                
                for stop_seq in parameters.get("stop_sequences", []):
                    if stop_seq in result:
                        result = result.split(stop_seq)[0]
                        logger.info(f"Applied stop sequence: {stop_seq}")
                
                final_result = result.strip()
                logger.info(f"Final result: {final_result}")

                if use_chat_history:
                    self.chat_history.append({"role": "human", "content": payload})
                    self.chat_history.append({"role": "ai", "content": final_result})

                return {
                    "result": final_result,
                    "relevant_entries_count": self.relevant_entries_count,
                    "total_entries_count": self.total_entries_count
                }
            else:
                raise ValueError("Neither embeddings nor model_inference is initialized.")
        except ModelError as e:
            logger.error(f"ModelError during inference: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during inference: {e}", exc_info=True)
            raise ModelError(f"An unexpected error occurred during inference: {str(e)}")

    def process_request(self, payload: dict):
        return self.inference(payload)

    def predict(self, text: str):
        return self.inference({"payload": text})

    def clear_chat_history(self):
        self.chat_history = []
        logger.info("Chat history cleared")

# ------------- LOCAL METHODS -------------

def check_service(resource_name, service_keyword):
    return service_keyword.lower().replace(' ', '') in resource_name.lower().replace(' ', '')

def format_service_name(service):
    return ' '.join(word.capitalize() for word in service.split('_'))

def format_service_name_to_list(services):
    if isinstance(services, str):
        services = [services]
    return '\n'.join(f"- {' '.join(word.capitalize() for word in service.replace('_', ' ').split())}" for service in services)