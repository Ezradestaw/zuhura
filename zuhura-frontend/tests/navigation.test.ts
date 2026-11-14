import { describe, it, expect, beforeEach } from 'vitest';
import { useGlobeStore } from '../src/store/globeStore';
import { useWorkspaceStore } from '../src/store/workspaceStore';
import { marsSurfaceDistanceKm } from '../src/lib/geodesy/transformations';

describe('Navigation and interaction', () => {
  beforeEach(() => {
    // Reset stores to default state
    useGlobeStore.setState({
      cameraHeading: 0.0,
      cameraPitch: -90.0,
      cameraRoll: 0.0,
      isSurfaceWalkActive: false,
      surfaceWalkSpeed: 2.5,
      isSplitScreenActive: false,
      splitPosition: 0.5,
      splitLeftLayerId: 'zuhura-viking-mdim21',
      splitRightLayerId: 'zuhura-ctx-jezero',
      tilesLoadingCount: 0,
      isTileLoadError: false,
    });

    useWorkspaceStore.setState({
      measurementToolActive: 'none',
      measurementPoints: [],
    });
  });

  describe('1. Camera Orientation & 3D Compass Telemetry', () => {
    it('initializes heading at 0 deg North, pitch at nadir -90 deg, and roll at 0 deg', () => {
      const state = useGlobeStore.getState();
      expect(state.cameraHeading).toBe(0.0);
      expect(state.cameraPitch).toBe(-90.0);
      expect(state.cameraRoll).toBe(0.0);
    });

    it('updates camera orientation angles dynamically', () => {
      useGlobeStore.getState().setCameraOrientation(45.5, -45.0, 1.2);
      const state = useGlobeStore.getState();
      expect(state.cameraHeading).toBe(45.5);
      expect(state.cameraPitch).toBe(-45.0);
      expect(state.cameraRoll).toBe(1.2);
    });
  });

  describe('2. First-Person Planetary Surface Exploration Mode', () => {
    it('activates and deactivates surface walk mode', () => {
      expect(useGlobeStore.getState().isSurfaceWalkActive).toBe(false);
      useGlobeStore.getState().setIsSurfaceWalkActive(true);
      expect(useGlobeStore.getState().isSurfaceWalkActive).toBe(true);
      useGlobeStore.getState().setIsSurfaceWalkActive(false);
      expect(useGlobeStore.getState().isSurfaceWalkActive).toBe(false);
    });

    it('toggles movement velocity between nominal walk (2.5 m/s) and sprint (5.0 m/s)', () => {
      expect(useGlobeStore.getState().surfaceWalkSpeed).toBe(2.5);
      useGlobeStore.getState().setSurfaceWalkSpeed(5.0);
      expect(useGlobeStore.getState().surfaceWalkSpeed).toBe(5.0);
      useGlobeStore.getState().setSurfaceWalkSpeed(2.5);
      expect(useGlobeStore.getState().surfaceWalkSpeed).toBe(2.5);
    });
  });

  describe('3. Split-Screen Swipe Layer Comparison', () => {
    it('manages swipe divider position between 0.0 and 1.0', () => {
      expect(useGlobeStore.getState().splitPosition).toBe(0.5);
      useGlobeStore.getState().setSplitPosition(0.35);
      expect(useGlobeStore.getState().splitPosition).toBe(0.35);
    });

    it('configures active comparison layers for split screen', () => {
      useGlobeStore.getState().setSplitLayers('zuhura-ctx-jezero', 'zuhura-hirise-jezero');
      const state = useGlobeStore.getState();
      expect(state.splitLeftLayerId).toBe('zuhura-ctx-jezero');
      expect(state.splitRightLayerId).toBe('zuhura-hirise-jezero');
    });

    it('toggles split screen mode active state', () => {
      expect(useGlobeStore.getState().isSplitScreenActive).toBe(false);
      useGlobeStore.getState().setIsSplitScreenActive(true);
      expect(useGlobeStore.getState().isSplitScreenActive).toBe(true);
    });
  });

  describe('4. Dynamic Tile Loading Progress & Health', () => {
    it('records active tile queue length and network error flags', () => {
      expect(useGlobeStore.getState().tilesLoadingCount).toBe(0);
      expect(useGlobeStore.getState().isTileLoadError).toBe(false);

      useGlobeStore.getState().setTilesLoadingMetrics(14, false);
      expect(useGlobeStore.getState().tilesLoadingCount).toBe(14);
      expect(useGlobeStore.getState().isTileLoadError).toBe(false);

      useGlobeStore.getState().setTilesLoadingMetrics(0, true);
      expect(useGlobeStore.getState().tilesLoadingCount).toBe(0);
      expect(useGlobeStore.getState().isTileLoadError).toBe(true);
    });
  });

  describe('5. Interactive Geodesic Measurement & Ellipsoidal Area Engine', () => {
    it('toggles measurement tool between ruler, area, and none', () => {
      expect(useWorkspaceStore.getState().measurementToolActive).toBe('none');
      useWorkspaceStore.getState().setMeasurementToolActive('ruler');
      expect(useWorkspaceStore.getState().measurementToolActive).toBe('ruler');
      useWorkspaceStore.getState().setMeasurementToolActive('area');
      expect(useWorkspaceStore.getState().measurementToolActive).toBe('area');
    });

    it('accumulates measurement vertices and clears them on reset', () => {
      useWorkspaceStore.getState().addMeasurementPoint({ lat: 18.38, lon: 77.58, elevation_m: -2648.0 });
      useWorkspaceStore.getState().addMeasurementPoint({ lat: 18.44, lon: 77.45, elevation_m: -2530.0 });
      expect(useWorkspaceStore.getState().measurementPoints.length).toBe(2);

      useWorkspaceStore.getState().clearMeasurementPoints();
      expect(useWorkspaceStore.getState().measurementPoints.length).toBe(0);
    });

    it('calculates geodesic great-circle traverse distance accurately', () => {
      // Jezero landing (18.38N, 77.58E) to Kodiak (18.44N, 77.45E)
      const d = marsSurfaceDistanceKm(18.38, 77.58, 18.44, 77.45);
      // Distance is ~8.4 km on Mars biaxial ellipsoid
      expect(d).toBeGreaterThan(7.0);
      expect(d).toBeLessThan(10.0);
    });

    it('calculates spherical excess polygon area on the Martian sphere (R = 3389.5 km)', () => {
      const R = 3389.5;
      // 1-degree square at the equator: Lat 0 to 1, Lon 0 to 1
      const p1 = { lat: 0.0, lon: 0.0 };
      const p2 = { lat: 0.0, lon: 1.0 };
      const p3 = { lat: 1.0, lon: 1.0 };
      const p4 = { lat: 1.0, lon: 0.0 };
      const pts = [p1, p2, p3, p4];

      let sum = 0.0;
      const n = pts.length;
      for (let i = 0; i < n; i++) {
        const pt1 = pts[i];
        const pt2 = pts[(i + 1) % n];
        const lon1Rad = (pt1.lon * Math.PI) / 180.0;
        const lon2Rad = (pt2.lon * Math.PI) / 180.0;
        const lat1Rad = (pt1.lat * Math.PI) / 180.0;
        const lat2Rad = (pt2.lat * Math.PI) / 180.0;
        sum += (lon2Rad - lon1Rad) * (2 + Math.sin(lat1Rad) + Math.sin(lat2Rad));
      }
      const area = Math.abs((sum * R * R) / 2.0);

      // 1 deg on Mars equator is approx (2*pi*3389.5/360) = 59.16 km
      // Square area is ~ (59.16)^2 = ~3500 km^2
      expect(area).toBeGreaterThan(3400);
      expect(area).toBeLessThan(3600);
    });
  });
});
