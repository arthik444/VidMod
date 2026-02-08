"""
VidMod Video Builder Module
Reconstructs video from frames using FFmpeg.
"""

import subprocess
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class VideoBuilder:
    """Reconstruct video from processed frames using FFmpeg."""
    
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path
    
    def build_video(
        self,
        frames_dir: Path,
        output_path: Path,
        fps: float = 30,
        audio_path: Optional[Path] = None,
        frame_pattern: str = "frame_%06d.png",
        codec: str = "libx264",
        crf: int = 18,
        preset: str = "medium"
    ) -> Path:
        """
        Reconstruct video from frames.
        
        Args:
            frames_dir: Directory containing frames
            output_path: Output video path
            fps: Frames per second
            audio_path: Optional path to audio file to merge
            frame_pattern: Pattern for frame filenames
            codec: Video codec (default: libx264)
            crf: Constant Rate Factor (quality, lower = better, 18-28 typical)
            preset: Encoding preset (ultrafast, fast, medium, slow, veryslow)
            
        Returns:
            Path to output video
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build base command
        cmd = [
            self.ffmpeg_path, "-y",
            "-framerate", str(fps),
            "-i", str(frames_dir / frame_pattern),
        ]
        
        # Add audio if provided
        if audio_path and audio_path.exists():
            cmd.extend(["-i", str(audio_path)])
        
        # Video encoding options
        cmd.extend([
            "-c:v", codec,
            "-crf", str(crf),
            "-preset", preset,
            "-pix_fmt", "yuv420p",  # Compatibility
        ])
        
        # Audio options
        if audio_path and audio_path.exists():
            cmd.extend([
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest"  # Match shortest stream
            ])
        
        cmd.append(str(output_path))
        
        logger.info(f"Building video: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Video built successfully: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Video build failed: {e.stderr}")
            raise RuntimeError(f"Failed to build video: {e.stderr}")
    
    def build_video_from_list(
        self,
        frame_paths: list[Path],
        output_path: Path,
        fps: float = 30,
        audio_path: Optional[Path] = None
    ) -> Path:
        """
        Build video from a list of frame paths (useful when frames aren't sequential).
        Uses a concat demuxer with a file list.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create file list
        list_file = output_path.parent / "frames_list.txt"
        with open(list_file, "w") as f:
            for frame in frame_paths:
                # FFmpeg concat requires specific format
                f.write(f"file '{frame.absolute()}'\n")
                f.write(f"duration {1/fps}\n")
        
        # Build command
        cmd = [
            self.ffmpeg_path, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
        ]
        
        if audio_path and audio_path.exists():
            cmd.extend(["-i", str(audio_path)])
        
        cmd.extend([
            "-c:v", "libx264",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-vsync", "vfr"
        ])
        
        if audio_path and audio_path.exists():
            cmd.extend(["-c:a", "aac", "-shortest"])
        
        cmd.append(str(output_path))
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            # Cleanup list file
            list_file.unlink()
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Video build failed: {e.stderr}")
            raise RuntimeError(f"Failed to build video: {e.stderr}")
    
    def create_preview_gif(
        self,
        frames_dir: Path,
        output_path: Path,
        fps: int = 10,
        scale: int = 320,
        duration: float = 3
    ) -> Path:
        """Create a preview GIF from frames."""
        max_frames = int(fps * duration)
        
        cmd = [
            self.ffmpeg_path, "-y",
            "-framerate", str(fps),
            "-i", str(frames_dir / "frame_%06d.png"),
            "-vframes", str(max_frames),
            "-vf", f"scale={scale}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"GIF creation failed: {e.stderr}")
            raise RuntimeError(f"Failed to create GIF: {e.stderr}")
    
    def apply_blur_with_mask(
        self,
        input_video: Path,
        mask_video: Path,
        output_path: Path,
        blur_strength: int = 30,
        audio_path: Optional[Path] = None
    ) -> Path:
        """
        Apply Gaussian blur to masked region of video.
        Uses scale2ref to ensure mask matches input dimensions.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # FFmpeg filter Explanation:
        # 1. Split input into [original] and [toblur]
        # 2. Blur [toblur] to create [blurred]
        # 3. Scale mask [1:v] to match [original] dimensions using scale2ref.
        #    This outputs [mask_scaled] and [original_ref].
        #    IMPORTANT: We MUST use [original_ref] later, otherwise FFmpeg errors with "unconnected output"
        # 4. Negate mask (if needed based on SAM3 output)
        # 5. Merge [blurred] and [original_ref] using [mask_inverted]
        
        filter_complex = (
            f"[0:v]split[toscale][toblur];"
            f"[toblur]boxblur={blur_strength}:1[blurred];"
            f"[1:v][toscale]scale2ref[mask_scaled][original_ref];"
            f"[mask_scaled]format=gray,negate[mask_inverted];"
            f"[blurred][original_ref][mask_inverted]maskedmerge[out]"
        )
        
        cmd = [
            self.ffmpeg_path, "-y",
            "-i", str(input_video),
            "-i", str(mask_video),
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
        ]
        
        # Add audio if provided
        if audio_path and audio_path.exists():
            cmd.extend(["-i", str(audio_path), "-map", "2:a", "-c:a", "aac", "-shortest"])
        elif input_video.suffix.lower() in ['.mp4', '.mov', '.mkv']:
            # Try to copy audio from original video
            cmd.extend(["-map", "0:a?", "-c:a", "copy"])
        
        cmd.append(str(output_path))
        
        logger.info(f"Applying blur with mask: {' '.join(cmd)}")
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Blurred video created: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Blur application failed: {e.stderr}")
            raise RuntimeError(f"Failed to apply blur: {e.stderr}")
    
    def apply_pixelate_with_mask(
        self,
        input_video: Path,
        mask_video: Path,
        output_path: Path,
        pixel_size: int = 16,
        audio_path: Optional[Path] = None
    ) -> Path:
        """
        Apply pixelation effect to masked region.
        Fixed to avoid unconnected output errors and hardcoded scaling.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        filter_complex = (
            f"[0:v]split[toscale][topix];"
            # Pixelate: Scale down by pixel_size, then scale back up to input dimensions (iw*pixel_size)
            # We use scale2ref style logic implicitly by just multiplying back, but exact iw/ih is safer.
            # actually better: scale=iw/N:-1, then scale=iw:ih.
            f"[topix]scale=iw/{pixel_size}:ih/{pixel_size}:flags=neighbor[small];"
            f"[small]scale=iw*{pixel_size}:ih*{pixel_size}:flags=neighbor[pixelated_raw];"
            # Ensure pixelated stream matches original size exactly (rounding errors might occur with simple math)
            f"[pixelated_raw][0:v]scale2ref[pixelated][unused_ref];"
            # Now handle mask scaling
            f"[1:v][toscale]scale2ref[mask_scaled][original_ref];"
            f"[mask_scaled]negate[mask_inverted];"
            f"[pixelated][original_ref][mask_inverted]maskedmerge[out]"
        )
        # Simplified Pixelation without extra scale2ref check if we trust math, but let's be safe:
        # Actually simplest valid graph:
        # Pixelate filter logic:
        # 1. Resize mask [1:v] to match original [0:v]. This outputs [mask_scaled] and [original_ref].
        # 2. Split [original_ref] so we have a base for merging and a source for pixelating.
        # 3. Downscale [toscale] to create the low-res mosaic blocks.
        # 4. Upscale [small] BACK to [base] dimensions. IMPORTANT: We use scale2ref again here
        #    to guarantee the upscaled version matches the base EXACTLY (avoiding odd-pixel rounding errors).
        # 5. Negate mask and merge.
        
        filter_complex = (
            f"[1:v][0:v]scale2ref[mask_scaled][original_ref];"
            f"[original_ref]split[base][toscale];"
            f"[toscale]scale=iw/{pixel_size}:ih/{pixel_size}:flags=neighbor[small];"
            f"[small][base]scale2ref=flags=neighbor[pixelated][base_ready];"
            f"[mask_scaled]negate[mask_inverted];"
            f"[pixelated][base_ready][mask_inverted]maskedmerge[out]"
        )
        
        cmd = [
            self.ffmpeg_path, "-y",
            "-i", str(input_video),
            "-i", str(mask_video),
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
        ]
        
        if audio_path and audio_path.exists():
            cmd.extend(["-i", str(audio_path), "-map", "2:a", "-c:a", "aac", "-shortest"])
        elif input_video.suffix.lower() in ['.mp4', '.mov', '.mkv']:
            cmd.extend(["-map", "0:a?", "-c:a", "copy"])
        
        cmd.append(str(output_path))
        
        logger.info(f"Applying pixelation with mask: {' '.join(cmd)}")
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Pixelated video created: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Pixelation failed: {e.stderr}")
            raise RuntimeError(f"Failed to apply pixelation: {e.stderr}")
    
    def get_video_fps(self, video_path: Path) -> float:
        """
        Get the frame rate of a video using ffprobe.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Frame rate as a float
        """
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            fps_str = result.stdout.strip()
            # Parse fps (can be "30/1" or "30")
            if "/" in fps_str:
                num, den = fps_str.split("/")
                fps = float(num) / float(den)
            else:
                fps = float(fps_str)
            logger.info(f"Video fps detected: {fps} for {video_path.name}")
            return fps
        except Exception as e:
            logger.warning(f"Could not detect fps for {video_path}, defaulting to 30: {e}")
            return 30.0
    
    def normalize_video_fps(
        self,
        input_video: Path,
        output_path: Path,
        target_fps: float,
        preserve_audio: bool = True,
        target_resolution: tuple = None
    ) -> Path:
        """
        Re-encode video to match a target frame rate and optionally resolution.
        This is crucial for stitching videos from different sources (e.g., Runway output).

        Args:
            input_video: Path to the source video (potentially with different fps)
            output_path: Path to save the normalized video
            target_fps: Target frame rate to match
            preserve_audio: Whether to copy audio stream
            target_resolution: Optional (width, height) to match original resolution

        Returns:
            Path to the normalized video
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get current fps
        current_fps = self.get_video_fps(input_video)

        # If fps is already close enough (within 0.5 fps), just copy
        if abs(current_fps - target_fps) < 0.5 and not target_resolution:
            logger.info(f"Video fps {current_fps:.1f} is close to target {target_fps:.1f}, no normalization needed")
            import shutil
            shutil.copy(input_video, output_path)
            return output_path

        logger.info(f"Normalizing video fps: {current_fps:.1f} -> {target_fps:.1f}")
        if target_resolution:
            logger.info(f"Normalizing resolution to: {target_resolution[0]}x{target_resolution[1]}")

        # Build filter chain
        filters = [f"fps={target_fps}"]

        # Add scale filter if target resolution is specified
        if target_resolution:
            width, height = target_resolution
            # Use scale with exact size and maintain aspect ratio with padding if needed
            filters.append(f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2")

        filter_chain = ",".join(filters)

        # Re-encode with target fps and resolution
        cmd = [
            self.ffmpeg_path, "-y",
            "-i", str(input_video),
            "-filter:v", filter_chain,
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
        ]
        
        if preserve_audio:
            cmd.extend(["-c:a", "aac", "-b:a", "192k"])
        else:
            cmd.extend(["-an"])
        
        cmd.append(str(output_path))
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Video normalized to {target_fps:.1f} fps: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FPS normalization failed: {e.stderr}")
            raise RuntimeError(f"Failed to normalize video fps: {e.stderr}")

    
    def insert_segment(
        self,
        original_video: Path,
        processed_segment: Path,
        output_path: Path,
        start_time: float,
        end_time: float,
        buffer_seconds: float = 0.0
    ) -> Path:
        """
        Replace a segment of the original video with a processed segment using FRAME-ACCURATE stitching.

        This method:
        1. Gets the video's FPS
        2. Converts timestamps to exact frame numbers
        3. Extracts segments at exact frame boundaries
        4. Stitches them together perfectly with no discontinuities

        Args:
            original_video: Path to the original full video
            processed_segment: Path to the processed clip
            output_path: Path to save the final video
            start_time: Exact start time of the segment (seconds)
            end_time: Exact end time of the segment (seconds)
            buffer_seconds: Optional buffer (default: 0.0 for frame-perfect stitching)

        Returns:
            Path to the stitched video
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get video info to determine FPS
        from core.frame_extractor import FrameExtractor
        extractor = FrameExtractor(ffmpeg_path=self.ffmpeg_path)
        video_info = extractor.get_video_info(original_video)
        fps = video_info['fps']

        logger.info(f"Frame-accurate stitching at {fps:.3f} fps")

        # Convert timestamps to exact frame numbers
        start_frame = int(start_time * fps)
        end_frame = int(end_time * fps)

        # Apply buffer in frames if specified
        buffer_frames = int(buffer_seconds * fps)
        buffered_start_frame = max(0, start_frame - buffer_frames)
        buffered_end_frame = end_frame + buffer_frames

        # Convert back to exact timestamps for frame boundaries
        buffered_start = buffered_start_frame / fps
        buffered_end = buffered_end_frame / fps

        logger.info(f"Frame range: {buffered_start_frame} to {buffered_end_frame} (time: {buffered_start:.3f}s to {buffered_end:.3f}s)")
        
        # Create temporary clips: before, processed, after
        temp_dir = output_path.parent / "temp_segments"
        temp_dir.mkdir(exist_ok=True)
        
        before_clip = temp_dir / "before.mp4"
        after_clip = temp_dir / "after.mp4"
        concat_list = temp_dir / "concat_list.txt"
        
        try:
            # Extract "before" segment using frame-accurate trim filter
            if buffered_start_frame > 0:
                # Use trim filter for exact frame cutting
                cmd_before = [
                    self.ffmpeg_path, "-y",
                    "-i", str(original_video),
                    "-vf", f"trim=end_frame={buffered_start_frame},setpts=PTS-STARTPTS",
                    "-af", f"atrim=end={buffered_start:.6f},asetpts=PTS-STARTPTS",
                    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
                    "-c:a", "aac", "-b:a", "192k",
                    str(before_clip)
                ]
                subprocess.run(cmd_before, capture_output=True, text=True, check=True)
                logger.info(f"Extracted 'before' segment: frame 0 to {buffered_start_frame} ({buffered_start:.3f}s)")

            # Extract "after" segment using frame-accurate trim filter
            # Get total frame count
            total_frames = video_info.get('total_frames', int(video_info['duration'] * fps))

            if buffered_end_frame < total_frames:
                cmd_after = [
                    self.ffmpeg_path, "-y",
                    "-i", str(original_video),
                    "-vf", f"trim=start_frame={buffered_end_frame},setpts=PTS-STARTPTS",
                    "-af", f"atrim=start={buffered_end:.6f},asetpts=PTS-STARTPTS",
                    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
                    "-c:a", "aac", "-b:a", "192k",
                    str(after_clip)
                ]
                result = subprocess.run(cmd_after, capture_output=True, text=True, check=False)
                has_after = after_clip.exists() and after_clip.stat().st_size > 1000
                if has_after:
                    logger.info(f"Extracted 'after' segment: frame {buffered_end_frame} to end ({buffered_end:.3f}s to end)")
            else:
                has_after = False
            
            # CRITICAL: Normalize processed segment fps AND resolution to match original video
            # This fixes the speed mismatch when Runway outputs different fps
            # AND fixes zoom issues when Runway outputs different resolution
            original_fps = self.get_video_fps(original_video)
            original_resolution = (video_info['width'], video_info['height'])
            normalized_segment = temp_dir / "processed_normalized.mp4"
            self.normalize_video_fps(
                processed_segment,
                normalized_segment,
                original_fps,
                preserve_audio=True,
                target_resolution=original_resolution
            )
            
            # Create concat list (using normalized segment)
            with open(concat_list, 'w') as f:
                if buffered_start > 0:
                    f.write(f"file '{before_clip.absolute()}'\n")
                f.write(f"file '{normalized_segment.absolute()}'\n")
                if has_after:
                    f.write(f"file '{after_clip.absolute()}'\n")
            
            # Concatenate all segments
            cmd_concat = [
                self.ffmpeg_path, "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list),
                "-c", "copy",
                str(output_path)
            ]
            
            subprocess.run(cmd_concat, capture_output=True, text=True, check=True)
            logger.info(f"Stitched video created: {output_path}")
            
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Video stitching failed: {e.stderr}")
            raise RuntimeError(f"Failed to stitch video segments: {e.stderr}")
        finally:
            # Cleanup temporary files
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def concat_clips(self, clips: list[Path], output_path: Path) -> Path:
        """
        Concatenate multiple video clips into one.
        
        Args:
            clips: List of paths to video clips
            output_path: Path to save the final video
            
        Returns:
            Path to the concatenated video
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not clips:
            raise ValueError("No clips provided for concatenation")
            
        if len(clips) == 1:
            import shutil
            shutil.copy(clips[0], output_path)
            return output_path
            
        # Create concat list file
        concat_list_path = output_path.parent / "concat_list_temp.txt"
        
        try:
            with open(concat_list_path, 'w') as f:
                for clip in clips:
                    # FFmpeg requires absolute paths in concat list
                    f.write(f"file '{clip.absolute()}'\n")
            
            # Concatenate
            cmd = [
                self.ffmpeg_path, "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list_path),
                "-c", "copy",
                str(output_path)
            ]
            
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Concatenated {len(clips)} clips to {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Concat failed: {e.stderr}")
            raise RuntimeError(f"Failed to concatenate clips: {e.stderr}")
        finally:
            if concat_list_path.exists():
                try:
                    concat_list_path.unlink()
                except:
                    pass

