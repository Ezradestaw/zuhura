import React from 'react';
import type { LucideIcon } from 'lucide-react';
import { Activity, CircleHelp, Eye, EyeOff, Layers, MessageSquare, Navigation } from 'lucide-react';
import { useGlobeStore } from '../store/globeStore';
import { useAIStore } from '../store/aiStore';

interface ToolbarButtonProps {
  label: string;
  title: string;
  icon: LucideIcon;
  active: boolean;
  onClick: () => void;
  labelClassName?: string;
}

const ToolbarButton: React.FC<ToolbarButtonProps> = ({
  label,
  title,
  icon: Icon,
  active,
  onClick,
  labelClassName = 'hidden sm:inline',
}) => (
  <button
    type="button"
    onClick={onClick}
    title={title}
    aria-pressed={active}
    className={`flex items-center gap-1.5 rounded px-2.5 py-1.5 text-xs font-medium transition-colors ${
      active ? 'bg-white text-brand-700' : 'text-brand-100 hover:bg-brand-600 hover:text-white'
    }`}
  >
    <Icon className="h-3.5 w-3.5" aria-hidden="true" />
    <span className={labelClassName}>{label}</span>
  </button>
);

function formatLatitude(lat: number | null): string {
  if (lat === null) return '--';
  return `${Math.abs(lat).toFixed(2)}° ${lat >= 0 ? 'N' : 'S'}`;
}

function formatLongitude(lon: number | null): string {
  if (lon === null) return '--';
  return `${(((lon % 360) + 360) % 360).toFixed(2)}° E`;
}

function formatElevation(elevation: number | null): string {
  if (elevation === null) return '--';
  const sign = elevation > 0 ? '+' : '';
  return `${sign}${Math.round(elevation).toLocaleString()} m`;
}

export const Header: React.FC = () => {
  const {
    cursorLat,
    cursorLon,
    cursorElevation,
    cameraAlt,
    isXRayMarsOpen,
    setIsXRayMarsOpen,
    isRoutePlannerOpen,
    setIsRoutePlannerOpen,
    isRegionDiscoveryOpen,
    setIsRegionDiscoveryOpen,
    isPlaceNamesVisible,
    setIsPlaceNamesVisible,
    setActiveMainView,
    setIsMissionBriefingOpen,
  } = useGlobeStore();
  const { isOpen: isAIOpen, toggleOpen: toggleAI } = useAIStore();

  const readouts = [
    { label: 'Position', value: `${formatLatitude(cursorLat)}, ${formatLongitude(cursorLon)}` },
    { label: 'Elevation', value: formatElevation(cursorElevation) },
    { label: 'Altitude', value: `${Math.round(cameraAlt / 1000).toLocaleString()} km` },
  ];

  return (
    <header className="fixed left-0 right-0 top-0 z-30 flex h-14 select-none items-center justify-between border-b border-brand-900 bg-brand-700 px-3 text-white md:px-5">
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-full border border-accent/60 bg-brand-900 text-sm font-semibold text-accent">
          Z
        </div>
        <div className="leading-tight">
          <div className="text-sm font-semibold tracking-wide">Zuhura Mars</div>
          <div className="hidden text-[11px] text-brand-200 sm:block">Planetary data explorer</div>
        </div>
      </div>

      <dl className="hidden items-center divide-x divide-brand-600 text-[11px] lg:flex">
        {readouts.map((item) => (
          <div key={item.label} className="flex items-baseline gap-1.5 px-3">
            <dt className="text-brand-200">{item.label}</dt>
            <dd className="font-mono font-medium tabular-nums text-white">{item.value}</dd>
          </div>
        ))}
      </dl>

      <nav className="flex items-center gap-1" aria-label="Tools">
        <ToolbarButton
          label="Interior"
          title="Planetary interior (InSight seismology)"
          icon={Activity}
          active={isXRayMarsOpen}
          onClick={() => setIsXRayMarsOpen(!isXRayMarsOpen)}
        />
        <ToolbarButton
          label="Traverse"
          title="Rover traverse planning"
          icon={Navigation}
          active={isRoutePlannerOpen}
          onClick={() => {
            setActiveMainView('explorer');
            setIsRoutePlannerOpen(!isRoutePlannerOpen);
          }}
        />
        <ToolbarButton
          label="Regions"
          title="Region discovery"
          icon={Layers}
          active={isRegionDiscoveryOpen}
          onClick={() => setIsRegionDiscoveryOpen(!isRegionDiscoveryOpen)}
          labelClassName="hidden lg:inline"
        />
        <ToolbarButton
          label="Place names"
          title={isPlaceNamesVisible ? 'Hide place names and outlines' : 'Show place names and outlines'}
          icon={isPlaceNamesVisible ? Eye : EyeOff}
          active={isPlaceNamesVisible}
          onClick={() => setIsPlaceNamesVisible(!isPlaceNamesVisible)}
          labelClassName="hidden xl:inline"
        />

        <div className="mx-1 h-6 w-px bg-brand-600" aria-hidden="true" />

        <button
          type="button"
          onClick={toggleAI}
          aria-pressed={isAIOpen}
          className={`flex items-center gap-1.5 rounded px-3 py-1.5 text-xs font-semibold transition-colors ${
            isAIOpen
              ? 'bg-accent text-brand-950'
              : 'border border-accent/70 text-accent hover:bg-accent hover:text-brand-950'
          }`}
        >
          <MessageSquare className="h-3.5 w-3.5" aria-hidden="true" />
          <span>Ask Zuhura</span>
        </button>

        <button
          type="button"
          onClick={() => setIsMissionBriefingOpen(true)}
          title="Help and guided tour"
          aria-label="Help"
          className="rounded p-1.5 text-brand-100 transition-colors hover:bg-brand-600 hover:text-white"
        >
          <CircleHelp className="h-4 w-4" aria-hidden="true" />
        </button>
      </nav>
    </header>
  );
};
