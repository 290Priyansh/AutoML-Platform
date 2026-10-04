from typing import Any
import importlib

__all__ = [
    "cv_strategy_agent",
    "training_agent",
    "hpo_agent",
    "evaluation_agent",
    "ranking_agent",
    "ensemble_agent",
]

_AGENT_MODULES = {
    "cv_strategy_agent": "backend.agents.phase3_modeling.cv_strategy_agent",
    "training_agent": "backend.agents.phase3_modeling.training_agent",
    "hpo_agent": "backend.agents.phase3_modeling.hpo_agent",
    "evaluation_agent": "backend.agents.phase3_modeling.evaluation_agent",
    "ranking_agent": "backend.agents.phase3_modeling.ranking_agent",
    "ensemble_agent": "backend.agents.phase3_modeling.ensemble_agent",
}

def __getattr__(name: str) -> Any:
    if name in _AGENT_MODULES:
        module = importlib.import_module(_AGENT_MODULES[name])
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")