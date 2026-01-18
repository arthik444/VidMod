"""
VidMod Object Tracker Module
Tracks objects across video frames using OpenCV trackers.
"""

import cv2
import numpy as np
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class ObjectTracker:
    """Tracks a bounding box across a sequence of frames."""
    
    def __init__(self):
        # Using MIL as it's more widely available in standard OpenCV builds
        self.tracker_type = "MIL"
        
    def track_finding(
        self, 
        finding: Dict[str, Any], 
        frame_paths: List[Path], 
        fps: float
    ) -> List[Dict[str, float]]:
        """
        Track a finding's box across the relevant frames.
        
        Args:
            finding: The compliance finding from Gemini
            frame_paths: List of all extracted frame paths for the job
            fps: Frames per second of the video
            
        Returns:
            List of bounding boxes for each frame in the time range
        """
        if "box" not in finding or not finding["box"]:
            return []
            
        start_time = finding["startTime"]
        end_time = finding["endTime"]
        seed_box = finding["box"]
        
        # Calculate frame indices
        start_idx = int(start_time * fps)
        end_idx = int(end_time * fps)
        
        # Limit indices to available frames
        start_idx = max(0, min(start_idx, len(frame_paths) - 1))
        end_idx = max(start_idx, min(end_idx, len(frame_paths) - 1))
        
        logger.info(f"Tracking finding from frame {start_idx} to {end_idx}")
        
        # Load the first frame to initialize tracker
        first_frame_path = frame_paths[start_idx]
        image = cv2.imread(str(first_frame_path))
        if image is None:
            logger.error(f"Failed to load frame: {first_frame_path}")
            return []
            
        h, w = image.shape[:2]
        
        # Optimization: Downscale for tracking if image is large
        self.scale = 1.0
        max_track_dim = 640
        if w > max_track_dim:
            self.scale = max_track_dim / w
            image = cv2.resize(image, (max_track_dim, int(h * self.scale)))
            logger.info(f"Downscaling for tracking: {w}x{h} -> {image.shape[1]}x{image.shape[0]}")
        
        track_h, track_w = image.shape[:2]
        
        # Convert percentage box to pixel coordinates (x, y, w, h) in tracking space
        x = int(seed_box["left"] * track_w / 100)
        y = int(seed_box["top"] * track_h / 100)
        box_w = int(seed_box["width"] * track_w / 100)
        box_h = int(seed_box["height"] * track_h / 100)
        
        roi = (x, y, box_w, box_h)
        
        # Initialize tracker
        tracker = cv2.TrackerMIL_create()
        tracker.init(image, roi)
        
        results = []
        # Add the seed box for the start frame
        results.append({
            "frame": start_idx,
            "top": seed_box["top"],
            "left": seed_box["left"],
            "width": seed_box["width"],
            "height": seed_box["height"]
        })
        
        # Optimization: More aggressive skipping for long durations to prevent HTTP timeouts.
        # We target about 100-150 points per finding max.
        total_frames_in_range = end_idx - start_idx
        target_points = 100
        skip_rate = max(1, total_frames_in_range // target_points)
        
        logger.info(f"Tracking {total_frames_in_range} frames with skip_rate {skip_rate} (targeting ~{target_points} points)")
        
        # Track through subsequent frames
        for i in range(start_idx + 1, end_idx + 1):
            # Only process every skip_rate frame, but always try to catch the last frame
            if (i - start_idx) % skip_rate != 0 and i != end_idx:
                continue
                
            frame_path = frame_paths[i]
            frame_image = cv2.imread(str(frame_path))
            if frame_image is None:
                continue
            
            # Apply same scaling as initial frame
            if self.scale != 1.0:
                frame_image = cv2.resize(frame_image, (track_w, track_h))
                
            success, box = tracker.update(frame_image)
            
            if success:
                (tx, ty, tw, th) = [float(v) for v in box]
                results.append({
                    "frame": i,
                    "top": (ty / track_h) * 100,
                    "left": (tx / track_w) * 100,
                    "width": (tw / track_w) * 100,
                    "height": (th / track_h) * 100
                })
            else:
                logger.warning(f"Tracking lost at frame {i}")
                break
                
        return results

def track_findings_in_job(job: Any, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Apply tracking to all findings in a job.
    Updates each finding with a 'path' property containing the tracked boxes.
    """
    # Refresh frame paths from disk if they seem missing or incomplete
    if hasattr(job, 'frames_dir') and job.frames_dir.exists():
        disk_frames = sorted(job.frames_dir.glob("*.png"))
        if len(disk_frames) > len(job.frame_paths or []):
            logger.info(f"Discovered {len(disk_frames)} frames on disk for job {job.job_id} (increased from {len(job.frame_paths or [])})")
            job.frame_paths = disk_frames

    if not job.frame_paths:
        logger.warning(f"No frames found for job {job.job_id}, cannot track")
        return findings
        
    fps = job.video_info.get("fps", 30)
    tracker = ObjectTracker()
    
    logger.info(f"Starting tracking for {len(findings)} findings in job {job.job_id} using {len(job.frame_paths)} frames at {fps} fps")
    
    for finding in findings:
        if "box" in finding and finding["box"]:
            logger.info(f"Tracking finding {finding.get('id')} ({finding.get('type')}) from {finding.get('startTime')}s to {finding.get('endTime')}s")
            tracked_path = tracker.track_finding(finding, job.frame_paths, fps)
            if tracked_path:
                finding["path"] = tracked_path
                logger.info(f"Successfully tracked finding {finding.get('id')} across {len(tracked_path)} frames")
            else:
                logger.warning(f"Failed to track finding {finding.get('id')}")
                
    return findings
