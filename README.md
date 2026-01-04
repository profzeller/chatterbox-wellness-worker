# Chatterbox TTS Wellness Worker

RunPod Serverless worker for Chatterbox Text-to-Speech with voice cloning.

## Capabilities

- **Text-to-Speech** - Natural speech synthesis
- **Voice Cloning** - Clone any voice from a reference audio sample
- **Emotion Tags** - Control emotion in speech
- **Speed Control** - Adjust playback speed

## Deployment on RunPod

### 1. Fork this repo to your GitHub

### 2. Create Serverless Endpoint

1. Go to Serverless → New Endpoint
2. Source: GitHub repo URL
3. GPU: RTX 4090 or similar (8GB+ VRAM sufficient)
4. Max Workers: 1-2
5. Idle Timeout: 5 seconds
6. No network volume needed (model is ~3GB, included in Docker image)

### 3. Environment Variables

None required - model is bundled.

## API Usage

### Basic TTS (Default Voice)

```json
{
  "input": {
    "text": "Welcome to your daily wellness moment. Take a deep breath."
  }
}
```

### Voice Cloning

```json
{
  "input": {
    "text": "Hello, this is my cloned voice speaking.",
    "reference_audio_url": "https://example.com/my-voice-sample.wav"
  }
}
```

Or with base64 audio:

```json
{
  "input": {
    "text": "Hello, this is my cloned voice speaking.",
    "reference_audio_base64": "UklGRi..."
  }
}
```

### With Emotion Tags

```json
{
  "input": {
    "text": "[happy] I'm so excited to share these wellness tips with you!"
  }
}
```

Supported emotions: `happy`, `sad`, `angry`, `surprised`, `neutral`, `calm`

### With Parameters

```json
{
  "input": {
    "text": "This is a calm meditation guide.",
    "temperature": 0.5,
    "exaggeration": 0.8,
    "speed": 0.9,
    "cfg_weight": 0.5
  }
}
```

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `temperature` | 0.7 | 0.0-1.0 | Creativity/variability |
| `exaggeration` | 1.0 | 0.5-2.0 | Emotion intensity |
| `speed` | 1.0 | 0.5-2.0 | Playback speed |
| `cfg_weight` | 0.5 | 0.0-1.0 | Classifier-free guidance |

## Response Format

```json
{
  "audio_base64": "UklGRi...",
  "sample_rate": 24000,
  "duration_seconds": 3.5,
  "text": "The synthesized text",
  "emotion": "happy"
}
```

## Cost Estimates

| Task | GPU | Time | Cost |
|------|-----|------|------|
| TTS (30 words) | RTX 4090 | ~10s | ~$0.001 |
| TTS (100 words) | RTX 4090 | ~30s | ~$0.003 |
| Voice Clone Setup | RTX 4090 | ~5s | ~$0.0005 |

## Reference Audio Requirements

For best voice cloning results:
- WAV format (16-bit, mono)
- 5-15 seconds of clear speech
- Minimal background noise
- Single speaker only
- Natural speaking pace

## Local Development

```bash
# Build
docker build -t chatterbox-wellness-worker .

# Run (requires NVIDIA GPU)
docker run --gpus all chatterbox-wellness-worker
```

## Example: Wellness Narration

```json
{
  "input": {
    "text": "[calm] Welcome to today's mindfulness session. Find a comfortable position, close your eyes, and let's begin our journey to inner peace.",
    "temperature": 0.5,
    "speed": 0.85
  }
}
```

## License

MIT
