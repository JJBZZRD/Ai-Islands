import logging
import cv2
import json
from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from typing import Annotated
import numpy as np
from backend.controlers.model_control import ModelControl
from backend.data_utils.dataset_processor import process_dataset
from backend.data_utils.training_handler import handle_training_request

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

class ModelRouter:
    def __init__(self, model_control: ModelControl):
        self.router = APIRouter()
        self.model_control = model_control

        # Define routes
        self.router.add_api_route("/get-models", self.get_models, methods=["GET"])
        self.router.add_api_route("/active", self.list_active_models, methods=["GET"])
        self.router.add_api_route("/load", self.load_model, methods=["POST"])
        self.router.add_api_route("/unload", self.unload_model, methods=["POST"])
        self.router.add_api_route("/download-model", self.download_model, methods=["POST"])
        self.router.add_api_route("/is-model-loaded", self.is_model_loaded, methods=["GET"])
        self.router.add_api_route("/inference", self.inference, methods=["POST"])
        self.router.add_api_route("/train", self.train_model, methods=["POST"])
        self.router.add_api_route("/configure", self.configure_model, methods=["POST"])

        self.router.add_websocket_route("/ws/predict-live/{model_id}", self.predict_live)
        self.router.add_api_route("/delete-model", self.delete_model, methods=["DELETE"])

    async def get_models(self, source: str = Query("index", description="Source of models: 'index' or 'library'")):
        try:
            if source == "library":
                with open('data/library.json', 'r') as f:
                    models = json.load(f)
            else:  
                with open('data/model_index.json', 'r') as f:
                    models = json.load(f)
            return JSONResponse(content=models)
        except Exception as e:
            logger.error(f"Error reading model {source}: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def list_active_models(self):
        try:
            active_models = self.model_control.list_active_models()
            return {"active_models": active_models}
        except Exception as e:
            logger.error(f"Error listing active models: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def load_model(self, model_id: str = Query(...)):
        try:
            if self.model_control.load_model(model_id):
                return {"message": f"Model {model_id} loaded successfully"}
            else:
                raise HTTPException(status_code=400, detail=f"Model {model_id} could not be loaded")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def unload_model(self, model_id: str = Query(...)):
        try:
            if self.model_control.unload_model(model_id):
                return {"message": f"Model {model_id} unloaded successfully"}
            else:
                raise HTTPException(status_code=400, detail=f"Model {model_id} could not be unloaded")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def download_model(self, model_id: str = Query(...), auth_token: str = Query(None)):
        try:
            success = self.model_control.download_model(model_id, auth_token)
            if success:
                return {"message": f"Model {model_id} downloaded successfully"}
            else:
                raise HTTPException(status_code=400, detail=f"Model {model_id} could not be downloaded")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def is_model_loaded(self, model_id: str = Query(...)):
        try:
            is_loaded = self.model_control.is_model_loaded(model_id)
            if is_loaded:
                return {"message": f"Model {model_id} is loaded"}
            else:
                return {"message": f"Model {model_id} is not loaded"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def inference(self, inferenceRequest: InferenceRequest):
        try:
            return self.model_control.inference(jsonable_encoder(inferenceRequest))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def train_model(self, trainRequest: TrainRequest):
        try:
            return self.model_control.train_model(jsonable_encoder(trainRequest))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def configure_model(self, configureRequest: ConfigureRequest):
        try:
            return self.model_control.configure_model(jsonable_encoder(configureRequest))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def predict_live(self, websocket: WebSocket, model_id: str):
        await websocket.accept()
        try:
            if not self.model_control.is_model_loaded(model_id):
                await websocket.send_json({"error": f"Model {model_id} is not loaded. Please load the model first"})
                await websocket.close()
                return

            active_model = self.model_control.get_active_model(model_id)
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

    async def delete_model(self, model_id: str = Query(...)):
        try:
            result = self.model_control.delete_model(model_id)
            if result:
                return {"message": f"Model {model_id} deleted successfully"}
            else:
                raise HTTPException(status_code=404, detail=f"Model {model_id} not found or could not be deleted")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))