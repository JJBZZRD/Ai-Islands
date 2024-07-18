# backend/data_utils/dataset_validation.py

import os

def validate_dataset(dataset_path: str) -> str:
    """
    Validate if the dataset is in YOLO, Pascal VOC, or COCO.

    Args:
        dataset_path (str): Path to the uploaded dataset.

    Returns:
        str: The detected format ('yolo', 'pascal_voc', 'coco') or 'unknown' if the format is not recognized.
    """
    yolo_detected = False
    pascal_voc_detected = False
    coco_detected = False

    for root, dirs, files in os.walk(dataset_path):
        for file in files:
            if file.endswith(".txt"):
                # Check for YOLO format
                with open(os.path.join(root, file), 'r') as f:
                    content = f.readline()
                    if len(content.split()) == 5:
                        yolo_detected = True
            elif file.endswith(".xml"):
                # Check for Pascal VOC format
                pascal_voc_detected = True

    if yolo_detected:
        return 'yolo'
    elif pascal_voc_detected:
        return 'pascal_voc'
    elif coco_detected:
        return 'coco'
    else:
        return 'unknown'
