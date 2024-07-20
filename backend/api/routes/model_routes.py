import logging
import cv2
from fastapi import UploadFile, APIRouter, File, HTTPException, Query, Body, WebSocket, WebSocketDisconnect
from backend.controlers.model_control import ModelControl
from backend.core.config import DOWNLOADED_MODELS_PATH, UPLOAD_IMAGE_DIR, UPLOAD_VID_DIR, UPLOAD_DATASET_DIR
from backend.data_utils.dataset_validation import validate_dataset
from backend.data_utils.yaml_generator import generate_yolo_yaml
from backend.data_utils.obj_generator import create_obj_data
from backend.data_utils.txt_generator import create_txt_files
from backend.controlers.library_control import LibraryControl
from backend.data_utils.zip_utils import extract_zip, move_files_from_subdirectory_if_present
from backend.data_utils.yaml_generator import generate_yolo_yaml
from backend.data_utils.obj_generator import create_obj_data
import os
import shutil
import uuid
from typing import Dict, Any
import json
from pydantic import BaseModel, Field
from typing import Annotated
import numpy as np
import asyncio
import torch
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import zipfile

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

def log_directory_structure(directory: str, message: str):
    for root, dirs, files in os.walk(directory):
        logger.debug(f"{message} - Directory structure: {root}, Directories: {dirs}, Files: {files}")


@router.post("/upload-dataset/")
async def upload_dataset(file: UploadFile = File(...), model_id: str = Query(...)):
    dataset_dir = ""
    try:
        # Generate a unique identifier for the dataset
        dataset_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1]
        dataset_dir = os.path.join(UPLOAD_DATASET_DIR, dataset_id)

        # Save the uploaded file
        os.makedirs(dataset_dir, exist_ok=True)
        file_path = os.path.join(dataset_dir, f"{dataset_id}.{file_extension}")

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Extract the dataset if it's a zip file
        if file_extension == 'zip':
            extract_zip(file_path, dataset_dir)
            move_files_from_subdirectory_if_present(dataset_dir)

        # Log the directory structure after extraction
        log_directory_structure(dataset_dir, "After extraction")

        # Generate train.txt and val.txt files
        create_txt_files(dataset_dir)
        logger.debug("Generated train.txt and val.txt files")

        # Read class names from obj.names file
        obj_names_path = os.path.join(dataset_dir, 'obj.names')
        if os.path.exists(obj_names_path):
            with open(obj_names_path, 'r') as f:
                class_names = [line.strip() for line in f.readlines()]
        else:
            raise HTTPException(status_code=400, detail="obj.names file not found")
        
        # Generate obj.data file
        create_obj_data(dataset_dir, len(class_names))
        logger.debug("Generated obj.data file")

        # Generate YAML file
        yaml_path = os.path.join(dataset_dir, f"{dataset_id}.yaml")
        generate_yolo_yaml(dataset_dir, yaml_path, class_names)
        logger.debug("Generated YAML file")

        # Log the directory structure after generating all files
        log_directory_structure(dataset_dir, "After generating all files")

        return {"dataset_id": dataset_id, "dataset_path": dataset_dir}
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
async def train_model(
    model_id: str = Query(...), 
    epochs: int = Body(...), 
    batch_size: int = Body(...), 
    learning_rate: float = Body(...), 
    dataset_id: str = Body(...),
    imgsz: int = Body(640)
):
    try:
        if epochs <= 0 or batch_size <= 0 or learning_rate <= 0:
            raise HTTPException(status_code=400, detail="Invalid training parameters")

        dataset_path = os.path.join(UPLOAD_DATASET_DIR, dataset_id)
        if not os.path.exists(dataset_path):
            raise HTTPException(status_code=400, detail="Dataset not found")

        yaml_path = os.path.join(dataset_path, f"{dataset_id}.yaml")
        if not os.path.exists(yaml_path):
            raise HTTPException(status_code=400, detail="YAML configuration file not found")

        train_txt_path = os.path.abspath(os.path.join(dataset_path, 'train.txt'))
        val_txt_path = os.path.abspath(os.path.join(dataset_path, 'val.txt'))

        # Log paths and YAML contents
        logger.debug(f"YAML Path: {yaml_path}")
        with open(yaml_path, 'r') as f:
            yaml_contents = f.read()
        logger.debug(f"YAML Contents: {yaml_contents}")
        
        # Log existence of train.txt and val.txt using absolute paths
        logger.debug(f"Checking paths: train.txt -> {train_txt_path}, val.txt -> {val_txt_path}")
        
        # Check for hidden characters or unexpected whitespace
        def check_hidden_chars(file_path):
            with open(file_path, 'rb') as f:
                content = f.read()
            if b'\0' in content:
                logger.error(f"Hidden characters found in {file_path}")
                return True
            return False
        
        # Verify file existence and content
        def verify_file(file_path):
            if not os.path.exists(file_path):
                logger.error(f"{file_path} does not exist")
                return False
            if check_hidden_chars(file_path):
                raise HTTPException(status_code=400, detail=f"{file_path} contains hidden characters")
            with open(file_path, 'r') as f:
                content = f.read()
            if not content.strip():
                logger.error(f"{file_path} is empty")
                return False
            logger.debug(f"Contents of {file_path}: {content[:1000]}...")  # Print first 1000 chars
            return True
        
        if not verify_file(train_txt_path) or not verify_file(val_txt_path):
            raise HTTPException(status_code=400, detail="train.txt or val.txt validation failed")

        # Log the current working directory
        current_working_dir = os.getcwd()
        logger.debug(f"Current working directory: {current_working_dir}")

        # Print directory listing
        dir_listing = os.listdir(dataset_path)
        logger.debug(f"Directory listing for {dataset_path}: {dir_listing}")

        training_params = {
            "data": yaml_path,
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "imgsz": imgsz
        }
        result = model_control.train_model(model_id, training_params)
        return result
    except Exception as e:
        logger.error(f"Error during training: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
async def predict(model_id: Annotated[str, "ID of the sentiment model"], sentence: Annotated[str, Body(embed=True)]):
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
    