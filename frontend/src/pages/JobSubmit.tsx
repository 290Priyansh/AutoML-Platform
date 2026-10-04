import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useNavigate } from 'react-router-dom';
import { useCreateJob, useAvailableModels } from '../hooks/useApi';
import {
  Upload,
  FileText,
  Loader2,
  AlertCircle,
  X,
  Sparkles,
  Layers,
  Cpu,
  ArrowRight,
  ShieldCheck,
  FileSpreadsheet,
} from 'lucide-react';
import { cn, formatNumber } from '../lib/utils';

const ACCEPTED_TYPES = {
  'text/csv': ['.csv'],
  'application/pdf': ['.pdf'],
  'text/plain': ['.txt'],
};

const MAX_FILE_SIZE = 500 * 1024 * 1024;

export function JobSubmit() {
  const navigate = useNavigate();
  const { data: models } = useAvailableModels();
  const createJob = useCreateJob();

  const [file, setFile] = useState<File | null>(null);
  const [model, setModel] = useState<string>('');
  const [targetCol, setTargetCol] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [isDragActive, setIsDragActive] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const newFile = acceptedFiles[0];
      if (validateFile(newFile)) {
        setFile(newFile);
        setError('');
      }
    }
  }, []);

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: MAX_FILE_SIZE,
    multiple: false,
    onDragEnter: () => setIsDragActive(true),
    onDragLeave: () => setIsDragActive(false),
  });

  const validateFile = (file: File) => {
    const extension = file.name.split('.').pop()?.toLowerCase();
    const allowedExtensions = ['csv', 'pdf', 'txt'];
    
    if (!allowedExtensions.includes(extension || '')) {
      setError('Invalid file type. Please upload a CSV, PDF, or TXT file.');
      return false;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError('File too large. Maximum size is 500MB for CSV, 200MB for PDF.');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file) {
      setError('Please select a dataset file to launch AutoML.');
      return;
    }

    try {
      const result = await createJob.mutateAsync({ file, model: model || undefined, targetCol: targetCol || undefined });
      navigate(`/jobs/${result.job_id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to create training job.');
    }
  };

  const removeFile = (e: React.MouseEvent) => {
    e.stopPropagation();
    setFile(null);
    setError('');
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      {/* Header Area - Flat typographic header with bottom divider */}
      <div className="border-b border-[var(--border)] pb-8">
        <div className="space-y-3">
          <div className="inline-flex items-center gap-1.5 text-xs font-medium text-[var(--accent)] tracking-tight">
            <Sparkles className="w-3.5 h-3.5" />
            Instant ML Training Pipeline
          </div>
          <h1 className="text-3xl sm:text-4xl font-serif font-normal tracking-tight text-[var(--text)]">
            Upload & Train Dataset
          </h1>
          <p className="text-sm sm:text-base text-[var(--text-muted)] max-w-2xl leading-relaxed">
            Upload your tabular CSV or document dataset. Our autonomous multi-agent pipeline will classify the task, clean features, run Optuna HPO, train models, and package artifacts.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Form Container: Grouped fields separated by dividers */}
        <div className="surface-card squircle-xl divide-y divide-[var(--border)] overflow-hidden">
          {/* Upload Zone Section */}
          <div className="p-6 sm:p-8 space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-semibold text-[var(--text)] flex items-center gap-2">
                <FileSpreadsheet className="w-4 h-4 text-[var(--accent)]" />
                Dataset File
              </label>
              <span className="text-xs text-[var(--text-muted)]">
                CSV, PDF, or TXT (up to 500MB)
              </span>
            </div>
            
            <div
              {...getRootProps()}
              className={cn(
                'relative border border-dashed squircle-lg p-8 sm:p-12 text-center transition-colors cursor-pointer group',
                isDragActive
                  ? 'border-[var(--accent)] bg-[var(--surface-2)]'
                  : 'border-[var(--border)] bg-[var(--surface)] hover:border-[var(--text-muted)] hover:bg-[var(--surface-2)]/40',
                file && 'border-[var(--accent)] bg-[var(--surface-2)]/60'
              )}
            >
              <input {...getInputProps()} />
              
              {file ? (
                <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                  <div className="w-12 h-12 squircle-md bg-[var(--surface)] border border-[var(--border)] flex items-center justify-center">
                    <FileText className="w-6 h-6 text-[var(--accent)]" />
                  </div>
                  <div className="text-center sm:text-left">
                    <p className="font-medium text-sm text-[var(--text)]">{file.name}</p>
                    <p className="text-xs text-[var(--text-muted)] mt-0.5 font-mono">
                      {formatNumber(file.size)} bytes • {file.type || 'Data file'}
                    </p>
                    <span className="inline-flex items-center gap-1.5 mt-1.5 text-[11px] font-medium text-[var(--status-success)]">
                      <span className="w-1.5 h-1.5 rounded-full bg-[var(--status-success)]" /> Ready for processing
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={removeFile}
                    className="p-1.5 text-[var(--text-muted)] hover:text-[var(--status-error)] hover:bg-[var(--surface)] squircle-sm transition-colors sm:ml-auto cursor-pointer"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div className="space-y-2.5">
                  <div className="w-10 h-10 mx-auto squircle-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--text-muted)] group-hover:text-[var(--text)] transition-colors">
                    <Upload className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-[var(--text)]">
                      Drop your dataset here, or <span className="text-[var(--accent)] underline">browse files</span>
                    </p>
                    <p className="text-xs text-[var(--text-muted)] mt-0.5">
                      Supports tabular CSV, text, and unstructured PDF documents
                    </p>
                  </div>
                </div>
              )}
            </div>

            {error && (
              <div className="flex items-center gap-2.5 p-3 squircle-sm border border-[var(--status-error)]/20 bg-[var(--surface-2)] text-[var(--status-error)] text-xs">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <p>{error}</p>
              </div>
            )}
          </div>

          {/* Configuration Options Section */}
          <div className="p-6 sm:p-8 space-y-5">
            <h3 className="text-sm font-semibold text-[var(--text)] flex items-center gap-2">
              <Layers className="w-4 h-4 text-[var(--accent)]" />
              Pipeline Parameters (Optional)
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-1.5">
                <label className="block text-[11px] font-medium uppercase tracking-wider text-[var(--text-muted)]">
                  Target Column Name
                </label>
                <input
                  type="text"
                  value={targetCol}
                  onChange={(e) => setTargetCol(e.target.value)}
                  placeholder="e.g., target, label, churn, price"
                  className="w-full h-10 px-3.5 border border-[var(--border)] squircle-sm bg-[var(--surface)] text-[var(--text)] text-xs placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:border-transparent transition-all shadow-none"
                />
                <p className="text-[11px] text-[var(--text-muted)]">
                  Leave empty for automatic heuristic and LLM target inference.
                </p>
              </div>

              <div className="space-y-1.5">
                <label className="block text-[11px] font-medium uppercase tracking-wider text-[var(--text-muted)]">
                  Algorithm Preference
                </label>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="w-full h-10 px-3.5 border border-[var(--border)] squircle-sm bg-[var(--surface)] text-[var(--text)] text-xs focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:border-transparent transition-all shadow-none cursor-pointer"
                >
                  <option value="">Auto-select & train top models</option>
                  {models?.map((m: any) => (
                    <option key={m.name} value={m.name}>
                      {m.name} ({m.problem_type})
                    </option>
                  ))}
                </select>
                <p className="text-[11px] text-[var(--text-muted)]">
                  Multi-algorithm benchmark will test top contenders automatically.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Submit Action */}
        <button
          type="submit"
          disabled={createJob.isPending || !file}
          className={cn(
            'w-full h-10 px-6 squircle-sm font-medium text-xs transition-colors flex items-center justify-center gap-2 cursor-pointer',
            createJob.isPending || !file
              ? 'bg-[var(--surface-2)] text-[var(--text-muted)] opacity-40 cursor-not-allowed border border-[var(--border)]'
              : 'bg-[var(--accent)] text-[var(--accent-contrast)] hover:bg-[var(--accent-hover)] border border-black/10 dark:border-white/10 shadow-[var(--shadow-subtle)]'
          )}
        >
          {createJob.isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Initializing Multi-Agent Pipeline...
            </>
          ) : (
            <>
              <Upload className="w-4 h-4" />
              Launch AutoML Pipeline
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </form>

      {/* Feature Highlights - Restyled as single surface with 1px dividers */}
      <div className="surface-card squircle-lg grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-[var(--border)]">
        {[
          { icon: Cpu, title: '24 Autonomous Agents', desc: 'From cleaning and NLP embeddings to Optuna HPO and ensembling.' },
          { icon: ShieldCheck, title: 'Bias & Data Quality', desc: 'Automatic missing-value imputation, outlier detection, and demographic fairness.' },
          { icon: Sparkles, title: 'SHAP & Packaged Model', desc: 'Global feature importance charts, markdown/PDF reports, and joblib artifacts.' },
        ].map((item, i) => (
          <div key={i} className="p-5 flex items-start gap-3.5">
            <item.icon className="w-4 h-4 text-[var(--text-muted)] flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="text-xs font-semibold text-[var(--text)]">{item.title}</h4>
              <p className="text-[11px] text-[var(--text-muted)] mt-1 leading-relaxed">{item.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}