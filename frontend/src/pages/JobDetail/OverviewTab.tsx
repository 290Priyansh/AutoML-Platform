import { Database, Search, Brain, Star } from 'lucide-react';
import { MetricCard } from '../../components/dashboard/MetricsDashboard';
import type { RankedModel } from '../../types';

export function OverviewTab({ jobStatus, jobResults }: { jobStatus?: any; jobResults?: any }) {
  if (!jobResults) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="relative w-12 h-12 mb-4">
          <div className="absolute inset-0 border-4 border-purple-200 dark:border-purple-800 rounded-full" />
          <div className="absolute inset-0 border-4 border-purple-600 rounded-full border-t-transparent animate-spin" />
        </div>
        <p className="text-gray-500 dark:text-gray-400">
          {jobStatus?.status === 'running' ? 'Pipeline is running...' : 'Waiting for pipeline results...'}
        </p>
      </div>
    );
  }

  const rankedModels: RankedModel[] = jobResults.ranked_models || [];

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard title="Rows" value={jobResults.row_count?.toLocaleString() || 'N/A'} icon={<Database className="w-5 h-5" />} subtitle="Total samples" />
        <MetricCard title="Columns" value={jobResults.col_count?.toLocaleString() || 'N/A'} icon={<Search className="w-5 h-5" />} subtitle="Features + target" />
        <MetricCard title="Problem Type" value={jobResults.problem_type || 'N/A'} icon={<Brain className="w-5 h-5" />} subtitle="Auto-detected" />
        <MetricCard title="Data Quality" value={`${Math.round((jobResults.data_quality_score || 0) * 100)}%`} icon={<Star className="w-5 h-5" />} subtitle="Quality score" />
      </div>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Top Models Comparison</h3>
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-green-500" /> Leaderboard</span>
          </div>
        </div>
        
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {rankedModels.slice(0, 3).map((model: RankedModel, i: number) => (
            <div key={model.model_name} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:border-purple-300 dark:hover:border-purple-700 transition-colors rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 flex items-center justify-center font-bold text-white">
                    {i + 1}
                  </div>
                  <div>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">{model.model_name}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Composite: {(model.composite_score * 100).toFixed(1)}%</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                    {(model.composite_score * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <p className="text-xs text-gray-500 dark:text-gray-400">Training Time</p>
                    <p className="font-mono text-lg text-gray-900 dark:text-white">{model.training_time || 0}s</p>
                  </div>
                  <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <p className="text-xs text-gray-500 dark:text-gray-400">Rank</p>
                    <p className="font-mono text-lg text-purple-600 dark:text-purple-400">#{model.rank}</p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(model.metrics || {}).slice(0, 4).map(([key, value]) => (
                    <span key={key} className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs text-gray-600 dark:text-gray-300">
                      {key}: {typeof value === 'number' ? value.toFixed(3) : String(value)}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-500 dark:text-gray-400">Total Models Trained</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{rankedModels.length}</p>
        </div>
        <div className="p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-500 dark:text-gray-400">Best Model</p>
          <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">{rankedModels[0]?.model_name || 'N/A'}</p>
        </div>
        <div className="p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-500 dark:text-gray-400">Ensemble Used</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{jobResults.ensemble_model_path ? 'Yes' : 'No'}</p>
        </div>
      </div>
    </div>
  );
}