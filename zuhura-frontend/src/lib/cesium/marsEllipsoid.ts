import * as Cesium from 'cesium';
import { MARS_SEMI_MAJOR_A, MARS_SEMI_MINOR_C } from '../geodesy/constants';

/**
 * Creates and exports the official IAU/IAG 2015 Mars Biaxial Ellipsoid for CesiumJS.
 */
export const MARS_ELLIPSOID = new Cesium.Ellipsoid(
  MARS_SEMI_MAJOR_A, // X radius in meters
  MARS_SEMI_MAJOR_A, // Y radius in meters
  MARS_SEMI_MINOR_C, // Z radius in meters
);

/**
 * Custom Mars Geographic Tiling Scheme using the Mars Ellipsoid.
 */
export const MARS_TILING_SCHEME = new Cesium.GeographicTilingScheme({
  ellipsoid: MARS_ELLIPSOID,
  numberOfLevelZeroTilesX: 2,
  numberOfLevelZeroTilesY: 1,
});

/**
 * Initializes a Cesium Viewer configured specifically for Mars rendering.
 * Configures the planetary appearance, restrained atmospheric scattering,
 * terrain oct-normal lighting, and optimized tile cache performance.
 */
export function initializeMarsViewer(container: HTMLElement): Cesium.Viewer {
  const viewer = new Cesium.Viewer(container, {
    baseLayer: false,
    ellipsoid: MARS_ELLIPSOID,
    mapProjection: new Cesium.GeographicProjection(MARS_ELLIPSOID),
    globe: new Cesium.Globe(MARS_ELLIPSOID),
    skyAtmosphere: new Cesium.SkyAtmosphere(MARS_ELLIPSOID),
    skyBox: false,
    baseLayerPicker: false,
    geocoder: false,
    homeButton: false,
    infoBox: false,
    sceneModePicker: false,
    selectionIndicator: false,
    navigationHelpButton: false,
    animation: false,
    timeline: false,
    fullscreenButton: false,
    vrButton: false,
  });

  const globe = viewer.scene.globe;

  // 1. High-resolution display scaling & anti-aliasing (Retina / 4K / HiDPI support)
  viewer.resolutionScale = Math.min(window.devicePixelRatio || 1.0, 2.0);
  try {
    viewer.scene.msaaSamples = 4;
  } catch {
    // Graceful fallback on older WebGL contexts
  }

  // 2. Maximum sharpness terrain & imagery tile loading (without adding extra datasets)
  globe.depthTestAgainstTerrain = true;
  globe.maximumScreenSpaceError = 0.8; // Reduced screen space error forces sharpest tiles sooner
  globe.tileCacheSize = 2500;
  globe.loadingDescendantLimit = 30;
  globe.preloadAncestors = true;
  globe.preloadSiblings = true;

  // 3. Martian crust base color (replaces Earth blue ocean fallback)
  globe.baseColor = new Cesium.Color(0.11, 0.08, 0.06, 1.0);

  // 4. Crystal-clear surface visibility: disable washed-out atmospheric fog haze
  globe.showGroundAtmosphere = false;
  globe.dynamicAtmosphereLighting = true;
  globe.dynamicAtmosphereLightingFromSun = false;
  globe.lambertDiffuseMultiplier = 0.95;

  // 4. Subtle atmospheric limb scattering at planetary horizon
  const atmosphere = viewer.scene.skyAtmosphere;
  if (atmosphere) {
    atmosphere.brightnessShift = -0.2;
    atmosphere.saturationShift = -0.3;
    atmosphere.hueShift = 0.05;
    atmosphere.atmosphereLightIntensity = 5.0;
  }

  // 5. Set default initial view over Jezero Crater (Perseverance landing site)
  viewer.camera.setView({
    destination: Cesium.Cartesian3.fromDegrees(
      77.45,
      18.44,
      1500000.0, // 1,500 km altitude
      MARS_ELLIPSOID,
    ),
  });

  return viewer;
}
