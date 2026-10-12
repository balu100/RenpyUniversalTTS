# Development

## Project Layout

```text
renpy_universal_tts.rpy          Game integration and playback
renpy_universal_tts_config.json Local user's active config
configs/                       Short engine examples
docs/engines/                   Installation and voice preparation
docs/ENGINE_COMPARISON.md       Sources, hardware, dated quality scores
tools/                         Optional validation and release packaging
tests/                         Runtime and local HTTP tests
```

The game installation remains two files. Configuration, text/speaker handling,
request building, process lifecycle, and Ren'Py hooks are organized inside the
single script so users do not need to install an extra Python package.

## Automated Checks

From this project folder in the source checkout (tests are excluded from the user ZIP):

```sh
python -m unittest discover -s tests -v
python tools/check_config.py configs/breeze.json
```

The tests execute extracted init blocks in a Ren'Py stub and use the runtime's
actual config rules. Integration tests require curl and a temporary local HTTP
server, and replace ffplay with a byte-recording subprocess. No GPU, voice model,
or audio playback is required. See [Compatibility](COMPATIBILITY.md) for limits.

## Manual Game Checks

For a live first-byte timing check with a registered Breeze voice:

```sh
python tools/probe_server.py configs/breeze.json --voice clone:your_saved_id
python tools/probe_server.py configs/breeze_design.json
```

This generates one short sentence, does not play sound or edit the config, and
prints response timing. First-byte delay is not audible onset or voice quality.

Check both Ren'Py 7 and 8 on Windows/Linux before claiming full compatibility:

1. Enable with V, hear the current line, then disable while audio is generating.
2. Advance once and several times rapidly, including just before response completion.
3. Repeat identical dialogue and switch speakers; check all name-reading modes.
4. Save/load/rollback; confirm no old process restarts or stale voice selection.
5. Disconnect the server, use an invalid voice, and restart it; inspect diagnostics.
6. Match each server's raw PCM or encoded stream format; check for noise/gaps.
7. Use clone and predefined profiles together and verify inherited settings.

## Benchmark Procedure

Use the same short dialogue, narration, and expressive passage per engine, and
the same clean reference recording/transcript for cloning. Save the complete
outputs and listen without knowing the engine where practical. Quality notes
should be labeled subjective; clone similarity needs its own evaluation.

Record CPU, GPU, RAM, OS, driver, exact model/checkpoint, quantization, server
revision, config, and concurrent game load. Record cold and warmed-up requests
separately. Measure first audio byte delay and audible onset separately, total
generation time, generated audio duration, peak RAM, and peak VRAM.

RTF = generation time / audio duration; below 1 means generation faster than
playback. First byte timing alone does not measure ffplay/device buffering.
For the selected Breeze server, its built-in `scripts/benchmark_api.py` and
`/metrics` can supply server measurements. Use its documented benchmark options.
[Breeze benchmark procedure](https://github.com/remominor/breeze-tts-api#metrics-and-benchmarking).

## Maintain the Comparison

Use primary sources for hardware and record whether a number is a published
measurement, a target recommendation, or our own measurement. Keep unknowns
visible. Date Artificial Analysis snapshots, preserve exact model variants and
board names, and do not transfer parent-model scores to a quantized fork.

## Build a Public Package

```sh
python tools/package_release.py
```

Creates `dist/renpy-universal-tts.zip` from an explicit allowlist of runtime,
presets, public docs, and the optional config checker. The included active config
is taken from the VibeVoice example; the user's working JSON is not published.
Tests, old local notes, personal launchers, logs, compiled files, references,
and model weights are excluded. Existing local files are preserved.
