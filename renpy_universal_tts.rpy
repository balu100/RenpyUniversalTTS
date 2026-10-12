init -999 python:
    import sys
    renpy.log("UNIVERSAL TTS: renpy_universal_tts.rpy loaded")
    renpy.log("UNIVERSAL TTS: python = %r" % sys.version)


init 999 python:
    import os
    import re
    import json
    import time
    import tempfile
    import subprocess
    import math
    import difflib

    try:
        import threading
    except Exception:
        threading = None

    try:
        text_type = unicode
        string_types = (str, unicode)
    except NameError:
        text_type = str
        string_types = (str,)

    try:
        _universal_tts_state_base = NoRollback
    except NameError:
        _universal_tts_state_base = object

    renpy.log("UNIVERSAL TTS: init block reached")

    UNIVERSAL_TTS_CONFIG_FILENAME = "renpy_universal_tts_config.json"
    UNIVERSAL_TTS_CONFIG = {}
    UNIVERSAL_TTS_CONFIG_PATH = None
    UNIVERSAL_TTS_CONFIG_ERROR = None


    def universal_tts_to_text(value):
        if value is None:
            return u""

        try:
            return text_type(value)
        except Exception:
            try:
                return str(value)
            except Exception:
                return u""


    def universal_tts_clean_text(text):
        text = universal_tts_to_text(text)

        if not text:
            return u""

        text = re.sub(r"\{[^}]*\}", "", text)
        text = text.replace("[", "").replace("]", "")
        text = re.sub(r"\s+", " ", text)

        return text.strip()


    def universal_tts_debug(message):
        message = universal_tts_to_text(message)

        try:
            renpy.log(message)
        except Exception:
            pass

        try:
            base = getattr(config, "gamedir", None) or os.getcwd()
            path = os.path.join(base, "renpy_universal_tts_debug.log")
            line = time.strftime("%Y-%m-%d %H:%M:%S") + " " + message + "\n"

            try:
                data = line.encode("utf-8")
            except Exception:
                data = str(line)

            handle = open(path, "ab")

            try:
                handle.write(data)
            finally:
                handle.close()
        except Exception:
            pass


    def universal_tts_add_unique_path(paths, path):
        if not path:
            return

        try:
            path = os.path.abspath(os.path.normpath(path))
        except Exception:
            pass

        if path not in paths:
            paths.append(path)


    def universal_tts_candidate_config_paths():
        paths = []
        module_file = globals().get("__file__", None)
        gamedir = getattr(config, "gamedir", None)
        basedir = getattr(config, "basedir", None)

        if module_file:
            universal_tts_add_unique_path(paths, os.path.join(os.path.dirname(module_file), UNIVERSAL_TTS_CONFIG_FILENAME))

        if gamedir:
            universal_tts_add_unique_path(paths, os.path.join(gamedir, UNIVERSAL_TTS_CONFIG_FILENAME))
            universal_tts_add_unique_path(paths, os.path.join(gamedir, "renpyuniversaltts", UNIVERSAL_TTS_CONFIG_FILENAME))

        if basedir:
            universal_tts_add_unique_path(paths, os.path.join(basedir, "game", UNIVERSAL_TTS_CONFIG_FILENAME))
            universal_tts_add_unique_path(paths, os.path.join(basedir, "game", "renpyuniversaltts", UNIVERSAL_TTS_CONFIG_FILENAME))

        if not gamedir and not basedir:
            universal_tts_add_unique_path(paths, os.path.join(os.getcwd(), UNIVERSAL_TTS_CONFIG_FILENAME))
            universal_tts_add_unique_path(paths, os.path.join(os.getcwd(), "renpyuniversaltts", UNIVERSAL_TTS_CONFIG_FILENAME))

        return paths


    def universal_tts_read_json(path):
        handle = open(path, "rb")

        try:
            raw = handle.read()
        finally:
            handle.close()

        if not raw:
            raise ValueError("config file is empty")

        if raw.startswith(b"\xef\xbb\xbf"):
            raw = raw[3:]

        if not isinstance(raw, text_type):
            raw = raw.decode("utf-8")

        return json.loads(raw)


    def universal_tts_is_mapping(value):
        return hasattr(value, "get") and hasattr(value, "keys")


    def universal_tts_validate_config(data):
        errors = []

        def object_at(value, path):
            if not universal_tts_is_mapping(value):
                errors.append(path + " must be a JSON object")
                return {}
            return value

        def known_keys(value, allowed, path):
            for key in value.keys():
                if key not in allowed:
                    suggestion = difflib.get_close_matches(key, allowed, n=1)
                    hint = "; did you mean " + suggestion[0] + "?" if suggestion else ""
                    errors.append(path + "." + key + " is unknown" + hint)

        def nonempty(value, path):
            if not isinstance(value, string_types) or not value.strip():
                errors.append(path + " must be a non-empty string")

        def boolean(value, path):
            if value is not True and value is not False:
                errors.append(path + " must be true or false")

        def number(value, path, minimum=None, integer=False):
            try:
                converted = float(value)
                valid = not isinstance(value, (bool,) + string_types) and not math.isnan(converted) and not math.isinf(converted)
                valid = valid and (minimum is None or converted >= minimum)
                valid = valid and (not integer or converted == int(converted))
            except (TypeError, ValueError, OverflowError):
                valid = False
            if not valid:
                errors.append(path + " must be a valid " + ("integer" if integer else "number") + (" >= " + str(minimum) if minimum is not None else ""))

        def extras(value, path):
            value = object_at(value, path)
            for key in ("input", "voice", "model", "response_format"):
                if key in value:
                    errors.append(path + "." + key + " must be set in its dedicated config field")
            if value.get("stream_format") == "sse":
                errors.append(path + ".stream_format must be audio; ffplay cannot decode SSE events")
            return value

        data = object_at(data, "config")
        known_keys(data, ("enabled", "engine", "speaker_name_mode", "tools", "audio", "network", "request", "request_type", "openai", "chatterbox", "default_voice", "voices"), "config")
        if "enabled" in data:
            boolean(data["enabled"], "enabled")
        if data.get("enabled") is False:
            return errors
        mode = data.get("speaker_name_mode", "on_speaker_change")
        valid_modes = ("true", "yes", "always", "on", "false", "no", "never", "off", "on speaker change", "on speaker changes", "on speaker changed", "on speakerchange", "onspeakerchange", "speaker change", "speaker changes", "when speaker changes", "when the speaker changes", "when it changes", "when changes", "on change", "change", "changes")
        if mode is not None and not isinstance(mode, bool) and universal_tts_to_text(mode).lower().replace("_", " ").replace("-", " ") not in valid_modes:
            errors.append("speaker_name_mode must be always, never, or on_speaker_change")

        request = object_at(data.get("request", {}), "request")
        known_keys(request, ("type",), "request")
        request_type = request.get("type", data.get("request_type", "chatterbox_tts" if data.get("engine") == "chatterbox" else "openai"))
        request_type = universal_tts_to_text(request_type).strip().lower().replace("-", "_").replace(" ", "_")
        if request_type not in ("openai", "openai_tts", "chatterbox", "chatterbox_tts", "tts"):
            errors.append("request.type must be openai or chatterbox_tts")

        audio = object_at(data.get("audio", {}), "audio")
        known_keys(audio, ("raw_pcm", "sample_format", "sample_rate", "channel_layout"), "audio")
        if "raw_pcm" in audio:
            boolean(audio["raw_pcm"], "audio.raw_pcm")
        if "sample_rate" in audio:
            number(audio["sample_rate"], "audio.sample_rate", 1, True)
        for key in ("sample_format", "channel_layout"):
            if key in audio:
                nonempty(audio[key], "audio." + key)

        tools = object_at(data.get("tools", {}), "tools")
        known_keys(tools, ("curl_path", "ffplay_path", "ffplay_loglevel", "ffplay_channel_option", "ffplay_volume", "ffplay_extra_args"), "tools")
        for key in ("curl_path", "ffplay_path"):
            if key in tools:
                nonempty(tools[key], "tools." + key)
        if tools.get("ffplay_volume") is not None:
            number(tools["ffplay_volume"], "tools.ffplay_volume", 0, True)
            if isinstance(tools["ffplay_volume"], (int, float)) and tools["ffplay_volume"] > 100:
                errors.append("tools.ffplay_volume must be between 0 and 100")
        if "ffplay_extra_args" in tools and (not isinstance(tools["ffplay_extra_args"], (list, tuple)) or not all(isinstance(arg, string_types) for arg in tools["ffplay_extra_args"])):
            errors.append("tools.ffplay_extra_args must be an array of strings")

        network = object_at(data.get("network", {}), "network")
        known_keys(network, ("connect_timeout", "request_timeout", "busy_retry_seconds"), "network")
        for key in ("connect_timeout", "request_timeout", "busy_retry_seconds"):
            if key in network:
                number(network[key], "network." + key, 0 if key == "busy_retry_seconds" else 0.1)

        native = request_type in ("chatterbox", "chatterbox_tts", "tts")
        if native:
            section = object_at(data.get("chatterbox", {}), "chatterbox")
            known_keys(section, ("url", "output_format", "stream", "split_text", "chunk_size", "language", "default_profile", "profiles"), "chatterbox")
            default = object_at(section.get("default_profile", {}), "chatterbox.default_profile")
            profiles = object_at(section.get("profiles", {}), "chatterbox.profiles")
            allowed_profile = ("voice_mode", "predefined_voice_id", "reference_audio_filename", "temperature", "exaggeration", "cfg_weight", "seed", "speed_factor", "language", "stream", "split_text", "chunk_size")
            for name, profile in [(None, default)] + list(profiles.items()):
                path = "chatterbox.default_profile" if name is None else "chatterbox.profiles." + universal_tts_to_text(name)
                if name is not None:
                    nonempty(name, path + " speaker name")
                if isinstance(profile, string_types):
                    profile = {"voice_mode": "predefined", "predefined_voice_id": profile}
                profile = object_at(profile, path)
                known_keys(profile, allowed_profile, path)
                merged = dict(default)
                merged.update(profile)
                mode = merged.get("voice_mode", "predefined")
                if mode not in ("clone", "predefined"):
                    errors.append(path + ".voice_mode must be clone or predefined")
                else:
                    key = "reference_audio_filename" if mode == "clone" else "predefined_voice_id"
                    nonempty(merged.get(key), path + "." + key)
                for key in ("temperature", "exaggeration", "cfg_weight", "speed_factor", "seed", "chunk_size"):
                    if key in merged:
                        number(merged[key], path + "." + key, 0.01 if key in ("speed_factor", "chunk_size") else None, key in ("seed", "chunk_size"))
                for key in ("stream", "split_text"):
                    if key in merged:
                        boolean(merged[key], path + "." + key)
            for key in ("stream", "split_text"):
                if key in section:
                    boolean(section[key], "chatterbox." + key)
            if "chunk_size" in section:
                number(section["chunk_size"], "chatterbox.chunk_size", 1, True)
            format_name = section.get("output_format", "pcm")
        else:
            section = object_at(data.get("openai", {}), "openai")
            known_keys(section, ("url", "model", "response_format", "stream", "speed", "extra_body"), "openai")
            nonempty(section.get("model"), "openai.model")
            global_extra = extras(section.get("extra_body", {}), "openai.extra_body")
            if "stream" in section:
                boolean(section["stream"], "openai.stream")
            if section.get("speed") is not None:
                number(section["speed"], "openai.speed", 0.01)
            profiles = object_at(data.get("voices", {}), "voices")
            entries = [(None, data.get("default_voice"))] + list(profiles.items())
            for name, profile in entries:
                path = "default_voice" if name is None else "voices." + universal_tts_to_text(name)
                if name is not None:
                    nonempty(name, path + " speaker name")
                extra = dict(global_extra)
                if universal_tts_is_mapping(profile):
                    known_keys(profile, ("voice", "extra_body"), path)
                    extra.update(extras(profile.get("extra_body", {}), path + ".extra_body"))
                    voice = profile.get("voice", data.get("default_voice"))
                else:
                    voice = profile
                if voice is not None:
                    nonempty(voice, path + ".voice" if universal_tts_is_mapping(profile) else path)
                elif not isinstance(extra.get("instructions"), string_types) or not extra["instructions"].strip():
                    errors.append(path + " needs a voice ID or extra_body.instructions for voice design")
            format_name = section.get("response_format", "pcm")

        url = section.get("url", "")
        if not isinstance(url, string_types) or not re.match(r"^https?://[^/\s]+", url):
            errors.append(("chatterbox" if native else "openai") + ".url must be an http:// or https:// endpoint")
        if format_name not in ("pcm", "wav", "mp3", "opus", "aac", "flac"):
            errors.append("audio response format is unsupported")
        if "raw_pcm" in audio and audio["raw_pcm"] != (format_name == "pcm"):
            errors.append("audio.raw_pcm must be true for pcm and false for encoded audio")
        return errors


    def universal_tts_load_config():
        global UNIVERSAL_TTS_CONFIG
        global UNIVERSAL_TTS_CONFIG_PATH
        global UNIVERSAL_TTS_CONFIG_ERROR

        paths = universal_tts_candidate_config_paths()
        universal_tts_debug("UNIVERSAL TTS: config search paths | %r" % paths)

        for path in paths:
            try:
                if not os.path.exists(path):
                    continue
            except Exception:
                continue

            try:
                data = universal_tts_read_json(path)
            except Exception as e:
                UNIVERSAL_TTS_CONFIG = {}
                UNIVERSAL_TTS_CONFIG_PATH = path
                UNIVERSAL_TTS_CONFIG_ERROR = "failed to read config: %r" % e
                universal_tts_debug("UNIVERSAL TTS ERROR: %s | path=%r" % (UNIVERSAL_TTS_CONFIG_ERROR, path))
                return

            if not universal_tts_is_mapping(data):
                UNIVERSAL_TTS_CONFIG = {}
                UNIVERSAL_TTS_CONFIG_PATH = path
                UNIVERSAL_TTS_CONFIG_ERROR = "config root must be a JSON object, got %r" % type(data)
                universal_tts_debug("UNIVERSAL TTS ERROR: %s | path=%r" % (UNIVERSAL_TTS_CONFIG_ERROR, path))
                return

            UNIVERSAL_TTS_CONFIG = data
            UNIVERSAL_TTS_CONFIG_PATH = path
            errors = universal_tts_validate_config(data)
            if errors:
                UNIVERSAL_TTS_CONFIG_ERROR = "; ".join(errors)
                universal_tts_debug("UNIVERSAL TTS ERROR: invalid config | %s" % UNIVERSAL_TTS_CONFIG_ERROR)
                return
            UNIVERSAL_TTS_CONFIG_ERROR = None
            universal_tts_debug("UNIVERSAL TTS: config loaded | path=%r" % path)
            return

        UNIVERSAL_TTS_CONFIG = {}
        UNIVERSAL_TTS_CONFIG_PATH = None
        UNIVERSAL_TTS_CONFIG_ERROR = "missing %s" % UNIVERSAL_TTS_CONFIG_FILENAME
        universal_tts_debug("UNIVERSAL TTS ERROR: %s | searched=%r" % (
            UNIVERSAL_TTS_CONFIG_ERROR,
            paths,
        ))


    def universal_tts_section(name):
        value = UNIVERSAL_TTS_CONFIG.get(name, {})

        if universal_tts_is_mapping(value):
            return value

        return {}


    def universal_tts_bool(value, default=False):
        if value is None:
            return default

        if value is True or value is False:
            return value

        text = universal_tts_clean_text(value).lower()

        if text in ("true", "yes", "1", "on", "enabled"):
            return True

        if text in ("false", "no", "0", "off", "disabled"):
            return False

        return default


    def universal_tts_integer(value, default=None):
        if value is None:
            return default

        try:
            return int(value)
        except Exception:
            return default


    def universal_tts_configured():
        return UNIVERSAL_TTS_CONFIG_ERROR is None and universal_tts_is_mapping(UNIVERSAL_TTS_CONFIG) and bool(UNIVERSAL_TTS_CONFIG)


    def universal_tts_enabled():
        if not universal_tts_configured():
            return False

        return universal_tts_bool(UNIVERSAL_TTS_CONFIG.get("enabled", True), True)


    def universal_tts_engine():
        return universal_tts_clean_text(UNIVERSAL_TTS_CONFIG.get("engine", "")).lower().replace("-", "_").replace(" ", "_")


    def universal_tts_request_type():
        request = universal_tts_section("request")
        request_type = universal_tts_clean_text(request.get("type", ""))

        if not request_type:
            request_type = universal_tts_clean_text(UNIVERSAL_TTS_CONFIG.get("request_type", ""))

        if request_type:
            return request_type.lower().replace("-", "_").replace(" ", "_")

        if universal_tts_engine() == "chatterbox":
            return "chatterbox_tts"

        return "openai"


    universal_tts_load_config()

    universal_tts_debug("UNIVERSAL TTS: config summary | path=%r | error=%r | enabled=%r | engine=%r | request_type=%r" % (
        UNIVERSAL_TTS_CONFIG_PATH,
        UNIVERSAL_TTS_CONFIG_ERROR,
        UNIVERSAL_TTS_CONFIG.get("enabled", None) if universal_tts_is_mapping(UNIVERSAL_TTS_CONFIG) else None,
        UNIVERSAL_TTS_CONFIG.get("engine", None) if universal_tts_is_mapping(UNIVERSAL_TTS_CONFIG) else None,
        universal_tts_request_type(),
    ))


    class UniversalTTSState(_universal_tts_state_base):
        def __init__(self):
            self.worker_started = False
            self.request_id = 0
            self.active_id = 0
            self.pending = None
            self.last_speech_mode = None
            self.last_self_voicing_mode = None
            self.last_spoken_speaker = None
            self.pending_speaker = None
            self.process = None
            self.request_file = None
            self.error_notified = False

            if threading is not None:
                self.lock = threading.RLock()
                self.condition = threading.Condition(self.lock)
            else:
                self.lock = None
                self.condition = None


    _universal_tts_state = UniversalTTSState()


    def universal_tts_self_voicing_mode():
        try:
            return renpy.game.preferences.self_voicing
        except Exception:
            return False


    def universal_tts_speech_mode_active():
        mode = universal_tts_self_voicing_mode()

        if mode is True or mode == True:
            return True

        mode_text = universal_tts_clean_text(mode).lower().replace("_", " ").replace("-", " ")

        return mode_text in (
            "speech",
            "tts",
            "text to speech",
            "self voicing",
            "selfvoicing",
            "voice",
            "true",
            "yes",
            "on",
        )


    def universal_tts_speaker_mapping():
        voices = UNIVERSAL_TTS_CONFIG.get("voices", {})

        if universal_tts_is_mapping(voices):
            return voices

        return {}


    def universal_tts_chatterbox_profiles():
        chatterbox = universal_tts_section("chatterbox")
        profiles = chatterbox.get("profiles", {})

        if universal_tts_is_mapping(profiles):
            return profiles

        return {}


    def universal_tts_sorted_speakers():
        speakers = []

        for mapping in (universal_tts_speaker_mapping(), universal_tts_chatterbox_profiles()):
            try:
                names = mapping.keys()
            except Exception:
                names = []

            for speaker in names:
                name = universal_tts_clean_text(speaker)

                if name and name not in speakers:
                    speakers.append(name)

        return sorted(speakers, key=len, reverse=True)


    def universal_tts_name_read_mode():
        mode = UNIVERSAL_TTS_CONFIG.get("speaker_name_mode", "on_speaker_change")

        if mode is True:
            return "always"

        if mode is False or mode is None:
            return "never"

        mode_text = universal_tts_clean_text(mode).lower().replace("_", " ").replace("-", " ")

        if mode_text in ("true", "yes", "always", "on"):
            return "always"

        if mode_text in ("false", "no", "never", "off"):
            return "never"

        if mode_text in (
            "on speaker change",
            "on speaker changes",
            "on speaker changed",
            "on speakerchange",
            "onspeakerchange",
            "speaker change",
            "speaker changes",
            "when speaker changes",
            "when the speaker changes",
            "when it changes",
            "when changes",
            "on change",
            "change",
            "changes",
        ):
            return "change"

        renpy.log("UNIVERSAL TTS: unknown speaker_name_mode value %r, using 'on_speaker_change'" % mode)
        return "change"


    def universal_tts_known_speaker_match(clean):
        for speaker in universal_tts_sorted_speakers():
            if clean == speaker:
                return speaker, u""

            if not clean.startswith(speaker):
                continue

            rest = clean[len(speaker):]
            stripped = rest.lstrip()

            if not stripped:
                continue

            if stripped[0] in (":", ".", "-"):
                return speaker, universal_tts_clean_text(stripped[1:])

            if rest.startswith(" "):
                return speaker, universal_tts_clean_text(rest)

        return None, clean


    def universal_tts_unknown_speaker_match(clean):
        match = re.match(r"^([^:]{1,40}):\s+(.+)$", clean)

        if match:
            speaker = universal_tts_clean_text(match.group(1))
            body = universal_tts_clean_text(match.group(2))

            if speaker and body:
                return speaker, body

        match = re.match(r"^(.{1,40}?)\s+-\s+(.+)$", clean)

        if match:
            speaker = universal_tts_clean_text(match.group(1))
            body = universal_tts_clean_text(match.group(2))

            if speaker and body:
                return speaker, body

        return None, clean


    def universal_tts_split_speaker_text(text):
        clean = universal_tts_clean_text(text)

        if not clean:
            return None, u""

        speaker, body = universal_tts_known_speaker_match(clean)

        if speaker is not None:
            return speaker, body

        return universal_tts_unknown_speaker_match(clean)


    def universal_tts_apply_name_policy(speaker, body):
        state = _universal_tts_state
        mode = universal_tts_name_read_mode()
        read_name = False

        if mode == "always":
            read_name = True
        elif mode == "change":
            read_name = speaker != state.last_spoken_speaker

        state.last_spoken_speaker = speaker

        if read_name:
            if body:
                speech_text = speaker + ". " + body
            else:
                speech_text = speaker
        else:
            speech_text = body

        return universal_tts_clean_text(speech_text), speaker


    def universal_tts_prepare_text_and_speaker(text):
        state = _universal_tts_state
        clean = universal_tts_clean_text(text)
        speaker, body = universal_tts_split_speaker_text(clean)

        if speaker is not None:
            if not body:
                state.pending_speaker = speaker
                return u"", speaker

            state.pending_speaker = None
            return universal_tts_apply_name_policy(speaker, body)

        if state.pending_speaker is not None:
            speaker = state.pending_speaker
            state.pending_speaker = None
            return universal_tts_apply_name_policy(speaker, clean)

        state.last_spoken_speaker = None
        return clean, None


    def universal_tts_lookup_by_speaker(mapping, speaker):
        if not universal_tts_is_mapping(mapping):
            return None

        if speaker and speaker in mapping:
            return mapping.get(speaker)

        if speaker:
            for speaker_name, value in mapping.items():
                if universal_tts_clean_text(speaker_name) == speaker:
                    return value

        return None


    def universal_tts_voice_for_speaker(speaker):
        voice = universal_tts_lookup_by_speaker(universal_tts_speaker_mapping(), speaker)

        if voice is not None:
            return voice

        return UNIVERSAL_TTS_CONFIG.get("default_voice", None)


    def universal_tts_chatterbox_profile_for_speaker(speaker):
        chatterbox = universal_tts_section("chatterbox")
        default_profile = chatterbox.get("default_profile", {})
        profile = universal_tts_lookup_by_speaker(universal_tts_chatterbox_profiles(), speaker)
        merged = {}

        if universal_tts_is_mapping(default_profile):
            merged.update(default_profile)

        if universal_tts_is_mapping(profile):
            merged.update(profile)
        elif isinstance(profile, text_type):
            merged["voice_mode"] = "predefined"
            merged["predefined_voice_id"] = profile

        return merged


    def universal_tts_possible_executable_paths(configured, fallback):
        configured = universal_tts_to_text(configured).strip()

        if not configured:
            configured = fallback

        names = [configured]

        if os.name == "nt" and not configured.lower().endswith(".exe"):
            names.append(configured + ".exe")

        bases = []
        candidates = []
        gamedir = getattr(config, "gamedir", None)
        basedir = getattr(config, "basedir", None)
        module_file = globals().get("__file__", None)

        if module_file:
            universal_tts_add_unique_path(bases, os.path.dirname(module_file))

        for base in (gamedir, basedir):
            universal_tts_add_unique_path(bases, base)

            if base:
                universal_tts_add_unique_path(bases, os.path.join(base, "renpyuniversaltts"))
                universal_tts_add_unique_path(bases, os.path.join(base, "game", "renpyuniversaltts"))

        for base in bases:
            if not base:
                continue

            for name in names:
                if os.path.isabs(name) or os.sep in name or "/" in name:
                    candidates.append(name)
                else:
                    candidates.append(os.path.join(base, name))

        candidates.extend(names)

        return candidates


    def universal_tts_find_existing_path(candidates):
        for candidate in candidates:
            try:
                if os.path.exists(candidate):
                    return candidate
            except Exception:
                pass

        return candidates[-1]


    def universal_tts_tools():
        return universal_tts_section("tools")


    def universal_tts_audio():
        return universal_tts_section("audio")


    def universal_tts_find_curl_path():
        tools = universal_tts_tools()
        return universal_tts_find_existing_path(universal_tts_possible_executable_paths(tools.get("curl_path", "curl"), "curl"))


    def universal_tts_find_ffplay_path():
        tools = universal_tts_tools()
        return universal_tts_find_existing_path(universal_tts_possible_executable_paths(tools.get("ffplay_path", "ffplay"), "ffplay"))


    def universal_tts_subprocess_kwargs():
        kwargs = {}

        if os.name == "nt":
            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0
                kwargs["startupinfo"] = startupinfo
            except Exception:
                pass

            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

            if creationflags:
                kwargs["creationflags"] = creationflags

        return kwargs


    def universal_tts_raw_pcm_enabled():
        audio = universal_tts_audio()
        if "raw_pcm" in audio:
            return universal_tts_bool(audio.get("raw_pcm"), False)
        native = universal_tts_request_type() in ("chatterbox", "chatterbox_tts", "tts")
        section = universal_tts_section("chatterbox" if native else "openai")
        return section.get("output_format" if native else "response_format", "pcm") == "pcm"


    def universal_tts_ffplay_command():
        tools = universal_tts_tools()
        audio = universal_tts_audio()
        command = [
            universal_tts_find_ffplay_path(),
            "-nodisp",
            "-autoexit",
            "-loglevel",
            universal_tts_clean_text(tools.get("ffplay_loglevel", "error")) or "error",
        ]

        if universal_tts_raw_pcm_enabled():
            sample_format = universal_tts_clean_text(audio.get("sample_format", "s16le")) or "s16le"
            sample_rate = universal_tts_integer(audio.get("sample_rate", 24000), 24000)
            channel_layout = universal_tts_clean_text(audio.get("channel_layout", "mono")) or "mono"

            command.extend([
                "-f",
                sample_format,
                "-sample_rate",
                str(sample_rate),
            ])

            channel_option = universal_tts_clean_text(tools.get("ffplay_channel_option", "ch_layout")).lower()

            if channel_option in ("ac", "channels", "legacy"):
                command.extend(["-ac", "1" if channel_layout == "mono" else channel_layout])
            else:
                command.extend(["-ch_layout", channel_layout])

        if tools.get("ffplay_volume", None) is not None:
            command.extend(["-volume", str(universal_tts_integer(tools.get("ffplay_volume"), 100))])

        extra_args = tools.get("ffplay_extra_args", [])

        if isinstance(extra_args, (list, tuple)):
            for arg in extra_args:
                command.append(universal_tts_to_text(arg))

        command.extend(["-i", "-"])

        return command


    def universal_tts_openai_payload(text, speaker):
        openai = universal_tts_section("openai")
        url = universal_tts_to_text(openai.get("url", "")).strip()
        model = openai.get("model", None)
        profile = universal_tts_voice_for_speaker(speaker)
        voice = profile.get("voice", UNIVERSAL_TTS_CONFIG.get("default_voice")) if universal_tts_is_mapping(profile) else profile
        response_format = openai.get("response_format", "pcm")

        if not url:
            raise ValueError("openai.url is missing")

        if model is None:
            raise ValueError("openai.model is missing")

        if response_format is None:
            raise ValueError("openai.response_format is missing")

        payload = {
            "model": model,
            "input": text,
            "response_format": response_format,
        }

        if voice is not None:
            payload["voice"] = voice

        if "stream" in openai:
            payload["stream"] = universal_tts_bool(openai.get("stream"), False)

        if openai.get("speed", None) is not None:
            payload["speed"] = openai.get("speed")

        extra_body = openai.get("extra_body", {})

        if universal_tts_is_mapping(extra_body):
            for key, value in extra_body.items():
                payload[key] = value

        if universal_tts_is_mapping(profile):
            for key, value in profile.get("extra_body", {}).items():
                payload[key] = value

        if voice is None and not payload.get("instructions"):
            raise ValueError("voice design needs extra_body.instructions")

        return payload, url, "openai voice=%r" % voice


    def universal_tts_chatterbox_payload(text, speaker):
        chatterbox = universal_tts_section("chatterbox")
        url = universal_tts_to_text(chatterbox.get("url", "")).strip()
        profile = universal_tts_chatterbox_profile_for_speaker(speaker)

        if not url:
            raise ValueError("chatterbox.url is missing")

        if not profile:
            raise ValueError("chatterbox.default_profile is missing")

        voice_mode = universal_tts_clean_text(profile.get("voice_mode", "predefined")).lower()

        if not voice_mode:
            voice_mode = "predefined"

        payload = {
            "text": text,
            "voice_mode": voice_mode,
        }

        payload["output_format"] = chatterbox.get("output_format", "pcm")

        for key in ("stream", "split_text", "chunk_size", "language"):
            if key in chatterbox:
                if key == "stream":
                    payload[key] = universal_tts_bool(chatterbox.get(key), False)
                else:
                    payload[key] = chatterbox.get(key)

        for key in (
            "predefined_voice_id",
            "reference_audio_filename",
            "temperature",
            "exaggeration",
            "cfg_weight",
            "seed",
            "speed_factor",
            "language",
            "stream",
            "split_text",
            "chunk_size",
        ):
            if key in profile:
                if key == "stream":
                    payload[key] = universal_tts_bool(profile.get(key), False)
                else:
                    payload[key] = profile.get(key)

        if voice_mode == "clone" and not payload.get("reference_audio_filename", None):
            raise ValueError("chatterbox clone profile is missing reference_audio_filename")

        if voice_mode == "predefined" and not payload.get("predefined_voice_id", None):
            raise ValueError("chatterbox predefined profile is missing predefined_voice_id")

        if voice_mode == "clone":
            payload.pop("predefined_voice_id", None)
        elif voice_mode == "predefined":
            payload.pop("reference_audio_filename", None)

        return payload, url, "chatterbox speaker=%r voice_mode=%r" % (speaker, voice_mode)


    def universal_tts_request_payload(text, speaker):
        request_type = universal_tts_request_type()

        if request_type in ("chatterbox", "chatterbox_tts", "tts"):
            return universal_tts_chatterbox_payload(text, speaker)

        return universal_tts_openai_payload(text, speaker)


    def universal_tts_write_request_file(text, speaker):
        payload, url, descriptor = universal_tts_request_payload(text, speaker)
        data = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("ascii")
        handle = tempfile.NamedTemporaryFile(prefix="renpy_universal_tts_", suffix=".json", delete=False)

        try:
            handle.write(data)
            return handle.name, url, descriptor
        finally:
            handle.close()


    def universal_tts_delete_request_file(path):
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            pass


    def universal_tts_curl_command(request_file, url):
        network = universal_tts_section("network")
        return [
            universal_tts_find_curl_path(),
            "--fail",
            "--silent",
            "--show-error",
            "--no-buffer",
            "--location",
            "--max-redirs", "3",
            "--connect-timeout", str(network.get("connect_timeout", 5)),
            "--max-time", str(network.get("request_timeout", 120)),
            "--header", "Content-Type: application/json",
            "--data-binary",
            "@" + request_file,
            url,
        ]


    def universal_tts_close_quietly(value):
        try:
            if value is not None:
                value.close()
        except Exception:
            pass


    def universal_tts_terminate_process(process):
        if process is None:
            return

        curl_process = getattr(process, "_universal_tts_curl_process", None)

        if curl_process is not None:
            universal_tts_terminate_process(curl_process)

        try:
            if process.poll() is None:
                process.terminate()
        except Exception:
            try:
                process.kill()
            except Exception:
                pass


    def universal_tts_request_is_active(request_id):
        state = _universal_tts_state

        if state.condition is not None:
            with state.condition:
                return request_id == state.active_id

        return request_id == state.active_id


    def universal_tts_set_current_process(request_id, process, request_file):
        state = _universal_tts_state

        if state.condition is not None:
            with state.condition:
                if request_id != state.active_id:
                    return False

                state.process = process
                state.request_file = request_file
                return True

        if request_id != state.active_id:
            return False

        state.process = process
        state.request_file = request_file
        return True


    def universal_tts_clear_current_process(request_id, process):
        state = _universal_tts_state

        if state.condition is not None:
            with state.condition:
                if request_id == state.active_id and state.process is process:
                    state.process = None
                    state.request_file = None
            return

        if request_id == state.active_id and state.process is process:
            state.process = None
            state.request_file = None


    def universal_tts_take_current_process():
        state = _universal_tts_state

        if state.condition is not None:
            with state.condition:
                process = state.process
                request_file = state.request_file
                state.process = None
                state.request_file = None
                return process, request_file

        process = state.process
        request_file = state.request_file
        state.process = None
        state.request_file = None
        return process, request_file


    def universal_tts_start_pipeline(request_file, url):
        curl_command = universal_tts_curl_command(request_file, url)
        ffplay_command = universal_tts_ffplay_command()
        devnull = open(os.devnull, "wb")
        curl_errors = tempfile.TemporaryFile(mode="w+b")
        player_errors = tempfile.TemporaryFile(mode="w+b")
        headers = tempfile.NamedTemporaryFile(prefix="renpy_universal_tts_headers_", delete=False)
        headers_path = headers.name
        headers.close()
        curl_command.extend(["--dump-header", headers_path])
        curl_process = None

        kwargs = {
            "bufsize": 0,
        }
        kwargs.update(universal_tts_subprocess_kwargs())

        try:
            curl_process = subprocess.Popen(
                curl_command,
                stdin=devnull,
                stdout=subprocess.PIPE,
                stderr=curl_errors,
                **kwargs
            )
            ffplay_process = subprocess.Popen(
                ffplay_command,
                stdin=curl_process.stdout,
                stdout=devnull,
                stderr=player_errors,
                **kwargs
            )
            universal_tts_close_quietly(curl_process.stdout)
            ffplay_process._universal_tts_curl_process = curl_process
            ffplay_process._universal_tts_devnull = devnull
            ffplay_process._universal_tts_curl_errors = curl_errors
            ffplay_process._universal_tts_player_errors = player_errors
            ffplay_process._universal_tts_headers_path = headers_path
            universal_tts_debug("UNIVERSAL TTS: pipe started | curl=%r | ffplay=%r" % (
                curl_command,
                ffplay_command,
            ))
            return ffplay_process
        except Exception as e:
            universal_tts_debug("UNIVERSAL TTS ERROR: failed to start pipe | curl=%r | ffplay=%r | error=%r" % (
                curl_command,
                ffplay_command,
                e,
            ))

            if curl_process is not None:
                universal_tts_terminate_process(curl_process)
                universal_tts_reap_process(curl_process)

            universal_tts_close_quietly(devnull)
            universal_tts_close_quietly(curl_errors)
            universal_tts_close_quietly(player_errors)
            universal_tts_delete_request_file(headers_path)
            raise


    def universal_tts_pipeline_status(process):
        path = getattr(process, "_universal_tts_headers_path", None)
        try:
            handle = open(path, "rb")
            try:
                headers = handle.read().decode("latin-1")
            finally:
                handle.close()
            statuses = re.findall(r"(?m)^HTTP/\S+\s+(\d+)", headers)
            return int(statuses[-1]) if statuses else None
        except Exception:
            return None


    def universal_tts_reap_process(process):
        if process is None:
            return
        deadline = time.time() + 0.5
        while process.poll() is None and time.time() < deadline:
            time.sleep(0.01)
        if process.poll() is None:
            try:
                process.kill()
            except Exception:
                pass
            deadline = time.time() + 0.5
            while process.poll() is None and time.time() < deadline:
                time.sleep(0.01)


    def universal_tts_report_pipeline(process):
        curl_process = getattr(process, "_universal_tts_curl_process", None)
        curl_code = curl_process.poll() if curl_process is not None else None
        player_code = process.poll()
        status = universal_tts_pipeline_status(process)
        failed = curl_code not in (None, 0) or player_code not in (None, 0) or (status is not None and not 200 <= status < 300)
        for name in ("curl_errors", "player_errors"):
            handle = getattr(process, "_universal_tts_" + name, None)
            try:
                handle.seek(0)
                message = handle.read(8192).decode("utf-8", "replace").strip()
                if message:
                    universal_tts_debug("UNIVERSAL TTS %s: %s | %s" % ("ERROR" if failed else "INFO", name, message))
            except Exception:
                pass
        universal_tts_debug("UNIVERSAL TTS: pipe result | HTTP=%r | curl=%r | ffplay=%r" % (status, curl_code, player_code))
        if failed:
            hints = {404: "Check the endpoint and voice ID.", 409: "The TTS server is still busy with the previous line.", 422: "The server rejected the voice or request settings.", 429: "The server is rate limited.", 503: "The TTS model is not ready; check server logs and free VRAM."}
            universal_tts_debug("UNIVERSAL TTS ERROR: %s" % hints.get(status, "Check the server and tool errors above."))
        return status, failed


    def universal_tts_close_process_handles(process):
        if process is None:
            return

        curl_process = getattr(process, "_universal_tts_curl_process", None)

        if curl_process is not None:
            if curl_process.poll() is None:
                universal_tts_terminate_process(curl_process)
            universal_tts_reap_process(curl_process)

        universal_tts_reap_process(process)

        try:
            stdin = getattr(process, "stdin", None)
            stdout = getattr(process, "stdout", None)
            stderr = getattr(process, "stderr", None)
            universal_tts_close_quietly(stdin)
            universal_tts_close_quietly(stdout)
            universal_tts_close_quietly(stderr)
        except Exception:
            pass

        devnull = getattr(process, "_universal_tts_devnull", None)
        universal_tts_close_quietly(devnull)
        for name in ("curl_errors", "player_errors"):
            universal_tts_close_quietly(getattr(process, "_universal_tts_" + name, None))
        universal_tts_delete_request_file(getattr(process, "_universal_tts_headers_path", None))


    def universal_tts_stream_to_ffplay(text, speaker, request_id):
        request_file = None
        process = None

        audio = universal_tts_audio()
        renpy.log("UNIVERSAL TTS: stream start | request=%r | speaker=%r | text=%r" % (
            request_id,
            speaker,
            text,
        ))
        renpy.log("UNIVERSAL TTS: playback format | raw_pcm=%r | sample_format=%r | sample_rate=%r | channel_layout=%r" % (
            universal_tts_raw_pcm_enabled(),
            audio.get("sample_format", None),
            audio.get("sample_rate", None),
            audio.get("channel_layout", None),
        ))

        try:
            if not universal_tts_request_is_active(request_id):
                return
            request_file, url, descriptor = universal_tts_write_request_file(text, speaker)
            renpy.log("UNIVERSAL TTS: request built | type=%r | %s" % (
                universal_tts_request_type(),
                descriptor,
            ))
            retry_deadline = time.time() + universal_tts_section("network").get("busy_retry_seconds", 3)
            while universal_tts_request_is_active(request_id):
                process = universal_tts_start_pipeline(request_file, url)
                if not universal_tts_set_current_process(request_id, process, request_file):
                    renpy.log("UNIVERSAL TTS: stale pipe ignored before playback | request=%r" % request_id)
                    return

                while process.poll() is None and universal_tts_request_is_active(request_id):
                    time.sleep(0.02)

                if not universal_tts_request_is_active(request_id):
                    renpy.log("UNIVERSAL TTS: pipe canceled | request=%r" % request_id)
                    return

                curl_process = process._universal_tts_curl_process
                exit_deadline = time.time() + 0.5
                while curl_process.poll() is None and time.time() < exit_deadline and universal_tts_request_is_active(request_id):
                    time.sleep(0.01)
                if not universal_tts_request_is_active(request_id):
                    return
                if curl_process.poll() is None:
                    universal_tts_terminate_process(curl_process)

                status, failed = universal_tts_report_pipeline(process)
                universal_tts_clear_current_process(request_id, process)
                universal_tts_close_process_handles(process)
                process = None
                if status == 409 and time.time() < retry_deadline:
                    renpy.log("UNIVERSAL TTS: busy retry | request=%r" % request_id)
                    pause_until = min(time.time() + 0.25, retry_deadline)
                    while time.time() < pause_until and universal_tts_request_is_active(request_id):
                        time.sleep(0.02)
                    continue
                if failed:
                    raise RuntimeError("TTS pipe failed (HTTP %r); see renpy_universal_tts_debug.log" % status)
                renpy.log("UNIVERSAL TTS: pipe finished")
                return
        finally:
            universal_tts_clear_current_process(request_id, process)

            if process is not None:
                universal_tts_terminate_process(process)

            universal_tts_close_process_handles(process)
            universal_tts_delete_request_file(request_file)


    def universal_tts_cancel_and_stop(reason, reset_speaker=False):
        state = _universal_tts_state

        if state.condition is not None:
            with state.condition:
                state.request_id += 1
                state.active_id = state.request_id
                state.pending = None
                process, request_file = universal_tts_take_current_process()
                state.condition.notify()
        else:
            process, request_file = universal_tts_take_current_process()

        if reset_speaker:
            state.last_spoken_speaker = None
            state.pending_speaker = None

        universal_tts_terminate_process(process)
        renpy.log("UNIVERSAL TTS: stopped playback | %s" % reason)


    def universal_tts_worker_loop(state):
        renpy.log("UNIVERSAL TTS: worker started")

        while True:
            with state.condition:
                while state.pending is None:
                    state.condition.wait()

                request_id, text, speaker = state.pending
                state.pending = None

            try:
                universal_tts_stream_to_ffplay(text, speaker, request_id)
            except Exception as e:
                universal_tts_debug("UNIVERSAL TTS ERROR: generation failed | request=%r | speaker=%r | text=%r | %r" % (
                    request_id,
                    speaker,
                    text,
                    e,
                ))


    def universal_tts_ensure_worker():
        state = _universal_tts_state

        if state.condition is None:
            renpy.log("UNIVERSAL TTS: threading unavailable; cannot run non-blocking TTS")
            return False

        if not hasattr(renpy, "invoke_in_thread"):
            renpy.log("UNIVERSAL TTS: Ren'Py thread helper unavailable; cannot run non-blocking TTS")
            return False

        should_start = False

        with state.condition:
            if not state.worker_started:
                state.worker_started = True
                should_start = True

        if should_start:
            try:
                renpy.invoke_in_thread(universal_tts_worker_loop, state)
            except Exception as e:
                with state.condition:
                    state.worker_started = False
                renpy.log("UNIVERSAL TTS: worker start failed: %r" % e)
                return False

        return True


    def universal_tts_queue_text(text, speaker):
        state = _universal_tts_state

        if not universal_tts_ensure_worker():
            return

        with state.condition:
            state.request_id += 1
            request_id = state.request_id
            state.active_id = request_id
            # Detach the old pipe before waking the worker so cancellation cannot stop the new one.
            process, request_file = universal_tts_take_current_process()
            state.pending = (request_id, text, speaker)
            state.condition.notify()

        universal_tts_terminate_process(process)

        universal_tts_debug("UNIVERSAL TTS: queued | request=%r | speaker=%r | text=%r" % (
            request_id,
            speaker,
            text,
        ))


    def universal_tts_function(text):
        universal_tts_debug("UNIVERSAL TTS: tts_function called | mode=%r | text=%r" % (
            universal_tts_self_voicing_mode(),
            text,
        ))

        if not universal_tts_enabled():
            universal_tts_debug("UNIVERSAL TTS: ignored because config is disabled or missing | error=%r" % UNIVERSAL_TTS_CONFIG_ERROR)
            return

        if text is None:
            universal_tts_cancel_and_stop("empty TTS request")
            return

        if not universal_tts_speech_mode_active():
            universal_tts_cancel_and_stop("self-voicing is not in speech mode", reset_speaker=True)
            return

        clean = universal_tts_clean_text(text)

        if not clean:
            universal_tts_cancel_and_stop("blank TTS request")
            return

        speech_text, speaker = universal_tts_prepare_text_and_speaker(clean)

        if not speech_text:
            renpy.log("UNIVERSAL TTS: speaker name skipped | speaker=%r | source=%r" % (
                speaker,
                clean,
            ))
            return

        universal_tts_queue_text(speech_text, speaker)


    def universal_tts_watch_self_voicing(*args, **kwargs):
        state = _universal_tts_state
        raw_mode = universal_tts_self_voicing_mode()
        active = universal_tts_speech_mode_active()

        if not universal_tts_enabled():
            if UNIVERSAL_TTS_CONFIG_ERROR and active and not state.error_notified:
                state.error_notified = True
                try:
                    renpy.notify("Universal TTS config error. See renpy_universal_tts_debug.log.")
                except Exception:
                    pass
            return

        if getattr(config, "tts_function", None) is not universal_tts_function:
            universal_tts_debug("UNIVERSAL TTS: config.tts_function was changed at runtime, patching it again | current=%r" % getattr(config, "tts_function", None))
            config.tts_function = universal_tts_function

        if state.last_self_voicing_mode != raw_mode or state.last_speech_mode != active:
            universal_tts_debug("UNIVERSAL TTS: self-voicing state | mode=%r | active=%r | tts_function=%r" % (
                raw_mode,
                active,
                getattr(config, "tts_function", None),
            ))

        if state.last_speech_mode and not active:
            universal_tts_cancel_and_stop("self-voicing turned off", reset_speaker=True)

        state.last_self_voicing_mode = raw_mode
        state.last_speech_mode = active


    try:
        if universal_tts_watch_self_voicing not in config.interact_callbacks:
            config.interact_callbacks.append(universal_tts_watch_self_voicing)
    except Exception as e:
        renpy.log("UNIVERSAL TTS: interact watcher registration failed: %r" % e)

    try:
        if hasattr(config, "periodic_callbacks") and universal_tts_watch_self_voicing not in config.periodic_callbacks:
            config.periodic_callbacks.append(universal_tts_watch_self_voicing)
    except Exception as e:
        renpy.log("UNIVERSAL TTS: periodic watcher registration failed: %r" % e)

    if universal_tts_enabled():
        config.tts_function = universal_tts_function
        universal_tts_debug("UNIVERSAL TTS: config.tts_function patched | engine=%r | request_type=%r" % (
            universal_tts_engine(),
            universal_tts_request_type(),
        ))
    else:
        universal_tts_debug("UNIVERSAL TTS: preserving original self-voicing | config disabled or invalid")


init 2000 python:
    try:
        if universal_tts_enabled():
            config.tts_function = universal_tts_function
            universal_tts_debug("UNIVERSAL TTS: config.tts_function late patch | current=%r" % config.tts_function)
    except Exception as e:
        universal_tts_debug("UNIVERSAL TTS: config.tts_function late patch failed: %r" % e)
