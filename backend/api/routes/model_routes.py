import logging
from typing import Annotated

import cv2
import numpy as np
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from backend.controlers.model_control import ModelControl
from backend.data_utils.dataset_processor import process_dataset
from backend.data_utils.training_handler import handle_training_request
from backend.utils.process_vis_out import process_vision_output, _ensure_json_serializable
from PIL import Image
from io import BytesIO
import base64
from backend.core.exceptions import FileReadError, ModelError
from backend.utils.api_response import error_response, success_response


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
    
class ProcessImageOutputRequest(BaseModel):
    image_path: str
    output: dict
    task: str

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
        self.router.add_api_route("/download-model", self.download_model, methods=["POST"])
        self.router.add_api_route("/load", self.load_model, methods=["POST"])
        self.router.add_api_route("/unload", self.unload_model, methods=["POST"])
        self.router.add_api_route("/is-model-loaded", self.is_model_loaded, methods=["GET"])
        self.router.add_api_route("/active", self.list_active_models, methods=["GET"])
        self.router.add_api_route("/inference", self.inference, methods=["POST"])
        self.router.add_api_route("/train", self.train_model, methods=["POST"])
        self.router.add_api_route("/configure", self.configure_model, methods=["POST"])
        self.router.add_api_route("/process-image", self.process_image, methods=["POST"], response_model=dict)
        self.router.add_api_route("/delete-model", self.delete_model, methods=["DELETE"])
        self.router.add_websocket_route("/ws/predict-live/{model_id}", self.predict_live)
        
    
    async def download_model(self, model_id: str = Query(...), auth_token: str = Query(None)):
        try:
            self.model_control.download_model(model_id, auth_token)
            return success_response(message=f"Model {model_id} downloaded successfully")
        except (ModelError, ValueError) as e:
            return error_response(message=str(e), status_code=500)
    
    async def load_model(self, model_id: str = Query(...)):
        try:
            self.model_control.load_model(model_id)
            return success_response(message=f"Model {model_id} loaded successfully")
        except ValueError as e:
            return error_response(message=str(e), status_code=404)
        except ModelError as e:
            return error_response(message=str(e), status_code=500)
        except FileNotFoundError as e:
            return error_response(message=str(e), status_code=500)
    
    async def unload_model(self, model_id: str = Query(...)):
        try:
            self.model_control.unload_model(model_id)
            return success_response(message=f"Model {model_id} unloaded successfully")
        except ModelError as e:
            return error_response(message=str(e), status_code=409)
        except ValueError as e:
            return error_response(message=str(e), status_code=404)
        except FileReadError as e:
            return error_response(message=str(e), status_code=500)
    
    async def is_model_loaded(self, model_id: str = Query(...)):
        is_loaded = self.model_control.is_model_loaded(model_id)
        if is_loaded:
            return success_response(message=f"Model {model_id} is loaded")
        else:
            return success_response(message=f"Model {model_id} is not loaded")
    
    async def list_active_models(self):
        active_models = self.model_control.list_active_models()
        return success_response(data=active_models)

    async def inference(self, inferenceRequest: InferenceRequest):
        try:
            result = self.model_control.inference(jsonable_encoder(inferenceRequest))
            return success_response(data=result)
        except KeyError as e:
            return error_response(message=str(e), status_code=400)
        except ModelError as e:
            return error_response(message=str(e), status_code=500)
        except FileNotFoundError as e:
            return error_response(message=str(e), status_code=422)

    async def train_model(self, trainRequest: TrainRequest):
        try:
            data, message = self.model_control.train_model(jsonable_encoder(trainRequest))
            return success_response(data=data, message=message)
        except KeyError as e:
            return error_response(message=str(e), status_code=400)
        except Exception as e:
            return error_response(message=str(e), status_code=500)

    async def configure_model(self, configureRequest: ConfigureRequest):
        try:
            response = self.model_control.configure_model(jsonable_encoder(configureRequest))
            return success_response(message=response)
        except KeyError as e:
            return error_response(message=str(e), status_code=400)
        except Exception as e:
            return error_response(message=str(e), status_code=500)
        
    async def process_image(self, request: ProcessImageOutputRequest):
        try:
            output = request.output
            if isinstance(output, list):
                output = {"predictions": output}
            processed_output = self.model_control.process_image(request.image_path, output, request.task)
            return processed_output
        except ValueError as e:
            logger.error(f"Error in process_image: {str(e)}")
            return error_response(message=str(e), status_code=400)
        except Exception as e:
            logger.error(f"Error in process_image: {str(e)}")
            return error_response(message=str(e), status_code=500)

    async def delete_model(self, model_id: str = Query(...)):
        try:
            response = self.model_control.delete_model(model_id)
            return success_response(message=response)
        except ModelError as e:
            return error_response(message=str(e), status_code=409)
        except ValueError as e:
            return error_response(message=str(e), status_code=404)
    
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
