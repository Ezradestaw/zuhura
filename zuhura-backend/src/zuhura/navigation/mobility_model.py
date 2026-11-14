"""
Rover mobility model and traverse simulation.
Implements terramechanics (Bekker-Wong theory), soil shearing, wheel sinkage,
slip ratio, rolling resistance, multi-rover specifications, diurnal thermal & insolation,
communications relay windows, mission timelines, and multi-criteria traverse risk analysis.

References:
- Bekker, M. G. (1969). Introduction to Terrain-Vehicle Systems. University of Michigan Press.
- Wong, J. Y. (2008). Theory of Ground Vehicles (4th ed.). John Wiley & Sons.
- Arvidson, R. E., et al. (2017). Mars Science Laboratory Curiosity rover traverse and science results. JGR Planets.
- Heverly, M., et al. (2013). Traverse performance of the Mars Science Laboratory rover. Journal of Field Robotics.
- Crisp, J. A., et al. (2003). Mars Exploration Rover mission. JGR Planets.
- Li, C., et al. (2022). The Zhurong rover's sub-surface exploration on Mars. Nature.
"""

import math
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

from zuhura.geodesy.constants import MARS_SURFACE_GRAVITY_M_S2


class VehicleMobilitySpecs(BaseModel):
    profile_id: str
    name: str
    mass_kg: float
    wheel_diameter_m: float
    number_of_wheels: int
    power_source: str  # "mmrtg", "solar_pv", "fuel_cell", "battery"
    nominal_power_w: float
    max_safe_slope_deg: float
    critical_rollover_slope_deg: float
    max_step_obstacle_m: float
    nominal_speed_km_h: float
    drive_motor_efficiency: float = 0.65
    avionics_power_w: float = 85.0
    rolling_resistance_coeff: float = 0.08  # Typical Martian loose regolith
    ground_clearance_m: float = 0.35
    wheel_width_m: float = 0.16
    battery_capacity_wh: float = 800.0
    science_payload_power_w: float = 40.0
    survival_heater_power_w: float = 20.0
    dust_sensitivity_factor: float = 1.0
    max_daily_drive_hours: float = 4.0


class RegolithProperties(BaseModel):
    regolith_id: str
    name: str
    description: str
    cohesion_kpa: float  # c
    internal_friction_deg: float  # phi
    sinkage_modulus_kc: float  # k_c (kN/m^(n+1))
    sinkage_modulus_kphi: float  # k_phi (kN/m^(n+2))
    sinkage_exponent_n: float  # n
    shear_deformation_modulus_k_cm: float = 1.8  # Janosi-Hanamoto K
    typical_rolling_resistance: float = 0.08


REGOLITH_DATABASE: Dict[str, RegolithProperties] = {
    "basaltic_sand": RegolithProperties(
        regolith_id="basaltic_sand",
        name="Basaltic Sand & Fine Regolith",
        description="Pervasive aeolian basaltic sand drifts; moderate bearing capacity and friction.",
        cohesion_kpa=0.2,
        internal_friction_deg=35.0,
        sinkage_modulus_kc=0.5,
        sinkage_modulus_kphi=1800.0,
        sinkage_exponent_n=1.0,
        shear_deformation_modulus_k_cm=1.8,
        typical_rolling_resistance=0.08
    ),
    "compact_dust": RegolithProperties(
        regolith_id="compact_dust",
        name="Compacted Surface Dust / Silt",
        description="Fine atmospheric fallout deposit over low-relief plains with slight cohesive crusting.",
        cohesion_kpa=1.0,
        internal_friction_deg=28.0,
        sinkage_modulus_kc=0.9,
        sinkage_modulus_kphi=1520.0,
        sinkage_exponent_n=1.0,
        shear_deformation_modulus_k_cm=2.5,
        typical_rolling_resistance=0.07
    ),
    "duricrust": RegolithProperties(
        regolith_id="duricrust",
        name="Cemented Sulfate Duricrust",
        description="Brittle cemented regolith crust; low sinkage until fracture threshold.",
        cohesion_kpa=4.5,
        internal_friction_deg=38.0,
        sinkage_modulus_kc=3.2,
        sinkage_modulus_kphi=3500.0,
        sinkage_exponent_n=1.1,
        shear_deformation_modulus_k_cm=1.0,
        typical_rolling_resistance=0.05
    ),
    "bedrock": RegolithProperties(
        regolith_id="bedrock",
        name="Competent Basaltic Bedrock",
        description="Exposed basalt and impact melt; negligible sinkage, high traction, minimal slip.",
        cohesion_kpa=50.0,
        internal_friction_deg=45.0,
        sinkage_modulus_kc=100.0,
        sinkage_modulus_kphi=50000.0,
        sinkage_exponent_n=1.2,
        shear_deformation_modulus_k_cm=0.5,
        typical_rolling_resistance=0.03
    ),
    "dune_fields": RegolithProperties(
        regolith_id="dune_fields",
        name="Active Aeolian Dune Fields (TARs)",
        description="Transverse Aeolian Ridges (TARs) and active ripples; severe wheel sinkage and entrapment hazard.",
        cohesion_kpa=0.05,
        internal_friction_deg=26.0,
        sinkage_modulus_kc=0.05,
        sinkage_modulus_kphi=400.0,
        sinkage_exponent_n=1.0,
        shear_deformation_modulus_k_cm=3.2,
        typical_rolling_resistance=0.14
    )
}


ROVER_SPECIFICATIONS: Dict[str, VehicleMobilitySpecs] = {
    "rover_perseverance": VehicleMobilitySpecs(
        profile_id="rover_perseverance",
        name="Mars 2020 Perseverance Rover (MMRTG Powered)",
        mass_kg=1025.0,
        wheel_diameter_m=0.526,
        number_of_wheels=6,
        power_source="mmrtg",
        nominal_power_w=110.0,
        max_safe_slope_deg=18.0,
        critical_rollover_slope_deg=30.0,
        max_step_obstacle_m=0.40,
        nominal_speed_km_h=0.12,
        drive_motor_efficiency=0.68,
        avionics_power_w=95.0,
        rolling_resistance_coeff=0.075,
        ground_clearance_m=0.40,
        wheel_width_m=0.16,
        battery_capacity_wh=860.0,
        science_payload_power_w=45.0,
        survival_heater_power_w=18.0,
        dust_sensitivity_factor=0.05,
        max_daily_drive_hours=4.0
    ),
    "rover_curiosity": VehicleMobilitySpecs(
        profile_id="rover_curiosity",
        name="MSL Curiosity Rover (MMRTG Powered)",
        mass_kg=899.0,
        wheel_diameter_m=0.50,
        number_of_wheels=6,
        power_source="mmrtg",
        nominal_power_w=110.0,
        max_safe_slope_deg=20.0,
        critical_rollover_slope_deg=32.0,
        max_step_obstacle_m=0.45,
        nominal_speed_km_h=0.14,
        drive_motor_efficiency=0.65,
        avionics_power_w=90.0,
        rolling_resistance_coeff=0.080,
        ground_clearance_m=0.45,
        wheel_width_m=0.16,
        battery_capacity_wh=860.0,
        science_payload_power_w=40.0,
        survival_heater_power_w=18.0,
        dust_sensitivity_factor=0.05,
        max_daily_drive_hours=4.0
    ),
    "rover_opportunity": VehicleMobilitySpecs(
        profile_id="rover_opportunity",
        name="MER-B Opportunity Rover (Solar PV Powered)",
        mass_kg=185.0,
        wheel_diameter_m=0.25,
        number_of_wheels=6,
        power_source="solar_pv",
        nominal_power_w=140.0,
        max_safe_slope_deg=15.0,
        critical_rollover_slope_deg=25.0,
        max_step_obstacle_m=0.25,
        nominal_speed_km_h=0.05,
        drive_motor_efficiency=0.60,
        avionics_power_w=40.0,
        rolling_resistance_coeff=0.085,
        ground_clearance_m=0.30,
        wheel_width_m=0.10,
        battery_capacity_wh=320.0,
        science_payload_power_w=20.0,
        survival_heater_power_w=25.0,
        dust_sensitivity_factor=1.40,
        max_daily_drive_hours=3.0
    ),
    "rover_spirit": VehicleMobilitySpecs(
        profile_id="rover_spirit",
        name="MER-A Spirit Rover (Degraded Wheel Drive)",
        mass_kg=185.0,
        wheel_diameter_m=0.25,
        number_of_wheels=6,
        power_source="solar_pv",
        nominal_power_w=140.0,
        max_safe_slope_deg=14.0,
        critical_rollover_slope_deg=24.0,
        max_step_obstacle_m=0.22,
        nominal_speed_km_h=0.04,
        drive_motor_efficiency=0.48,  # Degraded due to seized right-front wheel
        avionics_power_w=42.0,
        rolling_resistance_coeff=0.110,  # Wheel drag penalty
        ground_clearance_m=0.28,
        wheel_width_m=0.10,
        battery_capacity_wh=300.0,
        science_payload_power_w=20.0,
        survival_heater_power_w=25.0,
        dust_sensitivity_factor=1.50,
        max_daily_drive_hours=2.5
    ),
    "rover_zhurong": VehicleMobilitySpecs(
        profile_id="rover_zhurong",
        name="Tianwen-1 Zhurong Rover (Solar Active Suspension)",
        mass_kg=240.0,
        wheel_diameter_m=0.20,
        number_of_wheels=6,
        power_source="solar_pv",
        nominal_power_w=200.0,
        max_safe_slope_deg=20.0,
        critical_rollover_slope_deg=30.0,
        max_step_obstacle_m=0.30,
        nominal_speed_km_h=0.10,
        drive_motor_efficiency=0.70,
        avionics_power_w=50.0,
        rolling_resistance_coeff=0.075,
        ground_clearance_m=0.35,
        wheel_width_m=0.12,
        battery_capacity_wh=480.0,
        science_payload_power_w=30.0,
        survival_heater_power_w=22.0,
        dust_sensitivity_factor=1.10,
        max_daily_drive_hours=3.5
    ),
    "rover_exomars": VehicleMobilitySpecs(
        profile_id="rover_exomars",
        name="ExoMars Rosalind Franklin Rover (Wheel-Walking)",
        mass_kg=310.0,
        wheel_diameter_m=0.285,
        number_of_wheels=6,
        power_source="solar_pv",
        nominal_power_w=250.0,
        max_safe_slope_deg=25.0,
        critical_rollover_slope_deg=35.0,
        max_step_obstacle_m=0.40,
        nominal_speed_km_h=0.10,
        drive_motor_efficiency=0.72,
        avionics_power_w=65.0,
        rolling_resistance_coeff=0.070,
        ground_clearance_m=0.40,
        wheel_width_m=0.14,
        battery_capacity_wh=640.0,
        science_payload_power_w=80.0,  # Subsurface 2m drill load
        survival_heater_power_w=20.0,
        dust_sensitivity_factor=1.00,
        max_daily_drive_hours=4.0
    ),
    "crew_traverser": VehicleMobilitySpecs(
        profile_id="crew_traverser",
        name="Pressurized Crew Exploration Rover",
        mass_kg=3500.0,
        wheel_diameter_m=1.20,
        number_of_wheels=6,
        power_source="fuel_cell",
        nominal_power_w=5000.0,
        max_safe_slope_deg=14.0,
        critical_rollover_slope_deg=22.0,
        max_step_obstacle_m=0.60,
        nominal_speed_km_h=8.0,
        drive_motor_efficiency=0.82,
        avionics_power_w=1200.0,
        rolling_resistance_coeff=0.060,
        ground_clearance_m=0.60,
        wheel_width_m=0.35,
        battery_capacity_wh=45000.0,
        science_payload_power_w=500.0,
        survival_heater_power_w=250.0,
        dust_sensitivity_factor=0.10,
        max_daily_drive_hours=6.0
    ),
    "scout_hexacopter": VehicleMobilitySpecs(
        profile_id="scout_hexacopter",
        name="Autonomous Aerial Scout (Ingenuity Class)",
        mass_kg=2.4,
        wheel_diameter_m=0.0,
        number_of_wheels=0,
        power_source="battery",
        nominal_power_w=350.0,
        max_safe_slope_deg=45.0,
        critical_rollover_slope_deg=75.0,
        max_step_obstacle_m=10.0,
        nominal_speed_km_h=18.0,
        drive_motor_efficiency=0.75,
        avionics_power_w=20.0,
        rolling_resistance_coeff=0.0,
        ground_clearance_m=2.0,
        wheel_width_m=0.0,
        battery_capacity_wh=45.0,
        science_payload_power_w=10.0,
        survival_heater_power_w=8.0,
        dust_sensitivity_factor=0.30,
        max_daily_drive_hours=0.5
    )
}


class TerramechanicsMetrics(BaseModel):
    estimated_wheel_slip_pct: float
    traction_ratio: float
    sinkage_depth_cm: float
    soil_shear_risk: str  # "LOW", "MODERATE", "CRITICAL"
    bekker_motion_resistance_n: float = 0.0
    tractive_effort_n: float = 0.0
    entrapment_risk_pct: float = 0.0
    regolith_type_used: str = "basaltic_sand"


class EnergyConsumptionMetrics(BaseModel):
    mechanical_drive_energy_wh: float
    avionics_energy_wh: float
    total_energy_wh: float
    energy_rate_wh_per_km: float
    solar_insolation_mean_w_m2: float
    solar_energy_available_wh: float
    battery_net_delta_wh: float = 0.0
    survival_heater_energy_wh: float = 0.0


class CommunicationPass(BaseModel):
    target: str  # "MRO", "ODYSSEY", "TGO", "DTE_GOLDSTONE", "DTE_MADRID", "DTE_CANBERRA"
    pass_type: str  # "ORBITER_RELAY", "DIRECT_TO_EARTH"
    start_time_lmst: str
    end_time_lmst: str
    duration_minutes: float
    max_elevation_deg: float
    data_capacity_mbit: float
    frequency_band: str  # "UHF", "X-Band"


class SolTimelineEvent(BaseModel):
    time_window_lmst: str
    phase_name: str
    description: str
    power_draw_w: float
    is_comm_active: bool = False


class DailySolSchedule(BaseModel):
    sol_number: int
    drive_distance_m: float
    drive_duration_hours: float
    daily_energy_consumed_wh: float
    daily_solar_generated_wh: float
    net_battery_state_wh: float
    communication_passes: List[CommunicationPass]
    events: List[SolTimelineEvent]


class TraverseRiskAnalysis(BaseModel):
    tipping_risk: float = Field(ge=0.0, le=100.0)
    high_centering_risk: float = Field(ge=0.0, le=100.0)
    sinkage_entrapment_risk: float = Field(ge=0.0, le=100.0)
    thermal_deficit_risk: float = Field(ge=0.0, le=100.0)
    comm_blackout_risk: float = Field(ge=0.0, le=100.0)
    composite_risk: float = Field(ge=0.0, le=100.0)
    risk_rating: str  # "BENIGN", "ELEVATED", "HAZARDOUS", "PROHIBITIVE"


class RouteFeasibilityReport(BaseModel):
    geometric_feasible: bool = Field(description="Slope < critical rollover threshold & obstacle height passable")
    engineering_feasible: bool = Field(description="Wheel slip < 45% & soil traction sufficient")
    energy_feasible: bool = Field(description="Onboard power system can supply total required Watt-hours")
    mission_feasible: bool = Field(description="All operational and safety constraints satisfied")
    limiting_factor: Optional[str] = None


class RoverComparisonItem(BaseModel):
    rover_id: str
    name: str
    power_source: str
    mass_kg: float
    total_sols_required: float
    total_energy_wh: float
    energy_rate_wh_per_km: float
    max_wheel_slip_pct: float
    mean_sinkage_cm: float
    tipping_risk: float
    sinkage_risk: float
    high_centering_risk: float
    thermal_risk: float
    composite_risk: float
    risk_rating: str
    feasibility: RouteFeasibilityReport
    recommendation: str  # "RECOMMENDED", "VIABLE_WITH_CAUTION", "HIGH_RISK", "UNFEASIBLE"


class AdvancedMobilityAssessment(BaseModel):
    vehicle_profile: VehicleMobilitySpecs
    terramechanics: TerramechanicsMetrics
    energy: EnergyConsumptionMetrics
    feasibility: RouteFeasibilityReport
    risks: TraverseRiskAnalysis
    hazard_score: float = Field(ge=0.0, le=100.0, description="Composite terrain hazard score [0=Benign, 100=Impassable]")
    confidence_level_pct: float = Field(ge=0.0, le=100.0)
    estimated_duration_sols: float
    sample_sol_schedule: Optional[DailySolSchedule] = None


# --- Physical Calculation Engines ---

def get_regolith_properties(soil_type: str) -> RegolithProperties:
    """Returns regolith geotechnical parameters, falling back to basaltic_sand."""
    return REGOLITH_DATABASE.get(soil_type, REGOLITH_DATABASE["basaltic_sand"])


def assess_terramechanics(
    slope_deg: float,
    roughness_tri: float,
    vehicle: VehicleMobilitySpecs,
    soil_type: str = "basaltic_sand"
) -> TerramechanicsMetrics:
    """
    Computes Bekker-Wong terramechanics metrics for Martian regolith.
    Preserves exact backward compatibility with existing tests.
    """
    soil = get_regolith_properties(soil_type)

    if vehicle.profile_id == "scout_hexacopter":
        return TerramechanicsMetrics(
            estimated_wheel_slip_pct=0.0,
            traction_ratio=1.0,
            sinkage_depth_cm=0.0,
            soil_shear_risk="LOW",
            bekker_motion_resistance_n=0.0,
            tractive_effort_n=0.0,
            entrapment_risk_pct=0.0,
            regolith_type_used=soil.regolith_id
        )

    # 1. Slip Estimation based on terrain slope vs soil internal friction angle
    friction_angle_deg = soil.internal_friction_deg
    ratio = min(0.95, slope_deg / max(10.0, friction_angle_deg))
    base_slip = 5.0 + 85.0 * (ratio ** 2.8)

    # Regolith-specific modifier
    if soil.regolith_id == "dune_fields":
        base_slip = min(98.0, base_slip * 1.55 + 8.0)
    elif soil.regolith_id == "bedrock":
        base_slip = min(8.0, base_slip * 0.15 + 1.0)

    # Roughness contributes additional intermittent slip
    roughness_penalty = min(20.0, roughness_tri * 1.5)
    total_slip = min(99.0, max(2.0, base_slip + roughness_penalty))

    # 2. Traction ratio (gross pull to weight ratio)
    traction = max(0.05, math.cos(math.radians(slope_deg)) * (1.0 - total_slip / 100.0))

    # 3. Bekker Pressure-Sinkage Theory
    # Wheel contact patch geometry: z = (p / (k_c/b + k_phi))^(1/n)
    g = MARS_SURFACE_GRAVITY_M_S2
    w_normal_n = (vehicle.mass_kg * g * math.cos(math.radians(slope_deg))) / max(1, vehicle.number_of_wheels)
    b_m = max(0.05, vehicle.wheel_width_m)
    d_m = max(0.15, vehicle.wheel_diameter_m)

    # Iterative pressure-sinkage estimate
    denom = max(10.0, (soil.sinkage_modulus_kc / b_m) + soil.sinkage_modulus_kphi)
    # Estimate ground pressure with initial sinkage guess 2 cm
    contact_length_m = math.sqrt(max(0.001, d_m * 0.02))
    p_kpa = (w_normal_n / (b_m * contact_length_m)) / 1000.0
    sinkage_m = max(0.002, (max(0.1, p_kpa) / denom) ** (1.0 / max(0.4, soil.sinkage_exponent_n)))
    sinkage_cm = round(min(25.0, sinkage_m * 100.0 * (1.0 + total_slip / 80.0)), 1)

    # Bedrock hard stop
    if soil.regolith_id == "bedrock":
        sinkage_cm = 0.2

    # Motion resistance via Bekker equation: R_c = (b / (n+1)) * (k_c/b + k_phi) * z^(n+1)
    motion_res_n = (b_m / (soil.sinkage_exponent_n + 1.0)) * denom * 1000.0 * ((sinkage_cm / 100.0) ** (soil.sinkage_exponent_n + 1.0))
    motion_res_total_n = round(motion_res_n * vehicle.number_of_wheels, 1)

    # Maximum gross soil thrust: H = A_c * c + W * tan(phi)
    contact_area_total_m2 = vehicle.number_of_wheels * b_m * math.sqrt(max(0.001, d_m * (sinkage_cm / 100.0)))
    cohesion_n = contact_area_total_m2 * soil.cohesion_kpa * 1000.0
    friction_thrust_n = vehicle.mass_kg * g * math.cos(math.radians(slope_deg)) * math.tan(math.radians(soil.internal_friction_deg))
    total_thrust_n = round(cohesion_n + friction_thrust_n, 1)

    # Entrapment risk index [0 to 100]
    wheel_radius_cm = (vehicle.wheel_diameter_m * 100.0) / 2.0
    sinkage_ratio = sinkage_cm / max(5.0, wheel_radius_cm)
    entrapment_risk = min(100.0, max(0.0, (sinkage_ratio / 0.40) * 50.0 + (total_slip / 45.0) * 50.0))

    if total_slip < 25.0:
        risk = "LOW"
    elif total_slip < 45.0:
        risk = "MODERATE"
    else:
        risk = "CRITICAL"

    return TerramechanicsMetrics(
        estimated_wheel_slip_pct=round(total_slip, 1),
        traction_ratio=round(traction, 3),
        sinkage_depth_cm=round(sinkage_cm, 1),
        soil_shear_risk=risk,
        bekker_motion_resistance_n=motion_res_total_n,
        tractive_effort_n=total_thrust_n,
        entrapment_risk_pct=round(entrapment_risk, 1),
        regolith_type_used=soil.regolith_id
    )


def compute_diurnal_insolation(
    lat_deg: float,
    ls_deg: float = 180.0,
    dust_tau: float = 0.5,
    local_hour_lmst: float = 12.0
) -> Tuple[float, float]:
    """
    Computes solar insolation (W/m^2) and surface temperature (K) for given Martian sol conditions.
    """
    # 1. Heliocentric distance r (AU) accounting for Mars orbital eccentricity e=0.0934
    e = 0.0934
    omega_p = 250.0  # Longitude of perihelion
    r_au = (1.524 * (1.0 - e**2)) / (1.0 + e * math.cos(math.radians(ls_deg - omega_p)))

    # Solar constant at Mars distance
    s_mars = 1361.0 / (r_au ** 2)

    # Solar declination
    obliquity_deg = 25.19
    sin_delta = math.sin(math.radians(obliquity_deg)) * math.sin(math.radians(ls_deg))
    delta_rad = math.asin(sin_delta)

    # Hour angle
    h_rad = math.radians((local_hour_lmst - 12.0) * 15.0)
    lat_rad = math.radians(lat_deg)

    # Solar elevation angle alpha
    sin_alpha = math.sin(lat_rad) * math.sin(delta_rad) + math.cos(lat_rad) * math.cos(delta_rad) * math.cos(h_rad)

    if sin_alpha <= 0.0:
        # Nighttime
        t_surf_k = 175.0 + 15.0 * math.cos(math.radians(lat_deg))
        return 0.0, round(t_surf_k, 1)

    alpha_deg = math.degrees(math.asin(sin_alpha))
    zenith_rad = math.radians(90.0 - alpha_deg)

    # Direct beam attenuation via Beer-Lambert
    airmass = 1.0 / max(0.1, math.cos(zenith_rad))
    direct_flux = s_mars * math.cos(zenith_rad) * math.exp(-dust_tau * airmass)
    diffuse_flux = 0.18 * s_mars * math.cos(zenith_rad) * (1.0 - math.exp(-dust_tau * airmass))
    total_insolation = max(0.0, direct_flux + diffuse_flux)

    # Temperature model
    t_min_k = 175.0
    t_max_k = 265.0 - abs(lat_deg) * 0.8
    t_surf_k = t_min_k + (t_max_k - t_min_k) * (sin_alpha ** 0.8)

    return round(total_insolation, 1), round(t_surf_k, 1)


def compute_energy_consumption(
    distance_km: float,
    elevation_gain_m: float,
    mean_slope_deg: float,
    duration_hours: float,
    vehicle: VehicleMobilitySpecs,
    solar_elevation_deg: float = 45.0,
    lat_deg: float = 18.0,
    ls_deg: float = 180.0,
    dust_tau: float = 0.5
) -> EnergyConsumptionMetrics:
    """
    Computes total electrical energy expenditure over Martian terrain,
    integrating rolling resistance, gravity potential, avionics, science payload,
    and diurnal survival heating requirements.
    """
    g = MARS_SURFACE_GRAVITY_M_S2
    dist_m = distance_km * 1000.0

    if vehicle.profile_id == "scout_hexacopter":
        flight_power_w = 320.0
        mech_wh = flight_power_w * duration_hours
        avionics_wh = vehicle.avionics_power_w * duration_hours
        total_wh = mech_wh + avionics_wh
        rate = total_wh / max(0.01, distance_km)
        return EnergyConsumptionMetrics(
            mechanical_drive_energy_wh=round(mech_wh, 2),
            avionics_energy_wh=round(avionics_wh, 2),
            total_energy_wh=round(total_wh, 2),
            energy_rate_wh_per_km=round(rate, 2),
            solar_insolation_mean_w_m2=590.0,
            solar_energy_available_wh=35.0,
            battery_net_delta_wh=-round(total_wh, 2),
            survival_heater_energy_wh=8.0
        )

    # 1. Rolling resistance work
    w_roll_joules = vehicle.rolling_resistance_coeff * vehicle.mass_kg * g * math.cos(math.radians(mean_slope_deg)) * dist_m

    # 2. Gravitational potential work for uphill climbing
    w_climb_joules = max(0.0, vehicle.mass_kg * g * elevation_gain_m)

    total_mech_joules = (w_roll_joules + w_climb_joules) / max(0.1, vehicle.drive_motor_efficiency)
    mech_wh = total_mech_joules / 3600.0

    # 3. Avionics and science payload power
    avionics_wh = vehicle.avionics_power_w * duration_hours
    science_wh = vehicle.science_payload_power_w * (duration_hours * 0.35)

    # 4. Thermal survival heaters
    _, t_surf = compute_diurnal_insolation(lat_deg=lat_deg, ls_deg=ls_deg, dust_tau=dust_tau, local_hour_lmst=12.0)
    survival_heater_wh = 0.0
    if t_surf < 233.15:  # Below -40 deg C
        heater_hours = max(2.0, 24.66 - duration_hours)
        survival_heater_wh = vehicle.survival_heater_power_w * heater_hours

    total_wh = mech_wh + avionics_wh + science_wh + survival_heater_wh
    rate = total_wh / max(0.01, distance_km)

    # 5. Solar generation
    mean_insolation, _ = compute_diurnal_insolation(lat_deg=lat_deg, ls_deg=ls_deg, dust_tau=dust_tau, local_hour_lmst=12.0)
    solar_wh = 0.0
    if vehicle.power_source == "solar_pv":
        panel_area_m2 = 1.3
        panel_eff = 0.22
        # Attenuation by dust factor
        eff_tau = max(0.2, math.exp(-dust_tau * vehicle.dust_sensitivity_factor))
        solar_wh = mean_insolation * panel_area_m2 * panel_eff * eff_tau * min(duration_hours, 6.0)
    elif vehicle.power_source == "mmrtg":
        # Continuous steady generation
        solar_wh = vehicle.nominal_power_w * 24.66  # ~2640 Wh per sol

    net_delta_wh = solar_wh - total_wh

    return EnergyConsumptionMetrics(
        mechanical_drive_energy_wh=round(mech_wh, 2),
        avionics_energy_wh=round(avionics_wh, 2),
        total_energy_wh=round(total_wh, 2),
        energy_rate_wh_per_km=round(rate, 2),
        solar_insolation_mean_w_m2=round(mean_insolation, 1),
        solar_energy_available_wh=round(solar_wh, 2),
        battery_net_delta_wh=round(net_delta_wh, 2),
        survival_heater_energy_wh=round(survival_heater_wh, 2)
    )


def calculate_comm_windows(lat_deg: float, lon_deg: float) -> List[CommunicationPass]:
    """
    Computes representative daily communications relay opportunities for Martian surface assets.
    """
    return [
        CommunicationPass(
            target="MRO",
            pass_type="ORBITER_RELAY",
            start_time_lmst="15:10",
            end_time_lmst="15:22",
            duration_minutes=12.0,
            max_elevation_deg=74.5,
            data_capacity_mbit=144.0,
            frequency_band="UHF (400 MHz Electra)"
        ),
        CommunicationPass(
            target="ODYSSEY",
            pass_type="ORBITER_RELAY",
            start_time_lmst="17:05",
            end_time_lmst="17:18",
            duration_minutes=13.0,
            max_elevation_deg=58.2,
            data_capacity_mbit=36.0,
            frequency_band="UHF (400 MHz CE505)"
        ),
        CommunicationPass(
            target="TGO",
            pass_type="ORBITER_RELAY",
            start_time_lmst="11:40",
            end_time_lmst="11:52",
            duration_minutes=12.0,
            max_elevation_deg=66.0,
            data_capacity_mbit=120.0,
            frequency_band="UHF (400 MHz Electra)"
        ),
        CommunicationPass(
            target="DTE_MADRID",
            pass_type="DIRECT_TO_EARTH",
            start_time_lmst="09:15",
            end_time_lmst="10:30",
            duration_minutes=75.0,
            max_elevation_deg=42.0,
            data_capacity_mbit=8.5,
            frequency_band="X-Band (7.1 GHz HGA)"
        ),
        CommunicationPass(
            target="DTE_GOLDSTONE",
            pass_type="DIRECT_TO_EARTH",
            start_time_lmst="16:45",
            end_time_lmst="18:00",
            duration_minutes=75.0,
            max_elevation_deg=38.5,
            data_capacity_mbit=8.5,
            frequency_band="X-Band (7.1 GHz HGA)"
        )
    ]


def generate_daily_schedule(
    sol_num: int,
    drive_distance_m: float,
    drive_duration_hours: float,
    vehicle: VehicleMobilitySpecs,
    energy_wh: float,
    lat_deg: float,
    lon_deg: float
) -> DailySolSchedule:
    """Generates a detailed operational sol timeline."""
    passes = calculate_comm_windows(lat_deg=lat_deg, lon_deg=lon_deg)
    
    events = [
        SolTimelineEvent(
            time_window_lmst="00:00 - 08:30",
            phase_name="NIGHT_SURVIVAL_SLEEP",
            description="Deep sleep mode; survival heaters active, avionics throttled to minimum trickle.",
            power_draw_w=vehicle.survival_heater_power_w,
            is_comm_active=False
        ),
        SolTimelineEvent(
            time_window_lmst="08:30 - 09:30",
            phase_name="WAKEUP_AND_DTE_UPLINK",
            description="Computer boot, direct-to-Earth X-band command upload from DSN, pre-drive instrument checks.",
            power_draw_w=vehicle.avionics_power_w + 35.0,
            is_comm_active=True
        ),
        SolTimelineEvent(
            time_window_lmst="09:30 - 13:30",
            phase_name="AUTONOMOUS_TRAVERSE_DRIVE",
            description=f"AutoNav drive segment covering {drive_distance_m:.1f} m along terrain corridor.",
            power_draw_w=vehicle.avionics_power_w + (energy_wh / max(0.5, drive_duration_hours)),
            is_comm_active=False
        ),
        SolTimelineEvent(
            time_window_lmst="13:30 - 15:00",
            phase_name="SCIENCE_STOP_TARGETING",
            description="Robotic arm contact science (APXS, DRILL, RAMAN) and panoramic multispectral imaging.",
            power_draw_w=vehicle.avionics_power_w + vehicle.science_payload_power_w,
            is_comm_active=False
        ),
        SolTimelineEvent(
            time_window_lmst="15:00 - 16:30",
            phase_name="ORBITER_RELAY_DOWNLINK",
            description="UHF Electra proximity link to Mars Reconnaissance Orbiter (MRO); mission data dump.",
            power_draw_w=vehicle.avionics_power_w + 45.0,
            is_comm_active=True
        ),
        SolTimelineEvent(
            time_window_lmst="16:30 - 24:00",
            phase_name="EVENING_SHUTDOWN_SLEEP",
            description="Data compaction, flash memory sync, rover transition to sleep state.",
            power_draw_w=vehicle.avionics_power_w * 0.2,
            is_comm_active=False
        )
    ]

    solar_gen_wh = 2640.0 if vehicle.power_source == "mmrtg" else 550.0

    return DailySolSchedule(
        sol_number=sol_num,
        drive_distance_m=round(drive_distance_m, 1),
        drive_duration_hours=round(drive_duration_hours, 2),
        daily_energy_consumed_wh=round(energy_wh, 1),
        daily_solar_generated_wh=round(solar_gen_wh, 1),
        net_battery_state_wh=round(vehicle.battery_capacity_wh * 0.85, 1),
        communication_passes=passes,
        events=events
    )


def evaluate_traverse_risks(
    max_slope_deg: float,
    mean_slope_deg: float,
    roughness_tri: float,
    terramechanics: TerramechanicsMetrics,
    energy: EnergyConsumptionMetrics,
    vehicle: VehicleMobilitySpecs
) -> TraverseRiskAnalysis:
    """Computes multidimensional mission risk indices [0 to 100]."""
    if vehicle.profile_id == "scout_hexacopter":
        tipping = min(100.0, (max_slope_deg / vehicle.critical_rollover_slope_deg) * 20.0)
        centering = 0.0
        sinkage = 0.0
        thermal = 15.0
        comm = 10.0
        composite = round(tipping * 0.4 + thermal * 0.3 + comm * 0.3, 1)
        rating = "BENIGN" if composite < 25.0 else ("ELEVATED" if composite < 50.0 else "HAZARDOUS")
        return TraverseRiskAnalysis(
            tipping_risk=round(tipping, 1),
            high_centering_risk=0.0,
            sinkage_entrapment_risk=0.0,
            thermal_deficit_risk=thermal,
            comm_blackout_risk=comm,
            composite_risk=composite,
            risk_rating=rating
        )

    # 1. Tipping Risk: slope relative to rollover envelope
    tipping = min(100.0, max(0.0, (max_slope_deg / vehicle.critical_rollover_slope_deg) * 100.0))

    # 2. High Centering Risk: terrain roughness and step obstacles vs ground clearance
    clearance_m = max(0.1, vehicle.ground_clearance_m)
    step_ratio = (roughness_tri * 0.05) / clearance_m
    centering = min(100.0, max(0.0, step_ratio * 75.0))

    # 3. Sinkage & Entrapment Risk: Bekker sinkage and slip
    wheel_radius_cm = (vehicle.wheel_diameter_m * 100.0) / 2.0
    sinkage_ratio = terramechanics.sinkage_depth_cm / max(5.0, wheel_radius_cm)
    sinkage_risk = min(100.0, max(0.0, (sinkage_ratio / 0.35) * 50.0 + (terramechanics.estimated_wheel_slip_pct / 45.0) * 50.0))

    # 4. Thermal & Energy Deficit Risk
    if vehicle.power_source == "mmrtg":
        thermal_risk = 5.0  # MMRTG is immune to dust & night
    elif vehicle.power_source == "fuel_cell":
        thermal_risk = 10.0
    else:
        # Solar PV is sensitive to dust tau and night heaters
        deficit_ratio = max(0.0, -energy.battery_net_delta_wh) / max(10.0, vehicle.battery_capacity_wh)
        thermal_risk = min(100.0, max(10.0, deficit_ratio * 80.0))

    # 5. Communication Blackout Risk (standard orbiter pass gap)
    comm_risk = 12.0

    # Composite weighted risk
    composite = round(
        0.30 * tipping +
        0.25 * sinkage_risk +
        0.20 * centering +
        0.15 * thermal_risk +
        0.10 * comm_risk,
        1
    )

    if composite < 25.0:
        rating = "BENIGN"
    elif composite < 50.0:
        rating = "ELEVATED"
    elif composite < 75.0:
        rating = "HAZARDOUS"
    else:
        rating = "PROHIBITIVE"

    return TraverseRiskAnalysis(
        tipping_risk=round(tipping, 1),
        high_centering_risk=round(centering, 1),
        sinkage_entrapment_risk=round(sinkage_risk, 1),
        thermal_deficit_risk=round(thermal_risk, 1),
        comm_blackout_risk=round(comm_risk, 1),
        composite_risk=composite,
        risk_rating=rating
    )


def evaluate_mobility_feasibility(
    max_slope_deg: float,
    terramechanics: TerramechanicsMetrics,
    energy: EnergyConsumptionMetrics,
    vehicle: VehicleMobilitySpecs,
    duration_sols: float
) -> RouteFeasibilityReport:
    """
    Evaluates 4 independent feasibility pillars.
    Preserves exact backward compatibility with existing tests.
    """
    geo_feasible = max_slope_deg < vehicle.critical_rollover_slope_deg
    eng_feasible = terramechanics.estimated_wheel_slip_pct < 45.0 and max_slope_deg <= vehicle.max_safe_slope_deg

    if vehicle.power_source == "mmrtg":
        energy_feasible = energy.total_energy_wh <= (2640.0 * max(1.0, duration_sols))
    elif vehicle.power_source == "battery":
        energy_feasible = energy.total_energy_wh <= 45.0
    elif vehicle.power_source == "solar_pv":
        energy_feasible = energy.solar_energy_available_wh >= (energy.total_energy_wh * 0.65)
    else:
        energy_feasible = True

    mission_feasible = geo_feasible and eng_feasible and energy_feasible

    limiting_factor = None
    if not geo_feasible:
        limiting_factor = f"Slope ({max_slope_deg:.1f}°) exceeds rollover stability limit ({vehicle.critical_rollover_slope_deg}°)"
    elif not eng_feasible:
        limiting_factor = f"Excessive soil slip ({terramechanics.estimated_wheel_slip_pct:.1f}%) or slope > safe drive limit ({vehicle.max_safe_slope_deg}°)"
    elif not energy_feasible:
        limiting_factor = f"Energy demand ({energy.total_energy_wh:.1f} Wh) exceeds available power storage for planned duration"

    return RouteFeasibilityReport(
        geometric_feasible=geo_feasible,
        engineering_feasible=eng_feasible,
        energy_feasible=energy_feasible,
        mission_feasible=mission_feasible,
        limiting_factor=limiting_factor
    )


def simulate_multi_rover_comparison(
    distance_km: float,
    elevation_gain_m: float,
    max_slope_deg: float,
    mean_slope_deg: float,
    roughness_tri: float,
    selected_rovers: Optional[List[str]] = None,
    soil_type: str = "basaltic_sand",
    ls_deg: float = 180.0,
    dust_tau: float = 0.5,
    lat_deg: float = 18.0
) -> List[RoverComparisonItem]:
    """
    Executes an identical traverse corridor through all requested rovers simultaneously,
    comparing terramechanics, energy, mission duration in sols, and risk envelopes.
    """
    rover_keys = selected_rovers or list(ROVER_SPECIFICATIONS.keys())
    results: List[RoverComparisonItem] = []

    for key in rover_keys:
        if key not in ROVER_SPECIFICATIONS:
            continue
        v = ROVER_SPECIFICATIONS[key]

        # Terramechanics
        terramech = assess_terramechanics(
            slope_deg=mean_slope_deg,
            roughness_tri=roughness_tri,
            vehicle=v,
            soil_type=soil_type
        )

        # Drive duration and sol estimation
        eff_speed = v.nominal_speed_km_h * max(0.1, 1.0 - (terramech.estimated_wheel_slip_pct / 100.0))
        drive_hours = distance_km / max(0.01, eff_speed)
        sols_required = max(1.0, math.ceil(drive_hours / max(0.5, v.max_daily_drive_hours)))

        # Energy calculation
        energy = compute_energy_consumption(
            distance_km=distance_km,
            elevation_gain_m=elevation_gain_m,
            mean_slope_deg=mean_slope_deg,
            duration_hours=drive_hours,
            vehicle=v,
            lat_deg=lat_deg,
            ls_deg=ls_deg,
            dust_tau=dust_tau
        )

        # Feasibility & Risk
        feasibility = evaluate_mobility_feasibility(
            max_slope_deg=max_slope_deg,
            terramechanics=terramech,
            energy=energy,
            vehicle=v,
            duration_sols=sols_required
        )

        risks = evaluate_traverse_risks(
            max_slope_deg=max_slope_deg,
            mean_slope_deg=mean_slope_deg,
            roughness_tri=roughness_tri,
            terramechanics=terramech,
            energy=energy,
            vehicle=v
        )

        # Recommendation verdict
        if not feasibility.mission_feasible or risks.composite_risk >= 75.0:
            rec = "UNFEASIBLE"
        elif risks.composite_risk >= 50.0:
            rec = "HIGH_RISK"
        elif risks.composite_risk >= 25.0:
            rec = "VIABLE_WITH_CAUTION"
        else:
            rec = "RECOMMENDED"

        results.append(RoverComparisonItem(
            rover_id=v.profile_id,
            name=v.name,
            power_source=v.power_source,
            mass_kg=v.mass_kg,
            total_sols_required=round(sols_required, 1),
            total_energy_wh=round(energy.total_energy_wh, 1),
            energy_rate_wh_per_km=round(energy.energy_rate_wh_per_km, 1),
            max_wheel_slip_pct=terramech.estimated_wheel_slip_pct,
            mean_sinkage_cm=terramech.sinkage_depth_cm,
            tipping_risk=risks.tipping_risk,
            sinkage_risk=risks.sinkage_entrapment_risk,
            high_centering_risk=risks.high_centering_risk,
            thermal_risk=risks.thermal_deficit_risk,
            composite_risk=risks.composite_risk,
            risk_rating=risks.risk_rating,
            feasibility=feasibility,
            recommendation=rec
        ))

    return results
