from typing import Dict, Any, Optional
import threading
import logging

logger = logging.getLogger(__name__)

_jobs: Dict[str, Dict[str, Any]] = {}
_lock = threading.Lock()


def set_job_state(job_id: str, state: Dict[str, Any]) -> None:
    """Store or update the in-memory state for a given job."""
    with _lock:
        if job_id not in _jobs:
            _jobs[job_id] = {}
        _jobs[job_id].update(state)


def get_job_state(job_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a copy of the job state, if available."""
    with _lock:
        if job_id in _jobs:
            return _jobs[job_id].copy()
        return None


def get_all_jobs() -> list:
    """Retrieve all stored jobs."""
    with _lock:
        return [v.copy() for v in _jobs.values()]

