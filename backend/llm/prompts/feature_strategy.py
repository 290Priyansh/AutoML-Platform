# Feature Strategy Prompt v1

FEATURE_STRATEGY_PROMPT = """You are an expert feature engineer. Given a dataset summary, suggest feature engineering strategies.

Dataset Info:
- Columns: {columns}
- Problem type: {problem_type}
- Target column: {target_column}
- Sample rows (first 5): {sample_rows}
- Correlation with target: {correlations}

Task: Suggest:
1. New interaction features that might improve model performance
2. Transformations (log, sqrt, polynomial, etc.) for specific columns
3. Domain-specific features based on column names

Focus on safe, generally applicable transformations. Avoid suggestions that require domain knowledge not in the data.

Output ONLY valid JSON matching this schema:
{{
  "suggested_features": ["feature_name_1", "feature_name_2"],
  "interaction_terms": ["col1 * col2", "col3 / col4"],
  "reasoning": "explanation of why these features might help"
}}"""

def build_prompt(context: dict) -> str:
    return FEATURE_STRATEGY_PROMPT.format(
        columns=context.get("columns", []),
        problem_type=context.get("problem_type", ""),
        target_column=context.get("target_column", ""),
        sample_rows=context.get("sample_rows", []),
        correlations=context.get("correlations", {}),
    )