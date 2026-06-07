import html
import random

import gradio as gr
import requests


JUDGE_URL = "https://ramratanpadhy59--grand-tribunal-inference-api.modal.run/judge"
CHARACTER_URL = "https://ramratanpadhy59--grand-tribunal-inference-api.modal.run/character"

OPPONENTS = {
    "oscar_wilde": {
        "name": "Oscar Wilde",
        "image": "oscar_wilde.png",
        "sprite": "wilde",
        "epithet": "The Velvet Saboteur",
        "school": "Aesthetic wit and elegant contradiction",
    },
    "friedrich_nietzsche": {
        "name": "Friedrich Nietzsche",
        "image": "nietzsche.png",
        "sprite": "nietzsche",
        "epithet": "The Hammer of Certainty",
        "school": "Genealogy, will, and merciless revaluation",
    },
    "plato": {
        "name": "Plato",
        "image": "socrates.png",
        "sprite": "plato",
        "epithet": "The Keeper of Forms",
        "school": "Dialectic, justice, and ideal truth",
    },
    "schopenhauer": {
        "name": "Arthur Schopenhauer",
        "image": "schopenhauer.png",
        "sprite": "schopenhauer",
        "epithet": "The Pessimist Laureate",
        "school": "Will, suffering, and the limits of desire",
    },
}


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

#landing-hero {
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

#landing-hero:after {
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

#landing-hero > * {
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

#tribunal-app button.primary {
    background: linear-gradient(180deg, #d4a34b, #a7612f) !important;
    color: #151312 !important;
    border: 1px solid rgba(255, 246, 223, 0.24) !important;
    font-weight: 900 !important;
    border-radius: 6px !important;
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
    min-height: min(760px, calc(100vh - 120px));
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
    padding: 8px 10px 10px;
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
    font-size: 0.78rem;
    text-transform: uppercase;
}

.court-fighter.right .court-fighter-label {
    flex-direction: row-reverse;
}

.court-hp-track {
    height: 12px;
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
    left: clamp(24px, 10vw, 170px);
    bottom: 212px;
    width: min(34vw, 430px);
    max-height: calc(100% - 220px);
    object-fit: contain;
    object-position: bottom left;
    filter: drop-shadow(20px 20px 18px rgba(0, 0, 0, 0.45));
    image-rendering: auto;
}

.court-character.wide {
    width: min(28vw, 330px);
}

.court-player-badge {
    position: absolute;
    z-index: 2;
    right: clamp(18px, 5vw, 88px);
    bottom: 214px;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 9px 12px;
    border: 2px solid rgba(255, 232, 142, 0.62);
    background: rgba(9, 12, 18, 0.68);
    color: #fff7de;
    font-weight: 900;
    text-transform: uppercase;
}

.court-player-badge img {
    width: 72px;
    height: 72px;
    object-fit: contain;
    image-rendering: pixelated;
}

.court-verdict-strip {
    position: absolute;
    z-index: 3;
    right: 24px;
    bottom: 198px;
    max-width: min(420px, 42vw);
    padding: 10px 13px;
    border-left: 4px solid #ffd45f;
    background: rgba(11, 14, 22, 0.82);
    color: #f8e5af;
    font-size: 0.86rem;
    line-height: 1.35;
}

.dialogue-box {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 5;
    min-height: 186px;
    padding: 34px clamp(24px, 8vw, 160px) 28px;
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
    font: 500 clamp(1.8rem, 4vw, 3.1rem)/1.22 Georgia, "Times New Roman", serif;
    color: #fff;
    text-shadow: 0 2px 0 rgba(0, 0, 0, 0.42);
}

.dialogue-next {
    position: absolute;
    right: clamp(22px, 5vw, 76px);
    bottom: 25px;
    color: #ffda54;
    font: 900 clamp(2rem, 4vw, 3.2rem)/1 Inter, sans-serif;
    letter-spacing: -0.08em;
}

.argument-dock {
    padding: 12px;
    background: #080a0f;
    border-top: 1px solid rgba(255, 232, 142, 0.28);
}

.argument-dock textarea {
    min-height: 84px !important;
}

.hidden-runtime {
    display: none !important;
}

@media (max-width: 900px) {
    #landing-hero,
    .arena-stage,
    .court-hud {
        grid-template-columns: 1fr !important;
    }

    #landing-hero {
        min-height: auto;
        padding: 22px;
        gap: 18px;
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

    .court-player-badge,
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


def opponent_name(opponent):
    return OPPONENTS.get(opponent, {}).get("name", "Opponent")


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
                <img src="/file={html.escape(data["image"])}" alt="{html.escape(data["name"])}">
                <strong>{html.escape(data["name"])}</strong>
                <span>{html.escape(data["epithet"])}</span>
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
    speaker="Judge",
    dialogue="State your case. The court is listening.",
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
    sprite_size_class = "wide" if data["sprite"] == "wilde" else ""
    verdict_html = ""
    if verdict:
        verdict_html = f'<div class="court-verdict-strip">{html.escape(verdict)}</div>'

    return f"""
    <div id="court-scene" style="--court-bg: url('/file={html.escape(bg_path)}');">
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
        <img class="court-character {sprite_size_class}" src="/file={html.escape(sprite_path)}" alt="{html.escape(data["name"])}">
        <div class="court-player-badge">
            <img src="/file={html.escape(player_sprite_path)}" alt="Advocate">
            <span>Your Bench</span>
        </div>
        {verdict_html}
        <div class="dialogue-box">
            <div class="dialogue-name">{html.escape(speaker)}</div>
            <p class="dialogue-line">{html.escape(dialogue)}</p>
            <div class="dialogue-next">&gt;&gt;</div>
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
                100,
                100,
                opponent or "oscar_wilde",
                topic or "",
                stance or "For",
                "Judge",
                "Before the court can convene, enter a motion and choose your opponent.",
                "thinking",
                "thinking",
            ),
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
            100,
            100,
            opponent,
            topic,
            stance,
            "Judge",
            "The Grand Tribunal begins. You have the floor.",
            "thinking",
            "talking",
            f"{display_name} awaits your opening argument.",
        ),
    )


def handle_turn(user_arg, topic, stance, opponent, chat_history, user_hp, opp_hp):
    display_name = opponent_name(opponent)
    if not user_arg:
        return (
            "",
            chat_history,
            user_hp,
            opp_hp,
            get_health_bar_html(user_hp, "You", True),
            get_health_bar_html(opp_hp, display_name, False),
            get_arena_html(
                user_hp,
                opp_hp,
                opponent,
                topic,
                stance,
                "Judge",
                "State your argument when ready.",
                "thinking",
                "thinking",
            ),
        )

    chat_history.append({"role": "user", "content": user_arg})

    try:
        j_res = requests.post(JUDGE_URL, json={"topic": topic, "argument": user_arg}).json()
        score = int(j_res.get("score", 5))
        reasoning = j_res.get("reasoning", "No reasoning provided.")
    except Exception as e:
        score, reasoning = 5, f"Judge failed to evaluate: {str(e)}"

    damage = calculate_damage(score)
    fatigue = calculate_fatigue(score)

    turn_msg = f"### Judge's Verdict on Your Argument\n**Score: {score}/10** - *{reasoning}*\n\n"

    if damage > 0:
        opp_hp = max(0, opp_hp - damage)
        turn_msg += f"**Strike landed.** Dealt {damage} damage to {display_name}.\n\n"
    else:
        user_hp = max(0, user_hp - fatigue)
        turn_msg += f"**Mental fatigue.** You suffered {fatigue} self-inflicted damage.\n\n"

    if opp_hp == 0:
        turn_msg += f"**Victory.** {display_name} has been defeated."
        chat_history.append({"role": "assistant", "content": turn_msg})
        return (
            "",
            chat_history,
            user_hp,
            opp_hp,
            get_health_bar_html(user_hp, "You", True),
            get_health_bar_html(opp_hp, display_name, False),
            get_arena_html(
                user_hp,
                opp_hp,
                opponent,
                topic,
                stance,
                "Judge",
                f"{display_name} has been defeated. The motion stands with you.",
                "damage",
                "victory",
                f"Your score: {score}/10. Damage dealt: {damage}.",
            ),
        )
    if user_hp == 0:
        turn_msg += "**Defeat.** Your logic has crumbled."
        chat_history.append({"role": "assistant", "content": turn_msg})
        return (
            "",
            chat_history,
            user_hp,
            opp_hp,
            get_health_bar_html(user_hp, "You", True),
            get_health_bar_html(opp_hp, display_name, False),
            get_arena_html(
                user_hp,
                opp_hp,
                opponent,
                topic,
                stance,
                "Judge",
                "Your logic has crumbled. The tribunal rules against you.",
                "victory",
                "damage",
                f"Your score: {score}/10. Fatigue suffered: {fatigue}.",
            ),
        )

    turn_msg += "---\n\n"

    situation_prompt = f"(Debate Topic: {topic}. The user is arguing {stance} this topic.)\nUser argues: {user_arg}\nCounter their argument fiercely."
    try:
        c_res = requests.post(CHARACTER_URL, json={"character": opponent, "situation": situation_prompt}).json()
        opp_response = c_res.get("response", "I have no words.")
    except Exception as e:
        opp_response = f"*Opponent is stunned and silent.* ({str(e)})"

    turn_msg += f"### {display_name}'s Rebuttal\n\"{opp_response}\"\n\n"

    try:
        j_res2 = requests.post(JUDGE_URL, json={"topic": topic, "argument": opp_response}).json()
        opp_score = int(j_res2.get("score", 5))
        opp_reasoning = j_res2.get("reasoning", "No reasoning provided.")
    except Exception as e:
        opp_score, opp_reasoning = 5, f"Judge failed to evaluate: {str(e)}"

    opp_damage = calculate_damage(opp_score)
    opp_fatigue = calculate_fatigue(opp_score)

    turn_msg += f"### Judge's Verdict on Opponent\n**Score: {opp_score}/10** - *{opp_reasoning}*\n\n"

    if opp_damage > 0:
        user_hp = max(0, user_hp - opp_damage)
        turn_msg += f"**Counterstrike.** You took {opp_damage} damage from the retort."
    else:
        opp_hp = max(0, opp_hp - opp_fatigue)
        turn_msg += f"**Faulty premise.** {display_name} suffers {opp_fatigue} mental fatigue."

    if user_hp == 0:
        turn_msg += "\n\n**Defeat.** Your logic has crumbled."
        scene_speaker = "Judge"
        scene_dialogue = "Your logic has crumbled. The tribunal rules against you."
        opponent_pose = "victory"
        player_pose = "damage"
    elif opp_hp == 0:
        turn_msg += f"\n\n**Victory.** {display_name} has been undone by the exchange."
        scene_speaker = "Judge"
        scene_dialogue = f"{display_name} has been undone by the exchange."
        opponent_pose = "damage"
        player_pose = "victory"
    else:
        scene_speaker = display_name
        scene_dialogue = opp_response
        opponent_pose = "talking" if opp_damage > 0 else "damage"
        player_pose = "damage" if opp_damage > 0 else "thinking"

    chat_history.append({"role": "assistant", "content": turn_msg})

    verdict = (
        f"You: {score}/10"
        f" | {display_name}: {opp_score}/10"
        f" | Damage taken: {opp_damage if opp_damage > 0 else 0}"
        f" | Damage dealt: {damage if damage > 0 else 0}"
    )

    return (
        "",
        chat_history,
        user_hp,
        opp_hp,
        get_health_bar_html(user_hp, "You", True),
        get_health_bar_html(opp_hp, display_name, False),
        get_arena_html(
            user_hp,
            opp_hp,
            opponent,
            topic,
            stance,
            scene_speaker,
            scene_dialogue,
            opponent_pose,
            player_pose,
            verdict,
        ),
    )


with gr.Blocks(elem_id="tribunal-app", css=CSS, theme=gr.themes.Soft()) as demo:
    topic_state = gr.State("")
    stance_state = gr.State("")
    opponent_state = gr.State("")
    user_hp_state = gr.State(100)
    opp_hp_state = gr.State(100)

    with gr.Row(visible=True, elem_id="landing-hero") as setup_area:
        gr.HTML(
            """
            <div class="hero-copy">
                <span class="kicker">AI-powered dialectical combat</span>
                <h1>The Grand Tribunal</h1>
                <p>
                    Enter a turn-based battle of wit, where a judge scores the force of each argument
                    and history's sharpest minds answer from across the bench.
                </p>
                <div class="hero-statline">
                    <span>100 HP each</span>
                    <span>Score 5+ deals damage</span>
                    <span>Weak logic causes fatigue</span>
                </div>
            </div>
            """
        )
        with gr.Column(elem_classes="setup-panel"):
            gr.HTML(
                """
                <h2 class="setup-title">Set the docket</h2>
                <p class="setup-subtitle">The whole opening move now lives here: motion, stance, opponent, then straight into the arena.</p>
                """
            )
            topic_input = gr.Textbox(
                label="Debate Topic",
                placeholder="e.g. The pursuit of happiness is the highest good.",
                lines=3,
            )
            stance_input = gr.Radio(["For", "Against"], label="Your Stance", value="For", scale=1)

            opponent_input = gr.Radio(
                choices=[
                    ("Oscar Wilde", "oscar_wilde"),
                    ("Nietzsche", "friedrich_nietzsche"),
                    ("Plato", "plato"),
                    ("Schopenhauer", "schopenhauer"),
                ],
                label="Select Opponent",
                value="oscar_wilde",
            )
            gr.HTML(get_roster_html())
            start_btn = gr.Button("Enter the Tribunal", variant="primary")
            error_box = gr.HTML("", visible=True)

    with gr.Column(visible=False, elem_classes="debate-shell") as debate_area:
        arena_html = gr.HTML(get_arena_html())
        with gr.Row(elem_classes=["vitals-grid", "hidden-runtime"]):
            user_health_html = gr.HTML(get_health_bar_html(100, "You", True))
            opp_health_html = gr.HTML(get_health_bar_html(100, "Opponent", False))

        chatbot = gr.Chatbot(label="Tribunal Transcript", height=500, elem_id="tribunal-chat", visible=False)

        with gr.Row(elem_classes=["submit-row", "argument-dock"]):
            user_msg = gr.Textbox(
                label="Your Argument",
                placeholder="Type your objection, proof, or philosophical haymaker...",
                lines=4,
                scale=5,
                elem_id="submit-argument",
            )
            submit_btn = gr.Button("Submit Argument", variant="primary", scale=1)

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
        ],
    ).then(
        fn=lambda t, s, o: (t, s, o),
        inputs=[topic_input, stance_input, opponent_input],
        outputs=[topic_state, stance_state, opponent_state],
    )

    submit_btn.click(
        fn=handle_turn,
        inputs=[user_msg, topic_state, stance_state, opponent_state, chatbot, user_hp_state, opp_hp_state],
        outputs=[user_msg, chatbot, user_hp_state, opp_hp_state, user_health_html, opp_health_html, arena_html],
    )

    user_msg.submit(
        fn=handle_turn,
        inputs=[user_msg, topic_state, stance_state, opponent_state, chatbot, user_hp_state, opp_hp_state],
        outputs=[user_msg, chatbot, user_hp_state, opp_hp_state, user_health_html, opp_health_html, arena_html],
    )


if __name__ == "__main__":
    demo.launch(allowed_paths=["."], css=CSS, theme=gr.themes.Soft())
