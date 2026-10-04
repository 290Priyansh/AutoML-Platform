from backend.agents.base_agent import BaseAgent
from backend.orchestrator.state import PipelineState
from backend.mlops.artifact_store import download_from_s3, upload_to_s3
from backend.mlops.mlflow_client import log_model_run
from backend.llm.router import get_llm
import pandas as pd
import numpy as np
import io
import joblib
import json
import logging
from typing import Dict, Any, List
from sklearn.ensemble import VotingClassifier, VotingRegressor, StackingClassifier, StackingRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import accuracy_score, r2_score
from sklearn.base import clone

logger = logging.getLogger(__name__)


class EnsembleAgent(BaseAgent):
    name: str = "ensemble_agent"
    phase: str = "phase3_modeling"

    def run(self, state: PipelineState) -> Dict[str, Any]:
        ranked_models = state.get("ranked_models", [])
        if not ranked_models:
            return {
                "ranked_models": [],
                "ensemble_model_path": None,
                "current_agent": self.name,
                "progress_pct": 97,
            }

        train_path = state.get("resampled_train_path") or state["cleaned_train_path"].replace("cleaned_train", "resampled_train")
        val_path = state.get("selected_val_path") or state["cleaned_val_path"].replace("cleaned_val", "selected_val")
        test_path = state.get("selected_test_path") or state["cleaned_test_path"].replace("cleaned_test", "selected_test")
        target_column = state["target_column"]
        problem_type = state["problem_type"]
        
        # Get top 3 model names
        top3_names = [m["model_name"] for m in ranked_models[:3]]
        
        # Load pipelines for top 3
        pipelines = {}
        for model_name in top3_names:
            info = state.get("trained_models", {}).get(model_name)
            if not info:
                for k, v in state.get("trained_models", {}).items():
                    if model_name in k or model_name in v.get("path", ""):
                        info = v
                        break
            if info and info.get("path"):
                try:
                    model_bytes = download_from_s3(info["path"])
                    pipelines[model_name] = joblib.load(io.BytesIO(model_bytes))
                except Exception as e:
                    logger.warning(f"Could not load pipeline for {model_name}: {e}")
        
        if len(pipelines) < 2:
            return {
                "ranked_models": ranked_models,
                "ensemble_model_path": None,
                "current_agent": self.name,
                "progress_pct": 97,
            }
        
        # Load data with fallback
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
                train_df = pd.read_parquet(io.BytesIO(download_from_s3(train_path)))

        try:
            val_df = pd.read_parquet(io.BytesIO(download_from_s3(val_path)))
        except Exception:
            val_path = state["cleaned_val_path"]
            val_df = pd.read_parquet(io.BytesIO(download_from_s3(val_path)))

        try:
            test_df = pd.read_parquet(io.BytesIO(download_from_s3(test_path)))
        except Exception:
            test_path = state["cleaned_test_path"]
            test_df = pd.read_parquet(io.BytesIO(download_from_s3(test_path)))
        
        X_train = train_df.drop(columns=[target_column])
        y_train = train_df[target_column]
        X_val = val_df.drop(columns=[target_column])
        y_val = val_df[target_column]
        X_test = test_df.drop(columns=[target_column])
        y_test = test_df[target_column]

        # Apply label encoding if present in state or fallback
        if problem_type == "classification":
            le = None
            le_path = state.get("label_encoder_path")
            if not le_path and state.get("cleaned_train_path"):
                base_dir = state["cleaned_train_path"].rsplit("/", 1)[0]
                le_path = f"{base_dir}/label_encoder.joblib"
            
            if le_path:
                try:
                    le_bytes = download_from_s3(le_path)
                    if le_bytes:
                        le = joblib.load(io.BytesIO(le_bytes))
                except Exception:
                    pass

            if le is not None:
                try:
                    if y_train.dtype == 'object' or isinstance(y_train.iloc[0], str) or not pd.api.types.is_numeric_dtype(y_train):
                        y_train = pd.Series(le.transform(y_train.astype(str)), index=y_train.index)
                        y_val = pd.Series(le.transform(y_val.astype(str)), index=y_val.index)
                        y_test = pd.Series(le.transform(y_test.astype(str)), index=y_test.index)
                except Exception as e:
                    logger.warning(f"Could not apply label encoder to targets in ensemble: {e}")

            # Fallback if y_train is still strings or non-numeric
            if y_train.dtype == 'object' or isinstance(y_train.iloc[0], str) or not pd.api.types.is_numeric_dtype(y_train):
                from sklearn.preprocessing import LabelEncoder
                le_fallback = LabelEncoder()
                y_train = pd.Series(le_fallback.fit_transform(y_train.astype(str)), index=y_train.index)
                y_val = pd.Series(le_fallback.transform(y_val.astype(str)), index=y_val.index)
                y_test = pd.Series(le_fallback.transform(y_test.astype(str)), index=y_test.index)
        
        # Get composite scores for weighting matching loaded pipelines
        pipeline_scores = []
        for name in pipelines.keys():
            matching = [m.get("composite_score", 1.0) for m in ranked_models if m.get("model_name") == name]
            pipeline_scores.append(max(float(matching[0]) if matching else 1.0, 1e-4))
        sum_scores = sum(pipeline_scores)
        weights = [s / sum_scores for s in pipeline_scores] if sum_scores > 0 else None
        
        # Use LLM to decide ensemble strategy
        ensemble_strategy = self._get_ensemble_strategy(ranked_models, problem_type, pipelines)
        
        best_ensemble_score = -float('inf')
        best_ensemble = None
        best_ensemble_name = ""
        
        # 1. Soft / Hard Voting
        if ensemble_strategy.get("use_voting", True):
            try:
                if problem_type == "classification":
                    can_soft_vote = all(hasattr(pipe, 'predict_proba') for pipe in pipelines.values())
                    voting_mode = 'soft' if can_soft_vote else 'hard'
                    try:
                        voting = VotingClassifier(
                            estimators=[(name, pipe) for name, pipe in pipelines.items()],
                            voting=voting_mode,
                            weights=weights,
                            n_jobs=1
                        )
                        voting.fit(X_train, y_train)
                    except Exception as e:
                        if voting_mode == 'soft':
                            logger.warning(f"Soft voting failed ({e}), falling back to hard voting...")
                            voting = VotingClassifier(
                                estimators=[(name, pipe) for name, pipe in pipelines.items()],
                                voting='hard',
                                weights=None,
                                n_jobs=1
                            )
                            voting.fit(X_train, y_train)
                        else:
                            raise e
                else:
                    voting = VotingRegressor(
                        estimators=[(name, pipe) for name, pipe in pipelines.items()],
                        weights=weights,
                        n_jobs=1
                    )
                    voting.fit(X_train, y_train)
                
                voting_score = voting.score(X_test, y_test)
                
                if voting_score > best_ensemble_score:
                    best_ensemble_score = voting_score
                    best_ensemble = voting
                    best_ensemble_name = "voting"
                    
            except Exception as e:
                logger.warning(f"Voting ensemble failed: {e}")
        
        # 2. Stacking
        if ensemble_strategy.get("use_stacking", True):
            try:
                final_estimator = self._resolve_estimator(ensemble_strategy.get("stacking_final_estimator"), problem_type)
                if problem_type == "classification":
                    min_class_count = int(y_train.value_counts().min()) if len(y_train.value_counts()) > 0 else 5
                    cv_splits = max(2, min(5, min_class_count))
                    if min_class_count >= 2:
                        stacking = StackingClassifier(
                            estimators=[(name, pipe) for name, pipe in pipelines.items()],
                            final_estimator=final_estimator,
                            cv=cv_splits,
                            n_jobs=1
                        )
                        stacking.fit(X_train, y_train)
                        stacking_score = stacking.score(X_test, y_test)
                        if stacking_score > best_ensemble_score:
                            best_ensemble_score = stacking_score
                            best_ensemble = stacking
                            best_ensemble_name = "stacking"
                else:
                    cv_splits = min(5, len(X_train))
                    if cv_splits >= 2:
                        stacking = StackingRegressor(
                            estimators=[(name, pipe) for name, pipe in pipelines.items()],
                            final_estimator=final_estimator,
                            cv=cv_splits,
                            n_jobs=1
                        )
                        stacking.fit(X_train, y_train)
                        stacking_score = stacking.score(X_test, y_test)
                        if stacking_score > best_ensemble_score:
                            best_ensemble_score = stacking_score
                            best_ensemble = stacking
                            best_ensemble_name = "stacking"
                    
            except Exception as e:
                logger.warning(f"Stacking ensemble failed: {e}")
        
        # 3. Blending (use val set predictions as meta-features)
        if ensemble_strategy.get("use_blending", True):
            try:
                meta_features_val = np.hstack([
                    self._extract_meta_features(pipe, X_val, problem_type)
                    for pipe in pipelines.values()
                ])
                meta_features_test = np.hstack([
                    self._extract_meta_features(pipe, X_test, problem_type)
                    for pipe in pipelines.values()
                ])
                
                meta_learner = self._resolve_estimator(ensemble_strategy.get("blending_meta_learner"), problem_type)
                
                meta_learner.fit(meta_features_val, y_val)
                blending_score = meta_learner.score(meta_features_test, y_test)
                
                if blending_score > best_ensemble_score:
                    best_ensemble_score = blending_score
                    best_ensemble = {"meta_learner": meta_learner, "base_models": pipelines}
                    best_ensemble_name = "blending"
                    
            except Exception as e:
                logger.warning(f"Blending ensemble failed: {e}")
        
        # Check if ensemble beats top-1 model
        top1_score = ranked_models[0]["metrics"].get("f1_weighted" if problem_type == "classification" else "r2", 0)
        
        ensemble_model_path = None
        updated_ranked = ranked_models.copy()
        
        if best_ensemble and best_ensemble_score > top1_score:
            logger.info(f"Ensemble ({best_ensemble_name}) beats top-1 model: {best_ensemble_score:.4f} > {top1_score:.4f}")
            
            # Save ensemble
            if best_ensemble_name in ["voting", "stacking"]:
                model_buffer = io.BytesIO()
                joblib.dump(best_ensemble, model_buffer)
                model_buffer.seek(0)
                
                base_path = f"{train_path.rsplit('/', 1)[0]}/"
                ensemble_model_path = upload_to_s3(
                    model_buffer.getvalue(),
                    f"{base_path}models/ensemble_{best_ensemble_name}.joblib"
                )
            else:
                ensemble_model_path = "blending_ensemble"
            
            # Insert ensemble into ranked models
            ensemble_entry = {
                "model_name": f"Ensemble_{best_ensemble_name}",
                "composite_score": best_ensemble_score,
                "metrics": {"ensemble_score": best_ensemble_score, "type": best_ensemble_name},
                "train_time": 0,
                "model_path": ensemble_model_path,
                "rank": 1,
            }
            
            # Re-rank all models including ensemble
            all_models = ranked_models + [ensemble_entry]
            all_models.sort(key=lambda x: x["composite_score"], reverse=True)
            
            for i, model in enumerate(all_models):
                model["rank"] = i + 1
            
            updated_ranked = all_models[:3]
        else:
            ensemble_model_path = None
        
        return {
            "ranked_models": updated_ranked,
            "ensemble_model_path": ensemble_model_path,
            "current_agent": self.name,
            "progress_pct": 97,
        }
    
    def _get_ensemble_strategy(self, ranked_models: List[Dict], problem_type: str, 
                                pipelines: Dict) -> Dict[str, Any]:
        """Use LLM to decide optimal ensemble strategy"""
        try:
            llm = get_llm(task="reasoning")
            
            model_info = [
                {
                    "name": m["model_name"],
                    "score": m["composite_score"],
                    "metrics": {k: v for k, v in m.get("metrics", {}).items() if isinstance(v, (int, float))}
                }
                for m in ranked_models[:3]
            ]
            
            prompt = f"""You are an ML ensemble expert. Decide the optimal ensemble strategy for these top models.

Problem Type: {problem_type}
Top 3 Models:
{json.dumps(model_info, indent=2)}

Available base models: {list(pipelines.keys())}

Recommend the optimal ensemble configuration. Consider:
1. Model diversity (different algorithms = better ensembles)
2. Individual model performance
3. Problem type (classification vs regression)
4. Whether models are calibrated (for voting)

Respond with JSON:
{{
  "use_voting": true/false,
  "use_stacking": true/false,
  "use_blending": true/false,
  "voting_weights": "uniform" | "performance" | "custom",
  "stacking_final_estimator": "LogisticRegression" | "RandomForest" | "XGBoost" | null,
  "blending_meta_learner": "LogisticRegression" | "Ridge" | null,
  "reasoning": "explanation"
}}"""
            
            response = llm.invoke(prompt)
            content = response.content
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(content[start:end])
                logger.info(f"LLM ensemble strategy: {result.get('reasoning', '')}")
                return result
        except Exception as e:
            logger.warning(f"LLM ensemble strategy failed: {e}")
        
        # Fallback defaults
        return {
            "use_voting": True,
            "use_stacking": True,
            "use_blending": True,
            "stacking_final_estimator": None,
            "blending_meta_learner": None,
        }

    def _resolve_estimator(self, estimator_spec: Any, problem_type: str):
        if hasattr(estimator_spec, 'fit'):
            return estimator_spec
        name_str = str(estimator_spec).lower() if estimator_spec else ""
        if problem_type == "classification":
            if "randomforest" in name_str or "rf" in name_str:
                from sklearn.ensemble import RandomForestClassifier
                return RandomForestClassifier(n_estimators=100, random_state=42)
            elif "ridge" in name_str:
                from sklearn.linear_model import RidgeClassifier
                return RidgeClassifier()
            return LogisticRegression(max_iter=1000, random_state=42)
        else:
            if "randomforest" in name_str or "rf" in name_str:
                from sklearn.ensemble import RandomForestRegressor
                return RandomForestRegressor(n_estimators=100, random_state=42)
            elif "ridge" in name_str:
                from sklearn.linear_model import Ridge
                return Ridge(alpha=1.0)
            return LinearRegression()

    def _extract_meta_features(self, pipe, X, problem_type: str) -> np.ndarray:
        if problem_type == "classification" and hasattr(pipe, 'predict_proba'):
            try:
                proba = pipe.predict_proba(X)
                if proba.ndim == 2:
                    if proba.shape[1] == 2:
                        return proba[:, 1:]
                    return proba
            except Exception:
                pass
        pred = pipe.predict(X)
        if pred.ndim == 1:
            return pred.reshape(-1, 1)
        return pred


ensemble_agent = EnsembleAgent()