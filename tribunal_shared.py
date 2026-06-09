CHARACTER_REGISTRY = {
    "oscar_wilde": {
        "name": "Oscar Wilde",
        "image": "oscar_wilde.png",
        "sprite": "wilde",
        "sprite_scale": "wide",
        "epithet": "The Velvet Saboteur",
        "school": "Aesthetic wit and elegant contradiction",
    },
    "friedrich_nietzsche": {
        "name": "Friedrich Nietzsche",
        "image": "nietzsche.png",
        "sprite": "nietzsche",
        "sprite_scale": "tall",
        "epithet": "The Hammer of Certainty",
        "school": "Genealogy, will, and merciless revaluation",
    },
    "plato": {
        "name": "Plato",
        "image": "socrates.png",
        "sprite": "plato",
        "sprite_scale": "tall",
        "epithet": "The Keeper of Forms",
        "school": "Dialectic, justice, and ideal truth",
    },
    "schopenhauer": {
        "name": "Arthur Schopenhauer",
        "image": "schopenhauer.png",
        "sprite": "schopenhauer",
        "sprite_scale": "tall",
        "epithet": "The Pessimist Laureate",
        "school": "Will, suffering, and the limits of desire",
    },
}

MODAL_ENDPOINTS = {
    "judge": "https://ramratanpadhy59--grand-tribunal-inference-api.modal.run/judge",
    "character": "https://ramratanpadhy59--grand-tribunal-inference-api.modal.run/character",
    "stt": "https://ramratanpadhy59--grand-tribunal-inference-api.modal.run/stt",
    "tts": "https://ramratanpadhy59--grand-tribunal-inference-api.modal.run/tts",
}

GENERIC_MODAL_ERROR = "The philosopher is momentarily indisposed. Try again."
INVALID_ARGUMENT_MESSAGE = "Invalid argument. Please make a genuine debate point."
HALLUCINATION_PHRASES = {
    "hm",
    "hm.",
    "hmm",
    "hmm.",
    "thank you",
    "thank you.",
    "thanks",
    "thanks.",
}
PROMPT_INJECTION_MARKERS = (
    "ignore previous instructions",
    "system:",
    "<|im_start|>",
)


def get_character(character_id):
    return CHARACTER_REGISTRY.get(character_id, CHARACTER_REGISTRY["oscar_wilde"])


def get_character_name(character_id):
    return get_character(character_id)["name"]


def get_character_display_names():
    return {key: data["name"] for key, data in CHARACTER_REGISTRY.items()}


def normalize_text(text):
    return " ".join((text or "").strip().split())


def clamp_argument(text, limit=500):
    return normalize_text(text)[:limit]


def looks_like_bad_transcript(text):
    normalized = normalize_text(text).lower()
    if not normalized:
        return True
    if normalized in HALLUCINATION_PHRASES:
        return True
    if len(normalized) < 12 and len(normalized.split()) <= 3:
        return True
    return False


def looks_like_prompt_injection(text):
    normalized = normalize_text(text).lower()
    return any(marker in normalized for marker in PROMPT_INJECTION_MARKERS)
