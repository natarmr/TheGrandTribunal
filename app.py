from __future__ import annotations

import base64
import concurrent.futures
import html
import os
import random
import tempfile

import gradio as gr
import requests

from tribunal_shared import (
    CHARACTER_REGISTRY as OPPONENTS,
    GENERIC_MODAL_ERROR,
    INVALID_ARGUMENT_MESSAGE,
    MODAL_ENDPOINTS,
    clamp_argument,
    looks_like_bad_transcript,
    looks_like_prompt_injection,
)

JUDGE_URL = MODAL_ENDPOINTS["judge"]
CHARACTER_URL = MODAL_ENDPOINTS["character"]
STT_URL = MODAL_ENDPOINTS["stt"]
TTS_URL = MODAL_ENDPOINTS["tts"]
REQUEST_TIMEOUT = 240
MODAL_PROXY_AUTH_TOKEN_ID_ENV = "MODAL_PROXY_AUTH_TOKEN_ID"
MODAL_PROXY_AUTH_TOKEN_SECRET_ENV = "MODAL_PROXY_AUTH_TOKEN_SECRET"


def get_modal_proxy_auth_headers():
    token_id = os.environ.get(MODAL_PROXY_AUTH_TOKEN_ID_ENV, "").strip()
    token_secret = os.environ.get(MODAL_PROXY_AUTH_TOKEN_SECRET_ENV, "").strip()
    if not token_id or not token_secret:
        return {}
    return {"Modal-Key": token_id, "Modal-Secret": token_secret}


def load_asset_data_uri(filename, mime_type):
    asset_path = os.path.join(os.path.dirname(__file__), filename)
    with open(asset_path, "rb") as asset_file:
        encoded = base64.b64encode(asset_file.read()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


LANDING_LOGO_DATA_URI = load_asset_data_uri("logo.jpg", "image/jpeg")


CSS = """
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700;900&family=Inter:wght@400;500;700;800&display=swap');

:root {
    --ink: #111318;
    --paper: #f7efe0;
    --gold: #c99a3e;
    --jade: #2f8c68;
}

html, body {
    margin: 0 !important;
    padding: 0 !important;
    width: 100%;
    overflow-x: hidden;
    background: #111111 !important;
}

.gradio-container,
.gradio-container > .main {
    max-width: none !important;
    min-height: auto !important;
    height: auto !important;
    padding: 0 !important;
    margin: 0 !important;
    gap: 0 !important;
    background: #111111 !important;
    color: var(--paper);
    font-family: Inter, system-ui, sans-serif;
}

#tribunal-app {
    max-width: none !important;
    margin: 0 !important;
    padding: 0 !important;
    min-height: auto !important;
    height: auto !important;
}

#tribunal-app .block,
#tribunal-app .form,
#tribunal-app .column,
#tribunal-app .wrap,
#tribunal-app .gap {
    padding: 0 !important;
    margin: 0 !important;
    gap: 0 !important;
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
}

#tribunal-app textarea,
#tribunal-app input,
#tribunal-app select {
    background: #111111 !important;
    color: #ddd6ca !important;
    border: 1px solid rgba(255, 255, 255, 0.16) !important;
    border-radius: 8px !important;
}

#landing-view {
    display: flex !important;
    flex-direction: column !important;
    min-height: auto !important;
    height: auto !important;
    overflow: visible !important;
    padding: 0 !important;
    gap: 0 !important;
    border: 0 !important;
    background: linear-gradient(180deg, rgba(18, 18, 18, 0.98), rgba(15, 15, 15, 0.98)), #111111 !important;
}

#landing-view.hide,
#landing-view.hidden,
#landing-view[hidden] {
    display: none !important;
}

#landing-header {
    height: 90px;
    flex: 0 0 auto;
    display: flex;
    align-items: center;
    padding: 0 clamp(28px, 5vw, 92px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.12);
    background: #121212;
}

#landing-brand {
    display: flex;
    align-items: center;
    gap: 18px;
    min-width: 0;
}

#landing-brand img {
    width: 42px;
    height: 42px;
    object-fit: contain;
}

#landing-brand-title {
    color: #d6d0c6;
    font-family: Cinzel, serif;
    font-size: clamp(1.9rem, 3vw, 3.1rem);
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    white-space: nowrap;
}

#landing-stage {
    flex: 0 0 auto !important;
    display: grid;
    place-items: start center;
    padding: 24px 16px 32px !important;
}

#docket-card {
    width: min(92vw, 860px);
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 10px;
    background: linear-gradient(180deg, rgba(28, 28, 28, 0.99), rgba(22, 22, 22, 0.99)), #171717;
    box-shadow: 0 22px 60px rgba(0, 0, 0, 0.45);
    padding: 32px 0 28px;
}

#docket-inner {
    width: min(100%, 760px);
    margin: 0 auto;
    padding: 0 20px;
}

.field-label {
    margin: 0 0 10px;
    color: rgba(255, 255, 255, 0.5);
    font-family: "Space Mono", monospace;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.34em;
    text-transform: uppercase;
}

#topic-input { margin: 0 0 16px !important; }
#stance-input { margin: 0 0 16px !important; }
#opponent-input { margin: 0 0 20px !important; }

#topic-input textarea {
    min-height: 120px !important;
    padding: 16px !important;
    font-size: 1rem !important;
    line-height: 1.4 !important;
}

#stance-input input,
#stance-input button,
#stance-input [role="combobox"] {
    min-height: 64px !important;
    padding: 0 16px !important;
    font-family: Cinzel, serif !important;
    font-size: 1.35rem !important;
    text-transform: uppercase !important;
}

#opponent-input input,
#opponent-input button,
#opponent-input [role="combobox"] {
    min-height: 72px !important;
    padding: 0 16px !important;
    font-family: Cinzel, serif !important;
    font-size: 1.1rem !important;
}

#start-btn button {
    width: 100% !important;
    min-height: 88px !important;
    border: 2px solid rgba(201, 154, 62, 0.36) !important;
    border-radius: 0 !important;
    background: transparent !important;
    color: #d7ac43 !important;
    font-family: Cinzel, serif !important;
    font-size: 1.2rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.22em !important;
    text-transform: uppercase !important;
}

ul[role="listbox"] {
    background: #151515 !important;
    border: 1px solid rgba(255, 255, 255, 0.16) !important;
    border-radius: 8px !important;
}

li[data-testid="dropdown-option"] {
    color: #e2dbcf !important;
    font-family: Cinzel, serif !important;
    padding: 14px 18px !important;
}

.error-text { color: #ffd08a; font-weight: 800; }

.debate-shell {
    margin: 0 !important;
    padding: 0 !important;
    border: 1px solid rgba(245, 197, 79, 0.42);
    background: #06070a;
    overflow: hidden;
}

#court-scene {
    position: relative;
    min-height: min(720px, 85vh);
    overflow: hidden;
    border-radius: 6px;
    background:
        linear-gradient(180deg, rgba(255,255,255,0.06), transparent 26%),
        var(--court-bg) center / cover no-repeat,
        #b18115;
}

.court-hud {
    position: absolute;
    top: 16px;
    left: 16px;
    right: 16px;
    z-index: 4;
    display: grid;
    grid-template-columns: minmax(180px, 0.7fr) minmax(220px, 1fr) minmax(180px, 0.7fr);
    gap: 14px;
}

.court-docket,
.court-fighter {
    padding: 10px 12px;
    border: 2px solid rgba(255, 232, 142, 0.72);
    background: rgba(8, 11, 17, 0.78);
    color: #fff7de;
}

.court-docket { text-align: center; }
.court-fighter.right { text-align: right; }

.court-fighter-label {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    font-weight: 900;
    font-size: 0.9rem;
    text-transform: uppercase;
}

.court-hp-track {
    height: 18px;
    margin-top: 7px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.36);
    background: rgba(0, 0, 0, 0.62);
}

.court-hp-fill {
    height: 100%;
    background: linear-gradient(90deg, #18b974, #f2dc63);
}

.court-hp-fill.warning { background: linear-gradient(90deg, #d98520, #f6d46a); }
.court-hp-fill.danger { background: linear-gradient(90deg, #b51f32, #ff785e); }

.court-character {
    position: absolute;
    z-index: 2;
    left: clamp(34px, 8vw, 150px);
    bottom: 188px;
    width: min(50vw, 620px);
    max-height: calc(100% - 285px);
    object-fit: contain;
    object-position: bottom left;
}

.court-character.player {
    left: clamp(60px, 11vw, 190px);
    width: min(32vw, 380px);
    image-rendering: pixelated;
}

.court-verdict-strip {
    position: absolute;
    z-index: 3;
    right: 24px;
    top: 150px;
    max-width: min(420px, 42vw);
    padding: 10px 14px;
    background: rgba(11, 14, 22, 0.72);
    color: #e0d0b0;
    font-family: monospace;
    font-size: 0.8rem;
}

.dialogue-box {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 5;
    min-height: 170px;
    padding: 34px clamp(24px, 8vw, 150px) 24px;
    border-top: 3px solid rgba(255, 255, 255, 0.9);
    background: linear-gradient(90deg, rgba(3, 12, 26, 0.94), rgba(10, 17, 30, 0.82));
    color: white;
}

.dialogue-name {
    position: absolute;
    top: -28px;
    left: clamp(24px, 8vw, 150px);
    min-width: 210px;
    padding: 8px 28px 9px;
    font: 700 1.55rem/1 Cinzel, serif;
    background: linear-gradient(180deg, #3c9bc3, #257fa7);
    border: 2px solid white;
    text-align: center;
}

.dialogue-line {
    margin: 0;
    max-width: 1120px;
    font: 500 clamp(1.4rem, 3vw, 2.4rem)/1.2 Georgia, serif;
}

.argument-dock {
    padding: 10px 12px 12px;
    background: #080a0f;
    border-top: 1px solid rgba(255, 232, 142, 0.28);
}

.mic-panel {
    display: flex;
    align-items: center;
    gap: 8px;
    height: 52px;
}

.mic-panel button {
    height: 36px;
    min-height: 36px !important;
    padding: 0 16px;
    border-radius: 6px;
    background: linear-gradient(180deg, #d4a34b, #a7612f);
    color: #151312;
    font-weight: 900;
    cursor: pointer;
}

#tribunal-app button.primary {
    background: linear-gradient(180deg, #d4a34b, #a7612f) !important;
    color: #151312 !important;
    font-weight: 900 !important;
    min-height: 52px !important;
}

.hidden-runtime,
#mic-status,
.mic-playback {
    display: none !important;
}

#hidden-audio {
    position: absolute !important;
    opacity: 0 !important;
    pointer-events: none !important;
    width: 1px !important;
    height: 1px !important;
    overflow: hidden !important;
}

.voice-hint {
    padding: 8px 0;
    color: rgba(255, 255, 255, 0.38) !important;
    font-size: 0.75rem !important;
    text-align: center;
    text-transform: uppercase;
}

@media (max-width: 900px) {
    #landing-header { height: 80px; padding: 0 18px; }
    #landing-stage { padding: 16px 12px 24px !important; }
    #docket-card { padding: 24px 0 20px; }
    #docket-inner { padding: 0 16px; }
    .court-hud { grid-template-columns: 1fr; position: relative; inset: auto; padding: 12px; }
    #court-scene { min-height: 720px; }
    .court-character {
        left: 50%;
        transform: translateX(-50%);
        bottom: 215px;
        width: min(72vw, 310px);
    }
    .court-verdict-strip { display: none; }
}
"""


CUSTOM_JS = """
(() => {
    if (window.__tribunalRecorderInstalled) return;
    window.__tribunalRecorderInstalled = true;

    let recorder = null;
    let stream = null;
    let chunks = [];

    const setStatus = (message, recording = false) => {
        const status = document.getElementById("mic-status");
        if (!status) return;
        status.textContent = message;
        status.classList.toggle("recording", recording);
    };

    const setPayload = (value) => {
        const root = document.getElementById("voice-payload");
        const input = root && (root.querySelector("textarea") || root.querySelector("input"));
        if (!input) {
            setStatus("Recorder storage is not ready yet.");
            return;
        }
        const descriptor = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(input), "value");
        if (descriptor && descriptor.set) {
            descriptor.set.call(input, value);
        } else {
            input.value = value;
        }
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.dispatchEvent(new Event("change", { bubbles: true }));
    };

    const setButtons = (isRecording) => {
        const start = document.getElementById("mic-start");
        const stop = document.getElementById("mic-stop");
        if (start) start.disabled = isRecording;
        if (stop) stop.disabled = !isRecording;
    };

    document.addEventListener("click", async (event) => {
        const target = event.target;
        if (!(target instanceof HTMLElement)) return;

        if (target.id === "mic-start") {
            event.preventDefault();
            try {
                chunks = [];
                setPayload("");
                stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const options = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
                    ? { mimeType: "audio/webm;codecs=opus" }
                    : {};
                recorder = new MediaRecorder(stream, options);
                recorder.ondataavailable = (dataEvent) => {
                    if (dataEvent.data && dataEvent.data.size) chunks.push(dataEvent.data);
                };
                recorder.onstop = () => {
                    const blob = new Blob(chunks, { type: recorder.mimeType || "audio/webm" });
                    const playback = document.getElementById("mic-playback");
                    if (playback) playback.src = URL.createObjectURL(blob);
                    const reader = new FileReader();
                    reader.onloadend = () => {
                        setPayload(String(reader.result || ""));
                        setStatus("Recorded. Submit when ready.");
                    };
                    reader.readAsDataURL(blob);
                    if (stream) stream.getTracks().forEach((track) => track.stop());
                    setButtons(false);
                };
                recorder.start();
                setStatus("Recording...", true);
                setButtons(true);
            } catch (error) {
                setStatus("Microphone unavailable: " + error.message);
                setButtons(false);
            }
        }

        if (target.id === "mic-stop") {
            event.preventDefault();
            if (recorder && recorder.state === "recording") recorder.stop();
        }
    });
})();
"""


def opponent_name(opponent):
    return OPPONENTS.get(opponent, {}).get("name", "Opponent")


def file_url(path):
    return f"/gradio_api/file={html.escape(path)}"


def get_health_bar_html(hp, name, is_user=True):
    status = "danger" if hp <= 20 else "warning" if hp <= 50 else ""
    side = "left" if is_user else "right"
    safe_name = html.escape(name)
    safe_hp = max(0, min(100, int(hp)))
    return f"""
    <div class="health-card {side}">
        <div class="health-label">
            <span>{safe_name}</span>
            <span>{safe_hp}/100 HP</span>
        </div>
        <div class="health-track">
            <div class="health-fill {status}" style="width: {safe_hp}%;"></div>
        </div>
    </div>
    """


def get_sprite_path(opponent, pose="talking"):
    data = OPPONENTS.get(opponent) or OPPONENTS["oscar_wilde"]
    safe_pose = pose if pose in {"talking", "thinking", "damage", "victory"} else "talking"
    return f"sprites/{data['sprite']}_{safe_pose}.png"


def get_player_sprite_path(pose="thinking"):
    safe_pose = pose if pose in {"talking", "thinking", "damage", "victory"} else "thinking"
    return f"sprites/player_{safe_pose}.png"


def get_hp_class(hp):
    if hp <= 20:
        return "danger"
    if hp <= 50:
        return "warning"
    return ""


def get_arena_html(
    user_hp=100,
    opp_hp=100,
    opponent="oscar_wilde",
    topic="",
    stance="For",
    speaker="Advocate",
    dialogue="State your case. The tribunal is listening.",
    active_actor="player",
    opponent_pose="talking",
    player_pose="thinking",
    verdict="",
):
    data = OPPONENTS.get(opponent) or OPPONENTS["oscar_wilde"]
    topic_text = topic.strip() if topic else "Awaiting a motion before the court"
    stance_text = stance or "For"
    user_hp_safe = max(0, min(100, int(user_hp)))
    opp_hp_safe = max(0, min(100, int(opp_hp)))

    if active_actor == "opponent":
        active_sprite_path = get_sprite_path(opponent, opponent_pose)
        active_alt = data["name"]
        sprite_size_class = data.get("sprite_scale", "tall")
    else:
        active_sprite_path = get_player_sprite_path(player_pose)
        active_alt = "Advocate"
        sprite_size_class = "player"

    bg_path = "sprites/opp_background.jpg"
    verdict_html = ""
    if verdict:
        escaped_verdict = html.escape(verdict).replace("\n", "<br>")
        verdict_html = f'<div class="court-verdict-strip">{escaped_verdict}</div>'

    return f"""
    <div id="court-scene" style="--court-bg: url('{file_url(bg_path)}');">
        <div class="court-hud">
            <div class="court-fighter">
                <div class="court-fighter-label">
                    <span>Advocate</span>
                    <span>{user_hp_safe}/100</span>
                </div>
                <div class="court-hp-track">
                    <div class="court-hp-fill {get_hp_class(user_hp_safe)}" style="width: {user_hp_safe}%;"></div>
                </div>
            </div>
            <div class="court-docket">
                <strong>{html.escape(stance_text)} the motion</strong>
                <span>{html.escape(topic_text)}</span>
            </div>
            <div class="court-fighter right">
                <div class="court-fighter-label">
                    <span>{html.escape(data["name"])}</span>
                    <span>{opp_hp_safe}/100</span>
                </div>
                <div class="court-hp-track">
                    <div class="court-hp-fill {get_hp_class(opp_hp_safe)}" style="width: {opp_hp_safe}%;"></div>
                </div>
            </div>
        </div>
        <img class="court-character {sprite_size_class}" src="{file_url(active_sprite_path)}" alt="{html.escape(active_alt)}">
        {verdict_html}
        <div class="dialogue-box">
            <div class="dialogue-name">{html.escape(speaker)}</div>
            <p class="dialogue-line">{html.escape(dialogue)}</p>
        </div>
    </div>
    """


def calculate_damage(score):
    if score >= 5:
        return (score - 4) * 3
    return 0


def calculate_fatigue(score):
    if score < 5:
        return random.randint(1, 5)
    return 0


def _coerce_judge_int(value, fallback, minimum, maximum):
    try:
        coerced = int(round(float(value)))
    except (TypeError, ValueError):
        coerced = fallback
    return max(minimum, min(maximum, coerced))


def summarize_judge_result(j_res):
    if not isinstance(j_res, dict) or "error" in j_res:
        return {
            "score": 5,
            "raw_score": 5,
            "logic": 5,
            "relevance": 5,
            "creativity": 3,
            "reasoning": "Tribunal failed to evaluate the argument.",
        }

    raw_score = _coerce_judge_int(j_res.get("score", 5), 5, 1, 10)
    logic = _coerce_judge_int(j_res.get("logic", raw_score), raw_score, 1, 10)
    relevance = _coerce_judge_int(j_res.get("relevance", raw_score), raw_score, 1, 10)
    creativity = _coerce_judge_int(j_res.get("creativity", 3), 3, 1, 5)
    creativity_scaled = creativity * 2
    composite = round((raw_score + logic + relevance + creativity_scaled) / 4)

    return {
        "score": max(1, min(10, composite)),
        "raw_score": raw_score,
        "logic": logic,
        "relevance": relevance,
        "creativity": creativity,
        "reasoning": str(j_res.get("reasoning", "No reasoning provided.")),
    }


def post_modal_json(url, payload):
    try:
        response = requests.post(
            url,
            json=payload,
            headers=get_modal_proxy_auth_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except Exception:
        return {"error": GENERIC_MODAL_ERROR}


def build_scene_update(
    user_audio,
    user_text,
    chat_history,
    user_hp,
    opp_hp,
    opponent,
    topic,
    stance,
    speaker,
    dialogue,
    active_actor,
    opponent_pose,
    player_pose,
    verdict=None,
    opp_audio=None,
):
    display_name = opponent_name(opponent)
    return (
        user_audio,
        user_text,
        chat_history,
        user_hp,
        opp_hp,
        get_health_bar_html(user_hp, "You", True),
        get_health_bar_html(opp_hp, display_name, False),
        get_arena_html(
            user_hp=user_hp,
            opp_hp=opp_hp,
            opponent=opponent,
            topic=topic,
            stance=stance,
            speaker=speaker,
            dialogue=dialogue,
            active_actor=active_actor,
            opponent_pose=opponent_pose,
            player_pose=player_pose,
            verdict=verdict,
        ),
        opp_audio,
    )


def build_scene_error(user_audio, user_text, chat_history, user_hp, opp_hp, opponent, topic, stance, dialogue):
    return build_scene_update(
        user_audio,
        user_text,
        chat_history,
        user_hp,
        opp_hp,
        opponent,
        topic,
        stance,
        speaker="Advocate",
        dialogue=dialogue,
        active_actor="player",
        opponent_pose="thinking",
        player_pose="thinking",
    )


def transcribe_argument(audio_payload):
    if not audio_payload:
        return "", GENERIC_MODAL_ERROR

    temp_path = None
    if isinstance(audio_payload, str) and audio_payload.startswith("data:audio"):
        header, encoded = audio_payload.split(",", 1)
        mime = header.split(";", 1)[0].replace("data:", "")
        suffix = ".webm"
        if "wav" in mime:
            suffix = ".wav"
        elif "mp4" in mime or "m4a" in mime:
            suffix = ".m4a"
        elif "ogg" in mime:
            suffix = ".ogg"
        audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        audio_file.write(base64.b64decode(encoded))
        audio_file.close()
        audio_path = temp_path = audio_file.name
    else:
        audio_path = audio_payload

    try:
        with open(audio_path, "rb") as audio_file:
            response = requests.post(
                STT_URL,
                files={"file": (os.path.basename(audio_path), audio_file, "audio/webm")},
                headers=get_modal_proxy_auth_headers(),
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
        text = data.get("text", "").strip()
    except Exception:
        return "", GENERIC_MODAL_ERROR
    finally:
        if temp_path:
            try:
                os.remove(temp_path)
            except OSError:
                pass
    return text, ""


def synthesize_rebuttal_audio(text):
    if not text:
        return None

    try:
        response = requests.post(
            TTS_URL,
            json={"text": text},
            headers=get_modal_proxy_auth_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except Exception:
        return {"error": GENERIC_MODAL_ERROR}

    audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    audio_file.write(response.content)
    audio_file.close()
    return audio_file.name


def preview_player_argument(user_arg, topic, stance, opponent, user_hp, opp_hp):
    if not user_arg or not user_arg.strip():
        return gr.update()
    prompt = user_arg.strip()
    if len(prompt) > 140:
        prompt = prompt[:137].rstrip() + "..."
    return get_arena_html(
        user_hp=user_hp,
        opp_hp=opp_hp,
        opponent=opponent or "oscar_wilde",
        topic=topic,
        stance=stance,
        speaker="Advocate",
        dialogue=prompt,
        active_actor="player",
        player_pose="talking",
        opponent_pose="thinking",
    )


def start_debate(topic, stance, opponent):
    if not topic or not opponent:
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(value='<div class="error-text">Please enter a topic and select an opponent.</div>'),
            [],
            100,
            100,
            get_health_bar_html(100, "You", True),
            get_health_bar_html(100, opponent_name(opponent), False),
            "",
            None,
        )

    display_name = opponent_name(opponent)
    initial_chat = [
        {
            "role": "assistant",
            "content": (
                "**The Grand Tribunal begins.**\n\n"
                f"**Topic:** {topic}\n"
                f"**Your Stance:** {stance}\n"
                f"**Opponent:** {display_name}\n\n"
                "You have the floor. Present your opening argument."
            ),
        }
    ]
    return (
        gr.update(visible=False),
        gr.update(visible=True),
        gr.update(value=""),
        initial_chat,
        100,
        100,
        get_health_bar_html(100, "You", True),
        get_health_bar_html(100, display_name, False),
        get_arena_html(
            user_hp=100,
            opp_hp=100,
            opponent=opponent,
            topic=topic,
            stance=stance,
            speaker="Advocate",
            dialogue="The Grand Tribunal begins. Make your opening argument.",
            active_actor="player",
            player_pose="talking",
            opponent_pose="thinking",
            verdict=f"{display_name} awaits your opening argument.",
        ),
        None,
    )


def handle_turn(user_audio, user_text, topic, stance, opponent, chat_history, user_hp, opp_hp):
    display_name = opponent_name(opponent)
    typed_arg = clamp_argument(user_text)
    if not user_audio and not typed_arg:
        return build_scene_error(
            None,
            "",
            chat_history,
            user_hp,
            opp_hp,
            opponent,
            topic,
            stance,
            "State your argument when ready.",
        )

    if typed_arg:
        user_arg = typed_arg
    else:
        user_arg, transcription_error = transcribe_argument(user_audio)
        if transcription_error:
            return build_scene_error(
                None,
                "",
                chat_history,
                user_hp,
                opp_hp,
                opponent,
                topic,
                stance,
                "I could not transcribe that recording. Try again with a clearer argument.",
            )

        if looks_like_bad_transcript(user_arg):
            return build_scene_error(
                None,
                "",
                chat_history,
                user_hp,
                opp_hp,
                opponent,
                topic,
                stance,
                "That recording sounded like noise or a filler phrase. Please try again with a clearer argument.",
            )

    if looks_like_prompt_injection(user_arg):
        return build_scene_error(
            None,
            "",
            chat_history,
            user_hp,
            opp_hp,
            opponent,
            topic,
            stance,
            INVALID_ARGUMENT_MESSAGE,
        )

    if not user_arg:
        return build_scene_error(
            None,
            "",
            chat_history,
            user_hp,
            opp_hp,
            opponent,
            topic,
            stance,
            "I could not transcribe that recording. Try again with a clearer argument.",
        )

    chat_history.append({"role": "user", "content": user_arg})

    situation_prompt = (
        f"(Debate Topic: {topic}. The user is arguing {stance} this topic.)\n"
        f"User argues: {user_arg}\n"
        "Directly contradict and fiercely attack the core premise of the user's argument. "
        "Do not agree with them under any circumstances."
    )

    def run_judge_user():
        return post_modal_json(JUDGE_URL, {"topic": topic, "argument": user_arg})

    def run_character():
        return post_modal_json(CHARACTER_URL, {"character": opponent, "situation": situation_prompt})

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_judge = executor.submit(run_judge_user)
        future_char = executor.submit(run_character)
        j_res = future_judge.result()
        c_res = future_char.result()

    user_judge = summarize_judge_result(j_res)
    score = user_judge["score"]
    reasoning = user_judge["reasoning"]

    if "error" in c_res:
        opp_response = GENERIC_MODAL_ERROR
    else:
        opp_response = c_res.get("response", GENERIC_MODAL_ERROR)

    damage = calculate_damage(score)
    fatigue = calculate_fatigue(score)

    turn_msg = f"### Tribunal Verdict on Your Argument\n**Score: {score}/10** - *{reasoning}*\n\n"

    if damage > 0:
        opp_hp = max(0, opp_hp - damage)
        turn_msg += f"**Strike landed.** Dealt {damage} damage to {display_name}.\n\n"
    else:
        user_hp = max(0, user_hp - fatigue)
        turn_msg += f"**Mental fatigue.** You suffered {fatigue} self-inflicted damage.\n\n"

    if opp_hp == 0:
        turn_msg += f"**Victory.** {display_name} has been defeated."
        chat_history.append({"role": "assistant", "content": turn_msg})
        return build_scene_update(
            None,
            "",
            chat_history,
            user_hp,
            opp_hp,
            opponent,
            topic,
            stance,
            speaker="Advocate",
            dialogue=f"{display_name} has been defeated. The motion stands with you.",
            active_actor="player",
            opponent_pose="damage",
            player_pose="victory",
            verdict=f"Your score: {score}/10. Damage dealt: {damage}.",
        )
    if user_hp == 0:
        turn_msg += "**Defeat.** Your logic has crumbled."
        chat_history.append({"role": "assistant", "content": turn_msg})
        return build_scene_update(
            None,
            "",
            chat_history,
            user_hp,
            opp_hp,
            opponent,
            topic,
            stance,
            speaker="Advocate",
            dialogue="Your argument collapses under scrutiny.",
            active_actor="player",
            opponent_pose="victory",
            player_pose="damage",
            verdict=f"Your score: {score}/10. Fatigue suffered: {fatigue}.",
        )

    turn_msg += "---\n\n"

    def run_tts():
        return synthesize_rebuttal_audio(opp_response)

    def run_judge_opponent():
        return post_modal_json(JUDGE_URL, {"topic": topic, "argument": opp_response})

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_tts = executor.submit(run_tts)
        future_judge2 = executor.submit(run_judge_opponent)
        tts_res = future_tts.result()
        j_res2 = future_judge2.result()

    if isinstance(tts_res, dict) and "error" in tts_res:
        opp_audio = None
        opp_response_with_err = f"{opp_response}\n\n({GENERIC_MODAL_ERROR})"
    else:
        opp_audio = tts_res
        opp_response_with_err = opp_response

    opp_judge = summarize_judge_result(j_res2)
    opp_score = opp_judge["score"]
    opp_reasoning = opp_judge["reasoning"]

    turn_msg += f"### {display_name}'s Rebuttal\n\"{opp_response_with_err}\"\n\n"
    turn_msg += f"### Tribunal Verdict on Opponent\n**Score: {opp_score}/10** - *{opp_reasoning}*\n\n"

    opp_damage = calculate_damage(opp_score)
    opp_fatigue = calculate_fatigue(opp_score)

    if opp_damage > 0:
        user_hp = max(0, user_hp - opp_damage)
        turn_msg += f"**Counterstrike.** You took {opp_damage} damage from the retort."
    else:
        opp_hp = max(0, opp_hp - opp_fatigue)
        turn_msg += f"**Faulty premise.** {display_name} suffers {opp_fatigue} mental fatigue."

    if user_hp == 0:
        turn_msg += "\n\n**Defeat.** Your logic has crumbled."
        scene_speaker = display_name
        scene_dialogue = "A neat collapse. Even pessimism feels too generous."
        active_actor = "opponent"
        opponent_pose = "victory"
        player_pose = "damage"
    elif opp_hp == 0:
        turn_msg += f"\n\n**Victory.** {display_name} has been undone by the exchange."
        scene_speaker = "Advocate"
        scene_dialogue = f"{display_name} has been undone by the exchange."
        active_actor = "player"
        opponent_pose = "damage"
        player_pose = "victory"
    else:
        scene_speaker = display_name
        scene_dialogue = opp_response_with_err if opp_audio is None else opp_response
        active_actor = "opponent"
        opponent_pose = "talking" if opp_damage > 0 else "damage"
        player_pose = "damage" if opp_damage > 0 else "thinking"

    chat_history.append({"role": "assistant", "content": turn_msg})

    verdict = (
        f"You: {score}/10 | {display_name}: {opp_score}/10\n"
        f"Damage taken: {opp_damage if opp_damage > 0 else 0}\n"
        f"Damage dealt: {damage if damage > 0 else 0}"
    )

    return build_scene_update(
        None,
        "",
        chat_history,
        user_hp,
        opp_hp,
        opponent,
        topic,
        stance,
        speaker=scene_speaker,
        dialogue=scene_dialogue,
        active_actor=active_actor,
        opponent_pose=opponent_pose,
        player_pose=player_pose,
        verdict=verdict,
        opp_audio=opp_audio,
    )


# No fill_height — that was causing nested containers to grow and infinite scroll.
with gr.Blocks(elem_id="tribunal-app", css=CSS, theme=gr.themes.Soft()) as demo:
    topic_state = gr.State("")
    stance_state = gr.State("")
    opponent_state = gr.State("")
    user_hp_state = gr.State(100)
    opp_hp_state = gr.State(100)

    with gr.Column(visible=True, elem_id="landing-view") as setup_area:
        gr.HTML(
            f"""
            <header id="landing-header">
                <div id="landing-brand">
                    <img src="{LANDING_LOGO_DATA_URI}" alt="The Grand Tribunal">
                    <div id="landing-brand-title">THE GRAND TRIBUNAL</div>
                </div>
            </header>
            """
        )
        with gr.Column(elem_id="landing-stage"):
            with gr.Column(elem_id="docket-card"):
                with gr.Column(elem_id="docket-inner"):
                    gr.HTML('<div class="field-label">DEBATE TOPIC</div>')
                    topic_input = gr.Textbox(
                        label="Debate Topic",
                        placeholder="Enter the subject of your philosophical contention...",
                        lines=4,
                        show_label=False,
                        container=False,
                        elem_id="topic-input",
                    )
                    gr.HTML('<div class="field-label">YOUR STANCE</div>')
                    stance_input = gr.Dropdown(
                        choices=[("FOR", "For"), ("AGAINST", "Against")],
                        label="Your Stance",
                        value="For",
                        show_label=False,
                        container=False,
                        elem_id="stance-input",
                    )
                    gr.HTML('<div class="field-label">SELECT OPPONENT</div>')
                    opponent_input = gr.Dropdown(
                        choices=[
                            ("Oscar Wilde", "oscar_wilde"),
                            ("Nietzsche", "friedrich_nietzsche"),
                            ("Plato", "plato"),
                            ("Schopenhauer", "schopenhauer"),
                        ],
                        label="Select Opponent",
                        value="friedrich_nietzsche",
                        show_label=False,
                        container=False,
                        elem_id="opponent-input",
                    )
                    start_btn = gr.Button("ENTER THE TRIBUNAL ->", variant="secondary", elem_id="start-btn")
                    error_box = gr.HTML("", visible=False, elem_id="error-box")

    with gr.Column(visible=False, elem_classes="debate-shell") as debate_area:
        # Start empty — don't load 760px court scene on landing page.
        arena_html = gr.HTML("")
        with gr.Row(elem_classes=["hidden-runtime"]):
            user_health_html = gr.HTML(get_health_bar_html(100, "You", True))
            opp_health_html = gr.HTML(get_health_bar_html(100, "Opponent", False))

        chatbot = gr.Chatbot(label="Tribunal Transcript", height=500, elem_id="tribunal-chat", visible=False)
        opponent_voice = gr.Audio(label="Opponent Voice", autoplay=True, visible=True, elem_id="hidden-audio")
        user_audio = gr.Textbox(value="", elem_classes=["hidden-runtime"], elem_id="voice-payload")

        with gr.Row(elem_classes=["submit-row", "argument-dock"]):
            gr.HTML(
                """
                <div class="mic-panel">
                    <button type="button" id="mic-start">RECORD</button>
                    <button type="button" id="mic-stop" disabled>STOP</button>
                    <span class="mic-status" id="mic-status">Ready</span>
                    <audio class="mic-playback" id="mic-playback" controls></audio>
                </div>
                """,
                elem_classes=["mic-container-block"],
                scale=1,
                min_width=170,
            )
            user_text = gr.Textbox(
                show_label=False,
                placeholder="Optional typed fallback while testing...",
                lines=1,
                max_lines=1,
                scale=7,
            )
            submit_btn = gr.Button("SUBMIT ARGUMENT", variant="primary", scale=2)

        gr.HTML(
            '<div class="voice-hint">USE THE RECORDER, STOP WHEN FINISHED, THEN SUBMIT YOUR ARGUMENT.</div>'
        )

    start_btn.click(
        fn=start_debate,
        inputs=[topic_input, stance_input, opponent_input],
        outputs=[
            setup_area,
            debate_area,
            error_box,
            chatbot,
            user_hp_state,
            opp_hp_state,
            user_health_html,
            opp_health_html,
            arena_html,
            opponent_voice,
        ],
    ).then(
        fn=lambda t, s, o: (t, s, o),
        inputs=[topic_input, stance_input, opponent_input],
        outputs=[topic_state, stance_state, opponent_state],
    )

    submit_btn.click(
        fn=handle_turn,
        inputs=[
            user_audio,
            user_text,
            topic_state,
            stance_state,
            opponent_state,
            chatbot,
            user_hp_state,
            opp_hp_state,
        ],
        outputs=[
            user_audio,
            user_text,
            chatbot,
            user_hp_state,
            opp_hp_state,
            user_health_html,
            opp_health_html,
            arena_html,
            opponent_voice,
        ],
    )

    user_text.submit(
        fn=handle_turn,
        inputs=[
            user_audio,
            user_text,
            topic_state,
            stance_state,
            opponent_state,
            chatbot,
            user_hp_state,
            opp_hp_state,
        ],
        outputs=[
            user_audio,
            user_text,
            chatbot,
            user_hp_state,
            opp_hp_state,
            user_health_html,
            opp_health_html,
            arena_html,
            opponent_voice,
        ],
    )

    user_text.change(
        fn=preview_player_argument,
        inputs=[
            user_text,
            topic_state,
            stance_state,
            opponent_state,
            user_hp_state,
            opp_hp_state,
        ],
        outputs=[arena_html],
        show_progress="hidden",
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", "7860")),
        allowed_paths=["."],
        css=CSS,
        theme=gr.themes.Soft(),
        js=CUSTOM_JS,
    )
