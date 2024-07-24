from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.settings.settings import set_hardware_preference, get_hardware_preference
import torch

class HardwareRequest(BaseModel):
    device: str

class HardwareRouter:
    def __init__(self):
        self.router = APIRouter()
        self.router.add_api_route("/set-hardware", self.set_hardware, methods=["POST"])
        self.router.add_api_route("/get-hardware", self.get_hardware, methods=["GET"])
        self.router.add_api_route("/check-gpu", self.check_gpu, methods=["GET"])

    async def set_hardware(self, hardware_request: HardwareRequest):
        try:
            device = hardware_request.device
            set_hardware_preference(device)
            return {"message": f"Successfully set hardware to {device}"}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def get_hardware(self):
        try:
            hardware = get_hardware_preference()
            return {"hardware": hardware}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def check_gpu(self):
        try:
            cuda_available = torch.cuda.is_available()
            cuda_version = torch.version.cuda if cuda_available else None
            cudnn_version = torch.backends.cudnn.version() if cuda_available else None
            return {
                "CUDA available": cuda_available,
                "CUDA version": cuda_version,
                "cuDNN version": cudnn_version
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))