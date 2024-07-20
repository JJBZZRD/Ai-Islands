import os
import shutil
import zipfile
import logging

logger = logging.getLogger(__name__)

"""This is for unpacking the zip files and ensuring that the files are in the correct directory"""
def extract_zip(file_path: str, extract_to: str):
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        os.remove(file_path)
        logger.debug("Extracted zip file")
    except zipfile.BadZipFile as e:
        logger.error(f"Invalid zip file: {e}")
        raise

def move_files_from_subdirectory_if_present(dataset_dir: str):
    extracted_files = os.listdir(dataset_dir)
    if len(extracted_files) == 1 and os.path.isdir(os.path.join(dataset_dir, extracted_files[0])):
        sub_dir = os.path.join(dataset_dir, extracted_files[0])
        for file in os.listdir(sub_dir):
            shutil.move(os.path.join(sub_dir, file), dataset_dir)
        os.rmdir(sub_dir)
        logger.debug("Moved files from subdirectory")