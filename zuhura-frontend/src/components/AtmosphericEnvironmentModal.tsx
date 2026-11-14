import React, { useEffect, useState } from 'react';
import {
  X,
  Wind,
  Sun,
  Thermometer,
  Zap,
  Gauge,
  AlertTriangle,
  CheckCircle,
  Copy,
  Check,
  Compass,
  FileCode,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';
import { useEnvironmentStore, EnvironmentTab } from '../store/environmentStore';
import { useGlobeStore } from '../store/globeStore';
import { EpistemicBadge } from './EpistemicBadge';

export const AtmosphericEnvironmentModal: React.FC = () => {
  const {
    isEnvironmentModalOpen,
    setIsEnvironmentModalOpen,
    activeTab,
    setActiveTab,
    selectedLs,
    setSelectedLs,
    targetName,
    targetLat,
    targetLon,
    targetElevation,
    thermalInertia,
    setThermalInertia,
    panelArea,
    setPanelArea,
    globalDustMultiplier,
    setGlobalDustMultiplier,
    presets,
    loadPresets,
    applyPreset,
    assessment,
    runAssessment,
    isLoading,
    error,
  } = useEnvironmentStore();

  const { setCameraPosition, setActiveMainView } = useGlobeStore();
  const [copiedLatex, setCopiedLatex] = useState(false);
  const [copiedJson, setCopiedJson] = useState(false);

  useEffect(() => {
    if (isEnvironmentModalOpen) {
      loadPresets();
      if (!assessment) {
        runAssessment();
      }
    }
  }, [isEnvironmentModalOpen]);

  if (!isEnvironmentModalOpen) return null;

  const handleFlyToTarget = () => {
    setCameraPosition(targetLat, targetLon, 800000.0);
    setActiveMainView('explorer');
    setIsEnvironmentModalOpen(false);
  };

  const handleCopyLatex = () => {
    if (!assessment) return;
    const p = assessment.atmosphere.surface_pressure_pa;
    const tMin = assessment.thermal.min_surface_temp_k;
    const tMax = assessment.thermal.max_surface_temp_k;
    const tau = assessment.dust.tau_visible;
    const eSol = assessment.power_budget.daily_energy_wh_sol;

    const latex = `% Zuhura Mars Planetary Environmental Report
\\begin{table}[h!]
\\centering
\\caption{Planetary Environmental State for ${assessment.target_name} at $L_s = ${selectedLs}^\\circ$}
\\begin{tabular}{llr}
\\hline
\\textbf{Parameter} & \\textbf{Observed/Derived Value} & \\textbf{Unit} \\\\
\\hline
Planetocentric Latitude & $${targetLat.toFixed(2)}^\\circ$ & deg \\\\
Planetocentric Longitude & $${targetLon.toFixed(2)}^\\circ$ & deg \\\\
MOLA Surface Elevation & $${targetElevation.toFixed(1)}$ & m \\\\
Surface Barometric Pressure & $${p.toFixed(2)}$ & Pa \\\\
Visible Dust Optical Depth ($\\tau_{610}$) & $${tau.toFixed(2)}$ & dimensionless \\\\
Diurnal Minimum Surface Temp ($T_{\\min}$) & $${tMin.toFixed(1)}$ & K \\\\
Diurnal Maximum Surface Temp ($T_{\\max}$) & $${tMax.toFixed(1)}$ & K \\\\
Regolith Thermal Inertia ($I$) & $${thermalInertia.toFixed(0)}$ & $\\mathrm{J\\,m^{-2}\\,K^{-1}\\,s^{-1/2}}$ \\\\
Photovoltaic Daily Yield ($E_{\\mathrm{sol}}$) & $${eSol.toFixed(1)}$ & Wh/sol \\\\
Overall Site Viability Score & $${assessment.overall_site_viability_score.toFixed(1)}$ & / 100 \\\\
\\hline
\\end{tabular}
\\label{tab:zuhura_env_${assessment.target_name.toLowerCase().replace(/\\s+/g, '_')}}
\\end{table}`;

    navigator.clipboard.writeText(latex);
    setCopiedLatex(true);
    setTimeout(() => setCopiedLatex(false), 2000);
  };

  const handleCopyJson = () => {
    if (!assessment) return;
    navigator.clipboard.writeText(JSON.stringify(assessment, null, 2));
    setCopiedJson(true);
    setTimeout(() => setCopiedJson(false), 2000);
  };

  const tabs: { id: EnvironmentTab; label: string; icon: React.FC<{ className?: string }> }[] = [
    { id: 'overview', label: 'Mission Overview', icon: Gauge },
    { id: 'atmosphere', label: 'Atmosphere & Hypsometry', icon: Wind },
    { id: 'dust', label: 'Dust & Storm Risk', icon: Sun },
    { id: 'thermal', label: 'Diurnal Sol Thermal', icon: Thermometer },
    { id: 'power', label: 'Photovoltaic Budget', icon: Zap },
    { id: 'viability', label: 'Provenance & Citations', icon: ShieldCheck },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-brand-950/60 ">
      <div className="relative w-full max-w-6xl max-h-[92vh] flex flex-col rounded-xl border border-line-strong bg-surface-subtle text-ink shadow-2xl overflow-hidden font-sans">
        {/* Top Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-line bg-surface-subtle">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-brand-50 border border-brand-200 text-brand-600">
              <Wind className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-semibold text-ink">Environment</h2>
                <EpistemicBadge type="MODEL_ESTIMATED" compact />
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface-muted text-ink-soft border border-line">
                  MCD v5.3 / Viking / REMS
                </span>
              </div>
              <p className="text-xs text-ink-muted mt-0.5">
                Surface pressure, dust opacity, daily temperature and solar power for a chosen site and season.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => runAssessment()}
              disabled={isLoading}
              title="Refresh Simulation"
              className="p-2 rounded border border-line bg-surface-subtle hover:bg-surface-muted text-ink-soft transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-brand-600' : ''}`} />
            </button>
            <button
              onClick={() => setIsEnvironmentModalOpen(false)}
              className="p-2 rounded border border-line bg-surface-subtle hover:bg-surface-muted text-ink-soft hover:text-ink transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Global Planetary Orbital & Season Slider Bar */}
        <div className="px-6 py-3 border-b border-line bg-surface-subtle flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-4 flex-1 min-w-[280px]">
            <span className="text-xs font-semibold text-brand-600 whitespace-nowrap">
              Solar Longitude (L<sub>s</sub>):
            </span>
            <input
              type="range"
              min="0"
              max="359"
              step="1"
              value={selectedLs}
              onChange={(e) => setSelectedLs(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-surface-muted rounded-lg appearance-none cursor-pointer accent-brand-600"
            />
            <span className="text-xs font-mono font-bold text-ink px-2 py-1 bg-surface-muted rounded border border-line min-w-[54px] text-center">
              {selectedLs.toFixed(0)}&deg;
            </span>
          </div>

          {/* Quick Season Jump Buttons */}
          <div className="flex items-center space-x-1.5 text-[11px] font-mono">
            <button
              onClick={() => setSelectedLs(0)}
              className={`px-2 py-1 rounded transition-colors ${selectedLs === 0 ? 'bg-brand-50 text-brand-600 border border-brand-200' : 'bg-surface-subtle text-ink-muted hover:text-ink'}`}
            >
              L<sub>s</sub> 0&deg; (Vernal)
            </button>
            <button
              onClick={() => setSelectedLs(71)}
              className={`px-2 py-1 rounded transition-colors ${selectedLs === 71 ? 'bg-brand-50 text-brand-600 border border-brand-200' : 'bg-surface-subtle text-ink-muted hover:text-ink'}`}
            >
              L<sub>s</sub> 71&deg; (Aphelion)
            </button>
            <button
              onClick={() => setSelectedLs(180)}
              className={`px-2 py-1 rounded transition-colors ${selectedLs === 180 ? 'bg-brand-50 text-brand-600 border border-brand-200' : 'bg-surface-subtle text-ink-muted hover:text-ink'}`}
            >
              L<sub>s</sub> 180&deg; (Equinox)
            </button>
            <button
              onClick={() => setSelectedLs(251)}
              className={`px-2 py-1 rounded transition-colors ${selectedLs === 251 ? 'bg-brand-50 text-brand-600 border border-brand-600 font-bold' : 'bg-surface-subtle text-ink-muted hover:text-ink'}`}
            >
              L<sub>s</sub> 251&deg; (Perihelion Storm)
            </button>
          </div>
        </div>

        {/* Target Location Presets & Coordinates Bar */}
        <div className="px-6 py-2.5 border-b border-line bg-surface-subtle flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center space-x-2">
            <span className="text-ink-muted font-mono text-[11px]">Site:</span>
            <div className="flex items-center space-x-1 overflow-x-auto">
              {presets.map((p) => (
                <button
                  key={p.id}
                  onClick={() => applyPreset(p.id)}
                  className={`px-2.5 py-1 rounded text-[11px] font-mono whitespace-nowrap transition-colors ${
                    targetName.includes(p.name.split(' ')[0])
                      ? 'bg-warning-soft text-warning border border-warning-line font-semibold'
                      : 'bg-surface-subtle text-ink-soft hover:bg-surface-muted'
                  }`}
                >
                  {p.name.split('(')[0].trim()}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center space-x-4 font-mono text-[11px] text-ink-soft">
            <span>
              Lat: <strong className="text-ink">{targetLat.toFixed(2)}&deg;</strong>
            </span>
            <span>
              Lon: <strong className="text-ink">{targetLon.toFixed(2)}&deg;</strong>
            </span>
            <span>
              Elevation: <strong className="text-ink">{targetElevation.toFixed(0)} m</strong>
            </span>
            <button
              onClick={handleFlyToTarget}
              className="flex items-center space-x-1 px-2.5 py-0.5 rounded bg-brand-50 text-brand-600 hover:bg-brand-50 border border-brand-200 transition-colors"
            >
              <Compass className="w-3.5 h-3.5" />
              <span>Fly on Globe</span>
            </button>
          </div>
        </div>

        {/* Console Sub-navigation Tabs */}
        <div className="flex items-center px-6 border-b border-line bg-surface-subtle">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-3 px-4 border-b-2 text-xs font-medium transition-all ${
                  isActive
                    ? 'border-brand-600 text-brand-600 font-semibold bg-surface-subtle'
                    : 'border-transparent text-ink-muted hover:text-ink hover:border-line-strong'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-brand-600' : 'text-ink-muted'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Main Content Area */}
        <div className="flex-1 overflow-y-auto p-6 bg-white space-y-6">
          {error && (
            <div className="p-3 rounded-lg bg-danger-soft border border-danger-line text-danger text-xs flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 shrink-0 text-danger" />
              <span>{error}</span>
            </div>
          )}

          {isLoading && !assessment && (
            <div className="flex flex-col items-center justify-center py-20 space-y-3">
              <RefreshCw className="w-8 h-8 text-brand-600 animate-spin" />
              <p className="text-sm font-mono text-ink-muted">
                Computing Martian atmospheric hypsometry & solar insolation...
              </p>
            </div>
          )}

          {assessment && (
            <>
              {/* TAB 1: MISSION OVERVIEW */}
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  {/* Top Stats Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="p-4 rounded-xl border border-line bg-surface-subtle">
                      <div className="text-[11px] text-ink-muted">Site Viability Score</div>
                      <div className="mt-1 flex items-baseline space-x-2">
                        <span className="text-3xl font-mono font-bold text-ink">
                          {assessment.overall_site_viability_score.toFixed(1)}
                        </span>
                        <span className="text-xs font-mono text-ink-muted">/ 100</span>
                      </div>
                      <div className="mt-2 w-full bg-surface-muted h-1.5 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${
                            assessment.overall_site_viability_score >= 75
                              ? 'bg-success'
                              : assessment.overall_site_viability_score >= 50
                                ? 'bg-warning'
                                : 'bg-danger'
                          }`}
                          style={{ width: `${assessment.overall_site_viability_score}%` }}
                        />
                      </div>
                    </div>

                    <div className="p-4 rounded-xl border border-line bg-surface-subtle">
                      <div className="text-[11px] text-ink-muted">Surface Pressure</div>
                      <div className="mt-1 flex items-baseline space-x-2">
                        <span className="text-3xl font-mono font-bold text-ink">
                          {assessment.atmosphere.surface_pressure_pa.toFixed(0)}
                        </span>
                        <span className="text-xs font-mono text-ink-muted">
                          Pa ({assessment.atmosphere.surface_pressure_mbar.toFixed(2)} mbar)
                        </span>
                      </div>
                      <div className="mt-2 text-[11px] font-mono">
                        {assessment.atmosphere.above_water_triple_point ? (
                          <span className="text-success font-semibold flex items-center space-x-1">
                            <CheckCircle className="w-3 h-3" />
                            <span>Above Triple Point (611.7 Pa)</span>
                          </span>
                        ) : (
                          <span className="text-warning">Below Water Triple Point</span>
                        )}
                      </div>
                    </div>

                    <div className="p-4 rounded-xl border border-line bg-surface-subtle">
                      <div className="text-[11px] text-ink-muted">Dust Optical Depth (&tau;)</div>
                      <div className="mt-1 flex items-baseline space-x-2">
                        <span className="text-3xl font-mono font-bold text-ink">
                          {assessment.dust.tau_visible.toFixed(2)}
                        </span>
                        <span
                          className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${
                            assessment.dust.opacity_category === 'CLEAR'
                              ? 'bg-success-soft text-success'
                              : assessment.dust.opacity_category === 'MODERATE_DUST'
                                ? 'bg-warning-soft text-warning'
                                : 'bg-danger-soft text-danger'
                          }`}
                        >
                          {assessment.dust.opacity_category}
                        </span>
                      </div>
                      <div className="mt-2 text-[11px] font-mono text-ink-muted">
                        Risk Index: {(assessment.dust.dust_storm_risk_index * 100).toFixed(0)}%
                      </div>
                    </div>

                    <div className="p-4 rounded-xl border border-line bg-surface-subtle">
                      <div className="text-[11px] text-ink-muted">Photovoltaic Energy</div>
                      <div className="mt-1 flex items-baseline space-x-2">
                        <span className="text-3xl font-mono font-bold text-ink">
                          {assessment.power_budget.daily_energy_wh_sol.toFixed(0)}
                        </span>
                        <span className="text-xs font-mono text-ink-muted">Wh / sol</span>
                      </div>
                      <div className="mt-2 text-[11px] font-mono text-brand-600 font-semibold">
                        Status: {assessment.power_budget.operational_status}
                      </div>
                    </div>
                  </div>

                  {/* Orbital Mechanics & Heliocentric Parameters */}
                  <div className="p-5 rounded-xl border border-line bg-surface-subtle">
                    <h3 className="text-xs font-semibold text-brand-600 mb-3 flex items-center space-x-2">
                      <Compass className="w-4 h-4" />
                      <span>Orbital Ephemeris & Seasonal Geometry</span>
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
                      <div>
                        <span className="text-ink-muted block">Heliocentric Distance:</span>
                        <strong className="text-ink text-sm">{assessment.orbital.heliocentric_distance_au} AU</strong>
                      </div>
                      <div>
                        <span className="text-ink-muted block">Solar Constant (TOA):</span>
                        <strong className="text-ink text-sm">
                          {assessment.orbital.top_of_atmosphere_solar_flux_w_m2} W/m&sup2;
                        </strong>
                      </div>
                      <div>
                        <span className="text-ink-muted block">Solar Declination:</span>
                        <strong className="text-ink text-sm">{assessment.orbital.solar_declination_deg}&deg;</strong>
                      </div>
                      <div>
                        <span className="text-ink-muted block">Dust Season Risk:</span>
                        <strong className="text-warning text-sm">{assessment.orbital.dust_season_risk}</strong>
                      </div>
                    </div>
                    <div className="mt-3 pt-3 border-t border-line flex items-center justify-between text-xs text-ink-muted">
                      <span>
                        <strong>Northern Hemisphere:</strong> {assessment.orbital.season_northern}
                      </span>
                      <span>
                        <strong>Southern Hemisphere:</strong> {assessment.orbital.season_southern}
                      </span>
                    </div>
                  </div>

                  {/* Environmental Hazards */}
                  <div className="p-5 rounded-xl border border-line bg-surface-subtle">
                    <h3 className="text-xs font-semibold text-warning mb-3 flex items-center space-x-2">
                      <AlertTriangle className="w-4 h-4" />
                      <span>Hazards</span>
                    </h3>
                    {assessment.environmental_hazards.length === 0 ? (
                      <p className="text-xs font-mono text-success flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4" />
                        <span>
                          Nominal conditions: No severe atmospheric or thermal hazards identified at this site and
                          season.
                        </span>
                      </p>
                    ) : (
                      <div className="space-y-2">
                        {assessment.environmental_hazards.map((hazard, idx) => (
                          <div
                            key={idx}
                            className="p-2.5 rounded-lg bg-warning-soft border border-warning-line text-warning text-xs font-mono flex items-start space-x-2"
                          >
                            <span className="text-warning font-bold">&bull;</span>
                            <span>{hazard}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* TAB 2: ATMOSPHERE & HYPSOMETRY */}
              {activeTab === 'atmosphere' && (
                <div className="space-y-6">
                  {/* Hypsometry Summary */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 rounded-xl border border-line bg-surface-subtle">
                      <div className="text-[11px] text-ink-muted">Atmospheric Scale Height</div>
                      <div className="mt-1 text-2xl font-mono font-bold text-ink">
                        {assessment.atmosphere.scale_height_km} km
                      </div>
                      <div className="text-[11px] font-mono text-ink-muted mt-1">
                        H = R<sub>spec</sub>T / g<sub>mars</sub> (Martian R<sub>spec</sub> = 191.8 J/kg&middot;K)
                      </div>
                    </div>

                    <div className="p-4 rounded-xl border border-line bg-surface-subtle">
                      <div className="text-[11px] text-ink-muted">Surface Gas Density</div>
                      <div className="mt-1 text-2xl font-mono font-bold text-ink">
                        {assessment.atmosphere.surface_density_kg_m3} kg/m&sup3;
                      </div>
                      <div className="text-[11px] font-mono text-ink-muted mt-1">
                        ~1.5% of Earth sea-level air density
                      </div>
                    </div>

                    <div className="p-4 rounded-xl border border-line bg-surface-subtle">
                      <div className="text-[11px] text-ink-muted">Adiabatic Lapse Rate</div>
                      <div className="mt-1 text-2xl font-mono font-bold text-ink">
                        {assessment.atmosphere.adiabatic_lapse_rate_k_km} K / km
                      </div>
                      <div className="text-[11px] font-mono text-ink-muted mt-1">
                        CO<sub>2</sub> lower troposphere lapse
                      </div>
                    </div>
                  </div>

                  {/* Atmospheric Chemical Composition */}
                  <div className="p-5 rounded-xl border border-line bg-surface-subtle">
                    <h3 className="text-xs font-semibold text-brand-600 mb-3">
                      Mars Atmospheric Chemical Composition (Molar Fractions)
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
                      {Object.entries(assessment.atmosphere.gas_composition_molar_pct).map(([gas, pct]) => (
                        <div key={gas} className="p-2.5 rounded bg-surface-subtle border border-line">
                          <span className="text-ink-muted block text-[11px]">{gas}:</span>
                          <strong className="text-ink text-sm">{pct}%</strong>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Vertical Atmospheric Layers Table */}
                  <div className="p-5 rounded-xl border border-line bg-surface-subtle">
                    <h3 className="text-xs font-semibold text-brand-600 mb-3">
                      Vertical Atmospheric Column Hypsometric Profile (Surface to 50 km)
                    </h3>
                    <div className="overflow-x-auto max-h-72">
                      <table className="w-full text-left font-mono text-[11px] text-ink-soft">
                        <thead className="sticky top-0 bg-surface-subtle text-ink-muted border-b border-line">
                          <tr>
                            <th className="py-2 px-3">Altitude (km)</th>
                            <th className="py-2 px-3">Elevation Areoid (m)</th>
                            <th className="py-2 px-3">Pressure (Pa)</th>
                            <th className="py-2 px-3">Pressure (mbar)</th>
                            <th className="py-2 px-3">Density (kg/m&sup3;)</th>
                            <th className="py-2 px-3">Temp (K)</th>
                            <th className="py-2 px-3">Temp (&deg;C)</th>
                            <th className="py-2 px-3">Speed of Sound</th>
                            <th className="py-2 px-3">Earth Equiv Alt</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-line">
                          {assessment.atmosphere.layers.map((layer) => (
                            <tr key={layer.altitude_above_surface_km} className="hover:bg-surface-subtle">
                              <td className="py-2 px-3 font-semibold text-ink">
                                {layer.altitude_above_surface_km.toFixed(1)}
                              </td>
                              <td className="py-2 px-3">{layer.elevation_above_areoid_m.toFixed(0)}</td>
                              <td className="py-2 px-3 text-brand-600">{layer.pressure_pa.toFixed(1)}</td>
                              <td className="py-2 px-3">{layer.pressure_mbar.toFixed(3)}</td>
                              <td className="py-2 px-3">{layer.density_kg_m3.toFixed(5)}</td>
                              <td className="py-2 px-3">{layer.temperature_k.toFixed(1)}</td>
                              <td className="py-2 px-3">{layer.temperature_c.toFixed(1)}&deg;C</td>
                              <td className="py-2 px-3">{layer.speed_of_sound_m_s.toFixed(1)} m/s</td>
                              <td className="py-2 px-3 text-ink-muted">
                                {layer.earth_equivalent_altitude_km.toFixed(1)} km
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 3: DUST & STORM RISK */}
              {activeTab === 'dust' && (
                <div className="space-y-6">
                  {/* Dust Overview Banner */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 rounded-xl border border-line bg-surface-subtle">
                      <div className="text-[11px] text-ink-muted">
                        Visible Dust Tau (&tau;<sub>610</sub>)
                      </div>
                      <div className="mt-1 text-3xl font-mono font-bold text-ink">
                        {assessment.dust.tau_visible.toFixed(2)}
                      </div>
                      <div className="mt-2 text-xs font-mono text-ink-muted">
                        Direct Solar Transmission: {(assessment.dust.direct_transmission_zenith * 100).toFixed(1)}%
                      </div>
                    </div>

                    <div className="p-4 rounded-xl border border-line bg-surface-subtle">
                      <div className="text-[11px] text-ink-muted">Diffuse Scattering Fraction</div>
                      <div className="mt-1 text-3xl font-mono font-bold text-brand-600">
                        {(assessment.dust.diffuse_scattering_fraction * 100).toFixed(1)}%
                      </div>
                      <div className="mt-2 text-xs font-mono text-ink-muted">Forward scattered sunlight to ground</div>
                    </div>

                    <div className="p-4 rounded-xl border border-line bg-surface-subtle">
                      <div className="text-[11px] text-ink-muted">Basin Amplification</div>
                      <div className="mt-1 text-2xl font-mono font-bold text-ink">
                        {assessment.dust.is_basin_amplified ? (
                          <span className="text-warning">Active basin</span>
                        ) : (
                          <span className="text-ink-muted">Standard terrain</span>
                        )}
                      </div>
                      <div className="mt-2 text-xs font-mono text-ink-muted">
                        Thermal wind convergence in low depression
                      </div>
                    </div>
                  </div>

                  {/* Dust Storm Controls */}
                  <div className="p-5 rounded-xl border border-line bg-surface-subtle">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-xs font-semibold text-warning">Global Dust Storm Simulation Multiplier</h3>
                      <span className="text-xs font-mono font-bold text-ink px-2 py-0.5 rounded bg-surface-muted border border-line">
                        {globalDustMultiplier.toFixed(1)}x
                      </span>
                    </div>
                    <input
                      type="range"
                      min="0.5"
                      max="4.0"
                      step="0.1"
                      value={globalDustMultiplier}
                      onChange={(e) => setGlobalDustMultiplier(parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-surface-muted rounded-lg appearance-none cursor-pointer accent-brand-600"
                    />
                    <div className="flex justify-between text-[10px] font-mono text-ink-muted mt-2">
                      <span>0.5x (Super Clear)</span>
                      <span>1.0x (Standard Climatology)</span>
                      <span>2.0x (Regional Dust Storm)</span>
                      <span>4.0x (Planet-Encircling Storm)</span>
                    </div>
                  </div>

                  {/* Operational Recommendations */}
                  <div className="p-5 rounded-xl border border-line bg-surface-subtle">
                    <h3 className="text-xs font-semibold text-brand-600 mb-3">
                      Rover Tactical Operations & Mitigations
                    </h3>
                    <div className="space-y-2">
                      {assessment.dust.operational_recommendations.map((rec, idx) => (
                        <div
                          key={idx}
                          className="p-3 rounded-lg bg-surface-subtle border border-line text-xs font-mono text-ink-soft flex items-start space-x-2"
                        >
                          <CheckCircle className="w-4 h-4 text-brand-600 shrink-0 mt-0.5" />
                          <span>{rec}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 4: DIURNAL THERMAL SWINGS */}
              {activeTab === 'thermal' && (
                <div className="space-y-6">
                  {/* Thermal Inertia Configurator */}
                  <div className="p-5 rounded-xl border border-line bg-surface-subtle">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <span className="text-xs font-semibold text-brand-600">Regolith Thermal Inertia (I):</span>
                        <div className="text-xs font-mono text-ink-soft mt-0.5">
                          Classification: <strong className="text-warning">{assessment.thermal.regolith_type}</strong>
                        </div>
                      </div>
                      <span className="text-xs font-mono font-bold text-ink px-2 py-1 bg-surface-muted rounded border border-line">
                        {thermalInertia.toFixed(0)} TIU (J m&sup-2; K&sup-1; s&sup-1/2;)
                      </span>
                    </div>
                    <input
                      type="range"
                      min="50"
                      max="900"
                      step="25"
                      value={thermalInertia}
                      onChange={(e) => setThermalInertia(parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-surface-muted rounded-lg appearance-none cursor-pointer accent-brand-600 mt-2"
                    />
                    <div className="flex justify-between text-[10px] font-mono text-ink-muted mt-1">
                      <span>50 TIU (Fine Dust)</span>
                      <span>250 TIU (Sand Dunes)</span>
                      <span>500 TIU (Duricrust)</span>
                      <span>800+ TIU (Bedrock)</span>
                    </div>
                  </div>

                  {/* Thermal Metrics */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 rounded-xl border border-line bg-surface-subtle">
                      <div className="text-[11px] text-ink-muted">Min Temp (Nocturnal)</div>
                      <div className="mt-1 text-2xl font-mono font-bold text-brand-600">
                        {assessment.thermal.min_surface_temp_k.toFixed(1)} K
                      </div>
                      <div className="text-[11px] font-mono text-ink-muted">
                        ({(assessment.thermal.min_surface_temp_k - 273.15).toFixed(1)}&deg;C)
                      </div>
                    </div>

                    <div className="p-4 rounded-xl border border-line bg-surface-subtle">
                      <div className="text-[11px] text-ink-muted">Max Temp (Solar Noon)</div>
                      <div className="mt-1 text-2xl font-mono font-bold text-brand-600">
                        {assessment.thermal.max_surface_temp_k.toFixed(1)} K
                      </div>
                      <div className="text-[11px] font-mono text-ink-muted">
                        ({(assessment.thermal.max_surface_temp_k - 273.15).toFixed(1)}&deg;C)
                      </div>
                    </div>

                    <div className="p-4 rounded-xl border border-line bg-surface-subtle">
                      <div className="text-[11px] text-ink-muted">Diurnal Swing (&Delta;T)</div>
                      <div className="mt-1 text-2xl font-mono font-bold text-ink">
                        {assessment.thermal.diurnal_temperature_swing_k.toFixed(1)} K
                      </div>
                      <div className="text-[11px] font-mono text-ink-muted">Daily thermal cycle range</div>
                    </div>

                    <div className="p-4 rounded-xl border border-line bg-surface-subtle">
                      <div className="text-[11px] text-ink-muted">
                        CO<sub>2</sub> Frost Risk
                      </div>
                      <div className="mt-1 text-2xl font-mono font-bold">
                        {assessment.thermal.co2_frost_present ? (
                          <span className="text-brand-600">Frost likely</span>
                        ) : (
                          <span className="text-success">No frost</span>
                        )}
                      </div>
                      <div className="text-[11px] font-mono text-ink-muted">T &le; 148 K sublimation point</div>
                    </div>
                  </div>

                  {/* 24-Hour Diurnal Sol Curve Table */}
                  <div className="p-5 rounded-xl border border-line bg-surface-subtle">
                    <h3 className="text-xs font-semibold text-brand-600 mb-3">
                      24-Hour Martian Sol Diurnal Temperature & Insolation Profile
                    </h3>
                    <div className="overflow-x-auto max-h-72">
                      <table className="w-full text-left font-mono text-[11px] text-ink-soft">
                        <thead className="sticky top-0 bg-surface-subtle text-ink-muted border-b border-line">
                          <tr>
                            <th className="py-2 px-3">Local Solar Time</th>
                            <th className="py-2 px-3">Zenith Angle</th>
                            <th className="py-2 px-3">Solar Irradiance (W/m&sup2;)</th>
                            <th className="py-2 px-3">Surface Temp (K)</th>
                            <th className="py-2 px-3">Surface Temp (&deg;C)</th>
                            <th className="py-2 px-3">Air Temp 2m (K)</th>
                            <th className="py-2 px-3">
                              CO<sub>2</sub> Frost
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-line">
                          {assessment.thermal.hourly_curve.map((h) => (
                            <tr key={h.local_solar_time_hours} className="hover:bg-surface-subtle">
                              <td className="py-2 px-3 font-semibold text-ink">
                                {h.local_solar_time_hours.toFixed(0)}:00 Sol
                              </td>
                              <td className="py-2 px-3">{h.solar_zenith_angle_deg.toFixed(1)}&deg;</td>
                              <td className="py-2 px-3 text-brand-600">{h.solar_irradiance_w_m2.toFixed(1)}</td>
                              <td className="py-2 px-3">{h.surface_temperature_k.toFixed(1)}</td>
                              <td className="py-2 px-3">{h.surface_temperature_c.toFixed(1)}&deg;C</td>
                              <td className="py-2 px-3 text-ink-muted">{h.air_temperature_2m_k.toFixed(1)}</td>
                              <td className="py-2 px-3">
                                {h.co2_frost_risk ? (
                                  <span className="text-brand-600 font-bold">FROST</span>
                                ) : (
                                  <span className="text-ink-faint">-</span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 5: PHOTOVOLTAIC POWER BUDGET */}
              {activeTab === 'power' && (
                <div className="space-y-6">
                  {/* Array Size Configuration */}
                  <div className="p-5 rounded-xl border border-line bg-surface-subtle">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-semibold text-brand-600">
                        Photovoltaic Array Area (A<sub>pv</sub>):
                      </span>
                      <span className="text-xs font-mono font-bold text-ink px-2 py-1 bg-surface-muted rounded border border-line">
                        {panelArea.toFixed(1)} m&sup2;
                      </span>
                    </div>
                    <input
                      type="range"
                      min="0.5"
                      max="15.0"
                      step="0.5"
                      value={panelArea}
                      onChange={(e) => setPanelArea(parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-surface-muted rounded-lg appearance-none cursor-pointer accent-brand-600 mt-2"
                    />
                    <div className="flex justify-between text-[10px] font-mono text-ink-muted mt-1">
                      <span>1.3 m&sup2; (MER Opportunity)</span>
                      <span>7.0 m&sup2; (InSight Lander)</span>
                      <span>15.0 m&sup2; (Mars Habitat Array)</span>
                    </div>
                  </div>

                  {/* Power Metrics */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 rounded-xl border border-line bg-surface-subtle">
                      <div className="text-[11px] text-ink-muted">Daily Energy Yield</div>
                      <div className="mt-1 text-3xl font-mono font-bold text-ink">
                        {assessment.power_budget.daily_energy_wh_sol.toFixed(0)}
                      </div>
                      <div className="text-xs font-mono text-ink-muted mt-1">Watt-hours per 24.66-hour Martian Sol</div>
                    </div>

                    <div className="p-4 rounded-xl border border-line bg-surface-subtle">
                      <div className="text-[11px] text-ink-muted">Peak Electrical Power</div>
                      <div className="mt-1 text-3xl font-mono font-bold text-brand-600">
                        {assessment.power_budget.peak_power_w.toFixed(1)} W
                      </div>
                      <div className="text-xs font-mono text-ink-muted mt-1">At solar noon (maximum insolation)</div>
                    </div>

                    <div className="p-4 rounded-xl border border-line bg-surface-subtle">
                      <div className="text-[11px] text-ink-muted">Operational Status</div>
                      <div className="mt-1 text-lg font-mono font-bold text-warning">
                        {assessment.power_budget.operational_status}
                      </div>
                      <div className="text-xs font-mono text-ink-muted mt-1">
                        MER-class survival threshold: 220 Wh/sol
                      </div>
                    </div>
                  </div>

                  {/* Rover Compatibility Matrix */}
                  <div className="p-5 rounded-xl border border-line bg-surface-subtle">
                    <h3 className="text-xs font-semibold text-brand-600 mb-3">
                      Planetary Rover / Lander Power Compatibility Matrix
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
                      <div className="p-3.5 rounded-lg bg-surface-subtle border border-line">
                        <span className="font-semibold text-ink block mb-1">MER (Opportunity / Spirit)</span>
                        <div className="text-ink-muted text-[11px] space-y-1">
                          <div>Array Area: 1.3 m&sup2;</div>
                          <div>Survival: 220 Wh/sol</div>
                          <div>Nominal Drive: 650 Wh/sol</div>
                          <div className="mt-2 font-bold text-brand-600">
                            Status:{' '}
                            {assessment.power_budget.rover_compatibility?.mer_opportunity_spirit?.current_status}
                          </div>
                        </div>
                      </div>

                      <div className="p-3.5 rounded-lg bg-surface-subtle border border-line">
                        <span className="font-semibold text-ink block mb-1">InSight Lander</span>
                        <div className="text-ink-muted text-[11px] space-y-1">
                          <div>Array Area: 7.0 m&sup2;</div>
                          <div>Survival: 480 Wh/sol</div>
                          <div>Science Ops: 1200 Wh/sol</div>
                          <div className="mt-2 font-bold text-warning">
                            Status: {assessment.power_budget.rover_compatibility?.insight_lander?.current_status}
                          </div>
                        </div>
                      </div>

                      <div className="p-3.5 rounded-lg bg-surface-subtle border border-line">
                        <span className="font-semibold text-ink block mb-1">Perseverance / Curiosity</span>
                        <div className="text-ink-muted text-[11px] space-y-1">
                          <div>Power Source: Nuclear MMRTG</div>
                          <div>Continuous: 2400 Wh/sol</div>
                          <div>Dust Vulnerability: IMMUNE</div>
                          <div className="mt-2 font-bold text-success">Status: FULL_NOMINAL_DRIVE</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 6: PROVENANCE & CITATIONS */}
              {activeTab === 'viability' && (
                <div className="space-y-6">
                  {/* Epistemic Provenance Card */}
                  <div className="p-5 rounded-xl border border-line bg-surface-subtle space-y-3 font-mono text-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-ink-muted uppercase font-semibold">Provenance Metadata</span>
                      <EpistemicBadge type="MODEL_ESTIMATED" compact />
                    </div>
                    <div className="grid grid-cols-2 gap-3 text-ink-soft pt-2 border-t border-line">
                      <div>
                        <span className="text-ink-muted block">Original Dataset:</span>
                        <strong className="text-ink">{assessment.provenance?.original_dataset_id}</strong>
                      </div>
                      <div>
                        <span className="text-ink-muted block">Processing Algorithm:</span>
                        <strong className="text-ink">{assessment.provenance?.processing_algorithm}</strong>
                      </div>
                      <div>
                        <span className="text-ink-muted block">Coordinate Reference:</span>
                        <strong className="text-ink">{assessment.provenance?.coordinate_reference_system}</strong>
                      </div>
                      <div>
                        <span className="text-ink-muted block">Vertical Elevation Datum:</span>
                        <strong className="text-ink">{assessment.provenance?.vertical_datum}</strong>
                      </div>
                    </div>
                    <div className="p-3 rounded bg-surface-subtle border border-line text-[11px] text-ink-muted mt-2">
                      <strong className="text-warning">Note: </strong>
                      {assessment.provenance?.disclaimer}
                    </div>
                  </div>

                  {/* Peer-Reviewed References */}
                  <div className="p-5 rounded-xl border border-line bg-surface-subtle space-y-3">
                    <h3 className="text-xs font-semibold text-brand-600">Peer-Reviewed Literature References</h3>
                    <div className="space-y-2 text-xs font-mono text-ink-soft">
                      <div className="p-2.5 rounded bg-surface-subtle border border-line">
                        <strong>Forget, F., et al. (1999).</strong> Improved general circulation models of the Martian
                        atmosphere from the surface to above 80 km. <em>Journal of Geophysical Research: Planets</em>,
                        104(E10), 24155-24175.
                      </div>
                      <div className="p-2.5 rounded bg-surface-subtle border border-line">
                        <strong>Hess, S. L., et al. (1980).</strong> The annual cycle of pressure on Mars measured by
                        Viking Landers 1 and 2. <em>Tellus</em>, 32(3), 238-251.
                      </div>
                      <div className="p-2.5 rounded bg-surface-subtle border border-line">
                        <strong>Montabone, L., et al. (2015).</strong> An open-access database of Martian atmospheric
                        dust optical depth for 12 Martian years. <em>Icarus</em>, 251, 65-95.
                      </div>
                      <div className="p-2.5 rounded bg-surface-subtle border border-line">
                        <strong>Appelbaum, J., & Flood, D. J. (1990).</strong> Solar radiation on Mars.{' '}
                        <em>Solar Energy</em>, 45(6), 353-363.
                      </div>
                    </div>
                  </div>

                  {/* Scientific Export Actions */}
                  <div className="flex items-center space-x-3">
                    <button
                      onClick={handleCopyLatex}
                      className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-brand-50 text-brand-600 hover:bg-brand-50 border border-brand-200 text-xs font-mono transition-colors"
                    >
                      {copiedLatex ? <Check className="w-4 h-4 text-success" /> : <FileCode className="w-4 h-4" />}
                      <span>{copiedLatex ? 'LaTeX Copied!' : 'Copy LaTeX Table'}</span>
                    </button>
                    <button
                      onClick={handleCopyJson}
                      className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-surface-muted text-ink hover:bg-surface-muted border border-line-strong text-xs font-mono transition-colors"
                    >
                      {copiedJson ? <Check className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4" />}
                      <span>{copiedJson ? 'JSON Copied!' : 'Export JSON Manifest'}</span>
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
