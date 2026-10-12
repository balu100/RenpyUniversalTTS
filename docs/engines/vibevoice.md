# VibeVoice Realtime 0.5B

This preset targets the Realtime **0.5B** model, not VibeVoice 1.5B or 7B.
See [Engine Comparison](../ENGINE_COMPARISON.md) for hardware qualifications.
Microsoft publishes results for this exact Realtime model: SEED test-en WER
2.05% and speaker similarity 0.633. These are upstream model evaluations,
applicable as references when using the same weights through a server fork.
[Original evaluation](https://github.com/microsoft/VibeVoice/blob/main/docs/vibevoice-realtime-0.5b.md#results).

## Start the Server

```sh
git clone https://github.com/balu100/vibevoice-realtime-openai-api
cd vibevoice-realtime-openai-api
docker compose up -d --build
```

Wait for the model download and server readiness. The upstream wrapper describes
NVIDIA/CUDA requirements and an approximately 2 GB VRAM footprint; its CPU device
option is not a local game-speed benchmark.
[Upstream requirements](https://github.com/marhensa/vibevoice-realtime-openai-api#requirements).

If the selected fork's Compose file contains `default_volume_multiplier=3.0`,
edit it to your liking for louder or quieter speech.

## Select the Config

Use [vibevoice.json](../../configs/vibevoice.json), renamed to
`game/renpy_universal_tts_config.json`. The endpoint is
`http://localhost:8880/v1/audio/speech`; the preset requests streamed PCM.

## Choose Voices

| Voice | Project Listening Note |
| --- | --- |
| Carter | Male |
| Davis | Main narrator |
| Emma | Female |
| Frank | Australian |
| Grace | Soft male-sounding voice (subjective listening note) |
| Mike | Narrator |
| Samuel | Indian |

These are listening notes from the project's examples, not verified demographic
metadata or quality scores. Compatible aliases include `alloy`, `echo`, `fable`,
`onyx`, `nova`, and `shimmer`.

```json
"default_voice": "Emma",
"voices": {
  "Narrator": "Davis",
  "ExampleName1": "Emma",
  "ExampleName2": "Carter"
}
```

List the voices your server actually exposes:

```sh
curl --fail --silent --show-error http://localhost:8880/v1/audio/voices
```

The documented wrapper accepts compatible `.pt` presets in `models/voices/`;
it does not provide a public audio-to-cloned-voice workflow.
[Voice preparation](https://github.com/marhensa/vibevoice-realtime-openai-api#custom-voices--additional-voices).

Return to [game installation](../../README.md#set-it-up).
