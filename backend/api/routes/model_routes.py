import logging
import cv2
from fastapi import UploadFile, APIRouter, File, HTTPException, Query, Body, WebSocket, WebSocketDisconnect
from backend.controlers.model_control import ModelControl
from backend.core.config import DOWNLOADED_MODELS_PATH, UPLOAD_IMAGE_DIR, UPLOAD_VID_DIR
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
async def download_model(model_id: str = Query(...)):
    try:
        success = model_control.download_model(model_id)
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

# Conduct prediction
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
        raise HTTPException(status_code=500, detail=str(e))
    
# Creating a web socket connection for real-time video and live webcam processing
# It will receives video frames as bytes, process it using the model and sends results back to user
@router.websocket("/ws/predict-live/{model_id}")
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
        logger.info("Connection closed")

def process_frame(conn, frame):
    # Use GPU if available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type == 'cuda':
        logger.info("Using GPU for inference")
    else:
        logger.info("Using CPU for inference")

    request_payload = {"video_frame": frame.tolist()}
    conn.send(f"predict:{json.dumps(request_payload)}")
    prediction = conn.recv()
    return prediction


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
    