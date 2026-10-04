from backend.orchestrator.state import PipelineState

def route_after_ingestion(state: PipelineState) -> str:
    """Route after cleaning: check if text columns exist for NLP processing"""
    text_columns = state.get("text_columns", [])
    if text_columns:
        return "has_text"
    return "no_text"

def route_after_eda(state: PipelineState) -> str:
    """Route after feature selection: check if imbalance handling should be evaluated"""
    problem_type = state.get("problem_type", "")
    imbalance_strategy = state.get("imbalance_strategy", "none")
    if problem_type == "classification" or (imbalance_strategy and imbalance_strategy != "none"):
        return "imbalanced"
    return "balanced"

def route_after_preprocessing(state: PipelineState) -> str:
    """Route after preprocessing (legacy - not used in current graph)"""
    return "continue"

def route_after_training(state: PipelineState) -> str:
    """Route after ranking: check if ensemble should be built"""
    ranked_models = state.get("ranked_models", [])
    if len(ranked_models) >= 2:
        return "ensemble"
    return "skip_ensemble"