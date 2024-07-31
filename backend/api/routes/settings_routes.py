from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.utils.watson_settings_manager import watson_settings
from typing import List
from pathlib import Path
import logging
import json

logger = logging.getLogger(__name__)

class WatsonSettings(BaseModel):
    api_key: str = None
    project_id: str = None
    location: str = None

class ChunkingSettings(BaseModel):
    use_chunking: bool = False
    chunk_size: int = 500
    chunk_overlap: int = 50
    chunk_method: str = 'fixed_length'
    rows_per_chunk: int = 1
    csv_columns: List[str] = []

class SettingsRouter:
    def __init__(self):
        self.router = APIRouter()
        self.router.add_api_route("/update_watson_settings", self.update_watson_settings, methods=["POST"])
        self.router.add_api_route("/get_watson_settings", self.get_watson_settings, methods=["GET"])
        self.router.add_api_route("/update_chunking_settings", self.update_chunking_settings, methods=["POST"])

    async def update_watson_settings(self, settings: WatsonSettings):
        try:
            if settings.api_key is not None:
                watson_settings.set("IBM_CLOUD_API_KEY", settings.api_key)
            
            if settings.project_id is not None:
                watson_settings.set("USER_PROJECT_ID", settings.project_id)
            
            if settings.location is not None:
                watson_settings.update_location(settings.location)
            
            return {"message": "Watson settings updated successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating Watson settings: {str(e)}")

    async def get_watson_settings(self):
        try:
            current_settings = watson_settings.get_all_settings()
            # Mask the API key for security
            if current_settings['IBM_CLOUD_API_KEY']:
                current_settings['IBM_CLOUD_API_KEY'] = current_settings['IBM_CLOUD_API_KEY'][:5] + '*' * 10
            return current_settings
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving Watson settings: {str(e)}")

    async def update_chunking_settings(self, settings: ChunkingSettings):
        try:
            config_path = Path("backend/settings/chunking_settings.json")
            with open(config_path, 'w') as f:
                json.dump(settings.dict(), f, indent=2)
            return {"message": "Chunking settings updated successfully"}
        except Exception as e:
            logger.error(f"Error updating chunking settings: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error updating chunking settings: {str(e)}")