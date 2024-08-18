import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2
import json
import colorsys
import os
import uuid
import matplotlib.pyplot as plt
import io
import base64
from io import BytesIO
from backend.core.config import ROOT_DIR
import logging

logger = logging.getLogger(__name__)


def process_vision_output(image, output, task):
    logger.info(f"Image type: {type(image)}")
    logger.info(f"Output type: {type(output)}")
    logger.info(f"Task: {task}")

    if isinstance(image, str):
        logger.warning(f"Image is a string: {image}")
        try:
            image = Image.open(image)
        except Exception as e:
            logger.error(f"Error opening image: {str(e)}")
            raise ValueError(f"Error opening image: {str(e)}")

    if not isinstance(image, Image.Image):
        raise ValueError(f"Expected PIL.Image.Image, got {type(image)}")

    logger.info(f"Image size: {image.size}")

    if not isinstance(output, dict):
        output = {"predictions": output}

    try:
        result_image = visualise_output(image, output["predictions"], task)
    except Exception as e:
        logger.error(f"Error in visualise_output: {str(e)}")
        raise ValueError(f"Error visualizing output: {str(e)}")

    image_filename = f"image_result_{uuid.uuid4().hex}.png"
    output_dir = os.path.join(ROOT_DIR, "static", "results")
    image_path = os.path.join(output_dir, image_filename)

    os.makedirs(output_dir, exist_ok=True)
    result_image.save(image_path)

    return {
        "image_url": image_path
    }

def _ensure_json_serializable(obj):
    try:
        json.dumps(obj)
        return obj
    except TypeError:
        if isinstance(obj, (list, tuple)):
            return [_ensure_json_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: _ensure_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, Image.Image):
            # converting image to base64
            buffered = io.BytesIO()
            obj.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode('utf-8')
        elif hasattr(obj, '__dict__'):
            return _ensure_json_serializable(obj.__dict__)
        else:
            return str(obj)
        
def visualise_output(image, output, task):
    if task in ['object-detection', 'zero-shot-object-detection']:
        result_image = visualise_detection(image, output)
    elif task in ['image-segmentation', 'panoptic-segmentation', 'semantic-segmentation']:
        result_image = visualise_segmentation(image, output)
    else:
        result_image = image.copy()
        draw = ImageDraw.Draw(result_image)
        _draw_text(draw, str(output), (10, 10))

    return result_image

def visualise_detection(image, output):
    result_image = image.copy()
    draw = ImageDraw.Draw(result_image)
    
    items = output if isinstance(output, list) else output.get('predictions', [])
    
    for idx, item in enumerate(items):
        color = _get_color(idx)
        
        if 'coordinates' in item:  # YOLO format
            box = item['coordinates']
            label = item.get('class', 'Unknown')
            score = item.get('confidence', 0)
        elif 'box' in item:  # zero-shot object detection format
            box = [item['box']['xmin'], item['box']['ymin'], item['box']['xmax'], item['box']['ymax']]
            label = item.get('label', 'Unknown')
            score = item.get('score', 0)
        else:
            continue  

        _draw_box_and_label(draw, box, label, score, color)
    
    return result_image

def _draw_box_and_label(draw, box, label, score, color):
    # draw the bounding box
    draw.rectangle(box, outline=color, width=3)
    
    # prepare the label text
    label_text = f"{label}: {score:.2f}"
    
    # get text size using textbbox
    font = ImageFont.truetype("arial.ttf", 16)
    text_width, text_height = draw.textbbox((0, 0), label_text, font=font)[2:]  

    # calculate text position
    text_x = box[0]
    text_y = max(0, box[1] - text_height - 5)  
    
    draw.rectangle([text_x, text_y, text_x + text_width, text_y + text_height], 
                   fill=(0, 0, 0, 128))
    
    # draw the text
    draw.text((text_x, text_y), label_text, fill=color, font=font)

def _get_color(idx):
    # generate a unique color for each class
    hue = (idx * 0.618033988749895) % 1
    rgb = colorsys.hsv_to_rgb(hue, 0.9, 0.9)
    return tuple(int(255 * c) for c in rgb)

def visualise_segmentation(image, output):
    mask = Image.new('RGBA', image.size, (0, 0, 0, 0))
    
    items = output if isinstance(output, list) else output.get('predictions', [])

    unique_labels = set(item['label'] for item in items)
    color_map = _generate_color_map(len(unique_labels))
    label_to_color = dict(zip(unique_labels, color_map))

    for item in items:
        label = item['label']
        instance_mask = item['mask']
        color = label_to_color[label]

        if isinstance(instance_mask, str):
            instance_mask_bytes = base64.b64decode(instance_mask)
            instance_mask = np.array(Image.open(BytesIO(instance_mask_bytes)))

            expected_size = image.size[1] * image.size[0]
            if instance_mask.size != expected_size:
                logger.warning(f"Resizing mask to match the image dimensions: {image.size}")
                instance_mask = np.resize(instance_mask, (image.size[1], image.size[0]))

            instance_mask = instance_mask.reshape((image.size[1], image.size[0]))

        # applying the mask
        color_mask = np.zeros((image.size[1], image.size[0], 4), dtype=np.uint8)
        color_mask[instance_mask > 0] = color + (150,)  #alpha for transparency

        color_mask_image = Image.fromarray(color_mask)
        mask = Image.alpha_composite(mask, color_mask_image)

    blended = Image.alpha_composite(image.convert('RGBA'), mask)
    return blended.convert('RGB')

def _generate_color_map(num_classes):
    color_map = []
    for i in range(num_classes):
        r = int((i * 100 + 50) % 255)
        g = int((i * 150 + 100) % 255)
        b = int((i * 200 + 150) % 255)
        color_map.append((r, g, b))
    return color_map

def _draw_text(draw, text, position, color=(255, 255, 255)):
    draw.text(position, text, fill=color)


