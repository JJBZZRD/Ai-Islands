import os
import yaml

def generate_yolo_yaml(dataset_dir: str, yaml_path: str, class_names: list):
    try:
        # Create YAML content
        yaml_content = {
            'path': dataset_dir,
            'train': os.path.join(dataset_dir, 'train.txt'),
            'val': os.path.join(dataset_dir, 'val.txt'),
            'nc': len(class_names),
            'names': class_names
        }

        # Write YAML file
        with open(yaml_path, 'w') as f:
            yaml.dump(yaml_content, f, default_flow_style=False)

        print(f"YOLO YAML file generated at {yaml_path}")
    except Exception as e:
        print(f"Error creating YAML file: {str(e)}")
        raise