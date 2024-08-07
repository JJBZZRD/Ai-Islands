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

"""
This will process the output of vision model to provide a visualisation, currently the output is will be stored in a folder but later
later it should be linked to front end so user can view directly the result of the annotated image and not saved to a folder
As a side note:
- tasks means the vision task like object detection, etc
- output is the output from the vision model
- image is the original image that the model is applied to
"""

def process_vision_output(image, output, task):
    result_image = visualise_output(image, output, task)
    
    # generate a unique filename for the image
    image_filename = f"result_{uuid.uuid4().hex}.png"
    output_dir = os.path.join("static", "results")
    image_path = os.path.join(output_dir, image_filename)
    
    # creating directory if does not exist
    os.makedirs(output_dir, exist_ok=True)
    
    # save the image
    result_image.save(image_path)

    # processing the output to ensure it is json serializable
    processed_output = _ensure_json_serializable(output)
    #processed_output = output
    
    return {
        "image_url": f"/static/results/{image_filename}",
        "detections": processed_output
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
    """Creating visualisation based on the task, as each gives diffrent output"""
    if task in ['object-detection', 'zero-shot-object-detection']:
        result_image = visualise_detection(image, output)
    elif task in ['image-segmentation', 'panoptic-segmentation', 'semantic-segmentation']:
        result_image = visualise_segmentation(image, output)
    else:
        # For unknown tasks, the output will be displayed as text
        result_image = image.copy()
        draw = ImageDraw.Draw(result_image)
        _draw_text(draw, str(output), (10, 10))

    return result_image

def visualise_detection(image, output):
    result_image = image.copy()
    draw = ImageDraw.Draw(result_image)
    
    for idx, item in enumerate(output):
        color = _get_color(idx)
        
        if 'coordinates' in item:  # YOLO format
            coordinates = item['coordinates']
            label = item.get('class', 'Unknown')
            score = item.get('confidence', 0)
            box = coordinates
        elif 'box' in item:  # zero-shot object detection format
            box = [item['box']['xmin'], item['box']['ymin'], item['box']['xmax'], item['box']['ymax']]
            label = item.get('label', 'Unknown')
            score = item.get('score', 0)
        else:
            continue  # skip this item if it doesn't have the expected format

        _draw_box_and_label(draw, box, label, score, color)
        
        if 'mask' in item:
            mask = item['mask']
            _apply_mask(result_image, mask, color)
    
    return result_image

def _draw_box_and_label(draw, box, label, score, color):
    # draw the bounding box
    draw.rectangle(box, outline=color, width=3)
    
    # prepare the label text
    label_text = f"{label}: {score:.2f}"
    
    # get text size using textbbox
    font = ImageFont.truetype("arial.ttf", 16)
    text_width, text_height = draw.textbbox((0, 0), label_text, font=font)[2:]  # Use textbbox to get the size

    # calculate text position
    text_x = box[0]
    text_y = max(0, box[1] - text_height - 5)  # Ensure text doesn't go above image
    
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
    # Create a blank mask with the same size as the input image
    mask = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(mask)

    # Generate a color map for the labels
    unique_labels = set(item['label'] for item in output)
    color_map = _generate_color_map(len(unique_labels))
    label_to_color = dict(zip(unique_labels, color_map))

    # Draw each instance on the mask
    for item in output:
        label = item['label']
        instance_mask = item['mask']
        color = label_to_color[label]

        # Convert to binary mask (0 or 255)
        binary_mask = instance_mask.point(lambda p: 255 if p > 128 else 0)

        # Apply color to the binary mask
        color_mask = Image.new('RGBA', mask.size, color + (150,))  # Use alpha for transparency
        mask = Image.composite(color_mask, mask, binary_mask)

    # Blend the mask with the original image
    blended = Image.alpha_composite(image.convert('RGBA'), mask)

    return blended.convert('RGB')

def _draw_text(draw, text, position, color=(255, 255, 255)):
    draw.text(position, text, fill=color)

def _apply_mask(image, mask, color):
    mask_np = np.array(mask)
    color_mask = np.zeros((mask_np.shape[0], mask_np.shape[1], 3), dtype=np.uint8)
    color_mask[mask_np > 0.5] = color
    image_np = np.array(image)
    blended = cv2.addWeighted(image_np, 0.7, color_mask, 0.3, 0)
    image.paste(Image.fromarray(blended), (0, 0))

def _generate_color_map(num_classes):
    color_map = []
    for i in range(num_classes):
        r = int((i * 100 + 50) % 255)
        g = int((i * 150 + 100) % 255)
        b = int((i * 200 + 150) % 255)
        color_map.append((r, g, b))
    return color_map