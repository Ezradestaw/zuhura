# zuhura-data

Acquisition and processing pipelines for the planetary datasets used by Zuhura Mars, and the catalogue that describes them.

## Contents

```
src/zuhura_data/   Python package: catalogue models, data access, spatial and terrain processing
scripts/           Command-line pipelines (download, process, validate)
catalogs/          Dataset catalogue and imagery coverage manifests (JSON)
specs/             Processing specifications
docs/              Integration and terrain format notes
tests/             Pytest suites
data/              Local data directory (raw, processed and tile outputs are not tracked)
```

## Pipelines

| Script | Purpose |
| --- | --- |
| `download_mola.py` | Download MOLA elevation products from PDS |
| `process_stage2_mola.py` | Correct and convert MOLA rasters to Cloud Optimized GeoTIFF |
| `build_stage3_mosaic.py` | Build the global MOLA mosaic |
| `discover_and_acquire_pilot_datasets.py` | Find and download CTX, HiRISE and THEMIS products for pilot areas |
| `prepare_regional_imagery.py`, `prepare_jezero_terrain.py` | Prepare regional imagery and terrain for Jezero |
| `build_stage5_catalog.py` | Build the dataset catalogue |
| `build_stage7_global_terrain.py`, `build_stage7_regional_terrain.py` | Generate quantized-mesh terrain tiles |
| `validate_mola_integrity.py`, `validate_stage7_continuity.py` | Check data integrity and tile continuity |

Validation scripts write their output to `reports/`, which is not tracked.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Raster processing scripts also need GDAL with Python bindings.

Raw and processed data can reach tens of gigabytes and stays out of git; see `.gitignore`.
