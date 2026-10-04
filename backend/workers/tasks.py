try:
    from celery import shared_task
    from celery.exceptions import SoftTimeLimitExceeded
except ImportError:
    class SoftTimeLimitExceeded(Exception):
        pass

    def shared_task(*args, **kwargs):
        def decorator(f):
            def delay(*a, **kw):
                return f(None, *a, **kw)
            f.delay = delay
            return f
        return decorator

from backend.orchestrator.graph import build_pipeline_graph
from backend.orchestrator.state import PipelineState
from backend.orchestrator.store import set_job_state
from backend.mlops.mlflow_client import get_checkpointer
import logging

logger = logging.getLogger(__name__)

def _safe_push_progress(job_id: str, agent: str, state: dict):
    try:
        from backend.api.websocket import push_progress
        push_progress(job_id=job_id, agent=agent, state=state)
    except Exception as pe:
        logger.debug(f"Progress push error: {pe}")

@shared_task(bind=True, max_retries=2, soft_time_limit=1800, time_limit=2100)
def run_pipeline(self, job_id: str, initial_state: dict):
    """
    The main Celery task. Receives the initial state, runs the full LangGraph pipeline,
    pushes progress via WebSocket at each agent transition, and syncs status in the job store.
    """
    try:
        graph = build_pipeline_graph(checkpointer=get_checkpointer())
        config = {"configurable": {"thread_id": job_id}}
        
        # Update initial state with job_id
        initial_state["job_id"] = job_id
        set_job_state(job_id, initial_state)
        
        for event in graph.stream(initial_state, config=config):
            agent_name = list(event.keys())[0]
            state_update = event[agent_name]
            pct = state_update.get("progress_pct", 0)
            logger.info(f"Agent finished: {agent_name} -> progress {pct}%")
            print(f"[Pipeline] Finished: {agent_name} ({pct}%)", flush=True)
            
            # Sync to job store
            if state_update.get("status") != "failed":
                state_update["status"] = "running"
            set_job_state(job_id, state_update)
            
            # Push progress
            _safe_push_progress(job_id=job_id, agent=agent_name, state=state_update)
            
            # Check if failed
            if state_update.get("status") == "failed":
                logger.error(f"Pipeline failed at {agent_name}: {state_update.get('error')}")
                print(f"[Pipeline ERROR] Failed at {agent_name}: {state_update.get('error')}", flush=True)
                return
        
        # Pipeline reached end successfully
        completed_update = {
            "status": "completed",
            "progress_pct": 100,
            "current_agent": "complete",
        }
        set_job_state(job_id, completed_update)
        _safe_push_progress(job_id=job_id, agent="complete", state=completed_update)
                
    except SoftTimeLimitExceeded:
        failed_state = {"status": "failed", "error": "Pipeline timed out after 30 minutes"}
        set_job_state(job_id, failed_state)
        _safe_push_progress(job_id=job_id, agent="timeout", state=failed_state)
        raise
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        failed_state = {"status": "failed", "error": str(e)}
        set_job_state(job_id, failed_state)
        _safe_push_progress(job_id=job_id, agent="error", state=failed_state)
        raise