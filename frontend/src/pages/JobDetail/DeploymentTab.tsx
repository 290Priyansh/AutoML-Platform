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
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <Rocket className="w-5 h-5 text-purple-600" />
            Model Deployment
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Deploy your trained models as production-ready microservice endpoints.
          </p>
        </div>
      </div>

      {deployedEntries.length > 0 && (
        <div className="space-y-4">
          <h4 className="font-medium text-gray-900 dark:text-white flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-green-500" />
            Active Endpoints
          </h4>
          <div className="space-y-3">
            {deployedEntries.map(([name, url]) => (
              <div
                key={name}
                className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-4 flex items-center justify-between"
              >
                <div>
                  <p className="font-semibold text-gray-900 dark:text-white">{name}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-300 font-mono truncate max-w-md">
                    {url}
                  </p>
                </div>
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm flex items-center gap-1.5"
                >
                  <ExternalLink className="w-4 h-4" />
                  Open Endpoint
                </a>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-4">
        <h4 className="font-medium text-gray-900 dark:text-white">Top Recommended Models</h4>
        {topModels.length === 0 ? (
          <p className="text-sm text-gray-500">No trained models available to deploy.</p>
        ) : (
          <div className="space-y-3">
            {topModels.map((model, i) => {
              const isAlreadyDeployed = !!allEndpoints[model.model_name];
              const isCurrentlyDeploying = deployingIndex === i || isDeploying;

              return (
                <div
                  key={model.model_name || i}
                  className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:border-purple-300 dark:hover:border-purple-700 transition-colors rounded-xl p-4 flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 flex items-center justify-center font-bold text-white text-sm">
                      {i + 1}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{model.model_name}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        Score: {((model.composite_score || 0) * 100).toFixed(1)}% •{' '}
                        {model.train_time || 0}s training time
                      </p>
                    </div>
                  </div>

                  <div>
                    {isAlreadyDeployed ? (
                      <span className="px-3 py-1.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-lg text-sm font-medium flex items-center gap-1">
                        <CheckCircle2 className="w-4 h-4" /> Deployed
                      </span>
                    ) : (
                      <button
                        onClick={() => handleDeployClick(i)}
                        disabled={isCurrentlyDeploying}
                        className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 flex items-center gap-2 text-sm font-medium"
                      >
                        {isCurrentlyDeploying ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" /> Deploying...
                          </>
                        ) : (
                          <>
                            <Rocket className="w-4 h-4" /> Deploy
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