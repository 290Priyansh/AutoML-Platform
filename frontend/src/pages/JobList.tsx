import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import type { JobStatus } from '../types';
import { formatRelativeTime, cn } from '../lib/utils';
import {
  Search,
  MoreVertical,
  Download,
  Eye,
  RefreshCw,
  Loader2,
  Plus,
  Inbox,
} from 'lucide-react';
import { useMutation } from '@tanstack/react-query';

import { useJobsList } from '../hooks/useApi';

export function JobList() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedJob, setSelectedJob] = useState<string | null>(null);

  const { data: jobs, isLoading, refetch } = useJobsList();

  const deleteMutation = useMutation({
    mutationFn: async (jobId: string) => {
      await apiClient.getJobStatus(jobId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs', 'list'] });
    },
  });

  const filteredJobs = jobs?.filter((job: JobStatus) => {
    const matchesSearch = job.job_id.toLowerCase().includes(search.toLowerCase()) ||
      job.current_agent.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'all' || job.status === statusFilter;
    return matchesSearch && matchesStatus;
  }) || [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 animate-spin text-[var(--text-muted)]" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-serif font-normal text-[var(--text)] tracking-tight">Training Jobs</h1>
          <p className="text-xs text-[var(--text-muted)] mt-1">
            Monitor and manage your AutoML training jobs
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => navigate('/jobs/new')}
            className="h-9 px-4 bg-[var(--accent)] text-[var(--accent-contrast)] hover:bg-[var(--accent-hover)] border border-black/10 dark:border-white/10 shadow-[var(--shadow-subtle)] squircle-sm font-medium text-xs transition-colors flex items-center gap-1.5 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            New Job
          </button>
          <button
            onClick={() => refetch()}
            className="h-9 w-9 border border-[var(--border)] bg-transparent text-[var(--text-muted)] hover:text-[var(--text)] squircle-sm hover:bg-[var(--surface-2)] transition-colors flex items-center justify-center cursor-pointer"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
          <input
            type="text"
            placeholder="Search jobs..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full h-10 pl-9 pr-4 border border-[var(--border)] squircle-sm bg-[var(--surface)] text-[var(--text)] text-xs placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] transition-all"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="h-10 px-3.5 border border-[var(--border)] squircle-sm bg-[var(--surface)] text-[var(--text)] text-xs focus:outline-none focus:ring-2 focus:ring-[var(--accent)] sm:w-44 cursor-pointer"
        >
          <option value="all">All Status</option>
          <option value="queued">Queued</option>
          <option value="running">Running</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      <div className="surface-card squircle-lg overflow-hidden">
        {filteredJobs.length === 0 ? (
          <div className="py-16 text-center">
            <div className="w-12 h-12 mx-auto mb-3 squircle-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center">
              <Inbox className="w-6 h-6 text-[var(--text-muted)]" />
            </div>
            <h3 className="text-xl font-serif font-medium text-[var(--text)]">No jobs found</h3>
            <p className="text-xs text-[var(--text-muted)] mt-1">
              {search || statusFilter !== 'all' 
                ? 'Try adjusting your filters' 
                : 'Create your first training job to get started'}
            </p>
            {!search && statusFilter === 'all' && (
              <button
                onClick={() => navigate('/jobs/new')}
                className="mt-4 px-4 h-9 bg-[var(--accent)] text-[var(--accent-contrast)] hover:bg-[var(--accent-hover)] squircle-sm font-medium text-xs transition-colors cursor-pointer"
              >
                Create Job
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead className="bg-[var(--surface-2)] border-b border-[var(--border)] sticky top-0">
                <tr className="text-[11px] font-medium text-[var(--text-muted)] uppercase tracking-wider">
                  <th className="px-6 py-3 text-left">
                    Job ID
                  </th>
                  <th className="px-6 py-3 text-left">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left">
                    Current Agent
                  </th>
                  <th className="px-6 py-3 text-left">
                    Progress
                  </th>
                  <th className="px-6 py-3 text-left">
                    Created
                  </th>
                  <th className="px-6 py-3 text-right pr-6">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)] text-xs">
                {filteredJobs.map((job: JobStatus) => (
                  <tr
                    key={job.job_id}
                    className="h-12 hover:bg-[var(--surface-2)]/60 transition-colors"
                  >
                    <td className="px-6 py-3">
                      <code className="text-xs font-mono text-[var(--text)]">
                        {job.job_id.slice(0, 12)}...
                      </code>
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
                      </span>
                    </td>
                    <td className="px-6 py-3 text-xs text-[var(--text-muted)] max-w-xs truncate">
                      {job.current_agent.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())}
                    </td>
                    <td className="px-6 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-1 bg-[var(--surface-2)] border border-[var(--border)] squircle-sm overflow-hidden">
                          <div
                            className="h-full bg-[var(--accent)] squircle-sm transition-all duration-300"
                            style={{ width: `${job.progress_pct}%` }}
                          />
                        </div>
                        <span className="text-xs font-mono tabular-nums text-[var(--text-muted)]">{job.progress_pct}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-3 text-xs font-mono text-[var(--text-muted)]">
                      {formatRelativeTime(job.created_at)}
                    </td>
                    <td className="px-6 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Link
                          to={`/jobs/${job.job_id}`}
                          className="p-1.5 text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-2)] squircle-sm transition-colors cursor-pointer"
                          title="View details"
                        >
                          <Eye className="w-4 h-4" />
                        </Link>
                        {job.status === 'completed' && (
                          <Link
                            to={`/jobs/${job.job_id}/results`}
                            className="p-1.5 text-[var(--text-muted)] hover:text-[var(--accent)] hover:bg-[var(--surface-2)] squircle-sm transition-colors cursor-pointer"
                            title="View results"
                          >
                            <Download className="w-4 h-4" />
                          </Link>
                        )}
                        <button
                          onClick={() => setSelectedJob(job.job_id)}
                          className="p-1.5 text-[var(--text-muted)] hover:text-[var(--status-error)] hover:bg-[var(--surface-2)] squircle-sm transition-colors cursor-pointer"
                          title="More options"
                        >
                          <MoreVertical className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedJob && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-[2px]">
          <div className="bg-[var(--surface)] border border-[var(--border)] squircle-xl p-6 w-full max-w-md shadow-[var(--shadow-subtle)] text-[var(--text)]">
            <h3 className="text-xl font-serif font-medium text-[var(--text)] mb-2 tracking-tight">
              Delete Job?
            </h3>
            <p className="text-xs text-[var(--text-muted)] mb-6">
              Are you sure you want to delete job <code className="text-xs font-mono">{selectedJob.slice(0, 12)}...</code>? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-2.5">
              <button
                onClick={() => setSelectedJob(null)}
                className="px-4 h-9 border border-[var(--border)] bg-transparent text-[var(--text)] squircle-sm text-xs font-medium hover:bg-[var(--surface-2)] transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  deleteMutation.mutate(selectedJob);
                  setSelectedJob(null);
                }}
                disabled={deleteMutation.isPending}
                className="px-4 h-9 bg-[var(--status-error)] text-white squircle-sm text-xs font-medium hover:opacity-90 disabled:opacity-40 transition-colors cursor-pointer"
              >
                {deleteMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}