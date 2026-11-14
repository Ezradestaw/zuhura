import React, { useEffect, useState } from 'react';
import { Header } from './components/Header';
import { NavigationRail } from './components/NavigationRail';
import { MarsGlobe } from './components/MarsGlobe';
import { MissionOverviewDashboard } from './components/MissionOverviewDashboard';
import { MissionBriefingModal } from './components/MissionBriefingModal';
import { LayerPanel } from './components/LayerPanel';
import { AIPanel } from './components/AIPanel';
import { FeatureInspector } from './components/FeatureInspector';
import { TransectProfileDrawer } from './components/TransectProfileDrawer';
import { XRayMars3DModal } from './components/XRayMars3DModal';
import { RoutePlanningDrawer } from './components/RoutePlanningDrawer';
import { HoverIntelligenceTooltip } from './components/HoverIntelligenceTooltip';
import { LocationPinpointModal } from './components/LocationPinpointModal';
import { RegionDiscoveryPanel } from './components/RegionDiscoveryPanel';
import { ResearcherWorkspaceModal } from './components/ResearcherWorkspaceModal';
import { ScientificProvenanceModal } from './components/ScientificProvenanceModal';
import { VisualIntelligenceModal } from './components/VisualIntelligenceModal';
import { AtmosphericEnvironmentModal } from './components/AtmosphericEnvironmentModal';
import { RoverRawImagesModal } from './components/RoverRawImagesModal';
import { MountSharpExplorationModal } from './components/MountSharpExplorationModal';
import { DatasetExplorerModal } from './components/DatasetExplorerModal';
import { useGlobeStore } from './store/globeStore';
import { useAIStore } from './store/aiStore';
import { useWorkspaceStore } from './store/workspaceStore';
import { useProvenanceStore } from './store/provenanceStore';
import { useEnvironmentStore } from './store/environmentStore';
import { CesiumWebGLErrorBoundary } from './components/CesiumWebGLErrorBoundary';

export const App: React.FC = () => {
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
    isVisualIntelligenceOpen,
    setIsVisualIntelligenceOpen,
    setIsMissionBriefingOpen,
    setSelectedFeature,
    setIsSurfaceWalkActive,
    setIsSplitScreenActive,
    isRoverRawImagesOpen,
    setIsRoverRawImagesOpen,
    isMountSharpModalOpen,
    setIsMountSharpModalOpen,
    isDatasetExplorerOpen,
    setIsDatasetExplorerOpen,
    isAresHudOpen,
    setIsAresHudOpen,
    setIsVisorPovActive,
  } = useGlobeStore();

  const { isOpen: isAIOpen, toggleOpen: toggleAI } = useAIStore();
  const {
    isWorkspaceOpen,
    setIsWorkspaceOpen,
    setMeasurementToolActive,
  } = useWorkspaceStore();

  const {
    isProvenanceModalOpen,
    setIsProvenanceModalOpen,
  } = useProvenanceStore();

  const {
    isEnvironmentModalOpen,
    setIsEnvironmentModalOpen,
  } = useEnvironmentStore();

  const [globeEpoch, setGlobeEpoch] = useState(0);

  // Global Scientific Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if user is currently typing in an input or textarea
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        e.target instanceof HTMLSelectElement
      ) {
        return;
      }

      if (e.key === '1') {
        setActiveMainView('explorer');
      } else if (e.key === '2') {
        setActiveMainView(activeMainView === 'overview' ? 'explorer' : 'overview');
      } else if (e.key === '3') {
        setActiveMainView('explorer');
        setIsRoutePlannerOpen(!isRoutePlannerOpen);
      } else if (e.key === '4') {
        setIsXRayMarsOpen(!isXRayMarsOpen);
      } else if (e.key === '5') {
        setIsVisualIntelligenceOpen(!isVisualIntelligenceOpen);
      } else if (e.key === '6') {
        setIsPinpointOpen(!isPinpointOpen);
      } else if (e.key === '7') {
        toggleAI();
      } else if (e.key === '8') {
        setIsWorkspaceOpen(!isWorkspaceOpen);
      } else if (e.key === '9') {
        setIsProvenanceModalOpen(!isProvenanceModalOpen);
      } else if (e.key === '0') {
        setIsEnvironmentModalOpen(!isEnvironmentModalOpen);
      } else if (e.key === 'r' || e.key === 'R') {
        setIsRoverRawImagesOpen(!isRoverRawImagesOpen);
      } else if (e.key === 'm' || e.key === 'M') {
        setIsMountSharpModalOpen(!isMountSharpModalOpen);
      } else if (e.key === 'd' || e.key === 'D') {
        setIsDatasetExplorerOpen(!isDatasetExplorerOpen);
      } else if (e.key === 'e' || e.key === 'E') {
        setActiveMainView('explorer');
        setIsAresHudOpen(!isAresHudOpen);
      } else if (e.key === '?') {
        setIsMissionBriefingOpen(true);
      } else if (e.key === 'Escape') {
        setIsMissionBriefingOpen(false);
        setIsXRayMarsOpen(false);
        setIsRoverRawImagesOpen(false);
        setIsMountSharpModalOpen(false);
        setIsDatasetExplorerOpen(false);
        setIsAresHudOpen(false);
        setIsVisorPovActive(false);
        setIsRoutePlannerOpen(false);
        setIsPinpointOpen(false);
        setIsRegionDiscoveryOpen(false);
        setIsSurfaceWalkActive(false);
        setIsSplitScreenActive(false);
        setIsVisualIntelligenceOpen(false);
        setMeasurementToolActive('none');
        setIsProvenanceModalOpen(false);
        setIsEnvironmentModalOpen(false);
        if (isAIOpen) toggleAI();
        if (isWorkspaceOpen) setIsWorkspaceOpen(false);
        setSelectedFeature(null);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
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
    isVisualIntelligenceOpen,
    setIsVisualIntelligenceOpen,
    isAIOpen,
    toggleAI,
    isWorkspaceOpen,
    setIsWorkspaceOpen,
    isProvenanceModalOpen,
    setIsProvenanceModalOpen,
    isEnvironmentModalOpen,
    setIsEnvironmentModalOpen,
    setIsRoverRawImagesOpen,
    isRoverRawImagesOpen,
    setIsMountSharpModalOpen,
    isMountSharpModalOpen,
    setIsDatasetExplorerOpen,
    isDatasetExplorerOpen,
    isAresHudOpen,
    setIsAresHudOpen,
    setIsVisorPovActive,
    setIsMissionBriefingOpen,
    setSelectedFeature,
  ]);

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-white select-none font-sans text-ink">
      <Header />
      <NavigationRail />

      {/* Main Workspace (Full-bleed Mars Globe) */}
      <main className="relative w-full h-full">
        <CesiumWebGLErrorBoundary onRetry={() => setGlobeEpoch((epoch) => epoch + 1)}>
          <MarsGlobe key={globeEpoch} />
        </CesiumWebGLErrorBoundary>
      </main>

      {/* Mission Overview Cockpit Overlay */}
      <MissionOverviewDashboard />

      {/* Scientific Floating Instruments & Inspectors */}
      <LayerPanel />
      <AIPanel />
      <FeatureInspector />
      <TransectProfileDrawer />
      <XRayMars3DModal />
      <RoutePlanningDrawer />
      <LocationPinpointModal />
      <RegionDiscoveryPanel />
      <ResearcherWorkspaceModal />
      <ScientificProvenanceModal />
      <VisualIntelligenceModal />
      <AtmosphericEnvironmentModal />
      <RoverRawImagesModal />
      <MountSharpExplorationModal />
      <DatasetExplorerModal />
      <HoverIntelligenceTooltip />
      <MissionBriefingModal />
    </div>
  );
};

export default App;
