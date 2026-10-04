import { useState } from 'react';
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

export function ModelsPage() {
  const [search, setSearch] = useState('');
  const [problemType, setProblemType] = useState<'all' | 'classification' | 'regression'>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');

  const allModels = Object.values(MODEL_CATEGORIES).flat();

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
        <h1 className="text-2xl sm:text-3xl font-serif font-normal text-[var(--text)] tracking-tight">Available Models</h1>
        <p className="text-xs text-[var(--text-muted)] mt-1">
          AutoML supports a wide range of algorithms for both classification and regression tasks.
        </p>
      </div>

      <div className="surface-card squircle-lg p-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
            <input
              type="text"
              placeholder="Search models..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full h-10 pl-9 pr-4 border border-[var(--border)] squircle-sm bg-[var(--surface)] text-[var(--text)] text-xs placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] transition-all"
            />
          </div>
          <select
            value={problemType}
            onChange={(e) => setProblemType(e.target.value as any)}
            className="h-10 px-3.5 border border-[var(--border)] squircle-sm bg-[var(--surface)] text-[var(--text)] text-xs focus:outline-none focus:ring-2 focus:ring-[var(--accent)] sm:w-44 cursor-pointer"
          >
            <option value="all">All Problems</option>
            <option value="classification">Classification</option>
            <option value="regression">Regression</option>
          </select>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="h-10 px-3.5 border border-[var(--border)] squircle-sm bg-[var(--surface)] text-[var(--text)] text-xs focus:outline-none focus:ring-2 focus:ring-[var(--accent)] sm:w-44 cursor-pointer"
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
              className="surface-card squircle-lg p-5 flex flex-col justify-between hover:border-[var(--text-muted)] transition-colors"
            >
              <div>
                <div className="flex items-start justify-between mb-3">
                  <div className="w-8 h-8 squircle-sm bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--text-muted)]">
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className="text-[11px] font-mono text-[var(--text-muted)] bg-[var(--surface-2)] px-2 py-0.5 squircle-sm border border-[var(--border)]">
                    {model.problem_type}
                  </span>
                </div>
                <h3 className="font-semibold text-sm text-[var(--text)] mb-1.5">{model.name}</h3>
                <p className="text-xs text-[var(--text-muted)] mb-4 line-clamp-2 leading-relaxed">
                  {model.description}
                </p>
              </div>
              <div className="flex items-center gap-2 pt-2 border-t border-[var(--border)]">
                <span className="text-[11px] font-mono text-[var(--text-muted)]">
                  {model.type.charAt(0).toUpperCase() + model.type.slice(1)}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {filteredModels.length === 0 && (
        <div className="text-center py-12 surface-card squircle-lg">
          <Filter className="w-8 h-8 mx-auto text-[var(--text-muted)] mb-3" />
          <p className="text-xs text-[var(--text-muted)]">No models match your filters</p>
        </div>
      )}

      <div className="surface-card squircle-lg p-6">
        <h2 className="text-sm font-semibold text-[var(--text)] mb-4">How AutoML Selects Models</h2>
        <div className="grid gap-3 md:grid-cols-3">
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
    <div className="p-3.5 bg-[var(--surface-2)] squircle-md border border-[var(--border)]">
      <h3 className="text-xs font-semibold text-[var(--text)] mb-1">{title}</h3>
      <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">{description}</p>
    </div>
  );
}