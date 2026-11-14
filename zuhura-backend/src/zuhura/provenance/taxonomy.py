"""
Epistemic status taxonomy (observed, measured, derived, estimated, simulated).
Centralized Provenance & Epistemic Classification Architecture
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class EpistemicClassification(str, Enum):
    """
    Epistemic certainty classifications for planetary data and models.
    Enforces strict separation between empirical observations and mathematical models.
    """
    OBSERVED = "OBSERVED"                  # Calibrated instrument sensors (e.g. optical pixels)
    MEASURED = "MEASURED"                  # Physical measurements (e.g. MOLA laser transit time)
    DERIVED = "DERIVED"                    # Computed via deterministic mathematical transforms
    MODEL_ESTIMATED = "MODEL_ESTIMATED"    # Geophysical, mineralogical, or physical inversions
    SIMULATED = "SIMULATED"                # Synthetic pathfinding, rover mobility scenarios
    PROVISIONAL = "PROVISIONAL"            # Automated AI-discovered candidate features
    UNVERIFIED = "UNVERIFIED"              # Theoretical hypotheses lacking confirmation


class UncertaintyModel(BaseModel):
    """Rigorous uncertainty specification supporting scalar and bound intervals."""
    nominal_value: Optional[float] = None
    uncertainty_absolute: Optional[float] = None
    uncertainty_percentage: Optional[float] = None
    bounds_min: Optional[float] = None
    bounds_max: Optional[float] = None
    confidence_interval: Optional[float] = Field(default=0.95, description="Confidence interval fraction (e.g. 0.95 for 2-sigma)")
    unit: str = Field(..., description="SI or scientific unit (e.g. 'm', 'km', 'kg/m^3', 'km/s', 'degrees')")
    methodology: str = Field(default="gaussian_propagation", description="Uncertainty estimation methodology")


class ScientificReference(BaseModel):
    """Peer-reviewed scientific citation metadata."""
    citation: str
    doi: Optional[str] = None
    authors: Optional[List[str]] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    url: Optional[str] = None


class ScientificProvenanceRecord(BaseModel):
    """
    Standardized provenance metadata attached to every scientific calculation and data asset.
    """
    classification: EpistemicClassification
    original_dataset_id: str
    data_source: str
    processing_algorithm: str
    processing_version: str
    spatial_resolution: str
    coordinate_reference_system: str = "IAU_2015:MARS_WGCCRE"
    vertical_datum: str = "MARS_AREOID_MOLA_MEG128"
    measurement_units: str
    uncertainty: Optional[UncertaintyModel] = None
    scientific_references: List[ScientificReference] = Field(default_factory=list)
    validation_status: str = Field(default="VALIDATED", description="'VALIDATED', 'PROVISIONAL', 'RECONCILED', or 'UNCALIBRATED'")
    computation_timestamp: Optional[str] = None
    disclaimer: Optional[str] = None

    def to_summary_dict(self) -> Dict[str, Any]:
        """Provides concise summary dictionary for API responses."""
        return {
            "classification": self.classification.value,
            "dataset": self.original_dataset_id,
            "source": self.data_source,
            "algorithm": self.processing_algorithm,
            "crs": self.coordinate_reference_system,
            "vertical_datum": self.vertical_datum,
            "status": self.validation_status,
            "references_count": len(self.scientific_references)
        }


class ProvenanceFactory:
    """Helper to build standardized provenance records with default planetary geodetic frames."""

    @staticmethod
    def create_mola_elevation_provenance(algorithm: str = "bilinear_interpolation") -> ScientificProvenanceRecord:
        return ScientificProvenanceRecord(
            classification=EpistemicClassification.MEASURED,
            original_dataset_id="MOLA_MEG128",
            data_source="NASA PDS Geosciences Node / Mars Global Surveyor MOLA Team",
            processing_algorithm=algorithm,
            processing_version="v2.1",
            spatial_resolution="128 pixels/degree (~463 m/pixel at equator)",
            coordinate_reference_system="IAU_2015:MARS_WGCCRE (Planetocentric, East-Positive)",
            vertical_datum="MARS_AREOID_MOLA_MEG128 (Equipotential Zero Elevation)",
            measurement_units="meters",
            uncertainty=UncertaintyModel(
                uncertainty_absolute=1.0,
                bounds_min=-8200.0,
                bounds_max=21229.0,
                unit="meters",
                methodology="MOLA laser altimetry pulse transit time calibration"
            ),
            scientific_references=[
                ScientificReference(
                    citation="Smith, D. E., et al. (2001). Mars Orbiter Laser Altimeter: Experiment summary and selected results. J. Geophys. Res., 106(E10), 23689-23722.",
                    doi="10.1029/2000JE001364",
                    journal="Journal of Geophysical Research: Planets",
                    year=2001
                )
            ],
            validation_status="VALIDATED"
        )

    @staticmethod
    def create_insight_interior_provenance(profile: str = "samuel_2023_basal_molten") -> ScientificProvenanceRecord:
        if profile == "stahler_2021_large_core":
            return ScientificProvenanceRecord(
                classification=EpistemicClassification.MODEL_ESTIMATED,
                original_dataset_id="INSIGHT_SEIS_2021_ARCHIVE",
                data_source="NASA Planetary Data System / InSight Mars Lander SEIS Team",
                processing_algorithm="Direct core-reflected shear wave (ScS) and receiver function inversion",
                processing_version="2021-initial-science",
                spatial_resolution="Global point-station inversion (Station XB.ELYSE)",
                coordinate_reference_system="IAU_2015:MARS_WGCCRE",
                vertical_datum="MARS_AREOID_MOLA_MEG128",
                measurement_units="km, kg/m^3, km/s",
                uncertainty=UncertaintyModel(
                    nominal_value=1830.0,
                    uncertainty_absolute=40.0,
                    bounds_min=1790.0,
                    bounds_max=1870.0,
                    unit="km",
                    methodology="Markov Chain Monte Carlo seismic travel-time inversion"
                ),
                scientific_references=[
                    ScientificReference(
                        citation="Stähler, S. C., et al. (2021). Seismic detection of the Martian core. Science, 373(6553), 443-448.",
                        doi="10.1126/science.abi7730",
                        journal="Science",
                        year=2021
                    )
                ],
                validation_status="SUPERSEDED_BY_2023_DISCOVERY",
                disclaimer="HISTORICAL RECONCILIATION: This 2021 model inferred an apparent core radius of 1830 km. In 2023, discovery of a 160-km basal molten silicate layer revised the true core radius to ~1650 km."
            )
        else:
            return ScientificProvenanceRecord(
                classification=EpistemicClassification.DERIVED,
                original_dataset_id="INSIGHT_SEIS_2023_FINAL_ARCHIVE",
                data_source="NASA PDS / InSight SEIS Event S1000a Far-side Meteorite Impact Data",
                processing_algorithm="Diffracted P-diff and SKS wave travel-time inversion with basal slag decoupling",
                processing_version="2023-nature-reconciled",
                spatial_resolution="Global point-station inversion (Station XB.ELYSE)",
                coordinate_reference_system="IAU_2015:MARS_WGCCRE",
                vertical_datum="MARS_AREOID_MOLA_MEG128",
                measurement_units="km, kg/m^3, km/s",
                uncertainty=UncertaintyModel(
                    nominal_value=1650.0,
                    uncertainty_absolute=20.0,
                    bounds_min=1630.0,
                    bounds_max=1670.0,
                    unit="km",
                    methodology="Joint seismic wave travel time and geodynamic heat flow inversion"
                ),
                scientific_references=[
                    ScientificReference(
                        citation="Samuel, H., et al. (2023). Geophysical evidence for an enriched molten silicate layer above Mars's core. Nature, 622, 712-717.",
                        doi="10.1038/s41586-023-06601-8",
                        journal="Nature",
                        year=2023
                    ),
                    ScientificReference(
                        citation="Khan, A., et al. (2023). Evidence for a liquid silicate layer atop the Martian core. Nature, 622, 718-723.",
                        doi="10.1038/s41586-023-06586-4",
                        journal="Nature",
                        year=2023
                    )
                ],
                validation_status="VALIDATED",
                disclaimer="CURRENT SCIENTIFIC CONSENSUS: Confirms a 160-km thick molten silicate layer blanket atop a 1650-km liquid Fe-Ni metallic core."
            )

    @staticmethod
    def create_rover_simulation_provenance(mobility_profile: str) -> ScientificProvenanceRecord:
        return ScientificProvenanceRecord(
            classification=EpistemicClassification.SIMULATED,
            original_dataset_id="MOLA_MEG128_TRAVERSE_MODEL",
            data_source="Orbital Topography and Rover Mobility Mechanical Equations",
            processing_algorithm="Multi-criteria cost-distance A* pathfinding with Bekker soil mechanics & solar insolation",
            processing_version="Zuhura-Mobility-v2.0",
            spatial_resolution="25-50 grid points along traverse corridor",
            coordinate_reference_system="IAU_2015:MARS_WGCCRE",
            vertical_datum="MARS_AREOID_MOLA_MEG128",
            measurement_units="km, meters, degrees, Wh/km, sols",
            uncertainty=UncertaintyModel(
                uncertainty_percentage=15.0,
                unit="percentage",
                methodology="Sub-pixel hazard and soil slip uncertainty estimation"
            ),
            scientific_references=[
                ScientificReference(
                    citation="Arvidson, R. E., et al. (2017). Mars Science Laboratory Curiosity rover traverse and science results from Gale crater to Mount Sharp. J. Geophys. Res. Planets, 122(3), 614-633.",
                    doi="10.1002/2016JE005183",
                    year=2017
                )
            ],
            validation_status="SIMULATED",
            disclaimer="RESEARCH SIMULATION ONLY: Computed using orbital topographic models. Sub-pixel boulders, sand dunes, and soft regolith are not fully resolved at orbital scales."
        )

    @staticmethod
    def create_viking_basemap_provenance() -> ScientificProvenanceRecord:
        return ScientificProvenanceRecord(
            classification=EpistemicClassification.OBSERVED,
            original_dataset_id="VIKING_MDIM_21",
            data_source="USGS Astrogeology Science Center / NASA PDS Viking Visual Imaging Subsystem (VIS)",
            processing_algorithm="Orthorectified calibrated visual radiance mosaic with planetary limb correction",
            processing_version="MDIM 2.1",
            spatial_resolution="232 m/pixel (Level 0–10)",
            coordinate_reference_system="IAU_2015:MARS_WGCCRE (Planetocentric, East-Positive)",
            vertical_datum="MARS_AREOID_MOLA_MEG128",
            measurement_units="Radiance factor (I/F), dimensionless reflectance",
            uncertainty=UncertaintyModel(
                uncertainty_absolute=15.0,
                unit="meters",
                methodology="Geodetic control network adjustment (crater Airy-0 prime meridian anchor)"
            ),
            scientific_references=[
                ScientificReference(
                    citation="Archinal, B. A., et al. (2003). Mars Digital Image Mosaic 2.1. USGS Open-File Report 03-396.",
                    journal="USGS Astrogeology Publications",
                    year=2003
                )
            ],
            validation_status="VALIDATED",
            disclaimer="CALIBRATED VISUAL MOSAIC: Natural color albedo mosaic representing Viking orbiter observations normalized to 30 deg solar phase angle."
        )

    @staticmethod
    def create_ctx_mosaic_provenance() -> ScientificProvenanceRecord:
        return ScientificProvenanceRecord(
            classification=EpistemicClassification.OBSERVED,
            original_dataset_id="MRO_CTX_JEZERO_MOSAIC",
            data_source="Malin Space Science Systems (MSSS) / NASA PDS / MRO Context Camera",
            processing_algorithm="Radiometrically calibrated ISIS3 bundle-adjusted mosaic",
            processing_version="Jezero-CTX-v3.2",
            spatial_resolution="5.55 m/pixel (Level 9–15)",
            coordinate_reference_system="IAU_2015:MARS_WGCCRE (Planetocentric, East-Positive)",
            vertical_datum="MARS_AREOID_MOLA_MEG128",
            measurement_units="Calibrated radiance (W / m^2 / sr / um)",
            uncertainty=UncertaintyModel(
                uncertainty_absolute=3.0,
                unit="meters",
                methodology="MRO spacecraft SPICE ephemeris and stereo DTM ground tie-point resection"
            ),
            scientific_references=[
                ScientificReference(
                    citation="Malin, M. C., et al. (2007). Context Camera Investigation on board the Mars Reconnaissance Orbiter. J. Geophys. Res., 112(E5), E05S04.",
                    doi="10.1029/2006JE002808",
                    year=2007
                )
            ],
            validation_status="VALIDATED",
            disclaimer="REGIONAL CONTEXT OBSERVATION: High-contrast panchromatic imaging over Western Jezero Crater floor, delta deposits, and crater rim."
        )

    @staticmethod
    def create_hirise_provenance() -> ScientificProvenanceRecord:
        return ScientificProvenanceRecord(
            classification=EpistemicClassification.OBSERVED,
            original_dataset_id="MRO_HIRISE_JEZERO_PERSEVERANCE",
            data_source="University of Arizona Lunar & Planetary Laboratory / NASA PDS / HiRISE Team",
            processing_algorithm="Sub-pixel CCD pushbroom jitter correction & USGS ISIS3 orthorectification",
            processing_version="HiRISE-EDR-to-RDR-v4.0",
            spatial_resolution="0.25 to 0.50 m/pixel (Level 13–18)",
            coordinate_reference_system="IAU_2015:MARS_WGCCRE (Planetocentric, East-Positive)",
            vertical_datum="MARS_AREOID_MOLA_MEG128",
            measurement_units="Radiance factor (I/F)",
            uncertainty=UncertaintyModel(
                uncertainty_absolute=0.50,
                unit="meters",
                methodology="Rigorous spacecraft pointing jitter reconstruction and photoclinometry"
            ),
            scientific_references=[
                ScientificReference(
                    citation="McEwen, A. S., et al. (2007). Mars Reconnaissance Orbiter's High Resolution Imaging Science Experiment (HiRISE). J. Geophys. Res., 112(E5), E05S02.",
                    doi="10.1029/2005JE002605",
                    year=2007
                )
            ],
            validation_status="VALIDATED",
            disclaimer="SUB-METER TARGETED OBSERVATION: Resolves individual boulders (>1m), rover tracks, and outcrop layers across Octavia E. Butler touchdown ellipse."
        )

    @staticmethod
    def create_morphometry_provenance(derivative_type: str = "slope") -> ScientificProvenanceRecord:
        return ScientificProvenanceRecord(
            classification=EpistemicClassification.DERIVED,
            original_dataset_id="MOLA_MEG128_DERIVATIVE",
            data_source="NASA PDS Geosciences Node / MOLA Altimetry Grid",
            processing_algorithm=f"Metric Horn (1981) finite-difference gradient operator ({derivative_type})",
            processing_version="Zuhura-Morphometry-v1.4",
            spatial_resolution="463 m/pixel (128 pixels/degree)",
            coordinate_reference_system="IAU_2015:MARS_WGCCRE",
            vertical_datum="MARS_AREOID_MOLA_MEG128",
            measurement_units="degrees" if derivative_type == "slope" else "meters",
            uncertainty=UncertaintyModel(
                uncertainty_absolute=0.5,
                unit="degrees" if derivative_type == "slope" else "meters",
                methodology="3x3 moving window finite-difference propagation on MOLA DEM"
            ),
            scientific_references=[
                ScientificReference(
                    citation="Horn, B. K. P. (1981). Hill shading and the reflectance map. Proceedings of the IEEE, 69(1), 14-47.",
                    doi="10.1109/PROC.1981.11918",
                    year=1981
                )
            ],
            validation_status="VALIDATED",
            disclaimer="MATHEMATICALLY DERIVED PRODUCT: Derived directly from 3x3 kernel convolution over calibrated MOLA areoid topography."
        )

    @staticmethod
    def create_provisional_region_provenance() -> ScientificProvenanceRecord:
        return ScientificProvenanceRecord(
            classification=EpistemicClassification.PROVISIONAL,
            original_dataset_id="ZUHURA_TOPOGRAPHIC_CLUSTERING",
            data_source="MOLA MEG128 Elevation, TRI Roughness, and Metric Slope Derivatives",
            processing_algorithm="Multi-parametric radial-angular topographic boundary clustering",
            processing_version="Zuhura-Segmentation-v1.2",
            spatial_resolution="128 pixels/degree",
            coordinate_reference_system="IAU_2015:MARS_WGCCRE",
            vertical_datum="MARS_AREOID_MOLA_MEG128",
            measurement_units="Square kilometers (area), meters (elevation)",
            uncertainty=UncertaintyModel(
                uncertainty_percentage=12.0,
                unit="percentage",
                methodology="Boundary pixel classification sensitivity thresholding"
            ),
            scientific_references=[],
            validation_status="PROVISIONAL",
            disclaimer="PROVISIONAL CLASSIFICATION NOTICE: Region boundaries and provisional names are generated algorithmically by Zuhura Mars. They do NOT represent official International Astronomical Union (IAU) nomenclature until formally approved by the Working Group for Planetary System Nomenclature (WGPSN)."
        )

    @staticmethod
    def create_atmospheric_environment_provenance() -> ScientificProvenanceRecord:
        return ScientificProvenanceRecord(
            classification=EpistemicClassification.MODEL_ESTIMATED,
            original_dataset_id="MCD_V53_VIKING_REMS_APSS",
            data_source="Mars Climate Database (MCD v5.3) / Viking Lander / Curiosity REMS / InSight APSS",
            processing_algorithm="Hydrostatic scale height hypsometry with seasonal CO2 polar condensation cycle",
            processing_version="Zuhura-Atmosphere-v2.0",
            spatial_resolution="Point coordinate vertical hypsometry",
            coordinate_reference_system="IAU_2015:MARS_WGCCRE",
            vertical_datum="MARS_AREOID_MOLA_MEG128",
            measurement_units="Pascals (Pa), kg/m^3, Kelvin (K)",
            uncertainty=UncertaintyModel(
                uncertainty_absolute=18.0,
                bounds_min=550.0,
                bounds_max=1200.0,
                unit="Pa",
                methodology="Curiosity REMS and Viking pressure sensor empirical calibration"
            ),
            scientific_references=[
                ScientificReference(
                    citation="Forget, F., et al. (1999). Improved general circulation models of the Martian atmosphere from the surface to above 80 km. J. Geophys. Res., 104(E10), 24155-24175.",
                    doi="10.1029/1999JE001025",
                    journal="Journal of Geophysical Research: Planets",
                    year=1999
                ),
                ScientificReference(
                    citation="Hess, S. L., et al. (1980). The annual cycle of pressure on Mars measured by Viking Landers 1 and 2. Tellus, 32(3), 238-251.",
                    doi="10.3402/tellusa.v32i3.10574",
                    journal="Tellus",
                    year=1980
                )
            ],
            validation_status="VALIDATED",
            disclaimer="ATMOSPHERIC MODELING ESTIMATE: Hydrostatic hypsometric profile coupled with empirical CO2 condensation annual cycle. Local transient barometric fronts and microscale thermal plumes can cause +/- 5-10 Pa short-term deviations."
        )

    @staticmethod
    def create_dust_optical_depth_provenance() -> ScientificProvenanceRecord:
        return ScientificProvenanceRecord(
            classification=EpistemicClassification.MODEL_ESTIMATED,
            original_dataset_id="MGS_TES_MRO_MCS_DUST_SCENARIO",
            data_source="NASA PDS Atmospheres Node / MGS TES / MRO Mars Climate Sounder (MCS)",
            processing_algorithm="Visible column dust optical depth (tau_vis at 610 nm) Montabone climatology",
            processing_version="Zuhura-DustClim-v1.8",
            spatial_resolution="Regional grid climatology interpolated to point coordinate",
            coordinate_reference_system="IAU_2015:MARS_WGCCRE",
            vertical_datum="MARS_AREOID_MOLA_MEG128",
            measurement_units="Dimensionless optical depth (tau)",
            uncertainty=UncertaintyModel(
                uncertainty_absolute=0.10,
                bounds_min=0.15,
                bounds_max=5.0,
                unit="dimensionless",
                methodology="Thermal emission spectrometer visible extinction cross-calibration"
            ),
            scientific_references=[
                ScientificReference(
                    citation="Montabone, L., et al. (2015). An open-access database of Martian atmospheric dust optical depth for 12 Martian years. Icarus, 251, 65-95.",
                    doi="10.1016/j.icarus.2014.12.034",
                    journal="Icarus",
                    year=2015
                )
            ],
            validation_status="VALIDATED",
            disclaimer="CLIMATOLOGICAL ESTIMATE: Visible optical depth reflects seasonal median climatology. Stochastic regional dust storms (especially during Ls=180-320) can elevate tau dramatically within sols."
        )

    @staticmethod
    def create_solar_power_provenance() -> ScientificProvenanceRecord:
        return ScientificProvenanceRecord(
            classification=EpistemicClassification.SIMULATED,
            original_dataset_id="ZUHURA_MARS_PV_SOLAR_BUDGET_SIMULATOR",
            data_source="Orbital Insolation & Radiative Atmospheric Attenuation Model",
            processing_algorithm="Direct and diffuse solar irradiance integration with atmospheric tau extinction",
            processing_version="Zuhura-PowerBudget-v2.0",
            spatial_resolution="Diurnal solar curve integrated over 24.66-hour Martian Sol",
            coordinate_reference_system="IAU_2015:MARS_WGCCRE",
            vertical_datum="MARS_AREOID_MOLA_MEG128",
            measurement_units="Watts (W), Watt-hours per sol (Wh/sol)",
            uncertainty=UncertaintyModel(
                uncertainty_percentage=8.0,
                unit="percentage",
                methodology="Rayleigh scattering, aerosol single-scattering albedo, and dust obscuration propagation"
            ),
            scientific_references=[
                ScientificReference(
                    citation="Appelbaum, J., & Flood, D. J. (1990). Solar radiation on Mars. Solar Energy, 45(6), 353-363.",
                    doi="10.1016/0038-092X(90)90156-7",
                    journal="Solar Energy",
                    year=1990
                ),
                ScientificReference(
                    citation="Lorenz, R. D. (2020). Mars Rover and Lander Power: Operational Lessons and Future Outlook. Space Science Reviews, 216(7), 117.",
                    doi="10.1007/s11214-020-00742-8",
                    year=2020
                )
            ],
            validation_status="SIMULATED",
            disclaimer="MISSION SIMULATION PRODUCT: Predicted photovoltaic yield accounts for solar geometry and atmospheric column dust. Actual output is subject to local horizon obstruction, wind cleaning events, and panel degradation."
        )
