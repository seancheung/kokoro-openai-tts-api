# Kokoro OpenAI-TTS API

**English** · [中文](./README.zh.md)

An [OpenAI TTS](https://platform.openai.com/docs/api-reference/audio/createSpeech)-compatible HTTP service wrapping [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) — a tiny (82M parameters) open-weight TTS model with 54 built-in voices across 9 languages.

## Features

- **OpenAI TTS compatible** — `POST /v1/audio/speech` with the same request shape as the OpenAI SDK
- **54 built-in voices** across 9 languages — American English, British English, Spanish, French, Hindi, Italian, Japanese, Brazilian Portuguese, Mandarin Chinese (full catalogue from Kokoro's [VOICES.md](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md))
- **Voice mixing** — pass a comma-separated list (`af_heart,af_bella`) to average the style embeddings
- **2 images** — `cuda` and `cpu`
- **Model weights downloaded at runtime** — nothing heavy baked into the image; HuggingFace cache is mounted for reuse
- **Multiple output formats** — `mp3`, `opus`, `aac`, `flac`, `wav`, `pcm`

## Available images

| Image | Device |
|---|---|
| `ghcr.io/seancheung/kokoro-openai-tts-api:cuda-latest` | CUDA 12.4 |
| `ghcr.io/seancheung/kokoro-openai-tts-api:latest`      | CPU |

Images are built for `linux/amd64`.

## Quick start

### 1. Run the container

GPU (recommended):

```bash
docker run --rm -p 8000:8000 --gpus all \
  -v $PWD/cache:/root/.cache \
  ghcr.io/seancheung/kokoro-openai-tts-api:cuda-latest
```

CPU:

```bash
docker run --rm -p 8000:8000 \
  -v $PWD/cache:/root/.cache \
  ghcr.io/seancheung/kokoro-openai-tts-api:latest
```

Model weights (~330 MB) are pulled from HuggingFace on first start. Individual voice `.pt` files (~500 KB each) are fetched lazily on first use. Mounting `/root/.cache` persists them across container restarts.

> **GPU prerequisites**: NVIDIA driver + [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) on Linux. On Windows use Docker Desktop + WSL2 + NVIDIA Windows driver (R470+); no host CUDA toolkit required.

### 2. docker-compose

See [`docker/docker-compose.example.yml`](./docker/docker-compose.example.yml).

## API usage

The service listens on port `8000` by default.

### GET `/v1/audio/voices`

List all 54 built-in voices.

```bash
curl -s http://localhost:8000/v1/audio/voices | jq
```

Response:

```json
{
  "object": "list",
  "data": [
    {
      "id": "af_heart",
      "lang_code": "a",
      "language": "American English",
      "gender": "female",
      "traits": "❤️",
      "grade": "A"
    }
  ]
}
```

`traits` and `grade` come from upstream [VOICES.md](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md) (grade: A best → F worst).

### POST `/v1/audio/speech`

OpenAI TTS-compatible endpoint.

```bash
curl -s http://localhost:8000/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "kokoro",
    "input": "Hello world, this is a test.",
    "voice": "af_heart",
    "response_format": "mp3",
    "speed": 1.0
  }' \
  -o out.mp3
```

Request fields:

| Field | Type | Description |
|---|---|---|
| `model` | string | Accepted but ignored (for OpenAI SDK compatibility) |
| `input` | string | Text to synthesize, up to 8000 characters |
| `voice` | string | Voice id from `/v1/audio/voices`, or a comma-separated list (averaged) |
| `response_format` | string | `mp3` (default) / `opus` / `aac` / `flac` / `wav` / `pcm` |
| `speed` | float | Playback speed, `0.25 - 4.0`, default `1.0` |
| `lang_code` | string | Optional override of the language pipeline (`a`/`b`/`e`/`f`/`h`/`i`/`j`/`p`/`z`, or aliases like `en-us`, `zh`). Defaults to the first character of the voice id |

Output audio is mono 24 kHz; `pcm` is raw s16le, matching OpenAI's default `pcm` format.

### Using the OpenAI Python SDK

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="sk-noop")

with client.audio.speech.with_streaming_response.create(
    model="kokoro",
    voice="af_heart",
    input="Hello world",
    response_format="mp3",
) as resp:
    resp.stream_to_file("out.mp3")
```

The `lang_code` extension can be passed through `extra_body={"lang_code": "a"}`.

### GET `/healthz`

Returns repo id, device, sample rate, and which language pipelines have been built so far.

## Built-in voices

All 54 voices published in `hexgrad/Kokoro-82M`. The authoritative catalogue is [VOICES.md](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md); `GET /v1/audio/voices` returns the same set. Voice id format: first char = language, second char = gender (`f`/`m`).

| Language | Female | Male |
|---|---|---|
| American English (`a`) | `af_heart` ❤️, `af_bella` 🔥, `af_nicole` 🎧, `af_aoede`, `af_kore`, `af_sarah`, `af_nova`, `af_sky`, `af_alloy`, `af_jessica`, `af_river` | `am_michael`, `am_fenrir`, `am_puck`, `am_echo`, `am_eric`, `am_liam`, `am_onyx`, `am_santa`, `am_adam` |
| British English (`b`) | `bf_emma`, `bf_isabella`, `bf_alice`, `bf_lily` | `bm_george`, `bm_fable`, `bm_lewis`, `bm_daniel` |
| Japanese (`j`) | `jf_alpha`, `jf_gongitsune`, `jf_nezumi`, `jf_tebukuro` | `jm_kumo` |
| Mandarin Chinese (`z`) | `zf_xiaobei`, `zf_xiaoni`, `zf_xiaoxiao`, `zf_xiaoyi` | `zm_yunjian`, `zm_yunxi`, `zm_yunxia`, `zm_yunyang` |
| Spanish (`e`) | `ef_dora` | `em_alex`, `em_santa` |
| French (`f`) | `ff_siwis` | — |
| Hindi (`h`) | `hf_alpha`, `hf_beta` | `hm_omega`, `hm_psi` |
| Italian (`i`) | `if_sara` | `im_nicola` |
| Brazilian Portuguese (`p`) | `pf_dora` | `pm_alex`, `pm_santa` |

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `KOKORO_MODEL` | `hexgrad/Kokoro-82M` | HuggingFace repo id (or local path) hosting the model weights and voice packs |
| `KOKORO_CUDA_INDEX` | `0` | Selects `cuda:N` in the CUDA image (CPU image ignores it) |
| `KOKORO_CACHE_DIR` | — | Sets `HF_HOME` before model load |
| `KOKORO_PRELOAD_LANGS` | — | Comma-separated lang codes to eagerly build at startup (e.g. `a,b`) |
| `KOKORO_PRELOAD_VOICES` | — | Comma-separated voice ids to eagerly download at startup |
| `KOKORO_USE_TRANSFORMER_G2P` | `false` | Use Misaki's transformer-based G2P for English (heavier, slower, higher quality) |
| `KOKORO_SPLIT_PATTERN` | `\n+` | Regex used to split long input into chunks before inference |
| `MAX_INPUT_CHARS` | `8000` | Upper bound for the `input` field |
| `DEFAULT_RESPONSE_FORMAT` | `mp3` | |
| `HOST` | `0.0.0.0` | |
| `PORT` | `8000` | |
| `LOG_LEVEL` | `info` | |

## Building images locally

Initialize the submodule first (the workflow does this automatically).

```bash
git submodule update --init --recursive

# CUDA image
docker buildx build -f docker/Dockerfile.cuda \
  -t kokoro-openai-tts-api:cuda .

# CPU image
docker buildx build -f docker/Dockerfile.cpu \
  -t kokoro-openai-tts-api:cpu .
```

## Caveats

- **No per-voice audio preview** — the built-in voices do not come with sample audio; preview by calling `/v1/audio/speech` with any short text.
- **Concurrency** — a single `KModel` is not thread-safe; the service serialises inference with an asyncio Lock. Scale out by running more containers behind a load balancer.
- **Long text** — requests whose `input` exceeds `MAX_INPUT_CHARS` (default 8000) return 413. Within a request Kokoro chunks text around sentence boundaries (~510 phoneme tokens per chunk) and concatenates the outputs.
- **Streaming is not supported** — the endpoint returns the complete audio when generation finishes.
- **espeak-ng fallback** — used for non-English languages and for out-of-vocabulary English words. Both images ship with `espeak-ng` preinstalled.
- **No built-in auth** — deploy behind a reverse proxy (Nginx, Cloudflare, etc.) if you need token-based access control.
- **Pronunciation overrides** — inherited from Kokoro: `[Kokoro](/kˈOkəɹO/)` inline phonemes, stress markers (`ˈ`, `ˌ`), `[word](-1)` / `[word](+2)` stress shifts.

## Project layout

```
.
├── kokoro/                    # read-only submodule, never modified
├── app/                       # FastAPI application
│   ├── server.py
│   ├── engine.py              # KModel + per-lang KPipeline cache + inference
│   ├── voices.py              # built-in voice registry
│   ├── audio.py               # multi-format encoder
│   ├── config.py
│   └── schemas.py
├── docker/
│   ├── Dockerfile.cuda
│   ├── Dockerfile.cpu
│   ├── requirements.api.txt
│   ├── requirements.kokoro.txt
│   ├── entrypoint.sh
│   └── docker-compose.example.yml
├── .github/workflows/
│   └── build-images.yml       # cuda + cpu matrix build
└── README.md
```

## Acknowledgements

Built on top of [hexgrad/kokoro](https://github.com/hexgrad/kokoro) and the [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) model weights (Apache 2.0).
