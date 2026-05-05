# Config Examples

Most users only need `UNIVERSAL_TTS_ENGINE`.

Use one of these:

```python
UNIVERSAL_TTS_ENGINE = "vibevoice"
UNIVERSAL_TTS_ENGINE = "kokoro"
UNIVERSAL_TTS_ENGINE = "kokoro_mp3"
UNIVERSAL_TTS_ENGINE = "custom"
```

Leave advanced values as `None` unless you know you need to override them.

## VibeVoice

Use this when running:

```text
http://localhost:8880/v1/audio/speech
```

Simple config:

```python
UNIVERSAL_TTS_ENGINE = "vibevoice"
UNIVERSAL_TTS_DEFAULT_VOICE = "Emma"

UNIVERSAL_TTS_VOICE_BY_SPEAKER = {
    "Narrator": "Davis",
    "Alice": "Emma",
    "Bob": "Carter",
}
```

Preset details:

```python
UNIVERSAL_TTS_URL = "http://localhost:8880/v1/audio/speech"
UNIVERSAL_TTS_MODEL = "tts-1"
UNIVERSAL_TTS_RESPONSE_FORMAT = "pcm"
UNIVERSAL_TTS_REQUEST_STREAM = True

UNIVERSAL_TTS_FFPLAY_RAW_PCM = True
UNIVERSAL_TTS_PCM_SAMPLE_FORMAT = "s16le"
UNIVERSAL_TTS_PCM_SAMPLE_RATE = 24000
UNIVERSAL_TTS_PCM_CHANNEL_LAYOUT = "mono"
```

## Kokoro Raw PCM

Use this when your Kokoro server supports `response_format = "pcm"`.

Simple config:

```python
UNIVERSAL_TTS_ENGINE = "kokoro"
UNIVERSAL_TTS_DEFAULT_VOICE = "af_bella"

UNIVERSAL_TTS_VOICE_BY_SPEAKER = {
    "Narrator": "af_heart",
    "Alice": "af_bella",
    "Bob": "am_adam",
}
```

Preset details:

```python
UNIVERSAL_TTS_URL = "http://127.0.0.1:8880/v1/audio/speech"
UNIVERSAL_TTS_MODEL = "kokoro"
UNIVERSAL_TTS_RESPONSE_FORMAT = "pcm"
UNIVERSAL_TTS_REQUEST_STREAM = True
UNIVERSAL_TTS_SPEED = 1.0

UNIVERSAL_TTS_FFPLAY_RAW_PCM = True
UNIVERSAL_TTS_PCM_SAMPLE_FORMAT = "s16le"
UNIVERSAL_TTS_PCM_SAMPLE_RATE = 24000
UNIVERSAL_TTS_PCM_CHANNEL_LAYOUT = "mono"
```

## Kokoro MP3 Fallback

Use this if Kokoro PCM streaming does not work, or if the server only returns
MP3/WAV.

```python
UNIVERSAL_TTS_ENGINE = "kokoro_mp3"
UNIVERSAL_TTS_DEFAULT_VOICE = "af_bella"

UNIVERSAL_TTS_RESPONSE_FORMAT = "mp3"
UNIVERSAL_TTS_REQUEST_STREAM = False
UNIVERSAL_TTS_FFPLAY_RAW_PCM = False
```

This has more delay than raw PCM streaming, but it is simpler for some servers.

## Custom OpenAI-Compatible Server

Use this for any server that accepts OpenAI-style speech requests.

```python
UNIVERSAL_TTS_ENGINE = "custom"

UNIVERSAL_TTS_URL = "http://localhost:8880/v1/audio/speech"
UNIVERSAL_TTS_MODEL = "tts-1"
UNIVERSAL_TTS_DEFAULT_VOICE = "alloy"
UNIVERSAL_TTS_RESPONSE_FORMAT = "pcm"
UNIVERSAL_TTS_REQUEST_STREAM = True

UNIVERSAL_TTS_FFPLAY_RAW_PCM = True
UNIVERSAL_TTS_PCM_SAMPLE_FORMAT = "s16le"
UNIVERSAL_TTS_PCM_SAMPLE_RATE = 24000
UNIVERSAL_TTS_PCM_CHANNEL_LAYOUT = "mono"
```

For MP3/WAV:

```python
UNIVERSAL_TTS_RESPONSE_FORMAT = "mp3"
UNIVERSAL_TTS_REQUEST_STREAM = False
UNIVERSAL_TTS_FFPLAY_RAW_PCM = False
```

## Speaker Name Reading

```python
UNIVERSAL_TTS_READ_SPEAKER_NAMES = "always"
UNIVERSAL_TTS_READ_SPEAKER_NAMES = "never"
UNIVERSAL_TTS_READ_SPEAKER_NAMES = "on_speaker_change"
```

Recommended:

```python
UNIVERSAL_TTS_READ_SPEAKER_NAMES = "on_speaker_change"
```

## ffplay Path

If `ffplay` is next to the `.rpy` file or on `PATH`, keep:

```python
UNIVERSAL_TTS_FFPLAY_PATH = "ffplay"
```

Absolute Windows path example:

```python
UNIVERSAL_TTS_FFPLAY_PATH = "C:/Tools/ffmpeg/bin/ffplay.exe"
```

Absolute Linux path example:

```python
UNIVERSAL_TTS_FFPLAY_PATH = "/usr/bin/ffplay"
```

## Volume

Audio plays through external `ffplay`, not Ren'Py's voice mixer.

```python
UNIVERSAL_TTS_FFPLAY_VOLUME = 80
```

Leave it as `None` to use ffplay/system default volume.

## ffplay Channel Option

Current ffplay builds usually need:

```python
UNIVERSAL_TTS_FFPLAY_CHANNEL_OPTION = "ch_layout"
```

Older ffplay builds may need:

```python
UNIVERSAL_TTS_FFPLAY_CHANNEL_OPTION = "ac"
```

## Extra Request Fields

For server-specific options:

```python
UNIVERSAL_TTS_EXTRA_BODY = {
    "temperature": 0.7,
}
```

These fields are added to the JSON request body.
