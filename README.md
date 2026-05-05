# Ren'Py Universal TTS

A drop-in Ren'Py self-voicing replacement for OpenAI-compatible local TTS
servers.

Put `renpy_universal_tts.rpy` into a game's `game/` folder, run a local
OpenAI-compatible `/v1/audio/speech` server, and press `V` in-game to toggle
self-voicing. The script sends Ren'Py text to the server and plays the response
through `ffplay`.

The default playback path is optimized for low-latency raw PCM streaming:

```text
curl -> ffplay
s16le / 24000 Hz / mono
```

## Quick Start

1. Start a supported local TTS server. See the Kokoro and VibeVoice sections
   below.
2. Copy this file into the target game's `game/` folder:

```text
renpy_universal_tts.rpy
```

3. Make sure `curl` and `ffplay` are available.
4. Edit the config block near the top of `renpy_universal_tts.rpy`.
5. Start the game.
6. Press `V` to enable Ren'Py self-voicing.
7. Press `V` again to turn it off.

Do not install multiple Ren'Py TTS replacement scripts at the same time. This
script sets `config.tts_function`.

## Requirements

- A Ren'Py game.
- An OpenAI-compatible speech endpoint.
- `curl`.
- `ffplay`.

Windows includes `curl.exe` on most modern installs. Install FFmpeg to get
`ffplay`, or put `ffplay.exe` beside `renpy_universal_tts.rpy`.

Linux:

```bash
sudo apt install curl ffmpeg
```

## Basic Configuration

Open `renpy_universal_tts.rpy` and edit these values near the top.

### Endpoint

```python
UNIVERSAL_TTS_URL = "http://localhost:8880/v1/audio/speech"
UNIVERSAL_TTS_MODEL = "tts-1"
UNIVERSAL_TTS_RESPONSE_FORMAT = "pcm"
UNIVERSAL_TTS_REQUEST_STREAM = True
UNIVERSAL_TTS_SPEED = None
UNIVERSAL_TTS_EXTRA_BODY = {}
```

### Playback Format

For raw PCM streaming:

```python
UNIVERSAL_TTS_FFPLAY_RAW_PCM = True
UNIVERSAL_TTS_PCM_SAMPLE_FORMAT = "s16le"
UNIVERSAL_TTS_PCM_SAMPLE_RATE = 24000
UNIVERSAL_TTS_PCM_CHANNEL_LAYOUT = "mono"
```

For encoded formats like MP3 or WAV:

```python
UNIVERSAL_TTS_RESPONSE_FORMAT = "mp3"
UNIVERSAL_TTS_REQUEST_STREAM = False
UNIVERSAL_TTS_FFPLAY_RAW_PCM = False
```

Raw PCM gives the lowest latency when the server supports it.

### Default Voice

```python
UNIVERSAL_TTS_DEFAULT_VOICE = "Emma"
```

This voice is used when the script cannot identify a speaker or no speaker
mapping exists.

### Speaker Voices

```python
UNIVERSAL_TTS_VOICE_BY_SPEAKER = {
    "Narrator": "Davis",
    "MC": "Mike",
    "Daniel": "Mike",
}
```

Add or edit names to match the game:

```python
UNIVERSAL_TTS_VOICE_BY_SPEAKER = {
    "Narrator": "Davis",
    "Alice": "Emma",
    "Bob": "Carter",
    "Custom Character": "Grace",
}
```

### Speaker Name Reading

```python
UNIVERSAL_TTS_READ_SPEAKER_NAMES = "on_speaker_change"
```

Options:

```python
UNIVERSAL_TTS_READ_SPEAKER_NAMES = "always"
UNIVERSAL_TTS_READ_SPEAKER_NAMES = "never"
UNIVERSAL_TTS_READ_SPEAKER_NAMES = "on_speaker_change"
```

- `"always"` reads the speaker name before every line.
- `"never"` removes speaker names from spoken dialogue.
- `"on_speaker_change"` reads the speaker name only when the speaker changes.

Example:

```text
Alice: Hello.      -> reads "Alice. Hello."
Alice: Come here.  -> reads "Come here."
Bob: Wait.         -> reads "Bob. Wait."
```

## VibeVoice Setup

Start VibeVoice:

```powershell
git clone https://github.com/balu100/vibevoice-realtime-openai-api
cd vibevoice-realtime-openai-api
docker compose up -d --build
```

First run downloads models and voice presets, so it can take a while before
the server is ready.

Recommended VibeVoice config:

```python
UNIVERSAL_TTS_URL = "http://localhost:8880/v1/audio/speech"
UNIVERSAL_TTS_MODEL = "tts-1"
UNIVERSAL_TTS_RESPONSE_FORMAT = "pcm"
UNIVERSAL_TTS_REQUEST_STREAM = True
UNIVERSAL_TTS_SPEED = None

UNIVERSAL_TTS_FFPLAY_RAW_PCM = True
UNIVERSAL_TTS_PCM_SAMPLE_FORMAT = "s16le"
UNIVERSAL_TTS_PCM_SAMPLE_RATE = 24000
UNIVERSAL_TTS_PCM_CHANNEL_LAYOUT = "mono"

UNIVERSAL_TTS_DEFAULT_VOICE = "Emma"
UNIVERSAL_TTS_VOICE_BY_SPEAKER = {
    "Narrator": "Davis",
    "MC": "Mike",
    "Daniel": "Mike",
}
```

Common VibeVoice voice IDs:

```text
OpenAI-style aliases:
alloy, echo, fable, onyx, nova, shimmer

VibeVoice names:
Carter, Davis, Emma, Frank, Grace, Mike, Samuel
```

## Kokoro Setup

Start Kokoro:

CPU:

```powershell
docker run -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-cpu:latest
```

NVIDIA GPU:

```powershell
docker run --gpus all -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-gpu:latest
```

Recommended Kokoro raw PCM config, if your Kokoro server supports
`response_format = "pcm"`:

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

UNIVERSAL_TTS_DEFAULT_VOICE = "af_bella"
UNIVERSAL_TTS_VOICE_BY_SPEAKER = {
    "Narrator": "af_heart",
    "MC": "am_adam",
    "Daniel": "am_adam",
}
```

Kokoro MP3 fallback config, if raw PCM is not available:

```python
UNIVERSAL_TTS_URL = "http://127.0.0.1:8880/v1/audio/speech"
UNIVERSAL_TTS_MODEL = "kokoro"
UNIVERSAL_TTS_RESPONSE_FORMAT = "mp3"
UNIVERSAL_TTS_REQUEST_STREAM = False
UNIVERSAL_TTS_SPEED = 1.0

UNIVERSAL_TTS_FFPLAY_RAW_PCM = False
UNIVERSAL_TTS_DEFAULT_VOICE = "af_bella"
```

Common Kokoro voice IDs:

```text
American English female:
af_heart, af_alloy, af_aoede, af_bella, af_jessica, af_kore,
af_nicole, af_nova, af_river, af_sarah, af_sky

American English male:
am_adam, am_echo, am_eric, am_fenrir, am_liam, am_michael,
am_onyx, am_puck, am_santa

British English female:
bf_alice, bf_emma, bf_isabella, bf_lily

British English male:
bm_daniel, bm_fable, bm_george, bm_lewis
```

Your running server is the final source of truth. If it supports a voice-list
endpoint, check:

```text
http://localhost:8880/v1/audio/voices
```

## Test The Server

Raw PCM test:

PowerShell:

```powershell
$body = @{
  model = "tts-1"
  voice = "Emma"
  input = "Hello from universal TTS."
  response_format = "pcm"
  stream = $true
} | ConvertTo-Json -Compress

$tmp = Join-Path $env:TEMP "renpy_universal_tts.json"
Set-Content -NoNewline -Encoding ascii $tmp $body

cmd /c "curl.exe -sN --json @$tmp http://localhost:8880/v1/audio/speech | ffplay.exe -nodisp -autoexit -f s16le -sample_rate 24000 -ch_layout mono -i -"
```

Linux:

```bash
tmp="$(mktemp)"
printf '%s' '{"model":"tts-1","voice":"Emma","input":"Hello from universal TTS.","response_format":"pcm","stream":true}' > "$tmp"
curl -sN --json @"$tmp" http://localhost:8880/v1/audio/speech | ffplay -nodisp -autoexit -f s16le -sample_rate 24000 -ch_layout mono -i -
rm -f "$tmp"
```

If this works, the Ren'Py script is using the same audio path.

## Advanced Configuration

### ffplay Channel Option

Current ffplay builds use:

```python
UNIVERSAL_TTS_FFPLAY_CHANNEL_OPTION = "ch_layout"
```

Older ffplay builds may need:

```python
UNIVERSAL_TTS_FFPLAY_CHANNEL_OPTION = "ac"
```

### External Tool Paths

```python
UNIVERSAL_TTS_CURL_PATH = "curl"
UNIVERSAL_TTS_FFPLAY_PATH = "ffplay"
UNIVERSAL_TTS_FFPLAY_LOGLEVEL = "error"
UNIVERSAL_TTS_FFPLAY_VOLUME = None
UNIVERSAL_TTS_FFPLAY_EXTRA_ARGS = ()
```

If `ffplay` is not beside the script and not on `PATH`, set an absolute path:

```python
UNIVERSAL_TTS_FFPLAY_PATH = "C:/Tools/ffmpeg/bin/ffplay.exe"
```

Optional volume example:

```python
UNIVERSAL_TTS_FFPLAY_VOLUME = 80
```

### Extra Request Fields

Use `UNIVERSAL_TTS_EXTRA_BODY` for server-specific fields:

```python
UNIVERSAL_TTS_EXTRA_BODY = {
    "temperature": 0.7,
}
```

These fields are merged into the JSON request body.

## How It Works

This script sets Ren'Py's `config.tts_function`, so it only runs when Ren'Py
self-voicing is enabled. It does not patch every dialogue line directly.

When Ren'Py asks for a line to be spoken, the script writes a temporary JSON
request, starts `curl`, starts `ffplay`, and pipes `curl` stdout into `ffplay`
stdin.

When a new line starts or self-voicing is turned off, the script stops the
current `curl` and `ffplay` processes so they do not keep running in the
background.

## Troubleshooting

### Nothing happens when pressing `V`

- Make sure `renpy_universal_tts.rpy` is inside the game's `game/` folder.
- Make sure the game supports Ren'Py self-voicing.
- Check `log.txt` for lines starting with `UNIVERSAL TTS`.

### The game logs connection errors

- Make sure the TTS server is still running.
- Check that `UNIVERSAL_TTS_URL` matches the server address.
- Try the server test command above.

### The API works but no sound plays

- Make sure `ffplay` is installed or beside the `.rpy` file.
- For raw PCM, check that the PCM format matches the ffplay config.
- For MP3/WAV, set `UNIVERSAL_TTS_FFPLAY_RAW_PCM = False`.
- If ffplay exits immediately, try `UNIVERSAL_TTS_FFPLAY_CHANNEL_OPTION = "ac"`.

### Voice volume is too low or muted

Audio is played through external `ffplay`, not Ren'Py's voice mixer. Ren'Py
voice volume and mute settings do not control it.

Use:

```python
UNIVERSAL_TTS_FFPLAY_VOLUME = 80
```

or adjust system volume.

## Expected Logs

```text
UNIVERSAL TTS: stream MISS
UNIVERSAL TTS: playback format
UNIVERSAL TTS: pipe started
UNIVERSAL TTS: pipe finished
```

## Notes

- This is meant as a universal drop-in helper, so it avoids editing the target
  game's scripts.
- It depends on Ren'Py self-voicing. Use `V` to control it.
- It expects a local OpenAI-compatible TTS server. The script does not start the
  server by itself.
- Audio is played by `ffplay`, outside Ren'Py's mixer.
