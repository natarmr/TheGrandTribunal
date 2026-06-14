import re

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
    "judge": "https://ramratanpadhy59--grand-tribunal-inference-v2-api.modal.run/judge",
    "character": "https://ramratanpadhy59--grand-tribunal-inference-v2-api.modal.run/character",
    "stt": "https://ramratanpadhy59--grand-tribunal-inference-v2-api.modal.run/stt",
    "tts": "https://ramratanpadhy59--grand-tribunal-inference-v2-api.modal.run/tts",
    "turn": "https://ramratanpadhy59--grand-tribunal-inference-v2-api.modal.run/turn",
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


def looks_like_gibberish_topic(text):
    normalized = normalize_text(text).lower()
    if not normalized:
        return True
    if len(normalized) < 3:
        return True
    if not re.search(r"[a-z]", normalized):
        return True

    words = re.findall(r"[a-z][a-z0-9'\-]*", normalized)
    if not words:
        return True

    letters = sum(ch.isalpha() for ch in normalized)
    if letters / max(len(normalized), 1) < 0.55 and len(normalized) > 6:
        return True

    def clean_word(word):
        return re.sub(r"[^a-z]", "", word)

    def vowel_count(word):
        return sum(ch in "aeiou" for ch in word)

    def max_consonant_run(word):
        run = best = 0
        for ch in word:
            if ch in "aeiou":
                run = 0
            elif ch.isalpha():
                run += 1
                best = max(best, run)
        return best

    cleaned_words = [clean_word(word) for word in words]
    alpha_words = [word for word in cleaned_words if word]
    if not alpha_words:
        return True

    if len(alpha_words) == 1:
        word = alpha_words[0]
        if len(word) < 4:
            return True
        if not re.fullmatch(r"[a-z]+(?:-[a-z]+)?", words[0]):
            return True
        if vowel_count(word) == 0:
            return True
        if len(word) >= 6 and vowel_count(word) / len(word) < 0.2:
            return True
        if max_consonant_run(word) >= 5:
            return True
        return False

    vowel_total = sum(vowel_count(word) for word in alpha_words)
    letter_total = sum(len(word) for word in alpha_words)
    if letter_total and vowel_total / letter_total < 0.25 and len(alpha_words) >= 2:
        return True

    for word in alpha_words:
        if len(word) >= 5:
            if vowel_count(word) == 0:
                return True
            if vowel_count(word) / len(word) < 0.18:
                return True
            if max_consonant_run(word) >= 5:
                return True

    if len(alpha_words) >= 3:
        short_words = sum(len(word) <= 2 for word in alpha_words)
        if short_words >= len(alpha_words) - 1:
            return True

    return False
