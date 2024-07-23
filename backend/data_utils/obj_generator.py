import os

def create_obj_data(dataset_path, num_classes):
    obj_data_content = f"""classes={num_classes}
train={os.path.join(dataset_path, 'train.txt')}
valid={os.path.join(dataset_path, 'val.txt')}
names={os.path.join(dataset_path, 'obj.names')}
backup=backup/
"""
    obj_data_path = os.path.join(dataset_path, 'obj.data')
    with open(obj_data_path, 'w') as f:
        f.write(obj_data_content)
    print(f"Generated obj.data at {obj_data_path}")