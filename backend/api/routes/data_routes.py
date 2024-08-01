import logging
import os
import shutil
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from backend.core.config import UPLOAD_DATASET_DIR
from backend.data_utils.dataset_processor import process_dataset
from pydantic import BaseModel
from backend.utils.dataset_utility import DatasetManagement
from typing import List
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class ChunkingSettings(BaseModel):
    use_chunking: bool = False
    chunk_size: int = 500
    chunk_overlap: int = 50
    chunk_method: str = 'fixed_length'
    rows_per_chunk: int = 1
    csv_columns: List[str] = []

class DatasetProcessRequest(BaseModel):
    file_path: str
    model_name: str = None

class DataRouter:
    def __init__(self):
        self.router = APIRouter()

        # Define routes
        self.router.add_api_route("/upload-dataset/", self.upload_dataset, methods=["POST"])
        self.router.add_api_route("/process_dataset", self.process_dataset, methods=["POST"])
        self.router.add_api_route("/list_datasets", self.list_datasets, methods=["GET"])
        self.router.add_api_route("/available_models", self.get_available_models, methods=["GET"])

    async def upload_dataset(self, file: UploadFile = File(...), model_id: str = Query(...)):
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

    async def get_available_models(self):
        try:
            return DatasetManagement.get_available_models()
        except Exception as e:
            logger.error(f"Error getting available models: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error getting available models: {str(e)}")