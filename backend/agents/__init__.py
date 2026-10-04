from backend.agents.base_agent import BaseAgent
import importlib

_AGENT_MODULES = {
    # Phase 1
    "ingestion_agent": ("backend.agents.phase1_understanding", "ingestion_agent"),
    "eda_agent": ("backend.agents.phase1_understanding", "eda_agent"),
    "problem_classifier_agent": ("backend.agents.phase1_understanding", "problem_classifier_agent"),
    "data_quality_agent": ("backend.agents.phase1_understanding", "data_quality_agent"),
    "split_agent": ("backend.agents.phase1_understanding", "split_agent"),
    # Phase 2
    "cleaning_agent": ("backend.agents.phase2_preprocessing", "cleaning_agent"),
    "nlp_agent": ("backend.agents.phase2_preprocessing", "nlp_agent"),
    "encoding_agent": ("backend.agents.phase2_preprocessing", "encoding_agent"),
    "scaling_agent": ("backend.agents.phase2_preprocessing", "scaling_agent"),
    "feature_engineering_agent": ("backend.agents.phase2_preprocessing", "feature_engineering_agent"),
    "feature_selection_agent": ("backend.agents.phase2_preprocessing", "feature_selection_agent"),
    "imbalance_handler_agent": ("backend.agents.phase2_preprocessing", "imbalance_handler_agent"),
    # Phase 3
    "cv_strategy_agent": ("backend.agents.phase3_modeling", "cv_strategy_agent"),
    "training_agent": ("backend.agents.phase3_modeling", "training_agent"),
    "hpo_agent": ("backend.agents.phase3_modeling", "hpo_agent"),
    "evaluation_agent": ("backend.agents.phase3_modeling", "evaluation_agent"),
    "ranking_agent": ("backend.agents.phase3_modeling", "ranking_agent"),
    "ensemble_agent": ("backend.agents.phase3_modeling", "ensemble_agent"),
    # Phase 4
    "explainability_agent": ("backend.agents.phase4_output", "explainability_agent"),
    "report_agent": ("backend.agents.phase4_output", "report_agent"),
    "bias_fairness_agent": ("backend.agents.phase4_output", "bias_fairness_agent"),
    "packaging_agent": ("backend.agents.phase4_output", "packaging_agent"),
    "deployment_agent": ("backend.agents.phase4_output", "deployment_agent"),
    "drift_monitor_agent": ("backend.agents.phase4_output", "drift_monitor_agent"),
}

def __getattr__(name: str):
    if name in _AGENT_MODULES:
        mod_name, attr_name = _AGENT_MODULES[name]
        mod = importlib.import_module(mod_name)
        val = getattr(mod, attr_name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__} has no attribute {name}")

__all__ = ["BaseAgent"] + list(_AGENT_MODULES.keys())