---
title: The Grand Tribunal
emoji: ⚖️
colorFrom: brown
colorTo: amber
sdk: gradio
sdk_version: 5.16.0
python_version: '3.10'
app_file: app.py
pinned: false
hf_oauth: true
license: mit
thumbnail: https://huggingface.co/spaces/build-small-hackathon/grand-tribunal/resolve/main/logo.jpg
tags:
- build-small-hackathon
- gradio
- game
- custom-ui
- modal
- openbmb
- voxcpm2
- whisper
- qwen
- vllm
- track:[INSERT TRACK HERE]
- achievement:[INSERT ACHIEVEMENT HERE]
short_description: A turn-based AI debate battle game featuring historical philosophers.
---

# The Grand Tribunal
A turn-based AI debate battle game where you face off against history's most formidable philosophers in a battle of wit, judged by a relentless AI.

## Face the Tribunal
**The Grand Tribunal** turns a philosophical debate into a high-stakes, 100 HP visual novel combat arena. Enter a topic of your choice, select your stance, and defend your arguments against intellectual giants who are out to prove you wrong.

The AI is not decoration here. It is load-bearing:
- **vLLM Inference Engine**: Drives the core Qwen 3.5 9B base model to dynamically load character-specific LoRA adapters on-the-fly, giving Oscar Wilde, Friedrich Nietzsche, Plato, and Arthur Schopenhauer their distinct historical styles, wit, and philosophical frameworks.
- **Relentless AI Judge**: Evaluates arguments in real-time across five axes (Score, Logic, Relevance, Creativity, Reasoning) to calculate damage or self-inflicted fatigue.
- **Whisper STT**: Transcribes players' spoken arguments directly in the browser with low latency, supported by input validation filters that catch prompt injections and gibberish.
- **VoxCPM2 TTS**: Generates voice-cloned, spoken philosopher rebuttals using a reference waveform (`voice.wav`) to bring the courtroom debates to life.

## Demo Links
- Live Space: [https://huggingface.co/spaces/build-small-hackathon/grand-tribunal](https://huggingface.co/spaces/build-small-hackathon/grand-tribunal) *(Or insert your Space link)*
- Demo video: `[INSERT DEMO VIDEO LINK]`
- Social post X: `[INSERT X POST LINK]`
- Social post Linkedin: `[INSERT LINKEDIN POST LINK]`
- Field Notes: `[INSERT FIELD NOTES LINK]`
- GitHub repository: `[INSERT GITHUB REPOSITORY LINK]`

The GitHub repository above is the source-of-truth development repository. It contains the full implementation history, installation documentation, local-mode setup, and commits. This Space repository is a deployment copy prepared for judges to play the finished app.

## Hackathon Track
Submitted for `[INSERT HACKATHON TRACK HERE]` (e.g., An Adventure in Thousand Token Wood).
The goal was to build a highly interactive, custom-styled game that showcases how serverless GPU infrastructure and dynamic adapter loading can power low-latency voice-to-voice gameplay.

## Targeted Special Awards and Bonus Quests
- **Track**: `[INSERT TRACK]`
- **Sponsors**:
  - `sponsor:openbmb` (VoxCPM2 TTS model for voice cloning)
  - `sponsor:modal` (Modal serverless deployment)
  - `sponsor:openai` (Whisper STT model)
- **Achievements**:
  - `achievement:custom-ui` (Premium parchment-themed visual novel Gradio CSS layout)
  - `achievement:offgrid` (Custom serverless endpoints deployed on Modal)
  - `achievement:llama` / `achievement:fieldnotes` / `achievement:sharing` (Populate as applicable)

## Tech Stack
The game uses a split client-server architecture designed for low-latency inference on high-performance serverless GPU clusters.

```mermaid
graph TD
    %% Nodes
    User([User advocate])
    Gradio[Gradio Web Client / app.py]
    FastAPI[FastAPI Proxy Server / serve_modal_v2.py]
    vLLM[vLLM Inference Engine]
    BaseLLM[Qwen 3.5 9B Base Model]
    LoRA[LoRA Adapters Volume]
    Whisper[openai/whisper-tiny.en]
    VoxCPM[openbmb/VoxCPM2 TTS]

    %% Interactions
    User -->|Voice / Text Input| Gradio
    Gradio -->|FastAPI Endpoints| FastAPI
    
    subgraph Modal GPU Container (a100-80gb)
        FastAPI -->|STT transcription| Whisper
        FastAPI -->|TTS audio synthesis| VoxCPM
        FastAPI -->|Argument & Rebuttal| vLLM
        vLLM -->|Dynamic Adapter Loading| LoRA
        vLLM -->|Base LLM Inference| BaseLLM
    end

    FastAPI -->|Text & Audio Stream| Gradio
    Gradio -->|Visual novel UI / Spoken Rebuttals| User
```

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
