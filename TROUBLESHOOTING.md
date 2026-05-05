# Troubleshooting

Check the game's `log.txt` first. Search for:

```text
UNIVERSAL TTS
```

## Pressing V Does Nothing

- Make sure `renpy_universal_tts.rpy` is inside the game's `game/` folder.
- Make sure the game is a Ren'Py game.
- Make sure no other TTS replacement script is installed.
- Check `log.txt` for `UNIVERSAL TTS: renpy_universal_tts.rpy loaded`.

## Server Is Not Reached

Check that the server is running and that this URL matches your config:

```python
UNIVERSAL_TTS_URL = "http://localhost:8880/v1/audio/speech"
```

VibeVoice usually uses:

```python
UNIVERSAL_TTS_ENGINE = "vibevoice"
UNIVERSAL_TTS_URL = "http://localhost:8880/v1/audio/speech"
```

Kokoro usually uses:

```python
UNIVERSAL_TTS_ENGINE = "kokoro"
UNIVERSAL_TTS_URL = "http://127.0.0.1:8880/v1/audio/speech"
```

## API Works But There Is No Sound

Make sure `ffplay` works.

Windows:

```powershell
ffplay.exe -version
```

Linux:

```bash
ffplay -version
```

If `ffplay` is not found, install FFmpeg or set:

```python
UNIVERSAL_TTS_FFPLAY_PATH = "C:/Tools/ffmpeg/bin/ffplay.exe"
```

or:

```python
UNIVERSAL_TTS_FFPLAY_PATH = "/usr/bin/ffplay"
```

## Raw PCM Test Command

This is the same audio path the script uses.

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

If the terminal command works but Ren'Py does not, check the `UNIVERSAL TTS`
lines in `log.txt`.

## Loud Noise Or Broken Audio

This usually means the server output does not match the ffplay raw PCM settings.

For VibeVoice raw PCM, use:

```python
UNIVERSAL_TTS_RESPONSE_FORMAT = "pcm"
UNIVERSAL_TTS_REQUEST_STREAM = True
UNIVERSAL_TTS_FFPLAY_RAW_PCM = True
UNIVERSAL_TTS_PCM_SAMPLE_FORMAT = "s16le"
UNIVERSAL_TTS_PCM_SAMPLE_RATE = 24000
UNIVERSAL_TTS_PCM_CHANNEL_LAYOUT = "mono"
```

If your server returns MP3 or WAV, use:

```python
UNIVERSAL_TTS_FFPLAY_RAW_PCM = False
```

## ffplay Starts Then Exits

Try changing:

```python
UNIVERSAL_TTS_FFPLAY_CHANNEL_OPTION = "ch_layout"
```

to:

```python
UNIVERSAL_TTS_FFPLAY_CHANNEL_OPTION = "ac"
```

This depends on your ffplay build.

## Voice Volume Ignores Ren'Py Settings

This script plays audio through external `ffplay`, so Ren'Py voice volume does
not control it.

Use:

```python
UNIVERSAL_TTS_FFPLAY_VOLUME = 80
```

or adjust system volume.

## Current Line Is Skipped

The script cancels the old TTS process when a new line arrives. This is wanted
behavior when clicking through dialogue. If a line is skipped, check whether the
TTS server is still generating the previous request or has stopped accepting
new requests.

Useful log lines:

```text
UNIVERSAL TTS: queued
UNIVERSAL TTS: stream MISS
UNIVERSAL TTS: pipe started
UNIVERSAL TTS: pipe finished
```
