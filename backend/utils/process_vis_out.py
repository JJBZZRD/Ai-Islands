import base64
from io import BytesIO
from PIL import Image, ImageDraw
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
    
    # Generate a unique filename for the image
    image_filename = f"result_{uuid.uuid4().hex}.png"
    output_dir = os.path.join("static", "results")
    image_path = os.path.join(output_dir, image_filename)
    
    # Ensure the directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the image
    result_image.save(image_path)

    # Process the output to ensure it's JSON serializable
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
            # Convert PIL Image to base64 string
            buffered = io.BytesIO()
            obj.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode('utf-8')
        elif hasattr(obj, '__dict__'):
            return _ensure_json_serializable(obj.__dict__)
        else:
            return str(obj)
        
def visualise_output(image, output, task):
    """Creating visualisation based on the task, as each gives diffrent output"""
    if task == 'image-classification':
        result_image = visualise_classification(image, output)
    elif task in ['object-detection', 'instance-segmentation']:
        result_image = visualise_detection(image, output)
    elif task in ['image-segmentation', 'panoptic-segmentation', 'semantic-segmentation']:
        result_image = visualise_segmentation(image, output)
    else:
        # For unknown tasks, the output will be displayed as text
        result_image = image.copy()
        draw = ImageDraw.Draw(result_image)
        _draw_text(draw, str(output), (10, 10))

    return result_image

def visualise_classification(image, output):
    # Create a figure with the image and classification results
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(image)
    ax.axis('off')

    # Add classification results as text
    for i, result in enumerate(output):
        label = result['label']
        score = result['score']
        ax.text(10, 30 + i * 30, f"{label}: {score:.2f}", fontsize=12, 
                bbox=dict(facecolor='white', alpha=0.7))

    # Convert plot to image
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    buf.seek(0)
    result_image = Image.open(buf)

    plt.close(fig)
    return result_image

def visualise_detection(image, output):
    draw_image = image.copy()
    draw = ImageDraw.Draw(draw_image)
    
    for idx, item in enumerate(output):
        _visualise_detection(draw_image, draw, item, idx)
    
    return draw_image

def visualise_segmentation(image, output):
    """# Create a blank mask with the same size as the input image
    mask = Image.new('L', image.size, 0)
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
        
        # Draw this instance on the main mask
        mask = Image.composite(Image.new('L', mask.size, 255), mask, binary_mask)

    # Convert mask to RGB
    mask_rgb = Image.new('RGB', image.size)
    for label, color in label_to_color.items():
        label_mask = mask.point(lambda p: p if p == 255 else 0)
        colored_label_mask = Image.new('RGB', mask.size, color)
        mask_rgb = Image.composite(colored_label_mask, mask_rgb, label_mask)

    # Blend the mask with the original image
    blended = Image.blend(image.convert('RGB'), mask_rgb, 0.5)

    return blended"""
    
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

def _visualise_detection(image, draw, item, idx):
    color = _get_color(idx)
    
    if 'box' in item:
        box = item['box']
        label = item.get('label', 'Unknown')
        score = item.get('score', 0)
        _draw_box(draw, box, color)
        _draw_text(draw, f"{label}: {score:.2f}", (box[0], box[1] - 10), color)
    
    if 'mask' in item:
        mask = item['mask']
        _apply_mask(image, mask, color)

def _get_color(idx):
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
    return colors[idx % len(colors)]

def _draw_box(draw, box, color):
    draw.rectangle(box, outline=color, width=2)

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
    """color_map = []
    for i in range(num_classes):
        r = int((i * 100 + 50) % 255)
        g = int((i * 150 + 100) % 255)
        b = int((i * 200 + 150) % 255)
        color_map.append((r, g, b))
    return color_map"""
    
    color_map = []
    for i in range(num_classes):
        r = int((i * 100 + 50) % 255)
        g = int((i * 150 + 100) % 255)
        b = int((i * 200 + 150) % 255)
        color_map.append((r, g, b))
    return color_map