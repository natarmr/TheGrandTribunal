---
title: TheGrandTribunal
emoji: 🐨
colorFrom: yellow
colorTo: green
sdk: gradio
sdk_version: 6.18.0
python_version: '3.13'
app_file: app.py
pinned: false
license: mit
short_description: 'Ace Attorney-style turn-based AI debate game '
tags:
  - build-small-hackathon
  - thousand-token-wood
  - gradio
  - game
  - custom-ui
  - off-brand
  - tiny-titan
  - openbmb
  - voxcpm2
  - modal
  - llama-cpp
  - codex
  - field-notes
  - track:wood
  - sponsor:openbmb
  - sponsor:openai
  - sponsor:modal
  - achievement:offgrid
  - achievement:offbrand
  - achievement:fieldnotes
---
# The Grand Tribunal

Welcome to **The Grand Tribunal**, where you try to destroy your opponents in a battle of wit. Every word you say counts as a hit, and better you can tell the judge why hot showers are better than cold, the faster you win.

Enter a topic of your choice, select your stance, and face off against some of history's most formidable intellectual titans as they try to prove you wrong. Your arguments will be analyzed in real-time by a relentless AI Judge. Win by shattering your opponent's logic; lose if your own reasoning crumbles under pressure.

---

## Demo Links
- Live Space: https://huggingface.co/spaces/build-small-hackathon/TheGrandTribunal
- Demo video: https://youtu.be/a8g_5n4dlwM
- Social post X: https://x.com/IamRamratan/status/2066212388295311559?s=20
- Social post Linkedin: https://www.linkedin.com/posts/ramratan-ntlap_had-a-great-time-working-on-my-game-again-share-7471972506070048770-o6se/
- Field Notes: https://huggingface.co/blog/build-small-hackathon/grandtribunal
- GitHub repository: https://github.com/consolelogram/GrandTribunal

The GitHub repository above is the source-of-truth development repository. It contains the full implementation history, installation documentation, local-mode setup, and commits. This Space repository is a deployment copy prepared for judges to play the finished app.

## Hackathon Track
Submitted for An Adventure in Thousand Token Wood
The goal was to build a highly interactive, custom-styled game that showcases how serverless GPU infrastructure and dynamic adapter loading can power low-latency voice-to-voice gameplay.

## Targeted Special Awards and Bonus Quests
- **Track**: An Adventure in Thousand Token wood
- **Sponsors**:
  - `sponsor:openbmb` (VoxCPM2 TTS model for voice cloning)
  - `sponsor:modal` (Modal serverless deployment)
  - `sponsor:openai` (Codex)
- **Achievements**:
  - `achievement:custom-ui` (Premium parchment-themed visual novel Gradio CSS layout)
  - `achievement:offgrid` (Custom serverless endpoints deployed on Modal)
  - `achievement:fieldnotes` 
## Tech Stack
The game uses a split client-server architecture designed for low-latency inference on high-performance serverless GPU clusters.



- **Frontend (Gradio):** Custom parchment/courtroom CSS styling system, responsive layout media queries, and browser-based audio recording with input validation.
- **Inference Server (Modal):** Serverless architecture hosting:
  - **vLLM** for hosting the **Qwen 3.5 9B** base model.
  - **LoRA adapters** for character personas (Oscar Wilde, Friedrich Nietzsche, Plato, Arthur Schopenhauer) loaded dynamically from a persistent Modal Volume.
  - **Whisper (Tiny)** for voice-to-text transcriptions.
  - **VoxCPM2** for voice cloning and TTS audio synthesis.

## Gameplay Summary
Meet the intellectual adversaries:

| Philosopher | Epithet | School of Thought |
| :--- | :--- | :--- |
| **Oscar Wilde** | *The Velvet Saboteur* | Aesthetic wit and elegant contradiction |
| **Friedrich Nietzsche** | *The Hammer of Certainty* | Genealogy, will, and merciless revaluation |
| **Plato** | *The Keeper of Forms* | Dialectic, justice, and ideal truth |
| **Arthur Schopenhauer** | *The Pessimist Laureate* | Will, suffering, and the limits of desire |

### Mechanics:
1. **Player's Turn:** Present your argument by typing or recording your voice. Audio is transcribed via Whisper.
2. **The Judge's Evaluation:** Your logic, score, relevance, and creativity are evaluated. Score >= 5 deals damage: $\text{Damage Dealt} = (\text{Score} - 4) \times 3$. Score < 5 inflicts self fatigue: $\text{Fatigue} = \text{Random}(1, 5)$.
3. **Opponent's Turn:** The philosopher counters with a sharp rebuttal, synthesized as speech via VoxCPM2 using reference voice waveforms.
4. **Victory & Defeat:** Reduce the opponent to 0 HP to stand victorious, or fall if your own HP drops to 0.

## Local Mode
The app can run locally or connect to custom server endpoints:
- Local Gradio server: `python app.py`
- Modal API proxy for STT, TTS, and LLM generation.
- Check `serve_modal_v2.py` for deploying your own backend.

## Credits
- **Voice generation:** VoxCPM2 by OpenBMB.
- **STT Transcription:** Whisper Tiny by OpenAI.
- **LLM Base Model:** Qwen 3.5.
- **Backend Infrastructure:** Modal.

## License
MIT License.
