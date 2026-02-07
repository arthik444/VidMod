"""
Audio Separator Module
Uses the audio-separator library with UVR-MDX-NET models to separate
vocals from instrumental/background music for clean dubbing.
"""

import logging
import hashlib
from pathlib import Path
from typing import Tuple, Optional
import subprocess

logger = logging.getLogger(__name__)


class AudioSeparator:
    """
    Separates vocals from instrumental/background music using AI models.
    
    Uses UVR-MDX-NET-Voc_FT for a balance of speed and quality.
    Caches separated files based on audio hash to avoid re-processing.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None, ffmpeg_path: str = "ffmpeg"):
        """
        Initialize the audio separator.
        
        Args:
            cache_dir: Directory to store cached separated audio files
            ffmpeg_path: Path to ffmpeg executable
        """
        self.cache_dir = cache_dir or Path("storage/audio_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_path = ffmpeg_path
        
        # Model selection - UVR-MDX-NET-Voc_FT.onnx for speed/quality balance
        self.model_name = "UVR-MDX-NET-Voc_FT.onnx"
        
        logger.info(f"AudioSeparator initialized with model: {self.model_name}")
    
    def _get_audio_hash(self, video_path: Path) -> str:
        """
        Generate a hash of the audio track for caching purposes.
        Uses first 1MB of file + file size for fast hashing.
        """
        hasher = hashlib.md5()
        file_size = video_path.stat().st_size
        hasher.update(str(file_size).encode())
        
        # Read first 1MB for hash
        with open(video_path, 'rb') as f:
            chunk = f.read(1024 * 1024)
            hasher.update(chunk)
        
        return hasher.hexdigest()[:16]
    
    def _extract_audio(self, video_path: Path, output_path: Path) -> Path:
        """Extract audio from video to WAV format for processing."""
        logger.info(f"Extracting audio from video: {video_path}")
        
        cmd = [
            self.ffmpeg_path, "-y",
            "-i", str(video_path),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Audio extracted: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Audio extraction failed: {e.stderr}")
            raise RuntimeError(f"Failed to extract audio: {e.stderr}")
    
    def separate_vocals_and_music(
        self,
        video_path: Path,
        force_reprocess: bool = False
    ) -> Tuple[Path, Path]:
        """
        Separate vocals from instrumental/background music.
        
        Args:
            video_path: Path to input video file
            force_reprocess: If True, ignore cache and reprocess
            
        Returns:
            Tuple of (vocals_path, instrumental_path)
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        # Generate cache key from audio hash
        audio_hash = self._get_audio_hash(video_path)
        cache_subdir = self.cache_dir / audio_hash
        
        vocals_path = cache_subdir / "vocals.wav"
        instrumental_path = cache_subdir / "instrumental.wav"
        
        # Check cache
        if not force_reprocess and vocals_path.exists() and instrumental_path.exists():
            logger.info(f"CACHE HIT: Using cached separated audio for hash {audio_hash}")
            return vocals_path, instrumental_path
        
        logger.info(f"CACHE MISS: Separating audio for hash {audio_hash}")
        cache_subdir.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Extract audio from video
        temp_audio = cache_subdir / "full_audio.wav"
        self._extract_audio(video_path, temp_audio)
        
        # Step 2: Run audio-separator
        try:
            from audio_separator.separator import Separator
            
            separator = Separator(
                output_dir=str(cache_subdir),
                output_format="wav"
            )
            
            # Load the model
            separator.load_model(model_filename=self.model_name)
            
            # Separate the audio
            logger.info(f"Running audio separation with {self.model_name}...")
            output_files = separator.separate(str(temp_audio))
            
            logger.info(f"Separation complete. Output files: {output_files}")
            
            # The separator outputs files with specific naming patterns
            # Find vocals and instrumental from output
            for output_file in output_files:
                output_path = cache_subdir / output_file
                filename_lower = output_path.name.lower()
                
                if "vocal" in filename_lower or "vocals" in filename_lower:
                    output_path.rename(vocals_path)
                elif "instrumental" in filename_lower or "no_vocal" in filename_lower or "music" in filename_lower:
                    output_path.rename(instrumental_path)
            
            # Verify outputs exist
            if not vocals_path.exists() or not instrumental_path.exists():
                # Fallback: look for any output files and use them
                remaining_files = list(cache_subdir.glob("*.wav"))
                remaining_files = [f for f in remaining_files if f.name not in ["full_audio.wav", "vocals.wav", "instrumental.wav"]]
                
                if len(remaining_files) >= 2:
                    # Assume first is vocals, second is instrumental
                    remaining_files[0].rename(vocals_path)
                    remaining_files[1].rename(instrumental_path)
                elif len(remaining_files) == 1:
                    # Only got one output, use it as instrumental and copy original as vocals
                    remaining_files[0].rename(instrumental_path)
                    import shutil
                    shutil.copy(temp_audio, vocals_path)
            
            # Clean up temp audio
            if temp_audio.exists():
                temp_audio.unlink()
            
            logger.info(f"✅ Audio separation complete: vocals={vocals_path}, instrumental={instrumental_path}")
            return vocals_path, instrumental_path
            
        except ImportError:
            logger.error("audio-separator not installed. Install with: pip install audio-separator[cpu]")
            raise RuntimeError("audio-separator not installed. Run: pip install audio-separator[cpu]")
        except Exception as e:
            logger.error(f"Audio separation failed: {e}")
            raise RuntimeError(f"Audio separation failed: {e}")
    
    def clear_cache(self, video_path: Optional[Path] = None):
        """
        Clear cached separated audio files.
        
        Args:
            video_path: If provided, only clear cache for this video.
                       If None, clear entire cache.
        """
        if video_path:
            audio_hash = self._get_audio_hash(Path(video_path))
            cache_subdir = self.cache_dir / audio_hash
            if cache_subdir.exists():
                import shutil
                shutil.rmtree(cache_subdir)
                logger.info(f"Cleared cache for hash {audio_hash}")
        else:
            import shutil
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                logger.info("Cleared entire audio separation cache")
