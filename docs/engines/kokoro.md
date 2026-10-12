# Kokoro

Use this route for ready-made voices, including a CPU-only installation.
Hardware and AA results are in [Engine Comparison](../ENGINE_COMPARISON.md).

## Start the Server

Install Docker, then run one command.

CPU:

```sh
docker run -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-cpu:latest
```

NVIDIA GPU (check the upstream image selector for newer GPU generations):

```sh
docker run --gpus all -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-gpu:latest
```

The server documents separate CPU, NVIDIA, and experimental AMD paths.
[Server installation and GPU-specific tags](https://github.com/remsky/Kokoro-FastAPI#quick-start-docker).
You can add `-e default_volume_multiplier=3.0` to adjust server-side volume.

## Select the Config

Copy [kokoro.json](../../configs/kokoro.json) into the game's `game/` folder as
`renpy_universal_tts_config.json`. Its endpoint is
`http://127.0.0.1:8880/v1/audio/speech`.

If that server version cannot return PCM, use
[kokoro_mp3.json](../../configs/kokoro_mp3.json). An encoded response may start
later; PCM is preferred when supported.

## Choose Voices

```json
"default_voice": "af_heart",
"voices": {
  "ExampleName1": "af_bella",
  "ExampleName2": "am_puck"
}
```

The original example voice grades below are voice-specific annotations, not
Artificial Analysis Elo scores. Availability depends on the installed server.

| Voice | Grade | Voice | Grade |
| --- | --- | --- | --- |
| af_heart | A | am_adam | F+ |
| af_alloy | C | am_echo | D |
| af_aoede | C+ | am_eric | D |
| af_bella | A- | am_fenrir | C+ |
| af_jessica | D | am_liam | D |
| af_kore | C+ | am_michael | C+ |
| af_nicole | B- | am_onyx | D |
| af_nova | C | am_puck | C+ |
| af_river | D | am_santa | D- |
| af_sarah | C+ | | |
| af_sky | C- | | |

Query your installed server for other languages and voice IDs:

```sh
curl --fail --silent --show-error http://127.0.0.1:8880/v1/audio/voices
```

This preset selects voice IDs. Upstream now also documents custom voicepack
clone-tuning, which needs separate preparation in that server.
[Server voice features](https://github.com/remsky/Kokoro-FastAPI#features).

Return to [game installation](../../README.md#set-it-up).
