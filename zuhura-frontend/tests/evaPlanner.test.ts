import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock Cesium for headless environment
vi.mock('cesium', () => {
  class MockEllipsoid {
    radii = { x: 3396190.0, y: 3396190.0, z: 3376200.0 };
  }

  class MockCartesian3 {
    constructor(
      public x: number,
      public y: number,
      public z: number,
    ) {}
    static fromDegrees(lon: number, lat: number, height = 0) {
      return new MockCartesian3(lon, lat, height);
    }
  }

  class MockColor {
    constructor(
      public r: number,
      public g: number,
      public b: number,
      public a: number,
    ) {}
    static fromCssColorString(_str: string) {
      return new MockColor(1, 1, 1, 1);
    }
    withAlpha(alpha: number) {
      return new MockColor(this.r, this.g, this.b, alpha);
    }
  }

  return {
    Ellipsoid: MockEllipsoid,
    GeographicTilingScheme: class MockTilingScheme {
      constructor(public options: any) {}
    },
    Cartesian3: MockCartesian3,
    Cartesian2: class MockCartesian2 {
      constructor(
        public x: number,
        public y: number,
      ) {}
    },
    Color: MockColor,
    HeightReference: { CLAMP_TO_GROUND: 'CLAMP_TO_GROUND' },
    LabelStyle: { FILL_AND_OUTLINE: 'FILL_AND_OUTLINE' },
    VerticalOrigin: { BOTTOM: 'BOTTOM' },
    DistanceDisplayCondition: class MockDistanceDisplayCondition {
      constructor(
        public near: number,
        public far: number,
      ) {}
    },
    PolylineOutlineMaterialProperty: class MockPolylineOutlineMaterialProperty {
      constructor(public options: any) {}
    },
    ConstantPositionProperty: class MockConstantPositionProperty {
      constructor(public val: any) {}
    },
    ConstantProperty: class MockConstantProperty {
      constructor(public val: any) {}
    },
    Math: {
      toDegrees: (rad: number) => (rad * 180.0) / Math.PI,
      toRadians: (deg: number) => (deg * Math.PI) / 180.0,
    },
  };
});

import { useGlobeStore } from '../src/store/globeStore';
import {
  JEZERO_HAB_COORDINATES,
  JEZERO_HIRISE_BOUNDS,
  JEZERO_SCIENCE_TARGETS,
  THEMIS_REGOLITH_ZONES,
  RADIATION_SHIELDING_ZONES,
} from '../src/eva/jezeroScienceTargets';
import {
  calculateMarsGroundDistance,
  evaluateJezeroElevation,
  calculateSegmentMetabolicCost,
  planMetabolicEvaRoute,
  generateEmergencyAbortRoute,
  EvaPoint,
} from '../src/eva/metabolicPathfinder';
import { DEFAULT_TACTICAL_CONFIG, SLOPE_HAZARD_ZONES } from '../src/eva/tacticalLayers';

describe('EVA planner', () => {
  beforeEach(() => {
    const globe = useGlobeStore.getState();
    globe.setIsAresHudOpen(false);
    globe.setIsVisorPovActive(false);
    globe.setActiveEvaTargetId(null);
  });

  describe('Jezero Science Targets & Spatial Boundaries', () => {
    it('anchors the Jezero Habitat Base at authentic coordinates', () => {
      expect(JEZERO_HAB_COORDINATES.name).toBe('Ares Jezero Base / Hab');
      expect(JEZERO_HAB_COORDINATES.longitude).toBeCloseTo(77.58, 2);
      expect(JEZERO_HAB_COORDINATES.latitude).toBeCloseTo(18.44, 2);
      expect(JEZERO_HAB_COORDINATES.elevation_m).toBeLessThan(-2500);
    });

    it('defines HiRISE 0.5m/px bounding box strictly covering the western delta', () => {
      expect(JEZERO_HIRISE_BOUNDS.west).toBeCloseTo(77.5158, 4);
      expect(JEZERO_HIRISE_BOUNDS.south).toBeCloseTo(18.2876, 4);
      expect(JEZERO_HIRISE_BOUNDS.east).toBeCloseTo(77.6537, 4);
      expect(JEZERO_HIRISE_BOUNDS.north).toBeCloseTo(18.5834, 4);
    });

    it('contains authentic CRISM & Perseverance science targets with high priority scores', () => {
      expect(JEZERO_SCIENCE_TARGETS.length).toBeGreaterThanOrEqual(5);

      const targetIds = JEZERO_SCIENCE_TARGETS.map((t) => t.id);
      expect(targetIds).toContain('target-three-forks');
      expect(targetIds).toContain('target-kodiak-butte');
      expect(targetIds).toContain('target-bright-angel');
      expect(targetIds).toContain('target-neretya-vallis');
      expect(targetIds).toContain('target-octavia-butler');

      JEZERO_SCIENCE_TARGETS.forEach((target) => {
        expect(target.science_priority_score).toBeGreaterThanOrEqual(80);
        expect(target.science_priority_score).toBeLessThanOrEqual(100);
        expect(target.crism_mineral_signature.length).toBeGreaterThan(0);
        expect(target.longitude).toBeGreaterThanOrEqual(77.4);
        expect(target.longitude).toBeLessThanOrEqual(77.7);
        expect(target.latitude).toBeGreaterThanOrEqual(18.2);
        expect(target.latitude).toBeLessThanOrEqual(18.6);
      });
    });

    it('defines THEMIS regolith firmness and slip risk zones', () => {
      expect(THEMIS_REGOLITH_ZONES.length).toBeGreaterThanOrEqual(3);
      const rippleZone = THEMIS_REGOLITH_ZONES.find((z) => z.type === 'aeolian_sand_trap');
      expect(rippleZone).toBeDefined();
      expect(rippleZone?.metabolic_slip_penalty).toBeCloseTo(1.35, 2); // +35% O2 burn penalty
    });

    it('defines radiation shielding zones based on Curiosity RAD baseline and cliff masking', () => {
      expect(RADIATION_SHIELDING_ZONES.length).toBeGreaterThanOrEqual(2);
      const cliffShield = RADIATION_SHIELDING_ZONES.find((z) => z.type === 'shielded_scarp');
      const openRidge = RADIATION_SHIELDING_ZONES.find((z) => z.type === 'exposed_ridge' || z.type === 'open_plateau');
      expect(cliffShield).toBeDefined();
      expect(openRidge).toBeDefined();
      expect(cliffShield!.dose_rate_usv_hr).toBeLessThan(openRidge!.dose_rate_usv_hr);
    });
  });

  describe('Metabolic Cost & A* Pathfinding Engine', () => {
    it('computes accurate Mars ground distances using Vincenty elliptic formula', () => {
      const dist1Deg = calculateMarsGroundDistance(77.0, 18.0, 77.0, 19.0);
      // 1 degree of latitude on Mars is ~59.16 km (2 * pi * 3389.5 km / 360)
      expect(dist1Deg).toBeGreaterThan(58000);
      expect(dist1Deg).toBeLessThan(60500);
    });

    it('evaluates realistic Jezero Crater floor and delta scarp elevations', () => {
      const habElev = evaluateJezeroElevation(77.58, 18.44);
      expect(habElev).toBeLessThan(-2500);

      const deltaTopElev = evaluateJezeroElevation(77.52, 18.45);
      // Delta top is ~60-120m higher than crater floor
      expect(deltaTopElev).toBeGreaterThan(habElev);
    });

    it('penalizes steep slopes (>20°) as critical hazards and tags safe slopes (<12°) as optimal', () => {
      const flatStart: EvaPoint = { longitude: 77.58, latitude: 18.44, elevation_m: -2560.0 };
      const flatEnd: EvaPoint = { longitude: 77.581, latitude: 18.44, elevation_m: -2560.0 };
      const flatSeg = calculateSegmentMetabolicCost(flatStart, flatEnd);
      expect(flatSeg.hazard_level).toBe('optimal');
      expect(flatSeg.hazard_color).toBe('#10b981'); // Emerald Green

      const steepStart: EvaPoint = { longitude: 77.535, latitude: 18.43, elevation_m: -2550.0 };
      const cliffEnd: EvaPoint = { longitude: 77.5352, latitude: 18.43, elevation_m: -2480.0 }; // ~70m climb over ~12m = 80° cliff
      const steepSeg = calculateSegmentMetabolicCost(steepStart, cliffEnd);
      expect(steepSeg.hazard_level).toBe('critical');
      expect(steepSeg.hazard_color).toBe('#ef4444'); // Crimson Red
      expect(steepSeg.slope_deg).toBeGreaterThan(20.0);
    });

    it('applies +35% oxygen burn penalty when traversing aeolian sand ripple zones', () => {
      // In the South Séítah aeolian ripple sand trap (77.515°–77.535°E, 18.410°–18.430°N)
      const p1: EvaPoint = { longitude: 77.52, latitude: 18.42, elevation_m: -2560.0 };
      const p2: EvaPoint = { longitude: 77.522, latitude: 18.42, elevation_m: -2560.0 };
      const sandSeg = calculateSegmentMetabolicCost(p1, p2);

      expect(sandSeg.slip_penalty).toBeCloseTo(1.35, 2);
      expect(sandSeg.surface_type).toContain('Aeolian Sand');
    });

    it('plans a comprehensive metabolic EVA sortie with realistic suit telemetry metrics', () => {
      const sortieWaypoints: EvaPoint[] = [
        { ...JEZERO_HAB_COORDINATES, isHab: true },
        { longitude: 77.56, latitude: 18.442, elevation_m: -2550.0, name: 'Crater Floor Waypoint' },
        { longitude: 77.545, latitude: 18.445, elevation_m: -2500.0, name: 'Three Forks Delta Toe' },
      ];

      const plan = planMetabolicEvaRoute(sortieWaypoints, false);

      expect(plan.isEmergencyAbort).toBe(false);
      expect(plan.total_distance_m).toBeGreaterThan(1000);
      expect(plan.total_duration_minutes).toBeGreaterThan(15);
      expect(plan.total_metabolic_cost_kcal).toBeGreaterThan(50);
      expect(plan.total_oxygen_consumed_g).toBeGreaterThan(10);
      expect(plan.suit_oxygen_pct_remaining).toBeGreaterThan(0);
      expect(plan.suit_oxygen_pct_remaining).toBeLessThanOrEqual(100);
      expect(plan.suit_battery_pct_remaining).toBeGreaterThan(0);
      expect(plan.suit_battery_pct_remaining).toBeLessThanOrEqual(100);
      expect(plan.average_o2_burn_rate_kg_hr).toBeGreaterThan(0.04);
      expect(plan.segments.length).toBeGreaterThan(0);
      expect(plan.elevation_profile.length).toBeGreaterThan(0);
    });

    it('generates an immediate Emergency Abort to Hab route with lowest-burn retreat', () => {
      const astronautPos = { longitude: 77.542, latitude: 18.448, elevation_m: -2480.0 };
      const abortPlan = generateEmergencyAbortRoute(astronautPos);

      expect(abortPlan.isEmergencyAbort).toBe(true);
      expect(abortPlan.waypoints[0].isAbort).toBe(true);
      expect(abortPlan.waypoints[abortPlan.waypoints.length - 1].isHab).toBe(true);
      expect(abortPlan.waypoints[abortPlan.waypoints.length - 1].longitude).toBeCloseTo(
        JEZERO_HAB_COORDINATES.longitude,
        3,
      );
      expect(abortPlan.total_distance_m).toBeGreaterThan(0);
      expect(abortPlan.suit_oxygen_pct_remaining).toBeGreaterThan(0);
    });
  });

  describe('Tactical Layer Config & Zones', () => {
    it('exports DEFAULT_TACTICAL_CONFIG with all 4 layers enabled by default', () => {
      expect(DEFAULT_TACTICAL_CONFIG.slopeHazardVisible).toBe(true);
      expect(DEFAULT_TACTICAL_CONFIG.thermalRegolithVisible).toBe(true);
      expect(DEFAULT_TACTICAL_CONFIG.scienceTargetsVisible).toBe(true);
      expect(DEFAULT_TACTICAL_CONFIG.radiationShieldingVisible).toBe(true);
      expect(DEFAULT_TACTICAL_CONFIG.slopeHazardOpacity).toBeGreaterThan(0);
      expect(DEFAULT_TACTICAL_CONFIG.thermalRegolithOpacity).toBeGreaterThan(0);
      expect(DEFAULT_TACTICAL_CONFIG.radiationShieldingOpacity).toBeGreaterThan(0);
    });

    it('defines discrete slope hazard polygons across the Jezero delta scarp', () => {
      expect(SLOPE_HAZARD_ZONES.length).toBeGreaterThanOrEqual(4);
      const cliffZone = SLOPE_HAZARD_ZONES.find((z) => z.level === 'impassable');
      const safeZone = SLOPE_HAZARD_ZONES.find((z) => z.level === 'safe');

      expect(cliffZone).toBeDefined();
      expect(safeZone).toBeDefined();
      expect(cliffZone!.slope).toBeGreaterThan(20.0);
      expect(safeZone!.slope).toBeLessThan(12.0);
    });
  });

  describe('Globe store integration', () => {
    it('manages ARES-HUD, Visor POV, and Science Target state in globeStore', () => {
      const store = useGlobeStore.getState();

      expect(store.isAresHudOpen).toBe(false);
      expect(store.isVisorPovActive).toBe(false);
      expect(store.activeEvaTargetId).toBeNull();

      store.setIsAresHudOpen(true);
      expect(useGlobeStore.getState().isAresHudOpen).toBe(true);

      store.setIsVisorPovActive(true);
      expect(useGlobeStore.getState().isVisorPovActive).toBe(true);

      store.setActiveEvaTargetId('target-three-forks');
      expect(useGlobeStore.getState().activeEvaTargetId).toBe('target-three-forks');

      store.setIsAresHudOpen(false);
      store.setIsVisorPovActive(false);
      store.setActiveEvaTargetId(null);
      expect(useGlobeStore.getState().isAresHudOpen).toBe(false);
      expect(useGlobeStore.getState().isVisorPovActive).toBe(false);
      expect(useGlobeStore.getState().activeEvaTargetId).toBeNull();
    });
  });
});
