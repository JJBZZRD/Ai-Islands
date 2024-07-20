import os

def validate_dataset(dataset_path: str) -> str:
    yolo_detected = False
    pascal_voc_detected = False
    coco_detected = False

    for root, dirs, files in os.walk(dataset_path):
        if 'images' in dirs and 'labels' in dirs:
            for file in files:
                if file.endswith(".txt"):
                    with open(os.path.join(root, file), 'r') as f:
                        content = f.readline().strip()
                        if len(content.split()) == 5 and all(part.replace('.', '', 1).isdigit() for part in content.split()):
                            yolo_detected = True
                            break
                elif file.endswith(".xml"):
                    pascal_voc_detected = True
                elif file == "instances_train.json" or file == "instances_val.json":
                    coco_detected = True
            break

    if yolo_detected:
        return 'yolo'
    elif pascal_voc_detected:
        return 'pascal_voc'
    elif coco_detected:
        return 'coco'
    else:
        return 'unknown'