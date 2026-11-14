import React from 'react';
import { ArrowRight } from 'lucide-react';
import { useGlobeStore } from '../store/globeStore';
import { useAIStore } from '../store/aiStore';

export const MissionOverviewDashboard: React.FC = () => {
  const {
    activeMainView,
    setActiveMainView,
    setSelectedTerrain,
    setSelectedFeature,
    setCameraPosition,
    setIsXRayMarsOpen,
    setIsRoutePlannerOpen,
    setIsMissionBriefingOpen,
  } = useGlobeStore();
  const { toggleOpen: toggleAI } = useAIStore();

  if (activeMainView !== 'overview') return null;

  const EXPLORATION_ZONES = [
    {
      id: 'jezero',
      name: 'Jezero Crater',
      mission: 'Mars 2020 Perseverance & Ingenuity',
      lat: 18.38,
      lon: 77.58,
      elevation: -2530,
      diameter: '49 km',
      geology: 'Fan-delta system embedded in ancient Noachian/Early Hesperian impact basin with smectite clay phyllosilicates.',
      status: 'Perseverance landing site (2021)',
      camera: { lat: 18.38, lon: 77.58, alt: 180000 },
      badge: 'Delta scarp',
    },
    {
      id: 'gale',
      name: 'Gale Crater (Mount Sharp)',
      mission: 'Mars Science Laboratory Curiosity',
      lat: -4.59,
      lon: 137.44,
      elevation: -4503,
      diameter: '154 km',
      geology: 'Central 5.5 km layered sedimentary mound Aeolis Mons recording a shift from clay to sulfate-bearing units.',
      status: 'Curiosity landing site (2012)',
      camera: { lat: -4.59, lon: 137.44, alt: 180000 },
      badge: 'Sulfate unit',
    },
    {
      id: 'valles_marineris',
      name: 'Valles Marineris (Chasmata)',
      mission: 'Orbital Reconnaissance (MRO / MEX / MAVEN)',
      lat: -9.5,
      lon: 283.0,
      elevation: -1372,
      diameter: '4,000 km',
      geology: 'Equatorial canyon system up to about 7 km deep with hydrated sulfate deposits and recurring slope lineae (RSL).',
      status: 'Studied from orbit',
      camera: { lat: -9.5, lon: 283.0, alt: 850000 },
      badge: 'Tectonic rift',
    },
    {
      id: 'olympus_mons',
      name: 'Olympus Mons',
      mission: 'Global Topography Reference',
      lat: 18.65,
      lon: 226.2,
      elevation: 20015,
      diameter: '624 km',
      geology: 'Largest shield volcano in Solar System, towering 21.2 km above datum with multiple nested summit collapse calderas.',
      status: 'Elevation reference',
      camera: { lat: 18.65, lon: 226.2, alt: 500000 },
      badge: 'Shield volcano',
    },
  ];

  const handleFlyToZone = (zone: typeof EXPLORATION_ZONES[0]) => {
    setSelectedTerrain(zone.id);
    setSelectedFeature({
      id: `${zone.id}-feature`,
      name: zone.name,
      type: 'crater',
      latitude: zone.lat,
      longitude: zone.lon,
      diameter_km: parseFloat(zone.diameter),
      elevation_m: zone.elevation,
      description: zone.geology,
    });
    setCameraPosition(zone.camera.lat, zone.camera.lon, zone.camera.alt);
    setActiveMainView('explorer');
  };

  const facts = [
    ['Equatorial radius', '3,396,190 m', 'IAU 2015'],
    ['Polar radius', '3,376,200 m', 'Flattening 1/169.8'],
    ['Surface gravity', '3.7208 m/s²', '0.3794 Earth g'],
    ['Vertical datum', 'MOLA GMM-2B', 'Equipotential surface'],
    ['Metallic core', '1,650 ± 20 km', 'Samuel & Khan 2023'],
    ['Earth–Mars signal delay', '3–22 min', 'Varies with orbital distance'],
  ];

  const tools = [
    {
      title: 'Traverse',
      body: 'Plan a rover path from slope, soil slip, and the sunlight available along the way.',
      action: 'Open traverse',
      onClick: () => {
        setActiveMainView('explorer');
        setIsRoutePlannerOpen(true);
      },
    },
    {
      title: 'X-ray',
      body: 'Look through the crust, mantle, and core using the InSight seismic models from 2021 and 2023.',
      action: 'Open interior',
      onClick: () => setIsXRayMarsOpen(true),
    },
    {
      title: 'Ask Zuhura',
      body: 'Ask about a place. Answers stay tied to published sources and say when something is only a hypothesis.',
      action: 'Open assistant',
      onClick: toggleAI,
    },
  ];

  return (
    <div className="fixed inset-0 top-14 left-16 z-20 overflow-y-auto bg-surface-subtle text-ink font-sans">
      <div className="mx-auto max-w-6xl px-5 py-8 md:px-10 md:py-12">
        <header className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
          <div className="max-w-xl">
            <p className="text-sm font-medium text-brand-600">Overview</p>
            <h1 className="mt-1 text-3xl font-semibold tracking-tight md:text-4xl">A quiet look at Mars</h1>
            <p className="mt-3 text-sm leading-relaxed text-ink-soft md:text-base">
              Reference numbers, four places to open on the globe, and the tools that sit next to the map.
            </p>
          </div>
          <div className="flex shrink-0 gap-2">
            <button
              onClick={() => setIsMissionBriefingOpen(true)}
              className="rounded-full border border-line-strong bg-white px-4 py-2 text-sm text-ink hover:bg-surface-subtle"
            >
              Briefing
            </button>
            <button
              onClick={() => setActiveMainView('explorer')}
              className="rounded-full bg-brand-700 px-4 py-2 text-sm font-medium text-white hover:bg-brand-800"
            >
              Open the globe
            </button>
          </div>
        </header>

        <dl className="mt-10 grid grid-cols-2 gap-x-6 gap-y-5 border-y border-line py-5 sm:grid-cols-3 lg:grid-cols-6">
          {facts.map(([label, value, note]) => (
            <div key={label}>
              <dt className="text-[12px] text-ink-muted">{label}</dt>
              <dd className="mt-1 text-sm font-medium tabular-nums text-ink">{value}</dd>
              <dd className="mt-0.5 text-[11px] text-ink-faint">{note}</dd>
            </div>
          ))}
        </dl>

        <section className="mt-12">
          <div className="flex items-end justify-between gap-4">
            <h2 className="text-lg font-semibold tracking-tight">Places</h2>
            <p className="hidden text-sm text-ink-muted sm:block">Choose one to fly the camera there.</p>
          </div>
          <div className="mt-4 grid grid-cols-1 overflow-hidden rounded-2xl border border-line bg-line-strong sm:grid-cols-2">
            {EXPLORATION_ZONES.map((zone) => (
              <button
                key={zone.id}
                type="button"
                onClick={() => handleFlyToZone(zone)}
                className="flex h-full flex-col bg-surface-subtle p-5 text-left transition-colors hover:bg-white"
              >
                <div className="flex items-center justify-between gap-3 text-[12px] text-ink-muted">
                  <span>{zone.badge}</span>
                  <span className="tabular-nums">{zone.lat.toFixed(2)}°, {zone.lon.toFixed(2)}°</span>
                </div>
                <h3 className="mt-2 text-lg font-semibold tracking-tight">{zone.name}</h3>
                <p className="mt-1 text-[13px] text-brand-600">{zone.mission}</p>
                <p className="mt-3 line-clamp-3 text-sm leading-relaxed text-ink-soft">{zone.geology}</p>
                <div className="mt-4 flex items-center justify-between text-[13px]">
                  <span className="tabular-nums text-ink-soft">
                    {zone.elevation > 0 ? '+' : ''}{zone.elevation.toLocaleString()} m · {zone.diameter}
                  </span>
                  <span className="inline-flex items-center gap-1 font-medium text-ink">
                    Open <ArrowRight className="h-3.5 w-3.5" />
                  </span>
                </div>
                <p className="mt-2 text-[12px] text-ink-faint">{zone.status}</p>
              </button>
            ))}
          </div>
        </section>

        <section className="mt-12 grid grid-cols-1 gap-8 md:grid-cols-3">
          {tools.map((tool) => (
            <div key={tool.title} className="border-t border-line pt-4">
              <h3 className="text-base font-semibold">{tool.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink-soft">{tool.body}</p>
              <button
                type="button"
                onClick={tool.onClick}
                className="mt-4 text-sm font-medium text-brand-600 hover:underline"
              >
                {tool.action}
              </button>
            </div>
          ))}
        </section>

        <section className="mt-12 overflow-hidden rounded-2xl border border-line bg-white">
          <div className="flex items-end justify-between gap-4 px-5 py-4">
            <h2 className="text-lg font-semibold tracking-tight">Imagery on the globe</h2>
            <p className="hidden text-sm text-ink-muted sm:block">NASA PDS and USGS</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="text-[12px] text-ink-muted">
                <tr className="border-t border-line">
                  <th className="px-5 py-2 font-medium">Tier</th>
                  <th className="px-3 py-2 font-medium">Product</th>
                  <th className="px-3 py-2 font-medium">Instrument</th>
                  <th className="px-3 py-2 font-medium">Resolution</th>
                  <th className="px-3 py-2 font-medium">Coverage</th>
                  <th className="px-5 py-2 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="text-ink-soft">
                {[
                  ['1', 'Mars Viking MDIM 2.1', 'Viking Orbiter Visual Imaging', '231.5 m/px', 'Global', 'Validated'],
                  ['2', 'MRO CTX Jezero Mosaic', 'Context Camera (MRO)', '5.55 m/px', 'Jezero and Gale', 'Calibrated'],
                  ['3', 'MRO HiRISE strip', 'High Resolution Imaging Science', '0.25–0.50 m/px', 'Perseverance route', 'Active'],
                  ['DEM', 'MGS MOLA MEGDR 128', 'Mars Orbiter Laser Altimeter', '463 m/px', 'Global baseline', 'Datum'],
                ].map((row) => (
                  <tr key={row[0]} className="border-t border-line">
                    {row.map((cell, index) => (
                      <td key={cell} className={`py-3 ${index === 0 || index === 5 ? 'px-5' : 'px-3'} ${index === 1 ? 'font-medium text-ink' : ''}`}>
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
};
