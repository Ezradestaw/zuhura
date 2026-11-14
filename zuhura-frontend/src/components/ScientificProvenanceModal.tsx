import React, { useState, useEffect } from 'react';
import { ShieldCheck, X, ExternalLink, BookOpen, GitCompare, Layers, Database, Info } from 'lucide-react';
import { useProvenanceStore } from '../store/provenanceStore';
import { EpistemicBadge } from './EpistemicBadge';

export const ScientificProvenanceModal: React.FC = () => {
  const {
    isProvenanceModalOpen,
    setIsProvenanceModalOpen,
    activeTab,
    setActiveTab,
    selectedDatasetId,
    setSelectedDatasetId,
  } = useProvenanceStore();

  const [datasets, setDatasets] = useState<any[]>([]);
  const [competingModels, setCompetingModels] = useState<any[]>([]);
  const [classifications, setClassifications] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    if (!isProvenanceModalOpen) return;

    const fetchProvenance = async () => {
      try {
        setIsLoading(true);
        const [dsRes, modelsRes, classRes] = await Promise.all([
          fetch('/api/v1/provenance/datasets').then((r) => (r.ok ? r.json() : null)),
          fetch('/api/v1/provenance/competing-models').then((r) => (r.ok ? r.json() : null)),
          fetch('/api/v1/provenance/classifications').then((r) => (r.ok ? r.json() : null)),
        ]);

        if (dsRes?.records) setDatasets(dsRes.records);
        if (modelsRes?.comparisons) setCompetingModels(modelsRes.comparisons);
        if (classRes?.classifications) setClassifications(classRes.classifications);
      } catch (err) {
        console.warn('Provenance fetch notice:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchProvenance();
  }, [isProvenanceModalOpen]);

  if (!isProvenanceModalOpen) return null;

  const currentDataset = datasets.find((d) => d.original_dataset_id.includes(selectedDatasetId || '')) || datasets[0];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-brand-950/60 p-4 duration-150 select-none font-sans">
      <div className="relative w-full max-w-4xl max-h-[92vh] bg-white border border-line-strong rounded shadow-2xl overflow-hidden flex flex-col text-ink">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 bg-surface-subtle border-b border-line">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded bg-brand-700 flex items-center justify-center shadow-sm border border-brand-200">
              <ShieldCheck className="w-4 h-4 text-ink" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-sm font-semibold text-ink tracking-wide">Data provenance</h2>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-brand-50 text-brand-600 border border-brand-200 font-bold">
                  NASA PDS & IAU
                </span>
              </div>
              <p className="text-[11px] text-ink-muted">
                Peer-reviewed instrumentation, uncertainty bounds, and multi-model reconciliation
              </p>
            </div>
          </div>
          <button
            onClick={() => setIsProvenanceModalOpen(false)}
            className="p-1 rounded text-ink-muted hover:text-ink transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center px-5 border-b border-line bg-surface-subtle text-xs font-mono">
          <button
            onClick={() => setActiveTab('datasets')}
            className={`py-2.5 px-4 flex items-center space-x-1.5 border-b-2 transition-colors ${
              activeTab === 'datasets'
                ? 'border-brand-600 text-brand-600 font-bold'
                : 'border-transparent text-ink-muted hover:text-ink'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            <span>Dataset & Sensor Provenance</span>
          </button>
          <button
            onClick={() => setActiveTab('models')}
            className={`py-2.5 px-4 flex items-center space-x-1.5 border-b-2 transition-colors ${
              activeTab === 'models'
                ? 'border-warning text-warning font-bold'
                : 'border-transparent text-ink-muted hover:text-ink'
            }`}
          >
            <GitCompare className="w-3.5 h-3.5" />
            <span>Competing models</span>
          </button>
          <button
            onClick={() => setActiveTab('classifications')}
            className={`py-2.5 px-4 flex items-center space-x-1.5 border-b-2 transition-colors ${
              activeTab === 'classifications'
                ? 'border-brand-600 text-brand-600 font-bold'
                : 'border-transparent text-ink-muted hover:text-ink'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Data status levels</span>
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {isLoading ? (
            <div className="py-16 text-center font-mono text-xs text-ink-muted">
              Loading planetary truth records and scientific citations...
            </div>
          ) : activeTab === 'datasets' ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Dataset Sidebar Selector */}
              <div className="space-y-1.5 border-r border-line pr-3">
                <div className="text-[10px] text-ink-muted mb-2">Calibrated Datasets</div>
                {datasets.map((d) => (
                  <button
                    key={d.original_dataset_id}
                    onClick={() => setSelectedDatasetId(d.original_dataset_id)}
                    className={`w-full text-left p-2 rounded transition-colors text-xs font-mono flex flex-col space-y-1 ${
                      currentDataset?.original_dataset_id === d.original_dataset_id
                        ? 'bg-surface-muted border border-brand-200 text-brand-600'
                        : 'bg-surface-subtle border border-transparent text-ink-muted hover:text-ink hover:bg-surface-subtle'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold truncate">{d.original_dataset_id}</span>
                      <EpistemicBadge type={d.classification} compact />
                    </div>
                    <span className="text-[10px] text-ink-muted truncate">{d.data_source}</span>
                  </button>
                ))}
              </div>

              {/* Detailed Provenance Record */}
              <div className="md:col-span-2 space-y-3 font-sans">
                {currentDataset ? (
                  <>
                    <div className="flex items-center justify-between pb-2 border-b border-line">
                      <div>
                        <h3 className="text-base font-bold text-ink flex items-center space-x-2">
                          <span>{currentDataset.original_dataset_id}</span>
                          <EpistemicBadge type={currentDataset.classification} />
                        </h3>
                        <p className="text-xs text-ink-muted mt-0.5">{currentDataset.data_source}</p>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] bg-success-soft text-success border border-success-line font-bold">
                        {currentDataset.validation_status}
                      </span>
                    </div>

                    {/* Technical Parameter Grid */}
                    <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                      <div className="p-2.5 rounded bg-surface-subtle border border-line">
                        <span className="text-[10px] text-ink-muted block">Spatial resolution</span>
                        <span className="text-ink font-bold">{currentDataset.spatial_resolution}</span>
                      </div>
                      <div className="p-2.5 rounded bg-surface-subtle border border-line">
                        <span className="text-[10px] text-ink-muted block">Processing</span>
                        <span className="text-ink font-bold truncate">{currentDataset.processing_algorithm}</span>
                      </div>
                      <div className="p-2.5 rounded bg-surface-subtle border border-line">
                        <span className="text-[10px] text-ink-muted block">Coordinate reference system</span>
                        <span className="text-brand-600 font-bold">{currentDataset.coordinate_reference_system}</span>
                      </div>
                      <div className="p-2.5 rounded bg-surface-subtle border border-line">
                        <span className="text-[10px] text-ink-muted block">Vertical datum</span>
                        <span className="text-warning font-bold">{currentDataset.vertical_datum}</span>
                      </div>
                    </div>

                    {/* Uncertainty Model */}
                    {currentDataset.uncertainty && (
                      <div className="p-3 rounded bg-warning-soft border border-warning-line text-xs font-mono">
                        <div className="text-[10px] uppercase font-bold text-warning mb-1 flex items-center space-x-1">
                          <Info className="w-3 h-3 text-warning" />
                          <span>Uncertainty Model & Error Bounds</span>
                        </div>
                        <div className="grid grid-cols-3 gap-2 mt-1.5 text-center">
                          {currentDataset.uncertainty.uncertainty_absolute !== undefined && (
                            <div className="p-1 rounded bg-surface-subtle">
                              <span className="text-[9px] text-ink-muted block">Absolute error</span>
                              <span className="text-warning font-bold">
                                ± {currentDataset.uncertainty.uncertainty_absolute} {currentDataset.uncertainty.unit}
                              </span>
                            </div>
                          )}
                          {currentDataset.uncertainty.bounds_min !== undefined && (
                            <div className="p-1 rounded bg-surface-subtle">
                              <span className="text-[9px] text-ink-muted block">Valid range</span>
                              <span className="text-ink font-bold">
                                [{currentDataset.uncertainty.bounds_min}, {currentDataset.uncertainty.bounds_max}]
                              </span>
                            </div>
                          )}
                          <div className="p-1 rounded bg-surface-subtle">
                            <span className="text-[9px] text-ink-muted block">Method</span>
                            <span className="text-ink-soft text-[10px] truncate block">
                              {currentDataset.uncertainty.methodology}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Disclaimer */}
                    {currentDataset.disclaimer && (
                      <div className="p-2.5 rounded bg-surface-subtle border border-line text-[11px] font-mono text-ink-muted">
                        <span className="text-brand-600 font-bold block mb-0.5">Specification:</span>
                        {currentDataset.disclaimer}
                      </div>
                    )}

                    {/* Peer-Reviewed References */}
                    {currentDataset.scientific_references?.length > 0 && (
                      <div className="space-y-1.5 pt-2 border-t border-line">
                        <div className="text-[10px] text-ink-muted flex items-center space-x-1">
                          <BookOpen className="w-3 h-3 text-brand-600" />
                          <span>Peer-Reviewed Literature Citations</span>
                        </div>
                        {currentDataset.scientific_references.map((ref: any, idx: number) => (
                          <div
                            key={idx}
                            className="p-2 rounded bg-surface-subtle border border-line text-xs flex items-start justify-between"
                          >
                            <span className="text-ink-soft pr-2">{ref.citation}</span>
                            {ref.doi && (
                              <a
                                href={`https://doi.org/${ref.doi}`}
                                target="_blank"
                                rel="noreferrer"
                                className="shrink-0 flex items-center space-x-1 text-brand-600 hover:text-brand-600 text-[10px] font-mono transition-colors"
                              >
                                <span>DOI</span>
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                ) : null}
              </div>
            </div>
          ) : activeTab === 'models' ? (
            <div className="space-y-4">
              <div className="p-3 rounded bg-warning-soft border border-warning-line text-xs font-mono text-warning">
                <span className="font-bold block mb-1">Reconciling models:</span>
                Zuhura Mars does not arbitrarily pick one scientific hypothesis as absolute truth. When peer-reviewed
                literature presents competing interpretations, the platform explicitly exposes the empirical evidence,
                inversion methodologies, and consensus timeline.
              </div>

              {competingModels.map((comp, idx) => (
                <div key={idx} className="p-4 rounded bg-surface-subtle border border-line space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-ink flex items-center space-x-2">
                      <GitCompare className="w-4 h-4 text-brand-600" />
                      <span>{comp.subject}</span>
                    </h3>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-brand-50 text-brand-600 border border-brand-200">
                      {comp.competing_interpretations.length} Competing Models
                    </span>
                  </div>

                  {/* Side-by-Side Model Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
                    {comp.competing_interpretations.map((m: any, mIdx: number) => (
                      <div
                        key={mIdx}
                        className={`p-3 rounded border space-y-2 ${
                          m.status === 'CURRENT_CONSENSUS' || m.status === 'PREFERRED_CONSENSUS'
                            ? 'bg-success-soft border-success-line text-success'
                            : 'bg-surface-subtle border-line text-ink-soft'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-ink">{m.model_name}</span>
                          <span className="text-[9px] px-1.5 py-0.2 rounded font-bold uppercase tracking-wider bg-surface-subtle">
                            {m.status}
                          </span>
                        </div>
                        <p className="text-[11px] text-ink-muted leading-relaxed">{m.notes}</p>
                      </div>
                    ))}
                  </div>

                  <div className="p-2.5 rounded bg-surface-subtle border border-line text-xs font-mono">
                    <span className="text-success font-bold block mb-0.5">Current consensus:</span>
                    <span className="text-ink-soft">{comp.scientific_consensus}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              <div className="text-xs font-mono text-ink-muted mb-2">
                Zuhura enforces a strict 7-tier epistemic classification framework across all numerical outputs:
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {classifications.map((c) => (
                  <div key={c.id} className="p-3 rounded bg-surface-subtle border border-line space-y-1.5">
                    <div className="flex items-center space-x-2">
                      <EpistemicBadge type={c.id} />
                      <span className="text-xs font-bold text-ink">{c.label}</span>
                    </div>
                    <p className="text-xs text-ink-muted leading-relaxed font-sans">{c.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 bg-surface-subtle border-t border-line flex items-center justify-between text-xs font-mono text-ink-muted">
          <span>IAU/IAG 2015 WGCCRE · MOLA GMM-3 Areoid · NASA PDS / USGS</span>
          <button
            onClick={() => setIsProvenanceModalOpen(false)}
            className="px-3 py-1 rounded bg-surface-muted hover:bg-surface-muted text-ink transition-colors"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
