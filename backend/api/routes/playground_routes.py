from fastapi import APIRouter, Query, Body
from pydantic import BaseModel
from typing import List, Annotated
from backend.controlers.playground_control import PlaygroundControl
from backend.utils.api_response import success_response, error_response
import logging
from fastapi.encoders import jsonable_encoder
from backend.core.exceptions import FileReadError, FileWriteError, PlaygroundError, PlaygroundAlreadyExistsError, ChainNotCompatibleError
from backend.controlers.runtime_control import RuntimeControl

logger = logging.getLogger(__name__)

class CreatePlaygroundRequest(BaseModel):
    playground_id: str = None
    description: str = None

class UpdatePlaygroundRequest(BaseModel):
    playground_id: str = ...
    new_playground_id: str = None
    description: str = None

class ChainConfigureRequest(BaseModel):
    playground_id: str = ...
    chain: List[str]
    
class InferenceRequest(BaseModel):
    playground_id: str = ...
    data: dict = ...

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
            message = f"Successfully created new playground with ID: {playground_id}"
            return success_response(message=message, data=result, status_code=201)
        except PlaygroundAlreadyExistsError as e:
            return error_response(message=str(e), status_code=409)
        except FileWriteError as e:
            return error_response(message=str(e), status_code=500)

    async def update_playground(self, request: UpdatePlaygroundRequest):
        try:
            result = self.playground_control.update_playground_info(
                playground_id=request.playground_id, 
                new_playground_id=request.new_playground_id, 
                description=request.description
            )
            return success_response(message="Playground updated successfully", data=result, status_code=200)
        except KeyError as e:
            return error_response(message=str(e), status_code=404)
        except FileWriteError as e:
            return error_response(message=str(e), status_code=500)
        except Exception as e:
            return error_response(message=str(e), status_code=500)
        
    async def delete_playground(self, playground_id: str = Query(...)):
        try:
            result = self.playground_control.delete_playground(playground_id)
            if result:
                return success_response(status_code=204)
        except KeyError as e:
            return error_response(message=str(e), status_code=404)
        except PlaygroundError as e:
            return error_response(message=str(e), status_code=409)
        except FileWriteError as e:
            return error_response(message=str(e), status_code=500)

    async def add_model_to_playground(self, playground_id: str = Body(...), model_id: str = Body(...)):
        try:
            result = self.playground_control.add_model_to_playground(playground_id, model_id)
            return success_response(message=f"Model {model_id} added to playground {playground_id}", data=result, status_code=200)
        except KeyError as e:
            return error_response(message=str(e), status_code=404)
        except FileWriteError as e:
            return error_response(message=str(e), status_code=500)

    async def remove_model_from_playground(self, playground_id: str = Body(...), model_id: str = Body(...)):
        try:
            result = self.playground_control.remove_model_from_playground(playground_id, model_id)
            if result:
                return success_response(status_code=204)
        except KeyError as e:
            return error_response(message=str(e), status_code=404)
        except PlaygroundError as e:
            return error_response(message=str(e), status_code=409)
        except FileWriteError as e:
            return error_response(message=str(e), status_code=500)

    async def list_playgrounds(self):
        result = self.playground_control.list_playgrounds()
        return success_response(data=result, status_code=200)

    async def get_playground_info(self, playground_id: str = Query(...)):
        result = self.playground_control.get_playground_info(playground_id)
        return success_response(data=result, status_code=200)

    async def configure_chain(self, request: ChainConfigureRequest = ...):
        try:
            result = self.playground_control.configure_chain(request.playground_id, request.chain)
            return success_response(message="Chain configured successfully", data=result, status_code=200)
        except KeyError as e:
            return error_response(message=str(e), status_code=404)
        except ChainNotCompatibleError as e:
            return error_response(message=str(e), status_code=422)
        except PlaygroundError as e:
            return error_response(message=str(e), status_code=409)
        except FileWriteError as e:
            return error_response(message=str(e), status_code=500)
        
    async def load_playground_chain(self, playground_id: Annotated[str, Body(embed=True)] = ...):
        try:
            result = self.playground_control.load_playground_chain(playground_id)
            return success_response(message="Playground chain loaded successfully", data=result, status_code=200)
        except KeyError as e:
            return error_response(message=str(e), status_code=404)
        except (FileReadError, FileWriteError) as e:
            return error_response(message=str(e), status_code=500)
        except PlaygroundError as e:
            return error_response(message=str(e), status_code=409)
        except Exception as e:
            return error_response(message=str(e), status_code=500)

    async def stop_playground_chain(self, playground_id: Annotated[str, Body(embed=True)] = ...):
        try:
            result = self.playground_control.stop_playground_chain(playground_id)
            if result:
                return success_response(status_code=204)
        except KeyError as e:
            return error_response(message=str(e), status_code=404)
        except PlaygroundError as e:
            return error_response(message=str(e), status_code=409)
        except (FileReadError, FileWriteError) as e:
            return error_response(message=str(e), status_code=500)
        except Exception as e:
            return error_response(message=str(e), status_code=500)

    async def inference(self, inference_request: InferenceRequest):
        try:
            result = self.playground_control.inference(jsonable_encoder(inference_request))
            return success_response(data=result, status_code=200)
        except KeyError as e:
            return error_response(message=str(e), status_code=404)
        except Exception as e:
            return error_response(message=str(e), status_code=500)
