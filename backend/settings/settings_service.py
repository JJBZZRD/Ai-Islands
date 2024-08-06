import asyncio
from backend.utils.watson_settings_manager import watson_settings
import logging
import torch
from backend.core.config import CONFIG_PATH
from backend.data_utils.json_handler import JSONHandler

logger = logging.getLogger(__name__)

class SettingsService:
    async def update_watson_settings(self, settings):
        if settings.api_key is not None:
            watson_settings.set("IBM_CLOUD_API_KEY", settings.api_key)
        
        if settings.project_id is not None:
            watson_settings.set("USER_PROJECT_ID", settings.project_id)
        
        if settings.location is not None:
            watson_settings.update_location(settings.location)
        
        return "Watson settings updated successfully"

    async def get_watson_settings(self):
        current_settings = watson_settings.get_all_settings()
        formatted_settings = {
            "api_key": current_settings['IBM_CLOUD_API_KEY'],
            "location": current_settings['IBM_CLOUD_MODELS_URL'].split('//')[1].split('.')[0],
            "project": current_settings['USER_PROJECT_ID']
        }
        return formatted_settings

    async def update_chunking_settings(self, settings):
        config = await self._read_config()
        config["chunking"] = settings.dict()
        await self._write_config(config)
        return "Chunking settings updated successfully"

    async def get_chunking_settings(self):
        config = await self._read_config()
        return config.get("chunking", {})

    async def set_hardware_preference(self, device: str):
        if device not in ["cpu", "gpu"]:
            raise ValueError("Invalid device. Choose 'cpu' or 'gpu'.")

        if device == "gpu" and not torch.cuda.is_available():
            raise ValueError("GPU is not available on this system.")

        config = await self._read_config()
        config["hardware"] = device
        await self._write_config(config)
        return f"Successfully set hardware to {device}"

    async def get_hardware_preference(self):
        config = await self._read_config()
        return config.get("hardware", "cpu")

    async def check_gpu(self):
        cuda_available = torch.cuda.is_available()
        cuda_version = torch.version.cuda if cuda_available else None
        cudnn_version = torch.backends.cudnn.version() if cuda_available else None
        return {
            "CUDA available": cuda_available,
            "CUDA version": cuda_version,
            "cuDNN version": cudnn_version
        }

    async def _read_config(self):
        try:
            return await asyncio.to_thread(JSONHandler.read_json, CONFIG_PATH)
        except FileNotFoundError:
            return {"hardware": "cpu", "chunking": {}}

    async def _write_config(self, config):
        await asyncio.to_thread(JSONHandler.write_json, CONFIG_PATH, config)