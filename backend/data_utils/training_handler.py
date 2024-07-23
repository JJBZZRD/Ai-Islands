import os
import logging
from fastapi import HTTPException
from backend.data_utils.file_utils import verify_file
from backend.core.config import UPLOAD_DATASET_DIR


logger = logging.getLogger(__name__)

def handle_training_request(model_control, model_id, epochs, batch_size, learning_rate, dataset_id, imgsz):
    try:
        if epochs <= 0 or batch_size <= 0 or learning_rate <= 0:
            raise ValueError("Invalid training parameters")

        dataset_path = os.path.join(UPLOAD_DATASET_DIR, dataset_id)
        if not os.path.exists(dataset_path):
            raise FileNotFoundError("Dataset not found")

        yaml_path = os.path.join(dataset_path, f"{dataset_id}.yaml")
        if not os.path.exists(yaml_path):
            raise FileNotFoundError("YAML configuration file not found")

        train_txt_path = os.path.abspath(os.path.join(dataset_path, 'train.txt'))
        val_txt_path = os.path.abspath(os.path.join(dataset_path, 'val.txt'))

        # Log paths and YAML contents
        logger.debug(f"YAML Path: {yaml_path}")
        with open(yaml_path, 'r') as f:
            yaml_contents = f.read()
        logger.debug(f"YAML Contents: {yaml_contents}")
        
        # Log existence of train.txt and val.txt using absolute paths
        logger.debug(f"Checking paths: train.txt -> {train_txt_path}, val.txt -> {val_txt_path}")
        
        if not verify_file(train_txt_path) or not verify_file(val_txt_path):
            raise ValueError("train.txt or val.txt validation failed")

        # Log the current working directory
        current_working_dir = os.getcwd()
        logger.debug(f"Current working directory: {current_working_dir}")

        # Print directory listing
        dir_listing = os.listdir(dataset_path)
        logger.debug(f"Directory listing for {dataset_path}: {dir_listing}")

        training_params = {
            "data": yaml_path,
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "imgsz": imgsz
        }
        result = model_control.train_model(model_id, training_params)
        return result
    except Exception as e:
        logger.error(f"Error during training: {str(e)}")
        raise
