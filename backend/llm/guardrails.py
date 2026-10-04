from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal, Any
import json

class ProblemClassifierOutput(BaseModel):
    target_column: str
    problem_type: Literal["classification", "regression", "clustering", "timeseries"]
    reasoning: str

class EncodingDecisionOutput(BaseModel):
    column: str
    encoding_strategy: Literal["onehot", "target", "binary", "ordinal", "hash"]
    reasoning: str

class FeatureStrategyOutput(BaseModel):
    suggested_features: List[str]
    interaction_terms: List[str]
    reasoning: str

class RankingRationaleOutput(BaseModel):
    top_model: str
    rationale: str
    key_factors: List[str]

class ReportWriterOutput(BaseModel):
    report_markdown: str

class BiasAnalystOutput(BaseModel):
    bias_detected: bool
    sensitive_columns: List[str]
    fairness_metrics: dict
    recommendations: List[str]
    narrative: str

class HPOWarmStartOutput(BaseModel):
    model_name: str
    suggested_params: dict
    reasoning: str

class K8sCodegenOutput(BaseModel):
    deployment_yaml: str
    service_yaml: str
    ingress_yaml: str

def validate_llm_output(output: Any, model_class: type) -> BaseModel:
    """Parse and validate LLM JSON output against a Pydantic model"""
    try:
        if hasattr(output, "content"):
            output = output.content
        if not isinstance(output, str):
            output = str(output)
            
        # Try to extract JSON from the output
        start = output.find("{")
        end = output.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = output[start:end]
            data = json.loads(json_str)
        else:
            data = json.loads(output)
        return model_class(**data)
    except Exception as e:
        raise ValueError(f"Failed to validate LLM output: {e}")

def sanitize_for_prompt(data: dict, max_chars: int = 5000) -> str:
    """Sanitize data for inclusion in prompts - limit size, remove sensitive info"""
    import json
    json_str = json.dumps(data, default=str)
    if len(json_str) > max_chars:
        json_str = json_str[:max_chars] + "... (truncated)"
    return json_str