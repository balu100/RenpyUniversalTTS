"""Validate a config with the runtime's own rules; no Ren'Py or TTS server needed."""

import argparse
import ast
import difflib
import json
import math
import re
import textwrap
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]


def runtime_namespace(data=None):
    source = (PROJECT / "renpy_universal_tts.rpy").read_text(encoding="utf-8")
    block = re.search(r"^init 999 python:\n(.*?)(?=^init 2000 python:|\Z)", source, re.M | re.S)
    tree = ast.parse(textwrap.dedent(block.group(1)))
    names = {"universal_tts_to_text", "universal_tts_clean_text", "universal_tts_is_mapping", "universal_tts_validate_config",
             "universal_tts_section", "universal_tts_bool", "universal_tts_engine", "universal_tts_request_type",
             "universal_tts_speaker_mapping", "universal_tts_chatterbox_profiles", "universal_tts_lookup_by_speaker",
             "universal_tts_voice_for_speaker", "universal_tts_chatterbox_profile_for_speaker",
             "universal_tts_openai_payload", "universal_tts_chatterbox_payload", "universal_tts_request_payload"}
    definitions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    namespace = {"text_type": str, "string_types": (str,), "math": math, "difflib": difflib, "re": re,
                 "UNIVERSAL_TTS_CONFIG": data or {}}
    exec(compile(ast.Module(body=definitions, type_ignores=[]), str(PROJECT / "renpy_universal_tts.rpy"), "exec"), namespace)
    return namespace


def runtime_validator():
    return runtime_namespace()["universal_tts_validate_config"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, nargs="?", default=PROJECT / "renpy_universal_tts_config.json")
    args = parser.parse_args()
    try:
        data = json.loads(args.config.read_text(encoding="utf-8-sig"))
        errors = runtime_validator()(data)
    except (OSError, ValueError) as exc:
        print("Config could not be read: %s" % exc)
        return 1
    if errors:
        for error in errors:
            print("ERROR: " + error)
        return 1
    print("Valid config: %s" % args.config)
    print("Voice availability and server readiness require a live server check.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
