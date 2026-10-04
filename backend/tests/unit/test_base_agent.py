import pytest
from backend.agents.base_agent import BaseAgent
from backend.orchestrator.state import PipelineState


class TestBaseAgent:
    def test_base_agent_abstract(self):
        """Test that BaseAgent cannot be instantiated directly"""
        with pytest.raises(TypeError):
            BaseAgent()
    
    def test_base_agent_subclass(self, mock_state):
        """Test that a subclass can be instantiated"""
        class TestAgent(BaseAgent):
            name = "test_agent"
            
            def run(self, state):
                return {"test": "value"}
        
        agent = TestAgent()
        result = agent(mock_state)
        
        assert result == {"test": "value"}
        assert agent.name == "test_agent"


class TestPipelineState:
    def test_state_structure(self, mock_state):
        """Test that mock_state has all required keys"""
        required_keys = [
            "job_id", "user_id", "created_at", "status", "current_agent",
            "progress_pct", "error", "raw_data_path", "data_source_type",
            "user_model_preference", "dataframe_path", "schema", "row_count",
            "col_count", "eda_report", "problem_type", "target_column",
            "feature_columns", "data_quality_score", "data_quality_flags",
            "train_path", "val_path", "test_path", "split_strategy",
        ]
        
        for key in required_keys:
            assert key in mock_state