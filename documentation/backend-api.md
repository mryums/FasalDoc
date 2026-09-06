# FasalDoc Member 1 Backend

## Run locally

1. Create and activate a Python virtual environment.
2. Install dependencies with `python -m pip install -r requirements.txt`.
3. Copy `.env.example` to `.env`.
4. Start the API with `uvicorn backend.main:app --reload --port 8000`.

With no usable `DASHSCOPE_API_KEY`, the backend runs in mock mode. A blank key and template values such as `your_key_here` are treated as unconfigured.

## Qwen / DashScope credentials

To enable real Qwen requests, create a DashScope API key in the Alibaba Cloud Model Studio / DashScope console for the same region as `DASHSCOPE_BASE_URL`, then set it only as `DASHSCOPE_API_KEY` in local `.env` or the deployment platform's encrypted environment-variable store. Do not add it to source files, frontend variables, Vercel or Render configuration files, test fixtures, or documentation.

Deployments must set `DASHSCOPE_API_KEY` in their platform secret settings. The backend automatically selects real mode when the key is present and mock mode when it is absent.

## Environment variables

- `DASHSCOPE_API_KEY`: backend-only secret that enables real mode.
- `DASHSCOPE_BASE_URL`: OpenAI-compatible DashScope endpoint.
- `DASHSCOPE_VISION_MODEL`, `DASHSCOPE_TEXT_MODEL`, `DASHSCOPE_ASR_MODEL`, `DASHSCOPE_TTS_MODEL`: Qwen model identifiers.
- `DASHSCOPE_TTS_VOICE`: configured TTS voice.
- `DASHSCOPE_TIMEOUT_SECONDS`, `DASHSCOPE_MAX_RETRIES`: SDK request limits.
- `DASHSCOPE_TTS_MAX_LENGTH`: maximum input characters accepted by `/speak`.
- `DASHSCOPE_CONFIDENCE_THRESHOLD`: advice confidence threshold in percent.
- `CORS_ALLOW_ORIGINS`: comma-separated explicit browser origins.
- `BACKEND_PORT`: local server port selection.

## API

- `POST /diagnose`: multipart `image` (JPEG, PNG, or WEBP; maximum 10 MB) and optional `question` (maximum 1000 characters). Image-only requests remain supported.
- `POST /ask-followup`: JSON `{ "question": "..." }`; this endpoint is stateless.
- `POST /transcribe`: multipart `audio` (supported audio MIME type, maximum 10 MB). The server verifies the audio header before transcription.
- `POST /speak`: JSON `{ "text": "..." }`; returns `audio/wav`.
- `GET /health`: non-secret provider mode, configuration state, and model identifiers.

AI service failures return a typed, farmer-safe API error. Provider exception details and credentials are never included in responses.
