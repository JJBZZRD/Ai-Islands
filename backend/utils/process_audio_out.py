import soundfile as sf
import uuid
import os
import logging
from backend.core.config import ROOT_DIR


logger = logging.getLogger(__name__)

def process_audio_output(audio_data):
    
    # Generate a unique filename for the audio
    audio_filename = f"result_{uuid.uuid4().hex}.wav"
    output_dir_1 = os.path.join(ROOT_DIR, "static", "results")
    output_dir_2 = os.path.join(ROOT_DIR, "static", "results")
    audio_path = os.path.join(ROOT_DIR, output_dir_2, audio_filename)
    logger.info(f"Saving the audio to {audio_path}")
    
    # Ensure the directory exists
    os.makedirs(output_dir_1, exist_ok=True)
    os.makedirs(output_dir_2, exist_ok=True)
    
    # Save the audio into a wav file
    sf.write(audio_path, audio_data["audio"].squeeze(), audio_data["sampling_rate"])
    logger.info(f"Audio saved to {audio_path}")
    
    audio_data.update({"audio": audio_data["audio"].tolist()})
    audio_data.update({"audio_url": f"/static/results/{audio_filename}"})
    
    logger.info("auto data updated successfully")
    return audio_data
