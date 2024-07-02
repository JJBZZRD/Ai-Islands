from fastapi import APIRouter

router = APIRouter()

@router.get("/models")
async def list_models():
    return {"message": "List of models"}

@router.post("/models/load")
async def load_model(model_id: str):
    return {"message": f"Loading model {model_id}"}
