import { describe, it, expect, vi } from 'vitest';

// Mock Cesium for headless unit tests to avoid DOM/KML browser-only bundle requirements
vi.mock('cesium', () => {
  return {
    Ellipsoid: class MockEllipsoid {
      radii: { x: number; y: number; z: number };
      constructor(x: number, y: number, z: number) {
        this.radii = { x, y, z };
      }
    },
    GeographicTilingScheme: class MockTilingScheme {
      constructor(public options: any) {}
    },
    Viewer: class MockViewer {
      scene: any;
      camera: any;
      entities: any;
      constructor() {
        this.scene = { globe: {}, skyAtmosphere: {} };
        this.camera = { changed: { addEventListener: vi.fn() }, flyTo: vi.fn() };
        this.entities = { add: vi.fn() };
      }
      isDestroyed() { return false; }
      destroy() {}
    },
    Globe: class MockGlobe {},
    SkyAtmosphere: class MockSkyAtmosphere {},
    Cartesian3: {
      fromDegrees: (lon: number, lat: number, alt: number) => ({ x: lon, y: lat, z: alt }),
    },
    Color: {
      fromCssColorString: vi.fn(),
      WHITE: 'white',
      BLACK: 'black',
    },
    LabelStyle: { FILL_AND_OUTLINE: 1 },
    VerticalOrigin: { BOTTOM: 1 },
    ScreenSpaceEventHandler: class MockHandler {
      setInputAction = vi.fn();
      destroy = vi.fn();
    },
    ScreenSpaceEventType: { MOUSE_MOVE: 1 },
    Math: {
      toDegrees: (rad: number) => (rad * 180.0) / Math.PI,
    },
  };
});

import {
  MARS_SEMI_MAJOR_A,
  MARS_SEMI_MINOR_C,
  MARS_FLATTENING,
} from '../src/lib/geodesy/constants';
import {
  planetographicToPlanetocentricLat,
  planetocentricToPlanetographicLat,
  normalizeEastLongitude,
  marsSurfaceDistanceKm,
} from '../src/lib/geodesy/transformations';
import { MARS_ELLIPSOID } from '../src/lib/cesium/marsEllipsoid';

describe('Mars Geodetic Core Tests', () => {
  it('validates IAU/IAG 2015 Biaxial Ellipsoid constants', () => {
    expect(MARS_SEMI_MAJOR_A).toBe(3396190.0);
    expect(MARS_SEMI_MINOR_C).toBe(3376200.0);
    expect(MARS_FLATTENING).toBeCloseTo(0.005886, 5);

    // Cesium Ellipsoid radii verification
    expect(MARS_ELLIPSOID.radii.x).toBe(3396190.0);
    expect(MARS_ELLIPSOID.radii.y).toBe(3396190.0);
    expect(MARS_ELLIPSOID.radii.z).toBe(3376200.0);
  });

  it('verifies Planetographic to Planetocentric conversion at 0, 90, and 45 degrees', () => {
    expect(planetographicToPlanetocentricLat(0.0)).toBe(0.0);
    expect(planetographicToPlanetocentricLat(90.0)).toBe(90.0);
    expect(planetographicToPlanetocentricLat(-90.0)).toBe(-90.0);

    const phiC = planetographicToPlanetocentricLat(45.0);
    expect(phiC).toBeLessThan(45.0);
    expect(phiC).toBeCloseTo(44.662, 2);

    const roundTrip = planetocentricToPlanetographicLat(phiC);
    expect(roundTrip).toBeCloseTo(45.0, 5);
  });

  it('normalizes East-positive Martian longitudes', () => {
    expect(normalizeEastLongitude(77.45)).toBe(77.45);
    // Negative longitude (-45° -> 315° East)
    expect(normalizeEastLongitude(-45.0)).toBe(315.0);
    // West-positive convention (45° West -> 315° East)
    expect(normalizeEastLongitude(45.0, true)).toBe(315.0);
    // Out of bounds wrap around (> 360)
    expect(normalizeEastLongitude(390.0)).toBe(30.0);
  });

  it('calculates great-circle distance on Mars', () => {
    // Jezero Crater (18.38°N, 77.58°E) to Gale Crater (-5.37°N, 137.86°E)
    const dist = marsSurfaceDistanceKm(18.38, 77.58, -5.37, 137.86);
    expect(dist).toBeGreaterThan(3700);
    expect(dist).toBeLessThan(3900);
  });
});
