import React from 'react';
import { ShieldCheck, Eye, Cpu, Activity, AlertCircle, Sparkles, HelpCircle } from 'lucide-react';
import { useProvenanceStore } from '../store/provenanceStore';

export type EpistemicType =
  | 'OBSERVED'
  | 'MEASURED'
  | 'DERIVED'
  | 'MODEL_ESTIMATED'
  | 'SIMULATED'
  | 'PROVISIONAL'
  | 'UNVERIFIED';

interface EpistemicBadgeProps {
  type: EpistemicType | string;
  uncertainty?: string;
  datasetId?: string;
  className?: string;
  compact?: boolean;
}

const BADGE_CONFIGS: Record<
  string,
  { label: string; bg: string; text: string; border: string; icon: React.FC<{ className?: string }> }
> = {
  OBSERVED: {
    label: 'Observed',
    bg: 'bg-success-soft',
    text: 'text-success',
    border: 'border-success-line',
    icon: Eye,
  },
  MEASURED: {
    label: 'Measured',
    bg: 'bg-brand-50',
    text: 'text-brand-600',
    border: 'border-brand-200',
    icon: ShieldCheck,
  },
  DERIVED: {
    label: 'Derived',
    bg: 'bg-brand-50',
    text: 'text-brand-600',
    border: 'border-brand-200',
    icon: Cpu,
  },
  MODEL_ESTIMATED: {
    label: 'Model estimate',
    bg: 'bg-warning-soft',
    text: 'text-warning',
    border: 'border-warning-line',
    icon: Activity,
  },
  SIMULATED: {
    label: 'Simulated',
    bg: 'bg-brand-50',
    text: 'text-brand-600',
    border: 'border-brand-200',
    icon: Sparkles,
  },
  PROVISIONAL: {
    label: 'Provisional',
    bg: 'bg-warning-soft',
    text: 'text-warning',
    border: 'border-warning-line',
    icon: AlertCircle,
  },
  UNVERIFIED: {
    label: 'Unverified',
    bg: 'bg-danger-soft',
    text: 'text-danger',
    border: 'border-danger-line',
    icon: HelpCircle,
  },
};

export const EpistemicBadge: React.FC<EpistemicBadgeProps> = ({
  type,
  uncertainty,
  datasetId,
  className = '',
  compact = false,
}) => {
  const normType = type ? type.toUpperCase() : 'MEASURED';
  const config = BADGE_CONFIGS[normType] || BADGE_CONFIGS.MEASURED;
  const IconComponent = config.icon;
  const { openProvenanceModal } = useProvenanceStore();

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    openProvenanceModal(datasetId || normType);
  };

  return (
    <button
      onClick={handleClick}
      title={`${config.label}${uncertainty ? ` (uncertainty ${uncertainty})` : ''}. Click to see the data source.`}
      className={`inline-flex items-center gap-1 rounded border font-medium transition-colors hover:brightness-95 ${compact ? 'px-1 py-px text-[9px]' : 'px-1.5 py-0.5 text-[10px]'} ${config.bg} ${config.text} ${config.border} ${className}`}
    >
      <IconComponent className="w-2.5 h-2.5 shrink-0" />
      <span>{config.label}</span>
      {uncertainty && (
        <span className="opacity-75 font-normal ml-0.5 tabular-nums">
          ({uncertainty})
        </span>
      )}
    </button>
  );
};