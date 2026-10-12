# Compatibility and Test Status

## Runtime Scope

The mod uses desktop Ren'Py's self-voicing hook and external curl/ffplay processes.
It keeps Python 2.7-compatible runtime syntax for Ren'Py 7 and Python 3 syntax
compatibility for Ren'Py 8. Developer tools/tests use Python 3.9 or newer.
Android, iOS, and browser exports are outside this external-process workflow.

The same `.rpy` and JSON are used on Windows and Linux. Windows subprocess windows
are hidden; Linux uses ordinary executable names/paths. This design does not
establish that every TTS backend itself supports both operating systems.

Custom dialogue screens, accessibility hooks, renamed speakers, and existing
TTS mods can affect text/name detection. Install one replacement at a time.

## Checks in This Revision

| Check | Evidence | Limit |
| --- | --- | --- |
| Preset/config validation | Automated, runtime's own validator | Cannot verify remote voice-file existence |
| Legacy configs and profile inheritance | Automated with a Ren'Py stub | No actual engine save/load cycle |
| Rapid replacement / V off / repeated text | Automated state and cancellation tests | Not a game playthrough |
| HTTP streaming and 404 blocking | Real local HTTP + curl, synthetic PCM | Sink process records bytes instead of playing sound |
| Busy 409 retry | Real local HTTP integration | Synthetic server, not GPU cancellation timing |
| Windows process execution | Automated tests plus a live muted Breeze curl/ffplay run, both exit codes 0 | Audible quality and in-game behavior not verified |
| Linux execution | Portable arguments/code reviewed | No Linux host test in this session |
| Ren'Py 7 / 8 game execution | Historical Ren'Py 7.7.3 Windows success reported before this revision | Updated revision needs fresh game tests |
| Breeze protocol | Live saved-clone and text-design requests returned streamed PCM | Single short request per mode; no cloning-fidelity evaluation |

Do not convert protocol support or stub tests into a claim that all games and
GPUs have been tested. See [Development](DEVELOPMENT.md) for manual scenarios.
Single-run timings are recorded in [Engine Comparison](ENGINE_COMPARISON.md#breeze-live-check-2026-10-12).
