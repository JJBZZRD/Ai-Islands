import os
import logging

logger = logging.getLogger(__name__)    

def create_txt_files(dataset_path):
    train_images_path = os.path.join(dataset_path, 'images', 'train')
    val_images_path = os.path.join(dataset_path, 'images', 'val')
    
    train_txt_path = os.path.join(dataset_path, 'train.txt')
    val_txt_path = os.path.join(dataset_path, 'val.txt')
    
    try:
        # Checking if train and val directories exist
        if not os.path.exists(train_images_path):
            raise FileNotFoundError(f"Training images directory not found: {train_images_path}")
        if not os.path.exists(val_images_path):
            raise FileNotFoundError(f"Validation images directory not found: {val_images_path}")
        
        # Create train.txt
        with open(train_txt_path, 'w') as train_file:
            for root, _, files in os.walk(train_images_path):
                for file in files:
                    if file.endswith(('.jpg', '.jpeg', '.png')):
                        train_file.write(os.path.join(root, file) + '\n')
        logger.info(f"Generated train.txt at {train_txt_path}")
        
        # Create val.txt
        with open(val_txt_path, 'w') as val_file:
            for root, _, files in os.walk(val_images_path):
                for file in files:
                    if file.endswith(('.jpg', '.jpeg', '.png')):
                        val_file.write(os.path.join(root, file) + '\n')
        logger.info(f"Generated val.txt at {val_txt_path}")
        
    except Exception as e:
        logger.error(f"Error creating txt files: {e}")
        raise