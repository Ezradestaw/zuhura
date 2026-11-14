/**
 * Zuhura Frontend - Transect Elevation Profile Drawer
 * Interactive SVG cross-section visualization of great-circle geodesic profiles
 * with station inspection, slope gradients, and scientific provenance.
 */

import React, { useState } from 'react';
import { TrendingUp, X, RefreshCw, ChevronDown, ChevronUp, Compass } from 'lucide-react';
import { useTerrainAnalysisStore } from '../store/terrainAnalysisStore';

export const TransectProfileDrawer: React.FC = () => {
  const {
    isTransectMode,
    setIsTransectMode,
    transectStart,
    transectEnd,
    profileData,
    isLoadingProfile,
    profileError,
    sampleCount,
    setSampleCount,
    executeTransectQuery,
    hoveredSampleIndex,
    setHoveredSampleIndex,
  } = useTerrainAnalysisStore();

  const [isMinimized, setIsMinimized] = useState(false);

  if (!isTransectMode && !profileData) return null;

  const samples = profileData?.samples || [];
  const summary = profileData?.transect_summary;

  // Compute SVG chart coordinates
  const svgWidth = 650;
  const svgHeight = 160;
  const padLeft = 55;
  const padRight = 20;
  const padTop = 20;
  const padBottom = 30;

  const chartW = svgWidth - padLeft - padRight;
  const chartH = svgHeight - padTop - padBottom;

  let pathD = '';
  let areaD = '';
  let minElev = 0;
  let maxElev = 0;
  let maxDist = 1;

  if (samples.length > 1) {
    const elevs = samples.map((s) => s.elevation_m);
    minElev = Math.min(...elevs);
    maxElev = Math.max(...elevs);
    // Add small buffer to avoid flat lines
    const elevRange = Math.max(10, maxElev - minElev);
    const elevMinBuffered = minElev - elevRange * 0.08;
    const elevMaxBuffered = maxElev + elevRange * 0.08;

    maxDist = samples[samples.length - 1].distance_km || 1;

    const points = samples.map((s) => {
      const x = padLeft + (s.distance_km / maxDist) * chartW;
      const y = padTop + (1 - (s.elevation_m - elevMinBuffered) / (elevMaxBuffered - elevMinBuffered)) * chartH;
      return { x, y, sample: s };
    });

    pathD = points.reduce((acc, p, idx) => (idx === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`), '');

    const bottomY = padTop + chartH;
    areaD = `${pathD} L ${points[points.length - 1].x} ${bottomY} L ${points[0].x} ${bottomY} Z`;
  }

  const activeSample = hoveredSampleIndex !== null && samples[hoveredSampleIndex] ? samples[hoveredSampleIndex] : null;

  return (
    <div
      className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-20 w-[740px] max-w-[calc(100vw-4rem)] bg-white border border-line rounded shadow-2xl transition-all duration-150 font-sans text-ink overflow-hidden select-none ${
        isMinimized ? 'h-11' : ''
      }`}
    >
      {/* Header bar */}
      <div className="flex items-center justify-between px-3.5 py-2.5 bg-surface-subtle border-b border-line select-none">
        <div className="flex items-center space-x-2">
          <div className="p-1 rounded bg-brand-50 border border-brand-200 text-brand-600">
            <TrendingUp className="w-3.5 h-3.5" />
          </div>
          <span className="font-semibold text-xs text-ink">Mars Geodesic Transect Profile</span>
          {summary && (
            <span className="px-1.5 py-0.2 rounded bg-success-soft border border-success-line text-[9px] text-success font-mono font-bold">
              {summary.total_distance_km.toFixed(1)} km
            </span>
          )}
        </div>

        <div className="flex items-center space-x-1.5">
          <button
            onClick={() => executeTransectQuery()}
            disabled={isLoadingProfile || !transectStart || !transectEnd}
            className="flex items-center gap-1 px-2 py-1 text-[11px] font-semibold bg-brand-700 hover:bg-brand-700 rounded text-white disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`w-3 h-3 ${isLoadingProfile ? 'animate-spin' : ''}`} />
            <span>{isLoadingProfile ? 'Sampling...' : 'Sample Transect'}</span>
          </button>

          <button onClick={() => setIsMinimized(!isMinimized)} className="p-1 text-ink-muted hover:text-ink">
            {isMinimized ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
          <button onClick={() => setIsTransectMode(false)} className="p-1 text-ink-muted hover:text-ink">
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <div className="p-3 space-y-3">
          {/* Coordinates and Controls row */}
          <div className="flex items-center justify-between text-[11px] font-mono bg-surface-subtle p-2 rounded border border-line">
            <div className="flex items-center gap-3">
              <div>
                <span className="text-ink-muted block text-[9px]">Start</span>
                <span className="text-ink font-semibold">
                  {transectStart
                    ? `${transectStart.latitude.toFixed(2)}°N, ${transectStart.longitude.toFixed(2)}°E`
                    : 'Click Globe'}
                </span>
              </div>
              <Compass className="w-3.5 h-3.5 text-brand-600" />
              <div>
                <span className="text-ink-muted block text-[9px]">End</span>
                <span className="text-ink font-semibold">
                  {transectEnd
                    ? `${transectEnd.latitude.toFixed(2)}°N, ${transectEnd.longitude.toFixed(2)}°E`
                    : 'Click Globe'}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-ink-muted text-[10px]">Points:</span>
              {[25, 50, 100].map((count) => (
                <button
                  key={count}
                  onClick={() => setSampleCount(count)}
                  className={`px-1.5 py-0.5 rounded text-[10px] ${
                    sampleCount === count
                      ? 'bg-brand-700 text-white font-bold'
                      : 'bg-surface-muted text-ink-muted hover:text-ink'
                  }`}
                >
                  {count}
                </button>
              ))}
            </div>
          </div>

          {profileError && (
            <div className="p-2 bg-danger-soft border border-danger-line rounded text-danger text-xs">
              {profileError}
            </div>
          )}

          {/* SVG Profile Chart */}
          {samples.length > 1 ? (
            <div className="relative bg-white rounded border border-line p-1">
              <svg
                viewBox={`0 0 ${svgWidth} ${svgHeight}`}
                className="w-full h-36 overflow-visible"
                onMouseLeave={() => setHoveredSampleIndex(null)}
              >
                <defs>
                  <linearGradient id="profileGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#014166" stopOpacity="0.45" />
                    <stop offset="100%" stopColor="#014166" stopOpacity="0.05" />
                  </linearGradient>
                </defs>

                {/* Grid horizontal lines */}
                <line
                  x1={padLeft}
                  y1={padTop}
                  x2={padLeft + chartW}
                  y2={padTop}
                  stroke="#e4e7ec"
                  strokeDasharray="2,2"
                />
                <line
                  x1={padLeft}
                  y1={padTop + chartH / 2}
                  x2={padLeft + chartW}
                  y2={padTop + chartH / 2}
                  stroke="#e4e7ec"
                  strokeDasharray="2,2"
                />
                <line x1={padLeft} y1={padTop + chartH} x2={padLeft + chartW} y2={padTop + chartH} stroke="#d0d5dd" />

                {/* Y-axis labels */}
                <text
                  x={padLeft - 6}
                  y={padTop + 4}
                  fill="#667085"
                  fontSize="9"
                  fontFamily="monospace"
                  textAnchor="end"
                >
                  {Math.round(maxElev)} m
                </text>
                <text
                  x={padLeft - 6}
                  y={padTop + chartH + 3}
                  fill="#667085"
                  fontSize="9"
                  fontFamily="monospace"
                  textAnchor="end"
                >
                  {Math.round(minElev)} m
                </text>

                {/* X-axis labels */}
                <text
                  x={padLeft}
                  y={padTop + chartH + 15}
                  fill="#667085"
                  fontSize="9"
                  fontFamily="monospace"
                  textAnchor="start"
                >
                  0 km
                </text>
                <text
                  x={padLeft + chartW}
                  y={padTop + chartH + 15}
                  fill="#667085"
                  fontSize="9"
                  fontFamily="monospace"
                  textAnchor="end"
                >
                  {maxDist.toFixed(1)} km
                </text>

                {/* Area fill & Profile line */}
                <path d={areaD} fill="url(#profileGrad)" />
                <path
                  d={pathD}
                  fill="none"
                  stroke="#014166"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />

                {/* Interactive Station Markers */}
                {samples.map((s, idx) => {
                  const elevRange = Math.max(10, maxElev - minElev);
                  const bMin = minElev - elevRange * 0.08;
                  const bMax = maxElev + elevRange * 0.08;
                  const cx = padLeft + (s.distance_km / maxDist) * chartW;
                  const cy = padTop + (1 - (s.elevation_m - bMin) / (bMax - bMin)) * chartH;
                  const isHovered = hoveredSampleIndex === idx;

                  return (
                    <g key={idx}>
                      {isHovered && (
                        <line
                          x1={cx}
                          y1={padTop}
                          x2={cx}
                          y2={padTop + chartH}
                          stroke="#0277ba"
                          strokeWidth="1"
                          strokeDasharray="2,2"
                        />
                      )}
                      <circle
                        cx={cx}
                        cy={cy}
                        r={isHovered ? 5 : 2.5}
                        fill={isHovered ? '#0277ba' : '#014166'}
                        stroke="#ffffff"
                        strokeWidth="1"
                        className="cursor-pointer transition-all"
                        onMouseEnter={() => setHoveredSampleIndex(idx)}
                      />
                    </g>
                  );
                })}
              </svg>

              {/* Hover tooltip overlay */}
              {activeSample && (
                <div className="absolute top-2 right-2 bg-surface-subtle border border-line px-2 py-1 rounded text-[10px] font-mono shadow">
                  <div>
                    <span className="text-ink-muted">DIST: </span>
                    <span className="text-warning">{activeSample.distance_km.toFixed(2)} km</span>
                  </div>
                  <div>
                    <span className="text-ink-muted">ELEV: </span>
                    <span className="text-success font-bold">{activeSample.elevation_m.toFixed(1)} m</span>
                  </div>
                  {activeSample.segment_slope_deg !== undefined && (
                    <div>
                      <span className="text-ink-muted">SLOPE: </span>
                      <span className="text-ink">{activeSample.segment_slope_deg.toFixed(1)}°</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-ink-muted bg-surface-subtle rounded border border-dashed border-line">
              Click &quot;Sample Transect&quot; above to query MOLA elevations along this great-circle path.
            </div>
          )}

          {/* Morphometric Summary Cards */}
          {summary && (
            <div className="grid grid-cols-4 gap-2 text-[10px] font-mono">
              <div className="p-1.5 bg-surface-subtle rounded border border-line">
                <span className="text-ink-muted block text-[9px]">Relief</span>
                <span className="text-ink font-bold">{summary.elevation_relief_m.toFixed(0)} m</span>
                <span className="text-[8px] text-ink-muted block">
                  [{summary.min_elevation_m.toFixed(0)} to {summary.max_elevation_m.toFixed(0)}]
                </span>
              </div>
              <div className="p-1.5 bg-surface-subtle rounded border border-line">
                <span className="text-ink-muted block text-[9px]">Elevation gain / loss</span>
                <span className="text-success font-bold">
                  +{summary.cumulative_elevation_gain_m.toFixed(0)} m
                </span> /{' '}
                <span className="text-danger font-bold">-{summary.cumulative_elevation_loss_m.toFixed(0)} m</span>
              </div>
              <div className="p-1.5 bg-surface-subtle rounded border border-line">
                <span className="text-ink-muted block text-[9px]">Mean / max slope</span>
                <span className="text-warning font-bold">{summary.mean_slope_deg.toFixed(1)}°</span> /{' '}
                <span className="text-danger font-bold">{summary.max_slope_deg.toFixed(1)}°</span>
              </div>
              <div className="p-1.5 bg-surface-subtle rounded border border-line">
                <span className="text-ink-muted block text-[9px]">Point spacing</span>
                <span className="text-ink font-bold">{summary.sample_step_m.toFixed(0)} m</span>
                <span className="text-[8px] text-ink-muted block">N={summary.num_samples} stations</span>
              </div>
            </div>
          )}

          {/* Scientific Provenance Tag */}
          <div className="flex items-center justify-between text-[9px] text-ink-muted border-t border-line pt-1.5 font-mono">
            <span>Data: MOLA MEGDR, about 463 m/px. Elevations relative to the MOLA areoid.</span>
          </div>
        </div>
      )}
    </div>
  );
};
