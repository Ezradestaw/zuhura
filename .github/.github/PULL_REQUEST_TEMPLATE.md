## Description
What does this change do, and why?

Fixes # (issue)

## Repository / Component Affected
- [ ] `zuhura` (Platform orchestration, Docker, governance)
- [ ] `zuhura-frontend` (CesiumJS 3D Mars globe, UI components, Zustand stores)
- [ ] `zuhura-backend` (FastAPI services, spatial analysis, AI orchestration)
- [ ] `zuhura-api` (OpenAPI specs, JSON schemas, contracts)
- [ ] `zuhura-data` (PDS ingestion, STAC catalogs, GDAL pipelines)
- [ ] `zuhura-docs` (Technical & scientific documentation)
- [ ] `.github` (CI/CD workflows, templates)

## Mars data conventions
- [ ] No Earth conventions (WGS84) applied to Mars data.
- [ ] Latitude conventions are explicitly documented (Planetocentric vs Planetographic).
- [ ] Longitudes are east-positive (0–360° or −180–180°, stated explicitly).
- [ ] Scientific provenance, processing level, and citations are maintained.
- [ ] Assistant changes do not produce claims without a cited source.

## Checks
- [ ] Tests added or updated, and passing.
- [ ] No large data files committed.
- [ ] Frontend type check passes (`npm run typecheck`).
- [ ] Backend lint passes (`ruff check`).
