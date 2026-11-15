import React, { useEffect, useState } from 'react';
import { X, RefreshCw, TrendingUp, Pin } from 'lucide-react';
import { useGlobeStore } from '../store/globeStore';
import { useTerrainAnalysisStore } from '../store/terrainAnalysisStore';
import { useWorkspaceStore } from '../store/workspaceStore';
import { fetchPointAnalysis, PointAnalysisResult } from '../lib/terrainApiClient';
import { nearestHoverLandmarks } from '../lib/hoverData';
import { EpistemicBadge } from './EpistemicBadge';

export const FeatureInspector: React.FC = () => {
  const { selectedFeature, setSelectedFeature, setCameraPosition } = useGlobeStore();
  const { setIsTransectMode, setTransectStart, executeTransectQuery } = useTerrainAnalysisStore();
  const addBookmark = useWorkspaceStore((state) => state.addBookmark);

  const [liveElevation, setLiveElevation] = useState<number | null>(null);
  const [pointData, setPointData] = useState<PointAnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [pinned, setPinned] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'terrain' | 'landmarks'>('overview');

  useEffect(() => {
    if (!selectedFeature) return;
    setPinned(false);
    setLiveElevation(selectedFeature.elevation_m);

    const fetchAnalysis = async () => {
      try {
        setLoading(true);
        const data = await fetchPointAnalysis(selectedFeature.latitude, selectedFeature.longitude, 3, true);
        setPointData(data);
        if (data.elevation?.elevation_m !== null && data.elevation?.elevation_m !== undefined) {
          setLiveElevation(data.elevation.elevation_m);
        }
      } catch (e) {
        console.warn('Feature terrain intelligence query fallback:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalysis();
  }, [selectedFeature]);

  if (!selectedFeature) return null;

  const displayElev = liveElevation ?? selectedFeature.elevation_m;

  const handleProfileFromHere = () => {
    setIsTransectMode(true);
    setTransectStart({
      latitude: selectedFeature.latitude,
      longitude: selectedFeature.longitude,
    });
    executeTransectQuery();
  };

  const landmarks = nearestHoverLandmarks(selectedFeature.latitude, selectedFeature.longitude, 4);

  const pinLocation = () => {
    addBookmark({
      name: selectedFeature.name,
      lat: selectedFeature.latitude,
      lon: selectedFeature.longitude,
      elevation_m: Math.round(displayElev),
      geological_context: selectedFeature.description,
      tags: [selectedFeature.type],
    });
    setPinned(true);
  };

  return (
    <div className="location-rise fixed bottom-28 left-4 md:left-20 z-20 w-[min(26rem,calc(100vw-2rem))] rounded-2xl border border-line bg-surface-subtle text-ink shadow-2xl font-sans select-none">
      <div className="px-4 pt-3.5 pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="truncate text-[15px] font-semibold tracking-tight text-ink">{selectedFeature.name}</h3>
              <EpistemicBadge type="OBSERVED" datasetId="VIKING_MDIM_21" compact />
            </div>
            <p className="mt-1 text-[12px] text-ink">
              {selectedFeature.latitude.toFixed(2)}°N, {selectedFeature.longitude.toFixed(2)}°E
              <span className="mx-1.5 text-ink">·</span>
              {selectedFeature.type}
            </p>
          </div>
          <button
            onClick={() => setSelectedFeature(null)}
            className="rounded-full p-1 text-ink hover:bg-surface-muted hover:text-ink"
            aria-label="Close place card"
          >
            <X className="w-4 h-4" />
          </button>
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
              onClick={() => setActiveTab(id)}
              className={`flex-1 rounded-full px-2 py-1 transition-colors ${
                activeTab === id ? 'bg-white text-ink font-medium' : 'text-ink hover:text-ink'
              }`}
            >
              {label}
              {id === 'terrain' && loading && <RefreshCw className="ml-1 inline h-3 w-3 animate-spin" />}
            </button>
          ))}
        </div>
      </div>

      <div className="px-4 pb-3 min-h-[92px] text-[13px] leading-relaxed text-ink">
        {activeTab === 'overview' && (
          <div className="space-y-2">
            <p>{selectedFeature.description}</p>
            <p className="text-[12px] text-ink">
              Extent {selectedFeature.diameter_km} km
              <span className="mx-1.5 text-ink">·</span>
              {displayElev > 0 ? '+' : ''}
              {displayElev.toLocaleString()} m
            </p>
          </div>
        )}

        {activeTab === 'terrain' && (
          <div className="space-y-2 text-[12px]">
            <div className="flex items-center justify-between text-ink">
              <span>MOLA areoid</span>
              <EpistemicBadge type="MEASURED" uncertainty="±1m" datasetId="MOLA_MEG128" compact />
            </div>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-2">
              <div>
                <dt className="text-ink">Elevation</dt>
                <dd className="font-medium text-ink tabular-nums">
                  {displayElev > 0 ? '+' : ''}
                  {displayElev.toLocaleString()} m
                </dd>
              </div>
              <div>
                <dt className="text-ink">Slope</dt>
                <dd className="font-medium text-ink tabular-nums">
                  {pointData?.derivatives?.slope_deg != null ? `${pointData.derivatives.slope_deg.toFixed(2)}°` : 'N/A'}
                </dd>
              </div>
              <div>
                <dt className="text-ink">Aspect</dt>
                <dd className="font-medium text-ink">
                  {pointData?.derivatives?.aspect_deg != null
                    ? `${pointData.derivatives.aspect_deg.toFixed(1)}° ${pointData.derivatives.aspect_cardinal ?? ''}`
                    : 'N/A'}
                </dd>
              </div>
              <div>
                <dt className="text-ink">Roughness</dt>
                <dd className="font-medium text-ink tabular-nums">
                  {pointData?.morphometry?.tri_roughness_m != null
                    ? `${pointData.morphometry.tri_roughness_m.toFixed(1)} m`
                    : 'N/A'}
                </dd>
              </div>
              <div className="col-span-2">
                <dt className="text-ink">Landform</dt>
                <dd className="text-ink">
                  {pointData?.morphometry?.tpi_classification?.replace(/_/g, ' ') || 'N/A'}
                  <span className="text-ink">
                    {' '}
                    · relief {pointData?.morphometry?.local_relief_m ?? '--'} m · ±
                    {pointData?.elevation?.vertical_accuracy_m ?? 1} m
                  </span>
                </dd>
              </div>
            </dl>
          </div>
        )}

        {activeTab === 'landmarks' && (
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

      <div className="flex items-center justify-between gap-2 border-t border-line px-3 py-2.5">
        <button
          type="button"
          onClick={handleProfileFromHere}
          className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1.5 text-[12px] text-ink hover:bg-surface-muted"
        >
          <TrendingUp className="w-3.5 h-3.5" />
          Profile
        </button>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={pinLocation}
            className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[12px] text-ink hover:bg-surface-muted"
          >
            <Pin className="w-3.5 h-3.5" />
            {pinned ? 'Pinned' : 'Pin Location'}
          </button>
        </div>
      </div>
    </div>
  );
};
