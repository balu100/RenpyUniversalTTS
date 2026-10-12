# Breeze TTS 2

At a glance: **1222 AA Provider Voice Elo** for the upstream model, and an
**8 GB NVIDIA GPU target** for this guide's INT8 server. The model supports
reference cloning, text-described voice design, and delivery instructions.
[AA quality reference](https://artificialanalysis.ai/text-to-speech/leaderboard/provider-voice/open-weights).

This guide targets **remominor/breeze-tts-api**, using its INT8 hybrid checkpoint.
Its documented deployment requires Linux and NVIDIA CUDA and targets an 8 GB GPU.
See [Engine Comparison](../ENGINE_COMPARISON.md) for qualifications and AA results.
[Server requirements](https://github.com/remominor/breeze-tts-api#requirements).

## Official Model and INT8 Server

These are deployment options for **Breeze TTS 2**, not different model families.
The original PyTorch implementation recommends **12 GB GPU memory for eager
inference** or **24 GB for the full fast path**, with reported usage of about
7.7 GiB and 14.4 GiB respectively.
[Original-project requirements](https://github.com/breezeblue-ai/breeze-tts#requirements).

The included presets use the **8 GB-target INT8 server** below. Its JSON API and
saved profile IDs match this mod. The official server's multipart reference-upload
API is a different request format; the included JSON presets target remominor's
server. See [comparison and local memory measurement](../ENGINE_COMPARISON.md).

## Start the Server

```sh
git clone https://github.com/remominor/breeze-tts-api
cd breeze-tts-api
docker compose up -d --build
```

The default port is **7860**, and first startup downloads model assets.
On Windows this is a Linux-container deployment through Docker Desktop/WSL2
with NVIDIA GPU access, rather than a documented native Windows installation;
this project has not game-tested that route.
[Docker deployment](https://github.com/remominor/breeze-tts-api#docker-and-compose-deployment).

Open `http://127.0.0.1:7860/` for the server UI and
`http://127.0.0.1:7860/docs` for its API schema. Wait until the model is ready.

## Saved Character Voices

1. In the server UI, upload clean reference audio and its **exact transcript**.
2. Save the voice profile and copy its actual ID.
3. Copy [breeze.json](../../configs/breeze.json) as `game/renpy_universal_tts_config.json`.
4. Replace every `clone:example_*` placeholder with a saved profile ID.

You can list saved profiles with:

```sh
curl --fail --silent --show-error http://127.0.0.1:7860/v1/audio/voices
```

The server supports reusable profiles via its upload endpoint. Registration is
done once in its UI; the game sends the saved ID on each line.
[Profile API](https://github.com/remominor/breeze-tts-api#profiles-and-endpoint-summary).

```json
"default_voice": "clone:your_narrator_id",
"voices": {
  "ExampleName1": "clone:your_character_id",
  "ExampleName2": {
    "voice": "clone:your_character_id",
    "extra_body": {
      "instructions": "Speak calmly and thoughtfully.",
      "guidance_scale": 4
    }
  }
}
```

This selects a clone for ExampleName1 and directs that clone's delivery for
ExampleName2. English and Chinese are the model's documented languages.
[Voice cloning and direction](https://github.com/breezeblue-ai/breeze-tts#-voice-direction).

## Voice Design

Use [breeze_design.json](../../configs/breeze_design.json) to describe a voice
without reference audio. `default_voice: null` omits the API voice field.
Each character can override the global `extra_body.instructions`. The supplied
seed helps reproducibility but does not guarantee identical identity across
independent generated lines. Use saved reference profiles for a stable cast.

## Stream Settings

The presets request `stream: true`, `response_format: pcm`, and
`stream_format: audio`: continuous 24 kHz mono s16le bytes for ffplay.
SSE/base64 events are not supported by this player.
[Speech response formats](https://github.com/remominor/breeze-tts-api#voice-clone-or-direction).

This server permits one GPU request at a time. The mod briefly retries a `409`
busy response while that line remains current, and abandons the retry after a
skip or self-voicing shutdown. It does not use the experimental continuation API.

Check the model's [research/non-commercial license](https://github.com/remominor/breeze-tts-api/blob/main/MODEL_LICENSE)
for the intended use of locally generated output.
Return to [game installation](../../README.md#set-it-up).
