import logging
import os
import shutil
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from backend.core.config import UPLOAD_DATASET_DIR, DATASETS_DIR
from backend.data_utils.dataset_processor import process_dataset
from pydantic import BaseModel
from backend.utils.dataset_utility import DatasetManagement
from typing import List
from pathlib import Path
import json
from backend.utils.file_type_manager import FileTypeManager

logger = logging.getLogger(__name__)

class DatasetProcessRequest(BaseModel):
    file_path: str
    model_name: str = None

class DataRouter:
    def __init__(self):
        self.router = APIRouter()

        # Define routes
        self.router.add_api_route("/upload-dataset", self.upload_dataset, methods=["POST"])
        self.router.add_api_route("/upload-image-dataset/", self.upload_image_dataset, methods=["POST"])
        self.router.add_api_route("/process-dataset", self.process_dataset, methods=["POST"])
        self.router.add_api_route("/list-datasets", self.list_datasets, methods=["GET"])
        self.router.add_api_route("/list-datasets-names", self.list_datasets_names, methods=["GET"])
        self.router.add_api_route("/available-models", self.get_available_models, methods=["GET"])
        self.router.add_api_route("/preview-dataset", self.preview_dataset, methods=["GET"])
        self.router.add_api_route("/dataset-processing-status", self.get_dataset_processing_status, methods=["GET"])
        self.router.add_api_route("/delete-dataset", self.delete_dataset, methods=["DELETE"])
        self.router.add_api_route("/dataset-processing-info", self.get_dataset_processing_info, methods=["GET"])
    
    async def upload_dataset(self, request: DatasetProcessRequest):
        try:
            source_path = Path(request.file_path)
            if not source_path.exists():
                raise FileNotFoundError(f"File not found: {request.file_path}")

            dataset_name = source_path.stem
            dataset_folder = Path(DATASETS_DIR) / dataset_name
            dataset_folder.mkdir(parents=True, exist_ok=True)

            destination_path = dataset_folder / source_path.name
            shutil.copy2(source_path, destination_path)

            return {"message": f"Dataset uploaded successfully to {destination_path}"}
        except Exception as e:
            logger.error(f"Error uploading dataset: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def upload_image_dataset(self, file: UploadFile = File(...), model_id: str = Query(...)):
        dataset_dir = ""
        try:
            dataset_id = str(uuid.uuid4())
            dataset_dir = os.path.join(UPLOAD_DATASET_DIR, dataset_id)

            os.makedirs(dataset_dir, exist_ok=True)
            file_path = os.path.join(dataset_dir, file.filename)

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            result = process_dataset(file_path, dataset_dir, dataset_id)

            return result
        except Exception as e:
            logger.error(f"Error uploading dataset: {str(e)}")
            if os.path.exists(dataset_dir):
                shutil.rmtree(dataset_dir)
            raise HTTPException(status_code=500, detail=str(e))

    async def process_dataset(self, request: DatasetProcessRequest):
        try:
            dataset_manager = DatasetManagement(model_name=request.model_name)
            file_path = Path(request.file_path)
            result = dataset_manager.process_dataset(file_path)
            return result
        except Exception as e:
            logger.error(f"Error processing dataset: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error processing dataset: {str(e)}")

    async def list_datasets(self):
        try:
            dataset_manager = DatasetManagement()
            return dataset_manager.list_datasets()
        except Exception as e:
            logger.error(f"Error listing datasets: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error listing datasets: {str(e)}")
    
    async def list_datasets_names(self):
        try:
            dataset_manager = DatasetManagement()
            return dataset_manager.list_datasets_names()
        except Exception as e:
            logger.error(f"Error listing datasets: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error listing datasets: {str(e)}")

    async def get_available_models(self):
        try:
            return DatasetManagement.get_available_models()
        except Exception as e:
            logger.error(f"Error getting available models: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error getting available models: {str(e)}")

    async def preview_dataset(self, dataset_name: str):
        try:
            dataset_path = Path(DATASETS_DIR) / dataset_name
            file_type_manager = FileTypeManager()
            
            if not dataset_path.exists():
                raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

            for file in dataset_path.iterdir():
                if file.is_file():
                    preview_content = file_type_manager.read_file(file)
                    file_type = file.suffix.lower()
                    if file_type == '.csv' and preview_content:
                        # Preserve CSV formatting without processing
                        preview_content = preview_content[:10]
                    return {
                        "file_type": file_type,
                        "content": preview_content[:10] if isinstance(preview_content, list) else [preview_content[:1000]]
                    }

            raise FileNotFoundError(f"No files found in dataset directory: {dataset_path}")
        except Exception as e:
            logger.error(f"Error previewing dataset: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_dataset_processing_status(self, dataset_name: str):
        try:
            dataset_path = Path(DATASETS_DIR) / dataset_name
            if not dataset_path.exists():
                raise FileNotFoundError(f"Dataset not found: {dataset_name}")

            default_processed = (dataset_path / "default").exists()
            chunked_processed = (dataset_path / "chunked").exists()

            return {
                "default_processed": default_processed,
                "chunked_processed": chunked_processed
            }
        except Exception as e:
            logger.error(f"Error getting dataset processing status: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def delete_dataset(self, dataset_name: str):
        try:
            dataset_path = Path(DATASETS_DIR) / dataset_name
            if not dataset_path.exists():
                raise FileNotFoundError(f"Dataset not found: {dataset_name}")

            shutil.rmtree(dataset_path)
            return {"message": f"Dataset {dataset_name} deleted successfully"}
        except Exception as e:
            logger.error(f"Error deleting dataset: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_dataset_processing_info(self, dataset_name: str, processing_type: str):
        try:
            dataset_path = Path(DATASETS_DIR) / dataset_name / processing_type
            info_file = dataset_path / "embedding_model_info.json"
            
            if not info_file.exists():
                raise FileNotFoundError(f"Processing info not found for {dataset_name} ({processing_type})")

            with open(info_file, 'r') as f:
                info = json.load(f)

            if processing_type == "chunked" and "chunking_settings" in info:
                chunk_method = info["chunking_settings"].get("chunk_method", "")
                if chunk_method in ["fixed_length", "sentence", "paragraph"]:
                    info["chunking_settings"] = {
                        "use_chunking": True,
                        "chunk_method": chunk_method,
                        "chunk_size": info["chunking_settings"].get("chunk_size", 1000),
                        "chunk_overlap": info["chunking_settings"].get("chunk_overlap", 100),
                    }
                elif chunk_method == "csv_row":
                    info["chunking_settings"] = {
                        "use_chunking": True,
                        "chunk_method": "csv_row",
                        "rows_per_chunk": info["chunking_settings"].get("rows_per_chunk", 1),
                        "csv_columns": info["chunking_settings"].get("csv_columns", []),
                    }

            return info
        except Exception as e:
            logger.error(f"Error getting dataset processing info: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))