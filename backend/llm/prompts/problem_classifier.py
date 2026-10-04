# Problem Classifier Prompt v1

PROBLEM_CLASSIFIER_PROMPT = """You are an expert ML engineer. Given a dataset summary, identify the target column and problem type.

Dataset Info:
- Columns: {columns}
- Sample rows (first 10): {sample_rows}
- EDA Summary: {eda_summary}
- User specified target: {user_target}

Task: Determine:
1. Which column is the target (if not specified by user)
2. Problem type: classification, regression, clustering, or timeseries
3. Reasoning for your decision

Rules:
- If target is boolean or has ≤20 unique values → classification
- If target is continuous float → regression
- If no target specified and no clear target → clustering
- If datetime index with regular intervals → timeseries

Output ONLY valid JSON matching this schema:
{{
  "target_column": "column_name",
  "problem_type": "classification|regression|clustering|timeseries",
  "reasoning": "explanation"
}}"""

def build_prompt(context: dict) -> str:
    return PROBLEM_CLASSIFIER_PROMPT.format(
        columns=context.get("columns", []),
        sample_rows=context.get("sample_rows", []),
        eda_summary=context.get("eda_summary", ""),
        user_target=context.get("user_target", "Not specified"),
    )