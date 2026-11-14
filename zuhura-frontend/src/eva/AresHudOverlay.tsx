/**
 * ARES-HUD: Astronaut EVA Co-Pilot UI & Visor POV First-Person Engine
 * NASA Space Apps Challenge 2026: "Interplanetary Survival Guide: Martian Map"
 *
 * Implements:
 * 1. Live aerospace suit telemetry panel (O2 %, burn rate, battery %, radiation, distance, duration)
 * 2. Tactical layer controls (Slope Hazard, Thermal Inertia Firmness, Science Targets, Radiation Shielding)
 * 3. Walk simulation with status messages
 * 4. One-click "Emergency Abort to Hab" button
 * 5. Visor POV (First-Person Helmet Camera) HUD reticle & compass tape
 * 6. Waypoint inspector drawer with authentic Perseverance surface raw images vs orbital HiRISE view
 */

import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  BatteryCharging,
  Compass,
  Radio,
  Play,
  Pause,
  RotateCcw,
  AlertTriangle,
  Layers,
  ChevronRight,
  Eye,
  Sliders,
  X,
  Navigation,
} from 'lucide-react';
import {
  JEZERO_SCIENCE_TARGETS,
  JEZERO_HAB_COORDINATES,
  ScienceTarget,
} from './jezeroScienceTargets';
import {
  EvaPoint,
  EvaRoutePlan,
  planMetabolicEvaRoute,
  generateEmergencyAbortRoute,
} from './metabolicPathfinder';
import { TacticalLayerConfig } from './tacticalLayers';

interface AresHudOverlayProps {
  isOpen: boolean;
  onClose: () => void;
  tacticalConfig: TacticalLayerConfig;
  onTacticalConfigChange: (config: TacticalLayerConfig) => void;
  onRoutePlanned: (route: EvaRoutePlan) => void;
  onSimulationStep: (currentPos: EvaPoint, progressFrac: number) => void;
  onVisorPovToggle: (active: boolean) => void;
  isVisorPovActive: boolean;
  cameraHeading: number;
  cameraPitch: number;
}

export const AresHudOverlay: React.FC<AresHudOverlayProps> = ({
  isOpen,
  onClose,
  tacticalConfig,
  onTacticalConfigChange,
  onRoutePlanned,
  onSimulationStep,
  onVisorPovToggle,
  isVisorPovActive,
  cameraHeading,
  cameraPitch,
}) => {
  // Preset EVA Mission Sorties
  const [selectedPreset, setSelectedPreset] = useState<string>('preset-delta-front');

  // Active Route Plan & Metrics
  const [routePlan, setRoutePlan] = useState<EvaRoutePlan | null>(null);

  // Simulation State
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [simSpeed, setSimSpeed] = useState<number>(1); // 1x, 2x, 5x
  const [simProgress, setSimProgress] = useState<number>(0); // 0.0 - 1.0

  // Live Alerts
  const [activeAlert, setActiveAlert] = useState<string | null>(null);

  // Waypoint / Science Target Inspector Drawer
  const [selectedTarget, setSelectedTarget] = useState<ScienceTarget | null>(null);
  const [isInspectorOpen, setIsInspectorOpen] = useState<boolean>(false);

  // Tactical Layers Sub-Panel Open
  const [isLayerControlOpen, setIsLayerControlOpen] = useState<boolean>(false);

  // Initialize Route on Load
  useEffect(() => {
    if (isOpen) {
      loadPresetMission('preset-delta-front');
    }
  }, [isOpen]);

  const loadPresetMission = (presetId: string) => {
    setSelectedPreset(presetId);
    let waypoints: EvaPoint[] = [];

    const habPoint: EvaPoint = {
      ...JEZERO_HAB_COORDINATES,
      isHab: true,
    };

    if (presetId === 'preset-delta-front') {
      const kodiak = JEZERO_SCIENCE_TARGETS.find((t) => t.id === 'target-kodiak-butte')!;
      const threeForks = JEZERO_SCIENCE_TARGETS.find((t) => t.id === 'target-three-forks')!;
      waypoints = [
        habPoint,
        { longitude: kodiak.longitude, latitude: kodiak.latitude, elevation_m: kodiak.elevation_m, name: kodiak.name },
        { longitude: threeForks.longitude, latitude: threeForks.latitude, elevation_m: threeForks.elevation_m, name: threeForks.name },
        habPoint,
      ];
    } else if (presetId === 'preset-carbonate-scarp') {
      const brightAngel = JEZERO_SCIENCE_TARGETS.find((t) => t.id === 'target-bright-angel')!;
      const threeForks = JEZERO_SCIENCE_TARGETS.find((t) => t.id === 'target-three-forks')!;
      waypoints = [
        habPoint,
        { longitude: threeForks.longitude, latitude: threeForks.latitude, elevation_m: threeForks.elevation_m, name: threeForks.name },
        { longitude: brightAngel.longitude, latitude: brightAngel.latitude, elevation_m: brightAngel.elevation_m, name: brightAngel.name },
        habPoint,
      ];
    } else if (presetId === 'preset-neretya-canyon') {
      const threeForks = JEZERO_SCIENCE_TARGETS.find((t) => t.id === 'target-three-forks')!;
      const neretya = JEZERO_SCIENCE_TARGETS.find((t) => t.id === 'target-neretya-vallis')!;
      waypoints = [
        habPoint,
        { longitude: threeForks.longitude, latitude: threeForks.latitude, elevation_m: threeForks.elevation_m, name: threeForks.name },
        { longitude: neretya.longitude, latitude: neretya.latitude, elevation_m: neretya.elevation_m, name: neretya.name },
        habPoint,
      ];
    }

    const plan = planMetabolicEvaRoute(waypoints);
    setRoutePlan(plan);
    onRoutePlanned(plan);
    setSimProgress(0);
    setIsSimulating(false);
    setActiveAlert('Route loaded: path with the lowest metabolic cost.');
  };

  // Real-time Simulation Tick
  useEffect(() => {
    let timer: any = null;
    if (isSimulating && routePlan && routePlan.segments.length > 0) {
      timer = setInterval(() => {
        setSimProgress((prev) => {
          const next = prev + 0.005 * simSpeed;
          if (next >= 1.0) {
            setIsSimulating(false);
            setActiveAlert('Simulation complete: returned to the habitat.');
            return 1.0;
          }

          // Evaluate current segment & trigger alerts
          const segIndex = Math.min(
            routePlan.segments.length - 1,
            Math.floor(next * routePlan.segments.length)
          );
          const currentSeg = routePlan.segments[segIndex];

          if (currentSeg.alert_message) {
            setActiveAlert(currentSeg.alert_message);
          } else if (currentSeg.hazard_level === 'optimal') {
            setActiveAlert('Firm delta bedrock: normal oxygen use.');
          }

          // Interpolate current position for 3D astronaut avatar
          const curLon =
            currentSeg.from.longitude +
            (currentSeg.to.longitude - currentSeg.from.longitude) * 0.5;
          const curLat =
            currentSeg.from.latitude +
            (currentSeg.to.latitude - currentSeg.from.latitude) * 0.5;
          const curElev =
            currentSeg.from.elevation_m +
            (currentSeg.to.elevation_m - currentSeg.from.elevation_m) * 0.5;

          onSimulationStep(
            { longitude: curLon, latitude: curLat, elevation_m: curElev },
            next
          );

          return next;
        });
      }, 150);
    }
    return () => clearInterval(timer);
  }, [isSimulating, simSpeed, routePlan, onSimulationStep]);

  // One-Click Emergency Abort to Hab Trigger
  const handleEmergencyAbort = () => {
    if (!routePlan || routePlan.segments.length === 0) return;

    // Get current position along route
    const segIndex = Math.min(
      routePlan.segments.length - 1,
      Math.floor(simProgress * routePlan.segments.length)
    );
    const curPt = routePlan.segments[segIndex].from;

    const abortPlan = generateEmergencyAbortRoute(curPt);
    setRoutePlan(abortPlan);
    onRoutePlanned(abortPlan);
    setSimProgress(0);
    setIsSimulating(true);
    setSimSpeed(2); // Accelerate return cadence
    setActiveAlert('Return to habitat: using the route with the lowest oxygen use.');
  };

  if (!isOpen) return null;

  // Real-time simulated suit metrics adjusted by simulation progress
  const simulatedO2Pct = routePlan
    ? Math.max(12, Math.round(100 - simProgress * (100 - routePlan.suit_oxygen_pct_remaining)))
    : 100;
  const simulatedBatteryPct = routePlan
    ? Math.max(18, Math.round(100 - simProgress * (100 - routePlan.suit_battery_pct_remaining)))
    : 100;
  const simulatedRadDose = routePlan
    ? (simProgress * routePlan.total_radiation_dose_usv).toFixed(1)
    : '0.0';

  return (
    <div className="fixed inset-0 pointer-events-none z-10 overflow-hidden font-sans select-none">
      {/* 1. VISOR POV (FIRST-PERSON HELMET CAMERA OVERLAY) */}
      {isVisorPovActive && (
        <div className="absolute inset-0 pointer-events-none flex flex-col justify-between">
          {/* Curved Visor Reticle Edge Vignette */}
          <div className="absolute inset-0 border-[36px] border-ink rounded-[90px] pointer-events-none" />

          {/* Top Visor Heading Tape */}
          <div className="relative pt-6 flex flex-col items-center">
            <div className="px-6 py-1.5 rounded-full bg-white/95 border border-line font-mono text-xs text-brand-600 flex items-center space-x-4 shadow-xl">
              <Compass className="w-3.5 h-3.5 text-brand-600" />
              <span className="font-bold tracking-wide">
                HDG {Math.round(cameraHeading)}° | PITCH {Math.round(cameraPitch)}°
              </span>
              <span className="text-ink">|</span>
              <span className="text-success font-bold">EVA EYE-LEVEL (1.75m)</span>
            </div>
          </div>

          {/* Center Target Reticle */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="relative w-24 h-24 border border-brand-200 rounded-full flex items-center justify-center">
              <div className="w-2 h-2 bg-brand-700 rounded-full " />
              <div className="absolute w-full h-[1px] bg-brand-50" />
              <div className="absolute h-full w-[1px] bg-brand-50" />
            </div>
          </div>

          {/* Bottom Visor Status */}
          <div className="pb-6 text-center font-mono text-[11px] text-brand-600 drop-shadow">
            ARES-HUD FIRST-PERSON MISSION CO-PILOT • JEZERO HI-RES SECTOR
          </div>
        </div>
      )}

      {/* 2. TOP TELEMETRY HUD BAR */}
      <div className="absolute top-32 left-20 right-6 flex items-start justify-between pointer-events-auto">
        {/* Left: Suit Vitals Dashboard */}
        <div className="bg-white border border-brand-200 rounded-xl p-3 shadow-2xl flex items-center space-x-6 text-xs font-mono">
          {/* Oxygen Gauge */}
          <div className="flex items-center space-x-2.5">
            <div className="relative w-10 h-10 flex items-center justify-center">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                <path
                  className="text-ink"
                  strokeWidth="3"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                <path
                  className={simulatedO2Pct < 25 ? 'text-danger' : 'text-brand-600'}
                  strokeDasharray={`${simulatedO2Pct}, 100`}
                  strokeWidth="3.5"
                  strokeLinecap="round"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
              </svg>
              <span className="absolute text-[10px] font-bold text-ink">{simulatedO2Pct}%</span>
            </div>
            <div>
              <div className="text-[10px] uppercase text-ink-muted font-bold">Suit oxygen</div>
              <div className="text-ink font-bold text-xs">
                {routePlan ? `${routePlan.average_o2_burn_rate_kg_hr} kg/hr` : '0.075 kg/hr'}
              </div>
            </div>
          </div>

          <div className="h-8 w-[1px] bg-surface-muted" />

          {/* Battery Gauge */}
          <div className="flex items-center space-x-2">
            <BatteryCharging
              className={`w-5 h-5 ${simulatedBatteryPct < 25 ? 'text-danger ' : 'text-success'}`}
            />
            <div>
              <div className="text-[10px] uppercase text-ink-muted font-bold">Battery</div>
              <div className="text-ink font-bold text-xs">{simulatedBatteryPct}%</div>
            </div>
          </div>

          <div className="h-8 w-[1px] bg-surface-muted" />

          {/* Radiation Exposure Meter */}
          <div className="flex items-center space-x-2">
            <ShieldAlert className="w-5 h-5 text-warning" />
            <div>
              <div className="text-[10px] uppercase text-ink-muted font-bold">Radiation dose</div>
              <div className="text-warning font-bold text-xs">{simulatedRadDose} μSv</div>
            </div>
          </div>

          <div className="h-8 w-[1px] bg-surface-muted" />

          {/* Distance & Duration */}
          <div>
            <div className="text-[10px] uppercase text-ink-muted font-bold">Distance and time</div>
            <div className="text-ink font-bold text-xs">
              {routePlan?.total_distance_m || 0} m • {routePlan?.total_duration_minutes || 0} min
            </div>
          </div>

          <div className="h-8 w-[1px] bg-surface-muted" />

          {/* Visor POV Toggle Button */}
          <button
            onClick={() => onVisorPovToggle(!isVisorPovActive)}
            className={`px-3 py-1.5 rounded-lg border font-bold flex items-center space-x-1.5 transition-all ${
              isVisorPovActive
                ? 'bg-brand-700 text-ink border-brand-600 shadow-[0_0_15px_rgba(6,182,212,0.6)]'
                : 'bg-surface-muted text-brand-600 border-brand-200 hover:bg-brand-50'
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            <span>{isVisorPovActive ? 'EXIT VISOR POV' : 'VISOR POV (1.75m)'}</span>
          </button>
        </div>

        {/* Right: Emergency Abort to Hab & Close */}
        <div className="flex items-center space-x-3">
          <button
            onClick={handleEmergencyAbort}
            className="px-4 py-2 rounded-xl bg-danger hover:bg-danger text-white font-bold font-mono text-xs border border-danger shadow-2xl flex items-center space-x-2 transition-all hover:scale-105 active:scale-95"
          >
            <AlertTriangle className="w-4 h-4 text-warning" />
            <span>Return to habitat</span>
          </button>

          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-white/95 hover:bg-white text-ink-muted hover:text-ink border border-line transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 3. ACTIVE TACTICAL ALERT BANNER */}
      {activeAlert && (
        <div className="absolute top-56 left-1/2 -translate-x-1/2 pointer-events-auto">
          <div className="px-5 py-2 rounded-full bg-white/95 border border-warning-line text-warning font-mono text-xs flex items-center space-x-2.5 shadow-2xl">
            <Radio className="w-3.5 h-3.5 text-warning " />
            <span className="font-semibold">{activeAlert}</span>
          </div>
        </div>
      )}

      {/* 4. BOTTOM CONTROLS & SCIENCE TARGET DRAWER */}
      <div className="absolute bottom-6 left-20 right-6 flex items-end justify-between pointer-events-auto">
        {/* Left: Simulation Playback & Mission Sortie Deck */}
        <div className="bg-white border border-line-strong rounded-xl p-3.5 shadow-2xl font-mono text-xs space-y-2.5 max-w-lg">
          <div className="flex items-center justify-between border-b border-line pb-2">
            <span className="text-[11px] font-bold text-brand-600 uppercase tracking-wider flex items-center space-x-1.5">
              <Navigation className="w-3.5 h-3.5" />
              <span>EVA route (lowest metabolic cost)</span>
            </span>

            <button
              onClick={() => setIsLayerControlOpen(!isLayerControlOpen)}
              className="text-[10px] text-brand-600 hover:text-brand-600 flex items-center space-x-1"
            >
              <Layers className="w-3 h-3" />
              <span>Map layers</span>
            </button>
          </div>

          {/* Preset Sortie Selection */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => loadPresetMission('preset-delta-front')}
              className={`px-2.5 py-1 rounded text-[10px] font-bold border transition-colors ${
                selectedPreset === 'preset-delta-front'
                  ? 'bg-brand-50 text-brand-600 border-brand-600'
                  : 'bg-surface-subtle text-ink-muted border-line hover:bg-surface-muted'
              }`}
            >
              1. Delta Front Sortie
            </button>
            <button
              onClick={() => loadPresetMission('preset-carbonate-scarp')}
              className={`px-2.5 py-1 rounded text-[10px] font-bold border transition-colors ${
                selectedPreset === 'preset-carbonate-scarp'
                  ? 'bg-brand-50 text-brand-600 border-brand-600'
                  : 'bg-surface-subtle text-ink-muted border-line hover:bg-surface-muted'
              }`}
            >
              2. Bright Angel Carbonates
            </button>
            <button
              onClick={() => loadPresetMission('preset-neretya-canyon')}
              className={`px-2.5 py-1 rounded text-[10px] font-bold border transition-colors ${
                selectedPreset === 'preset-neretya-canyon'
                  ? 'bg-brand-50 text-brand-600 border-brand-600'
                  : 'bg-surface-subtle text-ink-muted border-line hover:bg-surface-muted'
              }`}
            >
              3. Neretya Inflow Canyon
            </button>
          </div>

          {/* Simulation Playback Controls */}
          <div className="flex items-center justify-between pt-1">
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setIsSimulating(!isSimulating)}
                className="px-3 py-1.5 rounded-lg bg-success hover:bg-success text-ink font-bold flex items-center space-x-1.5 transition-colors"
              >
                {isSimulating ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                <span>{isSimulating ? 'Pause' : 'Simulate walk'}</span>
              </button>

              <button
                onClick={() => {
                  setSimProgress(0);
                  setIsSimulating(false);
                }}
                className="p-1.5 rounded-lg bg-surface-muted hover:bg-surface-muted text-ink-soft border border-line"
                title="Reset Simulation"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>

              <div className="flex items-center space-x-1 bg-surface-subtle rounded px-1.5 py-1 text-[10px]">
                <span className="text-ink-muted">SPEED:</span>
                {[1, 2, 5].map((spd) => (
                  <button
                    key={spd}
                    onClick={() => setSimSpeed(spd)}
                    className={`px-1 rounded font-bold ${
                      simSpeed === spd ? 'text-brand-600 bg-surface-muted' : 'text-ink-muted'
                    }`}
                  >
                    {spd}x
                  </button>
                ))}
              </div>
            </div>

            <div className="text-[11px] text-ink-soft font-bold tabular-nums">
              PROGRESS: {Math.round(simProgress * 100)}%
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full h-1.5 bg-surface-muted rounded-full overflow-hidden border border-line">
            <div
              className="h-full bg-success transition-all duration-150"
              style={{ width: `${simProgress * 100}%` }}
            />
          </div>
        </div>

        {/* Right: Science Target Inspector Button & Quick Access */}
        <div className="flex flex-col items-end space-y-2">
          <div className="flex items-center space-x-1.5">
            {JEZERO_SCIENCE_TARGETS.map((target) => (
              <button
                key={target.id}
                onClick={() => {
                  setSelectedTarget(target);
                  setIsInspectorOpen(true);
                }}
                className="px-2.5 py-1 rounded bg-white/95 hover:bg-white border border-line hover:border-brand-600 font-mono text-[10px] text-ink transition-all shadow-lg flex items-center space-x-1"
              >
                <span>{target.name.split(' ')[0]}</span>
                <span className="text-warning font-bold">[{target.science_priority_score}]</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 5. TACTICAL LAYERS CONTROLLER MODAL / FLYOUT */}
      {isLayerControlOpen && (
        <div className="absolute bottom-40 left-20 bg-white border border-line-strong rounded-xl p-4 shadow-2xl font-mono text-xs w-80 space-y-3 pointer-events-auto">
          <div className="flex items-center justify-between border-b border-line pb-2">
            <span className="font-bold text-ink uppercase tracking-wider flex items-center space-x-1.5">
              <Sliders className="w-3.5 h-3.5 text-brand-600" />
              <span>EVA map layers</span>
            </span>
            <button
              onClick={() => setIsLayerControlOpen(false)}
              className="text-ink-muted hover:text-ink"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Layer 1: Slope Hazard */}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={tacticalConfig.slopeHazardVisible}
                  onChange={(e) =>
                    onTacticalConfigChange({
                      ...tacticalConfig,
                      slopeHazardVisible: e.target.checked,
                    })
                  }
                  className="rounded text-success"
                />
                <span className="text-[11px] text-ink">1. Slope & Roughness Hazard</span>
              </label>
              <span className="text-[10px] text-ink-muted">
                {Math.round(tacticalConfig.slopeHazardOpacity * 100)}%
              </span>
            </div>
            <input
              type="range"
              min="0.1"
              max="1.0"
              step="0.05"
              value={tacticalConfig.slopeHazardOpacity}
              onChange={(e) =>
                onTacticalConfigChange({
                  ...tacticalConfig,
                  slopeHazardOpacity: parseFloat(e.target.value),
                })
              }
              className="w-full h-1 bg-surface-muted rounded-lg accent-brand-600"
            />
          </div>

          {/* Layer 2: Thermal Inertia & Regolith */}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={tacticalConfig.thermalRegolithVisible}
                  onChange={(e) =>
                    onTacticalConfigChange({
                      ...tacticalConfig,
                      thermalRegolithVisible: e.target.checked,
                    })
                  }
                  className="rounded text-brand-600"
                />
                <span className="text-[11px] text-ink">2. Regolith Firmness (THEMIS)</span>
              </label>
              <span className="text-[10px] text-ink-muted">
                {Math.round(tacticalConfig.thermalRegolithOpacity * 100)}%
              </span>
            </div>
            <input
              type="range"
              min="0.1"
              max="1.0"
              step="0.05"
              value={tacticalConfig.thermalRegolithOpacity}
              onChange={(e) =>
                onTacticalConfigChange({
                  ...tacticalConfig,
                  thermalRegolithOpacity: parseFloat(e.target.value),
                })
              }
              className="w-full h-1 bg-surface-muted rounded-lg accent-brand-600"
            />
          </div>

          {/* Layer 3: Science Targets */}
          <div className="flex items-center justify-between">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={tacticalConfig.scienceTargetsVisible}
                onChange={(e) =>
                  onTacticalConfigChange({
                    ...tacticalConfig,
                    scienceTargetsVisible: e.target.checked,
                  })
                }
                className="rounded text-warning"
              />
              <span className="text-[11px] text-ink">3. Astrobiology Science Targets</span>
            </label>
            <span className="text-[10px] text-warning font-bold">6 Pinned</span>
          </div>

          {/* Layer 4: Radiation Shielding */}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={tacticalConfig.radiationShieldingVisible}
                  onChange={(e) =>
                    onTacticalConfigChange({
                      ...tacticalConfig,
                      radiationShieldingVisible: e.target.checked,
                    })
                  }
                  className="rounded text-danger"
                />
                <span className="text-[11px] text-ink">4. RAD Cosmic Shielding</span>
              </label>
              <span className="text-[10px] text-ink-muted">
                {Math.round(tacticalConfig.radiationShieldingOpacity * 100)}%
              </span>
            </div>
            <input
              type="range"
              min="0.1"
              max="1.0"
              step="0.05"
              value={tacticalConfig.radiationShieldingOpacity}
              onChange={(e) =>
                onTacticalConfigChange({
                  ...tacticalConfig,
                  radiationShieldingOpacity: parseFloat(e.target.value),
                })
              }
              className="w-full h-1 bg-surface-muted rounded-lg accent-brand-600"
            />
          </div>
        </div>
      )}

      {/* 6. WAYPOINT INSPECTOR DRAWER (GROUND-LEVEL PERSEVERANCE IMAGERY) */}
      {isInspectorOpen && selectedTarget && (
        <div className="absolute top-16 right-6 bottom-24 w-96 bg-white border border-line-strong rounded-2xl p-4 shadow-2xl flex flex-col justify-between font-mono text-xs pointer-events-auto overflow-y-auto">
          <div className="space-y-3">
            {/* Header */}
            <div className="flex items-start justify-between border-b border-line pb-2">
              <div>
                <div className="text-[10px] uppercase text-brand-600 font-bold">
                  Science target
                </div>
                <h3 className="text-sm font-bold text-ink">{selectedTarget.name}</h3>
                <div className="text-[11px] text-warning font-semibold">
                  Science Priority: {selectedTarget.science_priority_score} / 100 • Astrobiology:{' '}
                  {selectedTarget.astrobiology_potential}
                </div>
              </div>
              <button
                onClick={() => setIsInspectorOpen(false)}
                className="text-ink-muted hover:text-ink"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Geological Context */}
            <div className="bg-surface-subtle p-2.5 rounded-lg border border-line text-[11px] text-ink-soft leading-relaxed">
              {selectedTarget.geological_context}
            </div>

            {/* Mineral Signatures */}
            <div className="space-y-1.5 text-[11px]">
              <div className="text-ink-muted font-bold uppercase text-[10px]">
                CRISM Mineral Signatures:
              </div>
              <div className="text-success font-semibold bg-success-soft px-2 py-1 rounded border border-success-line">
                {selectedTarget.crism_mineral_signature}
              </div>
            </div>

            {/* Ground-Level Perseverance Surface Imagery vs Orbital HiRISE */}
            <div className="space-y-1.5 pt-1">
              <div className="text-ink-muted font-bold uppercase text-[10px] flex items-center justify-between">
                <span>Ground-Level Camera (Sol {selectedTarget.perseverance_imagery.sol}):</span>
                <span className="text-brand-600">{selectedTarget.perseverance_imagery.camera}</span>
              </div>

              <div className="relative rounded-xl overflow-hidden border border-line bg-surface-muted aspect-video group">
                <img
                  src={selectedTarget.perseverance_imagery.local_thumbnail}
                  alt={selectedTarget.perseverance_imagery.caption}
                  className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                  onError={(e: any) => {
                    // Fallback to high-res direct NASA URL if local path fails
                    e.target.src = selectedTarget.perseverance_imagery.high_res_url;
                  }}
                />
                <div className="absolute bottom-1.5 left-2 right-2 px-2 py-1 rounded bg-brand-950/75 text-[10px] text-white">
                  {selectedTarget.perseverance_imagery.caption}
                </div>
              </div>
            </div>

            {/* Terrain Parameters */}
            <div className="grid grid-cols-2 gap-2 text-[10px]">
              <div className="bg-surface-muted p-2 rounded border border-line">
                <div className="text-ink-muted uppercase">Thermal Inertia:</div>
                <div className="text-ink font-bold">{selectedTarget.themis_thermal_inertia} SI</div>
                <div className="text-brand-600">{selectedTarget.surface_firmness}</div>
              </div>
              <div className="bg-surface-muted p-2 rounded border border-line">
                <div className="text-ink-muted uppercase">Radiation Shield:</div>
                <div className="text-ink font-bold">{selectedTarget.radiation_shielding}</div>
                <div className="text-warning">Slip Risk: {selectedTarget.slip_risk}</div>
              </div>
            </div>
          </div>

          {/* Target Actions */}
          <div className="pt-3 border-t border-line flex items-center justify-between">
            <span className="text-[10px] text-ink-muted font-mono">
              Coord: {selectedTarget.longitude.toFixed(4)}°E, {selectedTarget.latitude.toFixed(4)}°N
            </span>
            <button
              onClick={() => {
                const targetPoint: EvaPoint = {
                  longitude: selectedTarget.longitude,
                  latitude: selectedTarget.latitude,
                  elevation_m: selectedTarget.elevation_m,
                  name: selectedTarget.name,
                };
                const plan = planMetabolicEvaRoute([
                  { ...JEZERO_HAB_COORDINATES, isHab: true },
                  targetPoint,
                  { ...JEZERO_HAB_COORDINATES, isHab: true },
                ]);
                setRoutePlan(plan);
                onRoutePlanned(plan);
                setSimProgress(0);
                setIsSimulating(true);
                setIsInspectorOpen(false);
              }}
              className="px-3 py-1.5 rounded-lg bg-brand-700 hover:bg-brand-700 text-ink font-bold text-[10px] flex items-center space-x-1"
            >
              <span>Plan route to target</span>
              <ChevronRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
