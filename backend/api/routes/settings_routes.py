from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from backend.settings.settings_service import SettingsService
import torch

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

class HardwareRequest(BaseModel):
    device: str

class SettingsRouter:
    def __init__(self):
        self.router = APIRouter()
        self.service = SettingsService()
        self.router.add_api_route("/update_watson_settings", self.update_watson_settings, methods=["POST"])
        self.router.add_api_route("/get_watson_settings", self.get_watson_settings, methods=["GET"])
        self.router.add_api_route("/update_chunking_settings", self.update_chunking_settings, methods=["POST"])
        # Add new hardware-related routes
        self.router.add_api_route("/set-hardware", self.set_hardware, methods=["POST"])
        self.router.add_api_route("/get-hardware", self.get_hardware, methods=["GET"])
        self.router.add_api_route("/check-gpu", self.check_gpu, methods=["GET"])

    async def update_watson_settings(self, settings: WatsonSettings):
        try:
            result = await self.service.update_watson_settings(settings)
            return {"message": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_watson_settings(self):
        try:
            return await self.service.get_watson_settings()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def update_chunking_settings(self, settings: ChunkingSettings):
        try:
            result = await self.service.update_chunking_settings(settings)
            return {"message": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def set_hardware(self, hardware_request: HardwareRequest):
        try:
            result = await self.service.set_hardware_preference(hardware_request.device)
            return {"message": result}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def get_hardware(self):
        try:
            hardware = await self.service.get_hardware_preference()
            return {"hardware": hardware}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def check_gpu(self):
        try:
            gpu_info = await self.service.check_gpu()
            return gpu_info
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))