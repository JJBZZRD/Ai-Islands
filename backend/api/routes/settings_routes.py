from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.utils.watson_settings_manager import watson_settings

router = APIRouter()

class WatsonSettings(BaseModel):
    api_key: str = None
    project_id: str = None
    location: str = None

@router.post("/update_watson_settings")
async def update_watson_settings(settings: WatsonSettings):
    try:
        if settings.api_key is not None:
            watson_settings.set("IBM_CLOUD_API_KEY", settings.api_key)
        
        if settings.project_id is not None:
            watson_settings.set("USER_PROJECT_ID", settings.project_id)
        
        if settings.location is not None:
            watson_settings.update_location(settings.location)
        
        return {"message": "Watson settings updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating Watson settings: {str(e)}")

@router.get("/get_watson_settings")
async def get_watson_settings():
    try:
        current_settings = watson_settings.get_all_settings()
        # Mask the API key for security
        if current_settings['IBM_CLOUD_API_KEY']:
            current_settings['IBM_CLOUD_API_KEY'] = current_settings['IBM_CLOUD_API_KEY'][:5] + '*' * 10
        return current_settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving Watson settings: {str(e)}")