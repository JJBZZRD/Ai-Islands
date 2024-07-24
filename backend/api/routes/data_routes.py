import logging
import os
import shutil
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from backend.core.config import UPLOAD_IMAGE_DIR, UPLOAD_VID_DIR, UPLOAD_DATASET_DIR
from backend.data_utils.dataset_processor import process_dataset

logger = logging.getLogger(__name__)

class DataRouter:
    def __init__(self):
        self.router = APIRouter()

        # Define routes
        self.router.add_api_route("/upload-image/", self.upload_image, methods=["POST"])
        self.router.add_api_route("/upload-video/", self.upload_video, methods=["POST"])
        self.router.add_api_route("/upload-dataset/", self.upload_dataset, methods=["POST"])

    async def upload_image(self, file: UploadFile = File(...)):
        try:
            image_id = str(uuid.uuid4())
            file_extension = file.filename.split('.')[-1]
            file_path = os.path.join(UPLOAD_IMAGE_DIR, f"{image_id}.{file_extension}")
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            relative_file_path = os.path.relpath(file_path, UPLOAD_IMAGE_DIR)
            
            return {"image_id": image_id, "file_path": relative_file_path}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def upload_video(self, file: UploadFile = File(...)):
        try:
            video_id = str(uuid.uuid4())
            file_extension = file.filename.split('.')[-1]
            file_path = os.path.join(UPLOAD_VID_DIR, f"{video_id}.{file_extension}")
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                
            relative_file_path = os.path.relpath(file_path, UPLOAD_VID_DIR)
            
            return {"video_id": video_id , "file_path": relative_file_path}
        
        except Exception as e:
            raise HTTPException(status_code=500, detail= str(e))

    async def upload_dataset(self, file: UploadFile = File(...), model_id: str = Query(...)):
        dataset_dir = ""
        try:
            dataset_id = str(uuid.uuid4())
            dataset_dir = os.path.join(UPLOAD_DATASET_DIR, dataset_id)

            os.makedirs(dataset_dir, exist_ok=True)
            file_path = os.path.join(dataset_dir, file.filename)

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            result = process_dataset(file_path, dataset_dir, dataset_id)

            return result
        except Exception as e:
            logger.error(f"Error uploading dataset: {str(e)}")
            if os.path.exists(dataset_dir):
                shutil.rmtree(dataset_dir)
            raise HTTPException(status_code=500, detail=str(e))
