from typing import Any
import importlib

__all__ = [
    "explainability_agent",
    "report_agent",
    "bias_fairness_agent",
    "packaging_agent",
    "deployment_agent",
    "drift_monitor_agent",
]

_AGENT_MODULES = {
    "explainability_agent": "backend.agents.phase4_output.explainability_agent",
    "report_agent": "backend.agents.phase4_output.report_agent",
    "bias_fairness_agent": "backend.agents.phase4_output.bias_fairness_agent",
    "packaging_agent": "backend.agents.phase4_output.packaging_agent",
    "deployment_agent": "backend.agents.phase4_output.deployment_agent",
    "drift_monitor_agent": "backend.agents.phase4_output.drift_monitor_agent",
}

def __getattr__(name: str) -> Any:
    if name in _AGENT_MODULES:
        module = importlib.import_module(_AGENT_MODULES[name])
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")