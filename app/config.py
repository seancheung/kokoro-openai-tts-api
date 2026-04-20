from __future__ import annotations

from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False, extra="ignore")

    kokoro_model: str = Field(
        default="hexgrad/Kokoro-82M",
        description="HuggingFace repo id (or local path) hosting Kokoro weights + voices.",
    )
    kokoro_cuda_index: int = Field(default=0)
    kokoro_cache_dir: Optional[str] = Field(default=None)

    # Comma-separated list of lang codes to eagerly initialise at startup;
    # pipelines are otherwise created lazily on first use.
    kokoro_preload_langs: str = Field(default="")
    # Comma-separated list of voice ids to preload (downloads .pt files eagerly).
    kokoro_preload_voices: str = Field(default="")

    kokoro_use_transformer_g2p: bool = Field(default=False)

    # Per-request generation defaults.
    kokoro_split_pattern: str = Field(default=r"\n+")

    max_input_chars: int = Field(default=8000)
    default_response_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] = Field(default="mp3")

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    log_level: str = Field(default="info")

    @property
    def preload_langs(self) -> list[str]:
        return [s.strip().lower() for s in self.kokoro_preload_langs.split(",") if s.strip()]

    @property
    def preload_voices(self) -> list[str]:
        return [s.strip() for s in self.kokoro_preload_voices.split(",") if s.strip()]

    @property
    def resolved_device(self) -> str:
        import torch

        if torch.cuda.is_available():
            return f"cuda:{self.kokoro_cuda_index}"
        return "cpu"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
