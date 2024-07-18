import os

def generate_yaml_file(dataset_dir: str, yaml_path: str):
    """
    Generate a YAML configuration file for the YOLO dataset.

    Args:
        dataset_dir (str): Path to the dataset directory.
        yaml_path (str): Path to save the generated YAML file.
    """
    # Define the structure of the YAML file
    class_names = get_class_names(os.path.join(dataset_dir, 'obj.names'))
    yaml_content = {
        'path': dataset_dir,
        'train': os.path.join(dataset_dir, 'images/train'),
        'val': os.path.join(dataset_dir, 'images/val'),
        'test': os.path.join(dataset_dir, 'images/test'),  # If you have a test set
        'nc': len(class_names),
        'names': class_names
    }

    # Write the YAML file
    with open(yaml_path, 'w') as yaml_file:
        yaml_file.write(f"path: {yaml_content['path']}\n")
        yaml_file.write(f"train: {yaml_content['train']}\n")
        yaml_file.write(f"val: {yaml_content['val']}\n")
        yaml_file.write(f"test: {yaml_content['test']}\n")
        yaml_file.write(f"nc: {yaml_content['nc']}\n")
        yaml_file.write("names: \n")
        for name in yaml_content['names']:
            yaml_file.write(f"  - {name}\n")

def get_class_names(names_file: str) -> list:
    """
    Get the class names from the obj.names file.

    Args:
        names_file (str): Path to the obj.names file.

    Returns:
        list: List of class names.
    """
    with open(names_file, 'r') as file:
        class_names = [line.strip() for line in file if line.strip()]  # Strip whitespace and ignore empty lines
    return class_names

