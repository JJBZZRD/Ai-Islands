import os
import yaml

def generate_yolo_yaml(dataset_dir: str, yaml_path: str):
    try:
        # Read class names from obj.names file
        obj_names_path = os.path.join(dataset_dir, 'obj.names')
        with open(obj_names_path, 'r') as f:
            class_names = [line.strip() for line in f.readlines()]

        # Create YAML content
        yaml_content = {
            'path': dataset_dir,
            'train': 'images/train',
            'val': 'images/val',
            'test': 'images/test',
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