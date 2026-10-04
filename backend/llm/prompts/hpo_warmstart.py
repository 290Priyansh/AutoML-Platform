# HPO Warm Start Prompt v1

HPO_WARMSTART_PROMPT = """You are an expert ML engineer suggesting initial hyperparameters for Optuna optimization.

Model: {model_name}
Dataset: {n_samples} samples, {n_features} features
Problem Type: {problem_type}

Task: Suggest a good starting point in the search space for this model.
Consider:
- Dataset size (small/medium/large)
- Problem type (classification/regression)
- Model characteristics

Output ONLY valid JSON matching this schema:
{{
  "model_name": "model_name",
  "suggested_params": {{"param": value}},
  "reasoning": "explanation"
}}"""

def build_prompt(context: dict) -> str:
    return HPO_WARMSTART_PROMPT.format(
        model_name=context.get("model_name", ""),
        n_samples=context.get("n_samples", 0),
        n_features=context.get("n_features", 0),
        problem_type=context.get("problem_type", ""),
    )