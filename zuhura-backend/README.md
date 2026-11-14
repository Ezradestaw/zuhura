# zuhura-backend

FastAPI service for Zuhura Mars. It provides elevation and terrain analysis, map tiles, rover route planning, the interior model, image analysis, the workspace, and the Ask Zuhura assistant.

## Requirements

- Python 3.11 or later
- GDAL with Python bindings (used for raster access)

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn zuhura.api.main:app --reload --port 8000
```

API documentation is served at `http://localhost:8000/docs`.

## Configuration

Settings are read from `.env` (see `.env.example`). The main ones:

| Variable | Purpose |
| --- | --- |
| `CORS_ORIGINS` | Allowed browser origins |
| `TRUSTED_PROXY_CIDRS` | Proxies allowed to set `X-Forwarded-For` |
| `GEMINI_API_KEY` | Enables Gemini for the assistant; without it, answers use local analysis |
| `GEMINI_MODEL` | Gemini model name |
| `AI_RATE_LIMIT` | Assistant requests per minute per client IP (default 60) |

## Tests

```bash
pytest
```

## Package layout

```
src/zuhura/
  api/v1/                 HTTP endpoints, one module per area
  ai/                     Assistant: Gemini client, tools, grounding, sessions
  core/                   Settings, cache, metrics, security middleware
  geodesy/                Mars ellipsoid constants and coordinate conversions
  terrain_intelligence/   Slope, curvature, roughness and elevation profiles
  navigation/             Rover mobility model and A* route search
  interior/               Interior layer models
  pinpoint/, vision/      Image location and image analysis
  segmentation/           Region discovery
  environment/            Atmosphere, temperature and solar power model
  provenance/             Epistemic status and reproducibility records
  workspace/              Studies, notes and activity
tests/
  unit/, integration/, performance/
```
