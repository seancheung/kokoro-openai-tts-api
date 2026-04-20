from __future__ import annotations

import asyncio
import logging
import os
from typing import Dict, List, Optional

import numpy as np

log = logging.getLogger(__name__)

KOKORO_SAMPLE_RATE = 24000

# Language-code aliases accepted on the API; mirrors kokoro.pipeline.ALIASES so
# clients can pass `en-us` / `zh` / etc. without needing kokoro import.
LANG_ALIASES = {
    "en-us": "a",
    "en-gb": "b",
    "es": "e",
    "fr-fr": "f",
    "hi": "h",
    "it": "i",
    "pt-br": "p",
    "ja": "j",
    "zh": "z",
}


class TTSEngine:
    def __init__(self, settings, catalog):
        # Import lazily so the module is importable without kokoro installed
        # (tests / type-checking / lint).
        from kokoro import KModel

        self.settings = settings
        self.catalog = catalog

        if settings.kokoro_cache_dir:
            os.environ.setdefault("HF_HOME", settings.kokoro_cache_dir)

        device = settings.resolved_device
        if device == "mps":
            os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

        log.info("loading KModel repo_id=%s device=%s", settings.kokoro_repo_id, device)
        self.model = KModel(repo_id=settings.kokoro_repo_id).to(device).eval()
        self.device = device
        self.sample_rate = KOKORO_SAMPLE_RATE

        self._pipelines: Dict[str, object] = {}
        self._pipeline_lock = asyncio.Lock()
        # A single KModel instance is not thread-safe; serialise inference.
        self._inference_lock = asyncio.Lock()

        for lang in settings.preload_langs:
            lang = LANG_ALIASES.get(lang, lang)
            try:
                self._build_pipeline(lang)
            except Exception:
                log.exception("preload: failed to build pipeline for %s", lang)

        for vid in settings.preload_voices:
            try:
                v = self.catalog.get(vid)
                if v is None:
                    log.warning("preload voice %s not found in catalog", vid)
                    continue
                pipeline = self._build_pipeline(v.lang_code)
                pipeline.load_voice(v.id)
            except Exception:
                log.exception("preload voice %s failed", vid)

    @property
    def loaded_langs(self) -> List[str]:
        return sorted(self._pipelines.keys())

    # ------------------------------------------------------------------
    # pipelines
    # ------------------------------------------------------------------
    def _build_pipeline(self, lang_code: str):
        from kokoro import KPipeline

        if lang_code in self._pipelines:
            return self._pipelines[lang_code]
        log.info("building KPipeline lang=%s", lang_code)
        pipeline = KPipeline(
            lang_code=lang_code,
            repo_id=self.settings.kokoro_repo_id,
            model=self.model,
            trf=self.settings.kokoro_use_transformer_g2p,
        )
        self._pipelines[lang_code] = pipeline
        return pipeline

    async def _get_pipeline(self, lang_code: str):
        async with self._pipeline_lock:
            return await asyncio.to_thread(self._build_pipeline, lang_code)

    # ------------------------------------------------------------------
    # inference
    # ------------------------------------------------------------------
    async def synthesize(
        self,
        text: str,
        *,
        voice_spec: str,
        response_speed: float = 1.0,
        lang_code: Optional[str] = None,
    ) -> np.ndarray:
        """Synthesize ``text`` with the voice(s) described by ``voice_spec``.

        ``voice_spec`` is what the client sent in ``voice``: a single id or a
        comma-separated list (averaged). ``lang_code`` takes precedence;
        otherwise the first character of the first voice id selects the
        pipeline.
        """
        ids = [v.strip() for v in voice_spec.split(",") if v.strip()]
        if not ids:
            raise ValueError("voice is empty")

        if lang_code:
            lang = LANG_ALIASES.get(lang_code.lower(), lang_code.lower())
        else:
            lang = ids[0][0].lower()
            lang = LANG_ALIASES.get(lang, lang)

        pipeline = await self._get_pipeline(lang)
        voice_arg = ",".join(ids)

        async with self._inference_lock:
            audio = await asyncio.to_thread(
                self._run, pipeline, text, voice_arg, response_speed,
            )
        return audio

    def _run(self, pipeline, text: str, voice_arg: str, speed: float) -> np.ndarray:
        import torch

        chunks: List[np.ndarray] = []
        for result in pipeline(
            text,
            voice=voice_arg,
            speed=speed,
            split_pattern=self.settings.kokoro_split_pattern,
        ):
            audio = getattr(result, "audio", None)
            if audio is None:
                continue
            if isinstance(audio, torch.Tensor):
                audio = audio.detach().cpu().numpy()
            chunks.append(np.asarray(audio).astype(np.float32, copy=False))

        if not chunks:
            raise RuntimeError("kokoro produced no audio")
        return np.concatenate(chunks, axis=-1)
