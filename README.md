# Ren'Py Universal TTS

Drop-in AI text-to-speech for Ren'Py games.

Copy the script and config file into a game's `game/` folder, start a local TTS
server, and press `V` in-game. Ren'Py self-voicing will use your local AI voice
instead of the default system voice.

The `.rpy` file is the mechanics. The JSON file is the config.

```text
game/
  renpy_universal_tts.rpy
  renpy_universal_tts_config.json
```

Do not install multiple Ren'Py TTS replacement scripts at the same time.

## Fast Setup

1. Copy these two files into the target game's `game/` folder:

```text
renpy_universal_tts.rpy
renpy_universal_tts_config.json
```

2. Start your TTS server.
3. Install `ffplay`.
4. Edit only `renpy_universal_tts_config.json`.
5. Start the game.
6. Press `V` to turn AI self-voicing on.
7. Press `V` again to turn it off.

To switch engine, copy one of the example configs from `configs/` and rename it:

```text
configs/vibevoice.json              -> renpy_universal_tts_config.json
configs/kokoro.json                 -> renpy_universal_tts_config.json
configs/kokoro_mp3.json             -> renpy_universal_tts_config.json
configs/chatterbox_predefined.json  -> renpy_universal_tts_config.json
configs/chatterbox_clone.json       -> renpy_universal_tts_config.json
configs/custom_openai.json          -> renpy_universal_tts_config.json
```

## Install ffplay

Windows:

- Install FFmpeg.
- Put `ffplay.exe` on `PATH`, or put it next to `renpy_universal_tts.rpy`.

Linux:

```bash
sudo apt install curl ffmpeg
```

## Start VibeVoice

```powershell
git clone https://github.com/balu100/vibevoice-realtime-openai-api
cd vibevoice-realtime-openai-api
docker compose up -d --build
```

You can edit the Compose file's `default_volume_multiplier=3.0` value to your
liking for louder or quieter sounds.

Use:

```text
configs/vibevoice.json
```

VibeVoice voices:

```text
Carter (Male)
Davis (Main narrator)
Emma (Female)
Frank (Australian)
Grace (Soft male)
Mike (Narrator)
Samuel (Indian)
```

OpenAI-style aliases:

```text
alloy, echo, fable, onyx, nova, shimmer
```

## Start Kokoro

CPU:

```powershell
docker run -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-cpu:latest
```

NVIDIA GPU:

```powershell
docker run --gpus all -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-gpu:latest
```

You can add `-e default_volume_multiplier=3.0` for louder sounds.

Use:

```text
configs/kokoro.json
```

If your Kokoro server does not support raw PCM streaming, use:

```text
configs/kokoro_mp3.json
```

Kokoro voices with quality grades:

```text
af_heart (A)
af_alloy (C)
af_aoede (C+)
af_bella (A-)
af_jessica (D)
af_kore (C+)
af_nicole (B-)
af_nova (C)
af_river (D)
af_sarah (C+)
af_sky (C-)
am_adam (F+)
am_echo (D)
am_eric (D)
am_fenrir (C+)
am_liam (D)
am_michael (C+)
am_onyx (D)
am_puck (C+)
am_santa (D-)
```

## Start Chatterbox

Start Chatterbox-TTS-Server, then open:

```text
http://localhost:8880/docs
```

Use predefined voices:

```text
configs/chatterbox_predefined.json
```

Use reference audio / voice cloning:

```text
configs/chatterbox_clone.json
```

Native Chatterbox streaming uses:

```json
"stream": true,
"chunk_size": 50,
"split_text": true
```

Streaming on the native `/tts` endpoint requires a Chatterbox server build that
supports `stream: true`. If your server does not support it yet, set
`"stream": false` in the Chatterbox config.

### Character Voice Cloning

Chatterbox can use reference audio files for cloned character voices.

Put reference `.wav` or `.mp3` files into the Chatterbox server's
`reference_audio` folder, then map game speakers to those files in
`renpy_universal_tts_config.json`.

```json
"profiles": {
  "Alice": {
    "voice_mode": "clone",
    "reference_audio_filename": "alice_reference.wav"
  },
  "Bob": {
    "voice_mode": "clone",
    "reference_audio_filename": "bob_reference.wav"
  }
}
```

This lets each character use a different cloned voice. Voice quality depends on
the reference audio and the Chatterbox server settings.

You can also tune a cloned profile with Chatterbox generation settings:

```json
"Alice": {
  "voice_mode": "clone",
  "reference_audio_filename": "Gianna.wav",
  "exaggeration": 1.2,
  "seed": 3000
}
```

For predefined voices, use filenames from the Chatterbox `voices` folder:

```json
"Bob": {
  "voice_mode": "predefined",
  "predefined_voice_id": "Michael.wav"
}
```

If your Chatterbox build does not support raw PCM, set:

```json
"audio": {
  "raw_pcm": false
},
"chatterbox": {
  "output_format": "wav"
}
```

## Change Voices

For VibeVoice, Kokoro, and other OpenAI-compatible servers:

```json
"default_voice": "Emma",
"voices": {
  "Narrator": "Davis",
  "Alice": "Emma",
  "Bob": "Carter"
}
```

For Chatterbox:

```json
"profiles": {
  "Narrator": {
    "voice_mode": "predefined",
    "predefined_voice_id": "Emily.wav"
  },
  "Alice": {
    "voice_mode": "clone",
    "reference_audio_filename": "Gianna.wav"
  }
}
```

Speaker names must match the names the game shows in dialogue.

## Speaker Name Reading

```json
"speaker_name_mode": "on_speaker_change"
```

Options:

```text
always             read the speaker name every line
never              never read speaker names
on_speaker_change  read the name only when the speaker changes
```

Example with `on_speaker_change`:

```text
Alice: Hello.      -> Alice. Hello.
Alice: Come here.  -> Come here.
Bob: Wait.         -> Bob. Wait.
```

## More Help

- See `CONFIG_EXAMPLES.md` for the config layout.
- See `TROUBLESHOOTING.md` if the server works but Ren'Py has no sound.

Useful log lines in `log.txt`:

```text
UNIVERSAL TTS: config loaded
UNIVERSAL TTS: stream MISS
UNIVERSAL TTS: request built
UNIVERSAL TTS: pipe started
UNIVERSAL TTS: pipe finished
```

If `log.txt` does not show these lines, check:

```text
game/renpy_universal_tts_debug.log
```
