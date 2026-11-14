"""
Image analysis endpoints (features, spectra, registration).
Provides endpoints for:
1. Automated feature detection (impact craters, dunes, gullies, RSL, layered sediments).
2. Analytical crater morphometry profiling (diameter, depth, d/D ratio, degradation state).
3. Multi-spectral band ratio calculations & THEMIS thermal inertia grain size estimation.
4. Temporal change detection (new craters, slope streaks, ripple migration).
5. Scientific image registration and sub-pixel alignment.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form

from zuhura.vision.feature_detection import (
    detect_planetary_features,
    profile_crater_morphology,
    DetectedPlanetaryFeature,
    CraterMorphologyProfile,
)
from zuhura.vision.multispectral import (
    run_multispectral_analysis,
    MultiSpectralAnalysisResult,
)
from zuhura.vision.registration import (
    detect_temporal_surface_changes,
    register_orbital_images,
    apply_super_resolution_enhancement,
    TemporalChangeDetectionResult,
    ImageRegistrationResult,
    SuperResolutionResult,
)

router = APIRouter()


class FeatureDetectionRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=360.0)
    radius_km: float = Field(default=150.0, ge=1.0, le=1000.0)


class CraterProfileRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=360.0)
    diameter_km: float = Field(..., ge=0.01, le=2500.0)
    rim_elevation_m: Optional[float] = None
    floor_elevation_m: Optional[float] = None


class MultiSpectralRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=360.0)


class ChangeDetectionRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=360.0)
    epoch_1_date: str = "2021-01-01"
    epoch_2_date: str = "2024-01-01"


class RegistrationRequest(BaseModel):
    reference_frame_id: str = "CTX_D14_032549_1985"
    target_frame_id: str = "HiRISE_ESP_04299_1985"


@router.post(
    "/detect-features",
    response_model=List[DetectedPlanetaryFeature],
    summary="Detect Planetary Geological Features",
    description="Identifies impact craters, dunes, gullies, RSL, and layered sediments near target coordinates.",
    status_code=status.HTTP_200_OK,
)
async def detect_features_endpoint(req: FeatureDetectionRequest) -> List[DetectedPlanetaryFeature]:
    try:
        return detect_planetary_features(
            latitude=req.latitude,
            longitude=req.longitude,
            search_radius_km=req.radius_km
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feature detection failed: {str(e)}"
        ) from e


@router.post(
    "/crater-profile",
    response_model=CraterMorphologyProfile,
    summary="Analytical Crater Morphometry Profiling",
    description="Computes depth, d/D ratio, degradation state, and ejecta blanket classification based on Pike (1980) and Barlow (2000).",
    status_code=status.HTTP_200_OK,
)
async def crater_profile_endpoint(req: CraterProfileRequest) -> CraterMorphologyProfile:
    try:
        return profile_crater_morphology(
            latitude=req.latitude,
            longitude=req.longitude,
            diameter_km=req.diameter_km,
            rim_elevation_m=req.rim_elevation_m,
            floor_elevation_m=req.floor_elevation_m
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Crater morphology profiling failed: {str(e)}"
        ) from e


@router.post(
    "/multispectral-analysis",
    response_model=MultiSpectralAnalysisResult,
    summary="Multi-Spectral Band Ratios & Thermal Inertia",
    description="Derives CRISM iron oxide/clay/olivine band ratios, false-color mapping, and THEMIS thermal inertia grain size estimation.",
    status_code=status.HTTP_200_OK,
)
async def multispectral_endpoint(req: MultiSpectralRequest) -> MultiSpectralAnalysisResult:
    try:
        return run_multispectral_analysis(latitude=req.latitude, longitude=req.longitude)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multi-spectral analysis failed: {str(e)}"
        ) from e


@router.post(
    "/change-detection",
    response_model=TemporalChangeDetectionResult,
    summary="Multi-Temporal Surface Change Detection",
    description="Detects active surface changes (new impacts, slope streaks, dune migration) between observation epochs.",
    status_code=status.HTTP_200_OK,
)
async def change_detection_endpoint(req: ChangeDetectionRequest) -> TemporalChangeDetectionResult:
    try:
        return detect_temporal_surface_changes(
            latitude=req.latitude,
            longitude=req.longitude,
            epoch_1_date=req.epoch_1_date,
            epoch_2_date=req.epoch_2_date
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Change detection failed: {str(e)}"
        ) from e


@router.post(
    "/image-registration",
    response_model=ImageRegistrationResult,
    summary="Scientific Sub-Pixel Image Registration",
    description="Computes projective homography transformation matrix and sub-pixel alignment residual between overlapping frames.",
    status_code=status.HTTP_200_OK,
)
async def registration_endpoint(req: RegistrationRequest) -> ImageRegistrationResult:
    try:
        # Mock payload bytes for synthetic frame verification
        ref_bytes = f"REF_FRAME_{req.reference_frame_id}".encode('utf-8') * 32
        tgt_bytes = f"TGT_FRAME_{req.target_frame_id}".encode('utf-8') * 32
        return register_orbital_images(
            ref_image_bytes=ref_bytes,
            target_image_bytes=tgt_bytes,
            ref_frame_id=req.reference_frame_id,
            target_frame_id=req.target_frame_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image registration failed: {str(e)}"
        ) from e


@router.post(
    "/super-resolution",
    response_model=SuperResolutionResult,
    summary="Super-Resolution Basemap Enhancement",
    description="Synthesizes high-resolution morphological reconstructions to reveal subtle stratigraphic features.",
    status_code=status.HTTP_200_OK,
)
async def super_resolution_endpoint(
    original_resolution_m_per_px: float = 6.0,
    enhancement_factor: float = 2.0
) -> SuperResolutionResult:
    try:
        sample_bytes = b"ORBITAL_FRAME_BUFFER" * 64
        return apply_super_resolution_enhancement(
            image_bytes=sample_bytes,
            original_res_m_per_px=original_resolution_m_per_px,
            enhancement_factor=enhancement_factor
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Super-resolution enhancement failed: {str(e)}"
        ) from e
