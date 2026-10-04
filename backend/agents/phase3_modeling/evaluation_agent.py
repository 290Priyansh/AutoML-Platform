from backend.agents.base_agent import BaseAgent
from backend.orchestrator.state import PipelineState
from backend.mlops.artifact_store import download_from_s3, upload_to_s3
from backend.mlops.mlflow_client import log_model_run
import pandas as pd
import numpy as np
import io
import joblib
import logging
from typing import Dict, Any
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
    cohen_kappa_score, matthews_corrcoef,
    mean_squared_error, mean_absolute_error, r2_score,
    mean_absolute_percentage_error
)
from sklearn.metrics import RocCurveDisplay, PrecisionRecallDisplay
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)


class EvaluationAgent(BaseAgent):
    name: str = "evaluation_agent"
    phase: str = "phase3_modeling"

    def run(self, state: PipelineState) -> Dict[str, Any]:
        trained_models = state["trained_models"]
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

        # Decode or transform categorical labels if label encoder was saved during training
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
                    if y_test.dtype == 'object' or isinstance(y_test.iloc[0], str) or not pd.api.types.is_numeric_dtype(y_test):
                        y_test = pd.Series(le.transform(y_test.astype(str)), index=y_test.index)
                except Exception as e:
                    logger.warning(f"Could not apply label encoder to y_test: {e}")

            # Fallback if y_test is still strings or non-numeric
            if y_test.dtype == 'object' or isinstance(y_test.iloc[0], str) or not pd.api.types.is_numeric_dtype(y_test):
                from sklearn.preprocessing import LabelEncoder
                le_fallback = LabelEncoder()
                y_test = pd.Series(le_fallback.fit_transform(y_test.astype(str)), index=y_test.index)
        
        evaluation_results = {}
        
        for model_name, model_info in trained_models.items():
            if not model_info.get("path") or model_info.get("error"):
                continue
            
            logger.info(f"Evaluating {model_name} on test set...")
            
            try:
                # Load model
                model_bytes = download_from_s3(model_info["path"])
                pipeline = joblib.load(io.BytesIO(model_bytes))
                
                # Predict
                y_pred = pipeline.predict(X_test)
                
                if problem_type == "classification":
                    metrics = self._evaluate_classification(pipeline, X_test, y_test, y_pred, model_name)
                else:
                    metrics = self._evaluate_regression(X_test, y_test, y_pred, model_name)
                
                # Save plots
                plot_paths = self._save_plots(pipeline, X_test, y_test, y_pred, model_name, problem_type, job_id)
                metrics["plot_paths"] = plot_paths
                
                evaluation_results[model_name] = metrics
                
                # Log to MLflow
                model_obj = pipeline.named_steps.get('model', pipeline) if hasattr(pipeline, 'named_steps') else pipeline
                preprocessor = pipeline.named_steps.get('preprocessor') if hasattr(pipeline, 'named_steps') else None
                log_model_run(
                    job_id=state["job_id"],
                    model_name=model_name,
                    params=model_info.get("params", {}),
                    metrics={k: v for k, v in metrics.items() if isinstance(v, (int, float))},
                    model_obj=model_obj,
                    preprocessor=preprocessor,
                )
                
            except Exception as e:
                logger.error(f"Failed to evaluate {model_name}: {e}")
                evaluation_results[model_name] = {"error": str(e)}
        
        return {
            "evaluation_results": evaluation_results,
            "current_agent": self.name,
            "progress_pct": 94,
        }
    
    def _evaluate_classification(self, pipeline, X_test, y_test, y_pred, model_name: str) -> Dict[str, Any]:
        metrics = {}
        
        # Basic metrics
        metrics["accuracy"] = float(accuracy_score(y_test, y_pred))
        metrics["precision_macro"] = float(precision_score(y_test, y_pred, average='macro', zero_division=0))
        metrics["precision_weighted"] = float(precision_score(y_test, y_pred, average='weighted', zero_division=0))
        metrics["recall_macro"] = float(recall_score(y_test, y_pred, average='macro', zero_division=0))
        metrics["recall_weighted"] = float(recall_score(y_test, y_pred, average='weighted', zero_division=0))
        metrics["f1_macro"] = float(f1_score(y_test, y_pred, average='macro', zero_division=0))
        metrics["f1_weighted"] = float(f1_score(y_test, y_pred, average='weighted', zero_division=0))
        try:
            metrics["cohen_kappa"] = float(cohen_kappa_score(y_test, y_pred))
        except Exception:
            metrics["cohen_kappa"] = 0.0
        try:
            metrics["matthews_corrcoef"] = float(matthews_corrcoef(y_test, y_pred))
        except Exception:
            metrics["matthews_corrcoef"] = 0.0
        
        # Probabilistic metrics
        if hasattr(pipeline, 'predict_proba'):
            try:
                y_proba = pipeline.predict_proba(X_test)
                if y_proba.shape[1] == 2:
                    # Binary
                    if len(np.unique(y_test)) == 2:
                        metrics["roc_auc"] = float(roc_auc_score(y_test, y_proba[:, 1]))
                        metrics["pr_auc"] = float(average_precision_score(y_test, y_proba[:, 1]))
                else:
                    # Multiclass
                    if len(np.unique(y_test)) == y_proba.shape[1]:
                        metrics["roc_auc_ovr"] = float(roc_auc_score(y_test, y_proba, multi_class='ovr'))
                        metrics["roc_auc_ovo"] = float(roc_auc_score(y_test, y_proba, multi_class='ovo'))
            except Exception as e:
                logger.warning(f"Could not compute probabilistic metrics for {model_name}: {e}")
        
        return metrics
    
    def _evaluate_regression(self, X_test, y_test, y_pred, model_name: str) -> Dict[str, Any]:
        metrics = {}
        
        metrics["rmse"] = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        metrics["mae"] = float(mean_absolute_error(y_test, y_pred))
        metrics["mse"] = float(mean_squared_error(y_test, y_pred))
        metrics["r2"] = float(r2_score(y_test, y_pred))
        
        # Adjusted R²
        n = len(y_test)
        p = X_test.shape[1]
        if (n - p - 1) > 0:
            metrics["adjusted_r2"] = float(1 - (1 - metrics["r2"]) * (n - 1) / (n - p - 1))
        else:
            metrics["adjusted_r2"] = metrics["r2"]
        
        try:
            metrics["mape"] = float(mean_absolute_percentage_error(y_test, y_pred))
        except Exception:
            metrics["mape"] = 0.0
        
        return metrics
    
    def _save_plots(self, pipeline, X_test, y_test, y_pred, model_name: str, problem_type: str, job_id: str) -> Dict[str, str]:
        plot_paths = {}
        base_name = f"{job_id}_{model_name}_{problem_type}"
        
        try:
            if problem_type == "classification":
                # Confusion matrix
                fig, ax = plt.subplots(figsize=(8, 6))
                try:
                    cm = confusion_matrix(y_test, y_pred)
                    sns.heatmap(cm, annot=True, fmt='d', ax=ax)
                    ax.set_title(f'Confusion Matrix - {model_name}')
                    cm_path = self._save_plot(fig, f"{base_name}_confusion_matrix.png")
                    plot_paths["confusion_matrix"] = cm_path
                finally:
                    plt.close(fig)
                
                # ROC curve (if binary)
                if hasattr(pipeline, 'predict_proba'):
                    try:
                        y_proba = pipeline.predict_proba(X_test)
                        if y_proba.shape[1] == 2 and len(np.unique(y_test)) == 2:
                            fig, ax = plt.subplots(figsize=(8, 6))
                            try:
                                RocCurveDisplay.from_predictions(y_test, y_proba[:, 1], ax=ax)
                                ax.set_title(f'ROC Curve - {model_name}')
                                roc_path = self._save_plot(fig, f"{base_name}_roc_curve.png")
                                plot_paths["roc_curve"] = roc_path
                            finally:
                                plt.close(fig)
                            
                            # PR curve
                            fig, ax = plt.subplots(figsize=(8, 6))
                            try:
                                PrecisionRecallDisplay.from_predictions(y_test, y_proba[:, 1], ax=ax)
                                ax.set_title(f'Precision-Recall Curve - {model_name}')
                                pr_path = self._save_plot(fig, f"{base_name}_pr_curve.png")
                                plot_paths["pr_curve"] = pr_path
                            finally:
                                plt.close(fig)
                    except Exception as e:
                        logger.warning(f"Could not generate ROC/PR plots for {model_name}: {e}")
            
            else:
                # Residuals plot
                fig, ax = plt.subplots(figsize=(8, 6))
                try:
                    residuals = y_test - y_pred
                    ax.scatter(y_pred, residuals, alpha=0.5)
                    ax.axhline(y=0, color='r', linestyle='--')
                    ax.set_xlabel('Predicted')
                    ax.set_ylabel('Residuals')
                    ax.set_title(f'Residuals Plot - {model_name}')
                    res_path = self._save_plot(fig, f"{base_name}_residuals.png")
                    plot_paths["residuals"] = res_path
                finally:
                    plt.close(fig)
                
                # Residuals histogram
                fig, ax = plt.subplots(figsize=(8, 6))
                try:
                    residuals = y_test - y_pred
                    ax.hist(residuals, bins=30, edgecolor='black')
                    ax.set_title(f'Residuals Histogram - {model_name}')
                    hist_path = self._save_plot(fig, f"{base_name}_residuals_hist.png")
                    plot_paths["residuals_hist"] = hist_path
                finally:
                    plt.close(fig)
                
        except Exception as e:
            logger.warning(f"Could not save plots for {model_name}: {e}")
        finally:
            plt.close('all')
        
        return plot_paths
    
    def _save_plot(self, fig, filename: str) -> str:
        """Save plot to S3 and return path"""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        return upload_to_s3(buf.getvalue(), f"plots/{filename}")


evaluation_agent = EvaluationAgent()