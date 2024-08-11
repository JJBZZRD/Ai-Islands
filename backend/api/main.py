import logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from backend.api.routes.model_routes import ModelRouter
from backend.api.routes.data_routes import DataRouter
from backend.api.routes.library_routes import LibraryRouter
from backend.api.routes.settings_routes import SettingsRouter
from backend.controlers.model_control import ModelControl
from backend.controlers.playground_control import PlaygroundControl
from backend.controlers.runtime_control import RuntimeControl
from backend.controlers.library_control import LibraryControl
from backend.api.routes.playground_routes import PlaygroundRouter

# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Instantiate controls and set all models inactive in chain
model_control = ModelControl()
library_control = LibraryControl()
playground_control = PlaygroundControl(model_control)

# Initialise library and runtime data files if they do not exist
library_control._initialise_library()
RuntimeControl._initialise_runtime_data()

# Create router instances
model_router = ModelRouter(model_control)
data_router = DataRouter()
library_router = LibraryRouter(library_control)
settings_router = SettingsRouter()
playground_router = PlaygroundRouter(playground_control)

# Add logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"New request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Completed response: {response.status_code}")
    return response

# customise error response for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder({"error": exc.errors()}),
    )

# Include routers
app.include_router(model_router.router, prefix="/model", tags=["model"])
app.include_router(data_router.router, prefix="/data", tags=["data"])
app.include_router(library_router.router, prefix="/library", tags=["library"])
app.include_router(settings_router.router, prefix="/settings", tags=["settings"])
app.include_router(playground_router.router, prefix="/playground", tags=["playground"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, log_level="debug")