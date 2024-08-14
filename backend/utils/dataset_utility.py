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
import shutil
from backend.utils.file_type_manager import FileTypeManager
from backend.data_utils.json_handler import JSONHandler
from backend.core.config import CONFIG_PATH

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
        self.model_type = 'watson' if self.model_name in self.WATSON_MODELS else 'sentence_transformer'
        logger.info(f"Initializing DatasetManagement with model: {self.model_name} (type: {self.model_type})")
        self.embeddings = None
        self.chunking_settings = self._load_chunking_settings()
        self.file_type_manager = FileTypeManager()

    def _load_chunking_settings(self):
        config = JSONHandler.read_json(CONFIG_PATH)
        chunking_settings = config.get('chunking', {})
        if not chunking_settings:
            logger.warning("Chunking settings not found. Using default settings.")
            return {
                "use_chunking": False,
                "chunk_size": 500,
                "chunk_overlap": 50,
                "chunk_method": "fixed_length",
                "rows_per_chunk": 1,
                "csv_columns": []
            }
        return chunking_settings

    def _initialize_embedding_model(self, model_info):
        logger.info(f"Initializing embedding model with info: {model_info}")
        model_type = model_info.get('model_type')
        model_name = model_info.get('model_name')
        
        logger.info(f"Model type: {model_type}, Model name: {model_name}")
        
        if model_type == 'watson':
            logger.info(f"Initializing Watson embeddings: {model_name}")
            return self._initialize_watson_embeddings(model_name)
        elif model_type == 'sentence_transformer':
            logger.info(f"Initializing SentenceTransformer: {model_name}")
            return SentenceTransformer(model_name)
        else:
            logger.error(f"Unsupported model type: {model_type}")
            raise ValueError(f"Unsupported model type: {model_type}")

    def _initialize_watson_embeddings(self, model_name):
        logger.info(f"Initializing Watson embeddings: {model_name}")
        api_key = watson_settings.get("IBM_CLOUD_API_KEY")
        url = watson_settings.get("IBM_CLOUD_MODELS_URL")
        project_id = watson_settings.get("USER_PROJECT_ID")

        logger.info(f"Initial project ID from settings: {project_id}")

        if not project_id:
            project_id = self._get_or_create_project_id()
            watson_settings.set("USER_PROJECT_ID", project_id)
            logger.info(f"New project ID set: {project_id}")

        logger.info(f"Final project ID being used: {project_id}")

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

        embedding_type = embedding_type_map.get(model_name)
        if not embedding_type:
            logger.error(f"Unsupported Watson embedding model: {model_name}")
            raise ValueError(f"Unsupported Watson embedding model: {model_name}")

        logger.info(f"Using embedding type: {embedding_type}")
        return WatsonxEmbeddings(
            model_id=embedding_type.value if isinstance(embedding_type, EmbeddingTypes) else embedding_type,
            url=url,
            apikey=api_key,
            project_id=project_id
        )

    def _check_service(self, resource_name, service_keyword):
        return service_keyword.lower().replace(' ', '') in resource_name.lower().replace(' ', '')

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

    def _get_or_create_project_id(self):
        logger.info("Getting or creating project ID")
        project_id = watson_settings.get("USER_PROJECT_ID")
        if project_id:
            logger.info(f"Using existing project ID: {project_id}")
            return project_id

        projects = get_projects()
        if not projects:
            logger.error("No projects available")
            raise ValueError("No projects available. Please create a project in IBM Watson Studio.")
        
        project_id = projects[0]["id"]
        watson_settings.set("USER_PROJECT_ID", project_id)
        logger.info(f"Created and stored new project ID: {project_id}")
        return project_id

    @classmethod
    def get_available_models(cls):
        return {
            'sentence_transformer': cls.SENTENCE_TRANSFORMER_MODELS,
            'watson': cls.WATSON_MODELS
        }

    def generate_embeddings(self, texts, model_info=None):
        logger.info(f"Generating embeddings for {len(texts)} texts")
        logger.info(f"Model info: {model_info}")
        
        if model_info is None:
            if self.embeddings is None:
                logger.info(f"Initializing default embedding model: {self.model_name} (type: {self.model_type})")
                self.embeddings = self._initialize_embedding_model({'model_type': self.model_type, 'model_name': self.model_name})
        else:
            logger.info(f"Initializing embedding model with provided info: {model_info}")
            self.embeddings = self._initialize_embedding_model(model_info)

        if isinstance(self.embeddings, WatsonxEmbeddings):
            embeddings = self.embeddings.embed_documents(texts)
        else:  # SentenceTransformer
            embeddings = self.embeddings.encode(texts, show_progress_bar=True)
        
        embeddings = np.array(embeddings).astype('float32')
        logger.info(f"Generated embeddings with shape: {embeddings.shape}")
        return embeddings

    def process_dataset(self, file_path: Path):
        logger.info(f"Processing dataset: {file_path}")
        try:
            filename = file_path.stem
            dataset_dir = Path("Datasets") / filename
            dataset_dir.mkdir(parents=True, exist_ok=True)

            original_file_path = dataset_dir / file_path.name
            if not original_file_path.exists():
                shutil.copy2(file_path, original_file_path)

            method_folder = "chunked" if self.chunking_settings["use_chunking"] else "default"
            processing_dir = dataset_dir / method_folder
            processing_dir.mkdir(exist_ok=True)

            is_csv = file_path.suffix.lower() == '.csv'
            
            if is_csv:
                df = pd.read_csv(file_path)
                if self.chunking_settings["use_chunking"] and self.chunking_settings["chunk_method"] == 'csv_row':
                    texts = self._process_csv_rows(df)
                    # Save chunks separately
                    chunks_pickle_path = processing_dir / "chunks.pkl"
                    with open(chunks_pickle_path, 'wb') as f:
                        pickle.dump(texts, f)
                    logger.info(f"Saved chunks to {chunks_pickle_path}")
                else:
                    texts = df.apply(lambda row: ', '.join([f"{col}: {val}" for col, val in row.items()]), axis=1).tolist()
            else:
                texts = self.file_type_manager.read_file(file_path)
                if self.chunking_settings["use_chunking"]:
                    texts = self._create_chunks(texts)
                    # Save chunks separately
                    chunks_pickle_path = processing_dir / "chunks.pkl"
                    with open(chunks_pickle_path, 'wb') as f:
                        pickle.dump(texts, f)
                    logger.info(f"Saved chunks to {chunks_pickle_path}")

            logger.info(f"Processed dataset with {len(texts)} chunks/rows")

            model_info = {
                "model_type": 'watson' if self.model_name in self.WATSON_MODELS else 'sentence_transformer',
                "model_name": self.model_name
            }
            embeddings = self.generate_embeddings(texts, model_info)
            logger.info(f"Generated {len(embeddings)} embeddings")

            faiss.normalize_L2(embeddings)

            index = faiss.IndexFlatIP(embeddings.shape[1])
            index.add(embeddings)

            faiss_index_path = processing_dir / "faiss_index.bin"
            faiss.write_index(index, str(faiss_index_path))
            logger.info(f"Saved FAISS index to {faiss_index_path}")

            embedding_pickle_path = processing_dir / "embeddings.pkl"
            with open(embedding_pickle_path, 'wb') as f:
                pickle.dump(embeddings, f)
            logger.info(f"Saved embeddings to {embedding_pickle_path}")

            data_pickle_path = processing_dir / "data.pkl"
            with open(data_pickle_path, 'wb') as f:
                pickle.dump(texts, f)
            logger.info(f"Saved processed data to {data_pickle_path}")

            model_info = {
                "model_type": 'watson' if isinstance(self.embeddings, WatsonxEmbeddings) else 'sentence_transformer',
                "model_name": self.model_name,
                "embedding_dimensions": embeddings.shape[1],
                "max_input_tokens": self.embeddings.max_seq_length if hasattr(self.embeddings, 'max_seq_length') else None,
                "chunking_settings": self.chunking_settings if self.chunking_settings["use_chunking"] else None
            }
            model_info_path = processing_dir / "embedding_model_info.json"
            with open(model_info_path, 'w') as f:
                json.dump(model_info, f, indent=4)
            logger.info(f"Saved model info to {model_info_path}")

            return {"message": "Dataset processed successfully", "model_info": model_info}

        except Exception as e:
            logger.error(f"Error processing dataset: {e}", exc_info=True)
            return {"message": "Error processing dataset", "error": str(e)}

    def _create_chunks(self, texts):
        chunk_method = self.chunking_settings.get('chunk_method', 'fixed_length')
        chunk_size = self.chunking_settings.get('chunk_size', 500)
        chunk_overlap = self.chunking_settings.get('chunk_overlap', 50)
        
        logger.info(f"Creating chunks with method: {chunk_method}")
        
        chunks = []
        if chunk_method == 'csv_row':
            chunks = texts  # For CSV, each row is already a separate item
        else:
            for text in texts:
                if chunk_method == 'fixed_length':
                    chunks.extend(self._fixed_length_chunks(text, chunk_size, chunk_overlap))
                elif chunk_method == 'sentence':
                    chunks.extend(self._sentence_chunks(text))
                elif chunk_method == 'paragraph':
                    chunks.extend(self._paragraph_chunks(text))
                else:
                    logger.warning(f"Unknown chunking method: {chunk_method}. Falling back to fixed_length.")
                    chunks.extend(self._fixed_length_chunks(text, chunk_size, chunk_overlap))
        
        logger.info(f"Created {len(chunks)} total chunks from {len(texts)} original texts")
        logger.info(f"Sample chunks:")
        for i in range(min(3, len(chunks))):
            logger.info(f"Chunk {i+1}: {chunks[i][:100]}...")  # Show first 100 chars of each sample chunk
        return chunks

    def _process_csv_rows(self, df):
        rows_per_chunk = self.chunking_settings.get('rows_per_chunk', 1)
        columns = self.chunking_settings.get('csv_columns', df.columns.tolist())
        
        chunks = []
        for i in range(0, len(df), rows_per_chunk):
            chunk_rows = df.iloc[i:i+rows_per_chunk]
            chunk_text = []
            for j, row in chunk_rows.iterrows():
                row_text = ', '.join([f"{col}: {row[col]}" for col in columns])
                chunk_text.append(f"Row {j+1}: {row_text}")
            chunks.append('\n'.join(chunk_text))
        
        logger.info(f"Created {len(chunks)} chunks from CSV data")
        logger.info(f"Sample chunk: {chunks[0][:200]}...")  # Log a sample chunk for verification
        return chunks

    def _fixed_length_chunks(self, text, chunk_size, chunk_overlap):
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - chunk_overlap
        return chunks

    def _sentence_chunks(self, text):
        # Simple sentence splitting using periods, question marks, and exclamation points
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        return [sentence.strip() for sentence in sentences if sentence.strip()]

    def _paragraph_chunks(self, text):
        # Simple paragraph splitting using double newlines
        paragraphs = text.split('\n\n')
        return [paragraph.strip() for paragraph in paragraphs if paragraph.strip()]

    def list_datasets_names(self):
        try:
            datasets_dir = Path("Datasets")
            datasets = [d.name for d in datasets_dir.iterdir() if d.is_dir()]
            logger.info(f"Found {len(datasets)} datasets")
            return {"datasets": datasets}
        except Exception as e:
            logger.error(f"Error listing datasets: {e}")
            return {"datasets": []}

    def list_datasets(self):
        try:
            datasets_dir = Path("Datasets")
            datasets = []
            for d in datasets_dir.iterdir():
                if d.is_dir():
                    for file in d.iterdir():
                        if file.is_file():
                            datasets.append(f"{d.name}{file.suffix}")
                            break  # Assume one file per dataset
            logger.info(f"Found {len(datasets)} datasets")
            return {"datasets": datasets}
        except Exception as e:
            logger.error(f"Error listing datasets: {e}")
            return {"datasets": []}

    def find_relevant_entries(self, query, dataset_name, use_chunking=False, similarity_threshold=0.5):
        logger.info(f"Finding relevant entries for query: '{query}' in dataset: {dataset_name}")
        dataset_dir = Path("Datasets") / dataset_name
        method_folder = "chunked" if use_chunking else "default"
        processing_dir = dataset_dir / method_folder

        embedding_pickle_path = processing_dir / "embeddings.pkl"
        data_pickle_path = processing_dir / "data.pkl"
        model_info_path = processing_dir / "embedding_model_info.json"

        with open(model_info_path, 'r') as f:
            model_info = json.load(f)
        logger.info(f"Loaded model info: {model_info}")

        with open(embedding_pickle_path, 'rb') as f:
            stored_embeddings = pickle.load(f)
        logger.info(f"Loaded stored embeddings with shape: {stored_embeddings.shape}")

        faiss_index_path = processing_dir / "faiss_index.bin"
        index = faiss.read_index(str(faiss_index_path))
        logger.info(f"Loaded FAISS index with {index.ntotal} vectors")

        original_data = pd.read_pickle(data_pickle_path)
        logger.info(f"Loaded original data with {len(original_data)} rows")

        query_vector = self.generate_embeddings([query], model_info)
        logger.info(f"Generated query embedding with shape: {query_vector.shape}")

        faiss.normalize_L2(query_vector)
        D, I = index.search(query_vector, index.ntotal)  # Search all vectors
        logger.info(f"Searched all {index.ntotal} vectors")

        relevant_indices = I[0][D[0] > similarity_threshold]
        relevant_similarities = D[0][D[0] > similarity_threshold]
        logger.info(f"Found {len(relevant_indices)} entries above similarity threshold {similarity_threshold}")

        if len(relevant_indices) == 0:
            logger.info("No relevant entries found above the similarity threshold")
            return []  # Return an empty list if no relevant entries are found

        if use_chunking:
            chunks_pickle_path = processing_dir / "chunks.pkl"
            if chunks_pickle_path.exists():
                with open(chunks_pickle_path, 'rb') as f:
                    chunks = pickle.load(f)
                relevant_entries = [chunks[i] for i in relevant_indices]
                logger.info(f"Using chunked data. Total chunks: {len(chunks)}, Relevant chunks: {len(relevant_entries)}")
                logger.info("Sample relevant chunks:")
                for i in range(min(3, len(relevant_entries))):
                    logger.info(f"Chunk {i+1}: {relevant_entries[i]}")
            else:
                logger.warning("Chunks file not found. Falling back to full entries.")
                relevant_entries = [original_data.iloc[i] if isinstance(original_data, pd.DataFrame) else original_data[i] for i in relevant_indices]
        else:
            relevant_entries = [original_data.iloc[i] if isinstance(original_data, pd.DataFrame) else original_data[i] for i in relevant_indices]
            logger.info(f"Using full entries. Relevant entries: {len(relevant_entries)}")

        # Sort entries by similarity (highest to lowest)
        sorted_entries = sorted(zip(relevant_entries, relevant_similarities), key=lambda x: x[1], reverse=True)
        relevant_entries = [entry for entry, _ in sorted_entries]

        formatted_entries = [self.format_entry(entry) for entry in relevant_entries]
        logger.info(f"Returning {len(formatted_entries)} formatted entries")
        return formatted_entries

    def format_entry(self, entry):
        if isinstance(entry, str):  # It's a chunk or a string entry
            return entry
        elif isinstance(entry, (list, np.ndarray)):
            return ', '.join([f"{val}" for val in entry])
        elif isinstance(entry, dict):
            return ', '.join([f"{key}: {value}" for key, value in entry.items()])
        elif isinstance(entry, pd.Series):
            return ', '.join([f"{key}: {value}" for key, value in entry.items()])
        else:
            return str(entry)  # Fallback for any other type