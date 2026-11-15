import React, { useEffect, useState } from 'react';
import { Header } from './components/Header';
import { NavigationRail } from './components/NavigationRail';
import { MarsGlobe } from './components/MarsGlobe';
import { MissionBriefingModal } from './components/MissionBriefingModal';
import { LayerPanel } from './components/LayerPanel';
import { AIPanel } from './components/AIPanel';
import { FeatureInspector } from './components/FeatureInspector';
import { TransectProfileDrawer } from './components/TransectProfileDrawer';
import { RoutePlanningDrawer } from './components/RoutePlanningDrawer';
import { LocationPinpointModal } from './components/LocationPinpointModal';
import { RegionDiscoveryPanel } from './components/RegionDiscoveryPanel';
import { ResearcherWorkspaceModal } from './components/ResearcherWorkspaceModal';
import { ScientificProvenanceModal } from './components/ScientificProvenanceModal';
import { VisualIntelligenceModal } from './components/VisualIntelligenceModal';
import { AtmosphericEnvironmentModal } from './components/AtmosphericEnvironmentModal';
import { RoverRawImagesModal } from './components/RoverRawImagesModal';
import { MountSharpExplorationModal } from './components/MountSharpExplorationModal';
import { DatasetExplorerModal } from './components/DatasetExplorerModal';
import { CesiumWebGLErrorBoundary } from './components/CesiumWebGLErrorBoundary';
import { useGlobeStore } from './store/globeStore';
import { useAIStore } from './store/aiStore';
import { useWorkspaceStore } from './store/workspaceStore';
import { useProvenanceStore } from './store/provenanceStore';
import { useEnvironmentStore } from './store/environmentStore';

function closeAllPanels() {
  const globe = useGlobeStore.getState();
  globe.setIsMissionBriefingOpen(false);
  globe.setIsRoverRawImagesOpen(false);
  globe.setIsMountSharpModalOpen(false);
  globe.setIsDatasetExplorerOpen(false);
  globe.setIsAresHudOpen(false);
  globe.setIsVisorPovActive(false);
  globe.setIsRoutePlannerOpen(false);
  globe.setRoutePickTarget(null);
  globe.setIsPinpointOpen(false);
  globe.setIsRegionDiscoveryOpen(false);
  globe.setIsSurfaceWalkActive(false);
  globe.setIsSplitScreenActive(false);
  globe.setIsVisualIntelligenceOpen(false);
  globe.setSelectedFeature(null);
  useWorkspaceStore.getState().setMeasurementToolActive('none');
  useWorkspaceStore.getState().setIsWorkspaceOpen(false);
  useProvenanceStore.getState().setIsProvenanceModalOpen(false);
  useEnvironmentStore.getState().setIsEnvironmentModalOpen(false);
  useAIStore.getState().setIsOpen(false);
}

function handleShortcut(key: string) {
  const globe = useGlobeStore.getState();
  const workspace = useWorkspaceStore.getState();
  const provenance = useProvenanceStore.getState();
  const environment = useEnvironmentStore.getState();

  switch (key.toLowerCase()) {
    case '1':
      globe.setIsRoutePlannerOpen(!globe.isRoutePlannerOpen);
      break;
    case '2':
      globe.setIsPinpointOpen(!globe.isPinpointOpen);
      break;
    case '3':
      globe.setIsVisualIntelligenceOpen(!globe.isVisualIntelligenceOpen);
      break;
    case '4':
      useAIStore.getState().toggleOpen();
      break;
    case '5':
      workspace.setIsWorkspaceOpen(!workspace.isWorkspaceOpen);
      break;
    case '6':
      provenance.setIsProvenanceModalOpen(!provenance.isProvenanceModalOpen);
      break;
    case '7':
      environment.setIsEnvironmentModalOpen(!environment.isEnvironmentModalOpen);
      break;
    case 'r':
      globe.setIsRoverRawImagesOpen(!globe.isRoverRawImagesOpen);
      break;
    case 'm':
      globe.setIsMountSharpModalOpen(!globe.isMountSharpModalOpen);
      break;
    case 'd':
      globe.setIsDatasetExplorerOpen(!globe.isDatasetExplorerOpen);
      break;
    case 'e':
      globe.setIsAresHudOpen(!globe.isAresHudOpen);
      break;
    case '?':
      globe.setIsMissionBriefingOpen(true);
      break;
    case 'escape':
      closeAllPanels();
      break;
  }
}

export const App: React.FC = () => {
  const [globeEpoch, setGlobeEpoch] = useState(0);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      const target = e.target;
      if (
        target instanceof HTMLInputElement ||
        target instanceof HTMLTextAreaElement ||
        target instanceof HTMLSelectElement
      ) {
        return;
      }
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      handleShortcut(e.key);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  return (
    <div className="relative h-screen w-screen select-none overflow-hidden bg-white font-sans text-ink">
      <Header />
      <NavigationRail />

      <main className="relative h-full w-full">
        <CesiumWebGLErrorBoundary onRetry={() => setGlobeEpoch((epoch) => epoch + 1)}>
          <MarsGlobe key={globeEpoch} />
        </CesiumWebGLErrorBoundary>
      </main>

      <LayerPanel />
      <AIPanel />
      <FeatureInspector />
      <TransectProfileDrawer />
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
      <MissionBriefingModal />
    </div>
  );
};

export default App;
