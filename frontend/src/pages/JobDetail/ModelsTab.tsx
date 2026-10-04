import { useState } from 'react';
import { ArrowUpDown } from 'lucide-react';

interface ModelsTabProps {
  models: any[];
  onSelectModel: (model: any) => void;
  onDeploy?: (modelIndex: number) => Promise<void>;
}

export function ModelsTab({ models, onSelectModel, onDeploy }: ModelsTabProps) {
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
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Model Comparison</h3>
        <div className="flex items-center gap-2">
          <ArrowUpDown className="w-4 h-4 text-gray-400" />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
          >
            <option value="rank">Sort by Rank</option>
            <option value="score">Sort by Score</option>
            <option value="time">Sort by Training Time</option>
          </select>
        </div>
      </div>

      <div className="space-y-3">
        {sortedModels.length === 0 ? (
          <p className="text-sm text-gray-500">No trained models available.</p>
        ) : (
          sortedModels.map((model) => (
            <div
              key={model.model_name}
              onClick={() => onSelectModel(model)}
              className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:border-purple-300 dark:hover:border-purple-700 transition-colors rounded-xl p-4 cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 flex items-center justify-center font-bold text-white">
                    {model.rank || 1}
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900 dark:text-white">{model.model_name}</p>
                    <div className="text-sm text-gray-500 dark:text-gray-400 flex items-center gap-2 mt-0.5">
                      <span className="px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded text-xs font-medium">
                        {((model.composite_score || 0) * 100).toFixed(1)}% score
                      </span>
                      <span className="text-gray-400 dark:text-gray-500">
                        Training: {model.train_time || 0}s
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                      {((model.composite_score || 0) * 100).toFixed(1)}%
                    </p>
                  </div>
                  <button
                    className="text-purple-600 dark:text-purple-400 hover:underline text-sm font-medium"
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