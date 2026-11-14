import { describe, it, expect, vi } from 'vitest';

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
      public north: number
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

import {
  IMAGERY_TIERS,
  createVikingImageryProvider,
  createCtxImageryProvider,
  createHiRiseImageryProvider,
  createMolaColormapImageryProvider,
} from '../src/lib/cesium/imageryProviders';

describe('Imagery providers and coverage', () => {
  it('defines all 4 progressive imagery tiers with validated manifests', () => {
    expect(IMAGERY_TIERS).toHaveProperty('viking');
    expect(IMAGERY_TIERS).toHaveProperty('ctx');
    expect(IMAGERY_TIERS).toHaveProperty('hirise');
    expect(IMAGERY_TIERS).toHaveProperty('molaColormap');

    expect(IMAGERY_TIERS.viking.tier).toBe(1);
    expect(IMAGERY_TIERS.ctx.tier).toBe(2);
    expect(IMAGERY_TIERS.hirise.tier).toBe(3);
    expect(IMAGERY_TIERS.molaColormap.tier).toBe(4);
  });

  it('validates Viking MDIM 2.1 zoom levels and global coverage', () => {
    const viking = IMAGERY_TIERS.viking;
    expect(viking.minZoom).toBe(0);
    expect(viking.maxZoom).toBe(10);
    expect(viking.bounds).toEqual([-180.0, -90.0, 180.0, 90.0]);
    expect(viking.templateUrl).toBe('/api/v1/tiles/viking/{z}/{x}/{y}.jpg');

    const provider = createVikingImageryProvider();
    expect(provider.url).toBe('/api/v1/tiles/viking/{z}/{x}/{y}.jpg');
    expect(provider.minimumLevel).toBe(0);
    expect(provider.maximumLevel).toBe(10);
    expect(provider.hasAlphaChannel).toBe(false);
  });

  it('validates CTX regional context zoom levels and footprint bounds', () => {
    const ctx = IMAGERY_TIERS.ctx;
    expect(ctx.minZoom).toBe(9);
    expect(ctx.maxZoom).toBe(15);
    expect(ctx.bounds).toEqual([77.0399, 17.8815, 77.6199, 18.6541]);
    expect(ctx.templateUrl).toBe('/api/v1/tiles/ctx/{z}/{x}/{y}.png');

    const provider = createCtxImageryProvider();
    expect(provider.url).toBe('/api/v1/tiles/ctx/{z}/{x}/{y}.png');
    expect(provider.minimumLevel).toBe(9);
    expect(provider.maximumLevel).toBe(15);
    expect(provider.hasAlphaChannel).toBe(true);
    expect(provider.rectangle).toBeDefined();
    expect(provider.rectangle.west).toBe(77.0399);
    expect(provider.rectangle.south).toBe(17.8815);
    expect(provider.rectangle.east).toBe(77.6199);
    expect(provider.rectangle.north).toBe(18.6541);
  });

  it('validates HiRISE targeted sub-meter zoom levels and landing site footprint', () => {
    const hirise = IMAGERY_TIERS.hirise;
    expect(hirise.minZoom).toBe(13);
    expect(hirise.maxZoom).toBe(18);
    expect(hirise.bounds).toEqual([77.5158, 18.2876, 77.6537, 18.5834]);
    expect(hirise.templateUrl).toBe('/api/v1/tiles/hirise/{z}/{x}/{y}.png');

    const provider = createHiRiseImageryProvider();
    expect(provider.url).toBe('/api/v1/tiles/hirise/{z}/{x}/{y}.png');
    expect(provider.minimumLevel).toBe(13);
    expect(provider.maximumLevel).toBe(18);
    expect(provider.hasAlphaChannel).toBe(true);
    expect(provider.rectangle).toBeDefined();
    expect(provider.rectangle.west).toBe(77.5158);
    expect(provider.rectangle.south).toBe(18.2876);
    expect(provider.rectangle.east).toBe(77.6537);
    expect(provider.rectangle.north).toBe(18.5834);
  });

  it('validates MOLA scientific colormap provider configuration', () => {
    const mola = IMAGERY_TIERS.molaColormap;
    expect(mola.minZoom).toBe(0);
    expect(mola.maxZoom).toBe(7);
    expect(mola.templateUrl).toContain('colormap=terrain');

    const provider = createMolaColormapImageryProvider();
    expect(provider.url).toContain('/api/v1/tiles/cog/{z}/{x}/{y}.png?colormap=terrain');
    expect(provider.minimumLevel).toBe(0);
    expect(provider.maximumLevel).toBe(7);
  });
});
