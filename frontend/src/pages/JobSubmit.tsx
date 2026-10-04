import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useNavigate } from 'react-router-dom';
import { useCreateJob, useAvailableModels } from '../hooks/useApi';
import {
  Upload,
  FileText,
  Loader2,
  AlertCircle,
  CheckCircle,
  X,
  Sparkles,
  Layers,
  Cpu,
  ArrowRight,
  ShieldCheck,
  FileSpreadsheet,
} from 'lucide-react';
import { cn, formatNumber } from '../lib/utils';
import { Button } from '../components/ui/button';

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
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-gray-950 via-purple-950 to-slate-900 text-white p-8 shadow-2xl border border-purple-500/20">
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30 backdrop-blur-md">
            <Sparkles className="w-3.5 h-3.5" />
            Instant ML Training Pipeline
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
            Upload & Train Dataset
          </h1>
          <p className="text-gray-300 text-sm sm:text-base max-w-2xl leading-relaxed">
            Upload your tabular CSV or document dataset. Our autonomous multi-agent pipeline will classify the task, clean features, run Optuna HPO, train models, and package artifacts.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Upload Zone Card */}
        <div className="glass-panel rounded-3xl p-6 sm:p-8 border border-gray-200/80 dark:border-gray-700/80 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <label className="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <FileSpreadsheet className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              Dataset File
            </label>
            <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">
              CSV, PDF, or TXT (up to 500MB)
            </span>
          </div>
          
          <div
            {...getRootProps()}
            className={cn(
              'relative border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center transition-all cursor-pointer group',
              isDragActive
                ? 'border-purple-500 bg-purple-50/80 dark:bg-purple-950/30 scale-[1.01]'
                : 'border-gray-300 dark:border-gray-700 hover:border-purple-400 hover:bg-purple-50/30 dark:hover:bg-purple-950/10',
              file && 'border-emerald-500 bg-emerald-50/40 dark:bg-emerald-950/20'
            )}
          >
            <input {...getInputProps()} />
            
            {file ? (
              <div className="flex flex-col sm:flex-row items-center justify-center gap-5">
                <div className="w-16 h-16 rounded-2xl bg-emerald-100 dark:bg-emerald-950/60 flex items-center justify-center shadow-md">
                  <FileText className="w-8 h-8 text-emerald-600 dark:text-emerald-400" />
                </div>
                <div className="text-center sm:text-left">
                  <p className="font-bold text-base text-gray-900 dark:text-white">{file.name}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {formatNumber(file.size)} bytes • {file.type || 'Data file'}
                  </p>
                  <span className="inline-flex items-center gap-1 mt-2 text-xs font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-100 dark:bg-emerald-950/60 px-2.5 py-0.5 rounded-full">
                    <CheckCircle className="w-3.5 h-3.5" /> Ready for processing
                  </span>
                </div>
                <button
                  type="button"
                  onClick={removeFile}
                  className="p-2 text-gray-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 rounded-xl transition-all ml-auto"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="w-16 h-16 mx-auto rounded-2xl bg-purple-100 dark:bg-purple-950/60 flex items-center justify-center text-purple-600 dark:text-purple-400 group-hover:scale-110 transition-transform shadow-inner">
                  <Upload className="w-8 h-8" />
                </div>
                <div>
                  <p className="text-base font-bold text-gray-900 dark:text-white">
                    Drop your dataset here, or <span className="text-purple-600 dark:text-purple-400 underline">browse files</span>
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Supports tabular CSV, text, and unstructured PDF documents
                  </p>
                </div>
              </div>
            )}
          </div>

          {error && (
            <div className="flex items-center gap-3 p-3.5 rounded-2xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800/60 text-rose-700 dark:text-rose-300 text-sm">
              <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-600" />
              <p>{error}</p>
            </div>
          )}
        </div>

        {/* Configuration Options Card */}
        <div className="glass-panel rounded-3xl p-6 sm:p-8 border border-gray-200/80 dark:border-gray-700/80 shadow-sm space-y-6">
          <h3 className="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            Pipeline Parameters (Optional)
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300">
                Target Column Name
              </label>
              <input
                type="text"
                value={targetCol}
                onChange={(e) => setTargetCol(e.target.value)}
                placeholder="e.g., target, label, churn, price"
                className="w-full px-4 py-3 border border-gray-200 dark:border-gray-700 rounded-2xl bg-white dark:bg-gray-800/90 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition-all shadow-sm"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Leave empty for automatic heuristic and LLM target inference.
              </p>
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300">
                Algorithm Preference
              </label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full px-4 py-3 border border-gray-200 dark:border-gray-700 rounded-2xl bg-white dark:bg-gray-800/90 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition-all shadow-sm"
              >
                <option value="">Auto-select & train top models</option>
                {models?.map((m: any) => (
                  <option key={m.name} value={m.name}>
                    {m.name} ({m.problem_type})
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Multi-algorithm benchmark will test top contenders automatically.
              </p>
            </div>
          </div>
        </div>

        {/* Submit Action */}
        <button
          type="submit"
          disabled={createJob.isPending || !file}
          className={cn(
            'w-full py-4 px-6 rounded-2xl font-bold text-base transition-all duration-300 flex items-center justify-center gap-3 shadow-lg',
            createJob.isPending || !file
              ? 'bg-gray-200 dark:bg-gray-800 text-gray-400 dark:text-gray-600 cursor-not-allowed border border-gray-200 dark:border-gray-700'
              : 'bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 hover:from-purple-700 hover:to-indigo-700 text-white shadow-purple-600/30 transform hover:-translate-y-0.5 active:translate-y-0'
          )}
        >
          {createJob.isPending ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Initializing Multi-Agent Pipeline...
            </>
          ) : (
            <>
              <Upload className="w-5 h-5" />
              Launch AutoML Pipeline
              <ArrowRight className="w-5 h-5" />
            </>
          )}
        </button>
      </form>

      {/* Feature Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 pt-4">
        {[
          { icon: Cpu, title: '24 Autonomous Agents', desc: 'From cleaning and NLP embeddings to Optuna HPO and ensembling.' },
          { icon: ShieldCheck, title: 'Bias & Data Quality', desc: 'Automatic missing-value imputation, outlier detection, and demographic fairness.' },
          { icon: Sparkles, title: 'SHAP & Packaged Model', desc: 'Global feature importance charts, markdown/PDF reports, and joblib artifacts.' },
        ].map((item, i) => (
          <div key={i} className="glass-panel p-5 rounded-3xl border border-gray-200/80 dark:border-gray-700/80 shadow-sm flex items-start gap-4">
            <div className="p-2.5 rounded-2xl bg-purple-100 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400 flex-shrink-0">
              <item.icon className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-gray-900 dark:text-white">{item.title}</h4>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 leading-relaxed">{item.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}