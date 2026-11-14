import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';
import { useGlobeStore } from './store/globeStore';
import { useAIStore } from './store/aiStore';
import { useWorkspaceStore } from './store/workspaceStore';
import { useLayerStore } from './store/layerStore';
import { useProvenanceStore } from './store/provenanceStore';

// Expose stores to the browser console and screenshot scripts in development only.
if (import.meta.env.DEV) {
  (window as any).__zuhura = {
    globe: useGlobeStore,
    ai: useAIStore,
    workspace: useWorkspaceStore,
    layers: useLayerStore,
    provenance: useProvenanceStore,
  };
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
