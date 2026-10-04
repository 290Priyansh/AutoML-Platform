from backend.agents.base_agent import BaseAgent
from backend.orchestrator.state import PipelineState
from backend.mlops.artifact_store import download_from_s3, upload_to_s3
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, TimeSeriesSplit, GroupKFold
import io
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SplitAgent(BaseAgent):
    name: str = "split_agent"
    phase: str = "phase1_understanding"

    def run(self, state: PipelineState) -> Dict[str, Any]:
        dataframe_path = state["dataframe_path"]
        problem_type = state["problem_type"]
        target_column = state["target_column"]
        eda_report = state["eda_report"]
        
        # Download parquet from S3
        parquet_bytes = download_from_s3(dataframe_path)
        df = pd.read_parquet(io.BytesIO(parquet_bytes))
        
        # Detect group column for GroupKFold
        group_column = self._detect_group_column(df.columns, df=df)
        
        # Determine split strategy and execute
        if problem_type == "classification":
            train_df, val_df, test_df, split_strategy = self._stratified_split(
                df, target_column, group_column
            )
        elif problem_type == "regression":
            train_df, val_df, test_df, split_strategy = self._random_split(df, group_column)
        elif problem_type == "timeseries":
            train_df, val_df, test_df, split_strategy = self._timeseries_split(df, eda_report)
        elif problem_type == "clustering":
            train_df, val_df, test_df, split_strategy = self._clustering_split(df)
        else:
            # Default to random split
            train_df, val_df, test_df, split_strategy = self._random_split(df, group_column)
        
        # Save splits to S3
        # Save splits to S3
        base_path = dataframe_path.replace("dataframe.parquet", "") if "dataframe.parquet" in dataframe_path else f"{dataframe_path.rsplit('/', 1)[0]}/"
        train_path = upload_to_s3(
            train_df.to_parquet(index=False),
            f"{base_path}train.parquet"
        )
        val_path = upload_to_s3(
            val_df.to_parquet(index=False),
            f"{base_path}val.parquet"
        )
        test_path = upload_to_s3(
            test_df.to_parquet(index=False),
            f"{base_path}test.parquet"
        )
        
        return {
            "train_path": train_path,
            "val_path": val_path,
            "test_path": test_path,
            "split_strategy": split_strategy,
            "current_agent": self.name,
            "progress_pct": 50,
        }
    
    def _detect_group_column(self, columns, df: pd.DataFrame = None) -> str:
        """Detect if there's a group column like user_id, patient_id, etc. where rows share groups"""
        group_patterns = ['user_id', 'patient_id', 'customer_id', 'client_id', 'subject_id', 'group_id']
        for col in columns:
            col_l = col.lower()
            if any(pattern in col_l for pattern in group_patterns):
                if df is not None and df[col].nunique() >= len(df) * 0.95:
                    continue  # Unique identifier, not a grouping variable
                return col
        return None
    
    def _stratified_split(self, df: pd.DataFrame, target_column: str, group_column: str = None):
        """Stratified split for classification"""
        if group_column and group_column in df.columns:
            try:
                groups = df[group_column]
                gkf = GroupKFold(n_splits=5)
                train_idx, test_idx = next(gkf.split(df, groups=groups))
                train_val_df = df.iloc[train_idx]
                test_df = df.iloc[test_idx]
                
                # Further split train_val into train/val
                gkf2 = GroupKFold(n_splits=4)
                train_groups = train_val_df[group_column]
                train_idx2, val_idx2 = next(gkf2.split(train_val_df, groups=train_groups))
                train_df = train_val_df.iloc[train_idx2]
                val_df = train_val_df.iloc[val_idx2]
                split_strategy = "group_stratified"
            except Exception as e:
                logger.warning(f"Group split failed ({e}), falling back to random split")
                return self._random_split(df)
        else:
            # Standard stratified split 70/15/15 with safe fallback
            try:
                min_class_count = df[target_column].value_counts().min()
                if min_class_count < 2:
                    return self._random_split(df)
                    
                train_val_df, test_df = train_test_split(
                    df, test_size=0.15, stratify=df[target_column], random_state=42
                )
                train_df, val_df = train_test_split(
                    train_val_df, test_size=0.176, stratify=train_val_df[target_column], random_state=42
                )
                split_strategy = "stratified"
            except Exception as e:
                logger.warning(f"Stratified split failed ({e}), falling back to random split")
                return self._random_split(df)
        
        return train_df, val_df, test_df, split_strategy
    
    def _random_split(self, df: pd.DataFrame, group_column: str = None):
        """Random split for regression"""
        if group_column and group_column in df.columns:
            groups = df[group_column]
            gkf = GroupKFold(n_splits=5)
            train_idx, test_idx = next(gkf.split(df, groups=groups))
            train_val_df = df.iloc[train_idx]
            test_df = df.iloc[test_idx]
            
            gkf2 = GroupKFold(n_splits=4)
            train_groups = train_val_df[group_column]
            train_idx2, val_idx2 = next(gkf2.split(train_val_df, groups=train_groups))
            train_df = train_val_df.iloc[train_idx2]
            val_df = train_val_df.iloc[val_idx2]
            split_strategy = "group_random"
        else:
            train_val_df, test_df = train_test_split(df, test_size=0.15, random_state=42)
            train_df, val_df = train_test_split(train_val_df, test_size=0.176, random_state=42)
            split_strategy = "random"
        
        return train_df, val_df, test_df, split_strategy
    
    def _timeseries_split(self, df: pd.DataFrame, eda_report: dict):
        """Time-ordered split for timeseries"""
        # Find datetime column
        datetime_col = None
        for col, info in eda_report.get("variables", {}).items():
            if info.get("type") == "DateTime":
                datetime_col = col
                break
        
        if datetime_col is None:
            # Fallback to first datetime column in dataframe
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    datetime_col = col
                    break
        
        if datetime_col:
            df = df.sort_values(datetime_col)
        
        n = len(df)
        train_end = int(n * 0.6)
        val_end = int(n * 0.8)
        
        train_df = df.iloc[:train_end]
        val_df = df.iloc[train_end:val_end]
        test_df = df.iloc[val_end:]
        split_strategy = "timeseries"
        
        return train_df, val_df, test_df, split_strategy
    
    def _clustering_split(self, df: pd.DataFrame):
        """Random split for clustering (no target)"""
        train_val_df, test_df = train_test_split(df, test_size=0.1, random_state=42)
        train_df, val_df = train_test_split(train_val_df, test_size=0.111, random_state=42)  # 0.1/0.9
        split_strategy = "clustering_random"
        return train_df, val_df, test_df, split_strategy


split_agent = SplitAgent()