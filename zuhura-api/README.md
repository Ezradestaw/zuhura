# zuhura-api

Interface definitions shared by the Zuhura Mars services. The backend, frontend and data pipelines follow the contracts defined here.

## Contents

| Path | Description |
| --- | --- |
| `openapi/zuhura-v1.yaml` | OpenAPI 3.1 definition of the REST API |
| `schemas/dataset.json` | Dataset catalogue record |
| `schemas/spatial_query.json` | Point, bounding box, transect and feature search parameters |
| `schemas/ai_query.json` | Assistant requests, tool calls and citations |
| `schemas/provenance.json` | Provenance and epistemic status |
| `schemas/mobility_simulation.json` | Rover mobility simulation requests and results |
| `stac/mars-stac-extension.json` | STAC extension for Mars reference systems, processing levels and the areoid datum |

## Validation

```bash
npm run validate                      # Node
python scripts/validate_schemas.py    # Python
```

Update the OpenAPI definition and schemas in the same change as the code that depends on them.
