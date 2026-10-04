from typing import Any
import importlib

__all__ = [
    "cleaning_agent",
    "nlp_agent",
    "encoding_agent",
    "scaling_agent",
    "feature_engineering_agent",
    "feature_selection_agent",
    "imbalance_handler_agent",
]

_AGENT_MODULES = {
    "cleaning_agent": "backend.agents.phase2_preprocessing.cleaning_agent",
    "nlp_agent": "backend.agents.phase2_preprocessing.nlp_agent",
    "encoding_agent": "backend.agents.phase2_preprocessing.encoding_agent",
    "scaling_agent": "backend.agents.phase2_preprocessing.scaling_agent",
    "feature_engineering_agent": "backend.agents.phase2_preprocessing.feature_engineering_agent",
    "feature_selection_agent": "backend.agents.phase2_preprocessing.feature_selection_agent",
    "imbalance_handler_agent": "backend.agents.phase2_preprocessing.imbalance_handler_agent",
}

def __getattr__(name: str) -> Any:
    if name in _AGENT_MODULES:
        module = importlib.import_module(_AGENT_MODULES[name])
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")