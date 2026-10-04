import { useState } from 'react';
import { ArrowUpDown } from 'lucide-react';

interface ModelsTabProps {
  models: any[];
  onSelectModel: (model: any) => void;
  onDeploy?: (modelIndex: number) => Promise<void>;
}

export function ModelsTab({ models, onSelectModel, onDeploy: _onDeploy }: ModelsTabProps) {
  const [sortBy, setSortBy] = useState<'rank' | 'score' | 'time'>('rank');

  const sortedModels = (models || [])
    .slice()
    .sort((a, b) => {
      if (sortBy === 'rank') return (a.rank || 0) - (b.rank || 0);
      if (sortBy === 'score') return (b.composite_score || 0) - (a.composite_score || 0);
      return (a.train_time || 0) - (b.train_time || 0);
    });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[var(--text)]">Model Comparison</h3>
        <div className="flex items-center gap-2">
          <ArrowUpDown className="w-3.5 h-3.5 text-[var(--text-muted)]" />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="h-9 px-3 border border-[var(--border)] squircle-sm bg-[var(--surface)] text-xs text-[var(--text)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] cursor-pointer"
          >
            <option value="rank">Sort by Rank</option>
            <option value="score">Sort by Score</option>
            <option value="time">Sort by Training Time</option>
          </select>
        </div>
      </div>

      <div className="space-y-2.5">
        {sortedModels.length === 0 ? (
          <p className="text-xs text-[var(--text-muted)]">No trained models available.</p>
        ) : (
          sortedModels.map((model) => (
            <div
              key={model.model_name}
              onClick={() => onSelectModel(model)}
              className="surface-card squircle-lg p-4 hover:border-[var(--text-muted)] transition-colors cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-7 h-7 squircle-sm bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center font-mono font-medium text-xs text-[var(--text)]">
                    {model.rank || 1}
                  </div>
                  <div>
                    <p className="font-semibold text-sm text-[var(--text)]">{model.model_name}</p>
                    <div className="text-xs text-[var(--text-muted)] flex items-center gap-2 mt-0.5">
                      <span className="px-2 py-0.5 bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-muted)] squircle-sm text-[11px] font-mono">
                        {((model.composite_score || 0) * 100).toFixed(1)}% score
                      </span>
                      <span className="font-mono text-[11px]">
                        Training: {model.train_time || 0}s
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-xl font-mono tabular-nums font-semibold text-[var(--text)]">
                      {((model.composite_score || 0) * 100).toFixed(1)}%
                    </p>
                  </div>
                  <button
                    className="text-[var(--accent)] hover:underline text-xs font-medium cursor-pointer"
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectModel(model);
                    }}
                  >
                    View Details
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}