from fastapi import FastAPI
from .routes import model_routes

app = FastAPI()

app.include_router(model_routes.router)
