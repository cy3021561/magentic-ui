import numpy as np
import soundfile as sf
from pathlib import Path
from .exceptions import AudioFormatError

def load_audio(file_path: str | Path) -> np.ndarray:
    """Load audio file and convert to the correct format."""
    try:
        # Explicitly specify dtype as float32 when reading
        audio, sample_rate = sf.read(str(file_path), dtype=np.float32)
        return audio
    except Exception as e:
        raise AudioFormatError(f"Failed to load audio file: {str(e)}")

def preprocess_audio(audio: np.ndarray, target_sample_rate: int) -> np.ndarray:
    """Preprocess audio data for transcription."""
    # Convert to mono if stereo
    if len(audio.shape) > 1:
        audio = audio.mean(axis=1)
    
    # Normalize audio
    audio = audio / np.max(np.abs(audio))
    
    # Ensure correct dtype for Whisper (float32)
    audio = audio.astype(np.float32)
    
    return audio