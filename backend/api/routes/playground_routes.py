import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any
from backend.controlers.playground_control import PlaygroundControl
from fastapi.encoders import jsonable_encoder

logger = logging.getLogger(__name__)

class CreatePlaygroundRequest(BaseModel):
    playground_id: str = None
    description: str = None

class UpdatePlaygroundRequest(BaseModel):
    new_playground_id: str = None
    description: str = None

class ChainConfigureRequest(BaseModel):
    chain: List[str]

class PlaygroundRouter:
    def __init__(self, playground_control: PlaygroundControl):
        self.playground_control = playground_control
        self.router = APIRouter()

        # Define routes
        self.router.add_api_route("/create", self.create_playground, methods=["POST"])
        self.router.add_api_route("/update", self.update_playground, methods=["PUT"])
        self.router.add_api_route("/delete", self.delete_playground, methods=["DELETE"])
        self.router.add_api_route("/add-model", self.add_model_to_playground, methods=["POST"])
        self.router.add_api_route("/remove-model", self.remove_model_from_playground, methods=["POST"])
        self.router.add_api_route("/list", self.list_playgrounds, methods=["GET"])
        self.router.add_api_route("/info", self.get_playground_info, methods=["GET"])
        self.router.add_api_route("/configure-chain", self.configure_chain, methods=["POST"])
        self.router.add_api_route("/load-chain", self.load_playground_chain, methods=["POST"])
        self.router.add_api_route("/stop-chain", self.stop_playground_chain, methods=["POST"])
        self.router.add_api_route("/inference", self.inference, methods=["POST"])

    async def create_playground(self, request: CreatePlaygroundRequest):
        try:
            playground_id = request.playground_id
            description = request.description
            result = self.playground_control.create_playground(playground_id, description)
            return result
        except Exception as e:
            logger.error(f"Error creating playground: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def update_playground(self, playground_id: str, request: UpdatePlaygroundRequest):
        try:
            result = self.playground_control.update_playround_info(
                playground_id, 
                new_playground_id=request.new_playground_id, 
                description=request.description
            )
            return result
        except Exception as e:
            logger.error(f"Error updating playground: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_playground(self, playground_id: str = Query(...)):
        try:
            result = self.playground_control.delete_playground(playground_id)
            return result
        except Exception as e:
            logger.error(f"Error deleting playground: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def add_model_to_playground(self, playground_id: str = Query(...), model_id: str = Query(...)):
        try:
            result = self.playground_control.add_model_to_playground(playground_id, model_id)
            return result
        except Exception as e:
            logger.error(f"Error adding model to playground: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def remove_model_from_playground(self, playground_id: str = Query(...), model_id: str = Query(...)):
        try:
            result = self.playground_control.remove_model_from_playground(playground_id, model_id)
            return result
        except Exception as e:
            logger.error(f"Error removing model from playground: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def list_playgrounds(self):
        try:
            result = self.playground_control.list_playgrounds()
            return result
        except Exception as e:
            logger.error(f"Error listing playgrounds: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_playground_info(self, playground_id: str = Query(...)):
        try:
            result = self.playground_control.get_playground_info(playground_id)
            return result
        except Exception as e:
            logger.error(f"Error getting playground info: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def configure_chain(self, playground_id: str = Query(...), request: ChainConfigureRequest = ...):
        try:
            result = self.playground_control.configure_chain(playground_id, request.chain)
            return result
        except Exception as e:
            logger.error(f"Error configuring chain: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def load_playground_chain(self, playground_id: str = Query(...)):
        try:
            result = self.playground_control.load_playground_chain(playground_id)
            return {"message": "Playground chain loaded successfully"} if result else {"error": "Failed to load playground chain"}
        except Exception as e:
            logger.error(f"Error loading playground chain: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def stop_playground_chain(self, playground_id: str = Query(...)):
        try:
            result = self.playground_control.stop_playground_chain(playground_id)
            return {"message": "Playground chain stopped successfully"} if result else {"error": "Failed to stop playground chain"}
        except Exception as e:
            logger.error(f"Error stopping playground chain: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def inference(self, playground_id: str = Query(...), payload: str = Query(...)):
        try:
            result = self.playground_control.inference(playground_id, payload)
            return result
        except Exception as e:
            logger.error(f"Error performing inference: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))