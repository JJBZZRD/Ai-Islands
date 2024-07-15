import json
import os
import torch
from backend.core.config import CONFIG_PATH
from backend.data_utils.json_handler import JSONHandler

def read_config():
    try:
        return JSONHandler.read_json(CONFIG_PATH)
    except FileNotFoundError:
        return {"hardware": "cpu"}

def write_config(config):
    JSONHandler.write_json(CONFIG_PATH, config)

def set_hardware_preference(device: str):
    if device not in ["cpu", "gpu"]:
        raise ValueError("Invalid device. Choose 'cpu' or 'gpu'.")

    if device == "gpu" and not torch.cuda.is_available():
        raise ValueError("GPU is not available on this system.")

    config = read_config()
    config["hardware"] = device
    write_config(config)

def get_hardware_preference():
    config = read_config()
    return config.get("hardware", "cpu")
