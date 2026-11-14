import React from 'react';
import { Ruler, Square, RotateCcw, Save, X, Info } from 'lucide-react';
import { useWorkspaceStore } from '../store/workspaceStore';
import { marsSurfaceDistanceKm } from '../lib/geodesy/transformations';

export const GlobeMeasurementHUD: React.FC = () => {
  const {
    measurementToolActive,
    setMeasurementToolActive,
    measurementPoints,
    clearMeasurementPoints,
    saveMeasurement,
  } = useWorkspaceStore();

  if (measurementToolActive === 'none') return null;

  // Calculate cumulative geodesic distance
  let totalDistanceKm = 0.0;
  for (let i = 0; i < measurementPoints.length - 1; i++) {
    totalDistanceKm += marsSurfaceDistanceKm(
      measurementPoints[i].lat,
      measurementPoints[i].lon,
      measurementPoints[i + 1].lat,
      measurementPoints[i + 1].lon
    );
  }

  // Calculate elevation delta
  const minElev = measurementPoints.length > 0 ? Math.min(...measurementPoints.map(p => p.elevation_m)) : 0;
  const maxElev = measurementPoints.length > 0 ? Math.max(...measurementPoints.map(p => p.elevation_m)) : 0;
  const elevationRelief = maxElev - minElev;

  // Calculate polygon area (spherical excess formula on Mars mean radius R = 3389.5 km)
  let polygonAreaKm2 = 0.0;
  if (measurementToolActive === 'area' && measurementPoints.length >= 3) {
    const R = 3389.5;
    let sum = 0.0;
    const n = measurementPoints.length;
    for (let i = 0; i < n; i++) {
      const p1 = measurementPoints[i];
      const p2 = measurementPoints[(i + 1) % n];
      const lon1Rad = (p1.lon * Math.PI) / 180.0;
      const lon2Rad = (p2.lon * Math.PI) / 180.0;
      const lat1Rad = (p1.lat * Math.PI) / 180.0;
      const lat2Rad = (p2.lat * Math.PI) / 180.0;
      sum += (lon2Rad - lon1Rad) * (2 + Math.sin(lat1Rad) + Math.sin(lat2Rad));
    }
    polygonAreaKm2 = Math.abs((sum * R * R) / 2.0);
  }

  const handleSaveToWorkspace = () => {
    if (measurementPoints.length < 2) return;
    saveMeasurement({
      mode: measurementToolActive === 'area' ? 'area' : 'distance',
      points: measurementPoints,
      result_value: Number((measurementToolActive === 'area' ? polygonAreaKm2 : totalDistanceKm).toFixed(2)),
      elevation_delta_m: elevationRelief,
    });
    clearMeasurementPoints();
    setMeasurementToolActive('none');
  };

  return (
    <div className="absolute top-16 left-20 z-10 w-80 bg-white border border-line-strong rounded shadow-2xl p-3 text-ink font-sans select-none">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-line">
        <div className="flex items-center space-x-2 text-brand-600 text-xs font-bold">
          {measurementToolActive === 'ruler' ? (
            <Ruler className="w-4 h-4 text-brand-600" />
          ) : (
            <Square className="w-4 h-4 text-brand-600" />
          )}
          <span>{measurementToolActive === 'ruler' ? 'Geodesic Ruler' : 'Polygon Area Tool'}</span>
        </div>
        <div className="flex items-center space-x-1">
          <button
            onClick={clearMeasurementPoints}
            className="flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-mono bg-surface-subtle hover:bg-surface-muted text-ink-soft transition-colors"
            title="Reset Measurement Points"
          >
            <RotateCcw className="w-3 h-3" />
            <span>Reset</span>
          </button>
          <button
            onClick={() => {
              clearMeasurementPoints();
              setMeasurementToolActive('none');
            }}
            className="p-1 rounded text-ink-muted hover:text-ink transition-colors"
            title="Close Tool"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Mode Selector Toggle */}
      <div className="grid grid-cols-2 gap-1.5 my-2.5">
        <button
          onClick={() => setMeasurementToolActive('ruler')}
          className={`py-1 px-2 rounded text-xs font-mono flex items-center justify-center space-x-1.5 border transition-colors ${
            measurementToolActive === 'ruler'
              ? 'bg-brand-50 border-brand-600 text-brand-600 font-bold'
              : 'bg-surface-subtle border-line text-ink-muted hover:text-ink'
          }`}
        >
          <Ruler className="w-3.5 h-3.5" />
          <span>Ruler (km)</span>
        </button>
        <button
          onClick={() => setMeasurementToolActive('area')}
          className={`py-1 px-2 rounded text-xs font-mono flex items-center justify-center space-x-1.5 border transition-colors ${
            measurementToolActive === 'area'
              ? 'bg-brand-50 border-brand-600 text-brand-600 font-bold'
              : 'bg-surface-subtle border-line text-ink-muted hover:text-ink'
          }`}
        >
          <Square className="w-3.5 h-3.5" />
          <span>Area (km²)</span>
        </button>
      </div>

      {/* Instructions / Status */}
      <div className="p-2 rounded bg-surface-subtle border border-line text-[11px] font-mono text-ink-soft flex items-start space-x-2">
        <Info className="w-3.5 h-3.5 text-brand-600 shrink-0 mt-0.5" />
        <div>
          {measurementPoints.length === 0 ? (
            <span>Click on the Mars globe to place first vertex pin.</span>
          ) : measurementPoints.length === 1 ? (
            <span>First pin set. Click on Mars to add destination station.</span>
          ) : (
            <span>
              {measurementPoints.length} vertices pinned. Click Mars to add more or Save.
            </span>
          )}
        </div>
      </div>

      {/* Measurement Metrics Grid */}
      <div className="mt-2.5 grid grid-cols-2 gap-2 text-center font-mono">
        <div className="p-2 rounded bg-surface-subtle border border-line">
          <div className="text-[9px] text-ink-muted uppercase tracking-wider">
            {measurementToolActive === 'ruler' ? 'Traverse Length' : 'Surface Area'}
          </div>
          <div className="text-sm font-bold text-warning">
            {measurementToolActive === 'ruler'
              ? `${totalDistanceKm.toFixed(2)} km`
              : `${polygonAreaKm2.toFixed(1)} km²`}
          </div>
        </div>
        <div className="p-2 rounded bg-surface-subtle border border-line">
          <div className="text-[9px] text-ink-muted uppercase tracking-wider">Elevation Relief</div>
          <div className="text-sm font-bold text-brand-600">
            {elevationRelief > 0 ? `±${Math.round(elevationRelief)} m` : '0 m'}
          </div>
        </div>
      </div>

      {/* Save Button */}
      {measurementPoints.length >= 2 && (
        <button
          onClick={handleSaveToWorkspace}
          className="mt-2.5 w-full py-1.5 px-3 rounded bg-brand-50 hover:bg-brand-50 border border-brand-200 text-brand-600 text-xs font-mono font-semibold flex items-center justify-center space-x-1.5 transition-colors"
        >
          <Save className="w-3.5 h-3.5" />
          <span>Save Measurement to Workspace</span>
        </button>
      )}
    </div>
  );
};