from abc import ABC, abstractmethod
from typing import Any, Dict
from backend.orchestrator.state import PipelineState
from backend.mlops.mlflow_client import log_agent_run
from backend.monitoring.prometheus import AGENT_DURATION, AGENT_ERRORS
import time
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    name: str = "base_agent"
    phase: str = "unknown"

    @abstractmethod
    def run(self, state: PipelineState) -> Dict[str, Any]:
        """
        Receives the full pipeline state.
        Returns a dict of ONLY the keys it updates.
        LangGraph merges this dict back into the full state.
        Must never mutate state in place.
        Must never raise unhandled exceptions — catch and set state["error"].
        Must update state["current_agent"] and state["progress_pct"].
        Must log start/end to MLflow.
        """
        pass

    def __call__(self, state: PipelineState) -> Dict[str, Any]:
        if state.get("status") == "failed" or state.get("error"):
            logger.warning(f"[{self.name}] Skipping because pipeline already failed: {state.get('error')}")
            return {"status": "failed", "error": state.get("error"), "current_agent": self.name}
        start = time.time()
        job_id = state.get("job_id", "unknown")
        logger.info(f"[{self.name}] Starting. Job: {job_id}")
        try:
            result = self.run(state)
            duration = time.time() - start
            try:
                AGENT_DURATION.labels(agent=self.name).observe(duration)
                log_agent_run(job_id=job_id, agent=self.name, duration=duration, success=True)
            except Exception as tel_err:
                logger.debug(f"Telemetry logging failed: {tel_err}")
            return result
        except Exception as e:
            try:
                AGENT_ERRORS.labels(agent=self.name).inc()
                log_agent_run(job_id=job_id, agent=self.name, duration=0, success=False, error=str(e))
            except Exception:
                pass
            logger.error(f"[{self.name}] Failed: {e}", exc_info=True)
            return {"error": str(e), "status": "failed", "current_agent": self.name}