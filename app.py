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
        "epithet": "The Velvet Saboteur",
        "school": "Aesthetic wit and elegant contradiction",
    },
    "friedrich_nietzsche": {
        "name": "Friedrich Nietzsche",
        "image": "nietzsche.png",
        "epithet": "The Hammer of Certainty",
        "school": "Genealogy, will, and merciless revaluation",
    },
    "plato": {
        "name": "Plato",
        "image": "socrates.png",
        "epithet": "The Keeper of Forms",
        "school": "Dialectic, justice, and ideal truth",
    },
    "schopenhauer": {
        "name": "Arthur Schopenhauer",
        "image": "schopenhauer.png",
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

.tribunal-hero {
    position: relative;
    min-height: 360px;
    display: grid;
    grid-template-columns: minmax(280px, 0.95fr) minmax(420px, 1.55fr);
    align-items: stretch;
    overflow: hidden;
    border: 1px solid rgba(201, 154, 62, 0.34);
    background:
        linear-gradient(90deg, rgba(16, 18, 22, 0.94), rgba(31, 22, 22, 0.72) 54%, rgba(239, 226, 198, 0.1)),
        url('/file=oscar_wilde.png') right 5% bottom 0 / min(48vw, 640px) auto no-repeat,
        #171a20;
    box-shadow: 0 24px 60px rgba(0, 0, 0, 0.35);
}

.tribunal-hero:after {
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
    padding: clamp(26px, 5vw, 58px);
    display: flex;
    flex-direction: column;
    justify-content: center;
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
    font: 900 clamp(2.25rem, 6vw, 5.8rem)/0.92 Cinzel, serif;
    letter-spacing: 0;
    max-width: 720px;
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

.setup-shell,
.debate-shell {
    margin-top: 14px;
    padding: clamp(12px, 2vw, 22px);
    border: 1px solid rgba(201, 154, 62, 0.3);
    background: rgba(17, 19, 24, 0.74);
}

.setup-title,
.panel-title {
    margin: 0 0 12px;
    color: #fff2d8;
    font: 800 1.02rem/1.2 Cinzel, serif;
}

.opponent-roster {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
    margin-top: 12px;
}

.opponent-chip {
    min-height: 154px;
    overflow: hidden;
    border: 1px solid rgba(201, 154, 62, 0.3);
    background: linear-gradient(180deg, rgba(239, 226, 198, 0.1), rgba(10, 11, 14, 0.4));
    border-radius: 6px;
    position: relative;
}

.opponent-chip img {
    width: 100%;
    height: 112px;
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

@media (max-width: 900px) {
    .tribunal-hero,
    .arena-stage {
        grid-template-columns: 1fr;
    }

    .tribunal-hero {
        min-height: 520px;
        background:
            linear-gradient(180deg, rgba(16, 18, 22, 0.96), rgba(31, 22, 22, 0.62) 58%, rgba(8, 9, 12, 0.88)),
            url('/file=oscar_wilde.png') center bottom / min(94vw, 520px) auto no-repeat,
            #171a20;
        align-items: start;
    }

    .hero-copy {
        padding-bottom: 260px;
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


def get_arena_html(user_hp=100, opp_hp=100, opponent="oscar_wilde", topic="", stance="For"):
    data = OPPONENTS.get(opponent) or OPPONENTS["oscar_wilde"]
    topic_text = topic.strip() if topic else "Awaiting a motion before the court"
    stance_text = stance or "For"
    return f"""
    <div class="arena-stage">
        <div class="combatant user">
            <div class="speaker-mark">YOU</div>
            <div class="nameplate">
                <strong>The Advocate</strong>
                <span>{int(user_hp)} HP - reasoning under oath</span>
            </div>
        </div>
        <div class="topic-docket">
            <span class="stage-kicker">Docket before the tribunal</span>
            <h2>{html.escape(topic_text)}</h2>
            <p>{html.escape(data["school"])}</p>
            <div class="stance-pill">Your stance: {html.escape(stance_text)}</div>
        </div>
        <div class="combatant opponent">
            <img src="/file={html.escape(data["image"])}" alt="{html.escape(data["name"])}">
            <div class="nameplate">
                <strong>{html.escape(data["name"])}</strong>
                <span>{html.escape(data["epithet"])} - {int(opp_hp)} HP</span>
            </div>
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
            get_arena_html(100, 100, opponent or "oscar_wilde", topic or "", stance or "For"),
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
        get_arena_html(100, 100, opponent, topic, stance),
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
            get_arena_html(user_hp, opp_hp, opponent, topic, stance),
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
            get_arena_html(user_hp, opp_hp, opponent, topic, stance),
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
            get_arena_html(user_hp, opp_hp, opponent, topic, stance),
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
    elif opp_hp == 0:
        turn_msg += f"\n\n**Victory.** {display_name} has been undone by the exchange."

    chat_history.append({"role": "assistant", "content": turn_msg})

    return (
        "",
        chat_history,
        user_hp,
        opp_hp,
        get_health_bar_html(user_hp, "You", True),
        get_health_bar_html(opp_hp, display_name, False),
        get_arena_html(user_hp, opp_hp, opponent, topic, stance),
    )


with gr.Blocks(elem_id="tribunal-app") as demo:
    gr.HTML(
        """
        <section class="tribunal-hero">
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
        </section>
        """
    )

    topic_state = gr.State("")
    stance_state = gr.State("")
    opponent_state = gr.State("")
    user_hp_state = gr.State(100)
    opp_hp_state = gr.State(100)

    with gr.Column(visible=True, elem_classes="setup-shell") as setup_area:
        gr.HTML('<h2 class="setup-title">Configure the debate</h2>')
        with gr.Row():
            topic_input = gr.Textbox(
                label="Debate Topic",
                placeholder="e.g. The pursuit of happiness is the highest good.",
                lines=3,
                scale=3,
            )
            stance_input = gr.Radio(["For", "Against"], label="Your Stance", value="For", scale=1)

        opponent_input = gr.Dropdown(
            choices=[
                ("Oscar Wilde", "oscar_wilde"),
                ("Friedrich Nietzsche", "friedrich_nietzsche"),
                ("Plato", "plato"),
                ("Arthur Schopenhauer", "schopenhauer"),
            ],
            label="Select Opponent",
            value="oscar_wilde",
        )
        gr.HTML(get_roster_html())
        start_btn = gr.Button("Enter the Tribunal", variant="primary")
        error_box = gr.HTML("", visible=True)

    with gr.Column(visible=False, elem_classes="debate-shell") as debate_area:
        arena_html = gr.HTML(get_arena_html())
        with gr.Row(elem_classes="vitals-grid"):
            user_health_html = gr.HTML(get_health_bar_html(100, "You", True))
            opp_health_html = gr.HTML(get_health_bar_html(100, "Opponent", False))

        chatbot = gr.Chatbot(label="Tribunal Transcript", height=500, elem_id="tribunal-chat")

        with gr.Row(elem_classes="submit-row"):
            user_msg = gr.Textbox(
                label="Your Argument",
                placeholder="State your case with force, clarity, and a little nerve.",
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
