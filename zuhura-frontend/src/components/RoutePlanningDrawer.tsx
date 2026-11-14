import React, { useState } from 'react';
import { Navigation, X, RefreshCw, Download, ChevronDown, ChevronUp, Radio } from 'lucide-react';
import { useGlobeStore } from '../store/globeStore';
import { fetchOptimizedRoute, RoutePlanningResponseData, RouteOptionData } from '../lib/advancedApiClient';
import { buildTraverseCsv, buildTraverseGeoJson, buildTraverseKml, downloadTextFile } from '../lib/routeExport';
import { MOLA_TRANSECT_STATUS, resolveRouteWithElevation } from '../lib/routeFallback';
import { EpistemicBadge } from './EpistemicBadge';

export const RoutePlanningDrawer: React.FC = () => {
  const { isRoutePlannerOpen, setIsRoutePlannerOpen, setActiveNavigationRoute } = useGlobeStore();

  const PRESETS = [
    {
      name: 'Jezero: Touchdown to Western Delta Scarp',
      start: { lat: 18.38, lon: 77.58, name: 'Octavia E. Butler Landing' },
      end: { lat: 18.44, lon: 77.45, name: 'Kodiak Delta Front' },
    },
    {
      name: 'Gale: Bradbury Landing to Mount Sharp Base',
      start: { lat: -4.59, lon: 137.44, name: 'Bradbury Landing Site' },
      end: { lat: -4.68, lon: 137.38, name: 'Vera Rubin Hematite Ridge' },
    },
    {
      name: 'Olympus Mons: Caldera Rim Traverse',
      start: { lat: 18.4, lon: 226.0, name: 'South Caldera Base' },
      end: { lat: 18.65, lon: 226.2, name: 'Summit Caldera Edge' },
    },
  ];

  const [travelMode, setTravelMode] = useState<'land' | 'air'>('land');
  const [activeDetailTab, setActiveDetailTab] = useState<'profile' | 'terramechanics' | 'timeline' | 'comms' | 'risks'>(
    'profile',
  );

  const [startLat, setStartLat] = useState<number>(18.38);
  const [startLon, setStartLon] = useState<number>(77.58);
  const [endLat, setEndLat] = useState<number>(18.44);
  const [endLon, setEndLon] = useState<number>(77.45);
  const [mobilityProfile, setMobilityProfile] = useState<string>('rover_perseverance');
  const [preference, setPreference] = useState<string>('minimum_slope');

  const [routeResult, setRouteResult] = useState<RoutePlanningResponseData | null>(null);
  const [selectedRouteOption, setSelectedRouteOption] = useState<RouteOptionData | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isMinimized, setIsMinimized] = useState<boolean>(false);

  if (!isRoutePlannerOpen) return null;

  const handleComputeRoute = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      let data: RoutePlanningResponseData;
      if (travelMode === 'land') {
        try {
          data = await fetchOptimizedRoute(startLat, startLon, endLat, endLon, mobilityProfile, preference);
        } catch {
          throw new Error('The rover route could not be planned. Check that the backend is running.');
        }
      } else {
        data = await resolveRouteWithElevation(
          { lat: startLat, lon: startLon },
          { lat: endLat, lon: endLon },
          'scout_hexacopter',
        );
        data.recommended_route = {
          ...data.recommended_route,
          name: 'Flight path',
          description:
            'Straight line between the two points, as a helicopter such as Ingenuity would fly. The profile shows the ground below.',
        };
        data.alternative_routes = [];
      }
      setRouteResult(data);
      setSelectedRouteOption(data.recommended_route);
      setActiveNavigationRoute(data.recommended_route);
    } catch (e: unknown) {
      setErrorMsg(e instanceof Error ? e.message : 'Route calculation failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectPreset = (p: (typeof PRESETS)[0]) => {
    setStartLat(p.start.lat);
    setStartLon(p.start.lon);
    setEndLat(p.end.lat);
    setEndLon(p.end.lon);
  };

  const exportBasename = selectedRouteOption
    ? `zuhura_mars_route_${selectedRouteOption.route_id}`
    : 'zuhura_mars_route';

  const handleExportGeoJSON = () => {
    if (!selectedRouteOption) return;
    downloadTextFile(
      `${exportBasename}.geojson`,
      JSON.stringify(buildTraverseGeoJson(selectedRouteOption), null, 2),
      'application/geo+json',
    );
  };

  const handleExportCsv = () => {
    if (!selectedRouteOption) return;
    downloadTextFile(`${exportBasename}.csv`, buildTraverseCsv(selectedRouteOption), 'text/csv');
  };

  const handleExportKml = () => {
    if (!selectedRouteOption) return;
    downloadTextFile(
      `${exportBasename}.kml`,
      buildTraverseKml(selectedRouteOption),
      'application/vnd.google-earth.kml+xml',
    );
  };

  const route = selectedRouteOption;
  const samples = route?.waypoints || [];
  const mobility = route?.mobility_assessment;
  const terramech = mobility?.terramechanics;
  const energy = mobility?.energy;
  const risks = mobility?.risks;
  const solSchedule = mobility?.sample_sol_schedule;

  // SVG Chart rendering
  const svgW = 380;
  const svgH = 80;
  const padL = 35;
  const padR = 15;
  const padT = 10;
  const padB = 20;
  const chartW = svgW - padL - padR;
  const chartH = svgH - padT - padB;

  let pathD = '';
  let areaD = '';
  if (samples.length > 1) {
    const elevs = samples.map((s) => s.elevation_m);
    const minE = Math.min(...elevs);
    const maxE = Math.max(...elevs);
    const rng = Math.max(10, maxE - minE);
    const maxD = samples[samples.length - 1].distance_km || 1;

    const points = samples.map((s) => {
      const x = padL + (s.distance_km / maxD) * chartW;
      const y = padT + (1 - (s.elevation_m - minE) / rng) * chartH;
      return { x, y };
    });

    pathD = points.reduce((acc, p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`), '');
    const bottomY = padT + chartH;
    areaD = `${pathD} L ${points[points.length - 1].x} ${bottomY} L ${points[0].x} ${bottomY} Z`;
  }

  return (
    <div className="fixed top-20 right-4 z-20 w-[min(26rem,calc(100vw-2rem))] bg-surface-subtle border border-line rounded-2xl shadow-panel overflow-hidden font-sans text-ink-soft select-none">
      <div className="flex items-start justify-between gap-3 px-4 py-3.5 bg-white border-b border-line">
        <div>
          <p className="text-[12px] font-medium text-brand-600">Traverse</p>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-semibold tracking-tight text-ink">Plan a route</h2>
            <EpistemicBadge type="SIMULATED" compact />
          </div>
        </div>
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1 text-ink-muted hover:text-ink rounded hover:bg-surface-muted transition-colors"
          >
            {isMinimized ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
          </button>
          <button
            onClick={() => {
              setIsRoutePlannerOpen(false);
              setActiveNavigationRoute(null);
            }}
            className="p-1 text-ink-muted hover:text-ink rounded hover:bg-surface-muted transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <div className="p-3 space-y-3 max-h-[calc(100vh-140px)] overflow-y-auto text-xs">
          {/* Travel mode */}
          <div>
            <p className="mb-1 text-[11px] font-medium text-ink-soft">How will you travel?</p>
            <div className="flex rounded border border-line bg-surface-muted p-0.5 text-[12px]">
              {(['land', 'air'] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => {
                    setTravelMode(mode);
                    setRouteResult(null);
                    setSelectedRouteOption(null);
                    setActiveNavigationRoute(null);
                  }}
                  className={`flex-1 rounded py-1.5 text-center transition-colors ${
                    travelMode === mode ? 'bg-brand-700 font-semibold text-white' : 'text-ink-muted hover:text-ink'
                  }`}
                >
                  {mode === 'land' ? 'Land (rover)' : 'Air (helicopter)'}
                </button>
              ))}
            </div>
          </div>

          {/* Quick Presets */}
          <div className="space-y-1">
            <span className="text-[10px] text-ink-muted block">Exploration Presets</span>
            <div className="flex flex-col gap-1">
              {PRESETS.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSelectPreset(p)}
                  className="text-left px-2 py-1.5 rounded bg-surface-subtle hover:bg-surface-muted border border-line text-[11px] text-ink-soft hover:text-brand-600 truncate transition-colors"
                >
                  {p.name}
                </button>
              ))}
            </div>
          </div>

          {/* Coordinates Inputs */}
          <div className="grid grid-cols-2 gap-2 font-mono text-[11px]">
            <div className="p-2 rounded bg-surface-subtle border border-line space-y-1">
              <span className="text-ink font-bold block">Start (A)</span>
              <div>
                <label className="text-[9px] text-ink-muted block">Lat (°N/S)</label>
                <input
                  type="number"
                  step="0.01"
                  value={startLat}
                  onChange={(e) => setStartLat(Number(e.target.value))}
                  className="w-full bg-white border border-line rounded px-1.5 py-0.5 text-ink"
                />
              </div>
              <div>
                <label className="text-[9px] text-ink-muted block">Lon (°E)</label>
                <input
                  type="number"
                  step="0.01"
                  value={startLon}
                  onChange={(e) => setStartLon(Number(e.target.value))}
                  className="w-full bg-white border border-line rounded px-1.5 py-0.5 text-ink"
                />
              </div>
            </div>

            <div className="p-2 rounded bg-surface-subtle border border-line space-y-1">
              <span className="text-brand-600 font-bold block">End (B)</span>
              <div>
                <label className="text-[9px] text-ink-muted block">Lat (°N/S)</label>
                <input
                  type="number"
                  step="0.01"
                  value={endLat}
                  onChange={(e) => setEndLat(Number(e.target.value))}
                  className="w-full bg-white border border-line rounded px-1.5 py-0.5 text-ink"
                />
              </div>
              <div>
                <label className="text-[9px] text-ink-muted block">Lon (°E)</label>
                <input
                  type="number"
                  step="0.01"
                  value={endLon}
                  onChange={(e) => setEndLon(Number(e.target.value))}
                  className="w-full bg-white border border-line rounded px-1.5 py-0.5 text-ink"
                />
              </div>
            </div>
          </div>

          {travelMode === 'land' ? (
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div>
                <label className="mb-0.5 block text-[10px] text-ink-muted">Vehicle</label>
                <select
                  value={mobilityProfile}
                  onChange={(e) => setMobilityProfile(e.target.value)}
                  className="w-full rounded border border-line bg-white px-2 py-1 text-[11px] text-ink-soft"
                >
                  <option value="rover_perseverance">Perseverance</option>
                  <option value="rover_curiosity">Curiosity</option>
                  <option value="rover_opportunity">Opportunity</option>
                  <option value="rover_zhurong">Zhurong</option>
                  <option value="rover_exomars">Rosalind Franklin (ExoMars)</option>
                  <option value="crew_traverser">Pressurised crew rover</option>
                </select>
              </div>
              <div>
                <label className="mb-0.5 block text-[10px] text-ink-muted">Prefer</label>
                <select
                  value={preference}
                  onChange={(e) => setPreference(e.target.value)}
                  className="w-full rounded border border-line bg-white px-2 py-1 text-[11px] text-ink-soft"
                >
                  <option value="minimum_slope">Gentle slopes (safest)</option>
                  <option value="balanced">Balanced</option>
                  <option value="shortest_distance">Shortest</option>
                </select>
              </div>
            </div>
          ) : (
            <p className="text-[11px] leading-relaxed text-ink-muted">
              A helicopter flies straight over the terrain, so the path is a direct line. The profile shows the ground
              elevation below it.
            </p>
          )}

          <button
            type="button"
            onClick={handleComputeRoute}
            disabled={isLoading}
            className="flex w-full items-center justify-center gap-2 rounded-md bg-brand-700 py-2 font-semibold text-white transition-colors hover:bg-brand-800 disabled:opacity-50"
          >
            {isLoading ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Navigation className="h-3.5 w-3.5" />}
            <span>{isLoading ? 'Planning…' : travelMode === 'land' ? 'Plan rover route' : 'Plan flight path'}</span>
          </button>

          {errorMsg && (
            <div className="p-2 rounded bg-danger-soft border border-danger-line text-danger text-[11px]">
              {errorMsg}
            </div>
          )}

          {/* Single Rover Route Results Display */}
          {route && (
            <div className="space-y-2.5 pt-2 border-t border-line">
              {/* Route Alternative Selector */}
              {routeResult && routeResult.alternative_routes.length > 0 && (
                <div className="flex gap-1.5 font-mono text-[10px]">
                  <button
                    onClick={() => {
                      setSelectedRouteOption(routeResult.recommended_route);
                      setActiveNavigationRoute(routeResult.recommended_route);
                    }}
                    className={`flex-1 py-1 rounded border text-center ${
                      selectedRouteOption?.route_id === routeResult.recommended_route.route_id
                        ? 'bg-brand-50 border-ink text-ink font-bold'
                        : 'bg-surface-subtle border-line text-ink-muted'
                    }`}
                  >
                    Recommended (A*)
                  </button>
                  <button
                    onClick={() => {
                      setSelectedRouteOption(routeResult.alternative_routes[0]);
                      setActiveNavigationRoute(routeResult.alternative_routes[0]);
                    }}
                    className={`flex-1 py-1 rounded border text-center ${
                      selectedRouteOption?.route_id === routeResult.alternative_routes[0].route_id
                        ? 'bg-brand-50 border-brand-600 text-brand-600 font-bold'
                        : 'bg-surface-subtle border-line text-ink-muted'
                    }`}
                  >
                    Direct Alternative
                  </button>
                </div>
              )}

              {/* Summary */}
              {travelMode === 'land' ? (
                <>
                  <div className="grid grid-cols-4 gap-1 font-mono text-[9px]">
                    <div className="p-1.5 rounded bg-surface-subtle border border-line">
                      <span className="text-ink-muted block">Distance</span>
                      <span className="text-ink font-bold">{route.total_distance_km} km</span>
                    </div>
                    <div className="p-1.5 rounded bg-surface-subtle border border-line">
                      <span className="text-ink-muted block">Max slope</span>
                      <span className="text-brand-600 font-bold">{route.max_slope_degrees}°</span>
                    </div>
                    <div className="p-1.5 rounded bg-surface-subtle border border-line">
                      <span className="text-ink-muted block">Est. sols</span>
                      <span className="text-ink font-bold">{mobility?.estimated_duration_sols ?? 1}d</span>
                    </div>
                    <div className="p-1.5 rounded bg-surface-subtle border border-line">
                      <span className="text-ink-muted block">RISK</span>
                      <span className={`font-bold ${risks?.risk_rating === 'BENIGN' ? 'text-ink' : 'text-brand-600'}`}>
                        {risks?.risk_rating || 'NOMINAL'}
                      </span>
                    </div>
                  </div>

                  {/* Detail Tabs Switcher */}
                  <div className="flex bg-white p-0.5 rounded border border-line text-[10px] font-mono">
                    <button
                      onClick={() => setActiveDetailTab('profile')}
                      className={`flex-1 py-0.5 rounded text-center ${
                        activeDetailTab === 'profile' ? 'bg-surface-muted text-ink font-bold' : 'text-ink-muted'
                      }`}
                    >
                      Elevation
                    </button>
                    <button
                      onClick={() => setActiveDetailTab('terramechanics')}
                      className={`flex-1 py-0.5 rounded text-center ${
                        activeDetailTab === 'terramechanics' ? 'bg-surface-muted text-ink font-bold' : 'text-ink-muted'
                      }`}
                    >
                      Soil
                    </button>
                    <button
                      onClick={() => setActiveDetailTab('timeline')}
                      className={`flex-1 py-0.5 rounded text-center ${
                        activeDetailTab === 'timeline' ? 'bg-surface-muted text-brand-600 font-bold' : 'text-ink-muted'
                      }`}
                    >
                      Sol
                    </button>
                    <button
                      onClick={() => setActiveDetailTab('comms')}
                      className={`flex-1 py-0.5 rounded text-center ${
                        activeDetailTab === 'comms' ? 'bg-surface-muted text-brand-600 font-bold' : 'text-ink-muted'
                      }`}
                    >
                      Comms
                    </button>
                    <button
                      onClick={() => setActiveDetailTab('risks')}
                      className={`flex-1 py-0.5 rounded text-center ${
                        activeDetailTab === 'risks' ? 'bg-surface-muted text-brand-600 font-bold' : 'text-ink-muted'
                      }`}
                    >
                      Risks
                    </button>
                  </div>
                </>
              ) : (
                <div className="grid grid-cols-2 gap-1 text-[11px]">
                  <div className="rounded border border-line bg-surface-subtle p-1.5">
                    <span className="block text-ink-muted">Distance</span>
                    <span className="font-semibold text-ink">{route.total_distance_km} km</span>
                  </div>
                  <div className="rounded border border-line bg-surface-subtle p-1.5">
                    <span className="block text-ink-muted">Ground elevation change</span>
                    <span className="font-semibold text-ink">
                      +{Math.round(route.elevation_gain_m)} m / −{Math.round(route.elevation_loss_m)} m
                    </span>
                  </div>
                </div>
              )}

              {/* Tab 1: Elevation Profile */}
              {(activeDetailTab === 'profile' || travelMode === 'air') && pathD && (
                <div className="p-2 rounded bg-surface-muted border border-line space-y-1">
                  <div className="flex justify-between text-[10px] font-mono text-ink-muted">
                    <span>Route Elevation Profile</span>
                    <span>
                      ΔElev: +{route.elevation_gain_m}m / -{route.elevation_loss_m}m
                    </span>
                  </div>
                  <svg width="100%" height={svgH} viewBox={`0 0 ${svgW} ${svgH}`} className="overflow-visible">
                    <path d={areaD} fill="rgba(143, 61, 44, 0.12)" />
                    <path d={pathD} fill="none" stroke="#014166" strokeWidth="2" />
                  </svg>
                </div>
              )}

              {/* Tab 2: Bekker Terramechanics */}
              {travelMode === 'land' && activeDetailTab === 'terramechanics' && terramech && (
                <div className="p-2 rounded bg-surface-muted border border-line space-y-1.5 font-mono text-[10px]">
                  <div className="text-ink font-bold text-[11px] flex items-center justify-between">
                    <span>Soil mechanics (Bekker–Wong)</span>
                    <span className="text-ink-muted text-[9px] uppercase">{terramech.regolith_type_used}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-1.5">
                    <div className="p-1 rounded bg-white border border-line">
                      <span className="text-ink-muted block text-[9px]">Wheel slip</span>
                      <span className="text-brand-600 font-bold text-xs">{terramech.estimated_wheel_slip_pct}%</span>
                    </div>
                    <div className="p-1 rounded bg-white border border-line">
                      <span className="text-ink-muted block text-[9px]">Sinkage</span>
                      <span className="text-ink font-bold text-xs">{terramech.sinkage_depth_cm} cm</span>
                    </div>
                    <div className="p-1 rounded bg-white border border-line">
                      <span className="text-ink-muted block text-[9px]">Motion resistance</span>
                      <span className="text-ink-soft font-bold">{terramech.bekker_motion_resistance_n || 0} N</span>
                    </div>
                    <div className="p-1 rounded bg-white border border-line">
                      <span className="text-ink-muted block text-[9px]">Tractive thrust</span>
                      <span className="text-ink-soft font-bold">{terramech.tractive_effort_n || 0} N</span>
                    </div>
                    <div className="p-1 rounded bg-white border border-line">
                      <span className="text-ink-muted block text-[9px]">Energy</span>
                      <span className="text-brand-600 font-bold">{energy?.total_energy_wh || 0} Wh</span>
                    </div>
                    <div className="p-1 rounded bg-white border border-line">
                      <span className="text-ink-muted block text-[9px]">Energy rate</span>
                      <span className="text-ink-soft font-bold">{energy?.energy_rate_wh_per_km || 0} Wh/km</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center pt-1 border-t border-line text-[9px]">
                    <span className="text-ink-muted">
                      Shear Risk: <span className="font-bold text-ink-soft">{terramech.soil_shear_risk}</span>
                    </span>
                    <span className="text-ink-muted">
                      Entrapment Risk:{' '}
                      <span className="font-bold text-brand-600">{terramech.entrapment_risk_pct}%</span>
                    </span>
                  </div>
                </div>
              )}

              {/* Tab 3: Sol-by-Sol Timeline */}
              {travelMode === 'land' && activeDetailTab === 'timeline' && solSchedule && (
                <div className="p-2 rounded bg-surface-muted border border-line space-y-1.5 font-mono text-[10px]">
                  <div className="flex justify-between items-center text-brand-600 font-bold text-[11px]">
                    <span>SOL {solSchedule.sol_number} SCHEDULE (LMST)</span>
                    <span className="text-ink-muted text-[9px]">Drive: {solSchedule.drive_distance_m}m</span>
                  </div>
                  <div className="space-y-1 max-h-40 overflow-y-auto">
                    {solSchedule.events.map((ev, idx) => (
                      <div key={idx} className="p-1.5 rounded bg-white border border-line space-y-0.5">
                        <div className="flex justify-between text-[9px] text-ink-muted">
                          <span className="text-ink font-bold">{ev.time_window_lmst}</span>
                          <span className="text-ink-faint">{ev.power_draw_w.toFixed(0)}W draw</span>
                        </div>
                        <div className="font-sans font-medium text-ink-soft">{ev.phase_name.replace(/_/g, ' ')}</div>
                        <div className="text-[9px] text-ink-muted font-sans">{ev.description}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tab 4: Comms Windows */}
              {travelMode === 'land' && activeDetailTab === 'comms' && solSchedule && (
                <div className="p-2 rounded bg-surface-muted border border-line space-y-1.5 font-mono text-[10px]">
                  <div className="flex justify-between items-center text-brand-600 font-bold text-[11px]">
                    <span>Orbiter and DTE passes</span>
                    <Radio className="w-3.5 h-3.5 text-brand-600" />
                  </div>
                  <div className="space-y-1">
                    {solSchedule.communication_passes.map((p, idx) => (
                      <div
                        key={idx}
                        className="p-1.5 rounded bg-white border border-line flex justify-between items-center text-[9px]"
                      >
                        <div>
                          <span className="font-bold text-ink block">
                            {p.target} ({p.pass_type === 'ORBITER_RELAY' ? 'Relay' : 'DTE'})
                          </span>
                          <span className="text-ink-muted">
                            {p.start_time_lmst} - {p.end_time_lmst} LMST ({p.duration_minutes}m)
                          </span>
                        </div>
                        <div className="text-right">
                          <span className="text-ink font-bold block">{p.data_capacity_mbit} Mbit</span>
                          <span className="text-ink-faint">{p.frequency_band.split(' ')[0]}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tab 5: Traverse Risks */}
              {travelMode === 'land' && activeDetailTab === 'risks' && risks && (
                <div className="p-2 rounded bg-surface-muted border border-line space-y-1.5 font-mono text-[10px]">
                  <div className="flex justify-between items-center text-brand-600 font-bold text-[11px]">
                    <span>Risk</span>
                    <span className="px-1.5 py-0.5 rounded bg-brand-50 border border-brand-200 text-brand-600 text-[9px]">
                      {risks.risk_rating} ({risks.composite_risk}/100)
                    </span>
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between text-[9px]">
                      <span className="text-ink-muted">Rollover / Tipping:</span>
                      <span className="text-ink-soft font-bold">{risks.tipping_risk}%</span>
                    </div>
                    <div className="w-full bg-surface-muted h-1 rounded overflow-hidden">
                      <div className="bg-brand-700 h-full" style={{ width: `${risks.tipping_risk}%` }} />
                    </div>

                    <div className="flex justify-between text-[9px] pt-1">
                      <span className="text-ink-muted">High-Centering:</span>
                      <span className="text-ink-soft font-bold">{risks.high_centering_risk}%</span>
                    </div>
                    <div className="w-full bg-surface-muted h-1 rounded overflow-hidden">
                      <div className="bg-brand-700 h-full" style={{ width: `${risks.high_centering_risk}%` }} />
                    </div>

                    <div className="flex justify-between text-[9px] pt-1">
                      <span className="text-ink-muted">Sinkage Entrapment:</span>
                      <span className="text-ink-soft font-bold">{risks.sinkage_entrapment_risk}%</span>
                    </div>
                    <div className="w-full bg-surface-muted h-1 rounded overflow-hidden">
                      <div className="bg-brand-700 h-full" style={{ width: `${risks.sinkage_entrapment_risk}%` }} />
                    </div>

                    <div className="flex justify-between text-[9px] pt-1">
                      <span className="text-ink-muted">Thermal Deficit:</span>
                      <span className="text-ink-soft font-bold">{risks.thermal_deficit_risk}%</span>
                    </div>
                    <div className="w-full bg-surface-muted h-1 rounded overflow-hidden">
                      <div className="bg-brand-700 h-full" style={{ width: `${risks.thermal_deficit_risk}%` }} />
                    </div>
                  </div>
                </div>
              )}

              {(routeResult?.is_synthetic || selectedRouteOption?.is_synthetic) && (
                <div className="px-2 py-1.5 rounded border border-brand-200 bg-brand-50 text-[10px] text-brand-600 font-mono leading-snug">
                  Elevations are estimated because the elevation service is unavailable.
                </div>
              )}
              {routeResult?.status === MOLA_TRANSECT_STATUS && (
                <div className="px-2 py-1.5 rounded border border-line bg-surface-subtle text-[10px] text-ink-soft font-mono leading-snug">
                  Ground elevations sampled from MOLA along the straight flight line.
                </div>
              )}

              <div className="grid grid-cols-3 gap-1.5">
                <button
                  onClick={handleExportGeoJSON}
                  className="py-1.5 rounded bg-surface-muted hover:bg-surface-muted border border-line text-[10px] font-mono text-ink-soft flex items-center justify-center space-x-1 transition-colors"
                >
                  <Download className="w-3 h-3 text-brand-600" />
                  <span>GeoJSON</span>
                </button>
                <button
                  onClick={handleExportCsv}
                  className="py-1.5 rounded bg-surface-muted hover:bg-surface-muted border border-line text-[10px] font-mono text-ink-soft flex items-center justify-center space-x-1 transition-colors"
                >
                  <Download className="w-3 h-3 text-brand-600" />
                  <span>CSV</span>
                </button>
                <button
                  onClick={handleExportKml}
                  className="py-1.5 rounded bg-surface-muted hover:bg-surface-muted border border-line text-[10px] font-mono text-ink-soft flex items-center justify-center space-x-1 transition-colors"
                >
                  <Download className="w-3 h-3 text-brand-600" />
                  <span>KML</span>
                </button>
              </div>

              <p className="text-[9px] text-ink-faint italic leading-tight">
                * Autonomous mission simulation. Not certified for flight operations without manual traversability
                verification.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
