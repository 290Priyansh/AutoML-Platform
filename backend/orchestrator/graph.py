from langgraph.graph import StateGraph, END
from backend.orchestrator.state import PipelineState
from backend.orchestrator.router import (
    route_after_ingestion,
    route_after_eda,
    route_after_training,
)
from backend.agents.phase1_understanding.ingestion_agent import ingestion_agent
from backend.agents.phase1_understanding.eda_agent import eda_agent
from backend.agents.phase1_understanding.problem_classifier_agent import problem_classifier_agent
from backend.agents.phase1_understanding.data_quality_agent import data_quality_agent
from backend.agents.phase1_understanding.split_agent import split_agent

from backend.agents.phase2_preprocessing.cleaning_agent import cleaning_agent
from backend.agents.phase2_preprocessing.nlp_agent import nlp_agent
from backend.agents.phase2_preprocessing.encoding_agent import encoding_agent
from backend.agents.phase2_preprocessing.scaling_agent import scaling_agent
from backend.agents.phase2_preprocessing.feature_engineering_agent import feature_engineering_agent
from backend.agents.phase2_preprocessing.feature_selection_agent import feature_selection_agent
from backend.agents.phase2_preprocessing.imbalance_handler_agent import imbalance_handler_agent

from backend.agents.phase3_modeling.cv_strategy_agent import cv_strategy_agent
from backend.agents.phase3_modeling.training_agent import training_agent
from backend.agents.phase3_modeling.hpo_agent import hpo_agent
from backend.agents.phase3_modeling.evaluation_agent import evaluation_agent
from backend.agents.phase3_modeling.ranking_agent import ranking_agent
from backend.agents.phase3_modeling.ensemble_agent import ensemble_agent

from backend.agents.phase4_output.explainability_agent import explainability_agent
from backend.agents.phase4_output.report_agent import report_agent
from backend.agents.phase4_output.bias_fairness_agent import bias_fairness_agent
from backend.agents.phase4_output.packaging_agent import packaging_agent
from backend.agents.phase4_output.deployment_agent import deployment_agent
from backend.agents.phase4_output.drift_monitor_agent import drift_monitor_agent


def build_pipeline_graph(checkpointer=None) -> StateGraph:
    graph = StateGraph(PipelineState)

    # Phase 1 - Understanding
    graph.add_node("ingestion", ingestion_agent)
    graph.add_node("eda", eda_agent)
    graph.add_node("problem_classifier", problem_classifier_agent)
    graph.add_node("data_quality", data_quality_agent)
    graph.add_node("split", split_agent)

    # Phase 2 - Preprocessing
    graph.add_node("cleaning", cleaning_agent)
    graph.add_node("nlp", nlp_agent)
    graph.add_node("encoding", encoding_agent)
    graph.add_node("scaling", scaling_agent)
    graph.add_node("feature_engineering", feature_engineering_agent)
    graph.add_node("feature_selection", feature_selection_agent)
    graph.add_node("imbalance_handler", imbalance_handler_agent)

    # Phase 3 - Modeling
    graph.add_node("cv_selection", cv_strategy_agent)
    graph.add_node("training", training_agent)
    graph.add_node("hpo", hpo_agent)
    graph.add_node("evaluation", evaluation_agent)
    graph.add_node("ranking", ranking_agent)
    graph.add_node("ensemble", ensemble_agent)

    # Phase 4 - Output
    graph.add_node("explainability", explainability_agent)
    graph.add_node("bias_fairness", bias_fairness_agent)
    graph.add_node("report", report_agent)
    graph.add_node("packaging", packaging_agent)
    graph.add_node("deployment", deployment_agent)
    graph.add_node("drift_monitor", drift_monitor_agent)

    # Entry point
    graph.set_entry_point("ingestion")

    # Phase 1 edges
    graph.add_edge("ingestion", "eda")
    graph.add_edge("eda", "problem_classifier")
    graph.add_edge("problem_classifier", "data_quality")
    graph.add_edge("data_quality", "split")

    # Phase 2 edges
    graph.add_edge("split", "cleaning")
    graph.add_conditional_edges(
        "cleaning",
        route_after_ingestion,
        {
            "has_text": "nlp",
            "no_text": "encoding",
        }
    )
    graph.add_edge("nlp", "encoding")
    graph.add_edge("encoding", "scaling")
    graph.add_edge("scaling", "feature_engineering")
    graph.add_edge("feature_engineering", "feature_selection")
    graph.add_conditional_edges(
        "feature_selection",
        route_after_eda,
        {
            "imbalanced": "imbalance_handler",
            "balanced": "cv_selection",
        }
    )
    graph.add_edge("imbalance_handler", "cv_selection")

    # Phase 3 edges
    graph.add_edge("cv_selection", "training")
    graph.add_edge("training", "hpo")
    graph.add_edge("hpo", "evaluation")
    graph.add_edge("evaluation", "ranking")
    graph.add_conditional_edges(
        "ranking",
        route_after_training,
        {
            "ensemble": "ensemble",
            "skip_ensemble": "explainability",
        }
    )
    graph.add_edge("ensemble", "explainability")

    # Phase 4 edges
    graph.add_edge("explainability", "bias_fairness")
    graph.add_edge("bias_fairness", "report")
    graph.add_edge("report", "packaging")
    graph.add_edge("packaging", "drift_monitor")
    graph.add_edge("drift_monitor", END)

    return graph.compile(checkpointer=checkpointer)