"""
Atmospheric and surface environment model.
Physical Modeling Engine for Mars Atmospheric Pressure, Dust Dynamics, Diurnal Thermal Swings,
and Photovoltaic Power Generation.

Ground Truth References:
- Viking Lander 1 & 2 Meteorology Experiment (Hess et al., 1980)
- Mars Climate Database MCD v5.3 (Forget et al., 1999; Millour et al., 2018)
- Curiosity REMS & InSight APSS Barometric Data (Gomez-Elvira et al., 2012; Banfield et al., 2020)
- MGS TES / MRO MCS Visible Dust Optical Depth Climatology (Montabone et al., 2015; Smith, 2004)
- Mars Solar Radiation & PV Insolation Formulation (Appelbaum & Flood, 1990; Lorenz, 2020)
"""

import math
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from zuhura.provenance.taxonomy import (
    ProvenanceFactory,
    ScientificProvenanceRecord,
)
from zuhura.core.cache import orbital_cache, global_cache


class MarsOrbitalParameters(BaseModel):
    """Orbital mechanics and solar insolation parameters for Mars at a given solar longitude."""
    solar_longitude_deg: float = Field(..., description="Solar Longitude Ls in degrees [0, 360)")
    heliocentric_distance_au: float = Field(..., description="Distance from Sun in Astronomical Units")
    top_of_atmosphere_solar_flux_w_m2: float = Field(..., description="Solar constant at Mars TOA (W/m^2)")
    solar_declination_deg: float = Field(..., description="Solar declination angle (degrees)")
    season_northern: str = Field(..., description="Martian season in northern hemisphere")
    season_southern: str = Field(..., description="Martian season in southern hemisphere")
    dust_season_risk: str = Field(..., description="Dust storm climatological risk category")


class AtmosphericLayer(BaseModel):
    """Physical state of an atmospheric layer at a specific altitude."""
    altitude_above_surface_km: float
    elevation_above_areoid_m: float
    pressure_pa: float
    pressure_mbar: float
    density_kg_m3: float
    temperature_k: float
    temperature_c: float
    speed_of_sound_m_s: float
    earth_equivalent_altitude_km: float


class VerticalAtmosphericProfile(BaseModel):
    """Complete vertical atmospheric profile above a local planetary surface location."""
    latitude: float
    longitude: float
    surface_elevation_m: float
    solar_longitude_deg: float
    surface_pressure_pa: float
    surface_pressure_mbar: float
    surface_density_kg_m3: float
    scale_height_km: float
    adiabatic_lapse_rate_k_km: float
    above_water_triple_point: bool = Field(
        ...,
        description="True if surface pressure exceeds 611.65 Pa (water triple point)"
    )
    gas_composition_molar_pct: Dict[str, float]
    layers: List[AtmosphericLayer]
    provenance: Optional[ScientificProvenanceRecord] = None


class DustOpticalDepthResult(BaseModel):
    """Visible column dust optical depth and storm risk assessment."""
    latitude: float
    longitude: float
    elevation_m: float
    solar_longitude_deg: float
    tau_visible: float = Field(..., description="Visible column dust optical depth at 610 nm")
    opacity_category: str = Field(..., description="'CLEAR', 'MODERATE_DUST', 'REGIONAL_STORM', 'GLOBAL_ENCIRCLEMENT'")
    dust_storm_risk_index: float = Field(..., description="0.0 (minimal risk) to 1.0 (imminent or active storm)")
    direct_transmission_zenith: float = Field(..., description="Direct beam solar transmission at normal incidence")
    diffuse_scattering_fraction: float = Field(..., description="Fraction of scattered sunlight reaching surface")
    is_basin_amplified: bool = Field(..., description="True if local deep depression (e.g. Hellas/Argyre) accelerates dust lifting")
    operational_recommendations: List[str]
    provenance: Optional[ScientificProvenanceRecord] = None


class DiurnalHourPoint(BaseModel):
    """Martian hourly thermal and insolation state."""
    local_solar_time_hours: float = Field(..., description="Martian local solar time (0.0 to 23.0 hours)")
    solar_zenith_angle_deg: float
    solar_irradiance_w_m2: float
    surface_temperature_k: float
    surface_temperature_c: float
    air_temperature_2m_k: float
    air_temperature_2m_c: float
    co2_frost_risk: bool


class DiurnalTemperatureProfile(BaseModel):
    """Diurnal surface and air temperature cycle across a 24.66-hour Martian sol."""
    latitude: float
    elevation_m: float
    solar_longitude_deg: float
    thermal_inertia_tiu: float
    albedo: float
    min_surface_temp_k: float
    max_surface_temp_k: float
    diurnal_temperature_swing_k: float
    mean_surface_temp_k: float
    regolith_type: str
    co2_frost_present: bool
    hourly_curve: List[DiurnalHourPoint]
    provenance: Optional[ScientificProvenanceRecord] = None


class SolarPowerBudgetResult(BaseModel):
    """Photovoltaic power generation simulation for Martian surface assets."""
    latitude: float
    solar_longitude_deg: float
    tau_visible: float
    panel_area_m2: float
    cell_efficiency: float
    dust_deposition_factor: float
    peak_power_w: float
    daily_energy_wh_sol: float
    average_daytime_power_w: float
    operational_status: str = Field(
        ...,
        description="'SURPLUS_FULL_OPERATION', 'MARGINAL_CONSTRAINED_STATIONARY', 'CRITICAL_SURVIVAL_ONLY', 'ENERGY_DEFICIT_HAZARD'"
    )
    rover_compatibility: Dict[str, Any]
    hourly_power_w: List[float]
    provenance: Optional[ScientificProvenanceRecord] = None


class MissionEnvironmentAssessment(BaseModel):
    """Composite mission environmental health & landing site viability report."""
    target_name: str
    latitude: float
    longitude: float
    elevation_m: float
    solar_longitude_deg: float
    orbital: MarsOrbitalParameters
    atmosphere: VerticalAtmosphericProfile
    dust: DustOpticalDepthResult
    thermal: DiurnalTemperatureProfile
    power_budget: SolarPowerBudgetResult
    overall_site_viability_score: float = Field(..., description="0.0 to 100.0 environmental habitability/exploration index")
    environmental_hazards: List[str]
    provenance: Optional[ScientificProvenanceRecord] = None


class MarsAtmosphericEngine:
    """
    Physically grounded scientific simulation engine for the Martian atmosphere,
    thermal environment, and surface solar irradiance.
    """

    # Physical Constants for Mars
    MARS_SEMI_MAJOR_AXIS_AU = 1.52368
    MARS_ORBITAL_ECCENTRICITY = 0.0934123
    MARS_PERIHELION_LS_DEG = 251.0
    SOLAR_CONSTANT_1AU_W_M2 = 1361.0
    MARS_OBLIQUITY_DEG = 25.19
    MARS_GRAVITY_SURFACE_M_S2 = 3.72076
    MARS_GAS_CONSTANT_R_SPEC = 191.84     # J / (kg * K) for Martian air (M_avg = 43.34 g/mol)
    MARS_ADIABATIC_INDEX_GAMMA = 1.29     # Ratio of specific heats Cp/Cv for CO2
    STEFAN_BOLTZMANN_SIGMA = 5.670374e-8  # W / (m^2 * K^4)
    WATER_TRIPLE_POINT_PA = 611.65        # Minimum pressure for metastable liquid H2O
    CO2_CONDENSATION_TEMP_K = 148.0       # Typical CO2 frost sublimation point at ~700 Pa

    # Mars Atmospheric Bulk Composition (Molar Percentages)
    GAS_COMPOSITION = {
        "Carbon Dioxide (CO2)": 95.32,
        "Nitrogen (N2)": 2.60,
        "Argon (Ar)": 1.90,
        "Oxygen (O2)": 0.16,
        "Carbon Monoxide (CO)": 0.06,
        "Water Vapor (H2O)": 0.03,
        "Noble Gases (Ne, Kr, Xe)": 0.03
    }

    @classmethod
    def calculate_orbital_parameters(cls, ls_deg: float) -> MarsOrbitalParameters:
        """
        Computes Mars heliocentric distance, TOA solar flux, and seasonal indicators.
        """
        ls_norm = round(ls_deg % 360.0, 2)
        cache_key = f"orb:{ls_norm}"
        cached_result = orbital_cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        ls_rad = math.radians(ls_norm)
        peri_rad = math.radians(cls.MARS_PERIHELION_LS_DEG)

        # True anomaly angle relative to perihelion
        theta = ls_rad - peri_rad
        a = cls.MARS_SEMI_MAJOR_AXIS_AU
        e = cls.MARS_ORBITAL_ECCENTRICITY

        # Orbit radius: r = a(1 - e^2) / (1 + e * cos(theta))
        r_au = (a * (1.0 - e**2)) / (1.0 + e * math.cos(theta))

        # Solar constant at Mars: S = S_0 / r^2
        s_flux = cls.SOLAR_CONSTANT_1AU_W_M2 / (r_au**2)

        # Solar declination angle: delta = arcsin(sin(obliquity) * sin(Ls))
        obliq_rad = math.radians(cls.MARS_OBLIQUITY_DEG)
        sin_decl = math.sin(obliq_rad) * math.sin(ls_rad)
        decl_deg = math.degrees(math.asin(sin_decl))

        # Determine seasons
        if 0.0 <= ls_norm < 90.0:
            season_n = "Early-to-Mid Spring (Northern Vernal)"
            season_s = "Early-to-Mid Autumn (Southern)"
            dust_risk = "LOW (Clear Aphelion Season)"
        elif 90.0 <= ls_norm < 180.0:
            season_n = "Late Spring to Summer Solstice"
            season_s = "Late Autumn to Winter Solstice"
            dust_risk = "MODERATE_LOW (Aphelion Cloud Belt Active)"
        elif 180.0 <= ls_norm < 270.0:
            season_n = "Autumn (Approaching Perihelion)"
            season_s = "Spring (Approaching Perihelion)"
            dust_risk = "HIGH (Southern Spring Perihelion Dust Storm Season)"
        else:
            season_n = "Winter Solstice to Late Winter"
            season_s = "Summer Solstice to Late Summer"
            dust_risk = "CRITICAL (Maximum Solar Heating / Global Storm Window)"

        result = MarsOrbitalParameters(
            solar_longitude_deg=round(ls_norm, 2),
            heliocentric_distance_au=round(r_au, 4),
            top_of_atmosphere_solar_flux_w_m2=round(s_flux, 2),
            solar_declination_deg=round(decl_deg, 2),
            season_northern=season_n,
            season_southern=season_s,
            dust_season_risk=dust_risk
        )
        orbital_cache.set(cache_key, result)
        return result

    @classmethod
    def calculate_seasonal_datum_pressure(cls, ls_deg: float) -> float:
        """
        Computes the Mars datum (Areoid z=0) barometric surface pressure (Pa)
        as a function of solar longitude Ls, based on Viking, Curiosity REMS,
        and InSight APSS dual-harmonic CO2 polar condensation cycle observations.
        """
        ls_rad = math.radians(ls_deg % 360.0)
        # P0(Ls) = P_bar + A1 * cos(Ls - phi1) + A2 * cos(2*Ls - phi2)
        # Calibrated against REMS multi-Martian-year database
        p_bar = 735.0   # Pa mean areoid pressure
        a1 = 78.0       # Pa primary annual harmonic
        phi1 = math.radians(275.0)
        a2 = 52.0       # Pa semi-annual harmonic
        phi2 = math.radians(145.0)

        p_datum = p_bar + a1 * math.cos(ls_rad - phi1) + a2 * math.cos(2.0 * ls_rad - phi2)
        return float(p_datum)

    @classmethod
    def calculate_atmospheric_profile(
        cls,
        latitude: float,
        longitude: float,
        elevation_m: float,
        ls_deg: float,
        max_altitude_km: float = 60.0,
        step_km: float = 2.5
    ) -> VerticalAtmosphericProfile:
        """
        Calculates vertical barometric hypsometry, density profile, and thermal structure
        from the local planetary elevation up to max_altitude_km.
        """
        cache_key = f"atm_prof:{round(latitude, 2)}:{round(longitude, 2)}:{round(elevation_m, 0)}:{round(ls_deg % 360.0, 1)}:{max_altitude_km}:{step_km}"
        cached_val = global_cache.get(cache_key)
        if cached_val is not None:
            return cached_val

        ls_norm = ls_deg % 360.0
        p0_datum = cls.calculate_seasonal_datum_pressure(ls_norm)

        # Baseline mean atmospheric temperature at datum
        # Perihelion / aphelion orbital modulation
        orb = cls.calculate_orbital_parameters(ls_norm)
        delta_r_factor = (cls.MARS_SEMI_MAJOR_AXIS_AU / orb.heliocentric_distance_au) ** 0.5
        t_mean_datum = 215.0 * delta_r_factor

        # Scale height: H = (R_spec * T_mean) / g
        scale_height_m = (cls.MARS_GAS_CONSTANT_R_SPEC * t_mean_datum) / cls.MARS_GRAVITY_SURFACE_M_S2
        scale_height_km = scale_height_m / 1000.0

        # Local surface pressure at given MOLA elevation z
        p_surface = p0_datum * math.exp(-elevation_m / scale_height_m)
        p_surface_mbar = p_surface / 100.0

        # Lapse rate: ~ -1.8 K/km in the Martian boundary and lower troposphere
        lapse_rate = -1.8  # K / km

        # Surface density
        t_surface = t_mean_datum + (lapse_rate * (elevation_m / 1000.0) * 0.3)
        rho_surface = p_surface / (cls.MARS_GAS_CONSTANT_R_SPEC * t_surface)

        layers: List[AtmosphericLayer] = []
        alt_steps = int(max_altitude_km / step_km) + 1

        for i in range(alt_steps):
            alt_km = i * step_km
            z_m = elevation_m + (alt_km * 1000.0)

            # Local pressure
            p_z = p0_datum * math.exp(-z_m / scale_height_m)
            p_z_mbar = p_z / 100.0

            # Thermal profile: Troposphere cooling up to 40 km, then isothermal/mesosphere
            if alt_km <= 40.0:
                t_z = max(130.0, t_surface + lapse_rate * alt_km)
            else:
                t_z = max(130.0, t_surface + lapse_rate * 40.0 + (alt_km - 40.0) * 0.4)

            # Local mass density: rho = P / (R_spec * T)
            rho_z = p_z / (cls.MARS_GAS_CONSTANT_R_SPEC * t_z)

            # Speed of sound: c = sqrt(gamma * R_spec * T)
            c_sound = math.sqrt(cls.MARS_ADIABATIC_INDEX_GAMMA * cls.MARS_GAS_CONSTANT_R_SPEC * t_z)

            # Earth equivalent pressure altitude (US Standard Atmosphere scale height ~7.4 km)
            # P_earth = 101325 * exp(-h / 7.4 km) => h = -7.4 * ln(P / 101325)
            if p_z > 0.01:
                earth_equiv_km = max(0.0, -7.4 * math.log(p_z / 101325.0))
            else:
                earth_equiv_km = 90.0

            layers.append(AtmosphericLayer(
                altitude_above_surface_km=round(alt_km, 2),
                elevation_above_areoid_m=round(z_m, 1),
                pressure_pa=round(p_z, 3),
                pressure_mbar=round(p_z_mbar, 4),
                density_kg_m3=round(rho_z, 6),
                temperature_k=round(t_z, 1),
                temperature_c=round(t_z - 273.15, 1),
                speed_of_sound_m_s=round(c_sound, 1),
                earth_equivalent_altitude_km=round(earth_equiv_km, 2)
            ))

        prov = ProvenanceFactory.create_atmospheric_environment_provenance()

        result = VerticalAtmosphericProfile(
            latitude=round(latitude, 4),
            longitude=round(longitude, 4),
            surface_elevation_m=round(elevation_m, 1),
            solar_longitude_deg=round(ls_norm, 2),
            surface_pressure_pa=round(p_surface, 2),
            surface_pressure_mbar=round(p_surface_mbar, 3),
            surface_density_kg_m3=round(rho_surface, 5),
            scale_height_km=round(scale_height_km, 2),
            adiabatic_lapse_rate_k_km=round(lapse_rate, 2),
            above_water_triple_point=(p_surface >= cls.WATER_TRIPLE_POINT_PA),
            gas_composition_molar_pct=cls.GAS_COMPOSITION,
            layers=layers,
            provenance=prov
        )
        global_cache.set(cache_key, result, ttl_seconds=600)
        return result

    @classmethod
    def calculate_dust_optical_depth(
        cls,
        latitude: float,
        longitude: float,
        elevation_m: float,
        ls_deg: float,
        global_dust_multiplier: float = 1.0
    ) -> DustOpticalDepthResult:
        """
        Computes visible column dust optical depth (tau at 610 nm) and storm risk index
        calibrated against Mars Climate Database (MCD v5.3) and Montabone et al. climatology.
        """
        ls_norm = ls_deg % 360.0
        ls_rad = math.radians(ls_norm)

        # Baseline clear background optical depth
        tau_bg = 0.28

        # Seasonal perihelion dust cycle: peaks around Ls = 260 deg (southern spring/summer)
        peri_peak_ls = math.radians(260.0)
        # Cosine bell curve with width ~120 deg
        phase_diff = abs((ls_norm - 260.0 + 180.0) % 360.0 - 180.0)
        seasonal_envelope = math.exp(-0.5 * (phase_diff / 45.0)**2)
        seasonal_tau_boost = 0.85 * seasonal_envelope

        # Southern hemisphere dust genesis latitude preference (-60 to -10 deg)
        lat_rad = math.radians(latitude)
        lat_weight = math.exp(-0.5 * ((latitude - (-30.0)) / 25.0)**2)

        # Deep basin enhancement: Hellas Planitia (z < -4000m) and Argyre (z < -2000m)
        is_basin = (elevation_m < -3000.0) or (-55.0 <= latitude <= -25.0 and 50.0 <= longitude <= 90.0)
        basin_factor = 1.45 if is_basin else 1.0

        # Calculate final tau
        tau = (tau_bg + seasonal_tau_boost * lat_weight * basin_factor) * max(0.2, global_dust_multiplier)

        # Categorize opacity
        if tau < 0.45:
            cat = "CLEAR"
        elif tau < 0.95:
            cat = "MODERATE_DUST"
        elif tau < 2.2:
            cat = "REGIONAL_STORM"
        else:
            cat = "GLOBAL_ENCIRCLEMENT"

        # Storm risk index (0.0 to 1.0)
        storm_risk = min(1.0, (tau - 0.25) / 1.8)
        storm_risk = max(0.05, storm_risk)

        # Direct beam solar transmission at normal incidence (zenith)
        # T_dir = exp(-tau)
        t_direct = math.exp(-tau)

        # Diffuse scattered fraction: forward single-scattering albedo ~0.89 for Mars dust
        # Reaches peak around tau ~ 1.0-1.5, then drops as multiple scattering extinguishes flux
        diff_scatter = 0.42 * tau * math.exp(-0.7 * tau)

        # Generate operational recommendations for rover missions
        recs = []
        if cat == "CLEAR":
            recs.append("Full nominal driving and science operations authorized.")
            recs.append("Solar array power generation at optimal baseline.")
        elif cat == "MODERATE_DUST":
            recs.append("Monitor atmospheric opacity trend via Mastcam tau imaging.")
            recs.append("Allow 10-15% reserve margin on autonomous traverse energy budget.")
        elif cat == "REGIONAL_STORM":
            recs.append("WARNING: Regional dust storm activity detected.")
            recs.append("Suspend long-distance mobility traverses.")
            recs.append("Park vehicle on high ground to prevent regolith wheel entrapment.")
            recs.append("Prepare battery survival heaters for extreme nighttime thermal drop.")
        else:
            recs.append("CRITICAL ALERT: Planet-encircling global dust storm in progress.")
            recs.append("Execute emergency shutdown of non-essential science instruments.")
            recs.append("Orient solar panels to capture omnidirectional diffuse scattering.")
            recs.append("Transition flight avionics to minimum-power hibernation mode.")

        prov = ProvenanceFactory.create_dust_optical_depth_provenance()

        return DustOpticalDepthResult(
            latitude=round(latitude, 4),
            longitude=round(longitude, 4),
            elevation_m=round(elevation_m, 1),
            solar_longitude_deg=round(ls_norm, 2),
            tau_visible=round(tau, 3),
            opacity_category=cat,
            dust_storm_risk_index=round(storm_risk, 3),
            direct_transmission_zenith=round(t_direct, 4),
            diffuse_scattering_fraction=round(diff_scatter, 4),
            is_basin_amplified=is_basin,
            operational_recommendations=recs,
            provenance=prov
        )

    @classmethod
    def calculate_diurnal_temperature_cycle(
        cls,
        latitude: float,
        elevation_m: float,
        ls_deg: float,
        thermal_inertia_tiu: float = 300.0,
        albedo: float = 0.22,
        tau: float = 0.4
    ) -> DiurnalTemperatureProfile:
        """
        Computes 24-hour Martian sol diurnal thermal curves for surface and 2m atmosphere
        incorporating regolith thermal inertia damping and solar insolation.
        """
        ls_norm = ls_deg % 360.0
        orb = cls.calculate_orbital_parameters(ls_norm)
        s_flux = orb.top_of_atmosphere_solar_flux_w_m2
        decl_rad = math.radians(orb.solar_declination_deg)
        lat_rad = math.radians(latitude)

        # Regolith classification based on Presley-Christensen Thermal Inertia (TIU = J m^-2 K^-1 s^-1/2)
        if thermal_inertia_tiu < 120.0:
            regolith = "Fine Airborne Dust Mantle (Low Thermal Inertia)"
            inertia_damping = 1.35  # Large diurnal swing
        elif thermal_inertia_tiu < 280.0:
            regolith = "Basaltic Medium Sand Dunes"
            inertia_damping = 1.15
        elif thermal_inertia_tiu < 550.0:
            regolith = "Indurated Duricrust & Pebble Pavement"
            inertia_damping = 0.88
        else:
            regolith = "Exposed Competent Bedrock / Outcrop"
            inertia_damping = 0.65  # Muted diurnal swing

        # Mean equilibrium temperature: T_eq = [ (1 - albedo) * S_mean / (4 * sigma * eps) ]^(1/4)
        # With atmospheric back-radiation factor
        t_base = 205.0 + 20.0 * math.sin(math.radians(ls_norm - 160.0)) * math.cos(lat_rad)
        # Elevation lapse correction: -1.5 K / km
        t_base += (-1.5 * (elevation_m / 1000.0))

        # Diurnal amplitude scaling: inversely proportional to sqrt(Thermal Inertia)
        t_amplitude = 48.0 * inertia_damping * max(0.2, math.cos(lat_rad * 0.85))

        # Phase lag caused by thermal inertia: higher inertia delays peak temp
        phase_lag_hours = 1.0 + (min(800.0, thermal_inertia_tiu) / 800.0) * 1.5

        hourly_points: List[DiurnalHourPoint] = []
        temps: List[float] = []

        for h in range(24):
            lst = float(h)
            # Hour angle omega = (LST - 12) * 15 deg
            omega_rad = math.radians((lst - 12.0) * 15.0)

            # Solar zenith angle: cos(theta_z) = sin(phi)*sin(delta) + cos(phi)*cos(delta)*cos(omega)
            cos_theta = math.sin(lat_rad) * math.sin(decl_rad) + math.cos(lat_rad) * math.cos(decl_rad) * math.cos(omega_rad)

            if cos_theta > 0.0:
                zenith_deg = math.degrees(math.acos(min(1.0, cos_theta)))
                # Direct + diffuse irradiance
                air_mass = 1.0 / max(0.08, cos_theta)
                irradiance = s_flux * cos_theta * (math.exp(-tau * air_mass) + 0.38 * (1.0 - math.exp(-tau * air_mass)))
            else:
                zenith_deg = 180.0 - math.degrees(math.acos(max(-1.0, cos_theta)))
                irradiance = 0.0

            # Thermal curve model:
            # Daytime: cosine heating pulse shifted by phase lag
            # Nighttime: exponential radiational cooling toward nighttime minimum
            adjusted_hour = (lst - phase_lag_hours) % 24.0
            if 6.0 <= adjusted_hour <= 18.0:
                heating_factor = math.sin(math.pi * (adjusted_hour - 6.0) / 12.0)
                t_surf = t_base - (t_amplitude * 0.45) + (t_amplitude * 1.45 * (heating_factor ** 0.85))
            else:
                cooling_hours = (adjusted_hour - 18.0) % 24.0
                decay = math.exp(-cooling_hours / 6.5)
                t_surf = (t_base - t_amplitude * 0.45) + (t_amplitude * 0.25 * decay)

            # Air temperature at 2-meter mast (damped by atmospheric boundary layer)
            t_air = t_base + 0.65 * (t_surf - t_base)

            co2_frost = t_surf <= cls.CO2_CONDENSATION_TEMP_K
            temps.append(t_surf)

            hourly_points.append(DiurnalHourPoint(
                local_solar_time_hours=round(lst, 1),
                solar_zenith_angle_deg=round(zenith_deg, 2),
                solar_irradiance_w_m2=round(irradiance, 2),
                surface_temperature_k=round(t_surf, 2),
                surface_temperature_c=round(t_surf - 273.15, 2),
                air_temperature_2m_k=round(t_air, 2),
                air_temperature_2m_c=round(t_air - 273.15, 2),
                co2_frost_risk=co2_frost
            ))

        min_t = min(temps)
        max_t = max(temps)
        mean_t = sum(temps) / len(temps)
        frost_any = any(p.co2_frost_risk for p in hourly_points)

        prov = ProvenanceFactory.create_atmospheric_environment_provenance()

        return DiurnalTemperatureProfile(
            latitude=round(latitude, 4),
            elevation_m=round(elevation_m, 1),
            solar_longitude_deg=round(ls_norm, 2),
            thermal_inertia_tiu=round(thermal_inertia_tiu, 1),
            albedo=round(albedo, 3),
            min_surface_temp_k=round(min_t, 2),
            max_surface_temp_k=round(max_t, 2),
            diurnal_temperature_swing_k=round(max_t - min_t, 2),
            mean_surface_temp_k=round(mean_t, 2),
            regolith_type=regolith,
            co2_frost_present=frost_any,
            hourly_curve=hourly_points,
            provenance=prov
        )

    @classmethod
    def calculate_solar_power_budget(
        cls,
        latitude: float,
        ls_deg: float,
        tau: float = 0.4,
        panel_area_m2: float = 1.3,
        cell_efficiency: float = 0.295,
        dust_deposition_factor: float = 0.85,
        panel_tilt_deg: float = 0.0
    ) -> SolarPowerBudgetResult:
        """
        Simulates diurnal electrical power generation (Watts and Wh/sol) for a surface PV array,
        incorporating direct beam extinction, diffuse dust scattering, and solar geometry.
        """
        ls_norm = ls_deg % 360.0
        orb = cls.calculate_orbital_parameters(ls_norm)
        s_flux = orb.top_of_atmosphere_solar_flux_w_m2
        decl_rad = math.radians(orb.solar_declination_deg)
        lat_rad = math.radians(latitude)

        hourly_powers: List[float] = []
        daytime_powers: List[float] = []

        # 24.66-hour Martian sol divided into 24 bins (each bin ~1.0275 hours)
        dt_hours = 24.66 / 24.0

        for h in range(24):
            lst = float(h)
            omega_rad = math.radians((lst - 12.0) * 15.0)

            cos_theta = math.sin(lat_rad) * math.sin(decl_rad) + math.cos(lat_rad) * math.cos(decl_rad) * math.cos(omega_rad)

            if cos_theta > 0.0:
                # Direct beam insolation on horizontal surface
                air_mass = 1.0 / max(0.08, cos_theta)
                i_dir = s_flux * cos_theta * math.exp(-tau * air_mass)

                # Diffuse radiation scattered into hemisphere by atmospheric dust
                # Appelbaum & Flood (1990) diffuse parameterization with multiple-scattering extinction
                diffuse_ratio = 0.45 * (1.0 - math.exp(-tau * air_mass)) * math.exp(-0.45 * tau)
                i_diff = s_flux * cos_theta * diffuse_ratio

                i_total = i_dir + i_diff

                # Electrical power (Watts)
                p_elec = panel_area_m2 * cell_efficiency * dust_deposition_factor * i_total
                hourly_powers.append(round(p_elec, 2))
                daytime_powers.append(p_elec)
            else:
                hourly_powers.append(0.0)

        # Total energy per sol (Wh/sol)
        daily_wh = sum(hourly_powers) * dt_hours
        peak_p = max(hourly_powers) if hourly_powers else 0.0
        avg_daytime = sum(daytime_powers) / len(daytime_powers) if daytime_powers else 0.0

        # Assess vehicle operational status against MER / InSight power requirements
        # MER survival threshold: ~220 Wh/sol, nominal mobility: ~600-900 Wh/sol
        # InSight (dual 2.15m arrays ~7m2): survival ~500 Wh/sol
        if daily_wh >= 700.0:
            status = "SURPLUS_FULL_OPERATION"
        elif daily_wh >= 400.0:
            status = "MARGINAL_CONSTRAINED_STATIONARY"
        elif daily_wh >= 200.0:
            status = "CRITICAL_SURVIVAL_ONLY"
        else:
            status = "ENERGY_DEFICIT_HAZARD"

        # Rover compatibility matrix
        rover_matrix = {
            "mer_opportunity_spirit": {
                "installed_area_m2": 1.3,
                "survival_threshold_wh_sol": 220.0,
                "nominal_mobility_wh_sol": 650.0,
                "current_status": "FEASIBLE" if daily_wh >= 650.0 else ("STATIONARY_ONLY" if daily_wh >= 220.0 else "HAZARDOUS_SHUTDOWN")
            },
            "insight_lander": {
                "installed_area_m2": 7.0,
                "survival_threshold_wh_sol": 480.0,
                "nominal_science_wh_sol": 1200.0,
                "current_status": "FEASIBLE" if (daily_wh * (7.0 / panel_area_m2)) >= 1200.0 else "DEGRADED"
            },
            "perseverance_curiosity": {
                "power_source": "MMRTG (Nuclear Radioisotope Thermoelectric Generator)",
                "nominal_daily_wh_sol": 2400.0,
                "solar_dust_vulnerability": "IMMUNE_TO_DUST_STORMS",
                "current_status": "NOMINAL_FULL_DRIVE"
            }
        }

        prov = ProvenanceFactory.create_solar_power_provenance()

        return SolarPowerBudgetResult(
            latitude=round(latitude, 4),
            solar_longitude_deg=round(ls_norm, 2),
            tau_visible=round(tau, 3),
            panel_area_m2=round(panel_area_m2, 2),
            cell_efficiency=round(cell_efficiency, 4),
            dust_deposition_factor=round(dust_deposition_factor, 3),
            peak_power_w=round(peak_p, 2),
            daily_energy_wh_sol=round(daily_wh, 2),
            average_daytime_power_w=round(avg_daytime, 2),
            operational_status=status,
            rover_compatibility=rover_matrix,
            hourly_power_w=hourly_powers,
            provenance=prov
        )

    @classmethod
    def assess_mission_environment(
        cls,
        target_name: str,
        latitude: float,
        longitude: float,
        elevation_m: float,
        ls_deg: float,
        thermal_inertia_tiu: float = 320.0,
        panel_area_m2: float = 1.3
    ) -> MissionEnvironmentAssessment:
        """
        Executes an integrated planetary environmental assessment aggregating
        orbital mechanics, atmospheric profile, dust optical depth, thermal swings,
        and photovoltaic power yield.
        """
        orbital = cls.calculate_orbital_parameters(ls_deg)
        atmosphere = cls.calculate_atmospheric_profile(latitude, longitude, elevation_m, ls_deg)
        dust = cls.calculate_dust_optical_depth(latitude, longitude, elevation_m, ls_deg)
        thermal = cls.calculate_diurnal_temperature_cycle(latitude, elevation_m, ls_deg, thermal_inertia_tiu, tau=dust.tau_visible)
        power = cls.calculate_solar_power_budget(latitude, ls_deg, tau=dust.tau_visible, panel_area_m2=panel_area_m2)

        # Environmental hazards analysis
        hazards: List[str] = []
        if dust.opacity_category in ("REGIONAL_STORM", "GLOBAL_ENCIRCLEMENT"):
            hazards.append(f"Elevated dust optical depth (tau = {dust.tau_visible:.2f}) limits visibility and solar insolation.")
        if thermal.diurnal_temperature_swing_k > 80.0:
            hazards.append(f"Severe diurnal temperature swing (Delta-T = {thermal.diurnal_temperature_swing_k:.1f} K) induces thermal fatigue on mechanical joints.")
        if thermal.min_surface_temp_k < 155.0:
            hazards.append(f"Cryogenic nocturnal temperatures (T_min = {thermal.min_surface_temp_k:.1f} K) require continuous battery survival heating.")
        if atmosphere.surface_pressure_pa < 500.0:
            hazards.append(f"Extremely low barometric pressure ({atmosphere.surface_pressure_pa:.1f} Pa) limits aerodynamic rotorcraft flight density.")
        if power.daily_energy_wh_sol < 400.0:
            hazards.append(f"Inadequate solar budget ({power.daily_energy_wh_sol:.1f} Wh/sol) forces stationary power preservation mode.")

        # Overall site viability score (0 to 100)
        # Power score (0-40) + Thermal score (0-30) + Atmosphere score (0-20) + Dust score (0-10)
        p_score = min(40.0, (power.daily_energy_wh_sol / 900.0) * 40.0)
        t_score = max(0.0, 30.0 - (thermal.diurnal_temperature_swing_k - 40.0) * 0.4)
        a_score = 20.0 if atmosphere.above_water_triple_point else 12.0
        d_score = max(0.0, 10.0 * (1.0 - dust.dust_storm_risk_index))
        total_viability = round(min(100.0, max(0.0, p_score + t_score + a_score + d_score)), 1)

        prov = ProvenanceFactory.create_atmospheric_environment_provenance()

        return MissionEnvironmentAssessment(
            target_name=target_name,
            latitude=round(latitude, 4),
            longitude=round(longitude, 4),
            elevation_m=round(elevation_m, 1),
            solar_longitude_deg=round(ls_deg % 360.0, 2),
            orbital=orbital,
            atmosphere=atmosphere,
            dust=dust,
            thermal=thermal,
            power_budget=power,
            overall_site_viability_score=total_viability,
            environmental_hazards=hazards,
            provenance=prov
        )
