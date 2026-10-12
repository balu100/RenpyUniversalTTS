# Custom OpenAI-Compatible Server

Use [custom_openai.json](../../configs/custom_openai.json), renamed to
`game/renpy_universal_tts_config.json`.

Set the **complete speech endpoint**, model, and voice IDs your server accepts:

```json
"openai": {
  "url": "http://127.0.0.1:8880/v1/audio/speech",
  "model": "tts-1",
  "response_format": "pcm",
  "stream": true,
  "extra_body": {}
},
"default_voice": "your_voice_id"
```

Omit `stream` if your server does not accept that field. A PCM response format
alone does not guarantee the server sends audio while generation is in progress.
The mod requests audio and plays bytes as they arrive; actual streaming depends
on the backend.

PCM defaults to **s16le, 24000 Hz, mono**. Change `audio.sample_rate`,
`audio.sample_format`, and `audio.channel_layout` when the server specifies
different output. For WAV/MP3 use its encoded response format; the player infers
encoded playback unless you explicitly set `audio.raw_pcm`.

Global extra request fields go in `openai.extra_body`. Per-character extras go
in the voice object's `extra_body`; see [Config Examples](../../CONFIG_EXAMPLES.md).
Do not select SSE or base64 streaming: ffplay expects audio bytes.

This client has no API-key/header configuration. An authenticated cloud service
needs a compatible local proxy or a separate authentication feature; placing a
key in `extra_body` is not an HTTP Authorization header.

Hardware, languages, cloning, and licensing depend on your chosen server.
Test its documented request outside the game first. Return to
[game installation](../../README.md#set-it-up).
