import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { useJobsList } from '../hooks/useApi';
import type { JobStatus } from '../types';
import { cn } from '../lib/utils';
import {
  BarChart2,
  Upload,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2,
  ArrowRight,
  Brain,
  Database,
  Server,
  HardDrive,
  Network,
  Zap,
  Workflow,
  Sparkles,
  Layers,
  ChevronRight,
} from 'lucide-react';

function HealthItem({
  label,
  icon: Icon,
  status,
  detail,
}: {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  status: string;
  detail: string;
}) {
  const isHealthy = status === 'healthy';
  return (
    <div className="flex items-center justify-between p-3 rounded-2xl bg-gray-50/80 dark:bg-gray-700/30 border border-gray-100 dark:border-gray-700/60 transition-all hover:bg-gray-100/60 dark:hover:bg-gray-700/50">
      <div className="flex items-center gap-3">
        <div className={cn('p-2 rounded-xl', isHealthy ? 'text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40' : 'text-amber-500 bg-amber-50 dark:bg-amber-950/40')}>
          <Icon className="w-4 h-4" />
        </div>
        <div>
          <p className="text-sm font-semibold text-gray-800 dark:text-gray-200">{label}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">{detail}</p>
        </div>
      </div>
      <span className={cn('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold', isHealthy ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300' : 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300')}>
        {isHealthy ? 'Operational' : 'Degraded'}
      </span>
    </div>
  );
}

export function Dashboard() {
  const navigate = useNavigate();
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.healthCheck(),
    refetchInterval: 30000,
  });

  const { data: jobs, isLoading: jobsLoading } = useJobsList();

  const totalJobs = jobs?.length || 0;
  const completedJobs = jobs?.filter((j: JobStatus) => j.status === 'completed').length || 0;
  const runningJobs = jobs?.filter((j: JobStatus) => j.status === 'running' || j.status === 'queued').length || 0;
  const failedJobs = jobs?.filter((j: JobStatus) => j.status === 'failed').length || 0;

  // Active or most recent job
  const activeJob = jobs?.find((j: JobStatus) => j.status === 'running' || j.status === 'queued') || jobs?.[0];

  const stats = [
    { 
      label: 'Total Pipelines', 
      value: totalJobs.toString(), 
      subtitle: totalJobs > 0 ? `${totalJobs} lifetime runs` : 'No runs yet',
      icon: <Workflow className="w-5 h-5" />,
      color: 'from-purple-600 to-indigo-600',
      bgColor: 'bg-purple-50 dark:bg-purple-950/30 text-purple-600 dark:text-purple-400',
    },
    { 
      label: 'Completed Models', 
      value: completedJobs.toString(), 
      subtitle: totalJobs > 0 ? `${Math.round((completedJobs / totalJobs) * 100)}% success rate` : 'Ready for data',
      icon: <CheckCircle className="w-5 h-5" />,
      color: 'from-emerald-600 to-teal-600',
      bgColor: 'bg-emerald-50 dark:bg-emerald-950/30 text-emerald-600 dark:text-emerald-400',
    },
    { 
      label: 'Running Agents', 
      value: runningJobs.toString(), 
      subtitle: runningJobs > 0 ? 'Active execution' : 'Idle queue',
      icon: runningJobs > 0 ? <Loader2 className="w-5 h-5 animate-spin" /> : <Clock className="w-5 h-5" />,
      color: 'from-blue-600 to-cyan-600',
      bgColor: 'bg-blue-50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400',
    },
    { 
      label: 'Failed Runs', 
      value: failedJobs.toString(), 
      subtitle: failedJobs > 0 ? 'Review trace logs' : '0 errors logged',
      icon: <AlertCircle className="w-5 h-5" />,
      color: 'from-rose-600 to-red-600',
      bgColor: 'bg-rose-50 dark:bg-rose-950/30 text-rose-600 dark:text-rose-400',
    },
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Hero Welcome Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-gray-950 via-purple-950 to-slate-900 text-white p-8 shadow-2xl border border-purple-500/20">
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-72 h-72 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/4 -mb-10 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30 backdrop-blur-md">
              <Sparkles className="w-3.5 h-3.5" />
              Autonomous Machine Learning Platform
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
              End-to-End Multi-Agent Pipeline
            </h1>
            <p className="text-gray-300 text-sm sm:text-base max-w-2xl leading-relaxed">
              Upload raw datasets and execute autonomous agents covering data ingestion, cleaning, NLP vectorization, Optuna hyperparameter optimization, SHAP explanations, and model packaging.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Link
              to="/jobs/new"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-2xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-semibold shadow-lg shadow-purple-600/30 transition-all transform hover:-translate-y-0.5 active:translate-y-0"
            >
              <Upload className="w-4 h-4" />
              Train New Dataset
            </Link>
            <Link
              to="/models"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-2xl bg-white/10 hover:bg-white/20 text-white font-semibold backdrop-blur-md border border-white/10 transition-all"
            >
              <Layers className="w-4 h-4" />
              Supported Algorithms
            </Link>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {stats.map((stat) => (
          <div 
            key={stat.label}
            className="glass-panel rounded-3xl p-6 border border-gray-200/80 dark:border-gray-700/80 shadow-sm hover:shadow-md transition-all duration-300 transform hover:-translate-y-0.5"
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm font-semibold text-gray-500 dark:text-gray-400">{stat.label}</span>
              <div className={cn('p-2.5 rounded-2xl', stat.bgColor)}>
                {stat.icon}
              </div>
            </div>
            <div className="space-y-1">
              <h3 className="text-3xl font-black text-gray-900 dark:text-white">{stat.value}</h3>
              <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">{stat.subtitle}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Quick Actions & System Health */}
        <div className="space-y-8">
          {/* Quick Actions */}
          <div className="glass-panel rounded-3xl p-6 border border-gray-200/80 dark:border-gray-700/80 shadow-sm">
            <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <Zap className="w-5 h-5 text-purple-600" />
              Quick Actions
            </h2>
            <div className="grid gap-3">
              <Link
                to="/jobs/new"
                className="p-4 border border-gray-200/80 dark:border-gray-700/80 rounded-2xl hover:border-purple-300 dark:hover:border-purple-600 transition-all hover:bg-purple-50/60 dark:hover:bg-purple-950/20 group flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-purple-100 dark:bg-purple-950/50 rounded-xl text-purple-600 dark:text-purple-400 group-hover:scale-110 transition-transform">
                    <Upload className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="font-semibold text-sm text-gray-900 dark:text-white">Start New Training</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Upload CSV/PDF & launch pipeline</p>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-purple-600 transition-colors" />
              </Link>

              <Link
                to="/jobs"
                className="p-4 border border-gray-200/80 dark:border-gray-700/80 rounded-2xl hover:border-blue-300 dark:hover:border-blue-600 transition-all hover:bg-blue-50/60 dark:hover:bg-blue-950/20 group flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-blue-100 dark:bg-blue-950/50 rounded-xl text-blue-600 dark:text-blue-400 group-hover:scale-110 transition-transform">
                    <BarChart2 className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="font-semibold text-sm text-gray-900 dark:text-white">Execution History</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">View all completed and active jobs</p>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-blue-600 transition-colors" />
              </Link>

              <Link
                to="/models"
                className="p-4 border border-gray-200/80 dark:border-gray-700/80 rounded-2xl hover:border-emerald-300 dark:hover:border-emerald-600 transition-all hover:bg-emerald-50/60 dark:hover:bg-emerald-950/20 group flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-emerald-100 dark:bg-emerald-950/50 rounded-xl text-emerald-600 dark:text-emerald-400 group-hover:scale-110 transition-transform">
                    <Brain className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="font-semibold text-sm text-gray-900 dark:text-white">Model Catalog</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">XGBoost, LightGBM, RF & Ensembles</p>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-emerald-600 transition-colors" />
              </Link>
            </div>
          </div>

          {/* System Health */}
          <div className="glass-panel rounded-3xl p-6 border border-gray-200/80 dark:border-gray-700/80 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-emerald-100 dark:bg-emerald-950/40 rounded-xl">
                <Server className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div>
                <h2 className="text-base font-bold text-gray-900 dark:text-white">Engine Health</h2>
                <p className="text-xs text-gray-500 dark:text-gray-400">Backend microservices status</p>
              </div>
            </div>
            <div className="space-y-2.5">
              {[
                { label: 'FastAPI Backend', icon: Server, status: health?.status === 'ok' ? 'healthy' : 'unhealthy', detail: 'Serving port 8000' },
                { label: 'LLM Multi-Agent Router', icon: Brain, status: 'healthy', detail: 'Groq + Fallback active' },
                { label: 'Optuna HPO Engine', icon: Workflow, status: 'healthy', detail: 'Hyperband pruning ready' },
                { label: 'Artifact Storage', icon: HardDrive, status: 'healthy', detail: 'Local & S3 sync enabled' },
              ].map(({ label, icon: Icon, status, detail }) => (
                <HealthItem key={label} label={label} icon={Icon} status={status} detail={detail} />
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Live Pipeline Monitor & Real Recent Jobs */}
        <div className="lg:col-span-2 space-y-8">
          {/* Active Job Progress Showcase */}
          <div className="glass-panel rounded-3xl p-6 sm:p-8 border border-gray-200/80 dark:border-gray-700/80 shadow-sm">
            {activeJob ? (
              <div>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold uppercase tracking-wider text-purple-600 dark:text-purple-400">
                        {activeJob.status === 'running' || activeJob.status === 'queued' ? 'Live Execution Monitor' : 'Latest Pipeline Run'}
                      </span>
                      <span className={cn(
                        'px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase',
                        activeJob.status === 'completed' && 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300',
                        activeJob.status === 'running' && 'bg-blue-100 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300 animate-pulse',
                        activeJob.status === 'queued' && 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300',
                        activeJob.status === 'failed' && 'bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300',
                      )}>
                        {activeJob.status}
                      </span>
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                      Job <span className="font-mono text-purple-600 dark:text-purple-400">{activeJob.job_id.slice(0, 10)}</span>
                    </h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                      Current Agent: <span className="font-medium text-gray-700 dark:text-gray-300">{activeJob.current_agent}</span>
                      {activeJob.target_column && ` • Target: ${activeJob.target_column}`}
                    </p>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="text-2xl font-black text-gray-900 dark:text-white">
                        {activeJob.status === 'completed' ? 100 : activeJob.status === 'queued' ? 0 : activeJob.progress_pct}%
                      </div>
                      <span className="text-xs text-gray-500 dark:text-gray-400">Overall Progress</span>
                    </div>
                    <Link
                      to={`/jobs/${activeJob.job_id}`}
                      className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-semibold transition-colors shadow-sm flex items-center gap-1.5"
                    >
                      View Live Run
                      <ChevronRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="w-full h-3 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden mb-6">
                  <div 
                    className="h-full bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-500 rounded-full transition-all duration-500"
                    style={{ 
                      width: `${activeJob.status === 'completed' ? 100 : activeJob.status === 'queued' ? 0 : activeJob.progress_pct}%` 
                    }}
                  />
                </div>

                {/* Agent Sequence Summary */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                  {[
                    { phase: '1. Understanding', desc: 'Ingestion, EDA & Split' },
                    { phase: '2. Preprocessing', desc: 'Cleaning, NLP & Features' },
                    { phase: '3. Modeling', desc: 'CV, Optuna HPO & Rank' },
                    { phase: '4. Serving', desc: 'SHAP, Audit & Export' },
                  ].map((p, idx) => (
                    <div key={p.phase} className="p-3 rounded-2xl bg-gray-50/70 dark:bg-gray-800/60 border border-gray-100 dark:border-gray-700/50">
                      <p className="text-xs font-bold text-gray-900 dark:text-white">{p.phase}</p>
                      <p className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5 truncate">{p.desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-10">
                <div className="w-14 h-14 mx-auto rounded-3xl bg-purple-100 dark:bg-purple-950/60 flex items-center justify-center text-purple-600 dark:text-purple-400 mb-4">
                  <Workflow className="w-7 h-7" />
                </div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">No Pipeline Runs Yet</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 max-w-md mx-auto">
                  Upload a dataset to initiate the 24-agent automated machine learning sequence.
                </p>
                <Link
                  to="/jobs/new"
                  className="mt-5 inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-purple-600 text-white text-sm font-semibold hover:bg-purple-700 transition-colors shadow-md"
                >
                  <Upload className="w-4 h-4" />
                  Launch First Job
                </Link>
              </div>
            )}
          </div>

          {/* Real Recent Jobs Table */}
          <div className="glass-panel rounded-3xl border border-gray-200/80 dark:border-gray-700/80 overflow-hidden shadow-sm">
            <div className="px-6 py-5 border-b border-gray-200/80 dark:border-gray-700/80 flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-gray-900 dark:text-white">Recent Pipeline Executions</h2>
                <p className="text-xs text-gray-500 dark:text-gray-400">All local and cloud training runs</p>
              </div>
              <Link to="/jobs" className="text-xs font-semibold text-purple-600 dark:text-purple-400 hover:underline flex items-center gap-1">
                View all ({totalJobs})
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            <div className="overflow-x-auto">
              {jobs && jobs.length > 0 ? (
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-100 dark:border-gray-800 text-xs font-bold text-gray-400 uppercase tracking-wider">
                      <th className="px-6 py-3.5 text-left">Job ID</th>
                      <th className="px-6 py-3.5 text-left">Status</th>
                      <th className="px-6 py-3.5 text-left">Current Agent</th>
                      <th className="px-6 py-3.5 text-left">Progress</th>
                      <th className="px-6 py-3.5 text-right pr-6">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-gray-800 text-sm">
                    {jobs.slice(0, 5).map((job: JobStatus) => (
                      <tr 
                        key={job.job_id} 
                        onClick={() => navigate(`/jobs/${job.job_id}`)}
                        className="hover:bg-purple-50/40 dark:hover:bg-gray-800/50 transition-colors cursor-pointer"
                      >
                        <td className="px-6 py-4">
                          <code className="font-mono text-xs font-semibold text-purple-600 dark:text-purple-400">
                            {job.job_id.slice(0, 12)}...
                          </code>
                          {job.created_at && (
                            <p className="text-[11px] text-gray-400 mt-0.5">
                              {new Date(job.created_at).toLocaleTimeString()}
                            </p>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          <span className={cn(
                            'inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase',
                            job.status === 'completed' && 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300',
                            job.status === 'running' && 'bg-blue-100 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300',
                            job.status === 'queued' && 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300',
                            job.status === 'failed' && 'bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300',
                          )}>
                            {job.status === 'running' && <Loader2 className="w-3 h-3 animate-spin" />}
                            {job.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-xs font-medium text-gray-700 dark:text-gray-300">
                          {job.current_agent}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <div className="w-20 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-purple-600 rounded-full" 
                                style={{ width: `${job.status === 'completed' ? 100 : job.status === 'queued' ? 0 : job.progress_pct}%` }} 
                              />
                            </div>
                            <span className="font-mono text-xs text-gray-600 dark:text-gray-300">
                              {job.status === 'completed' ? 100 : job.status === 'queued' ? 0 : job.progress_pct}%
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-right pr-6">
                          <span className="text-xs font-semibold text-purple-600 dark:text-purple-400 hover:underline">
                            Inspect →
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="text-center py-8 text-sm text-gray-500 dark:text-gray-400">
                  No previous training jobs found.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}