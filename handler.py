"""
RunPod Serverless Handler for Chatterbox TTS
Text-to-Speech with voice cloning and emotion control

Based on: https://github.com/geronimi73/runpod_chatterbox
"""

import runpod
import base64
import io
import os
import tempfile
import urllib.request
from typing import Optional

import torch
import soundfile as sf
import numpy as np

# Global model instance (loaded once per worker)
tts_model = None


def load_model():
    """Load Chatterbox TTS model."""
    global tts_model

    if tts_model is not None:
        return tts_model

    print("[Handler] Loading Chatterbox TTS model...")

    from chatterbox.tts import ChatterboxTTS

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[Handler] Using device: {device}")

    tts_model = ChatterboxTTS.from_pretrained(device=device)

    print("[Handler] Model loaded successfully")
    return tts_model


def download_reference_audio(url: str) -> str:
    """Download reference audio from URL to temp file."""
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)

    try:
        urllib.request.urlretrieve(url, temp_file.name)
        return temp_file.name
    except Exception as e:
        os.unlink(temp_file.name)
        raise Exception(f"Failed to download reference audio: {e}")


def base64_to_audio_file(b64_data: str) -> str:
    """Convert base64 audio to temp file."""
    # Remove data URL prefix if present
    if "," in b64_data:
        b64_data = b64_data.split(",")[1]

    audio_bytes = base64.b64decode(b64_data)
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_file.write(audio_bytes)
    temp_file.close()
    return temp_file.name


def audio_to_base64(audio_array: np.ndarray, sample_rate: int = 24000) -> str:
    """Convert audio array to base64 encoded WAV."""
    buffer = io.BytesIO()
    sf.write(buffer, audio_array, sample_rate, format="WAV")
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def parse_emotion_tags(text: str) -> tuple[str, Optional[str]]:
    """
    Parse emotion tags from text.
    Format: [happy] Hello there! or <emotion:sad> How are you?
    Returns: (clean_text, emotion)
    """
    import re

    # Check for [emotion] format
    bracket_match = re.match(r"^\[(\w+)\]\s*(.+)$", text, re.DOTALL)
    if bracket_match:
        return bracket_match.group(2).strip(), bracket_match.group(1).lower()

    # Check for <emotion:name> format
    tag_match = re.match(r"^<emotion:(\w+)>\s*(.+)$", text, re.DOTALL)
    if tag_match:
        return tag_match.group(2).strip(), tag_match.group(1).lower()

    return text, None


def handler(job: dict) -> dict:
    """Main RunPod handler function."""

    job_input = job.get("input", {})

    # Required: text to synthesize
    text = job_input.get("text", "")
    if not text:
        return {"error": "No text provided"}

    # Optional: reference audio for voice cloning
    reference_audio_url = job_input.get("reference_audio_url")
    reference_audio_base64 = job_input.get("reference_audio_base64")

    # Optional: emotion override (if not in text tags)
    emotion = job_input.get("emotion")

    # Optional: generation parameters
    temperature = job_input.get("temperature", 0.7)
    exaggeration = job_input.get("exaggeration", 1.0)
    speed = job_input.get("speed", 1.0)
    cfg_weight = job_input.get("cfg_weight", 0.5)

    # Parse emotion from text if not provided
    clean_text, text_emotion = parse_emotion_tags(text)
    if text_emotion and not emotion:
        emotion = text_emotion
        text = clean_text

    try:
        # Load model
        model = load_model()

        # Handle reference audio
        ref_audio_path = None

        if reference_audio_url:
            print(f"[Handler] Downloading reference audio from URL...")
            ref_audio_path = download_reference_audio(reference_audio_url)
        elif reference_audio_base64:
            print(f"[Handler] Decoding reference audio from base64...")
            ref_audio_path = base64_to_audio_file(reference_audio_base64)

        # Generate speech
        print(f"[Handler] Generating speech for: {text[:50]}...")
        print(f"[Handler] Emotion: {emotion}, Temp: {temperature}, Speed: {speed}")

        if ref_audio_path:
            # Voice cloning mode
            audio = model.generate(
                text=text,
                audio_prompt_path=ref_audio_path,
                temperature=temperature,
                exaggeration=exaggeration,
                cfg_weight=cfg_weight,
            )
            # Clean up temp file
            os.unlink(ref_audio_path)
        else:
            # Default voice mode
            audio = model.generate(
                text=text,
                temperature=temperature,
                exaggeration=exaggeration,
                cfg_weight=cfg_weight,
            )

        # Apply speed adjustment if not 1.0
        if speed != 1.0:
            from scipy import signal
            # Resample to adjust speed
            original_length = len(audio)
            new_length = int(original_length / speed)
            audio = signal.resample(audio, new_length)

        # Convert to numpy if tensor
        if hasattr(audio, "cpu"):
            audio = audio.cpu().numpy()

        # Ensure 1D
        if len(audio.shape) > 1:
            audio = audio.squeeze()

        # Normalize
        audio = audio / np.max(np.abs(audio)) * 0.95

        # Convert to base64
        audio_b64 = audio_to_base64(audio, sample_rate=24000)

        return {
            "audio_base64": audio_b64,
            "sample_rate": 24000,
            "duration_seconds": len(audio) / 24000,
            "text": text,
            "emotion": emotion,
        }

    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


# Pre-load model on worker start
print("[Handler] Pre-loading model...")
try:
    load_model()
except Exception as e:
    print(f"[Handler] Warning: Could not pre-load model: {e}")

# RunPod serverless entry point
runpod.serverless.start({"handler": handler})
