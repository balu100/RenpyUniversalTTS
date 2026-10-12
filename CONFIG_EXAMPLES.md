# Config Examples

Pick an engine preset, rename it to `renpy_universal_tts_config.json`, and place
it beside the `.rpy` in the game's `game/` folder. Restart the game after editing.
JSON allows neither comments nor trailing commas.

The short presets contain the settings most people need. Older full configs
with `tools` and `audio` blocks continue to work. Optional defaults are listed here.

## Basic Settings

```json
{
  "enabled": true,
  "engine": "kokoro",
  "speaker_name_mode": "on_speaker_change",
  "request": { "type": "openai" },
  "openai": {
    "url": "http://127.0.0.1:8880/v1/audio/speech",
    "model": "kokoro",
    "response_format": "pcm",
    "stream": true
  },
  "default_voice": "af_heart",
  "voices": {
    "ExampleName1": "af_bella",
    "ExampleName2": "am_puck"
  }
}
```

`engine` identifies the preset; `request.type` selects the wire protocol.
Set `enabled: false` to leave original self-voicing in place.
Speaker-name modes are `on_speaker_change`, `always`, and `never`.

Use the full endpoint URL, including `/v1/audio/speech` or native `/tts`.
Use the voice IDs or reference filenames actually registered on that server.
Unmatched speakers use `default_voice` (or Chatterbox's `default_profile`).

## OpenAI-Compatible Voices and Overrides

A string selects a voice. An object can also add per-character request settings:

```json
"openai": {
  "url": "http://127.0.0.1:7860/v1/audio/speech",
  "model": "tts-1",
  "response_format": "pcm",
  "stream": true,
  "extra_body": {
    "seed": 42,
    "guidance_scale": 4,
    "instructions": "Speak clearly and naturally."
  }
},
"default_voice": "clone:your_narrator",
"voices": {
  "ExampleName1": "clone:your_character",
  "ExampleName2": {
    "voice": "clone:your_character",
    "extra_body": {
      "instructions": "Speak calmly and thoughtfully."
    }
  }
}
```

Global `openai.extra_body` values are inherited by every speaker. The speaker's
`extra_body` replaces matching keys; other keys such as the seed remain inherited.
Omitting a profile's `voice` uses `default_voice`.

`extra_body` is for backend-specific options. Set `input`, `voice`, `model`,
and `response_format` using their dedicated fields; overriding those from
`extra_body` is rejected. Instructions/guidance fields above are Breeze features,
not universal OpenAI features. Only send options the selected server accepts.

For Breeze voice design, set `default_voice: null` and supply meaningful
`extra_body.instructions`; a profile can set `voice: null` explicitly to design
its own voice. The voice field is then omitted from the request.

`openai.speed` is optional and omitted when null. `openai.stream` is also
optional: Qwen's preset intentionally omits it. Transport format and actual
streaming behavior are server-specific.

## Native Chatterbox Profiles

Use `request.type: chatterbox_tts` and a `chatterbox` block:

```json
"chatterbox": {
  "url": "http://127.0.0.1:8880/tts",
  "output_format": "pcm",
  "stream": true,
  "split_text": true,
  "chunk_size": 50,
  "default_profile": {
    "voice_mode": "clone",
    "reference_audio_filename": "example_narrator.wav",
    "temperature": 0.8,
    "seed": 3000
  },
  "profiles": {
    "ExampleName1": {
      "reference_audio_filename": "example_character.wav"
    },
    "ExampleName2": {
      "voice_mode": "predefined",
      "predefined_voice_id": "Emily.wav",
      "seed": 2000
    }
  }
}
```

**All** default-profile fields are inherited, then speaker fields override them.
This includes voice mode, filename, temperature, exaggeration, CFG weight, seed,
speed, language, and any profile-level stream/split/chunk overrides. Native
global stream/split/chunk/language fields are applied before profile overrides.
Switching to predefined mode removes the inherited clone filename from the
API payload, and switching to clone mode removes the predefined filename.

Clone files must already exist in the **server's** `reference_audio/` folder.
Predefined files must exist in its `voices/` folder. The mod never uploads files.
Remove tuning fields unsupported by the selected model, especially Turbo.
See [Chatterbox](docs/engines/chatterbox.md) for the stock-WAV/PCM-fork distinction.

## Audio

When `audio.raw_pcm` is omitted, `pcm` selects raw playback and encoded formats
select decoder autodetection. A minimal PCM config defaults to:

```json
"audio": {
  "raw_pcm": true,
  "sample_format": "s16le",
  "sample_rate": 24000,
  "channel_layout": "mono"
}
```

Only change sample settings if your server produces another format. With a WAV,
MP3, Opus, AAC, or FLAC response, omit the block or set `raw_pcm: false`.
A contradictory explicit raw/encoded setting is rejected before self-voicing
is replaced. SSE event streams cannot be played by ffplay.

## Tool Paths and Volume

Optional defaults:

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

Executables are searched beside the script, in game folders, and on PATH.
If needed, use a full path with forward slashes, for example
`C:/Tools/ffmpeg/bin/ffplay.exe` or `/usr/bin/ffplay`.
Use `ffplay_channel_option: ac` only for a player version that needs that syntax.

`ffplay_volume` is 0-100; null leaves the player default. This is independent
of the game's voice mixer. Arbitrary player arguments are an advanced option
and can override playback behavior.

## Network

Optional defaults (seconds):

```json
"network": {
  "connect_timeout": 5,
  "request_timeout": 120,
  "busy_retry_seconds": 3
}
```

Connection and total-request timeouts prevent indefinite waits.
`busy_retry_seconds` allows short retries after HTTP 409, while that line is
still current. Set it to 0 to disable busy retries. Ordinary failures do not
automatically replay a partially heard line.

## Validation and Updates

The script checks required fields, known config keys, voice/profile shape,
numeric settings, and audio consistency when loading. It cannot know whether a
voice file exists on a remote server. That is checked by the server when called.

Missing, malformed, or disabled configs leave original self-voicing in place.
Inspect `game/renpy_universal_tts_debug.log` for precise field errors.
Optional preflight on a machine with Python:

```sh
python tools/check_config.py path/to/renpy_universal_tts_config.json
```

Updating the mod means replacing the `.rpy` and keeping your existing JSON.
New optional fields do not require rewriting an old config.
