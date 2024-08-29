import soundfile as sf
import uuid
import os
import logging
import base64
import io
from backend.core.config import ROOT_DIR

logger = logging.getLogger(__name__)

def process_audio_output(audio_data):
    try:
        # Generate a unique filename for the audio
        audio_filename = f"result_{uuid.uuid4().hex}.wav"
        output_dir = os.path.join(ROOT_DIR, "static", "results")
        audio_path = os.path.join(output_dir, audio_filename)
        logger.info(f"Processing audio for {audio_path}")
        
        # Ensure the directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert the audio data to a numpy array if it's a list
        import numpy as np
        audio_array = np.array(audio_data["audio"]) if isinstance(audio_data["audio"], list) else audio_data["audio"]
        
        # Save the audio into a BytesIO object
        buffer = io.BytesIO()
        sf.write(buffer, audio_array.squeeze(), audio_data["sampling_rate"], format='wav')
        buffer.seek(0)
        
        # Read the BytesIO object and encode to base64
        audio_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        
        # Save the audio file (optional, for debugging or if needed)
        sf.write(audio_path, audio_array.squeeze(), audio_data["sampling_rate"])
        logger.info(f"Audio saved to {audio_path}")
        
        return {
            "status": "success",
            "audio_content": audio_base64,
            "audio_url": f"/static/results/{audio_filename}"
        }
    except Exception as e:
        logger.error(f"Error processing audio output: {str(e)}")
        raise Exception(f"Error processing audio output: {str(e)}")
