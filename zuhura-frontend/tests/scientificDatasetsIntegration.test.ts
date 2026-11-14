import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock Cesium classes for headless unit testing
vi.mock('cesium', () => {
  class MockEllipsoid {
    radii = { x: 3396190.0, y: 3396190.0, z: 3376200.0 };
  }

  class MockTilingScheme {
    constructor(public options: any) {}
  }

  class MockRectangle {
    constructor(
      public west: number,
      public south: number,
      public east: number,
      public north: number,
    ) {}
    static fromDegrees(west: number, south: number, east: number, north: number) {
      return new MockRectangle(west, south, east, north);
    }
  }

  class MockEvent {
    addEventListener = vi.fn();
    removeEventListener = vi.fn();
  }

  class MockUrlTemplateImageryProvider {
    url: string;
    minimumLevel: number;
    maximumLevel: number;
    rectangle?: any;
    hasAlphaChannel: boolean;
    credit: string;
    errorEvent = new MockEvent();

    constructor(public options: any) {
      this.url = options.url;
      this.minimumLevel = options.minimumLevel;
      this.maximumLevel = options.maximumLevel;
      this.rectangle = options.rectangle;
      this.hasAlphaChannel = !!options.hasAlphaChannel;
      this.credit = options.credit;
    }
  }

  return {
    Ellipsoid: MockEllipsoid,
    GeographicTilingScheme: MockTilingScheme,
    Rectangle: MockRectangle,
    UrlTemplateImageryProvider: MockUrlTemplateImageryProvider,
    Math: {
      toDegrees: (rad: number) => (rad * 180.0) / Math.PI,
      toRadians: (deg: number) => (deg * Math.PI) / 180.0,
    },
  };
});

import { useGlobeStore } from '../src/store/globeStore';
import { useLayerStore } from '../src/store/layerStore';
import {
  IMAGERY_TIERS,
  createMolaHrscBlendImageryProvider,
  createThemisDayIrImageryProvider,
  createTesClinopyroxeneImageryProvider,
  createGenericTrekProvider,
} from '../src/lib/cesium/imageryProviders';

describe('Scientific Datasets & Exploration Engine Integration', () => {
  beforeEach(() => {
    const globe = useGlobeStore.getState();
    globe.setIsRoverRawImagesOpen(false);
    globe.setIsMountSharpModalOpen(false);
    globe.setIsDatasetExplorerOpen(false);
  });

  it('defines authentic Mars Trek and USGS imagery tiers in IMAGERY_TIERS', () => {
    expect(IMAGERY_TIERS.molaHrscBlend).toBeDefined();
    expect(IMAGERY_TIERS.molaHrscBlend.tier).toBe(5);
    expect(IMAGERY_TIERS.molaHrscBlend.credit).toContain('Solar System Treks');

    expect(IMAGERY_TIERS.themisDayIr).toBeDefined();
    expect(IMAGERY_TIERS.themisDayIr.credit).toContain('THEMIS');

    expect(IMAGERY_TIERS.tesClinopyroxene).toBeDefined();
    expect(IMAGERY_TIERS.tesClinopyroxene.credit).toContain('Thermal Emission Spectrometer');
  });

  it('instantiates Mars Trek and mineralogical Cesium imagery providers', () => {
    const molaHrsc = createMolaHrscBlendImageryProvider();
    expect(molaHrsc).toBeDefined();
    expect((molaHrsc as any).minimumLevel).toBe(0);

    const themis = createThemisDayIrImageryProvider();
    expect(themis).toBeDefined();

    const tes = createTesClinopyroxeneImageryProvider();
    expect(tes).toBeDefined();

    const generic = createGenericTrekProvider('Mars_MGS_MOLA_ClrShade_merge_global_463m');
    expect(generic).toBeDefined();
  });

  it('stores authentic Mars scientific layers in layerStore with toggle & opacity controls', () => {
    const { layers, toggleLayer, setOpacity } = useLayerStore.getState();

    const mountSharpLayer = layers.find((l) => l.id === 'zuhura-mount-sharp-route');
    expect(mountSharpLayer).toBeDefined();
    expect(mountSharpLayer?.name).toContain('Mount Sharp');

    const molaHrscLayer = layers.find((l) => l.id === 'zuhura-mola-hrsc-blend');
    expect(molaHrscLayer).toBeDefined();

    const tesLayer = layers.find((l) => l.id === 'zuhura-tes-clinopyroxene');
    expect(tesLayer).toBeDefined();
    expect(tesLayer?.category).toBe('mineralogy');

    // Test toggle
    const initialVisibility = molaHrscLayer?.visible;
    toggleLayer('zuhura-mola-hrsc-blend');
    const toggled = useLayerStore.getState().layers.find((l) => l.id === 'zuhura-mola-hrsc-blend');
    expect(toggled?.visible).toBe(!initialVisibility);

    // Test opacity
    setOpacity('zuhura-mola-hrsc-blend', 0.42);
    const withOpacity = useLayerStore.getState().layers.find((l) => l.id === 'zuhura-mola-hrsc-blend');
    expect(withOpacity?.opacity).toBeCloseTo(0.42);
  });

  it('manages modal visibility state for Rover Raw Images, Mount Sharp, and Dataset Explorer', () => {
    const globe = useGlobeStore.getState();

    expect(globe.isRoverRawImagesOpen).toBe(false);
    globe.setIsRoverRawImagesOpen(true);
    expect(useGlobeStore.getState().isRoverRawImagesOpen).toBe(true);
    globe.setIsRoverRawImagesOpen(false);
    expect(useGlobeStore.getState().isRoverRawImagesOpen).toBe(false);

    expect(globe.isMountSharpModalOpen).toBe(false);
    globe.setIsMountSharpModalOpen(true);
    expect(useGlobeStore.getState().isMountSharpModalOpen).toBe(true);
    globe.setIsMountSharpModalOpen(false);

    expect(globe.isDatasetExplorerOpen).toBe(false);
    globe.setIsDatasetExplorerOpen(true);
    expect(useGlobeStore.getState().isDatasetExplorerOpen).toBe(true);
  });
});
