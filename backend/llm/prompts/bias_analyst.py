# Bias Analyst Prompt v1

BIAS_ANALYST_PROMPT = """You are an AI ethics expert analyzing model fairness.

Fairness Metrics: {fairness_metrics}
Feature Importances: {feature_importances}
Sensitive Columns: {sensitive_columns}
Problem Type: {problem_type}

Task: Analyze the bias/fairness results and write:
1. Whether bias was detected
2. Which sensitive groups are affected
3. Specific fairness metric violations (demographic parity, equalized odds)
4. Root cause hypotheses (proxy features, historical bias, etc.)
5. Concrete recommendations for mitigation

Output ONLY valid JSON matching this schema:
{{
  "bias_detected": true/false,
  "sensitive_columns": ["col1", "col2"],
  "fairness_metrics": {{"metric": value}},
  "recommendations": ["rec1", "rec2", "rec3"],
  "narrative": "detailed analysis paragraph"
}}"""

def build_prompt(context: dict) -> str:
    return BIAS_ANALYST_PROMPT.format(
        fairness_metrics=context.get("fairness_metrics", {}),
        feature_importances=context.get("feature_importances", {}),
        sensitive_columns=context.get("sensitive_columns", []),
        problem_type=context.get("problem_type", ""),
    )