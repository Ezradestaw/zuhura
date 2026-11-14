"""
Layered interior model of Mars based on InSight results.
Based on NASA InSight seismic observations, gravity inversion and mineral physics.

Reconciles published interpretations:
- Stähler et al. (2021), Science 373(6553), 443-448 (Initial large-core model, R = 1830 km)
- Knapmeyer-Endrun et al. (2021), Science 373(6553), 438-443 (2-layer vs 3-layer crust)
- Khan et al. (2021), Science 373(6553), 434-438 (Thermal lithosphere & mantle structure)
- Samuel et al. (2023), Nature 622, 712-717 (Discovery of basal molten silicate slag layer)
- Khan et al. (2023), Nature 622, 718-723 (Reconciled core radius R = 1650 km)
- Irving et al. (2023), PNAS 120(18), e2217090120 (Core-transiting seismic wave observations)
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from zuhura.provenance.taxonomy import (
    EpistemicClassification,
    UncertaintyModel,
    ScientificReference,
    ScientificProvenanceRecord,
    ProvenanceFactory,
)


class InteriorLayer(BaseModel):
    id: str
    name: str
    classification: str = Field(description="Layer category: crust, lithosphere, mantle, cmb, outer_core, inner_core")
    depth_top_km: float = Field(description="Depth to top boundary from mean surface (km)")
    depth_bottom_km: float = Field(description="Depth to bottom boundary from mean surface (km)")
    thickness_km: float = Field(description="Estimated layer thickness (km)")
    thickness_uncertainty_km: float = Field(description="Uncertainty range (± km)")
    radius_top_km: float = Field(description="Radius from center of Mars to layer top (km)")
    radius_bottom_km: float = Field(description="Radius from center of Mars to layer bottom (km)")
    state_of_matter: str = Field(description="Solid, Partially Molten, Liquid, or Inferred Solid")
    primary_composition: str = Field(description="Dominant mineralogical and chemical constituents")
    density_kg_m3: float = Field(description="Estimated bulk density (kg/m^3)")
    density_range_kg_m3: List[float] = Field(description="Density uncertainty bounds [min, max]")
    temperature_k: float = Field(description="Estimated boundary or layer mean temperature (Kelvin)")
    temperature_range_k: List[float] = Field(description="Temperature range [min, max]")
    evidence_type: str = Field(description="OBSERVED, MEASURED, DERIVED, MODEL_ESTIMATED, SIMULATED, PROVISIONAL, or UNVERIFIED")
    seismic_p_velocity_km_s: Optional[float] = Field(default=None, description="Average P-wave velocity Vp (km/s)")
    seismic_s_velocity_km_s: Optional[float] = Field(default=None, description="Average S-wave velocity Vs (km/s)")
    scientific_significance: str
    source_citation: str
    doi: str
    model_notes: str


class MarsInteriorModel(BaseModel):
    profile_id: str
    profile_name: str
    planetary_radius_km: float = 3389.5
    planetary_mass_kg: float = 6.4171e23
    surface_gravity_m_s2: float = 3.72076
    seismic_station: str = "InSight SEIS (Station XB.ELYSE, Elysium Planitia, 4.50°N 135.62°E)"
    data_vintage: str = "NASA InSight Mission (2018-2022) Final Archive Data"
    core_radius_km: float
    core_radius_uncertainty_km: float
    has_basal_molten_layer: bool
    basal_molten_layer_thickness_km: float = 0.0
    layers: List[InteriorLayer]
    crustal_dichotomy_notes: str
    core_composition_notes: str
    scientific_provenance: ScientificProvenanceRecord


# ------------------------------------------------------------------------------
# Profile 1: Nature 2023 Reconciled Model (Samuel et al. 2023 & Khan et al. 2023)
# Current Scientific Consensus: Core R = 1,650 km with 160-km Basal Molten Silicate Slag
# ------------------------------------------------------------------------------
SAMUEL_2023_LAYERS: List[InteriorLayer] = [
    InteriorLayer(
        id="upper_crust",
        name="Upper Fractured Crust (Layer 1)",
        classification="crust",
        depth_top_km=0.0,
        depth_bottom_km=10.0,
        thickness_km=10.0,
        thickness_uncertainty_km=2.0,
        radius_top_km=3389.5,
        radius_bottom_km=3379.5,
        state_of_matter="Solid (Highly Fractured / Porous)",
        primary_composition="Basaltic impact regolith, altered basalt, volatile-rich porous volcanic breccia",
        density_kg_m3=2550.0,
        density_range_kg_m3=[2300.0, 2700.0],
        temperature_k=220.0,
        temperature_range_k=[200.0, 250.0],
        evidence_type="MEASURED",
        seismic_p_velocity_km_s=2.8,
        seismic_s_velocity_km_s=1.6,
        scientific_significance="Upper 8-10 km represents heavily bombarded, porous crust with pervasive micro-fracturing from Noachian-era impacts.",
        source_citation="Knapmeyer-Endrun et al. (2021), Science",
        doi="10.1126/science.abf8966",
        model_notes="Receiver functions at InSight reveal sharp seismic impedance contrast at 8-11 km depth."
    ),
    InteriorLayer(
        id="middle_crust",
        name="Middle Crystalline Crust (Layer 2)",
        classification="crust",
        depth_top_km=10.0,
        depth_bottom_km=24.0,
        thickness_km=14.0,
        thickness_uncertainty_km=4.0,
        radius_top_km=3379.5,
        radius_bottom_km=3365.5,
        state_of_matter="Solid",
        primary_composition="Consolidated basalt, andesitic-basaltic intrusions, plagioclase-bearing volcanic basement",
        density_kg_m3=2850.0,
        density_range_kg_m3=[2700.0, 3000.0],
        temperature_k=350.0,
        temperature_range_k=[300.0, 420.0],
        evidence_type="MEASURED",
        seismic_p_velocity_km_s=4.3,
        seismic_s_velocity_km_s=2.4,
        scientific_significance="Competent crystalline crust beneath the fractured regolith layer.",
        source_citation="Knapmeyer-Endrun et al. (2021), Science",
        doi="10.1126/science.abf8966",
        model_notes="Seismic discontinuity observed between 18 and 27 km."
    ),
    InteriorLayer(
        id="lower_crust",
        name="Lower Crust & Crust-Mantle Boundary (Moho)",
        classification="crust",
        depth_top_km=24.0,
        depth_bottom_km=42.0,
        thickness_km=18.0,
        thickness_uncertainty_km=8.0,
        radius_top_km=3365.5,
        radius_bottom_km=3347.5,
        state_of_matter="Solid",
        primary_composition="Mafic to ultramafic granulites, pyroxene-rich underplated basaltic residues",
        density_kg_m3=3100.0,
        density_range_kg_m3=[2950.0, 3250.0],
        temperature_k=550.0,
        temperature_range_k=[450.0, 700.0],
        evidence_type="MODEL_ESTIMATED",
        seismic_p_velocity_km_s=5.7,
        seismic_s_velocity_km_s=3.3,
        scientific_significance="Marks the Martian Moho (crust-mantle transition). Northern lowlands show thinner crust (~30 km), while southern highlands exhibit ~58 km average thickness.",
        source_citation="Knapmeyer-Endrun et al. (2021), Science",
        doi="10.1126/science.abf8966",
        model_notes="Under InSight lander, Moho depth is constrained to 39 ± 8 km (2-layer model) or 72 ± 15 km (3-layer model)."
    ),
    InteriorLayer(
        id="upper_mantle_lithosphere",
        name="Upper Mantle & Thermal Lithosphere",
        classification="lithosphere",
        depth_top_km=42.0,
        depth_bottom_km=450.0,
        thickness_km=408.0,
        thickness_uncertainty_km=50.0,
        radius_top_km=3347.5,
        radius_bottom_km=2939.5,
        state_of_matter="Solid (Mechanically Rigid Thermal Boundary Layer)",
        primary_composition="Olivine (Fo75-80), orthopyroxene, clinopyroxene, garnet / spinel peridotite",
        density_kg_m3=3450.0,
        density_range_kg_m3=[3350.0, 3550.0],
        temperature_k=1150.0,
        temperature_range_k=[900.0, 1400.0],
        evidence_type="MEASURED",
        seismic_p_velocity_km_s=7.9,
        seismic_s_velocity_km_s=4.4,
        scientific_significance="Thick stagnant thermal lid isolating mantle heat. Enables massive volcanic loads (e.g. Tharsis) without active plate tectonics.",
        source_citation="Khan et al. (2021), Science",
        doi="10.1126/science.abf2966",
        model_notes="Triplicated P and S arrivals demonstrate a velocity gradient consistent with a lithospheric thickness of ~400-500 km."
    ),
    InteriorLayer(
        id="mid_lower_mantle",
        name="Convecting Silicate Mantle",
        classification="mantle",
        depth_top_km=450.0,
        depth_bottom_km=1520.0,
        thickness_km=1070.0,
        thickness_uncertainty_km=60.0,
        radius_top_km=2939.5,
        radius_bottom_km=1869.5,
        state_of_matter="Solid (Viscously Convecting)",
        primary_composition="High-iron olivine polymorphs (wadsleyite/ringwoodite at base), majorite garnet, silicate perovskite / bridgmanite in lowermost zone",
        density_kg_m3=3750.0,
        density_range_kg_m3=[3600.0, 3950.0],
        temperature_k=1750.0,
        temperature_range_k=[1550.0, 1950.0],
        evidence_type="MODEL_ESTIMATED",
        seismic_p_velocity_km_s=8.8,
        seismic_s_velocity_km_s=4.9,
        scientific_significance="Sub-lithospheric convecting mantle. Lower pressure on Mars means bridgmanite only forms at the very base if at all, unlike Earth's vast lower mantle.",
        source_citation="Khan et al. (2021), Science",
        doi="10.1126/science.abf2966",
        model_notes="Absence of a deep bridgmanite blanket enhances thermal coupling with the molten core."
    ),
    InteriorLayer(
        id="basal_molten_layer",
        name="Basal Molten Silicate Slag Layer (CMB Interface)",
        classification="cmb",
        depth_top_km=1520.0,
        depth_bottom_km=1680.0,
        thickness_km=160.0,
        thickness_uncertainty_km=40.0,
        radius_top_km=1869.5,
        radius_bottom_km=1709.5,
        state_of_matter="Partially to Fully Molten Silicate",
        primary_composition="Enriched iron-silicate melt layer, incompatible radioactive isotopes (K, Th, U) concentrated at base",
        density_kg_m3=4100.0,
        density_range_kg_m3=[3900.0, 4300.0],
        temperature_k=2050.0,
        temperature_range_k=[1850.0, 2250.0],
        evidence_type="DERIVED",
        seismic_p_velocity_km_s=7.2,
        seismic_s_velocity_km_s=2.8,
        scientific_significance="Discovered in 2023: a molten silicate layer sits directly atop the metallic core, acting as a blanket that slowed Mars' dynamo cooling.",
        source_citation="Samuel et al. (2023), Nature; Khan et al. (2023), Nature",
        doi="10.1038/s41586-023-06601-8",
        model_notes="Explains anomalous core transit times and reconciled the unexpectedly large apparent core radius found in 2021."
    ),
    InteriorLayer(
        id="liquid_outer_core",
        name="Liquid Iron-Nickel Metallic Core",
        classification="outer_core",
        depth_top_km=1680.0,
        depth_bottom_km=3389.5,
        thickness_km=1709.5,
        thickness_uncertainty_km=20.0,
        radius_top_km=1709.5,
        radius_bottom_km=0.0,
        state_of_matter="Liquid Metallic Alloy",
        primary_composition="Liquid Fe-Ni alloy with 15-18 wt% Sulfur, plus Carbon, Oxygen, and Hydrogen",
        density_kg_m3=6100.0,
        density_range_kg_m3=[5800.0, 6400.0],
        temperature_k=2300.0,
        temperature_range_k=[2050.0, 2600.0],
        evidence_type="MEASURED",
        seismic_p_velocity_km_s=5.1,
        seismic_s_velocity_km_s=0.0,  # Shear waves cannot propagate through liquid
        scientific_significance="Liquid metallic core. Absence of a global magnetic field today suggests thermal stratification or lack of inner core crystallization prevented sustained geodynamo.",
        source_citation="Samuel et al. (2023), Nature; Irving et al. (2023), PNAS",
        doi="10.1038/s41586-023-06601-8",
        model_notes="Complete extinction of direct shear wave (Vs=0) proves liquid state. Core radius measured at 1650 ± 20 km."
    )
]

# ------------------------------------------------------------------------------
# Profile 2: Science 2021 Initial Model (Stähler et al. 2021)
# Historical Model: Apparent Core R = 1,830 km with No Basal Slag Layer
# ------------------------------------------------------------------------------
STAHLER_2021_LAYERS: List[InteriorLayer] = [
    InteriorLayer(
        id="crust_2021",
        name="Martian Crust (2-Layer Model Average)",
        classification="crust",
        depth_top_km=0.0,
        depth_bottom_km=39.0,
        thickness_km=39.0,
        thickness_uncertainty_km=8.0,
        radius_top_km=3389.5,
        radius_bottom_km=3350.5,
        state_of_matter="Solid",
        primary_composition="Basaltic and andesitic-basaltic crustal basement",
        density_kg_m3=2900.0,
        density_range_kg_m3=[2700.0, 3100.0],
        temperature_k=400.0,
        temperature_range_k=[200.0, 600.0],
        evidence_type="MEASURED",
        seismic_p_velocity_km_s=4.5,
        seismic_s_velocity_km_s=2.6,
        scientific_significance="Initial 2021 crustal thickness inversion from InSight SEIS.",
        source_citation="Knapmeyer-Endrun et al. (2021), Science",
        doi="10.1126/science.abf8966",
        model_notes="Two-layer inversion yielding ~39 km Moho."
    ),
    InteriorLayer(
        id="mantle_2021",
        name="Silicate Mantle (Direct Core Interface)",
        classification="mantle",
        depth_top_km=39.0,
        depth_bottom_km=1559.5,
        thickness_km=1520.5,
        thickness_uncertainty_km=60.0,
        radius_top_km=3350.5,
        radius_bottom_km=1830.0,
        state_of_matter="Solid",
        primary_composition="Olivine, pyroxene, garnet, ringwoodite",
        density_kg_m3=3600.0,
        density_range_kg_m3=[3400.0, 3850.0],
        temperature_k=1650.0,
        temperature_range_k=[1400.0, 1900.0],
        evidence_type="MODEL_ESTIMATED",
        seismic_p_velocity_km_s=8.5,
        seismic_s_velocity_km_s=4.7,
        scientific_significance="Direct mantle-core contact assumed in initial 2021 inversion.",
        source_citation="Khan et al. (2021), Science",
        doi="10.1126/science.abf2966",
        model_notes="Mantle bounded at bottom directly by apparent metallic core."
    ),
    InteriorLayer(
        id="large_liquid_core_2021",
        name="Large Liquid Metallic Core (Initial 2021 Interpretation)",
        classification="outer_core",
        depth_top_km=1559.5,
        depth_bottom_km=3389.5,
        thickness_km=1830.0,
        thickness_uncertainty_km=40.0,
        radius_top_km=1830.0,
        radius_bottom_km=0.0,
        state_of_matter="Liquid Metallic Alloy",
        primary_composition="Fe-Ni with exceptionally high light-element fraction (> 20 wt% S, O, C, H)",
        density_kg_m3=5900.0,
        density_range_kg_m3=[5700.0, 6300.0],
        temperature_k=2200.0,
        temperature_range_k=[1900.0, 2500.0],
        evidence_type="MODEL_ESTIMATED",
        seismic_p_velocity_km_s=5.0,
        seismic_s_velocity_km_s=0.0,
        scientific_significance="Initial 2021 estimate produced an unexpectedly large core that required difficult-to-explain light element enrichment.",
        source_citation="Stähler et al. (2021), Science",
        doi="10.1126/science.abi7730",
        model_notes="Superseded in 2023 by discovery of basal molten silicate layer."
    )
]

# Backward-compatibility alias
MARS_INTERIOR_LAYERS = SAMUEL_2023_LAYERS


def get_mars_interior_summary(profile: str = "samuel_2023_basal_molten") -> MarsInteriorModel:
    """
    Returns the specified scientific Mars interior model with InSight seismic provenance.
    Supports 'samuel_2023_basal_molten' (default consensus) and 'stahler_2021_large_core' (historical).
    """
    if profile == "stahler_2021_large_core":
        return MarsInteriorModel(
            profile_id="stahler_2021_large_core",
            profile_name="Stähler et al. (Science 2021) Initial Large-Core Model",
            planetary_radius_km=3389.5,
            planetary_mass_kg=6.4171e23,
            surface_gravity_m_s2=3.72076,
            seismic_station="InSight SEIS (Station XB.ELYSE, Elysium Planitia, 4.50°N 135.62°E)",
            data_vintage="NASA InSight Mission (2021 Initial Data Release)",
            core_radius_km=1830.0,
            core_radius_uncertainty_km=40.0,
            has_basal_molten_layer=False,
            basal_molten_layer_thickness_km=0.0,
            layers=STAHLER_2021_LAYERS,
            crustal_dichotomy_notes="Two-layer crust inversion with 39 ± 8 km Moho depth.",
            core_composition_notes="Low density (~5.9 g/cm³) implied >20 wt% light elements before basal silicate discovery.",
            scientific_provenance=ProvenanceFactory.create_insight_interior_provenance(profile="stahler_2021_large_core")
        )

    # Default: 2023 Nature Reconciled Model
    return MarsInteriorModel(
        profile_id="samuel_2023_basal_molten",
        profile_name="Samuel et al. & Khan et al. (Nature 2023) Reconciled Model",
        planetary_radius_km=3389.5,
        planetary_mass_kg=6.4171e23,
        surface_gravity_m_s2=3.72076,
        seismic_station="InSight SEIS (Station XB.ELYSE, Elysium Planitia, 4.50°N 135.62°E)",
        data_vintage="NASA InSight Mission (2023 Final Archive Data)",
        core_radius_km=1650.0,
        core_radius_uncertainty_km=20.0,
        has_basal_molten_layer=True,
        basal_molten_layer_thickness_km=160.0,
        layers=SAMUEL_2023_LAYERS,
        crustal_dichotomy_notes=(
            "The Martian crust exhibits strong hemispheric dichotomy: the smooth Northern Lowlands have an "
            "average crustal thickness of ~30 km, whereas the cratered Southern Highlands range from 55 to 75 km. "
            "Under the InSight lander in Elysium Planitia, Moho depth is ~39 ± 8 km."
        ),
        core_composition_notes=(
            "The reconciled core radius of 1650 ± 20 km yields a density of ~6.1-6.4 g/cm³, consistent with "
            "15 to 18 wt% sulfur plus minor C, O, and H. The overlying 160-km basal molten silicate layer "
            "explains previous seismic travel-time anomalies."
        ),
        scientific_provenance=ProvenanceFactory.create_insight_interior_provenance(profile="samuel_2023_basal_molten")
    )


def compare_interior_models() -> Dict[str, Any]:
    """Provides a structured scientific comparison between published InSight interior interpretations."""
    m2021 = get_mars_interior_summary("stahler_2021_large_core")
    m2023 = get_mars_interior_summary("samuel_2023_basal_molten")
    return {
        "status": "COMPARISON_READY",
        "key_discrepancy": "Core radius and existence of basal molten silicate layer",
        "resolution_year": 2023,
        "models": {
            "historical_2021": {
                "profile_id": m2021.profile_id,
                "citation": "Stähler et al. (2021), Science",
                "core_radius_km": m2021.core_radius_km,
                "core_radius_uncertainty_km": m2021.core_radius_uncertainty_km,
                "has_basal_silicate_layer": m2021.has_basal_molten_layer,
                "core_density_kg_m3": 5900.0,
                "light_elements_wt_pct": "> 20 wt%",
                "status": "SUPERSEDED"
            },
            "consensus_2023": {
                "profile_id": m2023.profile_id,
                "citation": "Samuel et al. (2023), Nature; Khan et al. (2023), Nature",
                "core_radius_km": m2023.core_radius_km,
                "core_radius_uncertainty_km": m2023.core_radius_uncertainty_km,
                "has_basal_silicate_layer": m2023.has_basal_molten_layer,
                "basal_layer_thickness_km": m2023.basal_molten_layer_thickness_km,
                "core_density_kg_m3": 6100.0,
                "light_elements_wt_pct": "15 - 18 wt%",
                "status": "CURRENT_CONSENSUS"
            }
        },
        "scientific_takeaway": (
            "The 2021 discovery inferred an apparent core radius of 1830 km by mistaking the top of a deep "
            "160-km molten silicate layer for the core boundary. S1000a meteorite impact data in 2023 resolved "
            "the true metallic core radius to 1650 ± 20 km, resolving mineral physics paradoxes."
        )
    }
