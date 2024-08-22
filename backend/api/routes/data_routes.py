import logging
import os
import shutil
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from backend.core.config import UPLOAD_DATASET_DIR, DATASETS_DIR
from backend.data_utils.dataset_processor import process_dataset
from pydantic import BaseModel
from backend.utils.dataset_utility import DatasetManagement
from backend.utils.dataset_management import DatasetFileManagement
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
            dataset_file_management = DatasetFileManagement()
            result = dataset_file_management.upload_dataset(request.file_path)
            return result
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
            dataset_file_management = DatasetFileManagement()
            return dataset_file_management.list_datasets()
        except Exception as e:
            logger.error(f"Error listing datasets: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error listing datasets: {str(e)}")
    
    async def list_datasets_names(self):
        try:
            dataset_file_management = DatasetFileManagement()
            return dataset_file_management.list_datasets_names()
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
            dataset_file_management = DatasetFileManagement()
            result = dataset_file_management.preview_dataset(dataset_name)
            return result
        except Exception as e:
            logger.error(f"Error previewing dataset: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_dataset_processing_status(self, dataset_name: str):
        try:
            dataset_file_management = DatasetFileManagement()
            result = dataset_file_management.get_dataset_processing_status(dataset_name)
            return result
        except Exception as e:
            logger.error(f"Error getting dataset processing status: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def delete_dataset(self, dataset_name: str):
        try:
            dataset_file_management = DatasetFileManagement()
            result = dataset_file_management.delete_dataset(dataset_name)
            return result
        except Exception as e:
            logger.error(f"Error deleting dataset: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_dataset_processing_info(self, dataset_name: str, processing_type: str):
        try:
            dataset_file_management = DatasetFileManagement()
            result = dataset_file_management.get_dataset_processing_info(dataset_name, processing_type)
            return result
        except Exception as e:
            logger.error(f"Error getting dataset processing info: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))