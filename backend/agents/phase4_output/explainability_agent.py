from backend.agents.base_agent import BaseAgent
from backend.orchestrator.state import PipelineState
from backend.mlops.artifact_store import download_from_s3, upload_to_s3
import pandas as pd
import numpy as np
import io
import joblib
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    shap = None
    SHAP_AVAILABLE = False

try:
    import lime
    import lime.lime_tabular
    LIME_AVAILABLE = True
except ImportError:
    lime = None
    LIME_AVAILABLE = False
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ExplainabilityAgent(BaseAgent):
    name: str = "explainability_agent"
    phase: str = "phase4_output"

    def run(self, state: PipelineState) -> Dict[str, Any]:
        ranked_models = state.get("ranked_models", [])[:3]  # Top 3
        test_path = state.get("selected_test_path") or state["cleaned_test_path"].replace("cleaned_test", "selected_test")
        target_column = state["target_column"]
        problem_type = state["problem_type"]
        job_id = state.get("job_id", "default_job")
        
        # Load test data with fallback
        try:
            test_df = pd.read_parquet(io.BytesIO(download_from_s3(test_path)))
        except Exception:
            test_path = state["cleaned_test_path"]
            test_df = pd.read_parquet(io.BytesIO(download_from_s3(test_path)))

        X_test = test_df.drop(columns=[target_column])
        y_test = test_df[target_column]
        
        # Sample for SHAP background (100 samples)
        background = None
        if SHAP_AVAILABLE and shap is not None:
            try:
                background = shap.sample(X_test, min(100, len(X_test)))
            except Exception as e:
                logger.warning(f"Could not sample background for SHAP: {e}")
        
        shap_plots_path = {}
        lime_explanations_path = {}
        feature_importance = {}
        
        for model_info in ranked_models:
            model_name = model_info["model_name"]
            model_path = model_info.get("model_path", "")
            
            if not model_path or model_name.startswith("Ensemble"):
                continue
            
            logger.info(f"Generating explanations for {model_name}...")
            
            try:
                # Load model
                model_bytes = download_from_s3(model_path)
                pipeline = joblib.load(io.BytesIO(model_bytes))
                
                # Get model from pipeline
                model = pipeline.named_steps.get('model', pipeline) if hasattr(pipeline, 'named_steps') else pipeline
                
                # SHAP explanations
                if background is not None:
                    shap_paths = self._generate_shap_plots(model, X_test, background, model_name, problem_type, job_id)
                    shap_plots_path[model_name] = shap_paths
                
                # LIME explanations
                lime_paths = self._generate_lime_explanations(model, X_test, y_test, model_name, job_id)
                lime_explanations_path[model_name] = lime_paths
                
                # Feature importance from SHAP or fallback
                importance = self._get_shap_importance(model, X_test, model_name)
                feature_importance[model_name] = importance
                
            except Exception as e:
                logger.error(f"Failed to generate explanations for {model_name}: {e}")
        
        return {
            "shap_plots_path": shap_plots_path,
            "lime_explanations_path": lime_explanations_path,
            "feature_importance": feature_importance,
            "current_agent": self.name,
            "progress_pct": 98,
        }
    
    def _generate_shap_plots(self, model, X_test: pd.DataFrame, background: pd.DataFrame, 
                            model_name: str, problem_type: str, job_id: str = "default_job") -> Dict[str, str]:
        """Generate SHAP plots"""
        if not SHAP_AVAILABLE or shap is None or background is None:
            return {}
        paths = {}
        
        try:
            # Choose explainer based on model type
            model_type = type(model).__name__
            
            if 'RandomForest' in model_type or 'XGB' in model_type or 'LGBM' in model_type or 'GradientBoosting' in model_type:
                explainer = shap.TreeExplainer(model)
            elif 'Linear' in model_type or 'Logistic' in model_type or 'Ridge' in model_type:
                explainer = shap.LinearExplainer(model, background)
            else:
                explainer = shap.KernelExplainer(model.predict, background)
            
            # Compute SHAP values
            shap_values = explainer.shap_values(X_test)
            
            # Summary plot (beeswarm)
            fig, ax = plt.subplots(figsize=(10, 8))
            try:
                if isinstance(shap_values, list):
                    # Multiclass - use first class
                    shap.summary_plot(shap_values[0], X_test, show=False)
                else:
                    shap.summary_plot(shap_values, X_test, show=False)
                plt.tight_layout()
                paths["summary"] = self._save_plot(fig, f"{job_id}_{model_name}_shap_summary.png")
            finally:
                plt.close(fig)
            
            # Bar plot (mean |SHAP|)
            fig, ax = plt.subplots(figsize=(10, 8))
            try:
                if isinstance(shap_values, list):
                    shap.summary_plot(shap_values[0], X_test, plot_type="bar", show=False)
                else:
                    shap.summary_plot(shap_values, X_test, plot_type="bar", show=False)
                plt.tight_layout()
                paths["bar"] = self._save_plot(fig, f"{job_id}_{model_name}_shap_bar.png")
            finally:
                plt.close(fig)
            
            # Waterfall for best and worst predictions
            if hasattr(model, 'predict_proba'):
                try:
                    preds = model.predict_proba(X_test)
                    if preds.shape[1] == 2:
                        probas = preds[:, 1]
                        best_idx = int(np.argmax(probas))
                        worst_idx = int(np.argmin(probas))
                        
                        for idx, label in [(best_idx, "best"), (worst_idx, "worst")]:
                            fig, ax = plt.subplots(figsize=(10, 6))
                            try:
                                if isinstance(shap_values, list):
                                    shap.waterfall_plot(shap_values[1][idx], X_test.iloc[idx], show=False)
                                else:
                                    shap.waterfall_plot(shap_values[idx], X_test.iloc[idx], show=False)
                                plt.tight_layout()
                                paths[f"waterfall_{label}"] = self._save_plot(fig, f"{job_id}_{model_name}_shap_waterfall_{label}.png")
                            finally:
                                plt.close(fig)
                except Exception as e:
                    logger.debug(f"Could not compute waterfall plots: {e}")
            
        except Exception as e:
            logger.warning(f"SHAP plots failed for {model_name}: {e}")
        finally:
            plt.close('all')
        
        return paths
    
    def _generate_lime_explanations(self, model, X_test: pd.DataFrame, y_test: pd.Series, model_name: str, job_id: str = "default_job") -> List[str]:
        """Generate LIME explanations for 5 random samples"""
        if not LIME_AVAILABLE or lime is None:
            return []
        paths = []
        
        try:
            # Create LIME explainer
            explainer = lime.lime_tabular.LimeTabularExplainer(
                X_test.values,
                feature_names=X_test.columns.tolist(),
                class_names=['0', '1'] if hasattr(model, 'classes_') else None,
                mode='classification' if hasattr(model, 'predict_proba') else 'regression',
            )
            
            # Explain 5 random samples
            n_explain = min(5, len(X_test))
            indices = np.random.choice(len(X_test), n_explain, replace=False)
            
            for i, idx in enumerate(indices):
                try:
                    if hasattr(model, 'predict_proba'):
                        exp = explainer.explain_instance(
                            X_test.iloc[idx].values,
                            model.predict_proba,
                            num_features=10
                        )
                    else:
                        exp = explainer.explain_instance(
                            X_test.iloc[idx].values,
                            model.predict,
                            num_features=10
                        )
                    
                    # Save as HTML
                    html = exp.as_html()
                    path = upload_to_s3(html.encode(), f"explanations/{job_id}_{model_name}_lime_{i}.html")
                    paths.append(path)
                except Exception as e:
                    logger.debug(f"Failed LIME explanation for sample {i}: {e}")
                
        except Exception as e:
            logger.warning(f"LIME explanations failed for {model_name}: {e}")
        
        return paths
    
    def _get_shap_importance(self, model, X_test: pd.DataFrame, model_name: str) -> Dict[str, float]:
        """Get mean absolute SHAP values as feature importance"""
        if not SHAP_AVAILABLE or shap is None:
            if hasattr(model, 'feature_importances_'):
                return {str(col): float(x) for col, x in zip(X_test.columns, model.feature_importances_)}
            elif hasattr(model, 'coef_'):
                coef = np.abs(model.coef_)
                if coef.ndim > 1:
                    coef = np.mean(coef, axis=0)
                return {str(col): float(x) for col, x in zip(X_test.columns, coef)}
            return {str(col): float(1.0 / len(X_test.columns)) for col in X_test.columns}
            
        try:
            model_type = type(model).__name__
            sample_bg = shap.sample(X_test, min(100, len(X_test)))
            if 'RandomForest' in model_type or 'XGB' in model_type or 'LGBM' in model_type or 'GradientBoosting' in model_type:
                explainer = shap.TreeExplainer(model)
            elif 'Linear' in model_type or 'Logistic' in model_type or 'Ridge' in model_type:
                explainer = shap.LinearExplainer(model, sample_bg)
            else:
                explainer = shap.KernelExplainer(model.predict, sample_bg)
            
            shap_values = explainer.shap_values(X_test)
            
            if isinstance(shap_values, list):
                # Multiclass - average across classes
                mean_shap = np.mean([np.mean(np.abs(sv), axis=0) for sv in shap_values], axis=0)
            else:
                mean_shap = np.mean(np.abs(shap_values), axis=0)
            
            importance = {str(k): float(v) for k, v in zip(X_test.columns, mean_shap)}
            # Sort by importance
            importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
            
            return importance
            
        except Exception as e:
            logger.warning(f"SHAP importance failed for {model_name}: {e}")
            if hasattr(model, 'feature_importances_'):
                return {str(col): float(x) for col, x in zip(X_test.columns, model.feature_importances_)}
            return {}
    
    def _save_plot(self, fig, filename: str) -> str:
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        return upload_to_s3(buf.getvalue(), f"plots/{filename}")


explainability_agent = ExplainabilityAgent()