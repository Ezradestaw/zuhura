import React, { useEffect, useState } from 'react';
import { Crosshair, Download, Loader2, X } from 'lucide-react';
import { useGlobeStore, type RoutePoint } from '../store/globeStore';
import { findPath, type AStarRoute, type Vehicle } from '../lib/traverse';
import { buildTraverseCsv, buildTraverseGeoJson, buildTraverseKml, downloadTextFile } from '../lib/routeExport';

const VEHICLES: { id: Vehicle; label: string; hint: string }[] = [
  { id: 'car', label: 'Car', hint: 'Slopes up to 10°, smooth ground only' },
  { id: 'rover', label: 'Rover', hint: 'Slopes up to 20°, tolerates rougher ground' },
];

function formatPoint(p: RoutePoint | null): string {
  if (!p) return 'Not set';
  const lat = `${Math.abs(p.lat).toFixed(3)}° ${p.lat >= 0 ? 'N' : 'S'}`;
  const lon = `${(((p.lon % 360) + 360) % 360).toFixed(3)}° E`;
  return `${lat}, ${lon}`;
}

const PointRow: React.FC<{
  label: string;
  point: RoutePoint | null;
  picking: boolean;
  onPick: () => void;
}> = ({ label, point, picking, onPick }) => (
  <div className="flex items-center justify-between gap-2 rounded border border-line bg-white px-3 py-2">
    <div className="min-w-0">
      <p className="text-[11px] font-medium text-ink-muted">{label}</p>
      <p className="truncate font-mono text-xs text-ink">{formatPoint(point)}</p>
      {point?.name && <p className="truncate text-[11px] text-ink-muted">{point.name}</p>}
    </div>
    <button
      type="button"
      onClick={onPick}
      aria-pressed={picking}
      className={`flex shrink-0 items-center gap-1 rounded px-2 py-1 text-xs font-medium transition-colors ${
        picking ? 'bg-brand-700 text-white' : 'border border-line text-brand-700 hover:bg-surface-muted'
      }`}
    >
      <Crosshair className="h-3.5 w-3.5" aria-hidden="true" />
      {picking ? 'Click the globe' : point ? 'Change' : 'Pick on map'}
    </button>
  </div>
);

const ElevationProfile: React.FC<{ route: AStarRoute }> = ({ route }) => {
  const pts = route.waypoints;
  if (pts.length < 2) return null;
  const w = 360;
  const h = 90;
  const pad = 4;
  const elevs = pts.map((p) => p.elevation_m);
  const min = Math.min(...elevs);
  const max = Math.max(...elevs);
  const range = Math.max(max - min, 10);
  const total = pts[pts.length - 1].distance_km || 1;
  const line = pts
    .map((p, i) => {
      const x = pad + (p.distance_km / total) * (w - 2 * pad);
      const y = pad + (1 - (p.elevation_m - min) / range) * (h - 2 * pad);
      return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');

  return (
    <div className="rounded border border-line bg-white p-2">
      <div className="mb-1 flex justify-between text-[11px] text-ink-muted">
        <span>Elevation along the path</span>
        <span className="font-mono">
          {Math.round(min).toLocaleString()} to {Math.round(max).toLocaleString()} m
        </span>
      </div>
      <svg viewBox={`0 0 ${w} ${h}`} className="h-20 w-full" preserveAspectRatio="none" aria-hidden="true">
        <path d={`${line} L${w - pad},${h} L${pad},${h} Z`} fill="#01416614" />
        <path d={line} fill="none" stroke="#014166" strokeWidth="1.5" vectorEffect="non-scaling-stroke" />
      </svg>
      <div className="flex justify-between text-[10px] text-ink-faint">
        <span>0 km</span>
        <span>{total.toFixed(1)} km</span>
      </div>
    </div>
  );
};

export const RoutePlanningDrawer: React.FC = () => {
  const {
    isRoutePlannerOpen,
    setIsRoutePlannerOpen,
    departurePoint,
    arrivalPoint,
    routePickTarget,
    setRoutePickTarget,
    setDeparturePoint,
    setArrivalPoint,
    activeNavigationRoute,
    setActiveNavigationRoute,
  } = useGlobeStore();

  const [vehicle, setVehicle] = useState<Vehicle>('car');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const route = activeNavigationRoute as AStarRoute | null;

  // A new point makes the old path stale.
  useEffect(() => {
    setActiveNavigationRoute(null);
    setError(null);
  }, [departurePoint, arrivalPoint, vehicle, setActiveNavigationRoute]);

  if (!isRoutePlannerOpen) return null;

  const close = () => {
    setIsRoutePlannerOpen(false);
    setRoutePickTarget(null);
    setDeparturePoint(null);
    setArrivalPoint(null);
    setActiveNavigationRoute(null);
  };

  const run = async () => {
    if (!departurePoint || !arrivalPoint) return;
    setLoading(true);
    setError(null);
    try {
      setActiveNavigationRoute(await findPath(departurePoint, arrivalPoint, vehicle));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Path finding failed.');
    } finally {
      setLoading(false);
    }
  };

  const exportAs = (kind: 'geojson' | 'csv' | 'kml') => {
    if (!route) return;
    const base = `zuhura_path_${vehicle}`;
    if (kind === 'geojson') {
      downloadTextFile(`${base}.geojson`, JSON.stringify(buildTraverseGeoJson(route), null, 2), 'application/geo+json');
    } else if (kind === 'csv') {
      downloadTextFile(`${base}.csv`, buildTraverseCsv(route), 'text/csv');
    } else {
      downloadTextFile(`${base}.kml`, buildTraverseKml(route), 'application/vnd.google-earth.kml+xml');
    }
  };

  const togglePick = (target: 'start' | 'end') => setRoutePickTarget(routePickTarget === target ? null : target);

  return (
    <section
      className="fixed right-4 top-20 z-20 w-[min(24rem,calc(100vw-2rem))] overflow-hidden rounded-lg border border-line bg-surface-subtle text-ink shadow-panel"
      aria-label="Traverse planner"
    >
      <header className="flex items-center justify-between border-b border-line bg-white px-4 py-3">
        <h2 className="text-sm font-semibold">Traverse</h2>
        <button
          type="button"
          onClick={close}
          aria-label="Close"
          className="rounded p-1 text-ink-muted hover:bg-surface-muted hover:text-ink"
        >
          <X className="h-4 w-4" />
        </button>
      </header>

      <div className="max-h-[calc(100vh-9rem)] space-y-3 overflow-y-auto p-3 text-xs">
        <PointRow
          label="Start"
          point={departurePoint}
          picking={routePickTarget === 'start'}
          onPick={() => togglePick('start')}
        />
        <PointRow
          label="Destination"
          point={arrivalPoint}
          picking={routePickTarget === 'end'}
          onPick={() => togglePick('end')}
        />

        <div>
          <p className="mb-1 text-[11px] font-medium text-ink-muted">Vehicle</p>
          <div className="flex rounded border border-line bg-white p-0.5">
            {VEHICLES.map((v) => (
              <button
                key={v.id}
                type="button"
                title={v.hint}
                onClick={() => setVehicle(v.id)}
                aria-pressed={vehicle === v.id}
                className={`flex-1 rounded py-1.5 transition-colors ${
                  vehicle === v.id ? 'bg-brand-700 font-semibold text-white' : 'text-ink-muted hover:text-ink'
                }`}
              >
                {v.label}
              </button>
            ))}
          </div>
          <p className="mt-1 text-[11px] text-ink-muted">{VEHICLES.find((v) => v.id === vehicle)?.hint}</p>
        </div>

        <button
          type="button"
          onClick={run}
          disabled={!departurePoint || !arrivalPoint || loading}
          className="flex w-full items-center justify-center gap-2 rounded bg-brand-700 py-2 text-sm font-semibold text-white transition-colors hover:bg-brand-800 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {loading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
          {loading ? 'Finding path…' : 'Find path'}
        </button>

        {error && <p className="rounded border border-danger-line bg-danger-soft p-2 text-danger">{error}</p>}

        {route && (
          <div className="space-y-3 border-t border-line pt-3">
            <dl className="grid grid-cols-2 gap-2">
              {[
                ['Path length', `${route.total_distance_km} km`],
                ['Straight line', `${route.direct_distance_km} km`],
                ['Steepest point', `${route.max_slope_degrees}°`],
                ['Climb / descent', `+${route.elevation_gain_m} / −${route.elevation_loss_m} m`],
              ].map(([label, value]) => (
                <div key={label} className="rounded border border-line bg-white px-2 py-1.5">
                  <dt className="text-[11px] text-ink-muted">{label}</dt>
                  <dd className="font-mono font-medium">{value}</dd>
                </div>
              ))}
            </dl>

            <ElevationProfile route={route} />

            <p className="text-[11px] leading-relaxed text-ink-muted">
              Yellow line: A* path. Dashed line: straight line. Searched a {route.grid.rows} × {route.grid.cols} grid
              of {route.grid.cell_size_m} m cells from {route.dataset}; {route.grid.blocked_percent}% of cells were too
              steep or rough.
            </p>

            <div className="flex gap-1.5">
              {(['geojson', 'csv', 'kml'] as const).map((kind) => (
                <button
                  key={kind}
                  type="button"
                  onClick={() => exportAs(kind)}
                  className="flex flex-1 items-center justify-center gap-1 rounded border border-line bg-white py-1.5 text-[11px] text-ink-soft hover:bg-surface-muted"
                >
                  <Download className="h-3 w-3" aria-hidden="true" />
                  {kind.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
};
