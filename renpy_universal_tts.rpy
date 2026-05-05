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

    # ============================================================
    # EASY CONFIG - MOST USERS ONLY EDIT THIS PART
    # ============================================================

    UNIVERSAL_TTS_ENABLED = True

    # Options:
    # "vibevoice" = VibeVoice server with streamed raw PCM.
    # "kokoro" = Kokoro server with streamed raw PCM.
    # "kokoro_mp3" = Kokoro server with MP3 fallback.
    # "custom" = use the Advanced Config values below.
    UNIVERSAL_TTS_ENGINE = "vibevoice"

    # Leave as None to use the engine preset default voice.
    UNIVERSAL_TTS_DEFAULT_VOICE = None

    # Speaker name reading mode:
    # "always", "never", or "on_speaker_change".
    UNIVERSAL_TTS_READ_SPEAKER_NAMES = "on_speaker_change"

    # Leave empty to use the engine preset speaker examples, or edit for a game.
    UNIVERSAL_TTS_VOICE_BY_SPEAKER = {}

    # ============================================================
    # ADVANCED CONFIG - CHANGE ONLY IF NEEDED
    # ============================================================

    # Leave values as None to let UNIVERSAL_TTS_ENGINE fill them in.
    UNIVERSAL_TTS_URL = None
    UNIVERSAL_TTS_MODEL = None
    UNIVERSAL_TTS_RESPONSE_FORMAT = None
    UNIVERSAL_TTS_REQUEST_STREAM = None
    UNIVERSAL_TTS_SPEED = None
    UNIVERSAL_TTS_EXTRA_BODY = {}

    UNIVERSAL_TTS_FFPLAY_RAW_PCM = None
    UNIVERSAL_TTS_PCM_SAMPLE_FORMAT = None
    UNIVERSAL_TTS_PCM_SAMPLE_RATE = None
    UNIVERSAL_TTS_PCM_CHANNEL_LAYOUT = None

    # Current ffplay builds use "ch_layout". Older builds may need "ac".
    UNIVERSAL_TTS_FFPLAY_CHANNEL_OPTION = "ch_layout"

    UNIVERSAL_TTS_CURL_PATH = "curl"
    UNIVERSAL_TTS_FFPLAY_PATH = "ffplay"
    UNIVERSAL_TTS_FFPLAY_LOGLEVEL = "error"
    UNIVERSAL_TTS_FFPLAY_VOLUME = None
    UNIVERSAL_TTS_FFPLAY_EXTRA_ARGS = ()


    def universal_tts_config_text(value):
        if value is None:
            return ""

        try:
            return text_type(value)
        except Exception:
            try:
                return str(value)
            except Exception:
                return ""


    def universal_tts_value_is_unset(value):
        if value is None:
            return True

        try:
            return universal_tts_config_text(value).strip() == ""
        except Exception:
            return False


    def universal_tts_apply_if_unset(name, value):
        if universal_tts_value_is_unset(globals().get(name, None)):
            globals()[name] = value


    def universal_tts_apply_engine_preset():
        engine = universal_tts_config_text(UNIVERSAL_TTS_ENGINE).strip().lower().replace("-", "_").replace(" ", "_")
        preset = None

        if engine in ("vibevoice", "vibe"):
            preset = {
                "url": "http://localhost:8880/v1/audio/speech",
                "model": "tts-1",
                "response_format": "pcm",
                "request_stream": True,
                "speed": None,
                "raw_pcm": True,
                "sample_format": "s16le",
                "sample_rate": 24000,
                "channel_layout": "mono",
                "default_voice": "Emma",
                "voices": {
                    "Narrator": "Davis",
                    "MC": "Mike",
                    "Daniel": "Mike",
                },
            }
        elif engine in ("kokoro", "kokoro_pcm"):
            preset = {
                "url": "http://127.0.0.1:8880/v1/audio/speech",
                "model": "kokoro",
                "response_format": "pcm",
                "request_stream": True,
                "speed": 1.0,
                "raw_pcm": True,
                "sample_format": "s16le",
                "sample_rate": 24000,
                "channel_layout": "mono",
                "default_voice": "af_heart",
                "voices": {
                    "Narrator": "af_heart",
                    "MC": "am_puck",
                    "Daniel": "am_puck",
                },
            }
        elif engine in ("kokoro_mp3", "kokoro_fallback", "kokoro_mp3_fallback"):
            preset = {
                "url": "http://127.0.0.1:8880/v1/audio/speech",
                "model": "kokoro",
                "response_format": "mp3",
                "request_stream": False,
                "speed": 1.0,
                "raw_pcm": False,
                "sample_format": "s16le",
                "sample_rate": 24000,
                "channel_layout": "mono",
                "default_voice": "af_heart",
                "voices": {
                    "Narrator": "af_heart",
                    "MC": "am_puck",
                    "Daniel": "am_puck",
                },
            }
        elif engine in ("custom", "openai", "openai_compatible"):
            preset = {
                "url": "http://localhost:8880/v1/audio/speech",
                "model": "tts-1",
                "response_format": "pcm",
                "request_stream": True,
                "speed": None,
                "raw_pcm": True,
                "sample_format": "s16le",
                "sample_rate": 24000,
                "channel_layout": "mono",
                "default_voice": "alloy",
                "voices": {},
            }
        else:
            renpy.log("UNIVERSAL TTS: unknown UNIVERSAL_TTS_ENGINE %r, using custom defaults" % UNIVERSAL_TTS_ENGINE)
            preset = {
                "url": "http://localhost:8880/v1/audio/speech",
                "model": "tts-1",
                "response_format": "pcm",
                "request_stream": True,
                "speed": None,
                "raw_pcm": True,
                "sample_format": "s16le",
                "sample_rate": 24000,
                "channel_layout": "mono",
                "default_voice": "alloy",
                "voices": {},
            }

        universal_tts_apply_if_unset("UNIVERSAL_TTS_URL", preset["url"])
        universal_tts_apply_if_unset("UNIVERSAL_TTS_MODEL", preset["model"])
        universal_tts_apply_if_unset("UNIVERSAL_TTS_RESPONSE_FORMAT", preset["response_format"])
        universal_tts_apply_if_unset("UNIVERSAL_TTS_REQUEST_STREAM", preset["request_stream"])
        universal_tts_apply_if_unset("UNIVERSAL_TTS_SPEED", preset["speed"])
        universal_tts_apply_if_unset("UNIVERSAL_TTS_FFPLAY_RAW_PCM", preset["raw_pcm"])
        universal_tts_apply_if_unset("UNIVERSAL_TTS_PCM_SAMPLE_FORMAT", preset["sample_format"])
        universal_tts_apply_if_unset("UNIVERSAL_TTS_PCM_SAMPLE_RATE", preset["sample_rate"])
        universal_tts_apply_if_unset("UNIVERSAL_TTS_PCM_CHANNEL_LAYOUT", preset["channel_layout"])
        universal_tts_apply_if_unset("UNIVERSAL_TTS_DEFAULT_VOICE", preset["default_voice"])

        try:
            if not UNIVERSAL_TTS_VOICE_BY_SPEAKER:
                globals()["UNIVERSAL_TTS_VOICE_BY_SPEAKER"] = dict(preset["voices"])
        except Exception:
            globals()["UNIVERSAL_TTS_VOICE_BY_SPEAKER"] = dict(preset["voices"])

        renpy.log("UNIVERSAL TTS: engine=%r url=%r model=%r format=%r stream=%r raw_pcm=%r" % (
            engine,
            UNIVERSAL_TTS_URL,
            UNIVERSAL_TTS_MODEL,
            UNIVERSAL_TTS_RESPONSE_FORMAT,
            UNIVERSAL_TTS_REQUEST_STREAM,
            UNIVERSAL_TTS_FFPLAY_RAW_PCM,
        ))


    universal_tts_apply_engine_preset()


    class UniversalTTSState(_universal_tts_state_base):
        def __init__(self):
            self.worker_started = False
            self.request_id = 0
            self.active_id = 0
            self.pending = None
            self.last_speech_mode = None
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


    def universal_tts_self_voicing_mode():
        try:
            return renpy.game.preferences.self_voicing
        except Exception:
            return False


    def universal_tts_speech_mode_active():
        mode = universal_tts_self_voicing_mode()
        return mode is True or mode == True


    def universal_tts_sorted_speakers():
        speakers = []

        for speaker in UNIVERSAL_TTS_VOICE_BY_SPEAKER.keys():
            name = universal_tts_clean_text(speaker)

            if name:
                speakers.append(name)

        return sorted(speakers, key=len, reverse=True)


    def universal_tts_name_read_mode():
        mode = UNIVERSAL_TTS_READ_SPEAKER_NAMES

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

        renpy.log("UNIVERSAL TTS: unknown UNIVERSAL_TTS_READ_SPEAKER_NAMES value %r, using 'on_speaker_change'" % mode)
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


    def universal_tts_voice_for_speaker(speaker):
        if speaker:
            voice = UNIVERSAL_TTS_VOICE_BY_SPEAKER.get(speaker, None)

            if voice is not None:
                return voice

            for speaker_name, mapped_voice in UNIVERSAL_TTS_VOICE_BY_SPEAKER.items():
                if universal_tts_clean_text(speaker_name) == speaker:
                    return mapped_voice

        return UNIVERSAL_TTS_DEFAULT_VOICE


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

        return universal_tts_clean_text(speech_text), universal_tts_voice_for_speaker(speaker), speaker


    def universal_tts_prepare_text_and_voice(text):
        state = _universal_tts_state
        clean = universal_tts_clean_text(text)
        speaker, body = universal_tts_split_speaker_text(clean)

        if speaker is not None:
            if not body:
                state.pending_speaker = speaker
                return u"", universal_tts_voice_for_speaker(speaker), speaker

            state.pending_speaker = None
            return universal_tts_apply_name_policy(speaker, body)

        if state.pending_speaker is not None:
            speaker = state.pending_speaker
            state.pending_speaker = None
            return universal_tts_apply_name_policy(speaker, clean)

        state.last_spoken_speaker = None
        return clean, UNIVERSAL_TTS_DEFAULT_VOICE, None


    def universal_tts_add_unique_path(paths, path):
        if not path:
            return

        try:
            path = os.path.normpath(path)
        except Exception:
            pass

        if path not in paths:
            paths.append(path)


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


    def universal_tts_find_curl_path():
        return universal_tts_find_existing_path(universal_tts_possible_executable_paths(UNIVERSAL_TTS_CURL_PATH, "curl"))


    def universal_tts_find_ffplay_path():
        return universal_tts_find_existing_path(universal_tts_possible_executable_paths(UNIVERSAL_TTS_FFPLAY_PATH, "ffplay"))


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


    def universal_tts_ffplay_command():
        command = [
            universal_tts_find_ffplay_path(),
            "-nodisp",
            "-autoexit",
            "-loglevel",
            universal_tts_clean_text(UNIVERSAL_TTS_FFPLAY_LOGLEVEL) or "error",
        ]

        if UNIVERSAL_TTS_FFPLAY_RAW_PCM:
            command.extend([
                "-f",
                universal_tts_clean_text(UNIVERSAL_TTS_PCM_SAMPLE_FORMAT) or "s16le",
                "-sample_rate",
                str(int(UNIVERSAL_TTS_PCM_SAMPLE_RATE)),
            ])

            channel_option = universal_tts_clean_text(UNIVERSAL_TTS_FFPLAY_CHANNEL_OPTION).lower()

            if channel_option in ("ac", "channels", "legacy"):
                command.extend(["-ac", "1" if universal_tts_clean_text(UNIVERSAL_TTS_PCM_CHANNEL_LAYOUT) == "mono" else universal_tts_clean_text(UNIVERSAL_TTS_PCM_CHANNEL_LAYOUT)])
            else:
                command.extend([
                    "-ch_layout",
                    universal_tts_clean_text(UNIVERSAL_TTS_PCM_CHANNEL_LAYOUT) or "mono",
                ])

        if UNIVERSAL_TTS_FFPLAY_VOLUME is not None:
            command.extend(["-volume", str(int(UNIVERSAL_TTS_FFPLAY_VOLUME))])

        for arg in UNIVERSAL_TTS_FFPLAY_EXTRA_ARGS:
            command.append(universal_tts_to_text(arg))

        command.extend(["-i", "-"])

        return command


    def universal_tts_request_payload(text, voice):
        payload = {
            "model": UNIVERSAL_TTS_MODEL,
            "voice": voice,
            "input": text,
            "response_format": UNIVERSAL_TTS_RESPONSE_FORMAT,
            "stream": bool(UNIVERSAL_TTS_REQUEST_STREAM),
        }

        if UNIVERSAL_TTS_SPEED is not None:
            payload["speed"] = UNIVERSAL_TTS_SPEED

        try:
            for key, value in UNIVERSAL_TTS_EXTRA_BODY.items():
                payload[key] = value
        except Exception:
            pass

        return payload


    def universal_tts_write_request_file(text, voice):
        payload = universal_tts_request_payload(text, voice)
        data = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("ascii")
        handle = tempfile.NamedTemporaryFile(prefix="renpy_universal_tts_", suffix=".json", delete=False)

        try:
            handle.write(data)
            return handle.name
        finally:
            handle.close()


    def universal_tts_delete_request_file(path):
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            pass


    def universal_tts_curl_command(request_file):
        return [
            universal_tts_find_curl_path(),
            "-sN",
            "--json",
            "@" + request_file,
            UNIVERSAL_TTS_URL,
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


    def universal_tts_start_pipeline(request_file):
        curl_command = universal_tts_curl_command(request_file)
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
            renpy.log("UNIVERSAL TTS: pipe started | curl=%r | ffplay=%r" % (
                curl_command,
                ffplay_command,
            ))
            return ffplay_process
        except Exception:
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


    def universal_tts_stream_to_ffplay(text, voice, request_id):
        request_file = None
        process = None
        finished_normally = False

        renpy.log("UNIVERSAL TTS: stream MISS | request=%r | voice=%r | text=%r" % (
            request_id,
            voice,
            text,
        ))
        renpy.log("UNIVERSAL TTS: playback format | raw_pcm=%r | format=%r | sample_rate=%r | channel_layout=%r" % (
            UNIVERSAL_TTS_FFPLAY_RAW_PCM,
            UNIVERSAL_TTS_PCM_SAMPLE_FORMAT,
            UNIVERSAL_TTS_PCM_SAMPLE_RATE,
            UNIVERSAL_TTS_PCM_CHANNEL_LAYOUT,
        ))

        try:
            request_file = universal_tts_write_request_file(text, voice)
            process = universal_tts_start_pipeline(request_file)

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

                request_id, text, voice = state.pending
                state.pending = None

            try:
                universal_tts_stream_to_ffplay(text, voice, request_id)
            except Exception as e:
                renpy.log("UNIVERSAL TTS ERROR: generation failed | request=%r | voice=%r | text=%r | %r" % (
                    request_id,
                    voice,
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


    def universal_tts_queue_text(text, voice):
        state = _universal_tts_state

        if not universal_tts_ensure_worker():
            return

        with state.condition:
            state.request_id += 1
            request_id = state.request_id
            state.active_id = request_id
            state.pending = (request_id, text, voice)
            state.condition.notify()

        universal_tts_stop_playback("new TTS request")

        renpy.log("UNIVERSAL TTS: queued | request=%r | voice=%r | text=%r" % (
            request_id,
            voice,
            text,
        ))


    def universal_tts_function(text):
        if not UNIVERSAL_TTS_ENABLED:
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

        speech_text, voice, speaker = universal_tts_prepare_text_and_voice(clean)

        if not speech_text:
            renpy.log("UNIVERSAL TTS: speaker name skipped | speaker=%r | source=%r" % (
                speaker,
                clean,
            ))
            return

        universal_tts_queue_text(speech_text, voice)


    def universal_tts_watch_self_voicing(*args, **kwargs):
        state = _universal_tts_state
        active = universal_tts_speech_mode_active()

        if state.last_speech_mode and not active:
            universal_tts_cancel_and_stop("self-voicing turned off", reset_speaker=True)

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

    renpy.log("UNIVERSAL TTS: config.tts_function patched")
