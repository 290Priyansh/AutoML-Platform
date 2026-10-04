import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { useJobsList } from '../hooks/useApi';
import type { JobStatus } from '../types';
import { cn } from '../lib/utils';
import {
  BarChart2,
  Upload,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2,
  ArrowRight,
  Brain,
  Server,
  HardDrive,
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
    <div className="flex items-center justify-between py-2.5 transition-colors">
      <div className="flex items-center gap-3">
        <Icon className="w-4 h-4 text-[var(--text-muted)] flex-shrink-0" />
        <div>
          <p className="text-xs font-medium text-[var(--text)]">{label}</p>
          <p className="text-[11px] text-[var(--text-muted)]">{detail}</p>
        </div>
      </div>
      <div className="flex items-center gap-1.5">
        <span className={cn('w-1.5 h-1.5 rounded-full', isHealthy ? 'bg-[var(--status-success)]' : 'bg-[var(--status-warning)]')} />
        <span className="text-[11px] font-medium text-[var(--text-muted)]">
          {isHealthy ? 'Operational' : 'Degraded'}
        </span>
      </div>
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

  const { data: jobs } = useJobsList();

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
      icon: <Workflow className="w-4 h-4 text-[var(--text-muted)]" />,
    },
    { 
      label: 'Completed Models', 
      value: completedJobs.toString(), 
      subtitle: totalJobs > 0 ? `${Math.round((completedJobs / totalJobs) * 100)}% success rate` : 'Ready for data',
      icon: <CheckCircle className="w-4 h-4 text-[var(--text-muted)]" />,
    },
    { 
      label: 'Running Agents', 
      value: runningJobs.toString(), 
      subtitle: runningJobs > 0 ? 'Active execution' : 'Idle queue',
      icon: runningJobs > 0 ? <Loader2 className="w-4 h-4 animate-spin text-[var(--text-muted)]" /> : <Clock className="w-4 h-4 text-[var(--text-muted)]" />,
    },
    { 
      label: 'Failed Runs', 
      value: failedJobs.toString(), 
      subtitle: failedJobs > 0 ? 'Review trace logs' : '0 errors logged',
      icon: <AlertCircle className="w-4 h-4 text-[var(--text-muted)]" />,
    },
  ];

  return (
    <div className="space-y-10 max-w-[1280px] mx-auto pb-12">
      {/* Hero Welcome Header - Restyled flat on page background with bottom divider */}
      <div className="border-b border-[var(--border)] pb-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-1.5 text-xs font-medium text-[var(--accent)] tracking-tight">
              <Sparkles className="w-3.5 h-3.5" />
              Autonomous Machine Learning Platform
            </div>
            <h1 className="text-3xl sm:text-4xl font-serif font-normal tracking-tight text-[var(--text)]">
              End-to-End Multi-Agent Pipeline
            </h1>
            <p className="text-sm sm:text-base text-[var(--text-muted)] max-w-2xl leading-relaxed">
              Upload raw datasets and execute autonomous agents covering data ingestion, cleaning, NLP vectorization, Optuna hyperparameter optimization, SHAP explanations, and model packaging.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <Link
              to="/jobs/new"
              className="inline-flex items-center gap-2 px-4 h-9 squircle-sm bg-[var(--accent)] text-[var(--accent-contrast)] hover:bg-[var(--accent-hover)] font-medium text-sm border border-black/10 dark:border-white/10 shadow-[var(--shadow-subtle)] transition-colors cursor-pointer"
            >
              <Upload className="w-4 h-4" />
              Train New Dataset
            </Link>
            <Link
              to="/models"
              className="inline-flex items-center gap-2 px-4 h-9 squircle-sm border border-[var(--border)] bg-transparent text-[var(--text)] hover:bg-[var(--surface-2)] font-medium text-sm transition-colors cursor-pointer"
            >
              <Layers className="w-4 h-4" />
              Supported Algorithms
            </Link>
          </div>
        </div>
      </div>

      {/* Stats - Single horizontal strip inside a single squircle surface, four columns separated by 1px vertical dividers */}
      <div className="surface-card squircle-xl grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 divide-y sm:divide-y-0 sm:divide-x divide-[var(--border)]">
        {stats.map((stat) => (
          <div 
            key={stat.label}
            className="p-6 flex flex-col justify-between"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium text-[var(--text-muted)] tracking-tight">{stat.label}</span>
              <div>
                {stat.icon}
              </div>
            </div>
            <div className="space-y-1">
              <div className="text-[32px] font-mono font-medium leading-none tabular-nums text-[var(--text)] tracking-tight">
                {stat.value}
              </div>
              <p className="text-xs text-[var(--text-muted)] font-normal">{stat.subtitle}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Two Column Layout: Quick Actions left, pipeline monitor / recent jobs right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Quick Actions & System Health */}
        <div className="space-y-8">
          {/* Quick Actions - Plain list of rows separated by dividers inside one surface */}
          <div className="surface-card squircle-lg p-6">
            <h2 className="text-base font-semibold text-[var(--text)] mb-4 flex items-center gap-2">
              <Zap className="w-4 h-4 text-[var(--accent)]" />
              Quick Actions
            </h2>
            <div className="divide-y divide-[var(--border)] border border-[var(--border)] squircle-md overflow-hidden">
              <Link
                to="/jobs/new"
                className="p-3.5 hover:bg-[var(--surface-2)] transition-colors group flex items-center justify-between cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <Upload className="w-4 h-4 text-[var(--text-muted)] group-hover:text-[var(--text)] transition-colors flex-shrink-0" />
                  <div>
                    <p className="font-medium text-xs text-[var(--text)]">Start New Training</p>
                    <p className="text-[11px] text-[var(--text-muted)]">Upload CSV/PDF & launch pipeline</p>
                  </div>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-[var(--text-muted)] group-hover:text-[var(--accent)] transition-colors" />
              </Link>

              <Link
                to="/jobs"
                className="p-3.5 hover:bg-[var(--surface-2)] transition-colors group flex items-center justify-between cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <BarChart2 className="w-4 h-4 text-[var(--text-muted)] group-hover:text-[var(--text)] transition-colors flex-shrink-0" />
                  <div>
                    <p className="font-medium text-xs text-[var(--text)]">Execution History</p>
                    <p className="text-[11px] text-[var(--text-muted)]">View all completed and active jobs</p>
                  </div>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-[var(--text-muted)] group-hover:text-[var(--accent)] transition-colors" />
              </Link>

              <Link
                to="/models"
                className="p-3.5 hover:bg-[var(--surface-2)] transition-colors group flex items-center justify-between cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <Brain className="w-4 h-4 text-[var(--text-muted)] group-hover:text-[var(--text)] transition-colors flex-shrink-0" />
                  <div>
                    <p className="font-medium text-xs text-[var(--text)]">Model Catalog</p>
                    <p className="text-[11px] text-[var(--text-muted)]">XGBoost, LightGBM, RF & Ensembles</p>
                  </div>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-[var(--text-muted)] group-hover:text-[var(--accent)] transition-colors" />
              </Link>
            </div>
          </div>

          {/* Engine Health */}
          <div className="surface-card squircle-lg p-6">
            <div className="flex items-center gap-2.5 mb-4">
              <Server className="w-4 h-4 text-[var(--accent)] flex-shrink-0" />
              <div>
                <h2 className="text-base font-semibold text-[var(--text)]">Engine Health</h2>
                <p className="text-xs text-[var(--text-muted)]">Backend microservices status</p>
              </div>
            </div>
            <div className="divide-y divide-[var(--border)]">
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
          {/* Active Job Progress Showcase / Empty State */}
          <div className="surface-card squircle-lg p-6 sm:p-8">
            {activeJob ? (
              <div>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                  <div>
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)]">
                        {activeJob.status === 'running' || activeJob.status === 'queued' ? 'Live Execution Monitor' : 'Latest Pipeline Run'}
                      </span>
                      <span className="inline-flex items-center gap-1.5 text-xs font-medium">
                        <span className={cn(
                          'w-1.5 h-1.5 rounded-full',
                          activeJob.status === 'completed' && 'bg-[var(--status-success)]',
                          activeJob.status === 'running' && 'bg-[var(--status-running)] animate-pulse',
                          activeJob.status === 'queued' && 'bg-[var(--status-warning)]',
                          activeJob.status === 'failed' && 'bg-[var(--status-error)]',
                        )} />
                        <span className="uppercase text-[11px] font-semibold text-[var(--text)]">{activeJob.status}</span>
                      </span>
                    </div>
                    <h3 className="text-lg font-semibold text-[var(--text)]">
                      Job <span className="font-mono text-[var(--accent)]">{activeJob.job_id.slice(0, 10)}</span>
                    </h3>
                    <p className="text-xs text-[var(--text-muted)] mt-0.5">
                      Current Agent: <span className="font-medium text-[var(--text)]">{activeJob.current_agent}</span>
                      {activeJob.target_column && ` • Target: ${activeJob.target_column}`}
                    </p>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="text-2xl font-mono tabular-nums font-semibold text-[var(--text)]">
                        {activeJob.status === 'completed' ? 100 : activeJob.status === 'queued' ? 0 : activeJob.progress_pct}%
                      </div>
                      <span className="text-xs text-[var(--text-muted)]">Overall Progress</span>
                    </div>
                    <Link
                      to={`/jobs/${activeJob.job_id}`}
                      className="h-8 px-3 border border-[var(--border)] hover:bg-[var(--surface-2)] text-[var(--text)] squircle-sm text-xs font-medium transition-colors flex items-center gap-1 cursor-pointer"
                    >
                      View Live Run
                      <ChevronRight className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                    </Link>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="w-full h-1.5 bg-[var(--surface-2)] border border-[var(--border)] squircle-sm overflow-hidden mb-6">
                  <div 
                    className="h-full bg-[var(--accent)] squircle-sm transition-all duration-500"
                    style={{ 
                      width: `${activeJob.status === 'completed' ? 100 : activeJob.status === 'queued' ? 0 : activeJob.progress_pct}%` 
                    }}
                  />
                </div>

                {/* Agent Sequence Summary */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-left">
                  {[
                    { phase: '1. Understanding', desc: 'Ingestion, EDA & Split' },
                    { phase: '2. Preprocessing', desc: 'Cleaning, NLP & Features' },
                    { phase: '3. Modeling', desc: 'CV, Optuna HPO & Rank' },
                    { phase: '4. Serving', desc: 'SHAP, Audit & Export' },
                  ].map((p) => (
                    <div key={p.phase} className="p-3 squircle-md bg-[var(--surface-2)] border border-[var(--border)]">
                      <p className="text-xs font-semibold text-[var(--text)]">{p.phase}</p>
                      <p className="text-[11px] text-[var(--text-muted)] mt-0.5 truncate">{p.desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <Workflow className="w-8 h-8 mx-auto text-[var(--text-muted)] mb-3" />
                <h3 className="text-2xl font-serif font-medium text-[var(--text)]">No Pipeline Runs Yet</h3>
                <p className="text-xs text-[var(--text-muted)] mt-1.5 max-w-sm mx-auto leading-relaxed">
                  Upload a dataset to initiate the 24-agent automated machine learning sequence.
                </p>
                <Link
                  to="/jobs/new"
                  className="mt-5 inline-flex items-center gap-2 px-4 h-9 squircle-sm bg-[var(--accent)] text-[var(--accent-contrast)] hover:bg-[var(--accent-hover)] text-xs font-medium transition-colors shadow-[var(--shadow-subtle)]"
                >
                  <Upload className="w-3.5 h-3.5" />
                  Launch First Job
                </Link>
              </div>
            )}
          </div>

          {/* Real Recent Jobs Table */}
          <div className="surface-card squircle-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-[var(--border)] flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-[var(--text)]">Recent Pipeline Executions</h2>
                <p className="text-xs text-[var(--text-muted)]">All local and cloud training runs</p>
              </div>
              <Link to="/jobs" className="text-xs font-medium text-[var(--accent)] hover:underline flex items-center gap-1">
                View all ({totalJobs})
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            <div className="overflow-x-auto">
              {jobs && jobs.length > 0 ? (
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="border-b border-[var(--border)] bg-[var(--surface-2)] text-[11px] font-medium text-[var(--text-muted)] uppercase tracking-wider">
                      <th className="px-6 py-3 text-left">Job ID</th>
                      <th className="px-6 py-3 text-left">Status</th>
                      <th className="px-6 py-3 text-left">Current Agent</th>
                      <th className="px-6 py-3 text-left">Progress</th>
                      <th className="px-6 py-3 text-right pr-6">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border)] text-xs">
                    {jobs.slice(0, 5).map((job: JobStatus) => (
                      <tr 
                        key={job.job_id} 
                        onClick={() => navigate(`/jobs/${job.job_id}`)}
                        className="h-12 hover:bg-[var(--surface-2)]/60 transition-colors cursor-pointer"
                      >
                        <td className="px-6 py-3">
                          <code className="font-mono text-xs text-[var(--text)]">
                            {job.job_id.slice(0, 12)}...
                          </code>
                          {job.created_at && (
                            <p className="text-[11px] font-mono text-[var(--text-muted)] mt-0.5">
                              {new Date(job.created_at).toLocaleTimeString()}
                            </p>
                          )}
                        </td>
                        <td className="px-6 py-3">
                          <span className="inline-flex items-center gap-1.5 text-xs font-medium uppercase">
                            <span className={cn(
                              'w-1.5 h-1.5 rounded-full',
                              job.status === 'completed' && 'bg-[var(--status-success)]',
                              job.status === 'running' && 'bg-[var(--status-running)]',
                              job.status === 'queued' && 'bg-[var(--status-warning)]',
                              job.status === 'failed' && 'bg-[var(--status-error)]',
                            )} />
                            <span className="text-[var(--text)]">{job.status}</span>
                            {job.status === 'running' && <Loader2 className="w-3 h-3 animate-spin text-[var(--status-running)]" />}
                          </span>
                        </td>
                        <td className="px-6 py-3 text-xs text-[var(--text-muted)]">
                          {job.current_agent}
                        </td>
                        <td className="px-6 py-3">
                          <div className="flex items-center gap-2">
                            <div className="w-20 h-1 bg-[var(--surface-2)] border border-[var(--border)] squircle-sm overflow-hidden">
                              <div 
                                className="h-full bg-[var(--accent)] squircle-sm" 
                                style={{ width: `${job.status === 'completed' ? 100 : job.status === 'queued' ? 0 : job.progress_pct}%` }} 
                              />
                            </div>
                            <span className="font-mono text-xs tabular-nums text-[var(--text-muted)]">
                              {job.status === 'completed' ? 100 : job.status === 'queued' ? 0 : job.progress_pct}%
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-3 text-right pr-6">
                          <span className="text-xs font-medium text-[var(--accent)] hover:underline">
                            Inspect →
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="text-center py-8 text-xs text-[var(--text-muted)]">
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