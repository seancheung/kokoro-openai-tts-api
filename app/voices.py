from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


LANG_NAMES: Dict[str, str] = {
    "a": "American English",
    "b": "British English",
    "e": "Spanish",
    "f": "French",
    "h": "Hindi",
    "i": "Italian",
    "j": "Japanese",
    "p": "Brazilian Portuguese",
    "z": "Mandarin Chinese",
}


# Full built-in voice registry, sourced from
# https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
# First char of id = lang code; second char = gender (`f`/`m`).
# `traits` is the emoji tag on VOICES.md; `grade` is the overall quality grade
# the authors published (A = best; blank entries had no grade at publish time).
BUILTIN_VOICES: Dict[str, Dict[str, Optional[str]]] = {
    # American English — female (11)
    "af_heart":   {"traits": "❤️", "grade": "A"},
    "af_alloy":   {"grade": "C"},
    "af_aoede":   {"grade": "C+"},
    "af_bella":   {"traits": "🔥", "grade": "A-"},
    "af_jessica": {"grade": "D"},
    "af_kore":    {"grade": "C+"},
    "af_nicole":  {"traits": "🎧", "grade": "B-"},
    "af_nova":    {"grade": "C"},
    "af_river":   {"grade": "D"},
    "af_sarah":   {"grade": "C+"},
    "af_sky":     {"grade": "C-"},
    # American English — male (9)
    "am_adam":    {"grade": "F+"},
    "am_echo":    {"grade": "D"},
    "am_eric":    {"grade": "D"},
    "am_fenrir":  {"grade": "C+"},
    "am_liam":    {"grade": "D"},
    "am_michael": {"grade": "C+"},
    "am_onyx":    {"grade": "D"},
    "am_puck":    {"grade": "C+"},
    "am_santa":   {"grade": "D-"},
    # British English — female (4)
    "bf_alice":    {"grade": "D"},
    "bf_emma":     {"grade": "B-"},
    "bf_isabella": {"grade": "C"},
    "bf_lily":     {"grade": "D"},
    # British English — male (4)
    "bm_daniel": {"grade": "D"},
    "bm_fable":  {"grade": "C"},
    "bm_george": {"grade": "C"},
    "bm_lewis":  {"grade": "D+"},
    # Japanese — female (4)
    "jf_alpha":      {"grade": "C+"},
    "jf_gongitsune": {"grade": "C"},
    "jf_nezumi":     {"grade": "C-"},
    "jf_tebukuro":   {"grade": "C"},
    # Japanese — male (1)
    "jm_kumo": {"grade": "C-"},
    # Mandarin Chinese — female (4)
    "zf_xiaobei":  {"grade": "D"},
    "zf_xiaoni":   {"grade": "D"},
    "zf_xiaoxiao": {"grade": "D"},
    "zf_xiaoyi":   {"grade": "D"},
    # Mandarin Chinese — male (4)
    "zm_yunjian": {"grade": "D"},
    "zm_yunxi":   {"grade": "D"},
    "zm_yunxia":  {"grade": "D"},
    "zm_yunyang": {"grade": "D"},
    # Spanish (3)
    "ef_dora":  {},
    "em_alex":  {},
    "em_santa": {},
    # French (1)
    "ff_siwis": {"grade": "B-"},
    # Hindi (4)
    "hf_alpha": {"grade": "C"},
    "hf_beta":  {"grade": "C"},
    "hm_omega": {"grade": "C"},
    "hm_psi":   {"grade": "C"},
    # Italian (2)
    "if_sara":   {"grade": "C"},
    "im_nicola": {"grade": "C"},
    # Brazilian Portuguese (3)
    "pf_dora":  {},
    "pm_alex":  {},
    "pm_santa": {},
}


@dataclass(frozen=True)
class Voice:
    id: str
    lang_code: str
    language: str
    gender: Optional[str]
    traits: Optional[str] = None
    grade: Optional[str] = None


def _gender_from_id(vid: str) -> Optional[str]:
    if len(vid) >= 2:
        g = vid[1].lower()
        if g == "f":
            return "female"
        if g == "m":
            return "male"
    return None


def _build(vid: str, meta: Dict[str, Optional[str]]) -> Voice:
    lang = vid[0].lower()
    return Voice(
        id=vid,
        lang_code=lang,
        language=LANG_NAMES.get(lang, lang),
        gender=_gender_from_id(vid),
        traits=meta.get("traits") or None,
        grade=meta.get("grade") or None,
    )


class VoiceCatalog:
    """Static registry of the built-in Kokoro voices."""

    def __init__(self) -> None:
        self._voices: Dict[str, Voice] = {
            vid: _build(vid, meta) for vid, meta in BUILTIN_VOICES.items()
        }

    def all(self) -> Dict[str, Voice]:
        return self._voices

    def get(self, vid: str) -> Optional[Voice]:
        return self._voices.get(vid)
