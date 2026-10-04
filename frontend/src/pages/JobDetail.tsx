import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useJobStatus, useJobResults, useJobModels, useJobPlots, useJobReport, useDeployModel } from '../hooks/useApi';
import { useJobWebSocket } from '../hooks/useWebSocket';
import { apiClient } from '../api/client';
import { cn, downloadBlob } from '../lib/utils';
import {
  Loader2,
  CheckCircle,
  AlertCircle,
  X,
  Download,
  BarChart2,
  FileText,
  Rocket,
  Brain,
  Search,
  Sparkles,
  Layers,
  Cpu,
  Workflow,
  Clock,
} from 'lucide-react';
import { OverviewTab } from './JobDetail/OverviewTab';
import { ModelsTab } from './JobDetail/ModelsTab';
import { PlotsTab } from './JobDetail/PlotsTab';
import { ExplainabilityTab } from './JobDetail/ExplainabilityTab';
import { ReportTab } from './JobDetail/ReportTab';
import { DeploymentTab } from './JobDetail/DeploymentTab';
import { Button } from '../components/ui/button';
import { Tabs, TabsList, TabsTrigger } from '../components/ui/tabs';

const AGENT_ORDER = [
  'ingestion', 'eda', 'problem_classifier', 'data_quality', 'split',
  'cleaning', 'nlp', 'encoding', 'scaling', 'feature_engineering', 'feature_selection', 'imbalance_handler',
  'cv_strategy', 'training', 'hpo', 'evaluation', 'ranking', 'ensemble',
  'explainability', 'bias_fairness', 'report', 'packaging', 'deployment', 'drift_monitor',
];

const AGENT_LABELS: Record<string, string> = {
  ingestion: 'Data Ingestion',
  eda: 'Exploratory Data Analysis',
  problem_classifier: 'Problem Classification',
  data_quality: 'Data Quality Assessment',
  split: 'Train/Val/Test Split',
  cleaning: 'Data Cleaning',
  nlp: 'NLP Processing',
  encoding: 'Feature Encoding',
  scaling: 'Feature Scaling',
  feature_engineering: 'Feature Engineering',
  feature_selection: 'Feature Selection',
  imbalance_handler: 'Imbalance Handling',
  cv_strategy: 'CV Strategy',
  training: 'Model Training',
  hpo: 'Hyperparameter Optimization',
  evaluation: 'Model Evaluation',
  ranking: 'Model Ranking',
  ensemble: 'Ensemble Building',
  explainability: 'Explainability & SHAP',
  bias_fairness: 'Bias & Fairness Audit',
  report: 'Report Generation',
  packaging: 'Model Packaging',
  deployment: 'Model Deployment',
  drift_monitor: 'Drift Monitoring Setup',
};

const AGENT_PHASES: Record<string, string> = {
  ingestion: 'phase1_understanding',
  eda: 'phase1_understanding',
  problem_classifier: 'phase1_understanding',
  data_quality: 'phase1_understanding',
  split: 'phase1_understanding',
  cleaning: 'phase2_preprocessing',
  nlp: 'phase2_preprocessing',
  encoding: 'phase2_preprocessing',
  scaling: 'phase2_preprocessing',
  feature_engineering: 'phase2_preprocessing',
  feature_selection: 'phase2_preprocessing',
  imbalance_handler: 'phase2_preprocessing',
  cv_strategy: 'phase3_modeling',
  training: 'phase3_modeling',
  hpo: 'phase3_modeling',
  evaluation: 'phase3_modeling',
  ranking: 'phase3_modeling',
  ensemble: 'phase3_modeling',
  explainability: 'phase4_output',
  bias_fairness: 'phase4_output',
  report: 'phase4_output',
  packaging: 'phase4_output',
  deployment: 'phase4_output',
  drift_monitor: 'phase4_output',
};

const PHASES_CONFIG = [
  {
    phase: 'phase1_understanding',
    label: 'Phase 1: Understanding',
    subtitle: 'Data Ingestion, EDA & Split',
    icon: Search,
    color: 'purple',
    gradient: 'from-purple-500 to-indigo-600',
    borderColor: 'border-purple-200 dark:border-purple-800/60',
    bgLight: 'bg-purple-50/70 dark:bg-purple-950/20',
    textColor: 'text-purple-700 dark:text-purple-300',
    dotColor: 'bg-purple-500',
  },
  {
    phase: 'phase2_preprocessing',
    label: 'Phase 2: Preprocessing',
    subtitle: 'Cleaning, NLP, Scaling & Features',
    icon: Layers,
    color: 'amber',
    gradient: 'from-amber-500 to-orange-600',
    borderColor: 'border-amber-200 dark:border-amber-800/60',
    bgLight: 'bg-amber-50/70 dark:bg-amber-950/20',
    textColor: 'text-amber-700 dark:text-amber-300',
    dotColor: 'bg-amber-500',
  },
  {
    phase: 'phase3_modeling',
    label: 'Phase 3: Modeling',
    subtitle: 'CV, Multi-Model, Optuna HPO & Ensembling',
    icon: Cpu,
    color: 'blue',
    gradient: 'from-blue-500 to-cyan-600',
    borderColor: 'border-blue-200 dark:border-blue-800/60',
    bgLight: 'bg-blue-50/70 dark:bg-blue-950/20',
    textColor: 'text-blue-700 dark:text-blue-300',
    dotColor: 'bg-blue-500',
  },
  {
    phase: 'phase4_output',
    label: 'Phase 4: Output & Deployment',
    subtitle: 'Explainability, Bias, Reports & Serving',
    icon: Rocket,
    color: 'emerald',
    gradient: 'from-emerald-500 to-teal-600',
    borderColor: 'border-emerald-200 dark:border-emerald-800/60',
    bgLight: 'bg-emerald-50/70 dark:bg-emerald-950/20',
    textColor: 'text-emerald-700 dark:text-emerald-300',
    dotColor: 'bg-emerald-500',
  },
];

export function JobDetail() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  
  const { data: jobStatus, isLoading: statusLoading } = useJobStatus(jobId!, true);
  const isCompleted = jobStatus?.status === 'completed';
  const isFailed = jobStatus?.status === 'failed';
  const isQueued = jobStatus?.status === 'queued';
  const isRunning = jobStatus?.status === 'running' || isQueued;

  const { data: jobResults } = useJobResults(jobId!, isCompleted);
  const { data: jobModels } = useJobModels(jobId!, isCompleted);
  const { data: jobPlots } = useJobPlots(jobId!, isCompleted);
  const { data: jobReport } = useJobReport(jobId!, isCompleted);
  const deployMutation = useDeployModel();

  const { isConnected, lastMessage } = useJobWebSocket(jobId!);

  const [activeTab, setActiveTab] = useState<'overview' | 'models' | 'plots' | 'explainability' | 'report' | 'deployment'>('overview');
  const [_selectedModel, setSelectedModel] = useState<any | null>(null);

  // Dynamic progress calculation (starting from 0% initially, never static 65%)
  const currentProgress = isCompleted
    ? 100
    : isQueued
      ? 0
      : Math.min(100, Math.max(0, lastMessage?.progress_pct ?? jobStatus?.progress_pct ?? 0));

  const activeAgentKey = lastMessage?.current_agent || jobStatus?.current_agent || 'ingestion';
  const activeAgentLabel = AGENT_LABELS[activeAgentKey] || activeAgentKey;
  const currentAgentIdx = isCompleted 
    ? AGENT_ORDER.length 
    : isQueued 
      ? -1 
      : AGENT_ORDER.indexOf(activeAgentKey);

  // Dynamic status evaluation for each agent
  const getAgentStatus = (agentName: string) => {
    const idx = AGENT_ORDER.indexOf(agentName);
    if (isCompleted) {
      return { status: 'completed' as const, progress: 100 };
    }
    if (isQueued) {
      return { status: 'pending' as const, progress: 0 };
    }
    if (isFailed) {
      if (idx < currentAgentIdx) return { status: 'completed' as const, progress: 100 };
      if (idx === currentAgentIdx) return { status: 'failed' as const, progress: currentProgress, error: jobStatus?.error };
      return { status: 'pending' as const, progress: 0 };
    }
    // Running state
    if (idx < currentAgentIdx) return { status: 'completed' as const, progress: 100 };
    if (idx === currentAgentIdx) return { status: 'running' as const, progress: currentProgress };
    return { status: 'pending' as const, progress: 0 };
  };

  const handleDeploy = async (modelIndex: number) => {
    try {
      await deployMutation.mutateAsync({ jobId: jobId!, modelIndex });
    } catch (error) {
      console.error('Deployment failed:', error);
    }
  };

  const handleDownloadReport = async (format: 'md' | 'pdf') => {
    try {
      const blob = await apiClient.downloadReport(jobId!, format);
      downloadBlob(blob, `automl-report-${jobId}.${format}`);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  if (statusLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-10 h-10 squircle-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center mb-3">
          <Loader2 className="w-5 h-5 animate-spin text-[var(--text-muted)]" />
        </div>
        <p className="text-xs text-[var(--text-muted)]">Synchronizing pipeline status...</p>
      </div>
    );
  }

  if (!jobStatus) {
    return (
      <div className="text-center py-16 surface-card squircle-xl border border-[var(--border)] max-w-md mx-auto p-8">
        <AlertCircle className="w-10 h-10 mx-auto text-[var(--status-error)] mb-3" />
        <h2 className="text-xl font-serif font-medium text-[var(--text)]">Job not found</h2>
        <p className="text-xs text-[var(--text-muted)] mt-1.5 px-4 leading-relaxed">
          The requested AutoML pipeline execution does not exist or has expired.
        </p>
        <Button 
          onClick={() => navigate('/jobs')} 
          variant="default"
          className="mt-6"
        >
          Return to Jobs
        </Button>
      </div>
    );
  }

  const mockFeatureImportance = {
    'feature_1': 0.45, 'feature_2': -0.32, 'feature_3': 0.28, 'feature_4': -0.24,
    'feature_5': 0.19, 'feature_6': -0.15, 'feature_7': 0.12, 'feature_8': -0.10,
    'feature_9': 0.08, 'feature_10': -0.06, 'feature_11': 0.05, 'feature_12': -0.04,
  };

  return (
    <div className="space-y-8 max-w-[1280px] mx-auto pb-12">
      {/* Header Banner - Restyled flat on page background with bottom divider */}
      <div className="border-b border-[var(--border)] pb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="flex items-start sm:items-center gap-3.5">
            <div className="w-10 h-10 squircle-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--text-muted)] flex-shrink-0">
              <Brain className="w-5 h-5" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2.5 mb-1">
                <h1 className="text-2xl sm:text-3xl font-serif font-normal tracking-tight text-[var(--text)]">
                  Job <span className="font-mono text-[var(--accent)]">{jobId?.slice(0, 10)}</span>
                </h1>
                <span className="inline-flex items-center gap-1.5 text-xs font-medium uppercase">
                  <span className={cn(
                    'w-1.5 h-1.5 rounded-full',
                    jobStatus.status === 'completed' && 'bg-[var(--status-success)]',
                    jobStatus.status === 'running' && 'bg-[var(--status-running)] animate-pulse',
                    jobStatus.status === 'queued' && 'bg-[var(--status-warning)]',
                    jobStatus.status === 'failed' && 'bg-[var(--status-error)]',
                  )} />
                  <span className="text-[var(--text)]">{jobStatus.status}</span>
                  {jobStatus.status === 'running' && <Loader2 className="w-3 h-3 animate-spin text-[var(--status-running)]" />}
                </span>

                {isConnected ? (
                  <span className="inline-flex items-center gap-1.5 text-[11px] font-mono text-[var(--text-muted)]">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--status-success)]" />
                    Live Stream
                  </span>
                ) : (
                  <span className="text-[11px] font-mono text-[var(--text-muted)]">
                    Polling (2s)
                  </span>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-2.5 text-xs text-[var(--text-muted)]">
                <span className="flex items-center gap-1 font-mono">
                  <Clock className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                  {jobStatus.created_at ? new Date(jobStatus.created_at).toLocaleTimeString() : 'Just now'}
                </span>
                {jobStatus.problem_type && (
                  <span className="px-2 py-0.5 squircle-sm bg-[var(--surface-2)] border border-[var(--border)] font-mono text-[11px] text-[var(--text-muted)]">
                    {jobStatus.problem_type}
                  </span>
                )}
                {jobStatus.target_column && (
                  <span className="px-2 py-0.5 squircle-sm bg-[var(--surface-2)] border border-[var(--border)] font-mono text-[11px] text-[var(--text-muted)]">
                    target: {jobStatus.target_column}
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            {isCompleted && (
              <div className="flex items-center gap-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => handleDownloadReport('pdf')}
                  className="squircle-sm"
                >
                  <Download className="w-3.5 h-3.5 mr-1.5" />
                  PDF Report
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => handleDownloadReport('md')}
                  className="squircle-sm"
                >
                  <FileText className="w-3.5 h-3.5 mr-1.5" />
                  Markdown
                </Button>
              </div>
            )}
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => navigate('/jobs')}
              className="squircle-sm text-[var(--text-muted)] hover:text-[var(--text)]"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Main Execution Overview Card */}
      <div className="surface-card squircle-xl p-6 sm:p-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-2.5">
            <Workflow className="w-5 h-5 text-[var(--accent)]" />
            <div>
              <h2 className="text-base font-semibold text-[var(--text)]">End-to-End Pipeline Progress</h2>
              <p className="text-xs text-[var(--text-muted)]">
                All 24 multi-agent processes executed in sequence
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-2xl font-mono tabular-nums font-semibold text-[var(--text)]">
                {currentProgress}%
              </div>
              <p className="text-xs text-[var(--text-muted)]">
                {isCompleted ? 'Finished' : isQueued ? 'Queued' : 'In Execution'}
              </p>
            </div>
          </div>
        </div>

        {/* Dynamic Progress Track */}
        <div className="w-full h-1.5 bg-[var(--surface-2)] border border-[var(--border)] squircle-sm overflow-hidden mb-6">
          <div 
            className="h-full bg-[var(--accent)] squircle-sm transition-all duration-700 ease-out"
            style={{ width: `${currentProgress}%` }}
          />
        </div>

        {/* Live Active Agent Spotlight */}
        {isRunning && (
          <div className="mb-6 p-4 squircle-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span className="w-2 h-2 rounded-full bg-[var(--status-running)] animate-pulse flex-shrink-0" />
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)]">
                    Executing Agent
                  </span>
                  <span className="text-[11px] font-mono text-[var(--text-muted)]">
                    (Step {Math.max(1, currentAgentIdx + 1)} of 24)
                  </span>
                </div>
                <h3 className="text-sm font-semibold text-[var(--text)]">
                  {activeAgentLabel}
                </h3>
                {lastMessage?.message && (
                  <p className="text-[11px] font-mono text-[var(--text-muted)] mt-0.5 truncate max-w-xl">
                    {lastMessage.message}
                  </p>
                )}
              </div>
            </div>
            <div className="hidden sm:flex items-center gap-1.5 text-xs font-mono text-[var(--status-running)]">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              Active
            </div>
          </div>
        )}

        {/* Failed Banner */}
        {isFailed && (
          <div className="mb-6 p-3.5 squircle-md bg-[var(--surface-2)] border border-[var(--status-error)]/30 flex items-center gap-2.5 text-[var(--status-error)]">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <div>
              <p className="font-medium text-xs">Pipeline failed during {activeAgentLabel}</p>
              <p className="text-[11px] text-[var(--text-muted)] mt-0.5">{jobStatus.error || 'Check server logs for detailed traceback.'}</p>
            </div>
          </div>
        )}

        {/* Dynamic 4-Phase Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {PHASES_CONFIG.map(({ phase, label, icon: PhaseIcon }) => {
            const phaseAgents = AGENT_ORDER.filter(a => AGENT_PHASES[a] === phase);
            const completedInPhase = phaseAgents.filter(a => getAgentStatus(a).status === 'completed').length;
            const hasRunning = phaseAgents.some(a => getAgentStatus(a).status === 'running');

            return (
              <div 
                key={phase} 
                className="squircle-lg border border-[var(--border)] bg-[var(--surface)] overflow-hidden flex flex-col"
              >
                {/* Phase Header */}
                <div className="p-3.5 bg-[var(--surface-2)] border-b border-[var(--border)] flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <PhaseIcon className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                    <div>
                      <h4 className="text-xs font-semibold text-[var(--text)]">{label}</h4>
                      <p className="text-[11px] font-mono text-[var(--text-muted)]">{completedInPhase} / {phaseAgents.length} completed</p>
                    </div>
                  </div>
                  {completedInPhase === phaseAgents.length && (
                    <CheckCircle className="w-3.5 h-3.5 text-[var(--status-success)] flex-shrink-0" />
                  )}
                  {hasRunning && (
                    <Loader2 className="w-3.5 h-3.5 text-[var(--status-running)] animate-spin flex-shrink-0" />
                  )}
                </div>

                {/* Agents in Phase */}
                <div className="divide-y divide-[var(--border)] flex-1">
                  {phaseAgents.map((agentName) => {
                    const agentState = getAgentStatus(agentName);
                    const isCurrent = agentState.status === 'running';

                    return (
                      <div 
                        key={agentName}
                        className={cn(
                          'px-3.5 py-2 flex items-center justify-between transition-colors text-xs',
                          isCurrent ? 'bg-[var(--surface-2)] font-medium' : 'hover:bg-[var(--surface-2)]/50'
                        )}
                      >
                        <div className="flex items-center gap-2 min-w-0 pr-2">
                          <span className={cn(
                            'w-1.5 h-1.5 rounded-full flex-shrink-0',
                            agentState.status === 'completed' && 'bg-[var(--status-success)]',
                            agentState.status === 'running' && 'bg-[var(--status-running)] animate-pulse',
                            agentState.status === 'failed' && 'bg-[var(--status-error)]',
                            agentState.status === 'pending' && 'bg-[var(--border)]'
                          )} />
                          <span className={cn(
                            'truncate text-[11px]',
                            agentState.status === 'completed' && 'text-[var(--text)]',
                            agentState.status === 'running' && 'text-[var(--text)] font-semibold',
                            agentState.status === 'failed' && 'text-[var(--status-error)]',
                            agentState.status === 'pending' && 'text-[var(--text-muted)]'
                          )}>
                            {AGENT_LABELS[agentName] || agentName}
                          </span>
                        </div>

                        <div className="flex items-center gap-1.5 flex-shrink-0">
                          {agentState.status === 'completed' && (
                            <CheckCircle className="w-3 h-3 text-[var(--status-success)]" />
                          )}
                          {agentState.status === 'running' && (
                            <Loader2 className="w-3 h-3 text-[var(--status-running)] animate-spin" />
                          )}
                          {agentState.status === 'failed' && (
                            <AlertCircle className="w-3 h-3 text-[var(--status-error)]" />
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Tabs Container */}
      <div className="surface-card squircle-xl overflow-hidden">
        <div className="border-b border-[var(--border)] px-6 pt-4 bg-[var(--surface-2)]/40">
          <Tabs value={activeTab} onValueChange={(val) => setActiveTab(val as any)} className="w-full">
            <TabsList className="grid w-full grid-cols-6 h-9">
              <TabsTrigger value="overview"><BarChart2 className="w-3.5 h-3.5 mr-1.5" />Overview</TabsTrigger>
              <TabsTrigger value="models" disabled={!isCompleted}><Brain className="w-3.5 h-3.5 mr-1.5" />Models</TabsTrigger>
              <TabsTrigger value="plots" disabled={!isCompleted}><FileText className="w-3.5 h-3.5 mr-1.5" />Plots</TabsTrigger>
              <TabsTrigger value="explainability" disabled={!isCompleted}><Search className="w-3.5 h-3.5 mr-1.5" />SHAP</TabsTrigger>
              <TabsTrigger value="report" disabled={!isCompleted}><Sparkles className="w-3.5 h-3.5 mr-1.5" />Report</TabsTrigger>
              <TabsTrigger value="deployment" disabled={!isCompleted}><Rocket className="w-3.5 h-3.5 mr-1.5" />Deploy</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        <div className="p-6 sm:p-8">
          {activeTab === 'overview' && <OverviewTab jobStatus={jobStatus} jobResults={jobResults} />}
          {activeTab === 'models' && <ModelsTab models={jobResults?.ranked_models || jobModels?.models || []} onSelectModel={setSelectedModel} onDeploy={handleDeploy} />}
          {activeTab === 'plots' && <PlotsTab plots={jobPlots || {}} />}
          {activeTab === 'explainability' && <ExplainabilityTab featureImportance={jobResults?.feature_importance || mockFeatureImportance} shapValues={jobResults?.shap_values} />}
          {activeTab === 'report' && <ReportTab report={jobReport} onDownload={handleDownloadReport} />}
          {activeTab === 'deployment' && (
            <DeploymentTab 
              jobId={jobId!} 
              models={jobResults?.ranked_models || jobModels?.models || []}
              endpoints={jobResults?.inference_endpoints} 
              onDeploy={handleDeploy}
              isDeploying={deployMutation.isPending}
            />
          )}
        </div>
      </div>
    </div>
  );
}