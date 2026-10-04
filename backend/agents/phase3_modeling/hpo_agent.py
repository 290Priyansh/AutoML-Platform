from backend.agents.base_agent import BaseAgent
from backend.orchestrator.state import PipelineState
from backend.mlops.artifact_store import download_from_s3, upload_to_s3
from backend.mlops.mlflow_client import log_model_run
from backend.monitoring.prometheus import MODEL_TRAIN_DURATION
from backend.llm.router import get_llm
from backend.llm.guardrails import validate_llm_output, HPOWarmStartOutput
from backend.config import settings
import pandas as pd
import numpy as np
import io
import joblib
try:
    import optuna
    OPTUNA_AVAILABLE = True
except ImportError:
    optuna = None
    OPTUNA_AVAILABLE = False
import time
import logging
from typing import Dict, Any, List
from sklearn.model_selection import cross_val_score, StratifiedKFold, KFold, TimeSeriesSplit, GroupKFold
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)


class HPOAgent(BaseAgent):
    name: str = "hpo_agent"
    phase: str = "phase3_modeling"

    # Search spaces for different models
    SEARCH_SPACES = {
        "RandomForestClassifier": {
            "model__n_estimators": ("int", 50, 500),
            "model__max_depth": ("int_none", 3, 20),
            "model__min_samples_split": ("int", 2, 20),
            "model__min_samples_leaf": ("int", 1, 10),
            "model__max_features": ("categorical", ["sqrt", "log2", None]),
        },
        "XGBClassifier": {
            "model__n_estimators": ("int", 50, 500),
            "model__max_depth": ("int", 3, 10),
            "model__learning_rate": ("float_log", 1e-3, 0.3),
            "model__subsample": ("float", 0.5, 1.0),
            "model__colsample_bytree": ("float", 0.5, 1.0),
            "model__reg_alpha": ("float_log", 1e-5, 10.0),
            "model__reg_lambda": ("float_log", 1e-5, 10.0),
        },
        "LGBMClassifier": {
            "model__n_estimators": ("int", 50, 500),
            "model__num_leaves": ("int", 20, 300),
            "model__learning_rate": ("float_log", 1e-3, 0.3),
            "model__min_child_samples": ("int", 5, 100),
            "model__feature_fraction": ("float", 0.5, 1.0),
            "model__bagging_fraction": ("float", 0.5, 1.0),
        },
        "RandomForestRegressor": {
            "model__n_estimators": ("int", 50, 500),
            "model__max_depth": ("int_none", 3, 20),
            "model__min_samples_split": ("int", 2, 20),
            "model__min_samples_leaf": ("int", 1, 10),
            "model__max_features": ("categorical", ["sqrt", "log2", None]),
        },
        "XGBRegressor": {
            "model__n_estimators": ("int", 50, 500),
            "model__max_depth": ("int", 3, 10),
            "model__learning_rate": ("float_log", 1e-3, 0.3),
            "model__subsample": ("float", 0.5, 1.0),
            "model__colsample_bytree": ("float", 0.5, 1.0),
            "model__reg_alpha": ("float_log", 1e-5, 10.0),
            "model__reg_lambda": ("float_log", 1e-5, 10.0),
        },
        "LGBMRegressor": {
            "model__n_estimators": ("int", 50, 500),
            "model__num_leaves": ("int", 20, 300),
            "model__learning_rate": ("float_log", 1e-3, 0.3),
            "model__min_child_samples": ("int", 5, 100),
            "model__feature_fraction": ("float", 0.5, 1.0),
            "model__bagging_fraction": ("float", 0.5, 1.0),
        },
        "LogisticRegression": {
            "model__C": ("float_log", 1e-4, 1e2),
            "model__penalty": ("categorical", ["l1", "l2"]),
            "model__solver": ("categorical", ["liblinear", "saga"]),
        },
        "Ridge": {
            "model__alpha": ("float_log", 1e-4, 1e2),
        },
        "SVR": {
            "model__C": ("float_log", 1e-2, 1e2),
            "model__gamma": ("float_log", 1e-4, 1e1),
            "model__kernel": ("categorical", ["rbf", "linear"]),
        },
    }

    def run(self, state: PipelineState) -> Dict[str, Any]:
        trained_models = state["trained_models"]
        cv_strategy = state["cv_strategy"]
        problem_type = state["problem_type"]
        train_path = state.get("resampled_train_path") or state["cleaned_train_path"].replace("cleaned_train", "resampled_train")
        target_column = state["target_column"]
        
        if not OPTUNA_AVAILABLE or optuna is None:
            logger.warning("Optuna is not available, skipping HPO tuning.")
            return {
                "hpo_results": {},
                "trained_models": trained_models,
                "current_agent": self.name,
                "progress_pct": 92,
            }
        
        # Load training data with fallback
        try:
            train_bytes = download_from_s3(train_path)
            train_df = pd.read_parquet(io.BytesIO(train_bytes))
        except Exception:
            try:
                train_path = state.get("selected_train_path") or state["cleaned_train_path"].replace("cleaned_train", "selected_train")
                train_bytes = download_from_s3(train_path)
                train_df = pd.read_parquet(io.BytesIO(train_bytes))
            except Exception:
                train_path = state["cleaned_train_path"]
                train_bytes = download_from_s3(train_path)
                train_df = pd.read_parquet(io.BytesIO(train_bytes))
        
        X_train = train_df.drop(columns=[target_column])
        y_train = train_df[target_column]
        
        # Select top 3 models by validation score
        # Select top 3 valid models by validation score
        valid_models = [(name, info) for name, info in trained_models.items() if info.get("path") and not info.get("error")]
        sorted_models = sorted(
            valid_models,
            key=lambda x: x[1].get("val_score", -999.0),
            reverse=True
        )
        top_models = sorted_models[:3]
        
        hpo_results = {}
        updated_models = trained_models.copy()
        
        for model_name, model_info in top_models:
            logger.info(f"Running HPO for {model_name}...")
            
            # Load base pipeline
            model_bytes = download_from_s3(model_info["path"])
            base_pipeline = joblib.load(io.BytesIO(model_bytes))
            
            # Get search space
            search_space = self.SEARCH_SPACES.get(model_name, {})
            if not search_space:
                logger.warning(f"No search space defined for {model_name}, skipping HPO")
                continue
            
            # Get CV splitter
            cv = self._get_cv_splitter(cv_strategy, train_df, target_column, problem_type)
            
            # Get warm start from LLM
            warm_start = self._get_warm_start(model_name, train_df.shape, problem_type)
            
            # Run Optuna study
            study = optuna.create_study(
                direction="maximize",
                pruner=optuna.pruners.MedianPruner(n_warmup_steps=5),
            )
            
            # Add warm start as first trial if available and valid
            if warm_start and isinstance(warm_start, dict):
                valid_warm = {k: v for k, v in warm_start.items() if k in search_space}
                if valid_warm:
                    try:
                        study.enqueue_trial(valid_warm)
                    except Exception as e:
                        logger.debug(f"Could not enqueue warm start: {e}")
            
            def objective(trial):
                params = {}
                for param_name, param_config in search_space.items():
                    param_type = param_config[0]
                    if param_type == "int":
                        params[param_name] = trial.suggest_int(param_name, param_config[1], param_config[2])
                    elif param_type == "int_none":
                        use_param = trial.suggest_categorical(f"{param_name}_use", [True, False])
                        params[param_name] = trial.suggest_int(param_name, param_config[1], param_config[2]) if use_param else None
                    elif param_type == "float":
                        params[param_name] = trial.suggest_float(param_name, param_config[1], param_config[2])
                    elif param_type == "float_log":
                        params[param_name] = trial.suggest_float(param_name, param_config[1], param_config[2], log=True)
                    elif param_type == "categorical":
                        params[param_name] = trial.suggest_categorical(param_name, param_config[1])
                
                # Clone pipeline to avoid mutating base in place
                pipeline = clone(base_pipeline)
                pipeline.set_params(**params)
                
                # Cross-validation score
                scoring = 'accuracy' if problem_type == 'classification' else 'r2'
                scores = cross_val_score(pipeline, X_train, y_train, cv=cv, n_jobs=1, scoring=scoring)
                mean_score = float(np.mean(scores))
                return mean_score if not np.isnan(mean_score) else float("-inf")
            
            # Run optimization with exception catching
            n_trials = getattr(settings, "OPTUNA_N_TRIALS", 10)
            timeout = getattr(settings, "OPTUNA_TIMEOUT_SECONDS", 30)
            try:
                study.optimize(objective, n_trials=n_trials, timeout=timeout, n_jobs=1, catch=(Exception,))
            except Exception as opt_err:
                logger.warning(f"Optuna optimize error for {model_name}: {opt_err}")
            
            if not study.trials or len(study.trials) == 0:
                logger.warning(f"No successful trials for {model_name}")
                continue

            best_score = study.best_value
            
            # Clean best_params: Optuna best_params contains `{param}_use` keys which crash set_params
            clean_best_params = {}
            for param_name, param_config in search_space.items():
                param_type = param_config[0]
                if param_type == "int_none":
                    use_key = f"{param_name}_use"
                    if not study.best_params.get(use_key, True):
                        clean_best_params[param_name] = None
                    elif param_name in study.best_params:
                        clean_best_params[param_name] = study.best_params[param_name]
                elif param_name in study.best_params:
                    clean_best_params[param_name] = study.best_params[param_name]
            
            # Retrain with clean best params on full training set
            best_pipeline = clone(base_pipeline)
            best_pipeline.set_params(**clean_best_params)
            best_pipeline.fit(X_train, y_train)
            
            # Save tuned model
            model_buffer = io.BytesIO()
            joblib.dump(best_pipeline, model_buffer)
            model_buffer.seek(0)
            
            base_path = f"{train_path.rsplit('/', 1)[0]}/"
            tuned_path = upload_to_s3(model_buffer.getvalue(), f"{base_path}models/{model_name}_tuned.joblib")
            
            hpo_results[model_name] = {
                "best_params": clean_best_params,
                "best_cv_score": float(best_score),
                "n_trials": len(study.trials),
            }
            
            updated_models[model_name] = {
                **model_info,
                "path": tuned_path,
                "params": clean_best_params,
                "val_score": float(best_score),
            }
            
            logger.info(f"{model_name} HPO complete: best_score={best_score:.4f}")
        
        return {
            "hpo_results": hpo_results,
            "trained_models": updated_models,
            "current_agent": self.name,
            "progress_pct": 92,
        }
    
    def _get_cv_splitter(self, cv_strategy: str, train_df: pd.DataFrame, target_column: str = None, problem_type: str = "classification"):
        """Get appropriate CV splitter"""
        n_splits = 5
        
        if problem_type == "classification" and target_column and target_column in train_df.columns:
            min_class_samples = train_df[target_column].value_counts().min()
            if min_class_samples < n_splits:
                n_splits = max(2, int(min_class_samples))
        
        if problem_type != "classification" and "Stratified" in cv_strategy:
            return KFold(n_splits=n_splits, shuffle=True, random_state=42)
            
        if cv_strategy in ["StratifiedKFold", "StratifiedKFold_shuffled"]:
            return StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        elif cv_strategy == "KFold":
            return KFold(n_splits=n_splits, shuffle=True, random_state=42)
        elif cv_strategy == "TimeSeriesSplit":
            return TimeSeriesSplit(n_splits=n_splits)
        elif cv_strategy == "GroupKFold":
            return KFold(n_splits=n_splits, shuffle=True, random_state=42)
        else:
            return KFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    def _get_warm_start(self, model_name: str, data_shape: tuple, problem_type: str) -> Dict[str, Any]:
        """Get warm start parameters from fine-tuned LLM"""
        try:
            llm = get_llm()
            from backend.llm.prompts.hpo_warmstart import build_prompt
            prompt = build_prompt({
                "model_name": model_name,
                "n_samples": data_shape[0],
                "n_features": data_shape[1],
                "problem_type": problem_type,
            })
            response = llm.invoke(prompt)
            warm_start = validate_llm_output(response.content, HPOWarmStartOutput)
            return warm_start.suggested_params
        except Exception as e:
            logger.warning(f"LLM warm start failed for {model_name}: {e}")
            return {}


hpo_agent = HPOAgent()