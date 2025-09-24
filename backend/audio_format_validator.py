"""
Audio Format Validator
Provides robust audio format validation and conversion for OpenAI Whisper API compatibility.
Handles various audio formats and provides detailed error reporting.
"""

import base64
import tempfile
import os
import io
import logging
from typing import Optional, Tuple, Dict, Any
import wave
import subprocess
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

class AudioFormatValidator:
    """Validates and converts audio formats for OpenAI Whisper API compatibility"""
    
    # OpenAI Whisper supported formats
    SUPPORTED_FORMATS = {
        '.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm'
    }
    
    # Maximum file size (25MB for OpenAI)
    MAX_FILE_SIZE = 25 * 1024 * 1024
    
    @staticmethod
    def validate_audio_data(audio_base64: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate and analyze base64 audio data
        
        Returns:
            - is_valid: bool
            - error_message: str
            - metadata: dict with file info
        """
        try:
            # Decode base64 data
            audio_data = base64.b64decode(audio_base64)
            
            # Check file size
            file_size = len(audio_data)
            if file_size == 0:
                return False, "Empty audio data", {}
            
            if file_size > AudioFormatValidator.MAX_FILE_SIZE:
                return False, f"File too large: {file_size} bytes (max: {AudioFormatValidator.MAX_FILE_SIZE})", {}
            
            # Detect format by magic bytes
            format_info = AudioFormatValidator._detect_format(audio_data)
            
            metadata = {
                "file_size": file_size,
                "detected_format": format_info.get("format"),
                "mime_type": format_info.get("mime_type"),
                "is_supported": format_info.get("is_supported", True)  # Default to True for unknown formats
            }
            
            # Only block explicitly unsupported formats (like OGG, FLAC)
            # Let "unknown" formats pass through - OpenAI will handle them
            explicitly_unsupported = format_info.get("format") in ["ogg", "flac"]
            
            if explicitly_unsupported:
                supported_list = ", ".join(AudioFormatValidator.SUPPORTED_FORMATS)
                return False, f"Unsupported audio format: {format_info.get('format')}. Supported: {supported_list}", metadata
            
            # Allow unknown formats to pass through - they might be valid
            if format_info.get("format") == "unknown":
                logger.info(f"Unknown audio format detected ({file_size} bytes) - allowing OpenAI to process")
                metadata["is_supported"] = True  # Let it through
            
            return True, "Valid audio format", metadata
            
        except Exception as e:
            logger.error(f"Audio validation error: {str(e)}")
            return False, f"Audio validation failed: {str(e)}", {}
    
    @staticmethod
    def _detect_format(data: bytes) -> Dict[str, Any]:
        """Detect audio format from magic bytes"""
        
        # Check if data is long enough for magic bytes
        if len(data) < 12:
            return {"format": "unknown", "mime_type": "unknown", "is_supported": False}
        
        # WAV format
        if data[:4] == b'RIFF' and data[8:12] == b'WAVE':
            return {
                "format": "wav", 
                "mime_type": "audio/wav", 
                "is_supported": True,
                "extension": ".wav"
            }
        
        # MP3 format
        if data[:3] == b'ID3' or (data[:2] == b'\xff\xfb'):
            return {
                "format": "mp3", 
                "mime_type": "audio/mpeg", 
                "is_supported": True,
                "extension": ".mp3"
            }
        
        # M4A/AAC format
        if data[4:8] == b'ftyp' and (b'M4A ' in data[8:16] or b'mp42' in data[8:16]):
            return {
                "format": "m4a", 
                "mime_type": "audio/mp4", 
                "is_supported": True,
                "extension": ".m4a"
            }
        
        # WebM format
        if data[:4] == b'\x1a\x45\xdf\xa3':
            return {
                "format": "webm", 
                "mime_type": "audio/webm", 
                "is_supported": True,
                "extension": ".webm"
            }
        
        # OGG format (not supported by OpenAI but common)
        if data[:4] == b'OggS':
            return {
                "format": "ogg", 
                "mime_type": "audio/ogg", 
                "is_supported": False,
                "extension": ".ogg"
            }
        
        # FLAC format (not supported by OpenAI but common)
        if data[:4] == b'fLaC':
            return {
                "format": "flac", 
                "mime_type": "audio/flac", 
                "is_supported": False,
                "extension": ".flac"
            }
        
        # Unknown format
        return {"format": "unknown", "mime_type": "unknown", "is_supported": False}
    
    @staticmethod
    def create_temp_audio_file(audio_data: bytes, format_info: Dict[str, Any]) -> Tuple[str, str]:
        """
        Create a temporary audio file with proper extension
        
        Returns:
            - temp_file_path: str
            - cleanup_path: str (same as temp_file_path for cleanup)
        """
        try:
            # Determine appropriate file extension
            extension = format_info.get("extension", ".wav")
            
            # Create temporary file with correct extension
            with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            logger.info(f"Created temporary audio file: {temp_path} ({len(audio_data)} bytes, {format_info.get('format', 'unknown')} format)")
            
            return temp_path, temp_path
            
        except Exception as e:
            logger.error(f"Error creating temporary audio file: {str(e)}")
            raise Exception(f"Failed to create temporary audio file: {str(e)}")
    
    @staticmethod
    def convert_to_supported_format(audio_data: bytes, source_format: str) -> Tuple[bytes, Dict[str, Any]]:
        """
        Convert unsupported audio format to WAV (widely supported)
        
        This is a placeholder for future format conversion if needed.
        Currently, we recommend users provide supported formats.
        """
        # For now, return original data
        # Future: implement conversion using ffmpeg or similar
        return audio_data, {
            "format": "wav",
            "mime_type": "audio/wav",
            "is_supported": True,
            "extension": ".wav",
            "converted": False
        }
    
    @staticmethod
    def cleanup_temp_file(file_path: str) -> None:
        """Safely clean up temporary audio file"""
        try:
            if file_path and os.path.exists(file_path):
                os.unlink(file_path)
                logger.debug(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary file {file_path}: {str(e)}")

    @staticmethod
    def get_audio_info(file_path: str) -> Dict[str, Any]:
        """Get detailed audio file information (optional, for debugging)"""
        try:
            # Basic file info
            file_stat = os.stat(file_path)
            info = {
                "file_size": file_stat.st_size,
                "file_path": file_path
            }
            
            # Try to get WAV file details if it's a WAV file
            if file_path.lower().endswith('.wav'):
                try:
                    with wave.open(file_path, 'rb') as wav_file:
                        info.update({
                            "sample_rate": wav_file.getframerate(),
                            "channels": wav_file.getnchannels(),
                            "sample_width": wav_file.getsampwidth(),
                            "duration_seconds": wav_file.getnframes() / wav_file.getframerate()
                        })
                except:
                    pass  # Not a valid WAV file or corrupted
            
            return info
            
        except Exception as e:
            logger.warning(f"Could not get audio info for {file_path}: {str(e)}")
            return {"error": str(e)}
