import { Brain } from 'lucide-react';

interface ExplainabilityTabProps {
  featureImportance?: Record<string, number>;
  shapValues?: any;
}

export function ExplainabilityTab({ featureImportance, shapValues: _shapValues }: ExplainabilityTabProps) {
  const fiEntries: [string, number][] = featureImportance && Object.keys(featureImportance).length > 0
    ? Object.entries(featureImportance).map(([k, v]): [string, number] => [k, Number(v) || 0])
    : [
        ['feature_1', 0.45],
        ['feature_2', -0.32],
        ['feature_3', 0.28],
      ];

  const maxVal = Math.max(...fiEntries.map(([, v]) => Math.abs(v)), 0.01);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-medium text-[var(--text)] flex items-center gap-2">
            <Brain className="w-4 h-4 text-[var(--accent)]" strokeWidth={1.5} />
            SHAP Explainability
          </h3>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            Understand how each feature drives individual model predictions.
          </p>
        </div>
        <div className="flex items-center gap-4 text-xs text-[var(--text-muted)] font-mono">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[var(--status-success)]" /> Positive impact
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[var(--status-error)]" /> Negative impact
          </span>
        </div>
      </div>

      <div className="surface-card squircle-lg border border-[var(--border)] p-5">
        <h4 className="text-xs font-mono uppercase tracking-wider text-[var(--text-muted)] mb-4">
          Feature Importance (Mean |SHAP| Value)
        </h4>

        <div className="space-y-3">
          {fiEntries.map(([name, val]) => {
            const isPositive = val >= 0;
            const pct = Math.min(Math.round((Math.abs(val) / maxVal) * 45), 45);

            return (
              <div key={name} className="flex items-center gap-3">
                <div className="w-44 text-right text-xs text-[var(--text-muted)] truncate pr-2 font-mono">
                  {name}
                </div>
                <div className="flex-1 h-3 relative bg-[var(--surface-2)] rounded-sm overflow-hidden border border-[var(--border)]">
                  <div className="absolute top-0 bottom-0 left-1/2 w-px bg-[var(--border)] z-10" />
                  {isPositive ? (
                    <div
                      className="absolute top-0 bottom-0 bg-[var(--status-success)] rounded-r-xs opacity-90"
                      style={{
                        left: '50%',
                        width: `${pct}%`,
                      }}
                    />
                  ) : (
                    <div
                      className="absolute top-0 bottom-0 bg-[var(--status-error)] rounded-l-xs opacity-90"
                      style={{
                        right: '50%',
                        width: `${pct}%`,
                      }}
                    />
                  )}
                </div>
                <span
                  className={`w-16 text-xs font-mono tabular-nums text-right ${
                    isPositive ? 'text-[var(--status-success)]' : 'text-[var(--status-error)]'
                  }`}
                >
                  {val > 0 ? `+${val.toFixed(3)}` : val.toFixed(3)}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}