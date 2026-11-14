import React, { useState } from 'react';
import { X, RefreshCw, Download, ChevronDown, ChevronUp, MapPin } from 'lucide-react';
import { useGlobeStore } from '../store/globeStore';
import { fetchDiscoveredRegions, RegionDiscoveryResponseData, DiscoveredRegionData } from '../lib/advancedApiClient';

export const RegionDiscoveryPanel: React.FC = () => {
  const {
    isRegionDiscoveryOpen,
    setIsRegionDiscoveryOpen,
    cameraLat,
    cameraLon,
    setActiveDiscoveredRegions,
    setCameraPosition,
  } = useGlobeStore();

  const [radiusKm, setRadiusKm] = useState<number>(60);
  const [data, setData] = useState<RegionDiscoveryResponseData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isMinimized, setIsMinimized] = useState<boolean>(false);

  if (!isRegionDiscoveryOpen) return null;

  const handleRunDiscovery = async (targetLat = cameraLat, targetLon = cameraLon) => {
    try {
      setIsLoading(true);
      setErrorMsg(null);
      const res = await fetchDiscoveredRegions(targetLat, targetLon, radiusKm);
      setData(res);
      setActiveDiscoveredRegions(res.regions);
    } catch (e: any) {
      setErrorMsg(e.message || 'Region discovery segmentation failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportGeoJSON = () => {
    if (!data?.geojson) return;
    const blob = new Blob([JSON.stringify(data.geojson, null, 2)], {
      type: 'application/geo+json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `zuhura_mars_regions_${Math.round(cameraLat)}N_${Math.round(cameraLon)}E.geojson`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleFlyToRegion = (reg: DiscoveredRegionData) => {
    setCameraPosition(reg.center_latitude, reg.center_longitude, 80000.0);
  };

  return (
    <div className="fixed top-20 left-4 md:left-20 z-20 w-[min(24rem,calc(100vw-2rem))] overflow-hidden rounded-2xl border border-line bg-surface-subtle text-ink shadow-panel font-sans">
      <div className="flex items-start justify-between gap-3 px-4 py-3.5">
        <div>
          <p className="text-[12px] font-medium text-brand-600">Regions</p>
          <h2 className="text-base font-semibold tracking-tight">Find geologic units</h2>
        </div>
        <div className="flex items-center">
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="rounded-full p-1.5 text-ink-muted hover:bg-surface-muted hover:text-ink"
            aria-label={isMinimized ? 'Expand regions' : 'Collapse regions'}
          >
            {isMinimized ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
          </button>
          <button
            onClick={() => {
              setIsRegionDiscoveryOpen(false);
              setActiveDiscoveredRegions([]);
            }}
            className="rounded-full p-1.5 text-ink-muted hover:bg-surface-muted hover:text-ink"
            aria-label="Close regions"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <div className="max-h-[calc(100vh-9rem)] space-y-4 overflow-y-auto px-4 pb-4">
          <p className="text-sm leading-relaxed text-ink-soft">
            Search around the camera at {cameraLat.toFixed(2)}°N, {cameraLon.toFixed(2)}°E.
          </p>

          <label className="block text-sm">
            <span className="flex items-baseline justify-between text-ink-soft">
              Search radius
              <span className="font-medium tabular-nums text-ink">{radiusKm} km</span>
            </span>
            <input
              type="range"
              min="20"
              max="200"
              step="10"
              value={radiusKm}
              onChange={(e) => setRadiusKm(Number(e.target.value))}
              className="mt-2 w-full accent-brand-600"
            />
          </label>

          <button
            onClick={() => handleRunDiscovery()}
            disabled={isLoading}
            className="w-full rounded-full bg-brand-700 py-2.5 text-sm font-medium text-white hover:bg-brand-800 disabled:opacity-50"
          >
            {isLoading ? (
              <span className="inline-flex items-center justify-center gap-2">
                <RefreshCw className="h-4 w-4 animate-spin" />
                Looking at the terrain
              </span>
            ) : (
              'Find regions'
            )}
          </button>

          {errorMsg && <p className="rounded-xl bg-brand-50 px-3 py-2 text-sm text-brand-600">{errorMsg}</p>}

          {data && (
            <div className="space-y-3 border-t border-line pt-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-ink-soft">{data.total_regions_discovered} units</span>
                <button
                  onClick={handleExportGeoJSON}
                  className="inline-flex items-center gap-1 font-medium text-brand-600 hover:underline"
                >
                  <Download className="h-3.5 w-3.5" />
                  GeoJSON
                </button>
              </div>

              <ul className="divide-y divide-line">
                {data.regions.map((reg) => (
                  <li key={reg.region_id} className="py-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-medium">{reg.name}</p>
                        <p className="text-[12px] text-ink-muted">Provisional unit</p>
                      </div>
                      <p className="shrink-0 text-sm tabular-nums text-ink-soft">{reg.surface_area_km2} km²</p>
                    </div>
                    <p className="mt-2 text-[13px] tabular-nums text-ink-soft">
                      {reg.mean_elevation_m.toFixed(0)} m · slope {reg.mean_slope_degrees.toFixed(1)}° · roughness{' '}
                      {reg.roughness_index_tri.toFixed(1)}
                    </p>
                    <p className="mt-2 text-sm leading-relaxed text-ink-soft">{reg.geological_interpretation}</p>
                    <div className="mt-2 flex items-center justify-between text-[12px]">
                      <span className="text-ink-faint">Confidence {Math.round(reg.confidence_score * 100)}%</span>
                      <button
                        onClick={() => handleFlyToRegion(reg)}
                        className="inline-flex items-center gap-1 font-medium text-ink hover:underline"
                      >
                        <MapPin className="h-3.5 w-3.5" />
                        Center map
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
              <p className="text-[12px] leading-relaxed text-ink-faint">
                Provisional names are for research only. Official IAU names stay as they are.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
