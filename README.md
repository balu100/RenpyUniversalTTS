# Ren'Py Universal TTS

Drop-in AI text-to-speech for Ren'Py games.

Copy one file into a game's `game/` folder, start a local TTS server, and press
`V` in-game. Ren'Py self-voicing will use your local AI voice instead of the
default system voice.

This project works with OpenAI-compatible `/v1/audio/speech` servers. Presets
are included for VibeVoice and Kokoro.

## Fast Setup

1. Start a TTS server.
2. Make sure `ffplay` is installed.
3. Copy `renpy_universal_tts.rpy` into the game's `game/` folder.
4. Open `renpy_universal_tts.rpy`.
5. Pick your engine near the top:

```python
UNIVERSAL_TTS_ENGINE = "vibevoice"
```

or:

```python
UNIVERSAL_TTS_ENGINE = "kokoro"
```

6. Start the game.
7. Press `V` to turn AI self-voicing on.
8. Press `V` again to turn it off.

Do not install multiple Ren'Py TTS replacement scripts at the same time.

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

Then use:

```python
UNIVERSAL_TTS_ENGINE = "vibevoice"
```

Default VibeVoice voices used by the preset:

```text
Narrator -> Davis
MC       -> Mike
Daniel   -> Mike
default  -> Emma
```

Other common VibeVoice voices:

```text
Carter, Davis, Emma, Frank, Grace, Mike, Samuel
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

You can add ```-e default_volume_multiplier=3.0``` for louder sounds

Then use:

```python
UNIVERSAL_TTS_ENGINE = "kokoro"
```

If your Kokoro server does not support raw PCM streaming, use the MP3 fallback:

```python
UNIVERSAL_TTS_ENGINE = "kokoro_mp3"
```

Default Kokoro voices used by the preset:

```text
Narrator -> af_heart
MC       -> am_puck
Daniel   -> am_puck
default  -> af_heart
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

## Change Voices

Edit this near the top of `renpy_universal_tts.rpy`:

```python
UNIVERSAL_TTS_DEFAULT_VOICE = "Emma"

UNIVERSAL_TTS_VOICE_BY_SPEAKER = {
    "Narrator": "Davis",
    "Alice": "Emma",
    "Bob": "Carter",
}
```

Speaker names must match the names the game shows in dialogue.

## Speaker Name Reading

```python
UNIVERSAL_TTS_READ_SPEAKER_NAMES = "on_speaker_change"
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

- See `CONFIG_EXAMPLES.md` for full config examples.
- See `TROUBLESHOOTING.md` if the server works but Ren'Py has no sound.

Useful log lines in `log.txt`:

```text
UNIVERSAL TTS: stream MISS
UNIVERSAL TTS: playback format
UNIVERSAL TTS: pipe started
UNIVERSAL TTS: pipe finished
```
