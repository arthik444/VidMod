
import sys
import os
from pathlib import Path

# Add project root to sys.path
root_dir = Path("/Users/karthik/Desktop/vidMod")
sys.path.append(str(root_dir))

from core.tracker import track_findings_in_job

class MockJob:
    def __init__(self, job_id, video_path, frame_paths, fps):
        self.job_id = job_id
        self.video_path = Path(video_path)
        self.frame_paths = [Path(p) for p in frame_paths]
        self.video_info = {"fps": fps}

def test_tracking():
    # Use real images if possible, otherwise we may need to mock cv2.imread
    # Looking at the directory, there are many videos.
    # For a quick test, I'll check if frames are already extracted for some job.
    
    storage_dir = Path("/Users/karthik/Desktop/vidMod/storage/jobs")
    if not storage_dir.exists():
        print("Storage dir not found, cannot run real end-to-end tracking test.")
        return

    # Find the most recent job
    jobs = sorted(storage_dir.glob("*"), key=os.path.getmtime, reverse=True)
    if not jobs:
        print("No jobs found in storage.")
        return

    job_dir = jobs[0]
    frames_dir = job_dir / "frames"
    frame_paths = sorted(frames_dir.glob("*.png"))
    
    if len(frame_paths) < 10:
        print(f"Not enough frames in {frames_dir} to test tracking.")
        return

    print(f"Testing tracking on job {job_dir.name} with {len(frame_paths)} frames")
    
    # Mock a finding (e.g., a logo detected at frame 0)
    # Finding box: {top: 40, left: 40, width: 20, height: 20}
    findings = [
        {
            "id": 1,
            "type": "Logo",
            "startTime": 0,
            "endTime": 1.0, # 1 second of content
            "box": {"top": 40, "left": 40, "width": 20, "height": 20}
        }
    ]
    
    job = MockJob(job_dir.name, job_dir / "input.mp4", frame_paths, 30.0)
    
    tracked_findings = track_findings_in_job(job, findings)
    
    for f in tracked_findings:
        if "path" in f:
            print(f"Finding {f['id']} tracked across {len(f['path'])} frames.")
            # Print first and last boxes
            print(f"Start: {f['path'][0]}")
            print(f"End: {f['path'][-1]}")
        else:
            print(f"Finding {f['id']} was NOT tracked.")

if __name__ == "__main__":
    test_tracking()
