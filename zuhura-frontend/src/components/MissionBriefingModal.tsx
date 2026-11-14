import React from 'react';
import { Activity, ArrowRight, Compass, MessageSquare, Navigation, ShieldCheck, X } from 'lucide-react';
import { useGlobeStore } from '../store/globeStore';
import { useAIStore } from '../store/aiStore';

export const MissionBriefingModal: React.FC = () => {
  const {
    isMissionBriefingOpen,
    setIsMissionBriefingOpen,
    setActiveMainView,
    setIsXRayMarsOpen,
    setIsRoutePlannerOpen,
    setSelectedTerrain,
    setCameraPosition,
  } = useGlobeStore();
  const { toggleOpen: toggleAI } = useAIStore();

  if (!isMissionBriefingOpen) return null;

  const handleLaunchExplorer = () => {
    setIsMissionBriefingOpen(false);
    setActiveMainView('explorer');
  };

  const handleTestDriveRover = () => {
    setIsMissionBriefingOpen(false);
    setActiveMainView('explorer');
    setSelectedTerrain('jezero');
    setCameraPosition(18.38, 77.58, 180000);
    setIsRoutePlannerOpen(true);
  };

  const handleTestDriveInterior = () => {
    setIsMissionBriefingOpen(false);
    setIsXRayMarsOpen(true);
  };

  const handleTestDriveAI = () => {
    setIsMissionBriefingOpen(false);
    toggleAI();
  };

  const sections = [
    {
      icon: Compass,
      title: 'Coordinates and elevation',
      text: (
        <>
          Positions use the IAU 2015 reference ellipsoid for Mars (equatorial radius 3,396,190 m, polar radius 3,376,200
          m). Elevations are given relative to the MOLA areoid, the Martian equivalent of sea level.
        </>
      ),
    },
    {
      icon: Navigation,
      title: 'Rover route planning',
      text: (
        <>
          Routes are found with an A* search over the elevation model. The cost of each step accounts for slope, wheel
          slip and sinkage in loose soil (Bekker model), and the energy the rover would need.
        </>
      ),
    },
    {
      icon: Activity,
      title: 'Planetary interior',
      text: (
        <>
          The interior model follows InSight seismic results. It compares the original core estimate (Stähler et al.,
          2021) with the later model that adds a molten silicate layer above a smaller core (Samuel et al., 2023; Khan
          et al., 2023).
        </>
      ),
    },
    {
      icon: ShieldCheck,
      title: 'How values are labelled',
      text: (
        <>
          Every value is marked as observed, measured, derived, model estimate or simulated, and links to the dataset or
          publication it comes from.
        </>
      ),
    },
  ];

  const shortcuts: [string, string][] = [
    ['1', 'Explorer'],
    ['2', 'Mission overview'],
    ['3', 'Rover traverse'],
    ['4', 'Planetary interior'],
    ['5', 'Visual intelligence'],
    ['6', 'Image locator'],
    ['7', 'Ask Zuhura'],
    ['8', 'Workspace'],
    ['9', 'Data provenance'],
    ['0', 'Environment'],
    ['R', 'Rover images'],
    ['M', 'Mount Sharp'],
    ['D', 'Datasets'],
    ['E', 'EVA planner'],
    ['Esc', 'Close all panels'],
  ];

  const secondaryButton =
    'flex items-center gap-1.5 rounded border border-line-strong bg-white px-3 py-1.5 text-xs font-medium text-ink-soft transition-colors hover:border-brand-600 hover:text-brand-700';

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-brand-950/60 p-4 font-sans"
      role="dialog"
      aria-modal="true"
      aria-labelledby="help-title"
    >
      <div className="relative max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-lg bg-white text-ink shadow-panel">
        <div className="flex items-start justify-between border-b border-line px-6 py-5">
          <div>
            <p className="text-xs font-medium text-brand-600">Help</p>
            <h2 id="help-title" className="mt-0.5 text-xl font-semibold">
              About Zuhura Mars
            </h2>
            <p className="mt-1 max-w-2xl text-sm text-ink-muted">
              A web application for exploring Mars with published elevation, imagery and seismic data: view the globe,
              plan rover routes, study the interior and ask questions about any location.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setIsMissionBriefingOpen(false)}
            aria-label="Close"
            className="rounded p-1.5 text-ink-muted transition-colors hover:bg-surface-muted hover:text-ink"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-6 px-6 py-5">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {sections.map(({ icon: Icon, title, text }) => (
              <section key={title} className="rounded-lg border border-line p-4">
                <h3 className="flex items-center gap-2 text-sm font-semibold text-brand-700">
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  {title}
                </h3>
                <p className="mt-2 text-xs leading-relaxed text-ink-soft">{text}</p>
              </section>
            ))}
          </div>

          <section>
            <h3 className="text-sm font-semibold">Imagery resolution</h3>
            <p className="mt-1 text-xs text-ink-muted">
              The globe loads finer imagery as you zoom in: Viking global mosaic (232 m/px), MOLA elevation (463 m/px),
              CTX (about 6 m/px) and HiRISE (0.25 m/px) where coverage exists.
            </p>
          </section>

          <section>
            <h3 className="text-sm font-semibold">Keyboard shortcuts</h3>
            <dl className="mt-2 grid grid-cols-2 gap-x-6 gap-y-1.5 text-xs sm:grid-cols-3">
              {shortcuts.map(([key, label]) => (
                <div key={key} className="flex items-center gap-2">
                  <dt>
                    <kbd className="inline-block min-w-[2rem] rounded border border-line-strong bg-surface-subtle px-1.5 py-0.5 text-center font-mono text-[11px] text-ink-soft">
                      {key}
                    </kbd>
                  </dt>
                  <dd className="text-ink-soft">{label}</dd>
                </div>
              ))}
            </dl>
          </section>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line bg-surface-subtle px-6 py-4">
          <div className="flex flex-wrap items-center gap-2">
            <button type="button" onClick={handleTestDriveRover} className={secondaryButton}>
              <Navigation className="h-3.5 w-3.5" aria-hidden="true" />
              Try route planning
            </button>
            <button type="button" onClick={handleTestDriveInterior} className={secondaryButton}>
              <Activity className="h-3.5 w-3.5" aria-hidden="true" />
              View the interior
            </button>
            <button type="button" onClick={handleTestDriveAI} className={secondaryButton}>
              <MessageSquare className="h-3.5 w-3.5" aria-hidden="true" />
              Ask Zuhura
            </button>
          </div>
          <button
            type="button"
            onClick={handleLaunchExplorer}
            className="flex items-center gap-2 rounded bg-brand-700 px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-brand-800"
          >
            Open the globe
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  );
};
