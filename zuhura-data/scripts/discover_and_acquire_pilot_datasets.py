#!/usr/bin/env python3
"""
Zuhura Planetary Digital Twin - Stage 4: THEMIS, CTX, and HiRISE Discovery & Pilot Acquisition
Implements:
  1. Automated PDS ODE REST API metadata-first discovery over Jezero Crater (18-19N, 77-78E)
  2. Catalogs generation for THEMIS, CTX, and HiRISE
  3. Controlled, documented pilot downloads for all three instruments
  4. Cryptographic checksums and acquisition manifest generation
"""

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

REPO_ROOT = Path("/home/anonymous/Zuhura/zuhura-data")
ODE_BASE_URL = "https://oderest.rsl.wustl.edu/live2/"

# Directory Architecture
DIRS = [
    REPO_ROOT / "data/raw/themis",
    REPO_ROOT / "data/processed/themis",
    REPO_ROOT / "data/derived/themis",
    REPO_ROOT / "data/raw/ctx",
    REPO_ROOT / "data/processed/ctx",
    REPO_ROOT / "data/derived/ctx",
    REPO_ROOT / "data/raw/hirise",
    REPO_ROOT / "data/processed/hirise",
    REPO_ROOT / "data/derived/hirise",
    REPO_ROOT / "catalogs",
    REPO_ROOT / "reports",
]

# Common Scientific Region: Jezero Crater (Perseverance Landing Site)
TARGET_REGION = {
    "name": "Jezero Crater",
    "minlat": 18.0,
    "maxlat": 19.0,
    "westlon": 76.5,
    "eastlon": 78.5,
    "description": "Perseverance rover landing site and ancient delta-lake system in Nili Fossae"
}


def setup_directories():
    for d in DIRS:
        d.mkdir(parents=True, exist_ok=True)
    print("  Directory structure verified.")


def query_ode_inventory(ihid: str, iid: str, pt: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Query NASA PDS ODE REST API for product metadata."""
    params = {
        "target": "mars",
        "query": "product",
        "results": "m",
        "output": "json",
        "ihid": ihid,
        "iid": iid,
        "pt": pt,
        "minlat": TARGET_REGION["minlat"],
        "maxlat": TARGET_REGION["maxlat"],
        "westlon": TARGET_REGION["westlon"],
        "eastlon": TARGET_REGION["eastlon"],
        "limit": limit
    }
    response = requests.get(ODE_BASE_URL, params=params, timeout=45)
    response.raise_for_status()
    data = response.json()

    products = data.get("ODEResults", {}).get("Products", {}).get("Product", [])
    if isinstance(products, dict):
        products = [products]
    return products


def download_file_with_checksum(url: str, dest_path: Path) -> Dict[str, Any]:
    """Download a file with curl (supporting resume and retry) and calculate SHA-256."""
    import subprocess
    temp_path = dest_path.with_suffix(dest_path.suffix + ".part")
    if dest_path.exists() and dest_path.stat().st_size > 0:
        # File already exists, verify hash
        h = hashlib.sha256()
        with open(dest_path, "rb") as f:
            while chunk := f.read(1024 * 1024):
                h.update(chunk)
        return {
            "status": "already_downloaded",
            "size_bytes": dest_path.stat().st_size,
            "sha256": h.hexdigest(),
            "path": str(dest_path)
        }

    # Run curl with resume support
    cmd = [
        "curl", "-fL",
        "--retry", "5",
        "--retry-delay", "3",
        "--connect-timeout", "30",
        "-C", "-",
        "-o", str(temp_path),
        url
    ]
    subprocess.run(cmd, check=True)

    # Compute SHA-256
    h = hashlib.sha256()
    with open(temp_path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)

    temp_path.replace(dest_path)
    return {
        "status": "downloaded",
        "size_bytes": dest_path.stat().st_size,
        "sha256": h.hexdigest(),
        "path": str(dest_path)
    }


def execute_discovery() -> Dict[str, Any]:
    print("\n--- Task 4.5: Metadata-First Discovery via NASA PDS ODE ---")

    # 1. THEMIS Discovery
    print("  Querying THEMIS IR RDR inventory over Jezero Crater...")
    themis_prods = query_ode_inventory("ODY", "THEMIS", "IRRDR", limit=10)
    themis_cat = {
        "instrument": "THEMIS",
        "mission": "2001 Mars Odyssey",
        "query_region": TARGET_REGION,
        "product_type": "IRRDR (Infrared Reduced Data Record)",
        "count": len(themis_prods),
        "products": themis_prods
    }
    themis_cat_path = REPO_ROOT / "catalogs/themis_jezero_inventory.json"
    with open(themis_cat_path, "w", encoding="utf-8") as f:
        json.dump(themis_cat, f, indent=2)
    print(f"    Saved THEMIS inventory: {themis_cat_path} ({len(themis_prods)} products)")

    # 2. CTX Discovery
    print("  Querying CTX EDR inventory over Jezero Crater...")
    ctx_prods = query_ode_inventory("MRO", "CTX", "EDR", limit=10)
    ctx_cat = {
        "instrument": "CTX",
        "mission": "Mars Reconnaissance Orbiter",
        "query_region": TARGET_REGION,
        "product_type": "EDR (Experiment Data Record)",
        "count": len(ctx_prods),
        "products": ctx_prods
    }
    ctx_cat_path = REPO_ROOT / "catalogs/ctx_jezero_inventory.json"
    with open(ctx_cat_path, "w", encoding="utf-8") as f:
        json.dump(ctx_cat, f, indent=2)
    print(f"    Saved CTX inventory: {ctx_cat_path} ({len(ctx_prods)} products)")

    # 3. HiRISE Discovery
    print("  Querying HiRISE RDR inventory over Jezero Crater...")
    hirise_prods = query_ode_inventory("MRO", "HIRISE", "RDRV11", limit=10)
    hirise_cat = {
        "instrument": "HiRISE",
        "mission": "Mars Reconnaissance Orbiter",
        "query_region": TARGET_REGION,
        "product_type": "RDRV11 (Reduced Data Record v1.1)",
        "count": len(hirise_prods),
        "products": hirise_prods
    }
    hirise_cat_path = REPO_ROOT / "catalogs/hirise_jezero_inventory.json"
    with open(hirise_cat_path, "w", encoding="utf-8") as f:
        json.dump(hirise_cat, f, indent=2)
    print(f"    Saved HiRISE inventory: {hirise_cat_path} ({len(hirise_prods)} products)")

    return {
        "themis_count": len(themis_prods),
        "ctx_count": len(ctx_prods),
        "hirise_count": len(hirise_prods),
    }


def execute_pilot_acquisition() -> Dict[str, Any]:
    print("\n--- Task 4.6: Initial Documented Pilot Acquisition ---")
    manifest = {
        "acquisition_timestamp": datetime.now(timezone.utc).isoformat(),
        "target_region": TARGET_REGION,
        "pilot_products": {}
    }

    # -------------------------------------------------------------------------
    # 1. THEMIS Pilot: I02413002RDR (Centered at 18.477 N, 77.384 E over Jezero)
    # -------------------------------------------------------------------------
    print("  [1/3] Downloading THEMIS Pilot Observation (I02413002RDR)...")
    themis_dir = REPO_ROOT / "data/raw/themis"
    themis_files = [
        {
            "name": "I02413002RDR.QUB",
            "url": "https://static.mars.asu.edu/pds/ODTSDP_v1/data/odtir1_0003/i024xxrdr/I02413002RDR.QUB",
            "type": "Data Cube (PDS3 / ISIS QUB, 10 spectral bands)"
        },
        {
            "name": "I02413002.png",
            "url": "https://static.mars.asu.edu/pds/ODTSDP_v1/browse/odtbws1_0003/i024xx/I02413002.png",
            "type": "Browse Image"
        }
    ]
    themis_manifest_entry = []
    for item in themis_files:
        dest = themis_dir / item["name"]
        print(f"    Downloading {item['name']}...")
        dl_info = download_file_with_checksum(item["url"], dest)
        dl_info["type"] = item["type"]
        themis_manifest_entry.append(dl_info)
        print(f"      {item['name']}: {dl_info['size_bytes']:,} bytes | SHA256: {dl_info['sha256'][:16]}...")

    manifest["pilot_products"]["THEMIS"] = {
        "observation_id": "I02413002",
        "product_id": "I02413002RDR",
        "instrument": "THEMIS Infrared",
        "spacecraft": "2001 Mars Odyssey",
        "center_coordinates": {"lat": 18.477, "lon": 77.384},
        "spatial_resolution_m": 100.0,
        "files": themis_manifest_entry
    }

    # -------------------------------------------------------------------------
    # 2. CTX Pilot: P02_001820_1984_XI_18N282W (Centered at 18.268 N, 77.330 E)
    # -------------------------------------------------------------------------
    print("  [2/3] Downloading CTX Pilot Observation (P02_001820_1984)...")
    ctx_dir = REPO_ROOT / "data/raw/ctx"
    ctx_files = [
        {
            "name": "P02_001820_1984_XI_18N282W.IMG",
            "url": "https://planetarydata.jpl.nasa.gov/img/data/mro/ctx/mrox_0023/data/P02_001820_1984_XI_18N282W.IMG",
            "type": "PDS3 IMG (with embedded VICAR/PDS label header)"
        },
        {
            "name": "P02_001820_1984_XI_18N282W.IMG.jpeg",
            "url": "https://planetarydata.jpl.nasa.gov/img/data/mro/ctx/mrox_0023/extras/browse/P02_001820_1984_XI_18N282W.IMG.jpeg",
            "type": "Browse Image"
        }
    ]
    ctx_manifest_entry = []
    for item in ctx_files:
        dest = ctx_dir / item["name"]
        print(f"    Downloading {item['name']}...")
        dl_info = download_file_with_checksum(item["url"], dest)
        dl_info["type"] = item["type"]
        ctx_manifest_entry.append(dl_info)
        print(f"      {item['name']}: {dl_info['size_bytes']:,} bytes | SHA256: {dl_info['sha256'][:16]}...")

    manifest["pilot_products"]["CTX"] = {
        "observation_id": "P02_001820_1984",
        "product_id": "P02_001820_1984_XI_18N282W",
        "instrument": "Context Camera (CTX)",
        "spacecraft": "Mars Reconnaissance Orbiter",
        "center_coordinates": {"lat": 18.268, "lon": 77.330},
        "spatial_resolution_m": 5.55,
        "files": ctx_manifest_entry
    }

    # -------------------------------------------------------------------------
    # 3. HiRISE Pilot: PSP_004299_1985 (Jezero Crater Delta Deposit)
    # -------------------------------------------------------------------------
    print("  [3/3] Downloading HiRISE Pilot Observation (PSP_004299_1985)...")
    hirise_dir = REPO_ROOT / "data/raw/hirise"
    hirise_files = [
        {
            "name": "PSP_004299_1985_MRGB.LBL",
            "url": "https://hirise.lpl.arizona.edu/PDS/EXTRAS/RDR/PSP/ORB_004200_004299/PSP_004299_1985/PSP_004299_1985_MRGB.LBL",
            "type": "PDS3 Map-Projected Label (Color MRGB Channel)"
        },
        {
            "name": "PSP_004299_1985_RED.LBL",
            "url": "https://hirise.lpl.arizona.edu/PDS/RDR/PSP/ORB_004200_004299/PSP_004299_1985/PSP_004299_1985_RED.LBL",
            "type": "PDS3 Map-Projected Label (Full Band RED Channel)"
        },
        {
            "name": "PSP_004299_1985_MRGB.abrowse.jpg",
            "url": "https://hirise.lpl.arizona.edu/PDS/EXTRAS/RDR/PSP/ORB_004200_004299/PSP_004299_1985/PSP_004299_1985_MRGB.abrowse.jpg",
            "type": "Color Browse Product (Georeferenced Preview)"
        },
        {
            "name": "PSP_004299_1985_RED_LBL.kml",
            "url": "https://ode.rsl.wustl.edu/mars/datafile/kmlfiles/mro-m-hirise-3-rdr-v11/mrohr_0001/rdr/psp/orb_004200_004299/psp_004299_1985/psp_004299_1985_red_lbl.kml",
            "type": "Spatial Footprint Vector (KML)"
        }
    ]
    hirise_manifest_entry = []
    for item in hirise_files:
        dest = hirise_dir / item["name"]
        print(f"    Downloading {item['name']}...")
        dl_info = download_file_with_checksum(item["url"], dest)
        dl_info["type"] = item["type"]
        hirise_manifest_entry.append(dl_info)
        print(f"      {item['name']}: {dl_info['size_bytes']:,} bytes | SHA256: {dl_info['sha256'][:16]}...")

    manifest["pilot_products"]["HiRISE"] = {
        "observation_id": "PSP_004299_1985",
        "product_id": "PSP_004299_1985_MRGB",
        "instrument": "High Resolution Imaging Science Experiment (HiRISE)",
        "spacecraft": "Mars Reconnaissance Orbiter",
        "center_coordinates": {"lat": 18.398, "lon": 77.585},
        "spatial_resolution_m": 0.25,
        "files": hirise_manifest_entry
    }

    # Save Manifest
    manifest_path = REPO_ROOT / "catalogs/pilot_acquisition_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nPilot Acquisition completed successfully. Manifest: {manifest_path}")

    return manifest


def main():
    print("=" * 70)
    print("ZUHURA PLANETARY DATA PIPELINE: STAGE 4 DISCOVERY & PILOT ACQUISITION")
    print("=" * 70)

    setup_directories()
    discovery_res = execute_discovery()
    manifest_res = execute_pilot_acquisition()

    print("\nStage 4 Discovery & Pilot Acquisition completed successfully.")


if __name__ == "__main__":
    main()
