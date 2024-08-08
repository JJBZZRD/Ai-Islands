import os
import shutil
import logging
from fastapi import HTTPException
from backend.data_utils.zip_utils import extract_zip, move_files_from_subdirectory_if_present
from backend.data_utils.txt_generator import create_txt_files
from backend.data_utils.obj_generator import create_obj_data
from backend.data_utils.yaml_generator import generate_yolo_yaml

logger = logging.getLogger(__name__)

def log_directory_structure(directory: str, message: str):
    for root, dirs, files in os.walk(directory):
        logger.debug(f"{message} - Directory structure: {root}, Directories: {dirs}, Files: {files}")

def process_dataset(file_path: str, dataset_dir: str, dataset_id: str):
    try:
        file_extension = os.path.splitext(file_path)[1][1:]

        # Extract the dataset from zip file
        if file_extension == 'zip':
            extract_zip(file_path, dataset_dir)
            move_files_from_subdirectory_if_present(dataset_dir)

        # Log the directory structure after extraction
        log_directory_structure(dataset_dir, "After extraction")

        # Generate train.txt and val.txt files
        create_txt_files(dataset_dir)
        logger.debug("Generated train.txt and val.txt files")

        # Read class names from obj.names file
        obj_names_path = os.path.join(dataset_dir, 'obj.names')
        if os.path.exists(obj_names_path):
            with open(obj_names_path, 'r') as f:
                class_names = [line.strip() for line in f.readlines()]
        else:
            raise HTTPException(status_code=400, detail="obj.names file not found")
        
        # Generate obj.data file
        create_obj_data(dataset_dir, len(class_names))
        logger.debug("Generated obj.data file")

        # Generate YAML file
        yaml_path = os.path.join(dataset_dir, f"{dataset_id}.yaml")
        generate_yolo_yaml(dataset_dir, yaml_path, class_names)
        logger.debug("Generated YAML file")

        # Log the directory structure after generating all files
        log_directory_structure(dataset_dir, "After generating all files")

        return {"dataset_id": dataset_id, "dataset_path": dataset_dir}
    except Exception as e:
        logger.error(f"Error processing dataset: {str(e)}")
        if os.path.exists(dataset_dir):
            shutil.rmtree(dataset_dir)
        raise HTTPException(status_code=500, detail=str(e))