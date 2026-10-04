# Encoding Decision Prompt v1

ENCODING_DECISION_PROMPT = """You are an expert feature engineer deciding on categorical encoding strategies.

Column: {column_name}
Cardinality: {cardinality}
Sample Values: {sample_values}
Problem Type: {problem_type}
Model Family: {model_family}

Task: Decide the best encoding strategy for this column.

Rules:
- Cardinality ≤ 10: one-hot encoding
- Cardinality 10-50: target encoding (for tree models) or binary encoding
- Cardinality > 50: binary encoding or hash encoding
- Ordinal columns (size, grade, level, rating): ordinal encoding
- For linear models: prefer one-hot or target encoding
- For tree models: target encoding often works well for high cardinality

Output ONLY valid JSON matching this schema:
{{
  "column": "column_name",
  "encoding_strategy": "onehot|target|binary|ordinal|hash",
  "reasoning": "explanation"
}}"""

def build_prompt(context: dict) -> str:
    return ENCODING_DECISION_PROMPT.format(
        column_name=context.get("column_name", ""),
        cardinality=context.get("cardinality", 0),
        sample_values=context.get("sample_values", []),
        problem_type=context.get("problem_type", ""),
        model_family=context.get("model_family", "tree"),
    )