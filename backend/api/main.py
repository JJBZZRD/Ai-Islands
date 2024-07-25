import logging
from fastapi import FastAPI
from backend.api.routes import model_routes, hardware, data_routes, settings_routes

import os
from dotenv import load_dotenv
load_dotenv()
logging.info(f"IBM_CLOUD_API_KEY: ...{os.getenv('IBM_CLOUD_API_KEY')[-4:]}")
logging.info(f"IBM_CLOUD_PROJECTS_URL: {os.getenv('IBM_CLOUD_PROJECTS_URL')}")
logging.info(f"USER_PROJECT_ID: {os.getenv('USER_PROJECT_ID')}")

# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"New request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Completed response: {response.status_code}")
    return response

app.include_router(model_routes.router)
app.include_router(hardware.router, prefix="/hardware", tags=["hardware"])
app.include_router(data_routes.router, prefix="/data", tags=["data"])
app.include_router(settings_routes.router, prefix="/settings", tags=["settings"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, log_level="debug")