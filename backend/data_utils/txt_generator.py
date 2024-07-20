import os

def create_txt_files(dataset_path):
    train_images_path = os.path.join(dataset_path, 'images', 'train')
    val_images_path = os.path.join(dataset_path, 'images', 'val')
    
    train_txt_path = os.path.join(dataset_path, 'train.txt')
    val_txt_path = os.path.join(dataset_path, 'val.txt')
    
    with open(train_txt_path, 'w') as train_file:
        for root, _, files in os.walk(train_images_path):
            for file in files:
                if file.endswith(('.jpg', '.jpeg', '.png')):
                    train_file.write(os.path.join(root, file) + '\n')
    
    with open(val_txt_path, 'w') as val_file:
        for root, _, files in os.walk(val_images_path):
            for file in files:
                if file.endswith(('.jpg', '.jpeg', '.png')):
                    val_file.write(os.path.join(root, file) + '\n')
    
    print(f"Generated train.txt at {train_txt_path}")
    print(f"Generated val.txt at {val_txt_path}")