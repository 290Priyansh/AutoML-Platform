# Report Writer Prompt v1

REPORT_WRITER_PROMPT = """You are a senior ML engineer writing a professional AutoML report for a client.

Context:
- Dataset: {row_count} rows, {col_count} columns
- Problem Type: {problem_type}
- Target: {target_column}
- Data Quality Score: {data_quality_score}/1.0
- Quality Flags: {quality_flags}
- Preprocessing: {preprocessing_summary}
- All Models Results: {all_results}
- Top 3 Models: {top3_models}
- Feature Importances: {feature_importances}
- Bias Report: {bias_report}

Write a complete, professional markdown report with these EXACT sections:

1. **Executive Summary** (3-4 sentences)
2. **Dataset Overview**
3. **Data Quality Assessment**
4. **Preprocessing Decisions and Rationale**
5. **Model Training Results** (table of all models + metrics)
6. **Top 3 Recommended Models** (detailed per-model analysis)
7. **Feature Importance Analysis**
8. **Bias and Fairness Assessment**
9. **Recommendations for Production Deployment**
10. **Next Steps**

Requirements:
- Use clear headings (##)
- Include metric tables in markdown format
- Be specific with numbers
- Professional tone
- Actionable recommendations

Output ONLY the markdown report (no JSON wrapper)."""

def build_prompt(context: dict) -> str:
    return REPORT_WRITER_PROMPT.format(
        row_count=context.get("row_count", 0),
        col_count=context.get("col_count", 0),
        problem_type=context.get("problem_type", ""),
        target_column=context.get("target_column", ""),
        data_quality_score=context.get("data_quality_score", 0.0),
        quality_flags=context.get("quality_flags", []),
        preprocessing_summary=context.get("preprocessing_summary", ""),
        all_results=context.get("all_results", {}),
        top3_models=context.get("top3_models", []),
        feature_importances=context.get("feature_importances", {}),
        bias_report=context.get("bias_report", {}),
    )