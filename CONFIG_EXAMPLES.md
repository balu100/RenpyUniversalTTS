# Config Examples

All user settings live in `renpy_universal_tts_config.json`.

The `.rpy` file should not be edited for normal setup. Pick an example from
`configs/`, copy it next to the `.rpy`, and rename it to:

```text
renpy_universal_tts_config.json
```

## Main Fields

```json
{
  "enabled": true,
  "engine": "vibevoice",
  "speaker_name_mode": "on_speaker_change",
  "tools": {},
  "audio": {},
  "request": {},
  "openai": {},
  "default_voice": "Emma",
  "voices": {}
}
```

For native Chatterbox `/tts` configs, the `openai`, `default_voice`, and
`voices` fields are replaced by a `chatterbox` profile block.

## VibeVoice

Use `configs/vibevoice.json`.

Voice mapping:

```json
"default_voice": "Emma",
"voices": {
  "Narrator": "Davis",
  "Alice": "Emma",
  "Bob": "Carter"
}
```

Endpoint:

```json
"request": {
  "type": "openai"
},
"openai": {
  "url": "http://localhost:8880/v1/audio/speech",
  "model": "tts-1",
  "response_format": "pcm",
  "stream": true,
  "speed": null,
  "extra_body": {}
}
```

## Kokoro Raw PCM

Use `configs/kokoro.json`.

```json
"default_voice": "af_heart",
"voices": {
  "Narrator": "af_heart",
  "Alice": "af_bella",
  "Bob": "am_puck"
}
```

## Kokoro MP3 Fallback

Use `configs/kokoro_mp3.json`.

```json
"audio": {
  "raw_pcm": false,
  "sample_format": "s16le",
  "sample_rate": 24000,
  "channel_layout": "mono"
},
"openai": {
  "response_format": "mp3",
  "stream": false
}
```

This has more delay than raw PCM streaming, but it is useful if a server does
not support raw PCM.

## Qwen3-TTS

Use `configs/qwen.json`.

Qwen uses the normal OpenAI-compatible config shape. Voice IDs come from the
Qwen server's `voices.json`; the example IDs below are placeholders.

Reference audio files need to be in the Qwen server's `reference_audio/` folder,
and each usable voice also needs an entry in `voices.json`.

```json
"request": {
  "type": "openai"
},
"openai": {
  "url": "http://127.0.0.1:8880/v1/audio/speech",
  "model": "tts-1",
  "response_format": "pcm",
  "speed": null,
  "extra_body": {}
},
"default_voice": "d01",
"voices": {
  "Narrator": "d01",
  "ExampleName1": "d03",
  "ExampleName2": "d12"
}
```

Qwen streams when `response_format` is `pcm`. Do not add `"stream": true`
unless your Qwen server explicitly supports that request field.

## Chatterbox Predefined Voices

Use `configs/chatterbox_predefined.json`.

Native Chatterbox streaming needs a server build that supports `stream: true`.
If your server rejects the request, set `"stream": false`.

For streaming Chatterbox, use `"split_text": true`. `chunk_size` controls how
many words are synthesized per streamed chunk. Lower values start faster; higher
values can sound smoother. The default example uses `50`.

```json
"request": {
  "type": "chatterbox_tts"
},
"chatterbox": {
  "url": "http://localhost:8880/tts",
  "output_format": "pcm",
  "stream": true,
  "chunk_size": 50,
  "split_text": true,
  "default_profile": {
    "voice_mode": "predefined",
    "predefined_voice_id": "Emily.wav"
  },
  "profiles": {
    "Alice": {
      "voice_mode": "predefined",
      "predefined_voice_id": "Alice.wav"
    }
  }
}
```

## Chatterbox Voice Cloning

Use `configs/chatterbox_clone.json`.

Reference audio filenames must exist in the Chatterbox server's
`reference_audio` folder. The Ren'Py mod does not upload audio files; it only
sends the filename to the Chatterbox API.

```text
Chatterbox-TTS-Server/
  reference_audio/
    alice_reference.wav
```

```json
"profiles": {
  "Alice": {
    "voice_mode": "clone",
    "reference_audio_filename": "alice_reference.wav",
    "temperature": 0.8,
    "exaggeration": 1.2,
    "cfg_weight": 0.5,
    "seed": 3000,
    "speed_factor": 1.0
  }
}
```

## Audio

Raw PCM streaming:

```json
"audio": {
  "raw_pcm": true,
  "sample_format": "s16le",
  "sample_rate": 24000,
  "channel_layout": "mono"
}
```

Encoded MP3/WAV/Opus:

```json
"audio": {
  "raw_pcm": false
}
```

## Tools

```json
"tools": {
  "curl_path": "curl",
  "ffplay_path": "ffplay",
  "ffplay_loglevel": "error",
  "ffplay_channel_option": "ch_layout",
  "ffplay_volume": null,
  "ffplay_extra_args": []
}
```

If `ffplay` is not beside the `.rpy` file and not on `PATH`, use an absolute
path:

```json
"ffplay_path": "C:/Tools/ffmpeg/bin/ffplay.exe"
```

Older ffplay builds may need:

```json
"ffplay_channel_option": "ac"
```
