from backend.agents.base_agent import BaseAgent
from backend.orchestrator.state import PipelineState
from backend.llm.router import get_llm
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class DataQualityAgent(BaseAgent):
    name: str = "data_quality_agent"
    phase: str = "phase1_understanding"

    def run(self, state: PipelineState) -> Dict[str, Any]:
        eda_report = state["eda_report"]
        schema = state["schema"]
        
        # Extract metrics from EDA report
        n_rows = eda_report.get("table", {}).get("n", 0)
        n_cols = eda_report.get("table", {}).get("n_var", 0)
        missing_cells = eda_report.get("table", {}).get("n_cells_missing", 0)
        duplicate_rows = eda_report.get("table", {}).get("n_duplicates", 0)
        
        # Calculate component scores (heuristic)
        missing_pct = missing_cells / (n_rows * n_cols) if n_rows * n_cols > 0 else 0
        missing_score = max(0, 1 - missing_pct * 2)
        
        duplicate_pct = duplicate_rows / n_rows if n_rows > 0 else 0
        duplicate_score = max(0, 1 - duplicate_pct * 5)
        
        outlier_score = self._calculate_outlier_score(eda_report)
        dtype_score = self._calculate_dtype_score(schema)
        cardinality_score = self._calculate_cardinality_score(eda_report)
        
        weights = {
            "missing": 0.3,
            "duplicate": 0.2,
            "outlier": 0.2,
            "dtype": 0.15,
            "cardinality": 0.15,
        }
        
        composite_score = (
            weights["missing"] * missing_score +
            weights["duplicate"] * duplicate_score +
            weights["outlier"] * outlier_score +
            weights["dtype"] * dtype_score +
            weights["cardinality"] * cardinality_score
        )
        
        # Generate human-readable flags
        flags = []
        if missing_pct > 0.1:
            flags.append(f"High missing data: {missing_pct:.1%} of cells")
        if duplicate_pct > 0.05:
            flags.append(f"Duplicate rows detected: {duplicate_pct:.1%}")
        if outlier_score < 0.7:
            flags.append("High outlier rate in numeric columns")
        if dtype_score < 0.8:
            flags.append("Inconsistent data types detected")
        if cardinality_score < 0.7:
            flags.append("High cardinality categorical columns may need encoding")
        
        if composite_score < 0.4:
            flags.insert(0, "WARNING: Overall data quality is low (< 0.4)")
        
        # Use LLM for nuanced quality assessment and recommendations
        llm_analysis = self._get_llm_quality_analysis(eda_report, schema, composite_score, flags)
        if llm_analysis:
            flags.extend(llm_analysis.get("additional_flags", []))
            # Adjust score based on LLM insight
            if llm_analysis.get("adjust_score"):
                composite_score = max(0, min(1, composite_score + llm_analysis["adjust_score"]))
        
        return {
            "data_quality_score": round(composite_score, 3),
            "data_quality_flags": flags,
            "current_agent": self.name,
            "progress_pct": 40,
        }
    
    def _get_llm_quality_analysis(self, eda_report: dict, schema: dict, score: float, flags: List[str]) -> Dict[str, Any]:
        """Use LLM for nuanced quality assessment"""
        try:
            llm = get_llm(task="analysis")
            
            # Summarize key info for LLM
            variables = eda_report.get("variables", {})
            numeric_vars = {k: v for k, v in variables.items() if v.get("type") == "Numeric"}
            categorical_vars = {k: v for k, v in variables.items() if v.get("type") in ["Categorical", "Ordinal"]}
            
            prompt = f"""You are a data quality expert. Analyze this dataset quality profile and provide insights.

Dataset Profile:
- Rows: {eda_report.get('table', {}).get('n', 0)}
- Columns: {eda_report.get('table', {}).get('n_var', 0)}
- Missing cells: {eda_report.get('table', {}).get('n_cells_missing', 0)}
- Duplicate rows: {eda_report.get('table', {}).get('n_duplicates', 0)}
- Current quality score: {score:.2f}/1.0
- Existing flags: {flags}

Numeric columns ({len(numeric_vars)}): {list(numeric_vars.keys())[:10]}
Categorical columns ({len(categorical_vars)}): {list(categorical_vars.keys())[:10]}

Provide JSON response with:
- "additional_flags": list of additional quality concerns
- "adjust_score": float (-0.2 to 0.2) to adjust the quality score
- "recommendations": list of specific remediation steps
- "critical_issues": list of issues that could break ML pipelines

Focus on: target leakage risk, data drift signals, categorical encoding challenges, scaling issues, class imbalance indicators."""
            
            response = llm.invoke(prompt)
            import json
            content = response.content if hasattr(response, "content") else str(response)
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
        except Exception as e:
            logger.warning(f"LLM quality analysis failed: {e}")
        return {}
    
    def _calculate_outlier_score(self, eda_report: dict) -> float:
        variables = eda_report.get("variables", {})
        numeric_vars = [v for v in variables.values() if v.get("type") == "Numeric"]
        
        if not numeric_vars:
            return 1.0
        
        outlier_ratios = []
        for var in numeric_vars:
            outliers = var.get("n_outliers", 0)
            total = var.get("n", 1)
            outlier_ratios.append(outliers / total)
        
        avg_outlier_ratio = np.mean(outlier_ratios) if outlier_ratios else 0
        return max(0, 1 - avg_outlier_ratio * 10)
    
    def _calculate_dtype_score(self, schema: dict) -> float:
        object_cols = sum(1 for dt in schema.values() if dt == 'object')
        total_cols = len(schema)
        if total_cols == 0:
            return 1.0
        return max(0.5, 1 - (object_cols / total_cols) * 0.5)
    
    def _calculate_cardinality_score(self, eda_report: dict) -> float:
        variables = eda_report.get("variables", {})
        categorical_vars = [v for v in variables.values() if v.get("type") in ["Categorical", "Ordinal"]]
        
        if not categorical_vars:
            return 1.0
        
        high_card_count = sum(1 for v in categorical_vars if v.get("n_distinct", 0) > 100)
        ratio = high_card_count / len(categorical_vars)
        return max(0.3, 1 - ratio)


data_quality_agent = DataQualityAgent()