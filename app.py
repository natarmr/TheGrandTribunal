import html
import base64
import os
import random
import tempfile
import concurrent.futures

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
    --parchment: #efe2c6;
    --wine: #611f31;
    --vermilion: #b44633;
    --gold: #c99a3e;
    --jade: #2f8c68;
    --smoke: #27313c;
    --line: rgba(32, 27, 20, 0.18);
}

.gradio-container {
    max-width: none !important;
    background:
        linear-gradient(115deg, rgba(17, 19, 24, 0.92), rgba(55, 30, 35, 0.82)),
        repeating-linear-gradient(90deg, rgba(255,255,255,0.035) 0, rgba(255,255,255,0.035) 1px, transparent 1px, transparent 30px),
        #16191f !important;
    color: var(--paper);
    font-family: Inter, system-ui, sans-serif;
}

#tribunal-app {
    max-width: 1380px;
    margin: 0 auto;
    padding: 18px clamp(12px, 2vw, 28px) 28px;
}

#tribunal-app .contain,
#tribunal-app .form,
#tribunal-app .block {
    border-radius: 6px !important;
}

#tribunal-app label,
#tribunal-app .label-wrap span {
    color: #f2dfb7 !important;
    font-weight: 800 !important;
    letter-spacing: 0 !important;
}

#tribunal-app textarea,
#tribunal-app input,
#tribunal-app select {
    background: rgba(247, 239, 224, 0.96) !important;
    color: var(--ink) !important;
    border: 1px solid rgba(201, 154, 62, 0.45) !important;
    border-radius: 6px !important;
}

#tribunal-app .wrap.svelte-1ipelgc {
    gap: 14px;
}

#landing-view {
    position: relative;
    min-height: min(720px, calc(100vh - 42px));
    display: grid !important;
    grid-template-columns: minmax(360px, 0.92fr) minmax(420px, 0.72fr) !important;
    align-items: center !important;
    gap: clamp(18px, 4vw, 62px) !important;
    overflow: hidden;
    border: 1px solid rgba(201, 154, 62, 0.34);
    background:
        radial-gradient(circle at 72% 20%, rgba(201, 154, 62, 0.12), transparent 28%),
        linear-gradient(90deg, rgba(16, 18, 22, 0.96), rgba(31, 22, 22, 0.84) 54%, rgba(12, 13, 16, 0.9)),
        #171a20;
    box-shadow: 0 24px 60px rgba(0, 0, 0, 0.35);
    padding: clamp(22px, 5vw, 72px);
}

#landing-view.hide,
#landing-view.hidden,
#landing-view[hidden],
#landing-view[style*="display: none"],
#landing-view[style*="visibility: hidden"],
#landing-view[aria-hidden="true"] {
    display: none !important;
    min-height: 0 !important;
    height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    border: 0 !important;
    overflow: hidden !important;
}

#landing-view:after {
    content: "";
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    height: 86px;
    background: linear-gradient(180deg, transparent, rgba(10, 11, 14, 0.84));
    pointer-events: none;
}

.hero-copy {
    position: relative;
    z-index: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-width: 0;
}

#landing-view > * {
    min-width: 0 !important;
}

.kicker,
.stage-kicker {
    color: #e9bd69;
    font-size: 0.78rem;
    font-weight: 900;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.hero-copy h1 {
    margin: 10px 0 10px;
    color: #fff7e8;
    font: 900 clamp(3.15rem, 7vw, 6.6rem)/0.9 Cinzel, serif;
    letter-spacing: 0;
    max-width: 760px;
}

.hero-copy p {
    max-width: 560px;
    margin: 0;
    color: rgba(247, 239, 224, 0.82);
    font-size: clamp(0.98rem, 1.6vw, 1.18rem);
    line-height: 1.55;
}

.hero-statline {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 24px;
}

.hero-statline span {
    border: 1px solid rgba(201, 154, 62, 0.42);
    background: rgba(17, 19, 24, 0.64);
    color: #f5d99b;
    border-radius: 999px;
    padding: 7px 12px;
    font-size: 0.78rem;
    font-weight: 800;
}

.debate-shell {
    margin-top: 14px;
    padding: clamp(12px, 2vw, 22px);
    border: 1px solid rgba(201, 154, 62, 0.3);
    background: rgba(17, 19, 24, 0.74);
}

.setup-panel {
    position: relative;
    z-index: 1;
    width: 100%;
    padding: clamp(16px, 2.3vw, 26px);
    border: 1px solid rgba(201, 154, 62, 0.42);
    border-radius: 6px;
    background:
        linear-gradient(180deg, rgba(247, 239, 224, 0.13), rgba(247, 239, 224, 0.045)),
        rgba(11, 12, 15, 0.72);
    box-shadow: 0 18px 48px rgba(0, 0, 0, 0.26);
    backdrop-filter: blur(10px);
}

.setup-title,
.panel-title {
    margin: 0 0 12px;
    color: #fff2d8;
    font: 800 1.02rem/1.2 Cinzel, serif;
}

.setup-subtitle {
    margin: -4px 0 16px;
    color: rgba(247, 239, 224, 0.68);
    font-size: 0.86rem;
    line-height: 1.4;
}

.opponent-roster {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    margin-top: 10px;
}

.opponent-chip {
    min-height: 118px;
    overflow: hidden;
    border: 1px solid rgba(201, 154, 62, 0.3);
    background: linear-gradient(180deg, rgba(239, 226, 198, 0.1), rgba(10, 11, 14, 0.4));
    border-radius: 6px;
    position: relative;
}

.opponent-chip img {
    width: 100%;
    height: 78px;
    object-fit: cover;
    object-position: top center;
    filter: saturate(0.92) contrast(1.05);
}

.opponent-chip strong,
.opponent-chip span {
    display: block;
    padding: 0 10px;
}

.opponent-chip strong {
    margin-top: 7px;
    color: #fff5de;
    font-size: 0.84rem;
}

.opponent-chip span {
    color: rgba(247, 239, 224, 0.68);
    font-size: 0.72rem;
    padding-bottom: 8px;
}

.setup-panel .form,
.setup-panel .block {
    background: transparent !important;
}

.setup-panel .radio-group {
    gap: 8px !important;
}

.arena-stage {
    display: grid;
    grid-template-columns: minmax(160px, 0.7fr) minmax(220px, 1fr) minmax(160px, 0.7fr);
    min-height: 360px;
    border: 1px solid rgba(201, 154, 62, 0.36);
    background:
        linear-gradient(180deg, rgba(29, 33, 39, 0.74), rgba(7, 8, 10, 0.9)),
        repeating-linear-gradient(0deg, rgba(239, 226, 198, 0.08) 0, rgba(239, 226, 198, 0.08) 1px, transparent 1px, transparent 26px);
    overflow: hidden;
    border-radius: 6px;
}

.combatant {
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    min-width: 0;
}

.combatant.user {
    padding: 22px;
    background: linear-gradient(155deg, rgba(47, 140, 104, 0.28), transparent 58%);
}

.combatant.opponent {
    padding: 0 0 0 18px;
    align-items: flex-end;
    background: linear-gradient(205deg, rgba(180, 70, 51, 0.24), transparent 58%);
}

.speaker-mark {
    width: min(72%, 230px);
    aspect-ratio: 1;
    display: grid;
    place-items: center;
    border: 2px solid rgba(233, 189, 105, 0.45);
    background: rgba(17, 19, 24, 0.52);
    color: #f3dfb8;
    font: 900 clamp(3rem, 8vw, 6rem)/1 Cinzel, serif;
}

.combatant img {
    width: min(100%, 370px);
    max-height: 360px;
    object-fit: contain;
    object-position: bottom right;
    filter: drop-shadow(-16px 20px 22px rgba(0, 0, 0, 0.48));
}

.nameplate {
    position: relative;
    z-index: 1;
    width: min(100%, 300px);
    margin-top: 12px;
    padding: 10px 12px;
    border-top: 2px solid rgba(201, 154, 62, 0.6);
    background: rgba(8, 9, 12, 0.72);
}

.nameplate strong {
    display: block;
    color: #fff7e8;
    font: 800 1rem/1.1 Cinzel, serif;
}

.nameplate span {
    color: rgba(247, 239, 224, 0.68);
    font-size: 0.76rem;
}

.topic-docket {
    padding: 26px 18px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    background: linear-gradient(180deg, rgba(239, 226, 198, 0.13), rgba(17, 19, 24, 0));
    min-width: 0;
}

.topic-docket h2 {
    margin: 10px 0 6px;
    color: #fff7e8;
    font: 800 clamp(1.4rem, 3vw, 2.4rem)/1.02 Cinzel, serif;
    letter-spacing: 0;
    overflow-wrap: anywhere;
}

.topic-docket p {
    margin: 0;
    color: rgba(247, 239, 224, 0.72);
    line-height: 1.45;
    overflow-wrap: anywhere;
}

.stance-pill {
    margin-top: 14px;
    padding: 7px 12px;
    border: 1px solid rgba(201, 154, 62, 0.45);
    color: #f5d99b;
    font-weight: 900;
    border-radius: 999px;
    background: rgba(17, 19, 24, 0.48);
}

.vitals-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 12px;
}

.health-card {
    padding: 11px;
    border: 1px solid rgba(201, 154, 62, 0.3);
    background: rgba(9, 10, 13, 0.66);
    border-radius: 6px;
}

.health-card.right {
    text-align: right;
}

.health-label {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 8px;
    color: #fff1d5;
    font-weight: 900;
    font-size: 0.88rem;
}

.health-card.right .health-label {
    flex-direction: row-reverse;
}

.health-track {
    height: 22px;
    overflow: hidden;
    border: 2px solid rgba(247, 239, 224, 0.18);
    background: #08090b;
    border-radius: 3px;
}

.health-fill {
    height: 100%;
    min-width: 0;
    transition: width 0.35s ease;
    background: linear-gradient(90deg, var(--jade), #9ed66f);
}

.health-fill.warning {
    background: linear-gradient(90deg, #cc7a2f, #f0bf5b);
}

.health-fill.danger {
    background: linear-gradient(90deg, #9d2932, #e35d45);
}

#tribunal-chat {
    border: 1px solid rgba(201, 154, 62, 0.34);
    background: rgba(247, 239, 224, 0.94);
    border-radius: 6px;
}

#tribunal-chat .message {
    border-radius: 6px !important;
}

#tribunal-chat .bot {
    background: #fff8eb !important;
    color: var(--ink) !important;
    border: 1px solid rgba(97, 31, 49, 0.16) !important;
}

#tribunal-chat .user {
    background: #e8f2ec !important;
    color: var(--ink) !important;
    border: 1px solid rgba(47, 140, 104, 0.18) !important;
}

.submit-row {
    align-items: end;
}

#submit-argument {
    min-height: 96px;
}

#voice-recorder {
    min-height: 96px;
}

#tribunal-app button.primary {
    background: linear-gradient(180deg, #d4a34b, #a7612f) !important;
    color: #151312 !important;
    border: 1px solid rgba(255, 246, 223, 0.24) !important;
    font-weight: 900 !important;
    border-radius: 6px !important;
    height: 52px !important;
    min-height: 52px !important;
}

#tribunal-app button.secondary {
    border-radius: 6px !important;
}

.error-text {
    color: #ffd08a;
    font-weight: 800;
}

.debate-shell {
    margin-top: 0;
    padding: 0;
    border: 1px solid rgba(245, 197, 79, 0.42);
    background: #06070a;
    overflow: hidden;
}

#court-scene {
    position: relative;
    min-height: min(760px, calc(100vh - 84px));
    overflow: hidden;
    border-radius: 6px;
    background:
        linear-gradient(180deg, rgba(255,255,255,0.06), transparent 26%),
        var(--court-bg) center / cover no-repeat,
        #b18115;
}

#court-scene:before {
    content: "";
    position: absolute;
    inset: 0;
    background:
        linear-gradient(90deg, rgba(0,0,0,0.22), transparent 32%, rgba(0,0,0,0.1)),
        repeating-linear-gradient(0deg, rgba(0,0,0,0.055) 0, rgba(0,0,0,0.055) 1px, transparent 1px, transparent 5px);
    pointer-events: none;
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
    align-items: start;
}

.court-docket {
    min-width: 0;
    padding: 10px 14px;
    border: 2px solid rgba(255, 232, 142, 0.72);
    background: rgba(10, 12, 18, 0.72);
    color: #fff4cf;
    text-align: center;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.26);
}

.court-docket strong,
.court-docket span {
    display: block;
    overflow-wrap: anywhere;
}

.court-docket strong {
    font: 900 0.78rem/1.1 Inter, sans-serif;
    color: #ffd56e;
    text-transform: uppercase;
}

.court-docket span {
    margin-top: 4px;
    font: 800 clamp(0.88rem, 1.7vw, 1.2rem)/1.15 Cinzel, serif;
}

.court-fighter {
    padding: 10px 12px 12px;
    border: 2px solid rgba(255, 232, 142, 0.72);
    background: rgba(8, 11, 17, 0.78);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.24);
}

.court-fighter.right {
    text-align: right;
}

.court-fighter-label {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    color: #fff7de;
    font-weight: 900;
    font-size: 0.9rem;
    text-transform: uppercase;
}

.court-fighter.right .court-fighter-label {
    flex-direction: row-reverse;
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

.court-hp-fill.warning {
    background: linear-gradient(90deg, #d98520, #f6d46a);
}

.court-hp-fill.danger {
    background: linear-gradient(90deg, #b51f32, #ff785e);
}

.court-character {
    position: absolute;
    z-index: 2;
    left: clamp(34px, 8vw, 150px);
    bottom: 188px;
    width: min(50vw, 620px);
    max-height: calc(100% - 285px);
    object-fit: contain;
    object-position: bottom left;
    filter: drop-shadow(20px 20px 18px rgba(0, 0, 0, 0.45));
    image-rendering: auto;
}

.court-character.wide {
    width: min(46vw, 470px);
}

.court-character.tall {
    width: min(43vw, 560px);
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
    border: 1px solid rgba(255, 255, 255, 0.12);
    background: rgba(11, 14, 22, 0.72);
    color: #e0d0b0;
    font-family: monospace;
    font-size: 0.8rem;
    line-height: 1.4;
    border-radius: 4px;
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
    background:
        linear-gradient(90deg, rgba(3, 12, 26, 0.94), rgba(10, 17, 30, 0.82)),
        repeating-linear-gradient(45deg, rgba(255,255,255,0.04) 0, rgba(255,255,255,0.04) 1px, transparent 1px, transparent 6px);
    color: white;
    box-shadow: 0 -20px 50px rgba(0, 0, 0, 0.36);
}

.dialogue-name {
    position: absolute;
    top: -28px;
    left: clamp(24px, 8vw, 150px);
    min-width: 210px;
    padding: 8px 28px 9px;
    color: white;
    font: 700 1.55rem/1 Cinzel, serif;
    background: linear-gradient(180deg, #3c9bc3, #257fa7);
    border: 2px solid white;
    clip-path: polygon(8% 0, 92% 0, 100% 50%, 92% 100%, 8% 100%, 0 50%);
    text-align: center;
    text-shadow: 0 2px 0 rgba(0, 0, 0, 0.2);
}

.dialogue-line {
    margin: 0;
    max-width: 1120px;
    font: 500 clamp(1.65rem, 3.7vw, 2.9rem)/1.2 Georgia, "Times New Roman", serif;
    color: #fff;
    text-shadow: 0 2px 0 rgba(0, 0, 0, 0.42);
}



.argument-dock {
    padding: 10px 12px 12px;
    background: #080a0f;
    border-top: 1px solid rgba(255, 232, 142, 0.28);
}

.voice-hint {
    padding: 8px 0;
    background: transparent;
    color: rgba(255, 255, 255, 0.38) !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.mic-recorder {
    padding: 12px;
    background: #080a0f;
    border-top: 1px solid rgba(255, 232, 142, 0.28);
}

.mic-panel {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: nowrap;
    padding: 0;
    height: 52px;
    box-sizing: border-box;
    background: transparent;
    border: none;
}

.mic-panel button {
    height: 36px;
    min-height: 36px !important;
    padding: 0 16px;
    border: 1px solid rgba(255, 246, 223, 0.24);
    border-radius: 6px;
    background: linear-gradient(180deg, #d4a34b, #a7612f);
    color: #151312;
    font-weight: 900;
    cursor: pointer;
}

.mic-panel button:disabled {
    cursor: not-allowed;
    opacity: 0.5;
}

.mic-container-block {
    padding: 0 !important;
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    min-width: 180px !important;
}

#mic-status,
.mic-playback {
    display: none !important;
}

.argument-dock textarea {
    height: 52px !important;
    min-height: 52px !important;
    resize: none !important;
    overflow-y: auto !important;
}

.hidden-runtime {
    display: none !important;
}

#hidden-audio {
    position: absolute !important;
    opacity: 0 !important;
    pointer-events: none !important;
    width: 1px !important;
    height: 1px !important;
    overflow: hidden !important;
    z-index: -9999 !important;
}

html,
body {
    margin: 0 !important;
    padding: 0 !important;
    width: 100%;
    min-height: 100%;
    overflow-x: hidden;
    background: #111111 !important;
}

.gradio-container {
    min-height: 100vh !important;
    padding: 0 !important;
    background: #111111 !important;
}

#tribunal-app {
    max-width: none !important;
    margin: 0 !important;
    padding: 0 !important;
    min-height: 100vh;
}

#tribunal-app .wrap {
    gap: 14px;
}

#landing-view {
    min-height: 100vh !important;
    padding: 0 !important;
    gap: 0 !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden;
    border: 0 !important;
    border-radius: 0 !important;
    background:
        linear-gradient(180deg, rgba(18, 18, 18, 0.98), rgba(15, 15, 15, 0.98)),
        #111111 !important;
    box-shadow: none !important;
}

#landing-view .wrap {
    gap: 0 !important;
}

#landing-header {
    height: 90px;
    flex: 0 0 auto;
    display: flex;
    align-items: center;
    padding: 0 clamp(28px, 5vw, 92px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.12);
    box-shadow:
        inset 0 -1px 0 rgba(255, 255, 255, 0.03),
        0 1px 0 rgba(255, 255, 255, 0.04);
    background: #121212;
}

#landing-brand {
    display: flex;
    align-items: center;
    gap: 18px;
    min-width: 0;
}

#landing-brand img {
    display: block;
    width: 42px;
    height: 42px;
    object-fit: contain;
    flex: 0 0 auto;
}

#landing-brand-title {
    color: #d6d0c6;
    font-family: Cinzel, serif;
    font-size: clamp(1.9rem, 3vw, 3.1rem);
    font-weight: 700;
    line-height: 1;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    white-space: nowrap;
}

#landing-stage {
    flex: 1 1 auto;
    display: grid;
    place-items: center;
    padding: 82px clamp(18px, 3.8vw, 56px) 60px;
}

#landing-stage .wrap {
    gap: 0 !important;
}

#docket-card {
    position: relative;
    width: min(92vw, 1440px);
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 10px;
    background:
        linear-gradient(180deg, rgba(28, 28, 28, 0.99), rgba(22, 22, 22, 0.99)),
        #171717;
    box-shadow: 0 22px 60px rgba(0, 0, 0, 0.45);
    overflow: hidden;
    padding: 48px 0 44px;
}

#docket-card::before {
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    background:
        radial-gradient(circle at 50% 0%, rgba(255, 255, 255, 0.04), transparent 42%),
        linear-gradient(180deg, rgba(255, 255, 255, 0.02), transparent 18%);
}

#docket-inner {
    position: relative;
    z-index: 1;
    width: min(58vw, 860px);
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 0;
}

.field-label {
    margin: 0 0 14px;
    color: rgba(255, 255, 255, 0.5);
    font-family: "Space Mono", monospace;
    font-size: 0.8rem;
    font-weight: 700;
    line-height: 1;
    letter-spacing: 0.34em;
    text-transform: uppercase;
}

#topic-input,
#stance-input,
#opponent-input,
#start-btn {
    width: 100%;
}

#topic-input {
    margin: 0 0 26px;
}

#stance-input {
    margin: 0 0 22px;
}

#opponent-input {
    margin: 0 0 58px;
}

#topic-input textarea,
#stance-input input,
#stance-input button,
#stance-input [role="combobox"],
#opponent-input input,
#opponent-input button,
#opponent-input [role="combobox"] {
    width: 100% !important;
    background: #111111 !important;
    color: #ddd6ca !important;
    border: 1px solid rgba(255, 255, 255, 0.16) !important;
    border-radius: 8px !important;
    box-shadow: none !important;
    outline: none !important;
}

#topic-input textarea {
    min-height: 146px !important;
    padding: 20px 20px 18px !important;
    color: #dcdcdc !important;
    font-family: Inter, system-ui, sans-serif !important;
    font-size: 1.02rem !important;
    line-height: 1.4 !important;
}

#topic-input textarea::placeholder {
    color: rgba(255, 255, 255, 0.78) !important;
    font-weight: 700 !important;
}

#stance-input input,
#stance-input button,
#stance-input [role="combobox"] {
    min-height: 76px !important;
    padding: 0 18px !important;
    color: #e3dccf !important;
    font-family: Cinzel, serif !important;
    font-size: clamp(1.55rem, 2vw, 1.9rem) !important;
    font-weight: 500 !important;
    letter-spacing: 0 !important;
    text-transform: uppercase !important;
}

#opponent-input input,
#opponent-input button,
#opponent-input [role="combobox"] {
    min-height: 100px !important;
    padding: 0 18px !important;
    color: #e3dccf !important;
    font-family: Cinzel, serif !important;
    font-size: clamp(1.15rem, 1.7vw, 1.45rem) !important;
    font-weight: 500 !important;
    letter-spacing: 0 !important;
}

#stance-input *,
#opponent-input * {
    background: transparent !important;
}

ul[role="listbox"] {
    background: #151515 !important;
    border: 1px solid rgba(255, 255, 255, 0.16) !important;
    border-radius: 8px !important;
    box-shadow: 0 18px 44px rgba(0, 0, 0, 0.5) !important;
    opacity: 1 !important;
    backdrop-filter: none !important;
}

li[data-testid="dropdown-option"] {
    color: #e2dbcf !important;
    font-family: Cinzel, serif !important;
    font-size: 1.2rem !important;
    line-height: 1.2 !important;
    padding: 16px 20px !important;
    opacity: 1 !important;
}

#tribunal-app [role="listbox"],
#tribunal-app [role="option"],
#tribunal-app [data-testid="dropdown-option"] {
    background-clip: padding-box !important;
}

li[data-testid="dropdown-option"]:hover,
li[data-testid="dropdown-option"][aria-selected="true"] {
    background: rgba(201, 154, 62, 0.18) !important;
}

#start-btn {
    margin-top: 0;
}

#start-btn button {
    width: 100% !important;
    min-height: 104px !important;
    border: 2px solid rgba(201, 154, 62, 0.36) !important;
    border-radius: 0 !important;
    background: transparent !important;
    color: #d7ac43 !important;
    font-family: Cinzel, serif !important;
    font-size: clamp(1.35rem, 2vw, 1.8rem) !important;
    font-weight: 700 !important;
    letter-spacing: 0.22em !important;
    text-transform: uppercase !important;
    box-shadow:
        inset 0 0 0 1px rgba(201, 154, 62, 0.12),
        0 0 0 1px rgba(201, 154, 62, 0.12);
}

#start-btn button:hover {
    border-color: rgba(233, 189, 105, 0.68) !important;
    box-shadow:
        inset 0 0 0 1px rgba(233, 189, 105, 0.18),
        0 0 22px rgba(233, 189, 105, 0.12);
}

#error-box {
    min-height: 0 !important;
}

@media (max-width: 900px) {
    #landing-view,
    .arena-stage,
    .court-hud {
        grid-template-columns: 1fr !important;
    }

    #landing-view {
        min-height: 100vh !important;
        padding: 0 !important;
        gap: 0 !important;
    }

    #landing-header {
        height: 80px;
        padding: 0 18px;
    }

    #landing-brand {
        gap: 12px;
    }

    #landing-brand img {
        width: 36px;
        height: 36px;
    }

    #landing-stage {
        padding: 32px 12px 20px;
    }

    #docket-card {
        width: 100%;
        padding: 28px 0 24px;
        border-radius: 8px;
    }

    #docket-inner {
        width: min(100%, 760px);
        padding: 0 16px;
    }

    #topic-input {
        margin-bottom: 18px;
    }

    #stance-input {
        margin-bottom: 16px;
    }

    #opponent-input {
        margin-bottom: 28px;
    }

    #topic-input textarea {
        min-height: 118px !important;
        padding: 16px !important;
        font-size: 0.95rem !important;
    }

    #stance-input input,
    #stance-input button,
    #stance-input [role="combobox"] {
        min-height: 64px !important;
        font-size: 1.3rem !important;
    }

    #opponent-input input,
    #opponent-input button,
    #opponent-input [role="combobox"] {
        min-height: 82px !important;
        font-size: 1.05rem !important;
    }

    #start-btn button {
        min-height: 88px !important;
        font-size: 1.05rem !important;
    }

    .opponent-roster,
    .vitals-grid {
        grid-template-columns: 1fr;
    }

    .combatant.opponent {
        align-items: center;
        padding: 12px 18px 0;
    }

    .combatant.user {
        align-items: center;
        text-align: center;
    }

    #court-scene {
        min-height: 720px;
    }

    .court-hud {
        position: relative;
        inset: auto;
        padding: 12px;
    }

    .court-character {
        left: 50%;
        transform: translateX(-50%);
        bottom: 215px;
        width: min(72vw, 310px);
        max-height: 390px;
    }

    .court-verdict-strip {
        display: none;
    }

    .dialogue-box {
        min-height: 190px;
        padding: 32px 20px 24px;
    }

    .dialogue-name {
        left: 18px;
        min-width: 160px;
        font-size: 1.1rem;
    }

    .dialogue-line {
        font-size: 1.45rem;
    }
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


def get_roster_html():
    chips = []
    for data in OPPONENTS.values():
        chips.append(
            f"""
            <div class="opponent-chip">
                <img src="{file_url(data["image"])}" alt="{html.escape(data["name"])}">
                <strong>{html.escape(data["name"])}</strong>
                <span>{html.escape(data["epithet"])}</span>
                <span>{html.escape(data["school"])}</span>
            </div>
            """
        )
    return f"""<div class="opponent-roster">{''.join(chips)}</div>"""


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
    sprite_path = get_sprite_path(opponent, opponent_pose)
    player_sprite_path = get_player_sprite_path(player_pose)
    bg_path = "sprites/opp_background.jpg"
    if active_actor == "opponent":
        active_sprite_path = sprite_path
        active_alt = data["name"]
        sprite_size_class = data.get("sprite_scale", "tall")
    else:
        active_sprite_path = player_sprite_path
        active_alt = "Advocate"
        sprite_size_class = "player"
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


def post_modal_json(url, payload):
    try:
        response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
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
        response = requests.post(TTS_URL, json={"text": text}, timeout=REQUEST_TIMEOUT)
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
            get_arena_html(
                user_hp=100,
                opp_hp=100,
                opponent=opponent or "oscar_wilde",
                topic=topic or "",
                stance=stance or "For",
                speaker="Advocate",
                dialogue="Before the court can convene, enter a motion and choose your opponent.",
                active_actor="player",
                player_pose="thinking",
            ),
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

    situation_prompt = f"(Debate Topic: {topic}. The user is arguing {stance} this topic.)\nUser argues: {user_arg}\nDirectly contradict and fiercely attack the core premise of the user's argument. Do not agree with them under any circumstances."

    # Parallelize Phase 1: User Argument Evaluation & Opponent Response Generation
    def run_judge_user():
        return post_modal_json(JUDGE_URL, {"topic": topic, "argument": user_arg})

    def run_character():
        return post_modal_json(CHARACTER_URL, {"character": opponent, "situation": situation_prompt})

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_judge = executor.submit(run_judge_user)
        future_char = executor.submit(run_character)
        j_res = future_judge.result()
        c_res = future_char.result()

    if "error" in j_res:
        score, reasoning = 5, "Tribunal failed to evaluate the argument."
    else:
        score = int(j_res.get("score", 5))
        reasoning = j_res.get("reasoning", "No reasoning provided.")

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

    # Parallelize Phase 2: Rebuttal TTS Synthesis & Rebuttal Evaluation
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

    if "error" in j_res2:
        opp_score, opp_reasoning = 5, "Tribunal failed to evaluate the rebuttal."
    else:
        opp_score = int(j_res2.get("score", 5))
        opp_reasoning = j_res2.get("reasoning", "No reasoning provided.")

    turn_msg += f"### {display_name}'s Rebuttal\n\"{opp_response_with_err}\"\n\n"

    opp_damage = calculate_damage(opp_score)
    opp_fatigue = calculate_fatigue(opp_score)

    turn_msg += f"### Tribunal Verdict on Opponent\n**Score: {opp_score}/10** - *{opp_reasoning}*\n\n"

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
        arena_html = gr.HTML(get_arena_html())
        with gr.Row(elem_classes=["vitals-grid", "hidden-runtime"]):
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
            """
            <div class="voice-hint">USE THE FAST RECORDER BELOW, STOP WHEN FINISHED, THEN SUBMIT YOUR ARGUMENT.</div>
            """
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
    demo.launch(allowed_paths=["."], css=CSS, theme=gr.themes.Soft(), js=CUSTOM_JS)
