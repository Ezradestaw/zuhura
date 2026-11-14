import * as Cesium from 'cesium';
import { MARS_ELLIPSOID, MARS_TILING_SCHEME } from './marsEllipsoid';

/**
 * Metadata definition for multi-resolution imagery tiers in the Zuhura platform.
 */
export interface ImageryTierDefinition {
  tier: number;
  id: string;
  name: string;
  minZoom: number;
  maxZoom: number;
  bounds: [number, number, number, number]; // [west, south, east, north] degrees
  templateUrl: string;
  hasAlpha: boolean;
  credit: string;
}

/**
 * Authoritative imagery tier configurations aligned with imagery_coverage_manifest.json.
 */
export const IMAGERY_TIERS: Record<string, ImageryTierDefinition> = {
  viking: {
    tier: 1,
    id: 'zuhura-viking-mdim21',
    name: 'Viking MDIM 2.1 Planetary Natural Color Basemap',
    minZoom: 0,
    maxZoom: 10,
    bounds: [-180.0, -90.0, 180.0, 90.0],
    templateUrl: '/api/v1/tiles/viking/{z}/{x}/{y}.jpg',
    hasAlpha: false,
    credit: 'USGS Astrogeology / NASA PDS Viking Visual Imaging Subsystem (VIS)',
  },
  ctx: {
    tier: 2,
    id: 'zuhura-ctx-jezero',
    name: 'MRO CTX Regional Context (Jezero Delta)',
    minZoom: 9,
    maxZoom: 15,
    bounds: [77.0399, 17.8815, 77.6199, 18.6541],
    templateUrl: '/api/v1/tiles/ctx/{z}/{x}/{y}.png',
    hasAlpha: true,
    credit: 'MSSS / NASA PDS Context Camera (CTX)',
  },
  hirise: {
    tier: 3,
    id: 'zuhura-hirise-jezero',
    name: 'MRO HiRISE Local High-Resolution (Touchdown & Delta)',
    minZoom: 13,
    maxZoom: 18,
    bounds: [77.5158, 18.2876, 77.6537, 18.5834],
    templateUrl: '/api/v1/tiles/hirise/{z}/{x}/{y}.png',
    hasAlpha: true,
    credit: 'UArizona / NASA PDS High Resolution Imaging Science Experiment (HiRISE)',
  },
  molaColormap: {
    tier: 4,
    id: 'zuhura-mola-global-v3-cog',
    name: 'MOLA MEG128 Topographic Colormap (Elevation)',
    minZoom: 0,
    maxZoom: 7,
    bounds: [-180.0, -88.0, 180.0, 88.0],
    templateUrl: '/api/v1/tiles/cog/{z}/{x}/{y}.png?colormap=terrain',
    hasAlpha: true,
    credit: 'NASA GSFC / MOLA Science Team (GMM-3 Areoid)',
  },
  molaHrscBlend: {
    tier: 5,
    id: 'zuhura-mola-hrsc-blend',
    name: 'MGS MOLA & Mars Express HRSC Color Hillshade (200m/px)',
    minZoom: 0,
    maxZoom: 9,
    bounds: [-180.0, -90.0, 180.0, 90.0],
    templateUrl: '/api/v1/tiles/trek/Mars_MOLA_blend200ppx_HRSC_ClrShade_clon0dd_200mpp_lzw/{z}/{x}/{y}.jpg',
    hasAlpha: false,
    credit: 'NASA / ESA / DLR / Solar System Treks (MOLA-HRSC Blend)',
  },
  themisDayIr: {
    tier: 6,
    id: 'zuhura-themis-day-ir',
    name: 'Mars Odyssey THEMIS-IR Daytime Global Mosaic (100m/px)',
    minZoom: 0,
    maxZoom: 9,
    bounds: [-180.0, -90.0, 180.0, 90.0],
    templateUrl: '/api/v1/tiles/trek/Mars_MGS_MOLA_ClrShade_merge_global_463m/{z}/{x}/{y}.jpg',
    hasAlpha: false,
    credit: 'ASU / NASA PDS / Mars Odyssey THEMIS Team',
  },
  tesClinopyroxene: {
    tier: 7,
    id: 'zuhura-tes-clinopyroxene',
    name: 'MGS TES Clinopyroxene (High-Ca Pyroxene) Abundance',
    minZoom: 0,
    maxZoom: 6,
    bounds: [-180.0, -90.0, 180.0, 90.0],
    templateUrl: '/api/v1/tiles/trek/TES_Clinopyroxene/{z}/{x}/{y}.jpg',
    hasAlpha: true,
    credit: 'NASA GSFC / ASU Thermal Emission Spectrometer (TES)',
  },
  tesPlagioclase: {
    tier: 8,
    id: 'zuhura-tes-plagioclase',
    name: 'MGS TES Plagioclase Feldspar Abundance',
    minZoom: 0,
    maxZoom: 6,
    bounds: [-180.0, -90.0, 180.0, 90.0],
    templateUrl: '/api/v1/tiles/trek/TES_Plagioclase/{z}/{x}/{y}.jpg',
    hasAlpha: true,
    credit: 'NASA GSFC / ASU Thermal Emission Spectrometer (TES)',
  },
};

/**
 * Creates the Viking MDIM 2.1 global natural color imagery provider (Tier 1).
 * Serves authentic Martian ochre, tan, and basalt tones across zoom levels 0-10.
 */
export function createVikingImageryProvider(): Cesium.UrlTemplateImageryProvider {
  const def = IMAGERY_TIERS.viking;
  const provider = new Cesium.UrlTemplateImageryProvider({
    url: def.templateUrl,
    tilingScheme: MARS_TILING_SCHEME,
    ellipsoid: MARS_ELLIPSOID,
    minimumLevel: def.minZoom,
    maximumLevel: def.maxZoom,
    hasAlphaChannel: def.hasAlpha,
    credit: def.credit,
  });

  provider.errorEvent.addEventListener((err) => {
    console.debug(`[Viking Tile Notice] Non-fatal tile fetch notification:`, err);
  });

  return provider;
}

/**
 * Creates the Context Camera (CTX) regional context imagery provider (Tier 2).
 * Drapes 5.55 m/px imagery strictly within the validated Jezero footprint.
 */
export function createCtxImageryProvider(): Cesium.UrlTemplateImageryProvider {
  const def = IMAGERY_TIERS.ctx;
  const provider = new Cesium.UrlTemplateImageryProvider({
    url: def.templateUrl,
    tilingScheme: MARS_TILING_SCHEME,
    ellipsoid: MARS_ELLIPSOID,
    minimumLevel: def.minZoom,
    maximumLevel: def.maxZoom,
    rectangle: Cesium.Rectangle.fromDegrees(def.bounds[0], def.bounds[1], def.bounds[2], def.bounds[3]),
    hasAlphaChannel: def.hasAlpha,
    credit: def.credit,
  });

  provider.errorEvent.addEventListener((err) => {
    console.debug(`[CTX Tile Notice] Non-fatal tile fetch notification:`, err);
  });

  return provider;
}

/**
 * Creates the HiRISE local targeted sub-meter imagery provider (Tier 3).
 * Drapes 0.50 m/px imagery strictly within the Perseverance touchdown ellipse and delta scarp.
 */
export function createHiRiseImageryProvider(): Cesium.UrlTemplateImageryProvider {
  const def = IMAGERY_TIERS.hirise;
  const provider = new Cesium.UrlTemplateImageryProvider({
    url: def.templateUrl,
    tilingScheme: MARS_TILING_SCHEME,
    ellipsoid: MARS_ELLIPSOID,
    minimumLevel: def.minZoom,
    maximumLevel: def.maxZoom,
    rectangle: Cesium.Rectangle.fromDegrees(def.bounds[0], def.bounds[1], def.bounds[2], def.bounds[3]),
    hasAlphaChannel: def.hasAlpha,
    credit: def.credit,
  });

  provider.errorEvent.addEventListener((err) => {
    console.debug(`[HiRISE Tile Notice] Non-fatal tile fetch notification:`, err);
  });

  return provider;
}

/**
 * Creates the MOLA MEG128 scientific elevation colormap imagery provider (Tier 4).
 * Optional topographic inspection layer; not the default optical basemap.
 */
export function createMolaColormapImageryProvider(): Cesium.UrlTemplateImageryProvider {
  const def = IMAGERY_TIERS.molaColormap;
  const provider = new Cesium.UrlTemplateImageryProvider({
    url: def.templateUrl,
    tilingScheme: MARS_TILING_SCHEME,
    ellipsoid: MARS_ELLIPSOID,
    minimumLevel: def.minZoom,
    maximumLevel: def.maxZoom,
    rectangle: Cesium.Rectangle.fromDegrees(def.bounds[0], def.bounds[1], def.bounds[2], def.bounds[3]),
    hasAlphaChannel: def.hasAlpha,
    credit: def.credit,
  });

  provider.errorEvent.addEventListener((err) => {
    console.debug(`[MOLA Colormap Notice] Non-fatal tile fetch notification:`, err);
  });

  return provider;
}

/**
 * Creates MGS MOLA + Mars Express HRSC blended color hillshade provider (Tier 5).
 */
export function createMolaHrscBlendImageryProvider(): Cesium.UrlTemplateImageryProvider {
  const def = IMAGERY_TIERS.molaHrscBlend;
  const provider = new Cesium.UrlTemplateImageryProvider({
    url: def.templateUrl,
    tilingScheme: MARS_TILING_SCHEME,
    ellipsoid: MARS_ELLIPSOID,
    minimumLevel: def.minZoom,
    maximumLevel: def.maxZoom,
    hasAlphaChannel: def.hasAlpha,
    credit: def.credit,
  });
  return provider;
}

/**
 * Creates Mars Odyssey THEMIS Daytime Infrared global mosaic provider (Tier 6).
 */
export function createThemisDayIrImageryProvider(): Cesium.UrlTemplateImageryProvider {
  const def = IMAGERY_TIERS.themisDayIr;
  const provider = new Cesium.UrlTemplateImageryProvider({
    url: def.templateUrl,
    tilingScheme: MARS_TILING_SCHEME,
    ellipsoid: MARS_ELLIPSOID,
    minimumLevel: def.minZoom,
    maximumLevel: def.maxZoom,
    hasAlphaChannel: def.hasAlpha,
    credit: def.credit,
  });
  return provider;
}

/**
 * Creates MGS TES Clinopyroxene mineralogy provider (Tier 7).
 */
export function createTesClinopyroxeneImageryProvider(): Cesium.UrlTemplateImageryProvider {
  const def = IMAGERY_TIERS.tesClinopyroxene;
  const provider = new Cesium.UrlTemplateImageryProvider({
    url: def.templateUrl,
    tilingScheme: MARS_TILING_SCHEME,
    ellipsoid: MARS_ELLIPSOID,
    minimumLevel: def.minZoom,
    maximumLevel: def.maxZoom,
    hasAlphaChannel: def.hasAlpha,
    credit: def.credit,
  });
  return provider;
}

/**
 * Creates an arbitrary authentic NASA Mars Trek WMTS layer provider.
 */
export function createGenericTrekProvider(
  layerLabel: string,
  credit: string = 'NASA Solar System Treks',
): Cesium.UrlTemplateImageryProvider {
  return new Cesium.UrlTemplateImageryProvider({
    url: `/api/v1/tiles/trek/${layerLabel}/{z}/{x}/{y}.jpg`,
    tilingScheme: MARS_TILING_SCHEME,
    ellipsoid: MARS_ELLIPSOID,
    minimumLevel: 0,
    maximumLevel: 12,
    hasAlphaChannel: true,
    credit: credit,
  });
}
