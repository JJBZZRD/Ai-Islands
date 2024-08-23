import argparse
import logging
import sys
import os
import torch
import shutil

# Adding the root directory of the project to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.core.config import ROOT_DIR
from backend.models.ultralytics_model import UltralyticsModel
from backend.data_utils.json_handler import JSONHandler
from backend.core.config import DOWNLOADED_MODELS_PATH
from backend.controlers.library_control import LibraryControl
from backend.controlers.model_control import ModelControl

logger = logging.getLogger(__name__)

def clean_output(output):
    problematic_chars = ['â', '€', '¦', '']
    for char in problematic_chars:
        output = output.replace(char, '')
    return output

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
        "imgsz": args.imgsz,
        "verbose": True  # Enable verbose output
    }

    # Train the model
    result = model.train(training_data)
    if "error" in result:
        logger.error(f"Training failed: {result['error']}")
    else:
        logger.info(f"Training completed successfully: {result['message']}")

        # Finding the best.pt file in the runs/detect/train folder
        runs_folder = os.path.join('runs', 'detect', 'train')
        best_pt_path = None
        for root, dirs, files in os.walk(runs_folder):
            if 'best.pt' in files:
                best_pt_path = os.path.join(root, 'best.pt')
                break

        if not best_pt_path:
            logger.error("best.pt file not found after training")
            return

        suffix = model.get_next_suffix(args.model_id)
        trained_model_name = f"{args.model_id}_{suffix}.pt"
        
        # Save the trained model to the ultralytics folder
        base_dir = os.path.join('data', 'downloads', 'ultralytics')
        trained_model_dir = os.path.join(base_dir, f"{args.model_id}_{suffix}")
        os.makedirs(trained_model_dir, exist_ok=True)
        
        trained_model_path = os.path.join(trained_model_dir, trained_model_name)
        shutil.copy(best_pt_path, trained_model_path)

        logger.info(f"Model trained on {training_data['dataset_id']} for {args.epochs} epochs with batch size {args.batch_size}, learning rate {args.learning_rate}, and image size {args.imgsz}. Model saved to {trained_model_path}")

        new_model_info = {
            "model_id": f"{args.model_id}_{suffix}",
            "base_model": f"{args.model_id}_{suffix}",
            "dir": trained_model_dir,
            "model_desc": f"Fine-tuned {args.model_id} model",
            "is_customised": True,
            "config": {
                "epochs": args.epochs,
                "batch_size": args.batch_size,
                "learning_rate": args.learning_rate,
                "imgsz": args.imgsz
            }
        }

        # Update the library with the new model information
        library_control = LibraryControl()
        library_control.add_fine_tuned_model(new_model_info)
        logger.info(f"New fine-tuned model {new_model_info['model_id']} added to library")

        # Remove the extra pretrained model file
        pretrained_model_path = os.path.join(ROOT_DIR, f"{args.model_id}.pt")
        if os.path.exists(pretrained_model_path):
            os.remove(pretrained_model_path)
            logger.info(f"Deleted pretrained model file from root directory: {pretrained_model_path}")
            
        # Remove the runs folder
        runs_folder = os.path.join(ROOT_DIR, 'runs')
        if os.path.exists(runs_folder) and os.path.isdir(runs_folder):
            shutil.rmtree(runs_folder)
            logger.info(f"Deleted runs folder: {runs_folder}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()