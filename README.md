# Zuhura

A web app for exploring Mars on a 3D globe using public NASA and USGS data.

Live site: https://zuhura-frontend.vercel.app

## What it does

- **Globe**: Viking colour mosaic for the whole planet, with sharper CTX and HiRISE images around
  Jezero crater, and MOLA elevation for heights and shading.
- **Traverse**: pick a start and a destination on the globe and the server finds a drivable path
  with the A* algorithm, going around slopes and rough ground.
- **Ask Zuhura**: a chat assistant (Google Gemini) that can look up elevation, slope and dataset
  information for the place you are looking at.
- Smaller tools: distance/area measuring, elevation profiles, layer comparison, rover images,
  Mount Sharp route, a dataset catalogue and a workspace for notes.

## Layout

```
zuhura-frontend/   React + TypeScript + Vite + CesiumJS + Tailwind
zuhura-backend/    FastAPI (Python): terrain, A* routing, assistant, data endpoints
zuhura-data/       Datasets and the code that reads them
zuhura-docs/       Documentation site (MkDocs)
```

## Running locally

Backend (needs Python 3.11+ and GDAL):

```bash
cd zuhura-backend
cp .env.example .env        # put your GEMINI_API_KEY in .env
pip install -e .
uvicorn zuhura.api.main:app --port 8000 --reload
```

Frontend (needs Node 20+):

```bash
cd zuhura-frontend
npm install
npm run dev                 # http://localhost:3000, /api is proxied to :8000
```

Tests: `pytest` in `zuhura-backend`, `npx vitest run` in `zuhura-frontend`.

## Data sources

- MOLA MEGDR elevation, 128 px/deg: NASA PDS Geosciences Node / MGS MOLA team
- Viking MDIM 2.1 colour mosaic: USGS Astrogeology
- CTX and HiRISE images: MSSS, University of Arizona, NASA PDS
- Mars Trek tile services: NASA Solar System Treks / JPL
- Mars reference ellipsoid: IAU WGCCRE 2015
