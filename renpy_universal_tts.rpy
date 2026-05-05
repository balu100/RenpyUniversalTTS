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

    try:
        import threading
    except Exception:
        threading = None

    try:
        text_type = unicode
    except NameError:
        text_type = str

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
        configured = universal_tts_clean_text(configured)

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
        return universal_tts_bool(audio.get("raw_pcm", False), False)


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
        url = universal_tts_clean_text(openai.get("url", ""))
        model = openai.get("model", None)
        voice = universal_tts_voice_for_speaker(speaker)
        response_format = openai.get("response_format", None)

        if not url:
            raise ValueError("openai.url is missing")

        if model is None:
            raise ValueError("openai.model is missing")

        if voice is None:
            raise ValueError("default_voice or voices mapping is missing")

        if response_format is None:
            raise ValueError("openai.response_format is missing")

        payload = {
            "model": model,
            "voice": voice,
            "input": text,
            "response_format": response_format,
        }

        if "stream" in openai:
            payload["stream"] = universal_tts_bool(openai.get("stream"), False)

        if openai.get("speed", None) is not None:
            payload["speed"] = openai.get("speed")

        extra_body = openai.get("extra_body", {})

        if universal_tts_is_mapping(extra_body):
            for key, value in extra_body.items():
                payload[key] = value

        return payload, url, "openai voice=%r" % voice


    def universal_tts_chatterbox_payload(text, speaker):
        chatterbox = universal_tts_section("chatterbox")
        url = universal_tts_clean_text(chatterbox.get("url", ""))
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

        if chatterbox.get("output_format", None) is not None:
            payload["output_format"] = chatterbox.get("output_format")

        for key in ("split_text", "chunk_size", "language"):
            if key in chatterbox:
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
            "split_text",
            "chunk_size",
        ):
            if key in profile:
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
        return [
            universal_tts_find_curl_path(),
            "-sN",
            "--json",
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
        curl_process = None

        kwargs = {
            "stderr": devnull,
            "bufsize": 0,
        }
        kwargs.update(universal_tts_subprocess_kwargs())

        try:
            curl_process = subprocess.Popen(
                curl_command,
                stdin=devnull,
                stdout=subprocess.PIPE,
                **kwargs
            )
            ffplay_process = subprocess.Popen(
                ffplay_command,
                stdin=curl_process.stdout,
                stdout=devnull,
                **kwargs
            )
            universal_tts_close_quietly(curl_process.stdout)
            ffplay_process._universal_tts_curl_process = curl_process
            ffplay_process._universal_tts_devnull = devnull
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

            universal_tts_close_quietly(devnull)
            raise


    def universal_tts_close_process_handles(process):
        if process is None:
            return

        curl_process = getattr(process, "_universal_tts_curl_process", None)

        if curl_process is not None:
            if curl_process.poll() is None:
                universal_tts_terminate_process(curl_process)

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


    def universal_tts_stop_playback(reason):
        process, request_file = universal_tts_take_current_process()

        if process is not None:
            universal_tts_terminate_process(process)
            universal_tts_close_process_handles(process)

        universal_tts_delete_request_file(request_file)
        renpy.log("UNIVERSAL TTS: stopped playback | %s" % reason)


    def universal_tts_stream_to_ffplay(text, speaker, request_id):
        request_file = None
        process = None
        finished_normally = False

        audio = universal_tts_audio()
        renpy.log("UNIVERSAL TTS: stream MISS | request=%r | speaker=%r | text=%r" % (
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
            request_file, url, descriptor = universal_tts_write_request_file(text, speaker)
            renpy.log("UNIVERSAL TTS: request built | type=%r | %s" % (
                universal_tts_request_type(),
                descriptor,
            ))
            process = universal_tts_start_pipeline(request_file, url)

            if not universal_tts_set_current_process(request_id, process, request_file):
                renpy.log("UNIVERSAL TTS: stale pipe ignored before playback | request=%r" % request_id)
                return

            while process.poll() is None and universal_tts_request_is_active(request_id):
                time.sleep(0.05)

            if not universal_tts_request_is_active(request_id):
                renpy.log("UNIVERSAL TTS: pipe canceled | request=%r" % request_id)
                return

            if process.poll() not in (0, None):
                renpy.log("UNIVERSAL TTS: pipe exited with code %r" % process.poll())

            renpy.log("UNIVERSAL TTS: pipe finished")
            finished_normally = True
        finally:
            universal_tts_clear_current_process(request_id, process)

            if process is not None and not finished_normally:
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
                state.condition.notify()

        if reset_speaker:
            state.last_spoken_speaker = None
            state.pending_speaker = None

        universal_tts_stop_playback(reason)


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
            state.pending = (request_id, text, speaker)
            state.condition.notify()

        universal_tts_stop_playback("new TTS request")

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

    config.tts_function = universal_tts_function

    universal_tts_debug("UNIVERSAL TTS: config.tts_function patched | engine=%r | request_type=%r" % (
        universal_tts_engine(),
        universal_tts_request_type(),
    ))


init 2000 python:
    try:
        config.tts_function = universal_tts_function
        universal_tts_debug("UNIVERSAL TTS: config.tts_function late patch | current=%r" % config.tts_function)
    except Exception as e:
        universal_tts_debug("UNIVERSAL TTS: config.tts_function late patch failed: %r" % e)
