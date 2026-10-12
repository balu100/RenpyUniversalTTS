# Qwen3-TTS Base

This setup uses the selected faster-qwen3-tts server with registered reference
voices. The **0.6B** and **1.7B** models use the same client config.

The original faster-qwen3-tts project benchmarks both on an RTX 4060 (8 GB),
which is a useful GPU starting point even when using this HTTP fork. Qwen's
official SEED test-en WER is 1.32% for 12Hz 0.6B Base and 1.24% for 12Hz 1.7B
Base. See [upstream hardware and quality references](../ENGINE_COMPARISON.md).

## Start the Server

```sh
git clone https://github.com/balu100/faster-qwen3-tts
cd faster-qwen3-tts
docker compose up
```

For 0.6B, change `Qwen/Qwen3-TTS-12Hz-1.7B-Base` in the Dockerfile to
`Qwen/Qwen3-TTS-12Hz-0.6B-Base`, then rebuild with `docker compose up --build`.
The compatibility `model` field in the game config does not select those weights.
[Selected server repository](https://github.com/balu100/faster-qwen3-tts).

## Register Your Voices

Put each reference recording in the server's `reference_audio/` directory and
add its ID to the server's `voices.json`. Example entry:

```json
{
  "example_narrator": {
    "ref_audio": "reference_audio/example_narrator.wav",
    "ref_text": "The exact words spoken in this reference recording.",
    "language": "English",
    "chunk_size": 8
  }
}
```

Use the transcript of your actual recording, not the literal example sentence.
Restart the server after changing its voice registry. Server-side `chunk_size`
is part of Qwen's registry; do not copy Chatterbox's chunk setting into it.

## Select the Config

Copy [qwen.json](../../configs/qwen.json) as `game/renpy_universal_tts_config.json`.
Replace the example IDs with registered IDs:

```json
"default_voice": "example_narrator",
"voices": {
  "Narrator": "example_narrator",
  "ExampleName1": "example_character"
}
```

The shipped `d01`, `d03`, and `d12` are personal example IDs, not built-in Qwen
voices. An unknown ID may fall back to the server's default voice.

The endpoint is `http://127.0.0.1:8880/v1/audio/speech`. This wrapper streams
24 kHz mono signed 16-bit PCM when `response_format` is `pcm`. Its preset omits
`stream` because that request field is not documented for this wrapper.
The `speed` schema field is not meaningfully implemented in this selected setup.

See [hardware and model-specific AA coverage](../ENGINE_COMPARISON.md), then
return to [game installation](../../README.md#set-it-up).
