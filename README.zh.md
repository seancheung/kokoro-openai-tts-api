# Kokoro OpenAI-TTS API

[English](./README.md) · **中文**

一个 [OpenAI TTS](https://platform.openai.com/docs/api-reference/audio/createSpeech) 兼容的 HTTP 服务，对 [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)（仅 82M 参数的开源权重 TTS 模型）进行封装。

## 特性

- **OpenAI TTS 兼容**：`POST /v1/audio/speech`，请求体格式与 OpenAI SDK 一致
- **54 个内置音色，覆盖 9 种语言**：美/英英语、西班牙语、法语、印地语、意大利语、日语、葡萄牙语、普通话（完整列表见 Kokoro 的 [VOICES.md](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md)）
- **多语言推理**：Kokoro 的 G2P 链覆盖多个语言，任意音色都可以通过 `lang_code` 切换到其它语言通道
- **音色混合**：`voice` 字段传逗号分隔的多个 id（如 `af_heart,af_bella`）即可对风格嵌入取平均
- **2 个镜像**：`cuda` 与 `cpu`
- **模型运行时下载**：不打包进镜像，HuggingFace 缓存目录挂载后可复用
- **多种输出格式**：`mp3`、`opus`、`aac`、`flac`、`wav`、`pcm`

## 可用镜像

| 镜像 | 设备 |
|---|---|
| `ghcr.io/seancheung/kokoro-openai-tts-api:cuda-latest` | CUDA 12.4 |
| `ghcr.io/seancheung/kokoro-openai-tts-api:latest`      | CPU |

镜像仅构建 `linux/amd64`。

## 快速开始

### 1. 运行容器

GPU 版本（推荐）：

```bash
docker run --rm -p 8000:8000 --gpus all \
  -v $PWD/cache:/root/.cache \
  ghcr.io/seancheung/kokoro-openai-tts-api:cuda-latest
```

CPU 版本：

```bash
docker run --rm -p 8000:8000 \
  -v $PWD/cache:/root/.cache \
  ghcr.io/seancheung/kokoro-openai-tts-api:latest
```

首次启动会从 HuggingFace 下载模型权重（约 330 MB）。单个音色 `.pt` 文件（约 500 KB）在首次使用时按需下载。挂载 `/root/.cache` 可让权重在容器重启后复用。

> **GPU 要求**：宿主机需安装 NVIDIA 驱动与 [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)。Windows 需 Docker Desktop + WSL2 + NVIDIA Windows 驱动。

### 2. docker-compose

参考 [`docker/docker-compose.example.yml`](./docker/docker-compose.example.yml)。

## API 用法

服务默认监听 `8000` 端口。

### GET `/v1/audio/voices`

列出全部 54 个内置音色。

```bash
curl -s http://localhost:8000/v1/audio/voices | jq
```

返回：

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

`traits` 与 `grade` 来自上游 [VOICES.md](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md)（grade：A 最好 → F 最差）。

### POST `/v1/audio/speech`

OpenAI TTS 兼容接口。

```bash
curl -s http://localhost:8000/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "kokoro",
    "input": "你好世界，这是一段测试语音。",
    "voice": "zf_xiaobei",
    "response_format": "mp3",
    "speed": 1.0
  }' \
  -o out.mp3
```

请求字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `model` | string | 接受但忽略（为了与 OpenAI SDK 兼容） |
| `input` | string | 要合成的文本，最长 8000 字符 |
| `voice` | string | `/v1/audio/voices` 中的 id，或逗号分隔的多个 id（自动求平均） |
| `response_format` | string | `mp3`（默认） / `opus` / `aac` / `flac` / `wav` / `pcm` |
| `speed` | float | 语速，范围 `0.25 - 4.0`，默认 `1.0` |
| `lang_code` | string | 可选，覆盖语言通道（`a`/`b`/`e`/`f`/`h`/`i`/`j`/`p`/`z`，或 `en-us`、`zh` 等别名）。默认取 `voice` 首字符 |

输出音频为单声道 24 kHz；`pcm` 为裸的 s16le 数据，与 OpenAI 默认 `pcm` 格式一致。

### 使用 OpenAI Python SDK

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

扩展字段 `lang_code` 可通过 `extra_body={"lang_code": "a"}` 传入。

### GET `/healthz`

返回仓库 id、设备、采样率以及当前已构建的语言通道列表，用于健康检查。

## 内置音色

全部 54 个官方音色，同步自 [VOICES.md](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md)，也可通过 `GET /v1/audio/voices` 获取。音色 id 首字符决定语言，第二个字符 `f`/`m` 表示女声/男声。

| 语言 | 女声 | 男声 |
|---|---|---|
| 美式英语（`a`） | `af_heart` ❤️、`af_bella` 🔥、`af_nicole` 🎧、`af_aoede`、`af_kore`、`af_sarah`、`af_nova`、`af_sky`、`af_alloy`、`af_jessica`、`af_river` | `am_michael`、`am_fenrir`、`am_puck`、`am_echo`、`am_eric`、`am_liam`、`am_onyx`、`am_santa`、`am_adam` |
| 英式英语（`b`） | `bf_emma`、`bf_isabella`、`bf_alice`、`bf_lily` | `bm_george`、`bm_fable`、`bm_lewis`、`bm_daniel` |
| 日语（`j`） | `jf_alpha`、`jf_gongitsune`、`jf_nezumi`、`jf_tebukuro` | `jm_kumo` |
| 普通话（`z`） | `zf_xiaobei`、`zf_xiaoni`、`zf_xiaoxiao`、`zf_xiaoyi` | `zm_yunjian`、`zm_yunxi`、`zm_yunxia`、`zm_yunyang` |
| 西班牙语（`e`） | `ef_dora` | `em_alex`、`em_santa` |
| 法语（`f`） | `ff_siwis` | — |
| 印地语（`h`） | `hf_alpha`、`hf_beta` | `hm_omega`、`hm_psi` |
| 意大利语（`i`） | `if_sara` | `im_nicola` |
| 巴西葡萄牙语（`p`） | `pf_dora` | `pm_alex`、`pm_santa` |

## 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `KOKORO_REPO_ID` | `hexgrad/Kokoro-82M` | 模型权重与音色包的 HuggingFace 仓库 id |
| `KOKORO_DEVICE` | `auto` | `auto` 按 CUDA > MPS > CPU 优先级。也可强制 `cuda` / `mps` / `cpu` |
| `KOKORO_CUDA_INDEX` | `0` | `cuda` / `auto` 时选择的 `cuda:N` |
| `KOKORO_CACHE_DIR` | — | 加载模型前写入 `HF_HOME` |
| `KOKORO_PRELOAD_LANGS` | — | 启动时预构建的语言通道（逗号分隔，如 `a,b`） |
| `KOKORO_PRELOAD_VOICES` | — | 启动时预下载的音色 id（逗号分隔） |
| `KOKORO_USE_TRANSFORMER_G2P` | `false` | 英语 G2P 使用 Misaki 的 transformer 版本（更慢，质量更高） |
| `KOKORO_SPLIT_PATTERN` | `\n+` | 长文本切块使用的正则 |
| `MAX_INPUT_CHARS` | `8000` | `input` 字段上限 |
| `DEFAULT_RESPONSE_FORMAT` | `mp3` | |
| `HOST` | `0.0.0.0` | |
| `PORT` | `8000` | |
| `LOG_LEVEL` | `info` | |

## 本地构建镜像

构建前需先初始化 submodule（workflow 已处理）。

```bash
git submodule update --init --recursive

# CUDA 镜像
docker buildx build -f docker/Dockerfile.cuda \
  -t kokoro-openai-tts-api:cuda .

# CPU 镜像
docker buildx build -f docker/Dockerfile.cpu \
  -t kokoro-openai-tts-api:cpu .
```

## 局限 / 注意事项

- **内置音色无预置试听样本**：请通过 `/v1/audio/speech` 发一段短文本来试听。
- **并发**：单个 `KModel` 非线程安全，服务内部用 asyncio Lock 串行化。并发请求依赖横向扩容（多容器 + 负载均衡）。
- **长文本**：超过 `MAX_INPUT_CHARS`（默认 8000）返回 413；请求内部 Kokoro 会按句切块（每块约 510 个音素）再拼接输出。
- **不支持流式返回**：生成完成后一次性返回。
- **espeak-ng 回退**：用于非英语语言以及英语 OOD 单词，两个镜像均已预装 `espeak-ng`。
- **无内置鉴权**：如需 token 访问控制，请在反向代理层（Nginx、Cloudflare 等）做。
- **发音控制**：沿用 Kokoro 原生语法——内联音标 `[Kokoro](/kˈOkəɹO/)`、重音 `ˈ` / `ˌ`、`[word](-1)` / `[word](+2)` 升降重音。

## 目录结构

```
.
├── kokoro/                    # 只读 submodule，不修改
├── app/                       # FastAPI 应用
│   ├── server.py
│   ├── engine.py              # KModel + 按语言缓存的 KPipeline + 推理
│   ├── voices.py              # 内置音色注册表
│   ├── audio.py               # 多格式编码
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
│   └── build-images.yml       # cuda + cpu 矩阵构建
└── README.md
```

## 致谢

基于 [hexgrad/kokoro](https://github.com/hexgrad/kokoro) 与 [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) 权重（Apache 2.0）。
