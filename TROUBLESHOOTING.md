# Troubleshooting

Check the game's `log.txt` first. Search for:

```text
UNIVERSAL TTS
```

If `log.txt` does not include `UNIVERSAL TTS` lines, check the script's own
debug file:

```text
game/renpy_universal_tts_debug.log
```

## Pressing V Does Nothing

- Make sure `renpy_universal_tts.rpy` is inside the game's `game/` folder.
- Make sure `renpy_universal_tts_config.json` is next to it.
- Make sure the game is a Ren'Py game.
- Make sure no other TTS replacement script is installed.
- Check for `UNIVERSAL TTS: config loaded`.
  If that line is not in `log.txt`, check `renpy_universal_tts_debug.log`.

If the config is missing, the log will contain:

```text
UNIVERSAL TTS ERROR: missing renpy_universal_tts_config.json
```

## Config Does Not Load

JSON does not allow comments or trailing commas.

Bad:

```json
{
  "engine": "vibevoice",
}
```

Good:

```json
{
  "engine": "vibevoice"
}
```

## Server Is Not Reached

For VibeVoice/Kokoro/custom OpenAI-compatible servers, check:

```json
"openai": {
  "url": "http://localhost:8880/v1/audio/speech"
}
```

For Chatterbox native profiles, check:

```json
"chatterbox": {
  "url": "http://localhost:8880/tts"
}
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

If `ffplay` is not found, set:

```json
"tools": {
  "ffplay_path": "C:/Tools/ffmpeg/bin/ffplay.exe"
}
```

or:

```json
"tools": {
  "ffplay_path": "/usr/bin/ffplay"
}
```

## Raw PCM Test Command

This is the same audio path the script uses for raw PCM.

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

## Chatterbox Raw PCM Test Command

PowerShell:

```powershell
$body = @{
  text = "Hello from Chatterbox."
  voice_mode = "predefined"
  predefined_voice_id = "Emily.wav"
  output_format = "pcm"
  split_text = $false
} | ConvertTo-Json -Compress

$tmp = Join-Path $env:TEMP "chatterbox_tts.json"
Set-Content -NoNewline -Encoding ascii $tmp $body

cmd /c "curl.exe -sN --json @$tmp http://localhost:8880/tts | ffplay.exe -nodisp -autoexit -f s16le -sample_rate 24000 -ch_layout mono -i -"
```

If this fails because your Chatterbox build does not support PCM, use WAV:

```json
"audio": {
  "raw_pcm": false
},
"chatterbox": {
  "output_format": "wav"
}
```

## Loud Noise Or Broken Audio

The server output does not match the `audio` settings.

For raw PCM:

```json
"audio": {
  "raw_pcm": true,
  "sample_format": "s16le",
  "sample_rate": 24000,
  "channel_layout": "mono"
}
```

For MP3/WAV/Opus:

```json
"audio": {
  "raw_pcm": false
}
```

## ffplay Starts Then Exits

Try changing:

```json
"ffplay_channel_option": "ch_layout"
```

to:

```json
"ffplay_channel_option": "ac"
```

## Voice Volume Ignores Ren'Py Settings

This script plays audio through external `ffplay`, so Ren'Py voice volume does
not control it.

Use:

```json
"tools": {
  "ffplay_volume": 80
}
```

or adjust system volume.

## Current Line Is Skipped

The script cancels the old TTS process when a new line arrives. This is wanted
behavior when clicking through dialogue.

Useful log lines:

```text
UNIVERSAL TTS: queued
UNIVERSAL TTS: stream MISS
UNIVERSAL TTS: request built
UNIVERSAL TTS: pipe started
UNIVERSAL TTS: pipe finished
```
