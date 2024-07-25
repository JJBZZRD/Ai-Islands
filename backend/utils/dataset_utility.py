import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from langchain_ibm import WatsonxEmbeddings
from ibm_watsonx_ai.foundation_models.utils.enums import EmbeddingTypes
from pathlib import Path
import pickle
import json
import os
from dotenv import load_dotenv
from backend.utils.ibm_cloud_account_auth import Authentication, ResourceService, AccountInfo, get_projects
import logging
from backend.utils.watson_settings_manager import watson_settings

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatasetManagement:
    SENTENCE_TRANSFORMER_MODELS = [
        'all-MiniLM-L6-v2',
        'all-mpnet-base-v2',
        'all-distilroberta-v1',
        'all-MiniLM-L12-v2',
        'paraphrase-multilingual-MiniLM-L12-v2',
        'paraphrase-multilingual-mpnet-base-v2',
        'distiluse-base-multilingual-cased-v1',
        'msmarco-distilbert-base-v4',
        'multi-qa-MiniLM-L6-cos-v1',
        'all-roberta-large-v1',
        'paraphrase-albert-small-v2',
        'paraphrase-MiniLM-L3-v2'
    ]

    WATSON_MODELS = [
        'ibm/slate-30m-english-rtrvr',
        'ibm/slate-125m-english-rtrvr',
        'sentence-transformers/all-minilm-l12-v2',
        'intfloat/multilingual-e5-large'
    ]

    def __init__(self, model_name=None):
        self.model_name = model_name or self.SENTENCE_TRANSFORMER_MODELS[0]
        logger.info(f"Initializing DatasetManagement with model: {self.model_name}")
        
        if self.model_name in self.WATSON_MODELS:
            self.model_type = 'watson'
            logger.info("Using Watson model")
            self._initialize_watson_embeddings()
        else:
            self.model_type = 'sentence_transformer'
            logger.info("Using SentenceTransformer model")
            self.embeddings = SentenceTransformer(self.model_name)

    def _initialize_watson_embeddings(self):
        logger.info(f"Initializing Watson embeddings: {self.model_name}")
        api_key = watson_settings.get("IBM_CLOUD_API_KEY")
        url = watson_settings.get("IBM_CLOUD_MODELS_URL")
        project_id = self._get_or_create_project_id()

        if not all([api_key, url, project_id]):
            logger.error("Missing required Watson credentials")
            raise ValueError("API key, URL, and project ID are required for Watson models")

        self._check_required_services()

        embedding_type_map = {
            "ibm/slate-30m-english-rtrvr": EmbeddingTypes.IBM_SLATE_30M_ENG,
            "ibm/slate-125m-english-rtrvr": EmbeddingTypes.IBM_SLATE_125M_ENG,
            "sentence-transformers/all-minilm-l12-v2": "sentence-transformers/all-minilm-l12-v2",
            "intfloat/multilingual-e5-large": "intfloat/multilingual-e5-large"
        }

        embedding_type = embedding_type_map.get(self.model_name)
        if not embedding_type:
            logger.error(f"Unsupported Watson embedding model: {self.model_name}")
            raise ValueError(f"Unsupported Watson embedding model: {self.model_name}")

        logger.info(f"Using embedding type: {embedding_type}")
        self.embeddings = WatsonxEmbeddings(
            model_id=embedding_type.value if isinstance(embedding_type, EmbeddingTypes) else embedding_type,
            url=url,
            apikey=api_key,
            project_id=project_id
        )
        logger.info("Watson embeddings initialized successfully")

    def _check_required_services(self):
        logger.info("Checking required services")
        account_info = AccountInfo()
        resources = account_info.get_resource_list()
        
        required_services = {
            'cloud_object_storage': False,
            'watson_studio': False,
            'watson_machine_learning': False
        }
        
        for resource in resources:
            resource_name = resource['name']
            if self._check_service(resource_name, 'cloud object storage'):
                required_services['cloud_object_storage'] = True
            elif self._check_service(resource_name, 'watson studio'):
                required_services['watson_studio'] = True
            elif self._check_service(resource_name, 'watson machine learning'):
                required_services['watson_machine_learning'] = True
        
        missing_services = [service for service, available in required_services.items() if not available]
        if missing_services:
            logger.error(f"Missing required services: {', '.join(missing_services)}")
            raise ValueError(f"The following required services are missing: {', '.join(missing_services)}")
        logger.info("All required services are available")

    def _check_service(self, resource_name, service_keyword):
        return service_keyword.lower().replace(' ', '') in resource_name.lower().replace(' ', '')

    def _get_or_create_project_id(self):
        logger.info("Getting or creating project ID")
        projects = get_projects()
        if not projects:
            logger.error("No projects available")
            raise ValueError("No projects available. Please create a project in IBM Watson Studio.")
        logger.info(f"Using project ID: {projects[0]['id']}")
        return projects[0]["id"]

    @classmethod
    def get_available_models(cls):
        return {
            'sentence_transformer': cls.SENTENCE_TRANSFORMER_MODELS,
            'watson': cls.WATSON_MODELS
        }

    def generate_embeddings(self, texts):
        logger.info(f"Generating embeddings for {len(texts)} texts")
        if self.model_type == 'watson':
            embeddings = np.array(self.embeddings.embed_documents(texts)).astype('float32')
        else:
            embeddings = self.embeddings.encode(texts, show_progress_bar=True)
        logger.info(f"Generated embeddings with shape: {embeddings.shape}")
        return embeddings

    def process_dataset(self, file_path: str):
        try:
            logger.info(f"Processing dataset: {file_path}")
            file_path = Path(file_path)
            filename = file_path.stem
            dataset_dir = Path("Datasets") / filename
            dataset_dir.mkdir(parents=True, exist_ok=True)

            df = pd.read_csv(file_path)
            logger.info(f"Loaded dataset with {len(df)} rows")
            
            texts = df.apply(lambda row: ' '.join([f"{col}: {val}" for col, val in row.items()]), axis=1).tolist()

            embeddings = self.generate_embeddings(texts)
            faiss.normalize_L2(embeddings)

            index = faiss.IndexFlatIP(embeddings.shape[1])
            index.add(embeddings)

            faiss_index_path = dataset_dir / f"{filename}_faiss_index.bin"
            faiss.write_index(index, str(faiss_index_path))
            logger.info(f"Saved FAISS index to {faiss_index_path}")

            embedding_pickle_path = dataset_dir / f"{filename}_embeddings.pkl"
            with open(embedding_pickle_path, 'wb') as f:
                pickle.dump(embeddings, f)
            logger.info(f"Saved embeddings to {embedding_pickle_path}")

            data_pickle_path = dataset_dir / f"{filename}_data.pkl"
            df.to_pickle(data_pickle_path)
            logger.info(f"Saved original data to {data_pickle_path}")

            model_info = {
                "model_type": self.model_type,
                "model_name": self.model_name,
                "embedding_dimensions": embeddings.shape[1],
                "max_input_tokens": self.embeddings.max_seq_length if hasattr(self.embeddings, 'max_seq_length') else None,
            }
            model_info_path = dataset_dir / f"{filename}_embedding_model_info.json"
            with open(model_info_path, 'w') as f:
                json.dump(model_info, f, indent=4)
            logger.info(f"Saved model info to {model_info_path}")

            return {"message": "Dataset processed successfully", "model_info": model_info}

        except Exception as e:
            logger.error(f"Error processing dataset: {e}")
            return {"message": "Error processing dataset", "error": str(e)}

    def list_datasets(self):
        try:
            datasets_dir = Path("Datasets")
            datasets = [d.name for d in datasets_dir.iterdir() if d.is_dir()]
            logger.info(f"Found {len(datasets)} datasets")
            return {"datasets": datasets}
        except Exception as e:
            logger.error(f"Error listing datasets: {e}")
            return {"datasets": []}

    def find_relevant_entries(self, query, dataset_name, similarity_threshold=0.5):
        logger.info(f"Finding relevant entries for query: '{query}' in dataset: {dataset_name}")
        dataset_dir = Path("Datasets") / dataset_name
        embedding_pickle_path = dataset_dir / f"{dataset_name}_embeddings.pkl"
        data_pickle_path = dataset_dir / f"{dataset_name}_data.pkl"
        model_info_path = dataset_dir / f"{dataset_name}_embedding_model_info.json"

        if not all(path.exists() for path in [embedding_pickle_path, data_pickle_path, model_info_path]):
            logger.error("Missing required files for dataset")
            return []

        with open(model_info_path, 'r') as f:
            model_info = json.load(f)
        logger.info(f"Loaded model info: {model_info}")

        self.model_name = model_info['model_name']
        self.model_type = model_info['model_type']

        if self.model_type == 'watson':
            logger.info(f"Initializing Watson embeddings for query: {self.model_name}")
            self._initialize_watson_embeddings()
        elif self.model_type == 'sentence_transformer':
            logger.info(f"Initializing SentenceTransformer: {self.model_name}")
            self.embeddings = SentenceTransformer(self.model_name)
        else:
            logger.error(f"Unsupported model type: {self.model_type}")
            return []

        with open(embedding_pickle_path, 'rb') as f:
            stored_embeddings = pickle.load(f)
        logger.info(f"Loaded stored embeddings with shape: {stored_embeddings.shape}")

        faiss_index_path = dataset_dir / f"{dataset_name}_faiss_index.bin"
        index = faiss.read_index(str(faiss_index_path))
        logger.info(f"Loaded FAISS index with {index.ntotal} vectors")

        original_data = pd.read_pickle(data_pickle_path)
        logger.info(f"Loaded original data with {len(original_data)} rows")

        query_vector = self.generate_embeddings([query])
        logger.info(f"Generated query embedding with shape: {query_vector.shape}")

        faiss.normalize_L2(query_vector)
        D, I = index.search(query_vector, index.ntotal)  # Search all vectors
        logger.info(f"Searched all {index.ntotal} vectors")

        relevant_indices = I[0][D[0] > similarity_threshold]
        logger.info(f"Found {len(relevant_indices)} entries above similarity threshold {similarity_threshold}")

        relevant_entries = original_data.iloc[relevant_indices].to_dict('records')
        formatted_entries = [self.format_entry(entry) for entry in relevant_entries]
        logger.info(f"Returning {len(formatted_entries)} formatted entries")
        return formatted_entries

    def format_entry(self, entry):
        return ', '.join([f"{key}: {value}" for key, value in entry.items()])