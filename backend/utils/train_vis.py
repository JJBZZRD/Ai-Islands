import argparse
import logging
import sys
import os
import torch

# Adding the root directory of the project to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.models.ultralytics_model import UltralyticsModel
from backend.data_utils.json_handler import JSONHandler
from backend.core.config import DOWNLOADED_MODELS_PATH
from backend.controlers.library_control import LibraryControl
from backend.controlers.model_control import ModelControl

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Train a model")
    parser.add_argument('--model_id', type=str, required=True, help='The ID of the model to train')
    parser.add_argument('--action', type=str, required=True, help='The action to perform (e.g., "fine_tune")')
    parser.add_argument('--epochs', type=int, default=10, help='Number of epochs for training')
    parser.add_argument('--batch_size', type=int, default=16, help='Batch size for training')
    parser.add_argument('--learning_rate', type=float, default=0.001, help='Learning rate for training')
    parser.add_argument('--dataset_id', type=str, required=True, help='Dataset ID for training')
    parser.add_argument('--imgsz', type=int, default=640, help='Image size for training')

    args = parser.parse_args()

    if args.action != "fine_tune":
        logger.error(f"Unsupported action: {args.action}")
        return

    # Load model info
    model_info = JSONHandler.read_json(DOWNLOADED_MODELS_PATH).get(args.model_id)
    if not model_info:
        logger.error(f"Model info not found for {args.model_id}")
        return

    # Initialise the model
    model = UltralyticsModel(args.model_id)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Check if the model is already loaded 
    model_control = ModelControl()
    if not model_control.is_model_loaded(args.model_id):
        model.load(device, model_info)

    # Prepare training data
    training_data = {
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "dataset_id": args.dataset_id,
        "imgsz": args.imgsz
    }

    # Train the model
    result = model.train(training_data)
    if "error" in result:
        logger.error(f"Training failed: {result['error']}")
    else:
        logger.info(f"Training completed successfully: {result['message']}")

        # Update the library with the new model information
        library_control = LibraryControl()
        new_model_info = result["data"]["new_model_info"]
        new_model_id = new_model_info["model_id"]

        # Get the original model info
        original_model_info = model_info

        # Create a new entry 
        updated_model_info = original_model_info.copy()
        updated_model_info.update(new_model_info)

        updated_model_info["is_customised"] = True
        updated_model_info["base_model"] = new_model_id  

        # Add the new model to the library
        library_control.add_fine_tuned_model(updated_model_info)
        logger.info(f"New fine-tuned model {new_model_id} added to library")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()