import React from 'react';

interface CesiumWebGLErrorBoundaryProps {
  children: React.ReactNode;
  onRetry?: () => void;
}

interface CesiumWebGLErrorBoundaryState {
  error: Error | null;
}

/**
 * Catches render failures from the Cesium WebGL viewer so a context crash
 * does not unmount the rest of the research workspace.
 */
export class CesiumWebGLErrorBoundary extends React.Component<
  CesiumWebGLErrorBoundaryProps,
  CesiumWebGLErrorBoundaryState
> {
  state: CesiumWebGLErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): CesiumWebGLErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error): void {
    console.error('Cesium WebGL viewer failed', error);
  }

  private handleRetry = () => {
    this.setState({ error: null });
    this.props.onRetry?.();
  };

  render() {
    if (!this.state.error) {
      return this.props.children;
    }

    return (
      <div className="absolute inset-0 z-40 flex items-center justify-center bg-white p-6">
        <div className="max-w-md p-6 bg-surface-subtle rounded-lg border border-danger-line text-center">
          <h2 className="text-danger font-bold mb-2">WebGL context unavailable</h2>
          <p className="text-xs text-ink-soft mb-3">
            The Cesium Mars globe stopped because the WebGL context failed. Other workspace panels stay available.
          </p>
          <p className="text-[11px] text-ink-muted mb-4 break-words">{this.state.error.message}</p>
          <button
            type="button"
            onClick={this.handleRetry}
            className="px-3 py-1.5 rounded bg-surface-muted hover:bg-surface-muted border border-line text-xs font-mono text-ink"
          >
            Retry globe
          </button>
        </div>
      </div>
    );
  }
}
