from backend.agents.base_agent import BaseAgent
from backend.orchestrator.state import PipelineState
from backend.mlops.artifact_store import download_from_s3
from backend.llm.router import get_llm
from backend.llm.prompts.problem_classifier import build_prompt as build_problem_classifier_prompt
from backend.llm.guardrails import validate_llm_output, ProblemClassifierOutput
import pandas as pd
import io
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ProblemClassifierAgent(BaseAgent):
    name: str = "problem_classifier_agent"
    phase: str = "phase1_understanding"

    def run(self, state: PipelineState) -> Dict[str, Any]:
        eda_report = state["eda_report"]
        schema = state["schema"]
        user_target = state.get("target_column", "")
        
        # Get sample data
        dataframe_path = state["dataframe_path"]
        parquet_bytes = download_from_s3(dataframe_path)
        df = pd.read_parquet(io.BytesIO(parquet_bytes))
        sample_rows = df.head(10).to_dict(orient='records')
        columns = list(df.columns)
        
        # Heuristic classification first
        heuristic_result = self._heuristic_classify(df, schema, user_target)
        
        # Use LLM to confirm/override
        llm = get_llm()
        prompt = build_problem_classifier_prompt({
            "columns": columns,
            "sample_rows": sample_rows,
            "eda_summary": str(eda_report)[:3000],
            "user_target": user_target or "Not specified",
        })
        
        try:
            response = llm.invoke(prompt)
            llm_output = validate_llm_output(response, ProblemClassifierOutput)
            
            # Use LLM result if confident, otherwise fall back to heuristic
            target_column = llm_output.target_column
            problem_type = llm_output.problem_type
            reasoning = llm_output.reasoning
        except Exception as e:
            logger.warning(f"LLM classification failed, using heuristic: {e}")
            target_column = heuristic_result["target_column"]
            problem_type = heuristic_result["problem_type"]
            reasoning = f"Heuristic: {heuristic_result['reasoning']}"
        
        # Determine feature columns (all except target)
        feature_columns = [c for c in columns if c != target_column]
        
        return {
            "problem_type": problem_type,
            "target_column": target_column,
            "feature_columns": feature_columns,
            "current_agent": self.name,
            "progress_pct": 30,
        }
    
    def _heuristic_classify(self, df: pd.DataFrame, schema: dict, user_target: str) -> Dict[str, Any]:
        # If user specified target, use it
        if user_target and user_target in df.columns:
            target_col = user_target
        else:
            # Look for common target column names (case-insensitive)
            target_candidates = ['target', 'label', 'class', 'outcome', 'response', 'y', 'status', 'churn', 'survived', 'v1']
            target_col = None
            lower_cols = {c.lower(): c for c in df.columns}
            for cand in target_candidates:
                if cand in lower_cols:
                    col_name = lower_cols[cand]
                    # Ensure column is not mostly empty
                    if df[col_name].isna().mean() < 0.5:
                        target_col = col_name
                        break

            if target_col is None:
                # Filter valid candidate columns: not Unnamed, not ID, not mostly missing
                valid_cols = [
                    c for c in df.columns
                    if not str(c).startswith('Unnamed:')
                    and not str(c).lower().endswith('_id')
                    and str(c).lower() not in ['id', 'uuid', 'index']
                    and df[c].isna().mean() < 0.5
                ]
                if valid_cols:
                    # Prefer a column with low non-zero cardinality or the last valid column
                    low_card = [c for c in valid_cols if 1 < df[c].nunique() <= 20]
                    target_col = low_card[0] if low_card else valid_cols[-1]
                else:
                    target_col = df.columns[-1]
        
        target_series = df[target_col]
        n_unique = target_series.nunique()
        
        is_bool = target_series.dtype == 'bool' or target_series.dtype == 'boolean'
        is_cat = isinstance(target_series.dtype, pd.CategoricalDtype) or target_series.dtype == 'object'
        is_integer = pd.api.types.is_integer_dtype(target_series)
        is_numeric = pd.api.types.is_numeric_dtype(target_series)

        # Determine problem type
        if is_bool or (n_unique <= 20 and (is_cat or is_integer or n_unique == 2)):
            problem_type = "classification"
            reasoning = f"Target '{target_col}' has {n_unique} unique values, indicating classification"
        elif pd.api.types.is_datetime64_any_dtype(target_series):
            problem_type = "timeseries"
            reasoning = f"Target '{target_col}' is datetime, suggesting timeseries"
        elif is_numeric and n_unique > 20:
            problem_type = "regression"
            reasoning = f"Target '{target_col}' is continuous numeric, suggesting regression"
        elif is_numeric and n_unique <= 20:
            problem_type = "classification"
            reasoning = f"Target '{target_col}' is discrete numeric with {n_unique} unique values, suggesting classification"
        else:
            problem_type = "classification" if n_unique <= 50 else "clustering"
            reasoning = f"Target '{target_col}' evaluated to {problem_type}"
        
        return {
            "target_column": target_col,
            "problem_type": problem_type,
            "reasoning": reasoning,
        }


problem_classifier_agent = ProblemClassifierAgent()