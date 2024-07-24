from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any
from backend.controlers.library_control import LibraryControl

class NewModelEntry(BaseModel):
    model_id: str
    base_model: str
    # Add other fields as necessary

class LibraryRouter:
    def __init__(self, library_control: LibraryControl):
        self.router = APIRouter()
        self.library_control = library_control

        # Define routes
        self.router.add_api_route("/update", self.update_library, methods=["POST"])
        self.router.add_api_route("/get-model-info", self.get_model_info, methods=["GET"])
        self.router.add_api_route("/get-model-index", self.get_model_index, methods=["GET"])
        self.router.add_api_route("/delete-model", self.delete_model, methods=["DELETE"])
        self.router.add_api_route("/add-fine-tuned-model", self.add_fine_tuned_model, methods=["POST"])

    async def update_library(self, model_id: str, new_entry: Dict[str, Any]):
        self.library_control.update_library(model_id, new_entry)
        return {"message": f"Library updated for model {model_id}"}

    async def get_model_info(self, model_id: str = Query(...)):
        model_info = self.library_control.get_model_info_library(model_id)
        if model_info:
            return model_info
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found in library")

    async def get_model_index(self, model_id: str = Query(...)):
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
