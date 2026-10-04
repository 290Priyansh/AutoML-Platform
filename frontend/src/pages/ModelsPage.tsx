import { useState } from 'react';
import { cn } from '../lib/utils';
import { Search, Filter, Brain, Network, Cpu, HardDrive } from 'lucide-react';

interface ModelDetail {
  name: string;
  type: string;
  description: string;
  problem_type: 'classification' | 'regression';
}

const MODEL_CATEGORIES: Record<string, ModelDetail[]> = {
  classification: [
    { name: 'LogisticRegression', type: 'linear', description: 'Linear model for binary/multiclass classification', problem_type: 'classification' },
    { name: 'RandomForestClassifier', type: 'tree', description: 'Ensemble of decision trees', problem_type: 'classification' },
    { name: 'XGBClassifier', type: 'boosting', description: 'Gradient boosting with XGBoost', problem_type: 'classification' },
    { name: 'LGBMClassifier', type: 'boosting', description: 'LightGBM gradient boosting', problem_type: 'classification' },
    { name: 'MLPClassifier', type: 'neural', description: 'Multi-layer perceptron neural network', problem_type: 'classification' },
    { name: 'SVC', type: 'svm', description: 'Support Vector Classifier', problem_type: 'classification' },
    { name: 'KNeighborsClassifier', type: 'instance', description: 'K-Nearest Neighbors', problem_type: 'classification' },
    { name: 'AdaBoostClassifier', type: 'boosting', description: 'Adaptive Boosting', problem_type: 'classification' },
  ],
  regression: [
    { name: 'LinearRegression', type: 'linear', description: 'Ordinary least squares linear regression', problem_type: 'regression' },
    { name: 'Ridge', type: 'linear', description: 'Linear regression with L2 regularization', problem_type: 'regression' },
    { name: 'RandomForestRegressor', type: 'tree', description: 'Ensemble of decision trees for regression', problem_type: 'regression' },
    { name: 'XGBRegressor', type: 'boosting', description: 'XGBoost for regression', problem_type: 'regression' },
    { name: 'LGBMRegressor', type: 'boosting', description: 'LightGBM for regression', problem_type: 'regression' },
    { name: 'SVR', type: 'svm', description: 'Support Vector Regression', problem_type: 'regression' },
    { name: 'MLPRegressor', type: 'neural', description: 'Neural network for regression', problem_type: 'regression' },
    { name: 'GradientBoostingRegressor', type: 'boosting', description: 'Gradient Boosting for regression', problem_type: 'regression' },
  ],
};

const TYPE_ICONS: Record<string, typeof Brain> = {
  linear: Brain,
  tree: Network,
  boosting: Cpu,
  neural: Brain,
  svm: HardDrive,
  instance: Network,
};

const TYPE_COLORS: Record<string, string> = {
  linear: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  tree: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  boosting: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  neural: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  svm: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  instance: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
};

export function ModelsPage() {
  const [search, setSearch] = useState('');
  const [problemType, setProblemType] = useState<'all' | 'classification' | 'regression'>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');

  const allModels = Object.entries(MODEL_CATEGORIES).flatMap(([_, modelList]) => modelList);

  const filteredModels = allModels.filter((model) => {
    const matchesSearch = model.name.toLowerCase().includes(search.toLowerCase());
    const matchesProblem = problemType === 'all' || model.problem_type === problemType;
    const matchesType = typeFilter === 'all' || model.type === typeFilter;
    return matchesSearch && matchesProblem && matchesType;
  });

  const availableTypes = [...new Set(allModels.map(m => m.type))];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Available Models</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          AutoML supports a wide range of algorithms for both classification and regression tasks.
        </p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search models..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
            />
          </div>
          <select
            value={problemType}
            onChange={(e) => setProblemType(e.target.value as any)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 w-48"
          >
            <option value="all">All Problems</option>
            <option value="classification">Classification</option>
            <option value="regression">Regression</option>
          </select>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 w-48"
          >
            <option value="all">All Types</option>
            {availableTypes.map(type => (
              <option key={type} value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {filteredModels.map((model) => {
          const Icon = TYPE_ICONS[model.type] || Brain;
          return (
            <div
              key={`${model.problem_type}-${model.name}`}
              className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 hover:border-purple-300 dark:hover:border-purple-700 transition-colors"
            >
              <div className="flex items-start justify-between mb-4">
                <div className={cn('p-3 rounded-lg', TYPE_COLORS[model.type])}>
                  <Icon className="w-6 h-6" />
                </div>
                <span className="text-xs font-medium px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                  {model.problem_type}
                </span>
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">{model.name}</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-4 line-clamp-2">
                {model.description}
              </p>
              <div className="flex items-center gap-2">
                <span className={cn(
                  'px-2 py-0.5 rounded text-xs font-medium',
                  TYPE_COLORS[model.type]
                )}>
                  {model.type.charAt(0).toUpperCase() + model.type.slice(1)}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {filteredModels.length === 0 && (
        <div className="text-center py-12">
          <Filter className="w-12 h-12 mx-auto text-gray-400 mb-4" />
          <p className="text-gray-500 dark:text-gray-400">No models match your filters</p>
        </div>
      )}

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">How AutoML Selects Models</h2>
        <div className="grid gap-4 md:grid-cols-3">
          <GuideCard
            title="Problem Detection"
            description="AutoML automatically detects whether your task is classification, regression, clustering, or time series based on the target variable."
          />
          <GuideCard
            title="Model Training"
            description="All 8 models per problem type are trained from scratch with default hyperparameters on your preprocessed data."
          />
          <GuideCard
            title="Hyperparameter Optimization"
            description="Top 3 models get optimized with Optuna (50 trials) using appropriate cross-validation strategy."
          />
          <GuideCard
            title="Evaluation & Ranking"
            description="Models are evaluated on held-out test set and ranked by composite score balancing accuracy, speed, and robustness."
          />
          <GuideCard
            title="Ensemble Building"
            description="Voting, stacking, and blending ensembles are created from top models. Best ensemble replaces 3rd place if better."
          />
          <GuideCard
            title="Production Deployment"
            description="Top model is automatically packaged (Joblib + ONNX), registered in MLflow, and deployed as a live REST endpoint."
          />
        </div>
      </div>
    </div>
  );
}

function GuideCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-700">
      <h3 className="font-medium text-gray-900 dark:text-white mb-1">{title}</h3>
      <p className="text-sm text-gray-600 dark:text-gray-400">{description}</p>
    </div>
  );
}