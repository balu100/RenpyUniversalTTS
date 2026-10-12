# Chatterbox

Pick the model in your server: Original, Multilingual, or Turbo. The model
variants differ in controls and language support; AA's Original Chatterbox score
does not establish Turbo quality. See [Engine Comparison](../ENGINE_COMPARISON.md).
For Original Chatterbox, a maintainer on the original project's tracker cites
local community reports around 6-7 GB VRAM; 8 GB is a practical starting budget.
[Original-project memory discussion](https://github.com/resemble-ai/chatterbox/issues/44).

## Start a Server

For the current upstream server:

```sh
git clone https://github.com/devnen/Chatterbox-TTS-Server
cd Chatterbox-TTS-Server
docker compose up -d --build
```

This is its default NVIDIA route. CPU users instead run
`docker compose -f docker-compose-cpu.yml up -d --build`. Other GPU generations
and AMD use their own Compose files.
[Hardware-specific installation](https://github.com/devnen/Chatterbox-TTS-Server#using-docker-compose-recommended).

Use the port published by that Compose file. The upstream guide commonly uses
`8004`; this project's older presets use `8880`. Set `chatterbox.url` to the
actual endpoint, for example `http://127.0.0.1:8004/tts`.

## Match the Audio Format

The supplied presets preserve the **PCM-capable server** setup previously used
by this project: `output_format: pcm`, `stream: true`, `split_text: true`, and
`chunk_size: 50`. A server merely accepting `stream` does not guarantee raw PCM.

Current upstream documents native `/tts` streaming as **WAV**. With that server,
change this field in either Chatterbox preset:

```json
"output_format": "wav"
```

With the new short presets, the script infers encoded playback from that format.
If your older config has `audio.raw_pcm`, change it to `false` too. ffplay then
decodes WAV instead of treating its header as PCM samples. Older builds without
streaming can use WAV with `stream: false`.
[Upstream streaming behavior](https://github.com/devnen/Chatterbox-TTS-Server#-v200-highlights-new).

## Predefined and Cloned Voices

Use [chatterbox_predefined.json](../../configs/chatterbox_predefined.json) for
predefined references, or [chatterbox_clone.json](../../configs/chatterbox_clone.json)
for cloning. Rename the chosen file to `game/renpy_universal_tts_config.json`.

Predefined filenames must exist in the server's `voices/` directory. Clone
filenames must exist in its **`reference_audio/` directory**, not the game folder.
The mod sends a filename and does not upload a recording.

```json
"profiles": {
  "ExampleName1": {
    "voice_mode": "clone",
    "reference_audio_filename": "example_reference.wav"
  },
  "ExampleName2": {
    "voice_mode": "predefined",
    "predefined_voice_id": "Emily.wav"
  }
}
```

Every profile inherits all `default_profile` values. A speaker overrides only
the fields it supplies; switching modes removes the other mode's filename from
the API request. The clone example's default `Emily.wav` must also exist in
`reference_audio/`. All named references are examples, not bundled files.

Turbo does not implement all Original tuning controls. Remove unsupported
`temperature`, `exaggeration`, `cfg_weight`, or `speed_factor` fields if the
selected server/model rejects them; consult that server's `/docs`.
Keep `split_text: true` and `chunk_size: 50` as the project's established split
settings, then tune against your server's schema and units.

Return to [game installation](../../README.md#set-it-up).
