import React from 'react';
import { X } from 'lucide-react';
import { useGlobeStore } from '../store/globeStore';
import { useAIStore } from '../store/aiStore';

export const SHORTCUTS: [string, string][] = [
  ['1', 'Traverse'],
  ['2', 'Image locator'],
  ['3', 'Visual intelligence'],
  ['4', 'Ask Zuhura'],
  ['5', 'Workspace'],
  ['6', 'Data provenance'],
  ['7', 'Environment'],
  ['R', 'Rover images'],
  ['M', 'Mount Sharp'],
  ['D', 'Datasets'],
  ['E', 'EVA planner'],
  ['Esc', 'Close panels'],
];

export const MissionBriefingModal: React.FC = () => {
  const { isMissionBriefingOpen, setIsMissionBriefingOpen, setIsRoutePlannerOpen, setCameraPosition } =
    useGlobeStore();
  const { setIsOpen: setAIOpen } = useAIStore();

  if (!isMissionBriefingOpen) return null;

  const close = () => setIsMissionBriefingOpen(false);

  const tryTraverse = () => {
    close();
    setCameraPosition(18.38, 77.58, 180000);
    setIsRoutePlannerOpen(true);
  };

  const askZuhura = () => {
    close();
    setAIOpen(true);
  };

  const button =
    'rounded border border-line-strong bg-white px-3 py-1.5 text-xs font-medium text-ink-soft hover:border-brand-600 hover:text-brand-700';

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-brand-950/60 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="help-title"
    >
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white text-ink shadow-panel">
        <div className="flex items-start justify-between border-b border-line px-6 py-4">
          <h2 id="help-title" className="text-lg font-semibold">
            Help
          </h2>
          <button
            type="button"
            onClick={close}
            aria-label="Close"
            className="rounded p-1.5 text-ink-muted hover:bg-surface-muted hover:text-ink"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-5 px-6 py-5 text-sm leading-relaxed text-ink-soft">
          <section>
            <h3 className="font-semibold text-ink">The globe</h3>
            <p className="mt-1">
              Drag to rotate, scroll to zoom. Imagery gets sharper as you zoom in: Viking mosaic (232 m/px), then CTX
              (about 6 m/px) and HiRISE (0.25 m/px) where they exist. Heights come from MOLA and are measured from the
              areoid, the Martian equivalent of sea level.
            </p>
          </section>

          <section>
            <h3 className="font-semibold text-ink">Traverse</h3>
            <p className="mt-1">
              Pick a start and a destination on the globe and press Find path. The server runs an A* search over the
              MOLA elevation grid and avoids ground that is too steep or rough for the chosen vehicle.
            </p>
          </section>

          <section>
            <h3 className="font-semibold text-ink">Ask Zuhura</h3>
            <p className="mt-1">
              A chat assistant (Google Gemini) that can look up elevations, slopes and datasets for the area you are
              viewing. Answers list the datasets they used.
            </p>
          </section>

          <section>
            <h3 className="font-semibold text-ink">Keyboard shortcuts</h3>
            <dl className="mt-2 grid grid-cols-2 gap-x-6 gap-y-1.5 text-xs sm:grid-cols-3">
              {SHORTCUTS.map(([key, label]) => (
                <div key={key} className="flex items-center gap-2">
                  <dt>
                    <kbd className="inline-block min-w-[2rem] rounded border border-line-strong bg-surface-subtle px-1.5 py-0.5 text-center font-mono text-[11px]">
                      {key}
                    </kbd>
                  </dt>
                  <dd>{label}</dd>
                </div>
              ))}
            </dl>
          </section>
        </div>

        <div className="flex flex-wrap justify-end gap-2 border-t border-line bg-surface-subtle px-6 py-3">
          <button type="button" onClick={tryTraverse} className={button}>
            Try the traverse planner
          </button>
          <button type="button" onClick={askZuhura} className={button}>
            Ask Zuhura
          </button>
          <button
            type="button"
            onClick={close}
            className="rounded bg-brand-700 px-4 py-1.5 text-xs font-semibold text-white hover:bg-brand-800"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
