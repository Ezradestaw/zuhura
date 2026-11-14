# Zuhura Mars

Zuhura Mars is a web application for exploring Mars with published planetary data. It displays the planet as a 3D globe and provides rover route planning, terrain analysis, a model of the planetary interior, and an assistant that answers questions about any location with cited sources. The project was started for the NASA Space Apps Challenge 2026.

This repository contains the Docker Compose setup and development scripts that run the services together.

## Repositories

| Repository | Contents |
| --- | --- |
| [zuhura](https://github.com/Zuhura-Mars/zuhura) | Docker Compose environment, setup scripts, architecture decision records |
| [zuhura-frontend](https://github.com/Zuhura-Mars/zuhura-frontend) | React 18 and CesiumJS web application |
| [zuhura-backend](https://github.com/Zuhura-Mars/zuhura-backend) | FastAPI service: spatial queries, terrain analysis, route planning, assistant |
| [zuhura-api](https://github.com/Zuhura-Mars/zuhura-api) | OpenAPI 3.1 definition, JSON schemas, Mars STAC extension |
| [zuhura-data](https://github.com/Zuhura-Mars/zuhura-data) | Data acquisition and processing pipelines |
| [zuhura-docs](https://github.com/Zuhura-Mars/zuhura-docs) | Documentation site |
| [.github](https://github.com/Zuhura-Mars/.github) | Issue and pull request templates, shared CI workflow |

Clone the repositories side by side in one parent directory; the Compose file refers to them by relative path.

## Requirements

- Docker with Compose v2.20 or later
- Python 3.11 or later
- Node.js 20 or later

## Running locally

```bash
# Create .env from .env.example and check that docker, python3 and node are installed
./scripts/dev-setup.sh

# Compose reads two more environment files; create them and set the passwords
cp docker/.env.example docker/.env
cp ../zuhura-backend/.env.example ../zuhura-backend/.env

# Start PostgreSQL/PostGIS, Redis, the backend and the frontend
cd docker
docker compose up -d

# Check that the services respond
../scripts/healthcheck.sh
```

Default ports:

| Service | Port |
| --- | --- |
| Frontend | 3000 |
| Backend API | 8000 |
| PostgreSQL | 5432 |
| Redis | 6379 |

The assistant uses Google Gemini when `GEMINI_API_KEY` is set in the backend environment. Without a key it falls back to local analysis.

## Coordinate conventions

- Reference ellipsoid: IAU 2015 Mars (a = 3,396,190 m, c = 3,376,200 m)
- Latitude: planetocentric unless stated otherwise; conversions to planetographic are explicit
- Longitude: 0–360° east
- Elevation: metres above the MOLA areoid

See the [documentation](https://github.com/Zuhura-Mars/zuhura-docs) for details.
