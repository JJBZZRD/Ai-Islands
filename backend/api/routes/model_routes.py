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
        

from fastapi import UploadFile, APIRouter, File, HTTPException
from backend.controlers.model_control import ModelControl
from backend.core.config import UPLOAD_DIR
import os
import shutil

router = APIRouter()

model_control = ModelControl()

@router.post("/upload-image/")
async def upload_image(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Predict using the model
        if model_control.model is None:
            raise HTTPException(status_code=400, detail="Model is not loaded")

        prediction = model_control.model.predict(file_path)
        
        return {"filename": file.filename, "prediction": prediction}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def list_models():
    try:
        models = model_control.list_active_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/load")
async def load_model(model_id: str):
    try:
        model_control.load_model(model_id)
        return {"message": f"Model {model_id} loaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/download-model/{model_id}")
async def download_model(model_id: str):
    try:
        model_control.download_model(model_id)
        return {"message": f"Model {model_id} downloaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/is-model-loaded/")
async def is_model_loaded():
    try:
        if model_control.model and model_control.model.model is not None:
            return {"message": "Model is loaded"}
        else:
            return {"message": "Model is not loaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    
