class TranscriptionError(Exception):
    """Base exception for transcription-related errors."""
    pass

class AudioFormatError(TranscriptionError):
    """Raised when audio format is not supported."""
    pass

class ModelLoadError(TranscriptionError):
    """Raised when the transcription model fails to load."""
    pass