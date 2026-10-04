from backend.agents.base_agent import BaseAgent
from backend.orchestrator.state import PipelineState
from backend.mlops.artifact_store import download_from_s3
from backend.llm.router import get_llm
from backend.llm.prompts.ranking_rationale import build_prompt as build_ranking_rationale_prompt
from backend.llm.guardrails import validate_llm_output, RankingRationaleOutput
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class RankingAgent(BaseAgent):
    name: str = "ranking_agent"
    phase: str = "phase3_modeling"

    def run(self, state: PipelineState) -> Dict[str, Any]:
        evaluation_results = state.get("evaluation_results", {})
        trained_models = state.get("trained_models", {})
        problem_type = state.get("problem_type", "classification")
        
        # Calculate dynamic normalization bounds
        all_rmses = [res["rmse"] for res in evaluation_results.values() if isinstance(res, dict) and "rmse" in res and not np.isnan(res["rmse"])]
        max_rmse = max(all_rmses) if all_rmses and max(all_rmses) > 0 else 1.0
        all_maes = [res["mae"] for res in evaluation_results.values() if isinstance(res, dict) and "mae" in res and not np.isnan(res["mae"])]
        max_mae = max(all_maes) if all_maes and max(all_maes) > 0 else 1.0
        all_times = [trained_models.get(m, {}).get("train_time", 0) for m in evaluation_results.keys()]
        max_time = max(all_times) if all_times and max(all_times) > 0 else 300.0

        # Calculate composite scores
        ranked_models = []
        
        for model_name, eval_results in evaluation_results.items():
            if not isinstance(eval_results, dict) or "error" in eval_results:
                continue
            
            train_time = trained_models.get(model_name, {}).get("train_time", 0)
            
            if problem_type == "classification":
                composite = self._classification_composite(eval_results, train_time, max_time)
            else:
                composite = self._regression_composite(eval_results, train_time, max_rmse, max_mae, max_time)
            
            ranked_models.append({
                "model_name": model_name,
                "composite_score": composite,
                "metrics": eval_results,
                "train_time": train_time,
                "model_path": trained_models.get(model_name, {}).get("path", ""),
            })
        
        # Sort by composite score descending
        ranked_models.sort(key=lambda x: x["composite_score"], reverse=True)
        
        # Add rank
        for i, model in enumerate(ranked_models):
            model["rank"] = i + 1
        
        # Get top 3
        top3 = ranked_models[:3]
        
        # Generate ranking rationale for top model using LLM
        ranking_rationale = ""
        if top3:
            ranking_rationale = self._generate_ranking_rationale(top3[0], ranked_models, problem_type)
        
        return {
            "ranked_models": ranked_models,
            "ranking_rationale": ranking_rationale,
            "current_agent": self.name,
            "progress_pct": 96,
        }
    
    def _classification_composite(self, metrics: Dict[str, float], train_time: float, max_time: float = 300.0) -> float:
        """Composite score for classification:
        0.4 * F1_weighted + 0.3 * AUC_ROC + 0.2 * Precision_weighted + 0.1 * (1 - Normalized_Training_Time)"""
        
        f1_weighted = max(float(metrics.get("f1_weighted", 0.0)), 0.0)
        auc_roc = max(float(metrics.get("roc_auc", metrics.get("roc_auc_ovr", 0.0))), 0.0)
        precision_weighted = max(float(metrics.get("precision_weighted", 0.0)), 0.0)
        
        norm_time = min(train_time / max(max_time, 1.0), 1.0)
        
        composite = (0.4 * f1_weighted + 
                    0.3 * auc_roc + 
                    0.2 * precision_weighted + 
                    0.1 * (1 - norm_time))
        
        return float(composite)
    
    def _regression_composite(self, metrics: Dict[str, float], train_time: float, max_rmse: float = 10.0, max_mae: float = 10.0, max_time: float = 300.0) -> float:
        """Composite score for regression:
        0.4 * R² + 0.3 * (1 - Normalized_RMSE) + 0.2 * (1 - Normalized_MAE) + 0.1 * (1 - Normalized_Training_Time)"""
        
        r2 = float(metrics.get("r2", 0.0))
        rmse = float(metrics.get("rmse", max_rmse))
        mae = float(metrics.get("mae", max_mae))
        
        norm_rmse = min(rmse / max(max_rmse, 1e-6), 1.0)
        norm_mae = min(mae / max(max_mae, 1e-6), 1.0)
        norm_time = min(train_time / max(max_time, 1.0), 1.0)
        
        composite = (0.4 * r2 + 
                    0.3 * (1 - norm_rmse) + 
                    0.2 * (1 - norm_mae) + 
                    0.1 * (1 - norm_time))
        
        return float(composite)
    
    def _generate_ranking_rationale(self, top_model: dict, all_models: list, problem_type: str) -> str:
        """Generate ranking rationale using LLM"""
        try:
            llm = get_llm()
            prompt = build_ranking_rationale_prompt({
                "top_model": top_model["model_name"],
                "all_results": {m["model_name"]: m["metrics"] for m in all_models},
                "problem_type": problem_type,
            })
            response = llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            llm_output = validate_llm_output(content, RankingRationaleOutput)
            return llm_output.rationale
        except Exception as e:
            logger.warning(f"LLM ranking rationale failed: {e}")
            return f"{top_model['model_name']} achieved the highest composite score based on {problem_type} metrics."


ranking_agent = RankingAgent()