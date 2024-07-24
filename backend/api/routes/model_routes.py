import logging
import cv2
import os
import shutil
import uuid
import json
import asyncio
import torch
from fastapi.responses import JSONResponse
from fastapi import UploadFile, APIRouter, File, HTTPException, Query, Body, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from typing import Annotated, Dict, Any
import numpy as np
from backend.controlers.model_control import ModelControl
from backend.core.config import UPLOAD_IMAGE_DIR, UPLOAD_VID_DIR, UPLOAD_DATASET_DIR
from backend.data_utils.dataset_processor import process_dataset
from backend.data_utils.training_handler import handle_training_request

router = APIRouter()

model_control = ModelControl()

logger = logging.getLogger(__name__)

class PredictRequest(BaseModel):
    image_path: str

class InferenceRequest(BaseModel):
    model_id: str
    data: Annotated[dict | None, 
                    Field(
                        title="Data to be used for inference", 
                        description="Example: For sentiment analysis, it will be a sentence. For image classification, it will be an image path"
                    )]

class TrainRequest(BaseModel):
    model_id: str
    data: Annotated[dict | None, 
                    Field(
                        title="Data to be used for training", 
                        description="Example: Training parameters and dataset path"
                    )]

class ConfigureRequest(BaseModel):
    model_id: str
    data: Annotated[dict | None, 
                    Field(
                        title="Data to be used for configuring", 
                        description="Example: Configuration parameters"
                    )]

@router.post("/upload-image/")
async def upload_image(file: UploadFile = File(...)):
    try:
        # Generate a unique identifier for the image
        image_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1]
        file_path = os.path.join(UPLOAD_IMAGE_DIR, f"{image_id}.{file_extension}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Return the relative path instead of absolute path
        relative_file_path = os.path.relpath(file_path, UPLOAD_IMAGE_DIR)
        
        return {"image_id": image_id, "file_path": relative_file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint for uploading video
@router.post("/upload-video/")
async def upload_video(file: UploadFile = File(...)):
    try:
        # Generating unique identifier fo the video
        video_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1]
        file_path = os.path.join(UPLOAD_VID_DIR, f"{video_id}.{file_extension}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Return the relative path instead of absolute path
        relative_file_path = os.path.relpath(file_path, UPLOAD_VID_DIR)
        
        return {"video_id": video_id , "file_path": relative_file_path}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail= str(e))

@router.post("/upload-dataset/")
async def upload_dataset(file: UploadFile = File(...), model_id: str = Query(...)):
    dataset_dir = ""
    try:
        # Generate a unique identifier for the dataset
        dataset_id = str(uuid.uuid4())
        dataset_dir = os.path.join(UPLOAD_DATASET_DIR, dataset_id)

        # Save the uploaded file
        os.makedirs(dataset_dir, exist_ok=True)
        file_path = os.path.join(dataset_dir, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process the dataset
        result = process_dataset(file_path, dataset_dir, dataset_id)

        return result
    except Exception as e:
        logger.error(f"Error uploading dataset: {str(e)}")
        if os.path.exists(dataset_dir):
            shutil.rmtree(dataset_dir)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/active")
async def list_active_models():
    try:
        active_models = model_control.list_active_models()
        return {"active_models": active_models}
    except Exception as e:
        logger.error(f"Error listing active models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/load")
async def load_model(model_id: str = Query(...)):
    try:
        if model_control.load_model(model_id):
            return {"message": f"Model {model_id} loaded successfully"}
        else:
            raise HTTPException(status_code=400, detail=f"Model {model_id} could not be loaded")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/unload")
async def unload_model(model_id: str = Query(...)):
    try:
        if model_control.unload_model(model_id):
            return {"message": f"Model {model_id} unloaded successfully"}
        else:
            raise HTTPException(status_code=400, detail=f"Model {model_id} could not be unloaded")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/download-model")
async def download_model(model_id: str = Query(...), auth_token: str = Query(None)):
    try:
        success = model_control.download_model(model_id, auth_token)
        if success:
            return {"message": f"Model {model_id} downloaded successfully"}
        else:
            raise HTTPException(status_code=400, detail=f"Model {model_id} could not be downloaded")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/is-model-loaded")
async def is_model_loaded(model_id: str = Query(...)):
    try:
        is_loaded = model_control.is_model_loaded(model_id)
        if is_loaded:
            return {"message": f"Model {model_id} is loaded"}
        else:
            return {"message": f"Model {model_id} is not loaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/inference")
async def inference(inferenceRequest: InferenceRequest):
    try:
        return model_control.inference(jsonable_encoder(inferenceRequest))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train")
async def train_model(trainRequest: TrainRequest):
    try:
        return model_control.train_model(jsonable_encoder(trainRequest))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/configure")
async def configure_model(configureRequest: ConfigureRequest):
    try:
        return model_control.configure_model(jsonable_encoder(configureRequest))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-model")
async def delete_model(model_id: str = Query(...)):
    try:
        return model_control.delete_model(model_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @router.post("/train")
# async def train_model(
#     model_id: str = Query(...), 
#     epochs: int = Body(...), 
#     batch_size: int = Body(...), 
#     learning_rate: float = Body(...), 
#     dataset_id: str = Body(...),
#     imgsz: int = Body(640)
# ):
#     try:
#         result = handle_training_request(model_control, model_id, epochs, batch_size, learning_rate, dataset_id, imgsz)
#         return result
#     except ValueError as ve:
#         raise HTTPException(status_code=400, detail=str(ve))
#     except FileNotFoundError as fnf:
#         raise HTTPException(status_code=404, detail=str(fnf))
#     except Exception as e:
#         logger.error(f"Error during training: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

# Creating a web socket connection for real-time video and live webcam processing
# It will receives video frames as bytes, process it using the model and sends results back to user
@router.websocket("/ws/predict-live/{model_id}")
async def predict_live(websocket: WebSocket, model_id: str):
    await websocket.accept()
    try:
        if not model_control.is_model_loaded(model_id):
            await websocket.send_json({"error": f"Model {model_id} is not loaded. Please load the model first"})
            await websocket.close()
            return

        active_model = model_control.get_active_model(model_id)
        if not active_model:
            await websocket.send_json({"error": f"Model {model_id} is not found or not loaded"})
            await websocket.close()
            return

        conn = active_model['conn']
        
        while True:
            frame_data = await websocket.receive_bytes()
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                await websocket.send_json({"error": "Invalid frame data"})
                continue
            
            conn.send({"task": "inference", "data": {"video_frame": frame.tolist()}})
            prediction = conn.recv()
            
            await websocket.send_json(prediction)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in predict_live: {str(e)}")
        await websocket.send_json({"error": str(e)})
    finally:
        await websocket.close()

"""
    This route is used to predict the sentiment of a given sentence using the sentiment model
    This route requires further modification to work with different types of models
    This route is a sample route for Annotated parameters
"""
@router.post("/predict/sentiment/")
async def predict_sentiment(model_id: Annotated[str, "ID of the sentiment model"], sentence: Annotated[str, Body(embed=True)]):
    try:
        active_model = model_control.get_active_model(model_id)
        if not active_model:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found or not loaded")

        conn = active_model['conn']

        conn.send(f"sentimentPredict:{sentence}")
        prediction = conn.recv()

        return {"model_id": model_id, "input_sentence": sentence,"prediction": prediction}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    