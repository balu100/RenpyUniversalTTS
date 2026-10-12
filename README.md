# Ren'Py Universal TTS

Read Ren'Py dialogue with a local AI voice. Press **V** to enable self-voicing;
press it again to stop. Character voices and speaker-name reading are configured
in one JSON file.

## What You Need

- A desktop Ren'Py game on Windows or Linux.
- `renpy_universal_tts.rpy` and `renpy_universal_tts_config.json` in its `game/` folder.
- **curl and ffplay** on the gaming computer. ffplay is included in FFmpeg builds.
- One running **TTS server**, on that computer or another reachable machine.

The server runs the AI model and determines the CPU/GPU and memory requirements.
The game-side script does not load model weights. Docker is needed only for the
server installation routes that use it.

## Engines at a Glance

Published quality references checked **2026-10-12**. GPU capacities below are
starting budgets for TTS; allow extra memory for the game.

| Engine / Model | Published Quality Reference | GPU / VRAM to Plan For | What It Offers | Setup |
| --- | --- | --- | --- | --- |
| **Breeze TTS 2** | **1222 AA Elo** | **8 GB NVIDIA** with the included INT8 server; **12 GB** official eager / **24 GB** official full fast path | Reference cloning, text-described voices, and delivery instructions; English/Chinese | [Breeze](docs/engines/breeze.md) |
| **Kokoro 82M v1.0** | **1064 AA Elo** | **CPU supported**; about **4 GB** GPU budget | Ready-made voices and a GPU-free installation route | [Kokoro](docs/engines/kokoro.md) |
| **Chatterbox Original** | **1026 AA Elo** | **8 GB** starting GPU budget; CPU also supported | Reference-file cloning and Original-model generation controls | [Chatterbox](docs/engines/chatterbox.md) |
| **VibeVoice Realtime 0.5B** | **2.05% WER**, SEED test-en | **4 GB+ NVIDIA** recommended; about **2 GB** published usage | Streamed English speech with ready-made voice presets | [VibeVoice](docs/engines/vibevoice.md) |
| **Qwen3-TTS 12Hz Base 0.6B** | **1.32% WER**, SEED test-en | **8 GB NVIDIA** demonstrated upstream | Reference cloning with the smaller Qwen Base model | [Qwen](docs/engines/qwen.md) |
| **Qwen3-TTS 12Hz Base 1.7B** | **1.24% WER**, SEED test-en | **8 GB NVIDIA** demonstrated upstream | Reference cloning with the larger Qwen Base model | [Qwen](docs/engines/qwen.md) |
| **Chatterbox Turbo / Multilingual** | [Publisher model demos](https://github.com/resemble-ai/chatterbox#-model-zoo) | **8 GB** starting server budget; CPU route available | Turbo reduces compute; Multilingual supports a wider language set | [Chatterbox](docs/engines/chatterbox.md) |
| **Custom OpenAI-compatible** | Your selected model's rating | Your selected server's requirements | Use another compatible speech server | [Custom Server](docs/engines/custom.md) |

**AA Elo: higher is better** for listener preference. **WER: lower is better**
for spoken-word accuracy. These are different measurements, not a shared ranking;
Turbo/Multilingual have no matching score on the AA boards used here.
Sources: [Artificial Analysis](https://artificialanalysis.ai/text-to-speech/leaderboard/provider-voice/open-weights),
[Qwen evaluation](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base#evaluation),
[Microsoft Realtime evaluation](https://github.com/microsoft/VibeVoice/blob/main/docs/vibevoice-realtime-0.5b.md#results).

Breeze's rating is the upstream **Breeze TTS 2** model reference; the included
INT8 server is its smaller-memory deployment option. Use **16 GB system RAM**
as a project starting recommendation, or **32 GB** for more game/Docker headroom.
See [memory sources, cloning scores, and measured local results](docs/ENGINE_COMPARISON.md)
for the evidence behind each row and the effect of model/server settings.

## Set It Up

1. Follow **one engine guide** above. Start its server and wait until its model is ready.
2. Install FFmpeg, including ffplay, and curl. On Windows check `curl.exe --version`
   and `ffplay.exe -version`; ffplay can also be placed beside the `.rpy` file.
   On Debian/Ubuntu use `sudo apt install curl ffmpeg`.
3. Copy `renpy_universal_tts.rpy` into the game's `game/` folder.
4. Copy the chosen preset from `configs/` into that folder and rename it to
   **`renpy_universal_tts_config.json`**. Replace its existing config if present.
5. Edit the server URL and voice IDs as described in the engine guide. Start the
   game and press **V**.

```text
YourGame/
  game/
    renpy_universal_tts.rpy
    renpy_universal_tts_config.json
```

Install one TTS replacement script at a time. Most presets use port `8880`;
Breeze uses `7860`. Servers sharing a port cannot run simultaneously unless you
change their published ports and matching config URLs.

## Pick a Preset

| Preset | Purpose |
| --- | --- |
| [kokoro.json](configs/kokoro.json) | Kokoro raw PCM |
| [kokoro_mp3.json](configs/kokoro_mp3.json) | Kokoro encoded MP3 fallback |
| [vibevoice.json](configs/vibevoice.json) | VibeVoice Realtime PCM stream |
| [qwen.json](configs/qwen.json) | Qwen registered voice IDs |
| [chatterbox_predefined.json](configs/chatterbox_predefined.json) | Predefined files, PCM-capable server |
| [chatterbox_clone.json](configs/chatterbox_clone.json) | Reference files, PCM-capable server |
| [breeze.json](configs/breeze.json) | Breeze saved clones and optional direction |
| [breeze_design.json](configs/breeze_design.json) | Breeze voices described in text |
| [custom_openai.json](configs/custom_openai.json) | Other compatible speech APIs |

Example names and custom voice IDs are placeholders. Reference audio is not bundled.
Register your voices on the server before selecting them in a config.
For stock Chatterbox WAV streaming, see the format change in its guide.

## Change Character Voices

For OpenAI-compatible presets, an unmatched speaker uses `default_voice`:

```json
"default_voice": "af_heart",
"voices": {
  "ExampleName1": "af_bella",
  "ExampleName2": "am_puck"
}
```

Replace the example names with the displayed speaker names in your game.
For Chatterbox references and Breeze instructions, use their engine guides.
[Config Examples](CONFIG_EXAMPLES.md) explains inheritance and advanced fields.

Speaker-name reading uses:

```json
"speaker_name_mode": "on_speaker_change"
```

| Value | Result |
| --- | --- |
| `on_speaker_change` | Read the name when the speaker changes |
| `always` | Read the name on every line |
| `never` | Read only the dialogue |

## Playback and Compatibility

Audio streams through external ffplay. It has its own volume; the game's voice
slider does not control it. Set `tools.ffplay_volume` between `0` and `100` if needed.
New dialogue interrupts the previous line. Audio is generated again on each
request; this version does not maintain an audio cache.

Missing or invalid configs leave the game's original self-voicing handler in
place. Errors are recorded in `game/renpy_universal_tts_debug.log`.

This is a desktop drop-in mod, not a guarantee for every game's custom dialogue
screens. See [Compatibility](docs/COMPATIBILITY.md) for test coverage.

## Help and Development

- [Troubleshooting](TROUBLESHOOTING.md): config, server, tool, and audio errors.
- [Config Examples](CONFIG_EXAMPLES.md): all optional settings.
- [Development](docs/DEVELOPMENT.md): tests, release packaging, and benchmarks.
