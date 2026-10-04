import { useState } from 'react';
import { Rocket, ExternalLink, Loader2, CheckCircle2 } from 'lucide-react';

interface DeploymentTabProps {
  jobId: string;
  models?: any[];
  endpoints?: Record<string, string>;
  onDeploy?: (index: number) => Promise<void>;
  isDeploying?: boolean;
}

export function DeploymentTab({ 
  jobId, 
  models = [], 
  endpoints = {}, 
  onDeploy, 
  isDeploying = false 
}: DeploymentTabProps) {
  const [deployingIndex, setDeployingIndex] = useState<number | null>(null);
  const [deployedModels, setDeployedModels] = useState<Record<string, string>>({});

  const handleDeployClick = async (index: number) => {
    setDeployingIndex(index);
    try {
      if (onDeploy) {
        await onDeploy(index);
      }
      const modelName = models[index]?.model_name || `model_${index}`;
      setDeployedModels(prev => ({
        ...prev,
        [modelName]: `https://api.automl.example.com/models/${modelName}/${jobId}`,
      }));
    } catch (error) {
      console.error('Deployment failed:', error);
    } finally {
      setDeployingIndex(null);
    }
  };

  const allEndpoints = { ...endpoints, ...deployedModels };
  const deployedEntries = Object.entries(allEndpoints);
  const topModels = models.slice(0, 3);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-medium text-[var(--text)] flex items-center gap-2">
            <Rocket className="w-4 h-4 text-[var(--accent)]" strokeWidth={1.5} />
            Model Deployment
          </h3>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            Deploy your trained models as production-ready microservice endpoints.
          </p>
        </div>
      </div>

      {deployedEntries.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-xs font-mono uppercase tracking-wider text-[var(--text-muted)] flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[var(--status-success)]" />
            Active Endpoints
          </h4>
          <div className="space-y-2">
            {deployedEntries.map(([name, url]) => (
              <div
                key={name}
                className="surface-card squircle-lg border border-[var(--border)] p-4 flex items-center justify-between"
              >
                <div>
                  <p className="text-sm font-medium text-[var(--text)]">{name}</p>
                  <p className="text-xs text-[var(--text-muted)] font-mono truncate max-w-md mt-0.5">
                    {url}
                  </p>
                </div>
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="h-8 px-3 border border-[var(--border)] rounded-[var(--r-sm)] squircle-sm bg-[var(--surface-2)] text-[var(--text)] hover:border-[var(--accent)] text-xs font-mono flex items-center gap-1.5 transition-colors"
                >
                  <ExternalLink className="w-3.5 h-3.5 text-[var(--text-muted)]" strokeWidth={1.5} />
                  Open Endpoint
                </a>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-3">
        <h4 className="text-xs font-mono uppercase tracking-wider text-[var(--text-muted)]">Top Recommended Models</h4>
        {topModels.length === 0 ? (
          <p className="text-xs text-[var(--text-muted)]">No trained models available to deploy.</p>
        ) : (
          <div className="space-y-2">
            {topModels.map((model, i) => {
              const isAlreadyDeployed = !!allEndpoints[model.model_name];
              const isCurrentlyDeploying = deployingIndex === i || isDeploying;

              return (
                <div
                  key={model.model_name || i}
                  className="surface-card squircle-lg border border-[var(--border)] p-4 flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-7 h-7 rounded-[var(--r-sm)] squircle-sm border border-[var(--border)] bg-[var(--surface-2)] flex items-center justify-center font-mono text-xs font-medium text-[var(--text)]">
                      {i + 1}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-[var(--text)]">{model.model_name}</p>
                      <p className="text-xs font-mono tabular-nums text-[var(--text-muted)] mt-0.5">
                        Score: {((model.composite_score || 0) * 100).toFixed(1)}% •{' '}
                        {model.train_time || 0}s training time
                      </p>
                    </div>
                  </div>

                  <div>
                    {isAlreadyDeployed ? (
                      <span className="h-8 px-3 rounded-[var(--r-sm)] squircle-sm border border-[var(--border)] bg-[var(--surface-2)] text-[var(--status-success)] text-xs font-mono flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5" strokeWidth={1.5} /> Deployed
                      </span>
                    ) : (
                      <button
                        onClick={() => handleDeployClick(i)}
                        disabled={isCurrentlyDeploying}
                        className="h-8 px-3.5 rounded-[var(--r-sm)] squircle-sm bg-[var(--accent)] text-[var(--accent-fg)] hover:opacity-90 disabled:opacity-50 flex items-center gap-1.5 text-xs font-medium transition-opacity"
                      >
                        {isCurrentlyDeploying ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin" strokeWidth={1.5} /> Deploying...
                          </>
                        ) : (
                          <>
                            <Rocket className="w-3.5 h-3.5" strokeWidth={1.5} /> Deploy
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}