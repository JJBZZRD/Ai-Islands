from backend.utils.watson_settings_manager import watson_settings
from pathlib import Path
import json
import logging
import torch
from backend.core.config import CONFIG_PATH
from backend.data_utils.json_handler import JSONHandler

logger = logging.getLogger(__name__)

class SettingsService:
    def update_watson_settings(self, settings):
        if settings.api_key is not None:
            watson_settings.set("IBM_CLOUD_API_KEY", settings.api_key)
        
        if settings.project_id is not None:
            watson_settings.set("USER_PROJECT_ID", settings.project_id)
        
        if settings.location is not None:
            watson_settings.update_location(settings.location)
        
        return "Watson settings updated successfully"

    def get_watson_settings(self):
        current_settings = watson_settings.get_all_settings()
        if current_settings['IBM_CLOUD_API_KEY']:
            current_settings['IBM_CLOUD_API_KEY'] = current_settings['IBM_CLOUD_API_KEY'][:5] + '*' * 10
        return current_settings

    def update_chunking_settings(self, settings):
        config_path = Path("backend/settings/chunking_settings.json")
        with open(config_path, 'w') as f:
            json.dump(settings.dict(), f, indent=2)
        return "Chunking settings updated successfully"

    def set_hardware_preference(self, device: str):
        if device not in ["cpu", "gpu"]:
            raise ValueError("Invalid device. Choose 'cpu' or 'gpu'.")

        if device == "gpu" and not torch.cuda.is_available():
            raise ValueError("GPU is not available on this system.")

        config = self._read_config()
        config["hardware"] = device
        self._write_config(config)
        return f"Successfully set hardware to {device}"

    def get_hardware_preference(self):
        config = self._read_config()
        return config.get("hardware", "cpu")

    def check_gpu(self):
        cuda_available = torch.cuda.is_available()
        cuda_version = torch.version.cuda if cuda_available else None
        cudnn_version = torch.backends.cudnn.version() if cuda_available else None
        return {
            "CUDA available": cuda_available,
            "CUDA version": cuda_version,
            "cuDNN version": cudnn_version
        }

    def _read_config(self):
        try:
            return JSONHandler.read_json(CONFIG_PATH)
        except FileNotFoundError:
            return {"hardware": "cpu"}

    def _write_config(self, config):
        JSONHandler.write_json(CONFIG_PATH, config)