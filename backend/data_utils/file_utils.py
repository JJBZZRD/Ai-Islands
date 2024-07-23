import os
import logging

logger = logging.getLogger(__name__)

def check_hidden_chars(file_path):
    with open(file_path, 'rb') as f:
        content = f.read()
    if b'\0' in content:
        logger.error(f"Hidden characters found in {file_path}")
        return True
    return False

def verify_file(file_path):
    if not os.path.exists(file_path):
        logger.error(f"{file_path} does not exist")
        return False
    if check_hidden_chars(file_path):
        return False
    with open(file_path, 'r') as f:
        content = f.read()
    if not content.strip():
        logger.error(f"{file_path} is empty")
        return False
    logger.debug(f"Contents of {file_path}: {content[:1000]}...")  # Print first 1000 chars
    return True