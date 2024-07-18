import logging
import cv2
from fastapi import UploadFile, APIRouter, File, HTTPException, Query, Body, WebSocket, WebSocketDisconnect
from backend.controlers.model_control import ModelControl
from backend.core.config import DOWNLOADED_MODELS_PATH, UPLOAD_IMAGE_DIR, UPLOAD_VID_DIR, UPLOAD_DATASET_DIR
from backend.data_utils.dataset_validation import validate_dataset
from backend.data_utils.yaml_generator import generate_yolo_yaml
from backend.controlers.library_control import LibraryControl
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
    
@router.post("/upload-dataset/")
async def upload_dataset(file: UploadFile = File(...), model_id: str = Query(...)):
    try:
        model_info = model_control.library_control.get_model_info_index(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

        dataset_format = model_info.get('dataset_format')
        if not dataset_format:
            raise HTTPException(status_code=400, detail="Model does not specify a dataset format")

        dataset_id = str(uuid.uuid4())
        dataset_dir = os.path.join(UPLOAD_DATASET_DIR, dataset_id)
        os.makedirs(dataset_dir, exist_ok=True)

        file_path = os.path.join(dataset_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        if file.filename.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                for zip_info in zip_ref.infolist():
                    if zip_info.filename[-1] == '/':
                        continue
                    zip_info.filename = os.path.basename(zip_info.filename)
                    zip_ref.extract(zip_info, dataset_dir)
            os.remove(file_path)

        # Check if 'images' and 'labels' folders exist directly under dataset_dir
        if not (os.path.exists(os.path.join(dataset_dir, 'images')) and 
                os.path.exists(os.path.join(dataset_dir, 'labels'))):
            shutil.rmtree(dataset_dir)
            raise HTTPException(status_code=400, detail="Invalid dataset structure. 'images' and 'labels' folders should be directly under the root.")

        detected_format = validate_dataset(dataset_dir)
        if detected_format != dataset_format:
            shutil.rmtree(dataset_dir)
            raise HTTPException(status_code=400, detail=f"Dataset format must be {dataset_format}, detected {detected_format}")

        if dataset_format == "YOLO":
            yaml_path = os.path.join(dataset_dir, f"{dataset_id}.yaml")
            generate_yolo_yaml(dataset_dir, yaml_path)
        else:
            pass 

        return {
            "dataset_id": dataset_id,
            "dataset_path": dataset_dir,
            "format": dataset_format,
            "yaml_path": yaml_path
        }
    except Exception as e:
        logger.error(f"Error uploading dataset: {str(e)}")
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

"""# Conduct prediction
@router.post("/predict/")
async def predict(model_id: str = Query(...), request_payload: Dict[str, Any] = Body(...)):
    try:
        active_model = model_control.get_active_model(model_id)
        if not active_model:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found or not loaded")

        conn = active_model['conn']
        
        # Adjust the image path to be absolute path before sending to the model process
        if "image_path" in request_payload:
            request_payload["image_path"] = os.path.join(UPLOAD_IMAGE_DIR, request_payload["image_path"])
        else:
            raise HTTPException(status_code = 500, detail = "Invalid request payload")

        conn.send(f"predict:{json.dumps(request_payload)}")
        prediction = conn.recv()

        return {"model_id": model_id, "prediction": prediction}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))"""

# Creating a web socket connection for real-time video and live webcam processing
# It will receives video frames as bytes, process it using the model and sends results back to user
"""@router.websocket("/ws/predict-live/{model_id}")
async def websocket_video(websocket: WebSocket, model_id: str):
    await websocket.accept()
    try:
        if not model_control.is_model_loaded(model_id):
            await websocket.send_json({"error": f"Model {model_id} is not loaded. Please load the model first"})
            await websocket.close()
            return

        active_model = model_control.get_active_model(model_id)
        if not active_model:
            await websocket.send_json({"error": f"Model {model_id} is not found or model is not loaded"})
            await websocket.close()
            return

        conn = active_model['conn']

        while True:
            try:
                data = await websocket.receive_bytes()
                nparr = np.frombuffer(data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                print("Frame received and decoded")

                # Process frame asynchronously
                prediction = await asyncio.get_event_loop().run_in_executor(None, process_frame, conn, frame)

                # Send prediction results back to the client
                await websocket.send_json(prediction)
                print("Prediction sent to client")
            except WebSocketDisconnect:
                logger.info("User disconnected")
                break
            except Exception as e:
                logger.error(f"Error processing frame: {str(e)}")
                await websocket.send_json({"error": f"Error processing frame: {str(e)}"})
                break
    except Exception as e:
        logger.error(f"Error during websocket communication: {str(e)}")
        await websocket.send_json({"error": f"Error during websocket communication: {str(e)}"})
    finally:
        try:
            await websocket.close()
        except Exception as close_exception:
            logger.error(f"Error closing websocket: {str(close_exception)}")
        logger.info("Connection closed")"""

@router.post("/train")
async def train_model(model_id: str = Query(...), epochs: int = Body(...), batch_size: int = Body(...), learning_rate: float = Body(...), dataset_id: str = Body(...)):
    try:
        if epochs <= 0 or batch_size <= 0 or learning_rate <= 0:
            raise HTTPException(status_code=400, detail="Invalid training parameters")

        dataset_path = os.path.join(UPLOAD_DATASET_DIR, dataset_id)
        if not os.path.exists(dataset_path):
            raise HTTPException(status_code=400, detail="Dataset not found")

        yaml_path = os.path.join(dataset_path, f"{dataset_id}.yaml")
        if not os.path.exists(yaml_path):
            raise HTTPException(status_code=400, detail="YAML configuration file not found")

        training_params = {
            "data_path": yaml_path,
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate
        }
        result = model_control.train_model(model_id, training_params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
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
    