from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


ResponseFormat = Literal["mp3", "opus", "aac", "flac", "wav", "pcm"]


class SpeechRequest(BaseModel):
    """OpenAI-compatible `/v1/audio/speech` request."""

    model: Optional[str] = Field(default=None, description="Accepted for OpenAI compatibility; ignored.")
    input: str = Field(..., description="Text to synthesize.")
    voice: str = Field(
        ...,
        description=(
            "Built-in voice id (e.g. `af_heart`). A comma-separated list "
            "averages the voices."
        ),
    )
    response_format: ResponseFormat = Field(default="mp3")
    speed: float = Field(default=1.0, ge=0.25, le=4.0)

    lang_code: Optional[str] = Field(
        default=None,
        description=(
            "Override the language pipeline (`a`, `b`, `e`, `f`, `h`, `i`, `j`, `p`, `z` or "
            "aliases like `en-us`). Defaults to the voice id's first character."
        ),
    )


class VoiceInfo(BaseModel):
    id: str
    lang_code: str
    language: str
    gender: Optional[str] = None
    traits: Optional[str] = Field(
        default=None,
        description="Emoji tag from VOICES.md (e.g. ❤️ / 🔥 / 🎧).",
    )
    grade: Optional[str] = Field(
        default=None,
        description="Overall quality grade published in VOICES.md (A best … F worst).",
    )


class VoiceList(BaseModel):
    object: Literal["list"] = "list"
    data: list[VoiceInfo]


class HealthResponse(BaseModel):
    status: Literal["ok", "loading", "error"]
    repo_id: str
    device: Optional[str] = None
    sample_rate: Optional[int] = None
    loaded_langs: list[str] = []
