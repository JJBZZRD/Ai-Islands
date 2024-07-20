import os
import logging

logger = logging.getLogger(__name__)

def validate_dataset(dataset_path: str) -> str:
    yolo_detected = False
    pascal_voc_detected = False
    coco_detected = False

    logger.debug(f"Starting dataset validation for path: {dataset_path}")

    for root, dirs, files in os.walk(dataset_path):
        logger.debug(f"Walking through directory: {root}, Directories: {dirs}, Files: {files}")
        if 'images' in dirs and 'labels' in dirs:
            for file in files:
                file_path = os.path.join(root, file)
                logger.debug(f"Checking file: {file_path}")
                if file.endswith(".txt"):
                    with open(file_path, 'r') as f:
                        content = f.readline().strip()
                        logger.debug(f"Read content from {file_path}: {content}")
                        if len(content.split()) == 5 and all(part.replace('.', '', 1).isdigit() for part in content.split()):
                            yolo_detected = True
                            logger.debug("YOLO format detected")
                            break
                elif file.endswith(".xml"):
                    pascal_voc_detected = True
                    logger.debug("Pascal VOC format detected")
                elif file == "instances_train.json" or file == "instances_val.json":
                    coco_detected = True
                    logger.debug("COCO format detected")
            break

    if yolo_detected:
        return 'yolo'
    elif pascal_voc_detected:
        return 'pascal_voc'
    elif coco_detected:
        return 'coco'
    else:
        return 'unknown'