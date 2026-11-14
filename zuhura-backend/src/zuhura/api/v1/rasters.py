"""
Raster access and metadata endpoints.
Provides controlled raster metadata inspection and secure streaming file access
with strict path traversal safeguards and catalog verification.
"""

import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from fastapi.responses import FileResponse, StreamingResponse
from zuhura.api.deps import get_science_access
from zuhura.core.config import settings
from zuhura_data.access.client import ZuhuraScienceAccess

router = APIRouter()


def secure_resolve_path(storage_path: str, repo_root: Path) -> Path:
    """
    Safely resolves a storage path ensuring it stays strictly inside the
    designated data directory and prevents directory traversal attacks.
    """
    # Reject suspicious path characters
    if ".." in storage_path or storage_path.startswith("/"):
        # If absolute, verify it resides under repo_root / data
        candidate = Path(storage_path).resolve()
    else:
        candidate = (repo_root / storage_path).resolve()

    allowed_data_dir = (repo_root / "data").resolve()
    if not str(candidate).startswith(str(allowed_data_dir)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Path outside permitted scientific data archive."
        )
    return candidate


@router.get("/{product_id}/metadata", summary="Get Scientific Raster Technical Metadata")
async def get_raster_metadata(
    product_id: str,
    science_access: ZuhuraScienceAccess = Depends(get_science_access)
):
    """
    Returns technical raster metadata (dimensions, CRS, geotransform,
    overviews, bands, and data types) for a cataloged raster or spectral product.
    """
    prod = science_access.get_product(product_id)
    if not prod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scientific product '{product_id}' not found in catalog."
        )

    if not prod.storage_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' is cataloged as a remote/discovered record without local raster storage."
        )

    try:
        info = science_access.get_raster_info(prod.product_id)
        info["product_metadata"] = {
            "dataset_id": prod.dataset_id,
            "instrument": prod.instrument,
            "mission": prod.mission,
            "units": prod.units,
            "validation_status": prod.validation_status.value,
            "resolution_m": prod.resolution
        }
        return info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to inspect raster file: {str(e)}"
        )


@router.get("/{product_id}", summary="Access and Stream Scientific Raster Data")
async def get_raster_file(
    product_id: str,
    request: Request,
    science_access: ZuhuraScienceAccess = Depends(get_science_access)
):
    """
    Provides secure, range-capable streaming access to a validated scientific raster file.
    Only serves cataloged products with strict path containment checks.
    """
    prod = science_access.get_product(product_id)
    if not prod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scientific product '{product_id}' not found in catalog."
        )

    if not prod.storage_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' has no local file asset."
        )

    safe_path = secure_resolve_path(prod.storage_path, science_access.repo_root)
    if not safe_path.exists() or not safe_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Local raster file asset is missing on disk."
        )

    # Determine Media Type
    suffix = safe_path.suffix.lower()
    media_type = "application/octet-stream"
    if suffix in [".tif", ".tiff"]:
        media_type = "image/tiff"
    elif suffix == ".png":
        media_type = "image/png"
    elif suffix in [".jpg", ".jpeg"]:
        media_type = "image/jpeg"
    elif suffix in [".lbl", ".txt"]:
        media_type = "text/plain"
    elif suffix == ".kml":
        media_type = "application/vnd.google-earth.kml+xml"

    # Return FileResponse supporting HTTP Range requests automatically
    return FileResponse(
        path=safe_path,
        media_type=media_type,
        filename=safe_path.name
    )
