from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.utils.dataset_utility import DatasetManagement
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ChunkingSettings(BaseModel):
    use_chunking: bool = False
    chunk_size: int = 500
    chunk_overlap: int = 50
    chunk_method: str = 'fixed_length'

class DatasetProcessRequest(BaseModel):
    file_path: str
    model_name: str = None

@router.post("/process_dataset")
async def process_dataset(request: DatasetProcessRequest):
    try:
        # Load chunking settings from the JSON file
        config_path = Path("backend/settings/chunking_settings.json")
        with open(config_path, 'r') as f:
            chunking_settings = json.load(f)

        dataset_manager = DatasetManagement(model_name=request.model_name)
        result = dataset_manager.process_dataset(request.file_path, chunking_settings=chunking_settings)
        return result
    except Exception as e:
        logger.error(f"Error processing dataset: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing dataset: {str(e)}")

@router.post("/update_chunking_settings")
async def update_chunking_settings(settings: ChunkingSettings):
    try:
        config_path = Path("backend/settings/chunking_settings.json")
        with open(config_path, 'w') as f:
            json.dump(settings.dict(), f, indent=2)
        return {"message": "Chunking settings updated successfully"}
    except Exception as e:
        logger.error(f"Error updating chunking settings: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating chunking settings: {str(e)}")

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