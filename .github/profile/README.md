# Zuhura Mars

Zuhura Mars is a web application for exploring Mars with published planetary data: a 3D globe, rover route planning, terrain analysis, a model of the planetary interior, and an assistant that answers with cited sources. The project was started for the NASA Space Apps Challenge 2026.

## Repositories

| Repository | Contents |
| --- | --- |
| [zuhura](https://github.com/Zuhura-Mars/zuhura) | Docker Compose environment and setup scripts |
| [zuhura-frontend](https://github.com/Zuhura-Mars/zuhura-frontend) | React and CesiumJS web application |
| [zuhura-backend](https://github.com/Zuhura-Mars/zuhura-backend) | FastAPI service |
| [zuhura-api](https://github.com/Zuhura-Mars/zuhura-api) | OpenAPI definition, JSON schemas, STAC extension |
| [zuhura-data](https://github.com/Zuhura-Mars/zuhura-data) | Data pipelines and catalogue |
| [zuhura-docs](https://github.com/Zuhura-Mars/zuhura-docs) | Documentation |

## Conventions

- Positions use the IAU 2015 Mars ellipsoid (a = 3,396.19 km, c = 3,376.20 km); elevations are relative to the MOLA areoid.
- Every dataset and derived value records its source and whether it is observed, measured, derived, a model estimate or simulated.
- Assistant answers list the datasets and tools they rely on.
