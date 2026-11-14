"""
Image location (pinpoint) endpoints.
Accepts Mars landscape image uploads and returns ranked candidate locations with
confidence levels, reference imagery, and morphological rationale.
"""

from typing import Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status
from pydantic import BaseModel, Field

from zuhura.pinpoint.engine import (
    LocationPinpointEngine,
    LocationPinpointResult,
    CandidateLocation,
    MARS_LANDSCAPE_CATALOG,
)

router = APIRouter()
_pinpoint_engine = LocationPinpointEngine()

MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post(
    "/analyze-image",
    response_model=LocationPinpointResult,
    summary="Estimate Martian Location from Landscape Image",
    description=(
        "Securely ingests a Martian landscape photo, evaluates morphological terrain signatures, "
        "and returns ranked candidate locations with similarity scores and uncertainty bounds."
    ),
    status_code=status.HTTP_200_OK,
)
async def pinpoint_mars_image(
    file: UploadFile = File(..., description="Martian landscape photo (JPEG, PNG, or WebP, max 10MB)"),
    mission_hint: Optional[str] = Form(default=None, description="Optional mission context (e.g. Perseverance, Curiosity, Opportunity, Spirit)"),
    camera_azimuth_deg: Optional[float] = Form(default=None, description="Optional compass pointing azimuth [0-360)"),
    camera_height_m: Optional[float] = Form(default=None, description="Optional camera mast height (meters)"),
    approx_lat: Optional[float] = Form(default=None, description="Optional approximate latitude [-90 to 90]"),
    approx_lon: Optional[float] = Form(default=None, description="Optional approximate longitude [0 to 360]"),
) -> LocationPinpointResult:
    # 1. Validate content type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file format '{file.content_type}'. Allowed types: image/jpeg, image/png, image/webp.",
        )

    # 2. Read bytes with size safeguard
    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded image exceeds maximum size limit of 10 MB ({len(contents)} bytes).",
        )

    if len(contents) < 128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty or corrupted.",
        )

    # 3. Execute localization matching
    try:
        result = _pinpoint_engine.estimate_location_from_image(
            image_bytes=contents,
            mission_hint=mission_hint,
            camera_azimuth_deg=camera_azimuth_deg,
            camera_height_m=camera_height_m,
            approx_lat=approx_lat,
            approx_lon=approx_lon,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Landscape localization matching failed: {str(e)}",
        ) from e


@router.get(
    "/reference-sites",
    summary="List Ground Truth Reference Landmark Sites",
    description="Returns the authoritative catalog of Mars rover traverse stations and ground truth reference sites.",
)
async def list_reference_sites():
    return {
        "status": "operational",
        "total_reference_sites": len(MARS_LANDSCAPE_CATALOG),
        "sites": MARS_LANDSCAPE_CATALOG,
    }
