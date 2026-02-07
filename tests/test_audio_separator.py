import sys
from pathlib import Path
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.audio_separator import AudioSeparator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_separation():
    video_path = Path("/Users/karthik/Desktop/vidMod/storage/jobs/f5f85d66/input.mp4")
    if not video_path.exists():
        print(f"Error: Test video not found at {video_path}")
        return

    separator = AudioSeparator()
    
    print(f"Starting separation for {video_path}...")
    try:
        vocals, instrumental = separator.separate_vocals_and_music(video_path)
        
        print("\n--- Results ---")
        print(f"Vocals track: {vocals}")
        print(f"Instrumental track: {instrumental}")
        
        if vocals.exists() and instrumental.exists():
            print("\n✅ Success! Both files generated successfully.")
            
            # Test cache
            print("\nTesting cache hit...")
            v2, i2 = separator.separate_vocals_and_music(video_path)
            if v2 == vocals and i2 == instrumental:
                print("✅ Cache hit confirmed!")
        else:
            print("\n❌ Failure: One or both files missing.")
            
    except Exception as e:
        print(f"\n❌ Error during separation: {e}")

if __name__ == "__main__":
    test_separation()
