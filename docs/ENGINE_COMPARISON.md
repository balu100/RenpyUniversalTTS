# Engine Comparison

Checked on **2026-10-12**. Use the original model and inference project's results
as the starting reference, even when the HTTP server is a fork. A wrapper does
not need its own published benchmark before its underlying model can be compared.
Fork-specific measurements are identified separately below.

## Hardware and Memory

The starting GPU capacities are planning recommendations for TTS alone. The
reference column explains the published evidence behind them; a successful run
on an 8 GB card establishes a working example, not exactly 8 GB consumed.

| Model / Setup | Suggested Starting GPU Capacity | Original Project / Upstream Reference | CPU Option |
| --- | --- | --- | --- |
| Kokoro 82M / Kokoro-FastAPI | GPU optional; budget about 4 GB for the documented GPU setup | Upstream measured 3.11 GB short-request and 3.98 GB long-form usage on RTX 4060 Ti | CPU Docker image available |
| VibeVoice Realtime 0.5B | About 2 GB published footprint; a 4 GB+ GPU leaves more headroom | The upstream wrapper advertises approximately 2 GB VRAM | CPU device option; GPU recommended for responsive playback |
| Qwen3-TTS 12Hz Base 0.6B | 8 GB NVIDIA starting point | Original faster-qwen3-tts benchmarks CUDA-graph streaming on RTX 4060 (8 GB) | The selected CUDA-graph server route uses a GPU |
| Qwen3-TTS 12Hz Base 1.7B | 8 GB NVIDIA starting point; allow additional game headroom | The same original project benchmarks 1.7B on RTX 4060 (8 GB) | The selected CUDA-graph server route uses a GPU |
| Chatterbox Original 500M | 8 GB GPU starting point | Original-project maintainer cites community reports around 6-7 GB, May 2025 | CPU supported by model/server |
| Chatterbox Turbo 350M / Multilingual | 8 GB starting budget for this server; tune by selected variant | Original project describes Turbo as lower-compute/lower-VRAM than Original; Multilingual is a separate variant | CPU server route available |
| Breeze TTS 2 official PyTorch | 12 GB eager; 24 GB full fast path | Official inference reports about 7.7 GiB eager and 14.4 GiB with `--fast-all` | Official route requires NVIDIA CUDA |
| Breeze TTS 2 selected INT8 hybrid server | 8 GB NVIDIA target | Selected server's published target; our local run reserved about 6.2 GB | Selected route requires NVIDIA CUDA |

Sources: [Kokoro measurements](https://github.com/remsky/Kokoro-FastAPI#performance--operations),
[VibeVoice upstream wrapper](https://github.com/marhensa/vibevoice-realtime-openai-api),
[original faster-qwen3-tts benchmarks](https://github.com/andimarafioti/faster-qwen3-tts#results),
[NVIDIA RTX 4060 memory specifications](https://www.nvidia.com/en-us/geforce/news/ultimate-guide-to-4060/),
[original Chatterbox memory discussion](https://github.com/resemble-ai/chatterbox/issues/44),
[Chatterbox model variants](https://github.com/resemble-ai/chatterbox),
[official Breeze requirements](https://github.com/breezeblue-ai/breeze-tts#requirements),
[selected Breeze hybrid server](https://github.com/remominor/breeze-tts-api#requirements).

For **system RAM**, start with **16 GB for the server plus a game**, or **32 GB**
for more headroom with larger games, Docker/WSL, and other applications. These
are project planning recommendations, not claimed official minima. RAM and VRAM
are separate budgets. Add the game's GPU usage to the TTS budget, or run the
server on another computer. Precision, CUDA graphs, context buffers, and cached
voices can change a fork's footprint even when its model weights are unchanged.

## Artificial Analysis Quality

Snapshot checked **2026-10-12**: all-category Provider Voice Open Weights board
and English Controlled Voice board. Values include published 95% intervals.

| Underlying Model | Provider Voice Elo | Controlled Voice Elo | Quality Reference |
| --- | --- | --- | --- |
| Breeze TTS 2 | 1222 +/-15 | 1017 +/-14 | Upstream model score for the Breeze setup |
| Kokoro 82M v1.0 | 1064 +/-11 | - | Upstream model score for Kokoro servers |
| Chatterbox Original | 1026 +/-11 | 933 +/-15 | Upstream Original-model score |
| VibeVoice Realtime 0.5B | - | - | Official WER/speaker-similarity results below |
| Qwen3-TTS 12Hz Base 0.6B / 1.7B | - | - | Official WER/speaker-similarity results below |

Sources: [Provider Voice](https://artificialanalysis.ai/text-to-speech/leaderboard/provider-voice/open-weights),
[Controlled Voice](https://artificialanalysis.ai/text-to-speech/leaderboard/controlled-voice).

Elo measures listener preference. Provider Voice uses provider-offered voices;
Controlled Voice uses common cloned references. The latter is not a percentage
of speaker-identity fidelity. Boards are fitted independently: compare within
a column, not across columns. Scores change over time. Neither measures the
mod's local latency or memory. [AA methodology](https://artificialanalysis.ai/methodology/text-to-speech).

Scores describe the underlying model, not the HTTP wrapper. Using a fork with
the same weights is a reasonable way to use those scores as a quality reference.
Quantization, reference recordings, and sampling settings can affect output.
A dash means no matching entry on these boards. VibeVoice 1.5B, Qwen-Audio hosted
models, and Chatterbox Original must not be relabeled as Realtime 0.5B,
Qwen3-TTS Base, or Chatterbox Turbo.

## Other Original-Model Quality Results

Models without an exact AA entry still have useful published evaluations.

| Exact Model | Benchmark | Word Error Rate (Lower Is Better) | Speaker Similarity (Higher Is Better) |
| --- | --- | --- | --- |
| Qwen3-TTS-12Hz-0.6B-Base | SEED test-en | 1.32% | See separate multilingual benchmark below |
| Qwen3-TTS-12Hz-1.7B-Base | SEED test-en | 1.24% | See separate multilingual benchmark below |
| VibeVoice-Realtime-0.5B | SEED test-en | 2.05% | 0.633 |
| VibeVoice-Realtime-0.5B | LibriSpeech test-clean | 2.00% | 0.695 |

Sources: [Qwen official model-card evaluation](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base#evaluation),
[Microsoft Realtime 0.5B evaluation](https://github.com/microsoft/VibeVoice/blob/main/docs/vibevoice-realtime-0.5b.md#results).

Qwen's **separate multilingual test set, English subset**, reports speaker SIM
**0.829 for 12Hz 0.6B Base** and **0.775 for 12Hz 1.7B Base**. Those values belong
to that test, not to the SEED rows. A larger model does not win every metric.

WER measures whether spoken words match the requested text; SIM measures
speaker-embedding similarity. Neither is a naturalness/listener-preference score
or an AA Elo substitute. Results from different authors may use different
evaluation pipelines, so use them as model evidence rather than one combined
ranking. Listen to each original project's demos when selecting a voice.

## Cloning and Expression

| Setup | Prepare a Voice | Delivery Control |
| --- | --- | --- |
| Kokoro preset | Ready-made voice ID | Voice choice; additional clone-tuning is outside this preset |
| VibeVoice Realtime | Shipped preset or compatible `.pt` file | Ready-made voices; no public cloning workflow in this wrapper |
| Qwen Base | Reference audio + transcript + server `voices.json` | Depends on selected model and wrapper |
| Chatterbox | Predefined file or `reference_audio` filename | Original tuning differs from Turbo |
| Breeze clone | Save reference audio + exact transcript as a server profile | Optional per-character instructions |
| Breeze design | Describe a voice in text | Voice design and delivery instructions |

See the engine guides for language support and registration. Cloning support
alone does not establish reference fidelity. This project has not measured
comparative cloning fidelity; listen to common samples before choosing.
Breeze's locally hosted model/outputs have research and non-commercial terms
separate from the server code. [Model license](https://github.com/remominor/breeze-tts-api/blob/main/MODEL_LICENSE).

## Local Speed

No comparative benchmark series is published yet. The VibeVoice wrapper advertises
about 0.5 RTF on an RTX 3060; that is an upstream result, not a mod measurement.
[Source](https://github.com/marhensa/vibevoice-realtime-openai-api#features).
Record first-audio delay, generation time, output duration, peak RAM/VRAM,
hardware, server revision, and concurrent game load. Separate cold and warm runs.
See [benchmark procedure](DEVELOPMENT.md#benchmark-procedure).

### Breeze Live Check: 2026-10-12

One short request per mode on an NVIDIA RTX 4070 Ti (12,282 MiB reported VRAM),
driver 617.42. The existing server reported an already-loaded hybrid-quantized
model with its fast path enabled. Test text: "Hello. This is a short streaming test."
The client ran on Windows; concurrent game load and server revision were not recorded.

| Mode | First Audio Byte | Full Response | Generated Audio | Client RTF |
| --- | --- | --- | --- | --- |
| Saved cloned reference | 409.2 ms | 1877.0 ms | 2.560 s | 0.733 |
| Text-described voice | 353.8 ms | 2301.6 ms | 2.960 s | 0.778 |

Both responses were HTTP 200, `audio/pcm`, s16le, 24 kHz. These are single-run
checks, not averaged latency benchmarks or listening-quality evaluations.
First byte arrival is earlier than audible onset, which also depends on the player.

After short tests the server reported 3425.7 MB process RSS, 4998 MB allocated
VRAM and 6184 MB reserved VRAM. Those are reported snapshots, not minimum
requirements or measured peaks. A separate muted run through the mod's actual
curl/ffplay pipeline completed with both exit codes 0; game integration still
needs testing. No personal reference audio is included in the public package.
