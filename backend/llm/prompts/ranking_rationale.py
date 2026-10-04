# Ranking Rationale Prompt v1

RANKING_RATIONALE_PROMPT = """You are an ML engineer explaining model selection to a business stakeholder.

Top Model: {top_model}
All Models Results: {all_results}
Problem Type: {problem_type}

Task: Write a clear, concise paragraph (3-5 sentences) explaining why the top model won. 
Focus on:
- Key metric advantages
- Trade-offs (speed vs accuracy)
- Practical implications

Avoid technical jargon. Write for a non-technical audience.

Output ONLY valid JSON matching this schema:
{{
  "top_model": "model_name",
  "rationale": "explanation paragraph",
  "key_factors": ["factor1", "factor2", "factor3"]
}}"""

def build_prompt(context: dict) -> str:
    return RANKING_RATIONALE_PROMPT.format(
        top_model=context.get("top_model", ""),
        all_results=context.get("all_results", {}),
        problem_type=context.get("problem_type", ""),
    )