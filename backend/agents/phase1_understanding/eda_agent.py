from backend.agents.base_agent import BaseAgent
from backend.orchestrator.state import PipelineState
from backend.mlops.artifact_store import download_from_s3, upload_to_s3
import pandas as pd
try:
    from ydata_profiling import ProfileReport
    YDATA_AVAILABLE = True
except ImportError:
    ProfileReport = None
    YDATA_AVAILABLE = False
import io
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class EDAAgent(BaseAgent):
    name: str = "eda_agent"
    phase: str = "phase1_understanding"

    def run(self, state: PipelineState) -> Dict[str, Any]:
        dataframe_path = state["dataframe_path"]
        
        # Download parquet from S3
        parquet_bytes = download_from_s3(dataframe_path)
        df = pd.read_parquet(io.BytesIO(parquet_bytes))
        
        if YDATA_AVAILABLE:
            # Run ydata-profiling in minimal mode
            profile = ProfileReport(df, minimal=True, progress_bar=False)
            profile_json = profile.to_json()
            eda_report = json.loads(profile_json)
        else:
            eda_report = {
                "table": {
                    "n": len(df),
                    "n_var": len(df.columns),
                    "n_cells_missing": int(df.isnull().sum().sum()),
                    "n_duplicates": int(df.duplicated().sum()),
                },
                "variables": {
                    col: {
                        "type": "Numeric" if pd.api.types.is_numeric_dtype(df[col]) else "Categorical",
                        "n": int(len(df[col].dropna())),
                        "n_distinct": int(df[col].nunique()),
                        "p_missing": float(df[col].isnull().mean()),
                    }
                    for col in df.columns
                }
            }
        
        # Additional computations
        # Class distribution if target is categorical (will be determined later)
        # For now, compute correlation matrix and missing value info
        numeric_cols = df.select_dtypes(include=['number']).columns
        correlation_matrix = df[numeric_cols].corr().to_dict() if len(numeric_cols) > 1 else {}
        
        missing_info = df.isnull().sum().to_dict()
        missing_pct = (df.isnull().sum() / len(df) * 100).to_dict()
        
        # High cardinality columns
        cardinality = df.nunique().to_dict()
        high_cardinality_cols = sorted(
            [(col, card) for col, card in cardinality.items() if card > 50],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Add additional info to report
        eda_report["correlation_matrix"] = correlation_matrix
        eda_report["missing_info"] = missing_info
        eda_report["missing_pct"] = missing_pct
        eda_report["high_cardinality_columns"] = high_cardinality_cols
        
        # Save full profile JSON to S3
        if "dataframe.parquet" in dataframe_path:
            profile_key = dataframe_path.replace("dataframe.parquet", "eda_report.json")
        else:
            profile_key = f"{dataframe_path.rsplit('/', 1)[0]}/eda_report.json"
        upload_to_s3(json.dumps(eda_report, default=str).encode(), profile_key)
        
        # Save missing value heatmap as PNG (optional, for visualization)
        # This would require matplotlib - skipping for minimal mode
        
        return {
            "eda_report": eda_report,
            "current_agent": self.name,
            "progress_pct": 20,
        }


eda_agent = EDAAgent()