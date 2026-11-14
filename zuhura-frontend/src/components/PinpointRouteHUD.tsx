import React from 'react';
import { Navigation, MapPin, Flag, RotateCcw, X, Download, Truck, Sparkles } from 'lucide-react';
import { useGlobeStore } from '../store/globeStore';
import { fetchOptimizedRoute } from '../lib/advancedApiClient';
import { buildTraverseGeoJson, downloadTextFile } from '../lib/routeExport';
import { resolveRouteWithElevation } from '../lib/routeFallback';

export const PinpointRouteHUD: React.FC = () => {
  const {
    isPinpointNavigationMode,
    pinpointStep,
    departurePoint,
    arrivalPoint,
    activeNavigationRoute,
    selectedVehicleProfile,
    setPinpointNavigationMode,
    setPinpointStep,
    clearPinpointRoute,
    setActiveNavigationRoute,
    setSelectedVehicleProfile,
  } = useGlobeStore();

  if (!isPinpointNavigationMode) return null;

  const routeDetails = activeNavigationRoute?.recommended_route || activeNavigationRoute;

  const handleProfileChange = async (profile: string) => {
    setSelectedVehicleProfile(profile);
    if (departurePoint && arrivalPoint) {
      setPinpointStep('routing');
      try {
        const res = await fetchOptimizedRoute(
          departurePoint.lat,
          departurePoint.lon,
          arrivalPoint.lat,
          arrivalPoint.lon,
          profile,
        );
        setActiveNavigationRoute(res);
        setPinpointStep('route_ready');
      } catch {
        const fallback = await resolveRouteWithElevation(departurePoint, arrivalPoint, profile);
        setActiveNavigationRoute(fallback);
        setPinpointStep('route_ready');
      }
    }
  };

  const routeIsSynthetic = Boolean(activeNavigationRoute?.is_synthetic || routeDetails?.is_synthetic);

  const handleExportGeoJSON = () => {
    if (!routeDetails?.waypoints) return;
    downloadTextFile(
      `zuhura-traverse-${Date.now()}.geojson`,
      JSON.stringify(buildTraverseGeoJson(routeDetails), null, 2),
      'application/geo+json',
    );
  };

  return (
    <>
      {/* Top Floating Instruction Banner */}
      <div className="absolute top-16 left-1/2 -translate-x-1/2 z-10 flex items-center space-x-3 px-4 py-2 rounded bg-white border border-line-strong shadow-2xl text-xs font-mono select-none">
        {pinpointStep === 'select_departure' && (
          <div className="flex items-center space-x-2 text-success">
            <span className="w-2 h-2 rounded-full bg-success " />
            <MapPin className="w-4 h-4 text-success" />
            <span className="text-ink font-bold tracking-wider">Step 1:</span>
            <span className="text-success">Click anywhere on the Mars surface to pinpoint DEPARTURE</span>
          </div>
        )}

        {pinpointStep === 'select_arrival' && (
          <div className="flex items-center space-x-2 text-brand-600">
            <span className="w-2 h-2 rounded-full bg-brand-700 " />
            <Flag className="w-4 h-4 text-brand-600" />
            <span className="text-ink font-bold tracking-wider">Step 2:</span>
            <span className="text-ink">Departure pinned. Click Mars surface to pinpoint ARRIVAL coordinate</span>
          </div>
        )}

        {pinpointStep === 'routing' && (
          <div className="flex items-center space-x-2 text-warning">
            <span className="w-2 h-2 rounded-full bg-warning animate-spin" />
            <Sparkles className="w-4 h-4 text-warning" />
            <span>Calculating MOLA DEM terramechanics path & energy slope...</span>
          </div>
        )}

        {pinpointStep === 'route_ready' && (
          <div className="flex items-center space-x-2 text-brand-600">
            <Navigation className="w-4 h-4 text-brand-600" />
            <span className="text-ink font-bold tracking-wider">Route found:</span>
            <span className="text-ink-soft font-mono">
              {routeDetails?.total_distance_km?.toFixed(1) || '0.0'} km traverse
            </span>
          </div>
        )}

        {/* Exit Mode Button */}
        <button
          onClick={() => {
            clearPinpointRoute();
            setPinpointNavigationMode(false);
          }}
          className="ml-3 pl-3 border-l border-line text-ink-muted hover:text-ink transition-colors"
          title="Exit Pinpoint Navigation"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Route Intelligence Details Card */}
      {(pinpointStep === 'route_ready' || departurePoint) && (
        <div className="absolute top-28 left-20 z-10 w-84 bg-white border border-line-strong rounded shadow-2xl p-4 font-sans text-ink select-none">
          <div className="flex items-center justify-between pb-2.5 border-b border-line">
            <div className="flex items-center space-x-2 text-brand-600 text-xs font-bold">
              <Navigation className="w-4 h-4 text-brand-600" />
              <span>Pinpoint Traverse HUD</span>
            </div>
            <button
              onClick={clearPinpointRoute}
              className="flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono bg-surface-subtle hover:bg-surface-muted border border-line text-ink-soft transition-colors"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset</span>
            </button>
          </div>

          {/* Departure & Arrival Summary */}
          <div className="mt-3 space-y-2 text-xs">
            {departurePoint && (
              <div className="p-2.5 rounded-lg bg-success-soft border border-success-line flex items-start space-x-2">
                <MapPin className="w-4 h-4 text-success shrink-0 mt-0.5" />
                <div className="min-w-0">
                  <div className="text-[10px] text-success font-bold">Departure (Start)</div>
                  <div className="font-semibold text-ink truncate">{departurePoint.name}</div>
                  <div className="text-[10px] font-mono text-ink-muted">
                    {departurePoint.lat.toFixed(2)}°, {departurePoint.lon.toFixed(2)}° |{' '}
                    {Math.round(departurePoint.elevation_m)} m
                  </div>
                </div>
              </div>
            )}

            {arrivalPoint ? (
              <div className="p-2.5 rounded-lg bg-danger-soft border border-danger-line flex items-start space-x-2">
                <Flag className="w-4 h-4 text-danger shrink-0 mt-0.5" />
                <div className="min-w-0">
                  <div className="text-[10px] text-danger font-bold">Arrival (Target)</div>
                  <div className="font-semibold text-ink truncate">{arrivalPoint.name}</div>
                  <div className="text-[10px] font-mono text-ink-muted">
                    {arrivalPoint.lat.toFixed(2)}°, {arrivalPoint.lon.toFixed(2)}° |{' '}
                    {Math.round(arrivalPoint.elevation_m)} m
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-2.5 rounded-lg bg-surface-muted border border-dashed border-line text-ink-muted text-[11px] text-center font-mono">
                Click on the Mars globe to select Arrival target...
              </div>
            )}
          </div>

          {/* Route Metrics when route is ready */}
          {routeDetails && (
            <div className="mt-3 pt-3 border-t border-line space-y-2.5">
              {routeIsSynthetic && (
                <div className="px-2 py-1.5 rounded border border-warning-line bg-warning-soft text-[10px] text-warning font-mono leading-snug">
                  Elevations are estimated because the elevation service is unavailable.
                </div>
              )}
              <div className="grid grid-cols-3 gap-2 text-center font-mono">
                <div className="p-2 rounded bg-surface-subtle border border-line">
                  <div className="text-[9px] text-ink-muted uppercase tracking-wider">Distance</div>
                  <div className="text-sm font-bold text-warning">{routeDetails.total_distance_km.toFixed(1)} km</div>
                </div>
                <div className="p-2 rounded bg-surface-subtle border border-line">
                  <div className="text-[9px] text-ink-muted uppercase tracking-wider">Climb</div>
                  <div className="text-sm font-bold text-success">
                    +{Math.round(routeDetails.elevation_gain_m || 0)} m
                  </div>
                </div>
                <div className="p-2 rounded bg-surface-subtle border border-line">
                  <div className="text-[9px] text-ink-muted uppercase tracking-wider">Detour</div>
                  <div className="text-sm font-bold text-brand-600">
                    {routeDetails.detour_factor?.toFixed(2) || '1.08'}x
                  </div>
                </div>
              </div>

              {/* Vehicle Profile Selector */}
              <div className="space-y-1">
                <label className="text-[10px] text-ink-muted flex items-center space-x-1">
                  <Truck className="w-3 h-3 text-brand-600" />
                  <span>Rover Terramechanics Profile</span>
                </label>
                <select
                  value={selectedVehicleProfile}
                  onChange={(e) => handleProfileChange(e.target.value)}
                  className="w-full bg-surface-subtle border border-line rounded px-2 py-1 text-xs text-ink font-mono focus:outline-none focus:border-brand-600"
                >
                  <option value="rover_perseverance">Perseverance / Curiosity (Max 25° Slope)</option>
                  <option value="rover_scout">Scout Rover (Agile, Max 30° Slope)</option>
                  <option value="transporter_heavy">Heavy Habitat Transporter (Max 15° Slope)</option>
                  <option value="rover_crew">Pressurized Crew Rover (Max 20° Slope)</option>
                </select>
              </div>

              {/* Export GeoJSON Button */}
              <button
                onClick={handleExportGeoJSON}
                className="w-full py-1.5 px-3 rounded bg-brand-50 hover:bg-brand-50 border border-brand-200 text-brand-600 text-xs font-mono font-semibold flex items-center justify-center space-x-1.5 transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export Traverse GeoJSON</span>
              </button>
            </div>
          )}
        </div>
      )}
    </>
  );
};
