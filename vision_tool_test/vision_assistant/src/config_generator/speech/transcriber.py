import wave
import numpy as np
from pathlib import Path
import whisper
from .exceptions import AudioFormatError, ModelLoadError, TranscriptionError
from .utils import load_audio, preprocess_audio


class TranscriberConfig:
    """Configuration settings for speech transcription."""
    
    def __init__(self):
        self.language = "en"
        self.sample_rate = 16000
        self.enable_punctuation = True
        self.enable_timestamps = False
        self.model_type = "base"  # or "large" for more accuracy

    def update(self, **kwargs):
        """Update configuration with provided parameters."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Invalid configuration parameter: {key}")

class SpeechTranscriber:
    """Main class for handling speech-to-text transcription."""
    
    def __init__(self, config: TranscriberConfig = None):
        self.config = config or TranscriberConfig()
        try:
            self.model = whisper.load_model(self.config.model_type)
        except Exception as e:
            raise ModelLoadError(f"Failed to load Whisper model: {str(e)}")
    
    def transcribe_file(self, audio_path: str | Path) -> dict:
        """
        Transcribe speech from an audio file.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            dict: Transcription results including text and metadata
        """
        try:
            # Load and preprocess audio
            audio = load_audio(audio_path)
            processed_audio = preprocess_audio(audio, self.config.sample_rate)
            
            # Perform transcription
            result = self.model.transcribe(
                processed_audio,
                language=self.config.language,
                task="transcribe"
            )
            
            return {
                'text': result['text'],
                'segments': result['segments'] if self.config.enable_timestamps else None,
                'language': result['language']
            }
            
        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {str(e)}")
    
    def transcribe_stream(self, audio_stream) -> str:
        """
        Transcribe speech from an audio stream (real-time audio).
        
        Args:
            audio_stream: Audio stream buffer
            
        Returns:
            str: Transcribed text
        """
        # Implementation for real-time transcription
        raise NotImplementedError("Real-time transcription not yet implemented")