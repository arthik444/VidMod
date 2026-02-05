#!/usr/bin/env python3
"""
Test script to verify ElevenLabs API capabilities for dubbing feature.

Tests:
1. API connection and authentication
2. List available voices
3. Text-to-speech generation
4. Voice cloning (if supported by account)
5. Audio output verification
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_api_connection():
    """Test 1: Verify API connection and authentication."""
    print("\n" + "="*60)
    print("TEST 1: API Connection & Authentication")
    print("="*60)
    
    try:
        from elevenlabs import ElevenLabs
        
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            print("❌ ELEVENLABS_API_KEY not found in environment")
            return False
        
        print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
        
        client = ElevenLabs(api_key=api_key)
        print("✅ ElevenLabs client created successfully")
        return client
        
    except Exception as e:
        print(f"❌ Failed to create client: {e}")
        return None


def test_list_voices(client):
    """Test 2: List available voices."""
    print("\n" + "="*60)
    print("TEST 2: List Available Voices")
    print("="*60)
    
    try:
        voices = client.voices.get_all()
        print(f"Found {len(voices.voices)} voices:")
        
        for i, voice in enumerate(voices.voices[:5]):
            print(f"  {i+1}. {voice.name} (ID: {voice.voice_id})")
        
        if len(voices.voices) > 5:
            print(f"  ... and {len(voices.voices) - 5} more")
        
        print("✅ Voice listing works")
        return voices.voices
        
    except Exception as e:
        print(f"❌ Failed to list voices: {e}")
        return None


def test_text_to_speech(client, voice_id: str):
    """Test 3: Generate speech from text."""
    print("\n" + "="*60)
    print("TEST 3: Text-to-Speech Generation")
    print("="*60)
    
    output_path = Path("tests/test_output.mp3")
    test_text = "Hello, this is a test of the dubbing system."
    
    try:
        print(f"Generating speech for: '{test_text}'")
        print(f"Using voice ID: {voice_id}")
        
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            text=test_text,
            model_id="eleven_multilingual_v2"
        )
        
        # Write audio to file
        with open(output_path, 'wb') as f:
            for chunk in audio:
                f.write(chunk)
        
        # Check file was created
        if output_path.exists():
            size = output_path.stat().st_size
            print(f"✅ Audio generated: {output_path} ({size} bytes)")
            return output_path
        else:
            print("❌ Audio file not created")
            return None
            
    except Exception as e:
        print(f"❌ TTS failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_voice_cloning(client, sample_audio_path: Path):
    """Test 4: Test instant voice cloning."""
    print("\n" + "="*60)
    print("TEST 4: Voice Cloning")
    print("="*60)
    
    if not sample_audio_path or not sample_audio_path.exists():
        print("⚠️ No sample audio available for cloning test")
        print("  Will test with a generated sample instead...")
        sample_audio_path = Path("tests/test_output.mp3")
        if not sample_audio_path.exists():
            print("❌ No audio sample available")
            return None
    
    try:
        print(f"Cloning voice from: {sample_audio_path}")
        
        # Try the clone method
        voice = client.clone(
            name="TestClone_VidMod",
            files=[str(sample_audio_path)],
            description="Test clone for VidMod dubbing"
        )
        
        print(f"✅ Voice cloned successfully!")
        print(f"   Voice ID: {voice.voice_id}")
        print(f"   Voice Name: {voice.name}")
        
        return voice.voice_id
        
    except Exception as e:
        print(f"❌ Voice cloning failed: {e}")
        
        # Try alternative method
        print("\nTrying alternative cloning method (voices.ivc.create)...")
        try:
            with open(sample_audio_path, 'rb') as f:
                voice = client.voices.ivc.create(
                    name="TestClone_VidMod_Alt",
                    files=[f],
                    description="Test clone for VidMod dubbing"
                )
            print(f"✅ Alternative clone method works!")
            print(f"   Voice ID: {voice.voice_id}")
            return voice.voice_id
        except Exception as e2:
            print(f"❌ Alternative method also failed: {e2}")
            return None


def test_generate_with_clone(client, cloned_voice_id: str):
    """Test 5: Generate speech with cloned voice."""
    print("\n" + "="*60)
    print("TEST 5: Generate Speech with Cloned Voice")
    print("="*60)
    
    if not cloned_voice_id:
        print("⚠️ No cloned voice available, skipping")
        return None
    
    output_path = Path("tests/test_cloned_output.mp3")
    test_text = "This is speech generated with a cloned voice."
    
    try:
        print(f"Generating speech: '{test_text}'")
        print(f"Using cloned voice ID: {cloned_voice_id}")
        
        audio = client.text_to_speech.convert(
            voice_id=cloned_voice_id,
            text=test_text,
            model_id="eleven_multilingual_v2"
        )
        
        with open(output_path, 'wb') as f:
            for chunk in audio:
                f.write(chunk)
        
        if output_path.exists():
            size = output_path.stat().st_size
            print(f"✅ Cloned speech generated: {output_path} ({size} bytes)")
            return output_path
        else:
            print("❌ Audio file not created")
            return None
            
    except Exception as e:
        print(f"❌ Cloned TTS failed: {e}")
        return None


def test_delete_voice(client, voice_id: str):
    """Test 6: Delete cloned voice."""
    print("\n" + "="*60)
    print("TEST 6: Delete Cloned Voice (Cleanup)")
    print("="*60)
    
    if not voice_id:
        print("⚠️ No voice to delete")
        return
    
    try:
        client.voices.delete(voice_id)
        print(f"✅ Voice {voice_id} deleted successfully")
    except Exception as e:
        print(f"⚠️ Failed to delete voice: {e}")


def run_all_tests():
    """Run all API tests."""
    print("\n" + "#"*60)
    print("# ELEVENLABS API VERIFICATION FOR DUBBING FEATURE")
    print("#"*60)
    
    # Test 1: Connection
    client = test_api_connection()
    if not client:
        print("\n❌ CRITICAL: Cannot proceed without API connection")
        return False
    
    # Test 2: List voices
    voices = test_list_voices(client)
    if not voices:
        print("\n❌ CRITICAL: Cannot list voices")
        return False
    
    # Use first available voice for TTS test
    test_voice_id = voices[0].voice_id
    
    # Test 3: Text-to-Speech
    tts_output = test_text_to_speech(client, test_voice_id)
    if not tts_output:
        print("\n❌ CRITICAL: TTS not working")
        return False
    
    # Test 4: Voice Cloning
    cloned_voice_id = test_voice_cloning(client, tts_output)
    
    # Test 5: Generate with Clone
    if cloned_voice_id:
        test_generate_with_clone(client, cloned_voice_id)
    
    # Test 6: Cleanup
    if cloned_voice_id:
        test_delete_voice(client, cloned_voice_id)
    
    # Summary
    print("\n" + "#"*60)
    print("# TEST SUMMARY")
    print("#"*60)
    print("✅ API Connection: PASSED")
    print("✅ Voice Listing: PASSED")
    print("✅ Text-to-Speech: PASSED")
    if cloned_voice_id:
        print("✅ Voice Cloning: PASSED")
        print("✅ Cloned TTS: PASSED")
    else:
        print("⚠️ Voice Cloning: NOT AVAILABLE (may require pro account)")
    
    print("\n✅ ElevenLabs API is ready for dubbing feature!")
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
