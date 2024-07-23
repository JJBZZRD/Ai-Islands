from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.utils.dataset_utility import DatasetManagement
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class DatasetProcessRequest(BaseModel):
    file_path: str
    model_name: str = None

@router.post("/process_dataset")
async def process_dataset(request: DatasetProcessRequest):
    try:
        # Initialize DatasetManagement with just the model_name
        dataset_manager = DatasetManagement(model_name=request.model_name)
        
        # Process the dataset
        result = dataset_manager.process_dataset(request.file_path)
        return result
    except Exception as e:
        logger.error(f"Error processing dataset: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing dataset: {str(e)}")

@router.get("/list_datasets")
async def list_datasets():
    try:
        dataset_manager = DatasetManagement()
        return dataset_manager.list_datasets()
    except Exception as e:
        logger.error(f"Error listing datasets: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing datasets: {str(e)}")

@router.get("/available_models")
async def get_available_models():
    try:
        return DatasetManagement.get_available_models()
    except Exception as e:
        logger.error(f"Error getting available models: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting available models: {str(e)}")