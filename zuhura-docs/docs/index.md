# Zuhura Mars

Zuhura Mars is a web application for exploring Mars with published planetary data. It shows the planet as a 3D globe and provides tools for rover route planning, terrain analysis, the planetary interior and questions about any location. The project was started for the NASA Space Apps Challenge 2026.

## Principles

- **Mars coordinates.** Positions use the IAU 2015 reference ellipsoid for Mars, and elevations are relative to the MOLA areoid.
- **Traceable data.** Values come from NASA Planetary Data System (PDS) and USGS Astrogeology products and are labelled as observed, measured, derived, model estimate or simulated.
- **Cited answers.** The assistant answers from catalogued datasets and analysis tools, and lists the sources it used.

## Repositories

| Repository | Contents |
| --- | --- |
| `zuhura-frontend` | React and CesiumJS web application |
| `zuhura-backend` | FastAPI service for spatial queries, analysis and the assistant |
| `zuhura-api` | OpenAPI 3.1 definition, JSON schemas and STAC extension |
| `zuhura-data` | Data acquisition and processing pipelines (PDS, COG tiling, validation) |
| `zuhura` | Docker Compose setup and development scripts |
| `zuhura-docs` | This documentation |

## Where to start

- [Getting started](developer/quickstart.md) explains how to run the stack locally.
- [System overview](architecture/system-overview.md) describes how the services fit together.
- [Mars coordinate systems](geodesy/mars-coordinate-systems.md) covers the reference frames used throughout.
