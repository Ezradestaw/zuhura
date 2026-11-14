"""
Environment and climate API endpoints.
Mounted at /api/v1/spatial/environment
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from zuhura.environment.atmospheric_model import (
    MarsAtmosphericEngine,
    MarsOrbitalParameters,
    VerticalAtmosphericProfile,
    DustOpticalDepthResult,
    DiurnalTemperatureProfile,
    SolarPowerBudgetResult,
    MissionEnvironmentAssessment,
)

router = APIRouter()


class AtmosphericProfileRequest(BaseModel):
    latitude: float = Field(default=18.38, ge=-90.0, le=90.0, description="Planetocentric latitude in degrees")
    longitude: float = Field(default=77.58, description="Planetocentric East-positive longitude in degrees")
    elevation_m: float = Field(default=-2500.0, description="Elevation relative to MOLA Areoid in meters")
    ls_deg: float = Field(default=0.0, ge=0.0, lt=360.0, description="Solar longitude Ls in degrees [0, 360)")
    max_altitude_km: float = Field(default=50.0, ge=10.0, le=100.0, description="Maximum vertical profile altitude in km")
    step_km: float = Field(default=2.5, ge=0.5, le=10.0, description="Vertical altitude step size in km")


class DustOpticalDepthRequest(BaseModel):
    latitude: float = Field(default=18.38, ge=-90.0, le=90.0)
    longitude: float = Field(default=77.58)
    elevation_m: float = Field(default=-2500.0)
    ls_deg: float = Field(default=260.0, ge=0.0, lt=360.0)
    global_dust_multiplier: float = Field(default=1.0, ge=0.2, le=5.0)


class DiurnalTemperatureRequest(BaseModel):
    latitude: float = Field(default=18.38, ge=-90.0, le=90.0)
    elevation_m: float = Field(default=-2500.0)
    ls_deg: float = Field(default=0.0, ge=0.0, lt=360.0)
    thermal_inertia_tiu: float = Field(default=320.0, ge=30.0, le=1200.0, description="Thermal inertia in TIU (J m^-2 K^-1 s^-1/2)")
    albedo: float = Field(default=0.22, ge=0.05, le=0.60)
    tau: float = Field(default=0.40, ge=0.1, le=5.0)


class SolarPowerBudgetRequest(BaseModel):
    latitude: float = Field(default=18.38, ge=-90.0, le=90.0)
    ls_deg: float = Field(default=0.0, ge=0.0, lt=360.0)
    tau: float = Field(default=0.40, ge=0.1, le=5.0)
    panel_area_m2: float = Field(default=1.3, ge=0.1, le=50.0, description="Photovoltaic array surface area in m^2")
    cell_efficiency: float = Field(default=0.295, ge=0.05, le=0.45, description="Photovoltaic cell conversion efficiency")
    dust_deposition_factor: float = Field(default=0.85, ge=0.05, le=1.0, description="Dust obscuration factor (1.0 = pristine clean)")


class MissionAssessmentRequest(BaseModel):
    target_name: str = Field(default="Jezero Crater Exploration Zone")
    latitude: float = Field(default=18.38, ge=-90.0, le=90.0)
    longitude: float = Field(default=77.58)
    elevation_m: float = Field(default=-2500.0)
    ls_deg: float = Field(default=180.0, ge=0.0, lt=360.0)
    thermal_inertia_tiu: float = Field(default=350.0, ge=30.0, le=1200.0)
    panel_area_m2: float = Field(default=1.3, ge=0.1, le=50.0)


# Planetary Site Presets
MARTIAN_SITE_PRESETS = [
    {
        "id": "jezero_crater",
        "name": "Jezero Crater (Perseverance Touchdown)",
        "latitude": 18.38,
        "longitude": 77.58,
        "elevation_m": -2500.0,
        "thermal_inertia_tiu": 360.0,
        "geological_context": "Noachian/Hesperian lacustrine delta deposit in ancient impact basin."
    },
    {
        "id": "gale_crater",
        "name": "Gale Crater (Curiosity Traverse)",
        "latitude": -4.59,
        "longitude": 137.44,
        "elevation_m": -4400.0,
        "thermal_inertia_tiu": 320.0,
        "geological_context": "Aeolis Mons central mound exhibiting sulfate and clay stratigraphy."
    },
    {
        "id": "olympus_mons_caldera",
        "name": "Olympus Mons Summit Caldera",
        "latitude": 18.65,
        "longitude": 226.20,
        "elevation_m": 21229.0,
        "thermal_inertia_tiu": 110.0,
        "geological_context": "Highest volcanic summit in the solar system; ultra-thin atmosphere (<1 mbar)."
    },
    {
        "id": "hellas_planitia_basin",
        "name": "Hellas Planitia Deep Basin Floor",
        "latitude": -42.70,
        "longitude": 70.00,
        "elevation_m": -7152.0,
        "thermal_inertia_tiu": 240.0,
        "geological_context": "Deepest impact depression on Mars; peak atmospheric pressure (>12 mbar, above water triple point)."
    },
    {
        "id": "valles_marineris_chasma",
        "name": "Coprates Chasma (Valles Marineris)",
        "latitude": -14.20,
        "longitude": 300.80,
        "elevation_m": -3800.0,
        "thermal_inertia_tiu": 410.0,
        "geological_context": "Grand canyon rift system with recurring slope lineae (RSL) candidates."
    },
    {
        "id": "phoenix_landing_site",
        "name": "Vastitas Borealis (Phoenix Lander)",
        "latitude": 68.22,
        "longitude": 234.25,
        "elevation_m": -4120.0,
        "thermal_inertia_tiu": 210.0,
        "geological_context": "High-latitude permafrost terrain with shallow subsurface water ice table."
    }
]


@router.get("/overview", summary="Mars Orbital & Seasonal Overview")
async def get_orbital_overview(
    ls_deg: float = Query(default=0.0, ge=0.0, lt=360.0, description="Solar Longitude Ls in degrees")
) -> Dict[str, Any]:
    """Returns Mars orbital parameters, solar constant, and global seasonal datum pressure."""
    orbital = MarsAtmosphericEngine.calculate_orbital_parameters(ls_deg)
    p0_datum = MarsAtmosphericEngine.calculate_seasonal_datum_pressure(ls_deg)
    return {
        "status": "success",
        "orbital": orbital,
        "mean_datum_pressure_pa": round(p0_datum, 2),
        "mean_datum_pressure_mbar": round(p0_datum / 100.0, 3),
        "water_triple_point_pa": MarsAtmosphericEngine.WATER_TRIPLE_POINT_PA
    }


@router.get("/presets", summary="Mars Environmental Benchmark Site Presets")
async def get_site_presets() -> Dict[str, Any]:
    """Returns curated landmark locations with standardized topographic and thermal coordinates."""
    return {
        "status": "success",
        "count": len(MARTIAN_SITE_PRESETS),
        "presets": MARTIAN_SITE_PRESETS
    }


@router.post("/atmospheric-profile", summary="Vertical Atmospheric Profile & Hypsometry")
async def compute_atmospheric_profile(req: AtmosphericProfileRequest) -> Dict[str, Any]:
    """Computes vertical barometric pressure, density, temperature, and speed of sound profile."""
    profile = MarsAtmosphericEngine.calculate_atmospheric_profile(
        latitude=req.latitude,
        longitude=req.longitude,
        elevation_m=req.elevation_m,
        ls_deg=req.ls_deg,
        max_altitude_km=req.max_altitude_km,
        step_km=req.step_km
    )
    return {
        "status": "success",
        "profile": profile
    }


@router.post("/dust-optical-depth", summary="Visible Dust Optical Depth & Storm Risk")
async def compute_dust_optical_depth(req: DustOpticalDepthRequest) -> Dict[str, Any]:
    """Computes visible column optical depth, storm risk index, and operational mitigations."""
    result = MarsAtmosphericEngine.calculate_dust_optical_depth(
        latitude=req.latitude,
        longitude=req.longitude,
        elevation_m=req.elevation_m,
        ls_deg=req.ls_deg,
        global_dust_multiplier=req.global_dust_multiplier
    )
    return {
        "status": "success",
        "result": result
    }


@router.post("/diurnal-temperature", summary="24-Hour Diurnal Temperature Cycle")
async def compute_diurnal_temperature(req: DiurnalTemperatureRequest) -> Dict[str, Any]:
    """Computes hourly surface and near-surface air temperatures over a Martian Sol."""
    profile = MarsAtmosphericEngine.calculate_diurnal_temperature_cycle(
        latitude=req.latitude,
        elevation_m=req.elevation_m,
        ls_deg=req.ls_deg,
        thermal_inertia_tiu=req.thermal_inertia_tiu,
        albedo=req.albedo,
        tau=req.tau
    )
    return {
        "status": "success",
        "profile": profile
    }


@router.post("/solar-power-budget", summary="Surface Photovoltaic Power Budget")
async def compute_solar_power_budget(req: SolarPowerBudgetRequest) -> Dict[str, Any]:
    """Simulates diurnal electrical power curve and daily Wh/sol generation for exploration assets."""
    budget = MarsAtmosphericEngine.calculate_solar_power_budget(
        latitude=req.latitude,
        ls_deg=req.ls_deg,
        tau=req.tau,
        panel_area_m2=req.panel_area_m2,
        cell_efficiency=req.cell_efficiency,
        dust_deposition_factor=req.dust_deposition_factor
    )
    return {
        "status": "success",
        "budget": budget
    }


@router.post("/mission-assessment", summary="Integrated Mission Environmental Assessment")
async def assess_mission_site(req: MissionAssessmentRequest) -> Dict[str, Any]:
    """Evaluates comprehensive environmental health, hazards, and site viability score."""
    assessment = MarsAtmosphericEngine.assess_mission_environment(
        target_name=req.target_name,
        latitude=req.latitude,
        longitude=req.longitude,
        elevation_m=req.elevation_m,
        ls_deg=req.ls_deg,
        thermal_inertia_tiu=req.thermal_inertia_tiu,
        panel_area_m2=req.panel_area_m2
    )
    return {
        "status": "success",
        "assessment": assessment
    }
