from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response

from .audio import CONTENT_TYPES, encode
from .config import get_settings
from .engine import TTSEngine
from .schemas import HealthResponse, SpeechRequest, VoiceInfo, VoiceList
from .voices import VoiceCatalog

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())
    app.state.settings = settings
    app.state.catalog = VoiceCatalog()
    app.state.engine = None
    try:
        app.state.engine = TTSEngine(settings, app.state.catalog)
    except Exception:
        log.exception("failed to load Kokoro model")
        raise
    yield


app = FastAPI(title="Kokoro OpenAI-TTS API", version="1.0.0", lifespan=lifespan)


@app.get("/healthz", response_model=HealthResponse)
async def healthz(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    engine: TTSEngine | None = request.app.state.engine
    if engine is None:
        return HealthResponse(status="loading", repo_id=settings.kokoro_repo_id)
    return HealthResponse(
        status="ok",
        repo_id=settings.kokoro_repo_id,
        device=engine.device,
        sample_rate=engine.sample_rate,
        loaded_langs=engine.loaded_langs,
    )


@app.get("/v1/audio/voices", response_model=VoiceList)
async def list_voices(request: Request) -> VoiceList:
    catalog: VoiceCatalog = request.app.state.catalog
    data = [
        VoiceInfo(
            id=v.id,
            lang_code=v.lang_code,
            language=v.language,
            gender=v.gender,
            traits=v.traits,
            grade=v.grade,
        )
        for v in catalog.all().values()
    ]
    return VoiceList(data=data)


@app.post("/v1/audio/speech")
async def create_speech(body: SpeechRequest, request: Request):
    settings = request.app.state.settings
    engine: TTSEngine = request.app.state.engine

    text = (body.input or "").strip()
    if not text:
        raise HTTPException(status_code=422, detail="input is empty")
    if len(text) > settings.max_input_chars:
        raise HTTPException(
            status_code=413,
            detail=f"input exceeds {settings.max_input_chars} chars",
        )
    if body.response_format not in CONTENT_TYPES:
        raise HTTPException(
            status_code=422, detail=f"unsupported response_format: {body.response_format}",
        )

    voice_spec = (body.voice or "").strip()
    if not voice_spec:
        raise HTTPException(status_code=422, detail="voice is empty")

    try:
        samples = await engine.synthesize(
            text,
            voice_spec=voice_spec,
            response_speed=body.speed,
            lang_code=body.lang_code,
        )
    except HTTPException:
        raise
    except Exception as e:
        log.exception("inference failed")
        raise HTTPException(status_code=500, detail=f"inference failed: {e}") from e

    try:
        audio_bytes, content_type = encode(samples, engine.sample_rate, body.response_format)
    except Exception as e:
        log.exception("encoding failed")
        raise HTTPException(status_code=500, detail=f"encoding failed: {e}") from e

    return Response(content=audio_bytes, media_type=content_type)
