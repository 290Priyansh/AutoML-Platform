from backend.agents.base_agent import BaseAgent
from backend.orchestrator.state import PipelineState
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class CVStrategyAgent(BaseAgent):
    name: str = "cv_strategy_agent"
    phase: str = "phase3_modeling"

    def run(self, state: PipelineState) -> Dict[str, Any]:
        problem_type = state["problem_type"]
        # Check for group column from split agent
        split_strategy = state.get("split_strategy", "")
        
        # Check for imbalance
        train_path = state["cleaned_train_path"].replace("cleaned_train", "resampled_train")
        # We'd need to load the data to check imbalance, but we can use the imbalance_strategy
        imbalance_strategy = state.get("imbalance_strategy", "none")
        is_imbalanced = imbalance_strategy != "none"
        
        # Determine CV strategy
        if problem_type == "classification":
            if is_imbalanced:
                cv_strategy = "StratifiedKFold_shuffled"
            else:
                cv_strategy = "StratifiedKFold"
        elif problem_type == "regression":
            cv_strategy = "KFold"
        elif problem_type == "timeseries":
            cv_strategy = "TimeSeriesSplit"
        else:
            cv_strategy = "KFold"
        
        # Override for group-based splits
        if "group" in split_strategy:
            cv_strategy = "GroupKFold"
        
        logger.info(f"Selected CV strategy: {cv_strategy}")
        
        return {
            "cv_strategy": cv_strategy,
            "current_agent": self.name,
            "progress_pct": 88,
        }


cv_strategy_agent = CVStrategyAgent()