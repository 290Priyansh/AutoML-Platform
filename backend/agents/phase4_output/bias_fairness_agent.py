from backend.agents.base_agent import BaseAgent
from backend.orchestrator.state import PipelineState
from backend.mlops.artifact_store import download_from_s3
from backend.llm.router import get_llm
from backend.llm.prompts.bias_analyst import build_prompt as build_bias_analyst_prompt
from backend.llm.guardrails import validate_llm_output, BiasAnalystOutput
import pandas as pd
import numpy as np
import logging
import io
import joblib
from typing import Dict, Any, List
from sklearn.metrics import accuracy_score, precision_score, recall_score

logger = logging.getLogger(__name__)

try:
    from fairlearn.metrics import MetricFrame, demographic_parity_difference, equalized_odds_difference
    FAIRLEARN_AVAILABLE = True
except ImportError:
    FAIRLEARN_AVAILABLE = False
    logger.warning("fairlearn not available, bias detection limited")


class BiasFairnessAgent(BaseAgent):
    name: str = "bias_fairness_agent"
    phase: str = "phase4_output"

    # Sensitive attribute patterns
    SENSITIVE_PATTERNS = [
        'gender', 'sex', 'race', 'ethnicity', 'ethnic',
        'age', 'nationality', 'religion', 'religious',
        'disability', 'veteran', 'marital', 'sexual_orientation'
    ]

    def run(self, state: PipelineState) -> Dict[str, Any]:
        ranked_models = state.get("ranked_models", [])[:3]
        if not ranked_models:
            return {
                "bias_report": {
                    "sensitive_columns_found": False,
                    "message": "No ranked models available for fairness evaluation.",
                    "sensitive_columns": [],
                    "fairness_metrics": {},
                    "recommendations": [],
                    "narrative": "No ranked models available for fairness evaluation.",
                },
                "current_agent": self.name,
                "progress_pct": 99,
            }

        test_path = state.get("selected_test_path") or state["cleaned_test_path"].replace("cleaned_test", "selected_test")
        target_column = state["target_column"]
        feature_importance = state.get("feature_importance", {})
        
        # Load test data
        try:
            test_bytes = download_from_s3(test_path)
            test_df = pd.read_parquet(io.BytesIO(test_bytes))
        except Exception:
            test_path = state["cleaned_test_path"]
            test_bytes = download_from_s3(test_path)
            test_df = pd.read_parquet(io.BytesIO(test_bytes))
        
        # Detect sensitive columns
        sensitive_columns = self._detect_sensitive_columns(test_df.columns)
        if not sensitive_columns and test_path != state.get("cleaned_test_path"):
            try:
                cleaned_bytes = download_from_s3(state["cleaned_test_path"])
                cleaned_test_df = pd.read_parquet(io.BytesIO(cleaned_bytes))
                extra_sensitive = self._detect_sensitive_columns(cleaned_test_df.columns)
                for col in extra_sensitive:
                    test_df[col] = cleaned_test_df[col].values
                sensitive_columns = extra_sensitive
            except Exception as e:
                logger.debug(f"Could not load sensitive columns from cleaned_test: {e}")
        
        if not sensitive_columns or not FAIRLEARN_AVAILABLE:
            return {
                "bias_report": {
                    "sensitive_columns_found": False,
                    "message": "No demographic columns detected or fairlearn not available.",
                    "sensitive_columns": [],
                    "fairness_metrics": {},
                    "recommendations": [],
                    "narrative": "No sensitive attributes detected in the dataset.",
                },
                "current_agent": self.name,
                "progress_pct": 99,
            }
        
        # Compute fairness metrics for each sensitive column
        fairness_results = {}
        
        for sensitive_col in sensitive_columns:
            if sensitive_col not in test_df.columns:
                continue
            
            # Get predictions from top model
            top_model_name = ranked_models[0]["model_name"]
            top_model_path = ranked_models[0].get("model_path", "")
            
            if not top_model_path:
                continue
            
            try:
                model_bytes = download_from_s3(top_model_path)
                pipeline = joblib.load(io.BytesIO(model_bytes))
                
                if hasattr(pipeline, "feature_names_in_"):
                    eval_cols = [c for c in pipeline.feature_names_in_ if c in test_df.columns]
                    X_test = test_df[eval_cols]
                else:
                    drop_cols = [target_column]
                    if sensitive_col in test_df.columns and sensitive_col not in state.get("selected_features", []):
                        drop_cols.append(sensitive_col)
                    X_test = test_df.drop(columns=[c for c in drop_cols if c in test_df.columns])
                    
                y_test = test_df[target_column]
                sensitive_features = test_df[sensitive_col]

                # Apply label encoding if present in state or fallback
                if state.get("problem_type") == "classification":
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
                            logger.warning(f"Could not apply label encoder in bias check: {e}")
                    if y_test.dtype == 'object' or isinstance(y_test.iloc[0], str) or not pd.api.types.is_numeric_dtype(y_test):
                        from sklearn.preprocessing import LabelEncoder
                        le_fallback = LabelEncoder()
                        y_test = pd.Series(le_fallback.fit_transform(y_test.astype(str)), index=y_test.index)
                
                y_pred = pipeline.predict(X_test)
                
                # Compute fairness metrics
                metrics = self._compute_fairness_metrics(y_test, y_pred, sensitive_features)
                fairness_results[sensitive_col] = metrics
                
            except Exception as e:
                logger.warning(f"Fairness computation failed for {sensitive_col}: {e}")
        
        # Generate narrative using LLM
        narrative = ""
        recommendations = []
        if fairness_results:
            try:
                llm = get_llm()
                # Get feature importance for top model
                top_fi = feature_importance.get(top_model_name, {})
                
                prompt = build_bias_analyst_prompt({
                    "fairness_metrics": fairness_results,
                    "feature_importances": top_fi,
                    "sensitive_columns": sensitive_columns,
                    "problem_type": state["problem_type"],
                })
                
                response = llm.invoke(prompt)
                content = response.content if hasattr(response, 'content') else str(response)
                llm_output = validate_llm_output(content, BiasAnalystOutput)
                
                narrative = llm_output.narrative
                recommendations = llm_output.recommendations
                
            except Exception as e:
                logger.warning(f"LLM bias narrative failed: {e}")
                narrative = "Bias analysis completed. See fairness metrics for details."
                recommendations = ["Review fairness metrics for each sensitive attribute", "Consider bias mitigation techniques if disparities found"]
        
        bias_report = {
            "sensitive_columns_found": True,
            "sensitive_columns": sensitive_columns,
            "fairness_metrics": fairness_results,
            "recommendations": recommendations,
            "narrative": narrative,
        }
        
        return {
            "bias_report": bias_report,
            "current_agent": self.name,
            "progress_pct": 99,
        }
    
    def _detect_sensitive_columns(self, columns: List[str]) -> List[str]:
        """Auto-detect sensitive attribute columns"""
        detected = []
        for col in columns:
            col_lower = str(col).lower()
            for pattern in self.SENSITIVE_PATTERNS:
                if pattern in col_lower:
                    detected.append(col)
                    break
        return detected
    
    def _compute_fairness_metrics(self, y_true, y_pred, sensitive_features) -> Dict[str, Any]:
        """Compute fairness metrics using fairlearn"""
        try:
            import json
            # MetricFrame for per-group metrics
            metric_frame = MetricFrame(
                metrics={
                    'accuracy': accuracy_score,
                    'precision': lambda y_t, y_p: precision_score(y_t, y_p, average='weighted', zero_division=0),
                    'recall': lambda y_t, y_p: recall_score(y_t, y_p, average='weighted', zero_division=0),
                },
                y_true=y_true,
                y_pred=y_pred,
                sensitive_features=sensitive_features
            )
            
            # Overall fairness metrics
            dp_diff = demographic_parity_difference(y_true, y_pred, sensitive_features=sensitive_features)
            eo_diff = equalized_odds_difference(y_true, y_pred, sensitive_features=sensitive_features)
            
            # Convert metric frame results to clean, JSON-serializable dictionaries
            by_group_dict = json.loads(json.dumps(metric_frame.by_group.to_dict(), default=str))
            overall_dict = json.loads(json.dumps(metric_frame.overall.to_dict(), default=str))
            
            return {
                "demographic_parity_difference": float(dp_diff),
                "equalized_odds_difference": float(eo_diff),
                "per_group_metrics": by_group_dict,
                "overall_metrics": overall_dict,
            }
        except Exception as e:
            logger.warning(f"Fairness metric computation failed: {e}")
            return {"error": str(e)}


bias_fairness_agent = BiasFairnessAgent()