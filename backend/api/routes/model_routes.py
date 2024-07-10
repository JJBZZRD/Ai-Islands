"""from fastapi import  UploadFile, APIRouter, File
from controlers.model_control import ModelControl
from core.config import UPLOAD_DIR
import os
import shutil

router = APIRouter()

model_control = ModelControl()

@router.post("/upload-image/")
async def upload_image(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Predict using the model
    prediction = model_control.model.predibutct(file_path)
    
    return {"filename": file.filename, "prediction": prediction}

@router.get("/models")
async def list_models():
    return {"message": "List of models"}

@router.post("/models/load")
async def load_model(model_id: str):
    return {"message": f"Loading model {model_id}"}

@router.post("/download-model/{model_id}")
async def download_model(model_id: str):
    try:
        model_control.download_model(model_id)
        return {"message": f"Model {model_id} downloaded successfully"}
    except Exception as e:
        return {"error": str(e)}
    
@router.get("/is-model-loaded/")
async def is_model_loaded():
    if model_control.model.model is not None:
        return {"message": "Model is loaded"}
    else:
        return {"message": "Model is not loaded"}"""
        

import logging
from fastapi import UploadFile, APIRouter, File, HTTPException, Query, Body
from backend.controlers.model_control import ModelControl
from backend.core.config import UPLOAD_DIR, DOWNLOADED_MODELS_PATH
import os
import shutil
import uuid
from typing import Dict, Any
import json
from pydantic import BaseModel

router = APIRouter()

model_control = ModelControl()

logger = logging.getLogger(__name__)

class PredictRequest(BaseModel):
    image_path: str

@router.post("/upload-image/")
async def upload_image(file: UploadFile = File(...)):
    try:
        # Generate a unique identifier for the image
        image_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1]
        file_path = os.path.join(UPLOAD_DIR, f"{image_id}.{file_extension}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Return the relative path instead of absolute path
        relative_file_path = os.path.relpath(file_path, UPLOAD_DIR)
        
        return {"image_id": image_id, "file_path": relative_file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/active")
async def list_active_models():
    try:
        active_models = model_control.list_active_models()
        return {"active_models": active_models}
    except Exception as e:
        logger.error(f"Error listing active models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/load/{model_id}")
async def load_model(model_id: str):
    try:
        if model_control.load_model(model_id):
            return {"message": f"Model {model_id} loaded successfully"}
        else:
            raise HTTPException(status_code=400, detail=f"Model {model_id} could not be loaded")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/unload/{model_id}")
async def unload_model(model_id: str):
    try:
        if model_control.unload_model(model_id):
            return {"message": f"Model {model_id} unloaded successfully"}
        else:
            raise HTTPException(status_code=400, detail=f"Model {model_id} could not be unloaded")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/download-model/{model_id}")
async def download_model(model_id: str):
    try:
        success = model_control.download_model(model_id)
        if success:
            return {"message": f"Model {model_id} downloaded successfully"}
        else:
            HTTPException(status_code=400, detail=f"Model {model_id} could not be downloaded")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/is-model-loaded/{model_id}")
async def is_model_loaded(model_id: str):
    try:
        is_loaded = model_control.is_model_loaded(model_id)
        if is_loaded:
            return {"message": f"Model {model_id} is loaded"}
        else:
            return {"message": f"Model {model_id} is not loaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/predict/")
async def predict(model_id: str = Query(...), request_payload: Dict[str, Any] = Body(...)):
    try:
        active_model = model_control.get_active_model(model_id)
        if not active_model:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found or not loaded")

        conn = active_model['conn']
        
        # Adjust the image path to be absolute path before sending to the model process
        if "image_path" in request_payload:
            request_payload["image_path"] = os.path.join(UPLOAD_DIR, request_payload["image_path"])

        conn.send(f"predict:{json.dumps(request_payload)}")
        prediction = conn.recv()

        return {"model_id": model_id, "prediction": prediction}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

