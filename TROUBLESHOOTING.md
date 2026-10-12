# Troubleshooting

Start with `game/renpy_universal_tts_debug.log`. Search the game's `log.txt`
for `UNIVERSAL TTS` too. Keep the TTS server terminal/log open while testing.

## Pressing V Does Nothing or Uses the System Voice

Check that both runtime files are in `game/` and only one replacement script
is installed. Restart the game after changing a config.

Missing, malformed, or disabled configs leave original self-voicing in place.
Look for `invalid config`, `failed to read config`, or `missing` in the debug
log. Field errors identify the offending key; typo messages may suggest its
correct spelling. JSON permits neither comments nor trailing commas.
If enabled and valid, expect `config loaded` and a self-voicing hook message.

## Server Is Not Reached

Check the **complete** endpoint and its published port:

| Preset | Default Speech Endpoint |
| --- | --- |
| Kokoro / VibeVoice / Qwen / custom | `http://127.0.0.1:8880/v1/audio/speech` |
| Chatterbox legacy PCM setup | `http://127.0.0.1:8880/tts` |
| Breeze | `http://127.0.0.1:7860/v1/audio/speech` |

Stock Chatterbox commonly publishes port 8004. Follow its actual Compose file.
Run one server per port. A model still downloading/loading is not yet ready.

The debug log records a pipe result with HTTP status, curl exit code, and player
exit code, followed by tool error text.

| Result | Check |
| --- | --- |
| curl code 7 | Server not running, wrong host/port, or refused connection |
| curl code 28 | Connection/request timeout; check readiness and `network` settings |
| HTTP 404 | Wrong endpoint or unknown voice ID |
| HTTP 409 | Server still working; brief retries apply only to the current line |
| HTTP 422 | Unsupported settings, wrong voice mode, or invalid reference |
| HTTP 429 | Server rate limit |
| HTTP 503 | Model not ready; inspect server logs, including GPU memory errors |

HTTP error bodies are blocked from the audio pipe. A server returning HTTP 200
with non-audio bytes or an incompatible format still needs investigation.

## API Works but There Is No Sound

On Windows check `curl.exe --version` and `ffplay.exe -version`.
On Linux check `curl --version` and `ffplay -version`.
Set `tools.curl_path` / `tools.ffplay_path` if tools are not on PATH or beside
the script. Player errors now appear in the debug log.

A `pipe finished` message confirms process completion, not that the device
audibly played speech. Check system output device and volume too.

## Loud Noise or Wrong-Speed Speech

Match server output to the player. The normal PCM defaults are s16le,
24000 Hz, mono. Do not decode a WAV header, MP3 bytes, JSON, or SSE as raw PCM.

For stock Chatterbox native WAV streaming set `chatterbox.output_format: wav`.
If an older config explicitly has `audio.raw_pcm`, set it to false.
See [Chatterbox format guide](docs/engines/chatterbox.md#match-the-audio-format).

## Voices Do Not Change

Speaker names must match what the game displays. Unmatched speakers use the
default. Voice IDs must exist on the server:

- Qwen: server `voices.json` IDs, not the reference filename.
- Breeze: saved profile IDs from its UI / `/v1/audio/voices`.
- Chatterbox clone: filename in server `reference_audio/`.
- Chatterbox predefined: filename in server `voices/`.
- VibeVoice/Kokoro: installed voice IDs.

The script does not upload references. Missing Qwen IDs may fall back server-side.
If a custom game screen does not expose names to self-voicing, character mapping
may need game-specific integration.

## Volume Ignores the Game Slider

External ffplay is independent of Ren'Py's voice mixer. Example:

```json
"tools": {
  "ffplay_volume": 80
}
```

Use 0-100, or adjust system output volume.

## A Line Is Interrupted or Skipped

Advancing dialogue cancels old playback and pending work; only the latest line
is wanted. The client cannot guarantee that every server cancels GPU generation
when its connection closes. Breeze may return 409 while winding down.
The mod retries that status briefly and cancels retries when you advance again.

Useful log events are `queued`, `stream start`, `request built`, `pipe started`,
`pipe result`, `pipe canceled`, `busy retry`, and `pipe finished`.
There is no audio-cache MISS/HIT workflow in this version.

## Test PCM Outside the Game

Use a known registered voice from your server. This example is VibeVoice;
Qwen should omit `stream`, and Chatterbox uses a different request body.

PowerShell:

```powershell
$body = @{
  model = "tts-1"
  voice = "Emma"
  input = "Hello from Universal TTS."
  response_format = "pcm"
  stream = $true
} | ConvertTo-Json -Compress
$tmp = Join-Path $env:TEMP "universal_tts_test.json"
Set-Content -NoNewline -Encoding ascii $tmp $body
cmd /c "curl.exe --fail --silent --show-error --no-buffer --connect-timeout 5 --max-time 120 --header Content-Type:application/json --data-binary @$tmp http://127.0.0.1:8880/v1/audio/speech | ffplay.exe -nodisp -autoexit -loglevel error -f s16le -sample_rate 24000 -ch_layout mono -i -"
```

Linux:

```sh
printf '%s' '{"model":"tts-1","voice":"Emma","input":"Hello.","response_format":"pcm","stream":true}' |
curl --fail --silent --show-error --no-buffer --connect-timeout 5 --max-time 120 \
  --header 'Content-Type: application/json' --data-binary @- \
  http://127.0.0.1:8880/v1/audio/speech |
ffplay -nodisp -autoexit -loglevel error -f s16le -sample_rate 24000 -ch_layout mono -i -
```

For other engine bodies follow the engine guide and installed API schema.
