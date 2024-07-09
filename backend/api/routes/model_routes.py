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
from fastapi import UploadFile, APIRouter, File, HTTPException, Query 
from backend.controlers.model_control import ModelControl
from backend.core.config import UPLOAD_DIR
import os
import shutil
import uuid

router = APIRouter()

model_control = ModelControl()

logger = logging.getLogger(__name__)

@router.post("/upload-image/")
async def upload_image(file: UploadFile = File(...)):
    try:
        # Generate a unique identifier for the image
        image_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1]
        file_path = os.path.join(UPLOAD_DIR, f"{image_id}.{file_extension}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {"image_id": image_id, "file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/active")
async def list_active_models():
    try:
        active_models = model_control.list_active_models()
        return {"active_models": active_models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/load/{model_id}")
async def load_model(model_id: str):
    try:
        model_control.load_model(model_id)
        return {"message": f"Model {model_id} loaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/unload/{model_id}")
async def unload_model(model_id: str):
    try:
        model_control.unload_model(model_id)
        return {"message": f"Model {model_id} unloaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/download-model/{model_id}")
async def download_model(model_id: str):
    try:
        model_control.download_model(model_id)
        return {"message": f"Model {model_id} downloaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/is-model-loaded/{model_id}")
async def is_model_loaded(model_id: str):
    try:
        if model_control.is_model_loaded(model_id):
            return {"message": f"Model {model_id} is loaded"}
        else:
            return {"message": f"Model {model_id} is not loaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/predict/")
async def predict(model_id: str = Query(...), image_id: str = Query(...)):
    try:
        # Find the image file path
        image_files = [f for f in os.listdir(UPLOAD_DIR) if f.startswith(image_id)]
        if not image_files:
            raise HTTPException(status_code=404, detail=f"Image with ID {image_id} not found")
        
        file_path = os.path.join(UPLOAD_DIR, image_files[0])
        
        # Find the specified model
        model_entry = next((m for m in model_control.models if m['model_id'] == model_id), None)
        if not model_entry:
            # Load the model if not already loaded
            if not model_control.load_model(model_id):
                raise HTTPException(status_code=400, detail=f"Model {model_id} could not be loaded")

            model_entry = next((m for m in model_control.models if m['model_id'] == model_id), None)
            if not model_entry:
                raise HTTPException(status_code=500, detail=f"Model {model_id} could not be found after loading")

        prediction = model_entry['model'].predict(file_path)
        
        # Ensure prediction is serializable
        prediction_serializable = prediction.tolist() if hasattr(prediction, 'tolist') else prediction
        
        return {"filename": image_files[0], "prediction": prediction_serializable}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))