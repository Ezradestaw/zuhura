import React from 'react';
import type { LucideIcon } from 'lucide-react';
import {
  Activity,
  Bookmark,
  Camera,
  CircleHelp,
  Columns2,
  Database,
  Footprints,
  Globe,
  Images,
  Layers,
  LayoutDashboard,
  MousePointer2,
  Mountain,
  Navigation,
  Ruler,
  Wind,
} from 'lucide-react';
import { useGlobeStore } from '../store/globeStore';
import { useAIStore } from '../store/aiStore';
import { useWorkspaceStore } from '../store/workspaceStore';
import { useEnvironmentStore } from '../store/environmentStore';

interface NavItem {
  id: string;
  label: string;
  description: string;
  icon: LucideIcon;
  active: boolean;
  onClick: () => void;
  shortcut?: string;
}

const NavButton: React.FC<{ item: NavItem }> = ({ item }) => {
  const Icon = item.icon;
  return (
    <button
      type="button"
      onClick={item.onClick}
      title={item.shortcut ? `${item.label} (${item.shortcut})` : item.label}
      aria-pressed={item.active}
      className={`relative mx-2 flex h-10 items-center rounded border-l-2 px-3 text-left transition-colors ${
        item.active
          ? 'border-accent bg-brand-700 text-white'
          : 'border-transparent text-brand-100 hover:bg-brand-700/60 hover:text-white'
      }`}
    >
      <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
      <span className="ml-3 flex min-w-0 flex-1 items-center justify-between gap-2 whitespace-nowrap opacity-0 transition-opacity duration-150 group-hover:opacity-100">
        <span className="min-w-0">
          <span className="block truncate text-xs font-medium">{item.label}</span>
          <span className="block truncate text-[10px] text-brand-200">{item.description}</span>
        </span>
        {item.shortcut && (
          <kbd className="rounded border border-brand-600 px-1 font-mono text-[10px] text-brand-200">
            {item.shortcut}
          </kbd>
        )}
      </span>
    </button>
  );
};

const SectionLabel: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="h-6 px-4 pt-2 text-[10px] font-semibold uppercase tracking-wider text-brand-300 opacity-0 transition-opacity group-hover:opacity-100">
    {children}
  </div>
);

export const NavigationRail: React.FC = () => {
  const {
    activeMainView,
    setActiveMainView,
    isXRayMarsOpen,
    setIsXRayMarsOpen,
    isRoutePlannerOpen,
    setIsRoutePlannerOpen,
    isPinpointOpen,
    setIsPinpointOpen,
    isRegionDiscoveryOpen,
    setIsRegionDiscoveryOpen,
    isPinpointNavigationMode,
    setPinpointNavigationMode,
    setIsMissionBriefingOpen,
    isSurfaceWalkActive,
    setIsSurfaceWalkActive,
    isSplitScreenActive,
    setIsSplitScreenActive,
    isRoverRawImagesOpen,
    setIsRoverRawImagesOpen,
    isMountSharpModalOpen,
    setIsMountSharpModalOpen,
    isDatasetExplorerOpen,
    setIsDatasetExplorerOpen,
    isAresHudOpen,
    setIsAresHudOpen,
    isHoverIntelligenceEnabled,
    setIsHoverIntelligenceEnabled,
  } = useGlobeStore();
  const { isOpen: isAIOpen, toggleOpen: toggleAI } = useAIStore();
  const { isWorkspaceOpen, setIsWorkspaceOpen, measurementToolActive, setMeasurementToolActive } =
    useWorkspaceStore();
  const { isEnvironmentModalOpen, setIsEnvironmentModalOpen } = useEnvironmentStore();

  const showExplorer = () => setActiveMainView('explorer');

  const toolItems: NavItem[] = [
    {
      id: 'explorer',
      label: 'Explorer',
      description: '3D globe',
      icon: Globe,
      active:
        activeMainView === 'explorer' &&
        !isXRayMarsOpen &&
        !isRoutePlannerOpen &&
        !isPinpointOpen &&
        !isRegionDiscoveryOpen &&
        !isAIOpen &&
        !isWorkspaceOpen &&
        !isPinpointNavigationMode,
      onClick: () => {
        showExplorer();
        setIsXRayMarsOpen(false);
        setIsRoutePlannerOpen(false);
        setIsPinpointOpen(false);
        setIsRegionDiscoveryOpen(false);
        if (isAIOpen) toggleAI();
        if (isWorkspaceOpen) setIsWorkspaceOpen(false);
        if (isPinpointNavigationMode) setPinpointNavigationMode(false);
      },
      shortcut: '1',
    },
    {
      id: 'overview',
      label: 'Mission overview',
      description: 'Summary dashboard',
      icon: LayoutDashboard,
      active: activeMainView === 'overview',
      onClick: () => setActiveMainView(activeMainView === 'overview' ? 'explorer' : 'overview'),
      shortcut: '2',
    },
    {
      id: 'traverse',
      label: 'Rover traverse',
      description: 'Route planning',
      icon: Navigation,
      active: isRoutePlannerOpen || isPinpointNavigationMode,
      onClick: () => {
        showExplorer();
        setIsRoutePlannerOpen(!isRoutePlannerOpen);
      },
      shortcut: '3',
    },
    {
      id: 'interior',
      label: 'Planetary interior',
      description: 'InSight seismology',
      icon: Activity,
      active: isXRayMarsOpen,
      onClick: () => setIsXRayMarsOpen(!isXRayMarsOpen),
      shortcut: '4',
    },
    {
      id: 'image-locator',
      label: 'Image locator',
      description: 'Match a photo to terrain',
      icon: Camera,
      active: isPinpointOpen,
      onClick: () => setIsPinpointOpen(!isPinpointOpen),
      shortcut: '6',
    },
    {
      id: 'regions',
      label: 'Regions',
      description: 'Geological units',
      icon: Layers,
      active: isRegionDiscoveryOpen,
      onClick: () => setIsRegionDiscoveryOpen(!isRegionDiscoveryOpen),
    },
    {
      id: 'workspace',
      label: 'Workspace',
      description: 'Bookmarks and notes',
      icon: Bookmark,
      active: isWorkspaceOpen,
      onClick: () => setIsWorkspaceOpen(!isWorkspaceOpen),
      shortcut: '8',
    },
    {
      id: 'environment',
      label: 'Environment',
      description: 'Climate and solar power',
      icon: Wind,
      active: isEnvironmentModalOpen,
      onClick: () => setIsEnvironmentModalOpen(!isEnvironmentModalOpen),
      shortcut: '0',
    },
    {
      id: 'rover-images',
      label: 'Rover images',
      description: 'Perseverance and Curiosity',
      icon: Images,
      active: isRoverRawImagesOpen,
      onClick: () => setIsRoverRawImagesOpen(!isRoverRawImagesOpen),
      shortcut: 'R',
    },
    {
      id: 'mount-sharp',
      label: 'Mount Sharp',
      description: 'Curiosity route',
      icon: Mountain,
      active: isMountSharpModalOpen,
      onClick: () => setIsMountSharpModalOpen(!isMountSharpModalOpen),
      shortcut: 'M',
    },
    {
      id: 'datasets',
      label: 'Datasets',
      description: 'Catalogue of layers',
      icon: Database,
      active: isDatasetExplorerOpen,
      onClick: () => setIsDatasetExplorerOpen(!isDatasetExplorerOpen),
      shortcut: 'D',
    },
    {
      id: 'eva',
      label: 'EVA planner',
      description: 'Jezero field traverse',
      icon: Footprints,
      active: isAresHudOpen,
      onClick: () => {
        showExplorer();
        setIsAresHudOpen(!isAresHudOpen);
      },
      shortcut: 'E',
    },
  ];

  const viewItems: NavItem[] = [
    {
      id: 'hover-details',
      label: 'Hover details',
      description: 'Card for the place under the cursor',
      icon: MousePointer2,
      active: isHoverIntelligenceEnabled,
      onClick: () => setIsHoverIntelligenceEnabled(!isHoverIntelligenceEnabled),
    },
    {
      id: 'surface-walk',
      label: 'Surface walk',
      description: 'First-person view (W A S D)',
      icon: Footprints,
      active: isSurfaceWalkActive,
      onClick: () => {
        showExplorer();
        setIsSurfaceWalkActive(!isSurfaceWalkActive);
      },
    },
    {
      id: 'compare',
      label: 'Compare layers',
      description: 'Split-screen swipe',
      icon: Columns2,
      active: isSplitScreenActive,
      onClick: () => {
        showExplorer();
        setIsSplitScreenActive(!isSplitScreenActive);
      },
    },
    {
      id: 'measure',
      label: 'Measure',
      description: 'Distance and area',
      icon: Ruler,
      active: measurementToolActive !== 'none',
      onClick: () => {
        showExplorer();
        setMeasurementToolActive(measurementToolActive === 'none' ? 'ruler' : 'none');
      },
    },
  ];

  return (
    <aside
      className="group fixed bottom-0 left-0 top-14 z-30 flex w-16 select-none flex-col justify-between overflow-hidden border-r border-brand-950 bg-brand-800 transition-[width] duration-200 hover:w-60"
      aria-label="Main navigation"
    >
      <nav className="flex flex-col gap-0.5 overflow-y-auto overflow-x-hidden pb-2">
        <SectionLabel>Tools</SectionLabel>
        {toolItems.map((item) => (
          <NavButton key={item.id} item={item} />
        ))}
        <SectionLabel>View</SectionLabel>
        {viewItems.map((item) => (
          <NavButton key={item.id} item={item} />
        ))}
      </nav>

      <div className="border-t border-brand-700 bg-brand-950 p-2">
        <button
          type="button"
          onClick={() => setIsMissionBriefingOpen(true)}
          title="Help and guided tour (?)"
          className="flex h-9 w-full items-center rounded px-3 text-brand-100 transition-colors hover:bg-brand-800 hover:text-white"
        >
          <CircleHelp className="h-4 w-4 shrink-0" aria-hidden="true" />
          <span className="ml-3 whitespace-nowrap text-xs font-medium opacity-0 transition-opacity group-hover:opacity-100">
            Help and guided tour
          </span>
        </button>
      </div>
    </aside>
  );
};
