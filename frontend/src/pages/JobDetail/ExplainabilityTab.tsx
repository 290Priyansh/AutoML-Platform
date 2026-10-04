import { Brain } from 'lucide-react';

interface ExplainabilityTabProps {
  featureImportance?: Record<string, number>;
  shapValues?: any;
}

export function ExplainabilityTab({ featureImportance, shapValues }: ExplainabilityTabProps) {
  const fiEntries: [string, number][] = featureImportance && Object.keys(featureImportance).length > 0
    ? Object.entries(featureImportance).map(([k, v]): [string, number] => [k, Number(v) || 0])
    : [
        ['feature_1', 0.45],
        ['feature_2', -0.32],
        ['feature_3', 0.28],
      ];

  const maxVal = Math.max(...fiEntries.map(([_, v]) => Math.abs(v)), 0.01);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <Brain className="w-5 h-5 text-purple-600" />
            SHAP Explainability
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Understand how each feature drives individual model predictions.
          </p>
        </div>
        <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-green-500" /> Positive impact
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-red-500" /> Negative impact
          </span>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h4 className="font-medium text-gray-900 dark:text-white mb-4">
          Feature Importance (Mean |SHAP| Value)
        </h4>

        <div className="space-y-3">
          {fiEntries.map(([name, val]) => {
            const isPositive = val >= 0;
            const pct = Math.min(Math.round((Math.abs(val) / maxVal) * 45), 45);

            return (
              <div key={name} className="flex items-center gap-3">
                <div className="w-48 text-right text-sm text-gray-600 dark:text-gray-300 truncate pr-2 font-mono">
                  {name}
                </div>
                <div className="flex-1 h-6 relative bg-gray-100 dark:bg-gray-700/50 rounded-full overflow-hidden">
                  <div className="absolute top-0 bottom-0 left-1/2 w-0.5 bg-gray-300 dark:bg-gray-500 z-10" />
                  {isPositive ? (
                    <div
                      className="absolute top-0 bottom-0 rounded-r-full bg-gradient-to-r from-emerald-500 to-teal-400"
                      style={{
                        left: '50%',
                        width: `${pct}%`,
                      }}
                    />
                  ) : (
                    <div
                      className="absolute top-0 bottom-0 rounded-l-full bg-gradient-to-l from-red-500 to-rose-400"
                      style={{
                        right: '50%',
                        width: `${pct}%`,
                      }}
                    />
                  )}
                </div>
                <span
                  className={`w-16 text-sm font-mono text-right ${
                    isPositive ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-500'
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