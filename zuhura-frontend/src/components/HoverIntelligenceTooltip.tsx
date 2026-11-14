import React, { useEffect, useRef, useState } from 'react';
import { Pin, Activity } from 'lucide-react';
import { useGlobeStore } from '../store/globeStore';
import { useWorkspaceStore } from '../store/workspaceStore';
import { getHoverPlaceDescription, nearestHoverLandmarks, HoverPlaceInfo } from '../lib/hoverData';
import { fetchHoverInspection, HoverInspectionData } from '../lib/advancedApiClient';

type InspectorTab = 'overview' | 'terrain' | 'landmarks';

export const HoverIntelligenceTooltip: React.FC = () => {
  const {
    cursorLat,
    cursorLon,
    cursorElevation,
    isHoverIntelligenceEnabled,
    activeMainView,
    setCameraPosition,
    setIsXRayMarsOpen,
    isRoutePlannerOpen,
    isRegionDiscoveryOpen,
    isPinpointOpen,
    isXRayMarsOpen,
  } = useGlobeStore();
  const addBookmark = useWorkspaceStore((state) => state.addBookmark);

  const [instantInfo, setInstantInfo] = useState<HoverPlaceInfo | null>(null);
  const [backendData, setBackendData] = useState<HoverInspectionData | null>(null);
  const [tab, setTab] = useState<InspectorTab>('overview');
  const [pinned, setPinned] = useState(false);
  const holdRef = useRef(false);
  const backendTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (holdRef.current) return;
    if (!isHoverIntelligenceEnabled || cursorLat === null || cursorLon === null) {
      setInstantInfo(null);
      setBackendData(null);
      return;
    }

    setPinned(false);
    setInstantInfo(getHoverPlaceDescription(cursorLat, cursorLon, cursorElevation ?? undefined));

    if (backendTimerRef.current) clearTimeout(backendTimerRef.current);
    const lat = cursorLat;
    const lon = cursorLon;
    backendTimerRef.current = setTimeout(async () => {
      try {
        const res = await fetchHoverInspection(lat, lon);
        if (!holdRef.current) setBackendData(res);
      } catch {
        if (!holdRef.current) setBackendData(null);
      }
    }, 180);

    return () => {
      if (backendTimerRef.current) clearTimeout(backendTimerRef.current);
    };
  }, [cursorLat, cursorLon, cursorElevation, isHoverIntelligenceEnabled]);

  const toolCoversTheGlobe = isRoutePlannerOpen || isRegionDiscoveryOpen || isPinpointOpen || isXRayMarsOpen;

  if (
    activeMainView !== 'explorer' ||
    !isHoverIntelligenceEnabled ||
    toolCoversTheGlobe ||
    !instantInfo ||
    cursorLat === null ||
    cursorLon === null
  ) {
    return null;
  }

  const latStr = `${Math.abs(cursorLat).toFixed(2)}°${cursorLat >= 0 ? 'N' : 'S'}`;
  const lonStr = `${(((cursorLon % 360) + 360) % 360).toFixed(2)}°E`;
  const currentElevation = backendData?.elevation_m ?? cursorElevation ?? instantInfo.elevation_m;
  const elevStr = `${currentElevation >= 0 ? '+' : ''}${Math.round(currentElevation).toLocaleString()} m`;
  const landmarks = nearestHoverLandmarks(cursorLat, cursorLon, 4);
  const slope = backendData?.slope_degrees;

  const hold = () => {
    holdRef.current = true;
  };
  const release = () => {
    holdRef.current = false;
  };

  const pinLocation = () => {
    addBookmark({
      name: instantInfo.name,
      lat: cursorLat,
      lon: cursorLon,
      elevation_m: Math.round(currentElevation),
      geological_context: instantInfo.description,
      tags: [instantInfo.category],
    });
    setPinned(true);
  };

  return (
    <div
      onMouseEnter={hold}
      onMouseLeave={release}
      className="location-rise fixed bottom-28 right-4 z-20 w-[min(26rem,calc(100vw-2rem))] rounded-2xl border border-line bg-surface-subtle text-ink shadow-2xl font-sans select-none"
    >
      <div className="px-4 pt-3.5 pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h4 className="text-[15px] font-semibold leading-snug tracking-tight text-ink truncate">
              {instantInfo.name}
            </h4>
            <p className="mt-1 text-[12px] text-ink">
              {latStr}, {lonStr}
              <span className="mx-1.5 text-ink">·</span>
              {elevStr}
            </p>
          </div>
          <span className="shrink-0 rounded-full bg-surface-muted px-2 py-1 text-[10px] text-ink">
            {instantInfo.category}
          </span>
        </div>

        <div className="mt-3 flex gap-1 rounded-full bg-surface-muted p-1 text-[11px]">
          {(
            [
              ['overview', 'Overview'],
              ['terrain', 'Terrain & Elevation'],
              ['landmarks', 'Nearby Landmarks'],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              onClick={() => setTab(id)}
              className={`flex-1 rounded-full px-2 py-1 transition-colors ${
                tab === id ? 'bg-white text-ink font-medium' : 'text-ink hover:text-ink'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="px-4 pb-3 min-h-[92px] text-[13px] leading-relaxed text-ink">
        {tab === 'overview' && (
          <div className="space-y-2">
            <p>{instantInfo.description}</p>
            <p className="text-[12px] text-ink">
              {backendData?.geological_era || instantInfo.geologicalEra}
              {backendData?.solar_status ? ` · Sun ${backendData.solar_status.solar_elevation_deg}°` : ''}
            </p>
          </div>
        )}

        {tab === 'terrain' && (
          <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-[12px]">
            <div>
              <dt className="text-ink">Elevation</dt>
              <dd className="text-ink font-medium tabular-nums">{elevStr}</dd>
            </div>
            <div>
              <dt className="text-ink">Datum</dt>
              <dd className="text-ink">{backendData?.vertical_datum || 'MOLA areoid'}</dd>
            </div>
            <div>
              <dt className="text-ink">Slope</dt>
              <dd className="text-ink font-medium tabular-nums">
                {slope !== undefined && slope !== null ? `${slope.toFixed(1)}°` : 'Sampling…'}
              </dd>
            </div>
            <div>
              <dt className="text-ink">Surface</dt>
              <dd className="text-ink">{backendData?.surface_description || instantInfo.category}</dd>
            </div>
          </dl>
        )}

        {tab === 'landmarks' && (
          <ul className="space-y-1.5">
            {landmarks.map((place) => (
              <li key={place.id}>
                <button
                  type="button"
                  onClick={() => setCameraPosition(place.lat, place.lon, 180000)}
                  className="flex w-full items-baseline justify-between gap-3 rounded-lg px-2 py-1.5 text-left hover:bg-surface-muted"
                >
                  <span className="min-w-0">
                    <span className="block truncate text-ink">{place.name}</span>
                    <span className="block truncate text-[11px] text-ink">{place.type}</span>
                  </span>
                  <span className="shrink-0 text-[11px] tabular-nums text-ink">
                    {place.distance_km < 1 ? '<1 km' : `${Math.round(place.distance_km)} km`}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="flex items-center justify-end gap-2 border-t border-line px-3 py-2.5">
        <button
          type="button"
          onClick={pinLocation}
          className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[12px] text-ink hover:bg-surface-muted"
        >
          <Pin className="w-3.5 h-3.5" />
          {pinned ? 'Pinned' : 'Pin Location'}
        </button>
        <button
          type="button"
          onClick={() => setIsXRayMarsOpen(true)}
          className="inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1.5 text-[12px] font-medium text-ink hover:bg-surface-muted"
        >
          <Activity className="w-3.5 h-3.5" />
          Analyze in X-Ray
        </button>
      </div>
    </div>
  );
};
