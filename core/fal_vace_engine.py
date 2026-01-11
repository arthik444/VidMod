"""
fal.ai VACE Video Inpainting Engine.
Takes video + mask video (from SAM3) and replaces masked regions.
"""

import logging
import os
import fal_client
from pathlib import Path
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

# fal.ai model for VACE video inpainting
FAL_VACE_MODEL = "fal-ai/wan-vace-14b/inpainting"


class FalVaceEngine:
    """
    Video inpainting using fal.ai Wan VACE model.
    Takes original video + mask video and replaces masked regions.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize fal.ai VACE engine.
        
        Args:
            api_key: fal.ai API key (or uses FAL_KEY env var)
        """
        self.api_key = api_key or os.getenv("FAL_KEY")
        if not self.api_key:
            raise ValueError("FAL_KEY not set")
        
        # Set the API key for fal_client
        os.environ["FAL_KEY"] = self.api_key
        logger.info("fal.ai VACE engine initialized")
    
    def _upload_file(self, file_path: Path) -> str:
        """Upload a local file to fal.ai and return the URL."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.info(f"Uploading file to fal.ai: {file_path}")
        url = fal_client.upload_file(str(file_path))
        logger.info(f"Uploaded: {url}")
        return url
    
    def replace_object(
        self,
        video_path: Path,
        mask_video_path: Path,
        prompt: str = "",
        reference_image_path: Optional[Path] = None,
        num_inference_steps: int = 30,
        guidance_scale: float = 5.0,
        output_resolution: str = "720p"
    ) -> dict:
        """
        Replace masked regions in video using VACE inpainting.
        
        Args:
            video_path: Path to original video
            mask_video_path: Path to mask video (white = replace, black = keep)
            prompt: Text prompt for replacement content
            reference_image_path: Optional path to reference image for the replacement
            num_inference_steps: Number of diffusion steps (default 30)
            guidance_scale: How closely to follow prompt (default 5.0)
            output_resolution: Output resolution (480p, 580p, 720p)
            
        Returns:
            Dict with 'video_url' of the result
        """
        logger.info(f"Starting VACE inpainting...")
        logger.info(f"Video: {video_path}")
        logger.info(f"Mask: {mask_video_path}")
        logger.info(f"Prompt: {prompt}")
        
        # Upload files to fal.ai
        video_url = self._upload_file(video_path)
        mask_url = self._upload_file(mask_video_path)
        
        # Build request
        request = {
            "video_url": video_url,
            "mask_video_url": mask_url,
            "prompt": prompt,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "resolution": output_resolution,
            "match_input_num_frames": True,
            "match_input_frames_per_second": True,
        }
        
        # Add reference image if provided
        if reference_image_path and Path(reference_image_path).exists():
            logger.info(f"Using reference image: {reference_image_path}")
            ref_url = self._upload_file(reference_image_path)
            request["ref_image_urls"] = [ref_url]
        
        logger.info("Calling fal.ai VACE API...")
        
        try:
            # Run the model
            result = fal_client.subscribe(
                FAL_VACE_MODEL,
                arguments=request,
                with_logs=True
            )
            
            logger.info(f"VACE inpainting complete")
            return result
            
        except Exception as e:
            logger.error(f"fal.ai VACE failed: {e}")
            raise
    
    def replace_and_download(
        self,
        video_path: Path,
        mask_video_path: Path,
        output_path: Path,
        prompt: str = "",
        **kwargs
    ) -> Path:
        """
        Replace masked regions and download the result.
        
        Args:
            video_path: Path to original video
            mask_video_path: Path to mask video
            output_path: Where to save the result
            prompt: Text prompt for replacement
            **kwargs: Additional arguments for replace_object
            
        Returns:
            Path to downloaded video
        """
        # Run inpainting
        result = self.replace_object(
            video_path=video_path,
            mask_video_path=mask_video_path,
            prompt=prompt,
            **kwargs
        )
        
        # Get video URL from result
        video_url = result.get("video", {}).get("url")
        if not video_url:
            # Try alternative response structure
            video_url = result.get("video_url") or result.get("output", {}).get("video")
        
        if not video_url:
            logger.error(f"No video URL in response: {result}")
            raise ValueError("No video URL in fal.ai response")
        
        # Download the result
        logger.info(f"Downloading result to {output_path}")
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with httpx.Client(timeout=120.0) as client:
            response = client.get(video_url, follow_redirects=True)
            response.raise_for_status()
            with open(output_path, 'wb') as f:
                f.write(response.content)
        
        logger.info(f"Downloaded: {output_path}")
        return output_path
