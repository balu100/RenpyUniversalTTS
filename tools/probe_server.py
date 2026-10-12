"""Make one speech request from a config and report first-byte streaming timing."""

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    from .check_config import runtime_namespace
except ImportError:
    from check_config import runtime_namespace


def probe(data, text, speaker=None):
    namespace = runtime_namespace(data)
    errors = namespace["universal_tts_validate_config"](data)
    if errors:
        raise ValueError("; ".join(errors))
    payload, url, _ = namespace["universal_tts_request_payload"](text, speaker)
    request = urllib.request.Request(url, data=json.dumps(payload, ensure_ascii=True).encode("ascii"),
                                     headers={"Content-Type": "application/json"}, method="POST")
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=data.get("network", {}).get("request_timeout", 120)) as response:
        first = response.read(1)
        first_at = time.perf_counter()
        audio = first + response.read()
        finished = time.perf_counter()
        content_type = response.headers.get("Content-Type", "")
        if not audio or "json" in content_type:
            raise ValueError("Server returned empty or non-audio output")
        result = {"http_status": response.status, "content_type": content_type,
                  "first_audio_byte_ms": round((first_at - started) * 1000, 1),
                  "total_response_ms": round((finished - started) * 1000, 1), "audio_bytes": len(audio),
                  "x_sample_rate": response.headers.get("X-Sample-Rate"),
                  "x_sample_format": response.headers.get("X-Sample-Format")}
    if payload.get("response_format", payload.get("output_format")) == "pcm":
        settings = data.get("audio", {})
        if settings.get("sample_format", "s16le") == "s16le" and settings.get("channel_layout", "mono") == "mono":
            rate = int(result["x_sample_rate"] or settings.get("sample_rate", 24000))
            duration = len(audio) / (2 * rate)
            result["audio_seconds"] = round(duration, 3)
            result["client_rtf"] = round((finished - started) / duration, 3)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--voice", help="Override a voice ID in memory, without editing the config")
    parser.add_argument("--speaker")
    parser.add_argument("--text", default="Hello. This is a short streaming test.")
    args = parser.parse_args()
    try:
        data = json.loads(args.config.read_text(encoding="utf-8-sig"))
        if args.voice:
            if args.speaker:
                profile = data.setdefault("voices", {}).get(args.speaker, {})
                if not isinstance(profile, dict):
                    profile = {}
                profile["voice"] = args.voice
                data["voices"][args.speaker] = profile
            else:
                data["default_voice"] = args.voice
        result = probe(data, args.text, args.speaker)
    except (OSError, ValueError, urllib.error.URLError) as exc:
        print("Probe failed: %s" % exc)
        return 1
    print(json.dumps(result, indent=2))
    print("First byte is not audible onset; this check does not measure cloning quality.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
