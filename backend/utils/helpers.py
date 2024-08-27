import json
import subprocess
import sys
from backend.data_utils.json_handler import JSONHandler
from backend.core.config import DOWNLOADED_MODELS_PATH


def read_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def write_json(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def install_packages(packages):
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"Successfully installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {package}")
            print(e)

def get_next_suffix(base_model_id):
    library = JSONHandler.read_json(DOWNLOADED_MODELS_PATH)
    i = 1
    while f"{base_model_id}_{i}" in library:
        i += 1
    return i
