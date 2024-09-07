import argparse
import logging
import sys
import os
import torch
import shutil
import json

# Adding the root directory of the project to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.core.config import ROOT_DIR
from backend.models.ultralytics_model import UltralyticsModel
from backend.data_utils.json_handler import JSONHandler

logger = logging.getLogger(__name__)

DOWNLOADED_MODELS_PATH = os.path.join(ROOT_DIR, 'data', 'library.json')

def clean_output(output):
    problematic_chars = ['â', '€', '¦', '']
    for char in problematic_chars:
        output = output.replace(char, '')
    return output

def write_library_json(data):
    """
    Writes the given data to the library.json file.
    """
    try:
        logger.info(f"Writing data to {DOWNLOADED_MODELS_PATH}")
        with open(DOWNLOADED_MODELS_PATH, 'w') as f:
            json.dump(data, f, indent=4)
        logger.info(f"Successfully wrote data to {DOWNLOADED_MODELS_PATH}")
    except Exception as e:
        logger.error(f"Failed to write data to {DOWNLOADED_MODELS_PATH}: {e}")
        raise e


def add_model_to_library(new_entry: dict):
    try:
        if not os.path.exists(DOWNLOADED_MODELS_PATH):
            logger.error(f"Library file not found at: {DOWNLOADED_MODELS_PATH}")
            return

        library = JSONHandler.read_json(DOWNLOADED_MODELS_PATH)
        new_model_id = new_entry['model_id']


        if new_model_id in library:
            logger.warning(f"Model ID {new_model_id} already exists in the library. Overwriting it.")

        library[new_entry['model_id']] = new_entry


        write_library_json(library)
        logger.info(f"Successfully added model {new_model_id} to the library.")
        return new_model_id

    except Exception as e:
        logger.error(f"Failed to add model to library: {e}")
        raise e


def main():
    parser = argparse.ArgumentParser(description="Train a model")
    parser.add_argument('--model_id', type=str, required=True, help='The ID of the model to train')
    parser.add_argument('--action', type=str, required=True, help='The action to perform')
    parser.add_argument('--epochs', type=int, default=10, help='Number of epochs for training')
    parser.add_argument('--batch_size', type=int, default=16, help='Batch size for training')
    parser.add_argument('--learning_rate', type=float, default=0.001, help='Learning rate for training')
    parser.add_argument('--dataset_id', type=str, required=True, help='Dataset ID for training')
    parser.add_argument('--imgsz', type=int, default=640, help='Image size for training')

    args = parser.parse_args()

    if args.action != "fine_tune":
        logger.error(f"Unsupported action: {args.action}")
        sys.exit(1)

    model_info = JSONHandler.read_json(DOWNLOADED_MODELS_PATH).get(args.model_id)
    if not model_info:
        logger.error(f"Model info not found for {args.model_id}")
        sys.exit(1)

    try:
        model = UltralyticsModel(args.model_id)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.load(device, model_info)

        # Prepare training data
        training_data = {
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "learning_rate": args.learning_rate,
            "dataset_id": args.dataset_id,
            "imgsz": args.imgsz,
            "verbose": True  
        }

        # Train the model
        result = model.train(training_data)
        if "error" in result:
            logger.error(f"Training failed: {result['error']}")
            sys.exit(1)  # Exit with failure

        # If successful, the model is added to the library
        result_data = result['data']
        new_model_info = result_data['new_model_info']

        fine_tuned_model_name = new_model_info.get("model_id", "unknown")
        print(fine_tuned_model_name)

        add_model_to_library(new_model_info)

        logger.info("Fine-tuning completed successfully.")
        sys.exit(0)  # Exit with success

    except Exception as e:
        logger.error(f"An error occurred during the fine-tuning process: {e}")
        sys.exit(1) 

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
