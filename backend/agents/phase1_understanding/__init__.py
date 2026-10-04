from typing import Any
import importlib

__all__ = [
    "ingestion_agent",
    "eda_agent",
    "problem_classifier_agent",
    "data_quality_agent",
    "split_agent",
]

_AGENT_MODULES = {
    "ingestion_agent": "backend.agents.phase1_understanding.ingestion_agent",
    "eda_agent": "backend.agents.phase1_understanding.eda_agent",
    "problem_classifier_agent": "backend.agents.phase1_understanding.problem_classifier_agent",
    "data_quality_agent": "backend.agents.phase1_understanding.data_quality_agent",
    "split_agent": "backend.agents.phase1_understanding.split_agent",
}

def __getattr__(name: str) -> Any:
    if name in _AGENT_MODULES:
        module = importlib.import_module(_AGENT_MODULES[name])
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")