import { Database, Search, Brain, Star, Loader2 } from 'lucide-react';
import { MetricCard } from '../../components/dashboard/MetricsDashboard';
import type { RankedModel } from '../../types';

export function OverviewTab({ jobStatus, jobResults }: { jobStatus?: any; jobResults?: any }) {
  if (!jobResults) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="w-8 h-8 squircle-sm bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center mb-3">
          <Loader2 className="w-4 h-4 animate-spin text-[var(--text-muted)]" />
        </div>
        <p className="text-xs text-[var(--text-muted)]">
          {jobStatus?.status === 'running' ? 'Pipeline is running...' : 'Waiting for pipeline results...'}
        </p>
      </div>
    );
  }

  const rankedModels: RankedModel[] = jobResults.ranked_models || [];

  return (
    <div className="space-y-6">
      <div className="grid gap-3 md:grid-cols-4">
        <MetricCard title="Rows" value={jobResults.row_count?.toLocaleString() || 'N/A'} icon={<Database className="w-4 h-4 text-[var(--text-muted)]" />} subtitle="Total samples" />
        <MetricCard title="Columns" value={jobResults.col_count?.toLocaleString() || 'N/A'} icon={<Search className="w-4 h-4 text-[var(--text-muted)]" />} subtitle="Features + target" />
        <MetricCard title="Problem Type" value={jobResults.problem_type || 'N/A'} icon={<Brain className="w-4 h-4 text-[var(--text-muted)]" />} subtitle="Auto-detected" />
        <MetricCard title="Data Quality" value={`${Math.round((jobResults.data_quality_score || 0) * 100)}%`} icon={<Star className="w-4 h-4 text-[var(--text-muted)]" />} subtitle="Quality score" />
      </div>

      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-[var(--text)]">Top Models Comparison</h3>
          <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)]">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--status-success)]" /> Leaderboard
          </div>
        </div>
        
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {rankedModels.slice(0, 3).map((model: RankedModel, i: number) => (
            <div key={model.model_name} className="surface-card squircle-lg p-4 flex flex-col justify-between hover:border-[var(--text-muted)] transition-colors">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 squircle-sm bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center font-mono font-medium text-xs text-[var(--text)]">
                    {i + 1}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-[var(--text)]">{model.model_name}</p>
                    <p className="text-xs text-[var(--text-muted)] font-mono">Composite: {(model.composite_score * 100).toFixed(1)}%</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xl font-mono tabular-nums font-semibold text-[var(--text)]">
                    {(model.composite_score * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2.5 bg-[var(--surface-2)] squircle-sm border border-[var(--border)]">
                    <p className="text-[11px] text-[var(--text-muted)]">Training Time</p>
                    <p className="font-mono text-sm text-[var(--text)] mt-0.5">{model.training_time || 0}s</p>
                  </div>
                  <div className="p-2.5 bg-[var(--surface-2)] squircle-sm border border-[var(--border)]">
                    <p className="text-[11px] text-[var(--text-muted)]">Rank</p>
                    <p className="font-mono text-sm text-[var(--accent)] mt-0.5">#{model.rank}</p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-1">
                  {Object.entries(model.metrics || {}).slice(0, 4).map(([key, value]) => (
                    <span key={key} className="px-1.5 py-0.5 bg-[var(--surface-2)] border border-[var(--border)] squircle-sm text-[11px] font-mono text-[var(--text-muted)]">
                      {key}: {typeof value === 'number' ? value.toFixed(3) : String(value)}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <div className="p-4 surface-card squircle-lg">
          <p className="text-xs text-[var(--text-muted)]">Total Models Trained</p>
          <p className="text-2xl font-mono tabular-nums font-semibold text-[var(--text)] mt-1">{rankedModels.length}</p>
        </div>
        <div className="p-4 surface-card squircle-lg">
          <p className="text-xs text-[var(--text-muted)]">Best Model</p>
          <p className="text-2xl font-mono font-semibold text-[var(--accent)] mt-1">{rankedModels[0]?.model_name || 'N/A'}</p>
        </div>
        <div className="p-4 surface-card squircle-lg">
          <p className="text-xs text-[var(--text-muted)]">Ensemble Used</p>
          <p className="text-2xl font-semibold text-[var(--text)] mt-1">{jobResults.ensemble_model_path ? 'Yes' : 'No'}</p>
        </div>
      </div>
    </div>
  );
}