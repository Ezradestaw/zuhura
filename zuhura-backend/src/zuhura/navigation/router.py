"""
Terrain-aware route search (A*).
Performs geodetically sound, cost-distance A* pathfinding over Martian topography
using MOLA elevation, metric slope gradients, and vehicle mobility constraints.
"""

import math
import heapq
import logging
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

from zuhura.geodesy.transformations import (
    mars_surface_distance_km,
    normalize_east_longitude,
    MARS_A_EQUATORIAL_RADIUS_M,
)
from zuhura.terrain_intelligence.engine import TerrainIntelligenceEngine, get_terrain_engine
from zuhura.api.v1.spatial import estimate_mars_elevation
from zuhura.navigation.mobility_model import (
    ROVER_SPECIFICATIONS,
    assess_terramechanics,
    compute_energy_consumption,
    evaluate_mobility_feasibility,
    evaluate_traverse_risks,
    generate_daily_schedule,
    calculate_comm_windows,
    REGOLITH_DATABASE,
    simulate_multi_rover_comparison,
)
from zuhura.provenance.taxonomy import ProvenanceFactory

logger = logging.getLogger("zuhura.navigation.router")


class Waypoint(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=360.0)
    name: Optional[str] = None


class RouteSegment(BaseModel):
    segment_index: int
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    surface_distance_m: float
    elevation_start_m: float
    elevation_end_m: float
    elevation_delta_m: float
    slope_degrees: float
    is_hazard: bool
    traversability: str  # traversable, difficult, hazard, impassable


class RouteElevationPoint(BaseModel):
    distance_km: float
    latitude: float
    longitude: float
    elevation_m: float
    slope_degrees: float
    roughness_tri: float


class RouteOption(BaseModel):
    route_id: str
    name: str
    description: str
    total_distance_km: float
    direct_distance_km: float
    detour_factor: float
    elevation_gain_m: float
    elevation_loss_m: float
    min_elevation_m: float
    max_elevation_m: float
    max_slope_degrees: float
    mean_slope_degrees: float
    hazard_segments_count: int
    waypoints: List[RouteElevationPoint]
    segments: List[RouteSegment]
    geojson: Dict[str, Any]
    mobility_assessment: Optional[Dict[str, Any]] = None
    quality_metrics: Optional[Dict[str, Any]] = None


class RoutePlanningRequest(BaseModel):
    start: Waypoint
    destination: Waypoint
    intermediate_waypoints: Optional[List[Waypoint]] = Field(default_factory=list)
    mobility_profile: str = Field(
        default="rover_perseverance",
        description="Vehicle profile: rover_perseverance (18° max), rover_curiosity (20° max), crew_traverser (12° max), scout_hexacopter (45° max)"
    )
    preference: str = Field(
        default="balanced",
        description="Cost preference: 'balanced', 'minimum_slope', 'shortest_distance', 'maximum_safety'"
    )
    grid_resolution: int = Field(default=25, ge=10, le=50, description="Spatial pathfinding lattice resolution")


class RoutePlanningResponse(BaseModel):
    status: str
    recommended_route: RouteOption
    alternative_routes: List[RouteOption]
    mobility_profile: str
    cost_model_parameters: Dict[str, Any]
    scientific_provenance: Dict[str, Any]
    disclaimer: str = (
        "RESEARCH SIMULATION ONLY: This route was computed using orbital topographic models (MOLA/DEM). "
        "It is not guaranteed safe for real rover operations or human extravehicular activities. "
        "Sub-pixel boulders, sand dunes (ripples), and soft regolith are not resolved."
    )


MOBILITY_PROFILES = {
    "rover_perseverance": {
        "name": "Mars 2020 Perseverance Class Rover",
        "max_climbable_slope_deg": 18.0,
        "critical_slope_deg": 25.0,
        "slope_weight": 2.5,
        "roughness_weight": 1.5,
        "max_step_obstacle_m": 0.40,
        "power_source": "mmrtg",
        "nominal_speed_km_h": 0.12
    },
    "rover_curiosity": {
        "name": "MSL Curiosity Class Rover",
        "max_climbable_slope_deg": 20.0,
        "critical_slope_deg": 28.0,
        "slope_weight": 2.0,
        "roughness_weight": 1.8,
        "max_step_obstacle_m": 0.50,
        "power_source": "mmrtg",
        "nominal_speed_km_h": 0.14
    },
    "rover_opportunity": {
        "name": "MER-B Opportunity Rover",
        "max_climbable_slope_deg": 15.0,
        "critical_slope_deg": 25.0,
        "slope_weight": 3.0,
        "roughness_weight": 2.0,
        "max_step_obstacle_m": 0.25,
        "power_source": "solar_pv",
        "nominal_speed_km_h": 0.05
    },
    "rover_spirit": {
        "name": "MER-A Spirit Rover (Seized Wheel)",
        "max_climbable_slope_deg": 14.0,
        "critical_slope_deg": 24.0,
        "slope_weight": 3.5,
        "roughness_weight": 2.2,
        "max_step_obstacle_m": 0.22,
        "power_source": "solar_pv",
        "nominal_speed_km_h": 0.04
    },
    "rover_zhurong": {
        "name": "Tianwen-1 Zhurong Rover",
        "max_climbable_slope_deg": 20.0,
        "critical_slope_deg": 30.0,
        "slope_weight": 2.2,
        "roughness_weight": 1.6,
        "max_step_obstacle_m": 0.30,
        "power_source": "solar_pv",
        "nominal_speed_km_h": 0.10
    },
    "rover_exomars": {
        "name": "ExoMars Rosalind Franklin Rover",
        "max_climbable_slope_deg": 25.0,
        "critical_slope_deg": 35.0,
        "slope_weight": 1.8,
        "roughness_weight": 1.4,
        "max_step_obstacle_m": 0.40,
        "power_source": "solar_pv",
        "nominal_speed_km_h": 0.10
    },
    "crew_traverser": {
        "name": "Pressurized Crew Rover (Human Mission)",
        "max_climbable_slope_deg": 14.0,
        "critical_slope_deg": 20.0,
        "slope_weight": 4.0,
        "roughness_weight": 2.5,
        "max_step_obstacle_m": 0.60,
        "power_source": "fuel_cell",
        "nominal_speed_km_h": 8.0
    },
    "scout_hexacopter": {
        "name": "Autonomous Aerial Scout (Ingenuity-derived)",
        "max_climbable_slope_deg": 45.0,
        "critical_slope_deg": 60.0,
        "slope_weight": 0.5,
        "roughness_weight": 0.2,
        "max_step_obstacle_m": 5.0,
        "power_source": "battery",
        "nominal_speed_km_h": 18.0
    }
}


class NavigationRouter:
    def __init__(self, engine: Optional[TerrainIntelligenceEngine] = None):
        self.engine = engine or get_terrain_engine()

    def _sample_elevation(self, lat: float, lon: float) -> Tuple[float, float, float]:
        """Returns (elevation_m, slope_deg, roughness_tri)."""
        norm_lon = normalize_east_longitude(lon)
        try:
            pt = self.engine.analyze_point(lat, norm_lon, kernel_size=3)
            elev = pt["elevation"]["elevation_m"]
            slope = pt["derivatives"]["slope_deg"]
            roughness = pt.get("morphometry", {}).get("tri_roughness_m", 2.0)
            return float(elev), float(slope), float(roughness)
        except Exception as exc:
            # No DEM coverage here: fall back to the coarse elevation model.
            logger.debug("Terrain lookup failed at (%.4f, %.4f): %s", lat, norm_lon, exc)
            elev = estimate_mars_elevation(lat, norm_lon)
            return float(elev), 2.5, 1.0

    def calculate_routes(self, req: RoutePlanningRequest) -> RoutePlanningResponse:
        start_lat = req.start.latitude
        start_lon = normalize_east_longitude(req.start.longitude)
        end_lat = req.destination.latitude
        end_lon = normalize_east_longitude(req.destination.longitude)

        profile_key = req.mobility_profile if req.mobility_profile in MOBILITY_PROFILES else "rover_perseverance"
        profile_params = dict(MOBILITY_PROFILES[profile_key])
        profile_params["profile_key"] = profile_key
        max_slope_limit = profile_params["max_climbable_slope_deg"]

        direct_dist_km = mars_surface_distance_km(start_lat, start_lon, end_lat, end_lon)

        # 1. Generate pathfinding grid
        n_steps = max(15, min(req.grid_resolution, 40))
        n_lateral = 15  # lateral tracks across the corridor

        # Orthogonal lateral vector for corridor search
        d_lat = end_lat - start_lat
        d_lon = end_lon - start_lon
        # Half-width of the search corridor: wide enough to route around steep ground.
        corridor_width_deg = max(0.05, min(0.5 * math.sqrt(d_lat**2 + d_lon**2), 5.0))

        # Sample grid vertices
        grid_nodes: List[List[Dict[str, Any]]] = []
        for i in range(n_steps + 1):
            t = i / float(n_steps)
            mid_lat = start_lat + t * d_lat
            mid_lon = start_lon + t * d_lon

            # Normal vector in 2D lat-lon
            norm_factor = math.hypot(d_lat, d_lon) or 1.0
            p_lat = -d_lon / norm_factor
            p_lon = d_lat / norm_factor

            row = []
            for j in range(n_lateral):
                if i == 0 or i == n_steps:
                    # Pinch to exact start and end at terminals
                    lat = start_lat if i == 0 else end_lat
                    lon = start_lon if i == 0 else end_lon
                else:
                    offset = (j - (n_lateral - 1) / 2.0) / ((n_lateral - 1) / 2.0) * corridor_width_deg
                    lat = mid_lat + offset * p_lat
                    lon = mid_lon + offset * p_lon

                elev, slope, tri = self._sample_elevation(lat, lon)
                row.append({
                    "lat": lat,
                    "lon": lon,
                    "elev": elev,
                    "slope": slope,
                    "tri": tri,
                    "i": i,
                    "j": j
                })
            grid_nodes.append(row)

        # 2. Run A* for 2 routing preferences:
        # A) Safe / Low-Slope (prioritizes minimal slope and roughness)
        # B) Direct / Fastest (prioritizes shortest distance with standard safety)
        safe_path = self._astar_search(grid_nodes, profile_params, preference="minimum_slope")
        direct_path = self._astar_search(grid_nodes, profile_params, preference="shortest_distance")

        # Convert paths into structured RouteOptions
        recommended_opt = self._build_route_option(
            route_id="route_opt_recommended",
            name=f"Recommended Traverse ({profile_params['name']})",
            description=f"Terrain-optimized route balanced for safety, trafficability, and battery expenditure. Avoids slopes > {max_slope_limit}°.",
            nodes=safe_path if req.preference in ("balanced", "minimum_slope", "maximum_safety") else direct_path,
            direct_dist_km=direct_dist_km,
            profile_params=profile_params
        )

        alt_opt = self._build_route_option(
            route_id="route_opt_alternative",
            name="Direct Geodesic Alternative",
            description="Shortest corridor traverse. Incurs higher localized slope gradients and rougher boulder terrain.",
            nodes=direct_path if req.preference in ("balanced", "minimum_slope", "maximum_safety") else safe_path,
            direct_dist_km=direct_dist_km,
            profile_params=profile_params
        )

        return RoutePlanningResponse(
            status="success",
            recommended_route=recommended_opt,
            alternative_routes=[alt_opt],
            mobility_profile=profile_key,
            cost_model_parameters={
                "profile_name": profile_params["name"],
                "max_climbable_slope_deg": max_slope_limit,
                "critical_slope_deg": profile_params["critical_slope_deg"],
                "slope_weight": profile_params["slope_weight"],
                "roughness_weight": profile_params["roughness_weight"],
                "optimization_preference": req.preference,
                "geodetic_radius_m": MARS_A_EQUATORIAL_RADIUS_M
            },
            scientific_provenance=ProvenanceFactory.create_rover_simulation_provenance(profile_key).to_summary_dict()
        )

    def _astar_search(
        self,
        grid: List[List[Dict[str, Any]]],
        profile_params: Dict[str, Any],
        preference: str
    ) -> List[Dict[str, Any]]:
        n_rows = len(grid)
        n_cols = len(grid[0])

        # Start in the centre lane so the search can bend either way.
        start_node = (0, n_cols // 2)
        goal_node = (n_rows - 1, n_cols // 2)

        # Priority queue stores (f_score, i, j)
        open_set = []
        heapq.heappush(open_set, (0.0, start_node[0], start_node[1]))

        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        g_score = { (i, j): float("inf") for i in range(n_rows) for j in range(n_cols) }
        g_score[start_node] = 0.0

        target_lat = grid[goal_node[0]][goal_node[1]]["lat"]
        target_lon = grid[goal_node[0]][goal_node[1]]["lon"]

        while open_set:
            current_f, cur_i, cur_j = heapq.heappop(open_set)

            if cur_i == goal_node[0]:
                # Reconstruct path
                path = []
                curr = (cur_i, cur_j)
                while curr in came_from:
                    path.append(grid[curr[0]][curr[1]])
                    curr = came_from[curr]
                path.append(grid[start_node[0]][start_node[1]])
                path.reverse()
                return path

            if cur_i >= n_rows - 1:
                continue

            # Move one step forward and up to two lanes sideways.
            next_i = cur_i + 1
            for dj in (-2, -1, 0, 1, 2):
                next_j = cur_j + dj
                if 0 <= next_j < n_cols:
                    u = grid[cur_i][cur_j]
                    v = grid[next_i][next_j]

                    seg_dist_km = mars_surface_distance_km(u["lat"], u["lon"], v["lat"], v["lon"])
                    elev_delta_m = v["elev"] - u["elev"]
                    seg_dist_m = max(seg_dist_km * 1000.0, 1.0)
                    step_slope_deg = math.degrees(math.atan(abs(elev_delta_m) / seg_dist_m))
                    local_slope = max(v["slope"], step_slope_deg)

                    # Cost function
                    max_limit = profile_params["max_climbable_slope_deg"]
                    slope_penalty = 1.0
                    if local_slope > max_limit:
                        slope_penalty = 100.0 * (local_slope - max_limit + 1.0) ** 2
                    else:
                        slope_scale = profile_params["slope_weight"] * (2.0 if preference == "minimum_slope" else 0.5)
                        slope_penalty = 1.0 + slope_scale * (local_slope / 10.0) ** 2

                    roughness_penalty = 1.0 + profile_params["roughness_weight"] * (v["tri"] / 5.0)
                    step_cost = seg_dist_km * slope_penalty * roughness_penalty

                    tentative_g = g_score[(cur_i, cur_j)] + step_cost
                    if tentative_g < g_score[(next_i, next_j)]:
                        came_from[(next_i, next_j)] = (cur_i, cur_j)
                        g_score[(next_i, next_j)] = tentative_g
                        # Heuristic: remaining great-circle distance
                        h = mars_surface_distance_km(v["lat"], v["lon"], target_lat, target_lon)
                        heapq.heappush(open_set, (tentative_g + h, next_i, next_j))

        # Fallback to direct centerline
        return [grid[i][n_cols // 2 if 0 < i < n_rows - 1 else 0] for i in range(n_rows)]

    def _build_route_option(
        self,
        route_id: str,
        name: str,
        description: str,
        nodes: List[Dict[str, Any]],
        direct_dist_km: float,
        profile_params: Dict[str, Any]
    ) -> RouteOption:
        waypoints: List[RouteElevationPoint] = []
        segments: List[RouteSegment] = []

        cum_dist_km = 0.0
        elev_gain = 0.0
        elev_loss = 0.0
        max_slope = 0.0
        slope_sum = 0.0
        hazard_count = 0
        elevations = []

        max_allowed_slope = profile_params["max_climbable_slope_deg"]

        for idx, node in enumerate(nodes):
            lat = node["lat"]
            lon = node["lon"]
            elev = node["elev"]
            slope = node["slope"]
            tri = node["tri"]
            elevations.append(elev)

            if idx > 0:
                prev = nodes[idx - 1]
                d_km = mars_surface_distance_km(prev["lat"], prev["lon"], lat, lon)
                cum_dist_km += d_km
                d_elev = elev - prev["elev"]
                if d_elev > 0:
                    elev_gain += d_elev
                else:
                    elev_loss += abs(d_elev)

                seg_dist_m = max(d_km * 1000.0, 1.0)
                seg_slope = max(slope, math.degrees(math.atan(abs(d_elev) / seg_dist_m)))
                max_slope = max(max_slope, seg_slope)
                slope_sum += seg_slope

                is_hazard = seg_slope > max_allowed_slope or tri > 15.0
                if is_hazard:
                    hazard_count += 1

                traversability = "traversable"
                if seg_slope > max_allowed_slope:
                    traversability = "impassable" if seg_slope > profile_params["critical_slope_deg"] else "hazard"
                elif seg_slope > max_allowed_slope * 0.7:
                    traversability = "difficult"

                segments.append(RouteSegment(
                    segment_index=idx - 1,
                    start_lat=round(prev["lat"], 5),
                    start_lon=round(prev["lon"], 5),
                    end_lat=round(lat, 5),
                    end_lon=round(lon, 5),
                    surface_distance_m=round(d_km * 1000.0, 1),
                    elevation_start_m=round(prev["elev"], 1),
                    elevation_end_m=round(elev, 1),
                    elevation_delta_m=round(d_elev, 1),
                    slope_degrees=round(seg_slope, 2),
                    is_hazard=is_hazard,
                    traversability=traversability
                ))

            waypoints.append(RouteElevationPoint(
                distance_km=round(cum_dist_km, 3),
                latitude=round(lat, 5),
                longitude=round(lon, 5),
                elevation_m=round(elev, 1),
                slope_degrees=round(slope, 2),
                roughness_tri=round(tri, 2)
            ))

        mean_slope = slope_sum / max(len(segments), 1)
        detour = cum_dist_km / max(direct_dist_km, 0.001)

        # Mobility Terramechanics & Energy Modeling
        v_profile_key = profile_params.get("profile_key", "rover_perseverance")
        v_specs = ROVER_SPECIFICATIONS.get(v_profile_key, ROVER_SPECIFICATIONS["rover_perseverance"])
        
        # Drive duration: rover drives at nominal speed with slope/roughness slowdown
        drive_speed = max(0.01, v_specs.nominal_speed_km_h / (1.0 + mean_slope * 0.05))
        duration_hours = cum_dist_km / drive_speed
        duration_sols = max(0.1, duration_hours / 4.0)  # ~4 hours active driving per sol

        mean_tri = sum(w.roughness_tri for w in waypoints) / max(len(waypoints), 1)
        terramech = assess_terramechanics(mean_slope, mean_tri, v_specs)
        energy_metrics = compute_energy_consumption(cum_dist_km, elev_gain, mean_slope, duration_hours, v_specs)
        feasibility_rep = evaluate_mobility_feasibility(max_slope, terramech, energy_metrics, v_specs, duration_sols)
        risks = evaluate_traverse_risks(max_slope, mean_slope, mean_tri, terramech, energy_metrics, v_specs)

        start_pt = waypoints[0] if waypoints else RouteElevationPoint(distance_km=0, latitude=18.0, longitude=77.0, elevation_m=0, slope_degrees=0, roughness_tri=0)
        daily_schedule = generate_daily_schedule(
            sol_num=1,
            drive_distance_m=(cum_dist_km * 1000.0) / max(1.0, duration_sols),
            drive_duration_hours=min(4.0, duration_hours),
            vehicle=v_specs,
            energy_wh=energy_metrics.total_energy_wh / max(1.0, duration_sols),
            lat_deg=start_pt.latitude,
            lon_deg=start_pt.longitude
        )

        # Hazard Score [0-100]
        hazard_score = min(100.0, max(0.0, (
            (max_slope / v_specs.critical_rollover_slope_deg) * 45.0 +
            (terramech.estimated_wheel_slip_pct / 60.0) * 35.0 +
            (hazard_count / max(1, len(segments))) * 20.0
        )))
        confidence_pct = round(max(30.0, 100.0 - hazard_score * 0.5 - detour * 5.0), 1)

        mobility_assessment = {
            "vehicle_profile": v_specs.model_dump(),
            "terramechanics": terramech.model_dump(),
            "energy": energy_metrics.model_dump(),
            "feasibility": feasibility_rep.model_dump(),
            "risks": risks.model_dump(),
            "sample_sol_schedule": daily_schedule.model_dump(),
            "hazard_score": round(hazard_score, 1),
            "confidence_level_pct": confidence_pct,
            "estimated_duration_sols": round(duration_sols, 2),
            "estimated_duration_hours": round(duration_hours, 1)
        }

        quality_metrics = {
            "total_distance_km": round(cum_dist_km, 2),
            "elevation_gain_m": round(elev_gain, 1),
            "elevation_loss_m": round(elev_loss, 1),
            "average_slope_deg": round(mean_slope, 2),
            "maximum_slope_deg": round(max_slope, 2),
            "estimated_energy_demand_wh": energy_metrics.total_energy_wh,
            "terrain_hazard_score": round(hazard_score, 1),
            "confidence_level_pct": confidence_pct,
            "estimated_travel_duration_sols": round(duration_sols, 2),
            "geometric_feasible": feasibility_rep.geometric_feasible,
            "engineering_feasible": feasibility_rep.engineering_feasible,
            "energy_feasible": feasibility_rep.energy_feasible,
            "mission_feasible": feasibility_rep.mission_feasible
        }

        # Generate GeoJSON
        geojson_feature = {
            "type": "Feature",
            "properties": {
                "route_id": route_id,
                "name": name,
                "total_distance_km": round(cum_dist_km, 2),
                "elevation_gain_m": round(elev_gain, 1),
                "max_slope_deg": round(max_slope, 2),
                "hazard_segments": hazard_count,
                "energy_wh": energy_metrics.total_energy_wh,
                "duration_sols": round(duration_sols, 2),
                "mission_feasible": feasibility_rep.mission_feasible,
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [[w.longitude, w.latitude, w.elevation_m] for w in waypoints]
            }
        }
        geojson = {
            "type": "FeatureCollection",
            "features": [geojson_feature]
        }

        return RouteOption(
            route_id=route_id,
            name=name,
            description=description,
            total_distance_km=round(cum_dist_km, 2),
            direct_distance_km=round(direct_dist_km, 2),
            detour_factor=round(detour, 2),
            elevation_gain_m=round(elev_gain, 1),
            elevation_loss_m=round(elev_loss, 1),
            min_elevation_m=round(min(elevations), 1),
            max_elevation_m=round(max(elevations), 1),
            max_slope_degrees=round(max_slope, 2),
            mean_slope_degrees=round(mean_slope, 2),
            hazard_segments_count=hazard_count,
            waypoints=waypoints,
            segments=segments,
            geojson=geojson,
            mobility_assessment=mobility_assessment,
            quality_metrics=quality_metrics
        )
