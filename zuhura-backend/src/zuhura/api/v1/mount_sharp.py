"""
Endpoints for the Curiosity route on Mount Sharp.
Provides metadata, geological units, and high-resolution assets
for Curiosity's exploration path up Mount Sharp (PIA23179).
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel

from zuhura.core.config import settings

router = APIRouter()

MOUNT_SHARP_DIR = Path(settings.MARS_DATA_ROOT) / 'mount_sharp'
METADATA_FILE = MOUNT_SHARP_DIR / 'metadata.json'


@router.get("", summary="Get Mount Sharp exploration region specification and assets")
async def get_mount_sharp_data():
    """
    Returns authentic NASA scientific data for Curiosity's path up Mount Sharp (PIA23179).
    Includes HiRISE/CRISM/CTX/HRSC dataset citations, stratigraphy units, and downloadable assets.
    """
    if not METADATA_FILE.exists():
        raise HTTPException(status_code=404, detail="Mount Sharp dataset metadata not found")

    with open(METADATA_FILE, 'r') as f:
        data = json.load(f)

    # Attach live API asset links
    data['download_links'] = {
        'original_tiff': '/api/v1/mount-sharp/assets/PIA23179.tif',
        'route_animation': '/api/v1/mount-sharp/assets/PIA23179.gif',
        'full_jpg': '/api/v1/mount-sharp/assets/PIA23179.jpg',
        'annotated_fig1': '/api/v1/mount-sharp/assets/PIA23179_fig1.jpg'
    }
    return data


@router.get("/assets/{filename}", summary="Download or view Mount Sharp original scientific asset")
async def get_mount_sharp_asset(filename: str):
    """
    Serves original-resolution files: PIA23179.tif (13.7 MB master),
    PIA23179.gif (3.0 MB animation), and PIA23179.jpg.
    """
    safe_name = Path(filename).name
    file_path = MOUNT_SHARP_DIR / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Asset {safe_name} not found")

    media_types = {
        '.tif': 'image/tiff',
        '.tiff': 'image/tiff',
        '.gif': 'image/gif',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png'
    }
    content_type = media_types.get(file_path.suffix.lower(), 'application/octet-stream')

    headers = {}
    if file_path.suffix.lower() in ['.tif', '.tiff']:
        headers["Content-Disposition"] = f'attachment; filename="{safe_name}"'

    return FileResponse(file_path, media_type=content_type, headers=headers)
