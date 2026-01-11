"""
Gemini Inpaint Engine - Frame-by-frame image editing using Gemini 2.5 Flash Image.
Uses Nano Banana for object detection and replacement in individual frames.
"""

import logging
import os
import base64
from pathlib import Path
from typing import Optional, List
from PIL import Image
import io

logger = logging.getLogger(__name__)

# Gemini model for image editing (Nano Banana)
GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"


class GeminiInpaintEngine:
    """
    Frame-by-frame image editing using Gemini 2.5 Flash Image (Nano Banana).
    Supports object detection, replacement with text prompts, and reference images.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize Gemini Inpaint engine.
        
        Args:
            api_key: Gemini API key (or uses GEMINI_API_KEY env var)
        """
        from google import genai
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set")
        
        self.client = genai.Client(api_key=self.api_key)
        logger.info("Gemini Inpaint engine initialized")
    
    def edit_frame(
        self,
        image_path: Path,
        edit_prompt: str,
        reference_image_path: Optional[Path] = None
    ) -> Image.Image:
        """
        Edit a single frame using Gemini image editing.
        
        Args:
            image_path: Path to the frame image
            edit_prompt: Prompt describing the edit (e.g., "replace the coffee cup with a red Coca-Cola can")
            reference_image_path: Optional path to reference image for the replacement object
            
        Returns:
            Edited PIL Image
        """
        from google.genai import types
        
        logger.info(f"Editing frame: {image_path}")
        logger.info(f"Edit prompt: {edit_prompt}")
        
        # Load the source image
        source_image = Image.open(image_path)
        
        # Build the content list
        contents = [edit_prompt, source_image]
        
        # Add reference image if provided
        if reference_image_path and Path(reference_image_path).exists():
            logger.info(f"Using reference image: {reference_image_path}")
            reference_image = Image.open(reference_image_path)
            contents = [
                f"{edit_prompt}. Use the provided reference image as a guide for the replacement object.",
                source_image,
                reference_image
            ]
        
        try:
            # Call Gemini API with image generation config
            response = self.client.models.generate_content(
                model=GEMINI_IMAGE_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"]
                )
            )
            
            # Check if we have candidates
            if not response.candidates:
                logger.warning("No candidates in response, returning original")
                return source_image
            
            # Get parts from the first candidate
            candidate = response.candidates[0]
            if not candidate.content or not candidate.content.parts:
                logger.warning("No parts in response, returning original")
                return source_image
            
            # Extract the generated image
            for part in candidate.content.parts:
                if hasattr(part, 'inline_data') and part.inline_data is not None:
                    # Decode image from base64
                    image_data = part.inline_data.data
                    image_bytes = base64.b64decode(image_data) if isinstance(image_data, str) else image_data
                    return Image.open(io.BytesIO(image_bytes))
            
            # If no image returned, return original
            logger.warning("No image in response parts, returning original")
            return source_image
            
        except Exception as e:
            logger.error(f"Gemini image editing failed: {e}")
            raise
    
    def process_frames(
        self,
        frame_paths: List[Path],
        object_prompt: str,
        replacement_prompt: str,
        reference_image_path: Optional[Path] = None,
        frame_interval: int = 1,
        output_dir: Optional[Path] = None,
        progress_callback=None
    ) -> List[Path]:
        """
        Process multiple frames with object replacement.
        
        Args:
            frame_paths: List of paths to frame images
            object_prompt: What object to find (e.g., "coffee cup")
            replacement_prompt: What to replace it with (e.g., "red Coca-Cola can")
            reference_image_path: Optional reference image for the replacement
            frame_interval: Process every Nth frame (others will be copied from nearest)
            output_dir: Directory to save edited frames
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of paths to edited frames
        """
        if output_dir is None:
            output_dir = frame_paths[0].parent / "edited_frames"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        total_frames = len(frame_paths)
        keyframe_indices = list(range(0, total_frames, frame_interval))
        
        logger.info(f"Processing {len(keyframe_indices)} keyframes out of {total_frames} total")
        
        # Build the edit prompt with consistency requirements
        if reference_image_path:
            edit_prompt = f"In this image, find the {object_prompt} and replace it with a {replacement_prompt} that matches the reference image EXACTLY. The replacement must be the SAME SIZE and in the SAME POSITION as the original object. Keep everything else exactly the same."
        else:
            edit_prompt = f"In this image, find the {object_prompt} and replace it with a {replacement_prompt}. The replacement MUST be the SAME SIZE and in the SAME POSITION as the original {object_prompt}. Keep everything else exactly the same."
        
        edited_frames = {}
        output_paths = []
        
        # Process keyframes
        for i, idx in enumerate(keyframe_indices):
            frame_path = frame_paths[idx]
            output_path = output_dir / f"frame_{idx:06d}.png"
            
            try:
                # Edit the frame
                edited_image = self.edit_frame(
                    image_path=frame_path,
                    edit_prompt=edit_prompt,
                    reference_image_path=reference_image_path
                )
                
                # Save edited frame
                edited_image.save(output_path)
                edited_frames[idx] = output_path
                
                logger.info(f"Edited keyframe {i+1}/{len(keyframe_indices)}: {output_path}")
                
            except Exception as e:
                logger.warning(f"Failed to edit frame {idx}: {e}, copying original")
                # Copy original on failure
                Image.open(frame_path).save(output_path)
                edited_frames[idx] = output_path
            
            if progress_callback:
                progress = (i + 1) / len(keyframe_indices) * 100
                progress_callback(progress, f"Editing frame {i+1}/{len(keyframe_indices)}")
        
        # Fill in non-keyframes by copying from nearest keyframe
        for idx in range(total_frames):
            output_path = output_dir / f"frame_{idx:06d}.png"
            
            if idx in edited_frames:
                output_paths.append(edited_frames[idx])
            else:
                # Find nearest keyframe
                nearest_keyframe = min(keyframe_indices, key=lambda k: abs(k - idx))
                nearest_path = edited_frames[nearest_keyframe]
                
                # Copy the nearest keyframe
                Image.open(nearest_path).save(output_path)
                output_paths.append(output_path)
        
        logger.info(f"Processed {total_frames} frames ({len(keyframe_indices)} edited)")
        return output_paths
