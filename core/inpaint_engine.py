"""
Wan 2.1 Inpainting Engine - Video object replacement using mask-based inpainting.
Uses andreasjansson/wan-1.3b-inpaint on Replicate.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Union
import replicate
import httpx

logger = logging.getLogger(__name__)

# Replicate model for Wan 2.1 inpainting with version hash
WAN_INPAINT_MODEL = "andreasjansson/wan-1.3b-inpaint:7abfdb3370aba087f9a5eb8b733c2174bc873a957e5c2c4835767247287dbf89"


class WanInpaintingEngine:
    """
    Video object replacement using Wan 2.1 inpainting via Replicate API.
    Takes an input video + mask video and replaces masked regions based on text prompt.
    """
    
    def __init__(self, api_token: str = None):
        """
        Initialize Wan 2.1 inpainting engine with Replicate API.
        
        Args:
            api_token: Replicate API token (or uses REPLICATE_API_TOKEN env var)
        """
        self.api_token = api_token or os.getenv("REPLICATE_API_TOKEN")
        if not self.api_token:
            raise ValueError("REPLICATE_API_TOKEN not set")
        
        os.environ["REPLICATE_API_TOKEN"] = self.api_token
        logger.info("Wan 2.1 Inpainting engine initialized with Replicate API")
    
    def replace_object(
        self,
        video_path: Union[str, Path],
        mask_path: Union[str, Path],
        prompt: str,
        num_frames: int = 81,
        guidance_scale: float = 5.0,
        num_inference_steps: int = 30
    ) -> Dict[str, Any]:
        """
        Replace masked region in video with AI-generated content.
        
        Args:
            video_path: Path to original video file
            mask_path: Path to mask video (white = areas to replace)
            prompt: Text description of replacement object (e.g., "a red Coca-Cola can")
            num_frames: Number of frames to generate (default 81)
            guidance_scale: Guidance scale for generation (default 5.0)
            num_inference_steps: Number of inference steps (default 30)
            
        Returns:
            Dict with 'output_url' for the inpainted video
        """
        logger.info(f"Replacing object with prompt: '{prompt}'")
        logger.info(f"Video: {video_path}")
        logger.info(f"Mask: {mask_path}")
        
        # Prepare file inputs
        video_file = self._prepare_file_input(video_path)
        mask_file = self._prepare_file_input(mask_path)
        
        try:
            output = replicate.run(
                WAN_INPAINT_MODEL,
                input={
                    "input_video": video_file,
                    "mask_video": mask_file,
                    "prompt": prompt,
                    "num_frames": num_frames,
                    "guidance_scale": guidance_scale,
                    "num_inference_steps": num_inference_steps
                }
            )
            
            # Get the output URL
            output_url = None
            if hasattr(output, 'url'):
                output_url = output.url
            elif isinstance(output, str):
                output_url = output
            elif isinstance(output, list) and len(output) > 0:
                output_url = output[0] if isinstance(output[0], str) else str(output[0])
            
            logger.info(f"Object replacement complete, output: {output_url}")
            
            return {
                "output_url": output_url,
                "output": output,
                "prompt": prompt
            }
            
        except Exception as e:
            logger.error(f"Object replacement failed: {e}")
            raise
        finally:
            # Close file handles if they were opened
            if hasattr(video_file, 'close'):
                video_file.close()
            if hasattr(mask_file, 'close'):
                mask_file.close()
    
    def _prepare_file_input(self, file_source: Union[str, Path]):
        """
        Prepare file input for Replicate API.
        
        Args:
            file_source: Path to file or URL
            
        Returns:
            File object or URL string
        """
        # Convert to string if Path
        if isinstance(file_source, Path):
            file_source = str(file_source)
        
        # Check if it's a URL
        if file_source.startswith(('http://', 'https://')):
            return file_source
        
        # It's a local file
        path = Path(file_source)
        if not path.exists():
            raise ValueError(f"File not found: {file_source}")
        
        logger.info(f"Opening file: {file_source}")
        return open(file_source, 'rb')
    
    def download_result(self, url: str, output_path: Path) -> Path:
        """
        Download the inpainted video result.
        
        Args:
            url: URL of the inpainted video
            output_path: Path to save the downloaded file
            
        Returns:
            Path to the downloaded file
        """
        logger.info(f"Downloading inpainted video to {output_path}")
        
        with httpx.Client(timeout=300.0) as client:
            response = client.get(url, follow_redirects=True)
            response.raise_for_status()
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(response.content)
        
        logger.info(f"Downloaded to {output_path}")
        return output_path
