import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useJobStatus, useJobResults, useJobModels, useJobPlots, useJobReport, useDeployModel } from '../hooks/useApi';
import { useJobWebSocket } from '../hooks/useWebSocket';
import { apiClient } from '../api/client';
import { cn, formatDuration, downloadBlob } from '../lib/utils';
import {
  Loader2,
  CheckCircle,
  AlertCircle,
  X,
  ChevronRight,
  Download,
  BarChart2,
  FileText,
  Rocket,
  Brain,
  Search,
  Sparkles,
  Activity,
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
  const [selectedModel, setSelectedModel] = useState<any | null>(null);

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
        <div className="relative w-20 h-20">
          <div className="absolute inset-0 rounded-full border-4 border-purple-200 dark:border-purple-900/40 animate-ping opacity-25" />
          <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-purple-600 border-r-indigo-600 animate-spin" />
        </div>
        <p className="mt-6 text-base font-medium text-gray-700 dark:text-gray-300">Synchronizing pipeline status...</p>
      </div>
    );
  }

  if (!jobStatus) {
    return (
      <div className="text-center py-20 bg-white dark:bg-gray-800 rounded-3xl border border-gray-200 dark:border-gray-700 shadow-sm max-w-lg mx-auto">
        <AlertCircle className="w-14 h-14 mx-auto text-red-500 mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Job not found</h2>
        <p className="text-gray-500 dark:text-gray-400 mt-2 px-6">The requested AutoML pipeline execution does not exist or has expired.</p>
        <Button 
          onClick={() => navigate('/jobs')} 
          className="mt-6 px-6 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-xl shadow-md transition-all"
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
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-gray-900 via-purple-950 to-slate-900 text-white p-6 sm:p-8 shadow-xl border border-purple-500/20">
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 -mb-12 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="flex items-start sm:items-center gap-4">
            <div className="p-3.5 bg-gradient-to-tr from-purple-600 to-indigo-500 rounded-2xl shadow-lg ring-4 ring-purple-500/20">
              <Brain className="w-8 h-8 text-white" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2.5 mb-1.5">
                <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
                  Job <span className="font-mono text-purple-300">{jobId?.slice(0, 10)}</span>
                </h1>
                <span className={cn(
                  'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider backdrop-blur-md shadow-sm',
                  jobStatus.status === 'completed' && 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30',
                  jobStatus.status === 'running' && 'bg-blue-500/20 text-blue-300 border border-blue-500/30 animate-pulse',
                  jobStatus.status === 'queued' && 'bg-amber-500/20 text-amber-300 border border-amber-500/30',
                  jobStatus.status === 'failed' && 'bg-rose-500/20 text-rose-300 border border-rose-500/30',
                )}>
                  {jobStatus.status === 'running' && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  {jobStatus.status === 'completed' && <CheckCircle className="w-3.5 h-3.5" />}
                  {jobStatus.status}
                </span>

                {isConnected ? (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
                    </span>
                    Live Stream
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-700/50 text-gray-400 border border-gray-600/40">
                    Polling (2s)
                  </span>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-3 text-xs sm:text-sm text-gray-300">
                <span className="flex items-center gap-1">
                  <Clock className="w-4 h-4 text-purple-400" />
                  {jobStatus.created_at ? new Date(jobStatus.created_at).toLocaleTimeString() : 'Just now'}
                </span>
                {jobStatus.problem_type && (
                  <span className="px-2 py-0.5 rounded-md bg-white/10 text-white font-mono text-xs">
                    {jobStatus.problem_type}
                  </span>
                )}
                {jobStatus.target_column && (
                  <span className="px-2 py-0.5 rounded-md bg-white/10 text-white font-mono text-xs">
                    target: {jobStatus.target_column}
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {isCompleted && (
              <div className="flex items-center gap-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => handleDownloadReport('pdf')}
                  className="bg-white/10 hover:bg-white/20 text-white border-white/20 rounded-xl"
                >
                  <Download className="w-4 h-4 mr-1.5" />
                  PDF Report
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => handleDownloadReport('md')}
                  className="bg-white/10 hover:bg-white/20 text-white border-white/20 rounded-xl"
                >
                  <FileText className="w-4 h-4 mr-1.5" />
                  Markdown
                </Button>
              </div>
            )}
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => navigate('/jobs')}
              className="text-gray-300 hover:text-white hover:bg-white/10 rounded-xl"
            >
              <X className="w-5 h-5" />
            </Button>
          </div>
        </div>
      </div>

      {/* Main Execution Overview Card */}
      <div className="glass-panel rounded-3xl p-6 sm:p-8 shadow-sm border border-gray-200/80 dark:border-gray-700/80">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-purple-100 dark:bg-purple-950/60 rounded-2xl">
              <Workflow className="w-6 h-6 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">End-to-End Pipeline Progress</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                All 24 multi-agent processes executed in sequence
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-2xl font-black bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent">
                {currentProgress}%
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">
                {isCompleted ? 'Finished' : isQueued ? 'Queued' : 'In Execution'}
              </p>
            </div>
          </div>
        </div>

        {/* Dynamic Progress Track */}
        <div className="relative w-full h-4 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden p-0.5 shadow-inner">
          <div 
            className="h-full bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-500 rounded-full transition-all duration-700 ease-out relative"
            style={{ width: `${currentProgress}%` }}
          >
            {isRunning && <div className="absolute inset-0 animate-shimmer rounded-full" />}
          </div>
        </div>

        {/* Live Active Agent Spotlight */}
        {isRunning && (
          <div className="mt-6 p-4 rounded-2xl bg-gradient-to-r from-blue-50/90 via-indigo-50/70 to-purple-50/90 dark:from-blue-950/30 dark:via-indigo-950/20 dark:to-purple-950/30 border border-blue-200/80 dark:border-blue-800/60 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3.5">
              <div className="relative">
                <div className="w-10 h-10 rounded-xl bg-blue-600 dark:bg-blue-500 flex items-center justify-center shadow-md">
                  <Activity className="w-5 h-5 text-white animate-pulse" />
                </div>
                <span className="absolute -top-1 -right-1 flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500" />
                </span>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs uppercase tracking-wider font-bold text-blue-600 dark:text-blue-400">
                    Executing Agent
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    (Step {Math.max(1, currentAgentIdx + 1)} of 24)
                  </span>
                </div>
                <h3 className="text-base font-bold text-gray-900 dark:text-white">
                  {activeAgentLabel}
                </h3>
                {lastMessage?.message && (
                  <p className="text-xs text-gray-600 dark:text-gray-300 mt-0.5 font-mono truncate max-w-xl">
                    {lastMessage.message}
                  </p>
                )}
              </div>
            </div>
            <div className="hidden sm:flex items-center gap-2 bg-white/80 dark:bg-gray-800/80 px-3.5 py-1.5 rounded-xl border border-blue-200 dark:border-blue-800/40 text-xs font-semibold text-blue-700 dark:text-blue-300 shadow-sm">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-600" />
              Active
            </div>
          </div>
        )}

        {/* Failed Banner */}
        {isFailed && (
          <div className="mt-6 p-4 rounded-2xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800/60 flex items-center gap-3 text-rose-700 dark:text-rose-300">
            <AlertCircle className="w-6 h-6 flex-shrink-0 text-rose-600" />
            <div>
              <p className="font-semibold text-sm">Pipeline failed during {activeAgentLabel}</p>
              <p className="text-xs text-rose-600 dark:text-rose-400 mt-0.5">{jobStatus.error || 'Check server logs for detailed traceback.'}</p>
            </div>
          </div>
        )}

        {/* Dynamic 4-Phase Grid */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {PHASES_CONFIG.map(({ phase, label, subtitle, icon: PhaseIcon, gradient, borderColor, bgLight, textColor, dotColor }) => {
            const phaseAgents = AGENT_ORDER.filter(a => AGENT_PHASES[a] === phase);
            const completedInPhase = phaseAgents.filter(a => getAgentStatus(a).status === 'completed').length;
            const hasRunning = phaseAgents.some(a => getAgentStatus(a).status === 'running');
            const hasFailed = phaseAgents.some(a => getAgentStatus(a).status === 'failed');

            return (
              <div 
                key={phase} 
                className={cn(
                  'rounded-2xl border transition-all duration-300 overflow-hidden flex flex-col bg-white dark:bg-gray-800/90 shadow-sm hover:shadow-md',
                  hasRunning ? 'ring-2 ring-blue-500 dark:ring-blue-400 border-blue-300 dark:border-blue-700 glow-active' : borderColor
                )}
              >
                {/* Phase Header */}
                <div className={cn('p-4 border-b flex items-center justify-between', bgLight, borderColor)}>
                  <div className="flex items-center gap-2.5">
                    <div className={cn('w-7 h-7 rounded-lg flex items-center justify-center text-white bg-gradient-to-tr shadow-sm', gradient)}>
                      <PhaseIcon className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className={cn('text-sm font-bold', textColor)}>{label}</h4>
                      <p className="text-[11px] text-gray-500 dark:text-gray-400">{completedInPhase} / {phaseAgents.length} completed</p>
                    </div>
                  </div>
                  {completedInPhase === phaseAgents.length && (
                    <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                  )}
                  {hasRunning && (
                    <Loader2 className="w-4 h-4 text-blue-500 animate-spin flex-shrink-0" />
                  )}
                </div>

                {/* Agents in Phase */}
                <div className="divide-y divide-gray-100 dark:divide-gray-700/60 flex-1">
                  {phaseAgents.map((agentName) => {
                    const agentState = getAgentStatus(agentName);
                    const isCurrent = agentState.status === 'running';

                    return (
                      <div 
                        key={agentName}
                        className={cn(
                          'px-3.5 py-2.5 flex items-center justify-between transition-colors text-xs',
                          isCurrent ? 'bg-blue-50/80 dark:bg-blue-900/20 font-semibold' : 'hover:bg-gray-50/80 dark:hover:bg-gray-700/30'
                        )}
                      >
                        <div className="flex items-center gap-2.5 min-w-0 pr-2">
                          <div className={cn(
                            'w-2 h-2 rounded-full flex-shrink-0',
                            agentState.status === 'completed' && 'bg-emerald-500',
                            agentState.status === 'running' && 'bg-blue-500 animate-ping',
                            agentState.status === 'failed' && 'bg-rose-500',
                            agentState.status === 'pending' && 'bg-gray-300 dark:bg-gray-600'
                          )} />
                          <span className={cn(
                            'truncate',
                            agentState.status === 'completed' && 'text-gray-700 dark:text-gray-200',
                            agentState.status === 'running' && 'text-blue-700 dark:text-blue-300',
                            agentState.status === 'failed' && 'text-rose-700 dark:text-rose-300',
                            agentState.status === 'pending' && 'text-gray-400 dark:text-gray-500'
                          )}>
                            {AGENT_LABELS[agentName] || agentName}
                          </span>
                        </div>

                        <div className="flex items-center gap-1.5 flex-shrink-0">
                          {agentState.status === 'completed' && (
                            <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
                          )}
                          {agentState.status === 'running' && (
                            <Loader2 className="w-3.5 h-3.5 text-blue-500 animate-spin" />
                          )}
                          {agentState.status === 'failed' && (
                            <AlertCircle className="w-3.5 h-3.5 text-rose-500" />
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
      <div className="glass-panel rounded-3xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
        <div className="border-b border-gray-200 dark:border-gray-700 px-6 pt-4 bg-gray-50/50 dark:bg-gray-900/40">
          <Tabs value={activeTab} onValueChange={(val) => setActiveTab(val as any)} className="w-full">
            <TabsList className="grid w-full grid-cols-6 bg-gray-200/60 dark:bg-gray-800/60 p-1 rounded-2xl">
              <TabsTrigger value="overview" className="rounded-xl font-medium"><BarChart2 className="w-4 h-4 mr-2" />Overview</TabsTrigger>
              <TabsTrigger value="models" disabled={!isCompleted} className="rounded-xl font-medium"><Brain className="w-4 h-4 mr-2" />Models</TabsTrigger>
              <TabsTrigger value="plots" disabled={!isCompleted} className="rounded-xl font-medium"><FileText className="w-4 h-4 mr-2" />Plots</TabsTrigger>
              <TabsTrigger value="explainability" disabled={!isCompleted} className="rounded-xl font-medium"><Search className="w-4 h-4 mr-2" />SHAP</TabsTrigger>
              <TabsTrigger value="report" disabled={!isCompleted} className="rounded-xl font-medium"><Sparkles className="w-4 h-4 mr-2" />Report</TabsTrigger>
              <TabsTrigger value="deployment" disabled={!isCompleted} className="rounded-xl font-medium"><Rocket className="w-4 h-4 mr-2" />Deploy</TabsTrigger>
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