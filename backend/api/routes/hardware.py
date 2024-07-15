from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.settings.settings import set_hardware_preference, get_hardware_preference
import torch

router = APIRouter()

class HardwareRequest(BaseModel):
    device: str

@router.post("/set-hardware")
async def set_hardware(hardware_request: HardwareRequest):
    try:
        device = hardware_request.device
        set_hardware_preference(device)
        return {"message": f"Successfully set hardware to {device}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/get-hardware")
async def get_hardware():
    try:
        hardware = get_hardware_preference()
        return {"hardware": hardware}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/check-gpu")
async def check_gpu():
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