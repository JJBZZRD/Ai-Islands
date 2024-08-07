from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any
from backend.controlers.library_control import LibraryControl
import json

class NewModelEntry(BaseModel):
    model_id: str
    base_model: str
    # Add other fields as necessary

class ConfigUpdateRequest(BaseModel):
    model_id: str
    new_config: Dict[str, Any]

class SaveNewModelRequest(BaseModel):
    model_id: str
    new_model_id: str
    new_config: Dict[str, Any]

class UpdateModelIdRequest(BaseModel):
    model_id: str
    new_model_id: str

class LibraryRouter:
    def __init__(self, library_control: LibraryControl):
        self.router = APIRouter()
        self.library_control = library_control

        self.router.add_api_route("/get-full-model-index", self.get_full_model_index, methods=["GET"])
        self.router.add_api_route("/get-full-library", self.get_full_library, methods=["GET"])

        # Define routes
        self.router.add_api_route("/update", self.update_library, methods=["POST"])
        self.router.add_api_route("/get-model-info-library", self.get_model_info_library, methods=["GET"])
        self.router.add_api_route("/get-model-info-index", self.get_model_info_index, methods=["GET"])
        self.router.add_api_route("/delete-model", self.delete_model, methods=["DELETE"])
        self.router.add_api_route("/add-fine-tuned-model", self.add_fine_tuned_model, methods=["POST"])
        self.router.add_api_route("/update-model-config", self.update_model_config, methods=["POST"])
        self.router.add_api_route("/save-new-model", self.save_new_model, methods=["POST"])
        self.router.add_api_route("/update-model-id", self.update_model_id, methods=["POST"])

    async def get_full_model_index(self):
        with open('data/model_index.json', 'r') as file:
            full_model_index = json.load(file)
        return full_model_index

    async def get_full_library(self):
        with open('data/library.json', 'r') as file:
            library = json.load(file)
        return library

    async def update_library(self, model_id: str, new_entry: Dict[str, Any]):
        self.library_control.update_library(model_id, new_entry)
        return {"message": f"Library updated for model {model_id}"}

    async def get_model_info_library(self, model_id: str = Query(...)):
        model_info = self.library_control.get_model_info_library(model_id)
        if model_info:
            return model_info
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found in library")

    async def get_model_info_index(self, model_id: str = Query(...)):
        model_info = self.library_control.get_model_info_index(model_id)
        if model_info:
            return model_info
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found in index")

    async def delete_model(self, model_id: str = Query(...)):
        success = self.library_control.delete_model(model_id)
        if success:
            return {"message": f"Model {model_id} deleted from library"}
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found in library")

    async def add_fine_tuned_model(self, new_entry: NewModelEntry):
        new_model_id = self.library_control.add_fine_tuned_model(new_entry.dict())
        return {"message": f"Fine-tuned model {new_model_id} added to library"}

    async def update_model_config(self, request: ConfigUpdateRequest):
        updated_config = self.library_control.update_model_config(request.model_id, request.new_config)
        if updated_config:
            return {"message": f"Configuration updated for model {request.model_id}", "new_config": updated_config}
        raise HTTPException(status_code=404, detail=f"Model {request.model_id} not found or configuration update failed")

    async def save_new_model(self, request: SaveNewModelRequest):
        new_model_id = self.library_control.save_new_model(request.model_id, request.new_model_id, request.new_config)
        if new_model_id:
            return {"message": f"New model {new_model_id} saved successfully"}
        raise HTTPException(status_code=400, detail=f"Failed to save new model based on {request.model_id}")

    async def update_model_id(self, request: UpdateModelIdRequest):
        new_model_id = self.library_control.update_model_id(request.model_id, request.new_model_id)
        if new_model_id:
            return {"message": f"Model ID updated from {request.model_id} to {new_model_id}"}
        raise HTTPException(status_code=400, detail=f"Failed to update model ID from {request.model_id} to {request.new_model_id}")