import pytest
from backend.orchestrator.graph import build_pipeline_graph
from backend.orchestrator.router import (
    route_after_ingestion,
    route_after_eda,
    route_after_training,
)
from backend.orchestrator.state import PipelineState


class TestGraphCompilation:
    def test_build_pipeline_graph(self):
        """Test that the full LangGraph pipeline compiles without error"""
        app = build_pipeline_graph()
        assert app is not None
        # Check that nodes exist in the graph
        node_names = list(app.get_graph().nodes.keys())
        expected_nodes = [
            "ingestion", "eda", "problem_classifier", "data_quality", "split",
            "cleaning", "nlp", "encoding", "scaling", "feature_engineering",
            "feature_selection", "imbalance_handler", "cv_selection", "training",
            "hpo", "evaluation", "ranking", "ensemble", "explainability",
            "bias_fairness", "report", "packaging", "deployment", "drift_monitor"
        ]
        for node in expected_nodes:
            assert node in node_names, f"Node {node} missing from compiled graph"

    def test_route_after_ingestion(self):
        """Test text column routing logic"""
        state_with_text: PipelineState = {"text_columns": ["review_text"]}
        assert route_after_ingestion(state_with_text) == "has_text"

        state_no_text: PipelineState = {"text_columns": []}
        assert route_after_ingestion(state_no_text) == "no_text"

    def test_route_after_eda(self):
        """Test imbalance handling routing logic"""
        state_clf: PipelineState = {"problem_type": "classification", "imbalance_strategy": "none"}
        assert route_after_eda(state_clf) == "imbalanced"

        state_reg: PipelineState = {"problem_type": "regression", "imbalance_strategy": "none"}
        assert route_after_eda(state_reg) == "balanced"

        state_custom: PipelineState = {"problem_type": "regression", "imbalance_strategy": "smote"}
        assert route_after_eda(state_custom) == "imbalanced"

    def test_route_after_training(self):
        """Test ensemble routing logic"""
        state_3_models: PipelineState = {
            "ranked_models": [
                {"model_name": "m1"},
                {"model_name": "m2"},
                {"model_name": "m3"}
            ]
        }
        assert route_after_training(state_3_models) == "ensemble"

        state_1_model: PipelineState = {
            "ranked_models": [{"model_name": "m1"}]
        }
        assert route_after_training(state_1_model) == "skip_ensemble"
