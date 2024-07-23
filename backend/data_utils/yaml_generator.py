import os
import yaml

def generate_yolo_yaml(dataset_dir: str, yaml_path: str, class_names: list):
    try:
        # Ensure path is normalised
        dataset_dir = os.path.normpath(dataset_dir)
        train_path = os.path.normpath(os.path.join(dataset_dir, 'train.txt'))
        val_path = os.path.normpath(os.path.join(dataset_dir, 'val.txt'))

        # Create YAML content
        yaml_content = {
            'path': dataset_dir,  # Using the absolute path to the dataset directory
            'train': train_path,  # Both train and val are using absolute path
            'val': val_path,      
            'nc': len(class_names),
            'names': {i: name for i, name in enumerate(class_names)}
        }

        # Write YAML file
        with open(yaml_path, 'w') as f:
            yaml.dump(yaml_content, f, default_flow_style=False)

        print(f"YOLO YAML file generated at {yaml_path}")
    except Exception as e:
        print(f"Error creating YAML file: {str(e)}")
        raise
