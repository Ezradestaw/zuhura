# Zuhura 🪐
### Mars Digital Twin, Planetary GIS & Autonomous Scientific Intelligence Platform

[![Vercel](https://img.shields.io/badge/Deployed%20with-Vercel-black?style=flat&logo=vercel)](https://zuhura-frontend.vercel.app)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Vite-61DAFB?style=flat&logo=react)](https://vitejs.dev/)
[![Cesium](https://img.shields.io/badge/Globe-CesiumJS-6A9955?style=flat)](https://cesium.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Zuhura** is an open-source, mission-grade planetary digital twin of Mars. It merges authentic NASA, USGS, and ESA planetary science datasets with a high-fidelity 3D Cesium/Three.js digital twin, an authoritative IAU 2015 ellipsoidal geodesy engine, and an autonomous AI planetary research scientist grounded with Google Gemini.

---

## 🌟 Key Capabilities

- **3D Planetary Exploration**: Ultra-high-resolution multi-tier globe supporting USGS Viking MDIM 2.1 natural color basemap, MRO CTX, HiRISE local detail, and MOLA topographic relief.
- **Mars AI Research Scientist**: An autonomous planetary scientist powered by Google Gemini, capable of reasoning over spatial coordinates, crater morphology, rover traverses, and returning verified scientific citations.
- **Mission & Surface Telemetry**: Interactive 3D rover traverses for Perseverance, Curiosity, Opportunity, and Spirit with authentic landing sites and sol-by-sol tracking.
- **Planetary Geodesy & Terrain Engine**: Sub-meter IAU/IAG 2015 biaxial ellipsoid geodesy, slope profiling, elevation transects, and areoid datum reference.
- **Scientific Data Catalog**: STAC-compatible planetary data catalog referencing NASA PDS, USGS Astrogeology, and Mars Trek WMTS services.

---

## 🏗️ Architecture

```
zuhura/
├── zuhura-frontend/     # React 18 + TypeScript + Vite + CesiumJS + Tailwind CSS
├── zuhura-backend/      # FastAPI + PROJ + GDAL + Gemini Scientific Assistant
├── zuhura-api/          # OpenAPI schemas and STAC catalog specifications
├── zuhura-data/         # Planetary features, missions, quadrangles, rover traverses
├── zuhura-docs/         # MkDocs Material technical documentation
└── zuhura/docker/       # Docker Compose multi-service deployment orchestrator
```

---

## 🚀 Quick Start (Local Development)

### 1. Prerequisites
- Node.js >= 20.x
- Python >= 3.11
- Docker & Docker Compose (optional for full-stack containerization)

### 2. Backend Setup
```bash
cd zuhura-backend
cp ../.env.example .env
# Add your GEMINI_API_KEY to .env
pip install -e .
uvicorn zuhura.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup
```bash
cd zuhura-frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to explore Mars.

---

## ☁️ Deployment

- **Frontend**: Hosted on [Vercel](https://zuhura-frontend.vercel.app)
- **Backend**: Containerized via Docker / Render / Koyeb
- **Documentation**: Built with MkDocs Material (`mkdocs gh-deploy`)

---

## 📜 Scientific Datasets & Attribution

- **Viking Orbiter**: USGS Astrogeology Science Center / NASA PDS
- **MOLA**: NASA Goddard Space Flight Center / MGS Science Team
- **CTX & HiRISE**: Malin Space Science Systems (MSSS) & University of Arizona / NASA PDS
- **Mars Trek**: NASA Solar System Treks Project / JPL-Caltech
- **Geodesy**: IAU/IAG Working Group on Cartographic Coordinates and Rotational Elements (WGCCRE 2015)
