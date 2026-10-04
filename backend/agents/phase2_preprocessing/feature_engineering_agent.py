from backend.agents.base_agent import BaseAgent
from backend.orchestrator.state import PipelineState
from backend.mlops.artifact_store import download_from_s3, upload_to_s3
from backend.llm.router import get_llm
from backend.llm.prompts.feature_strategy import build_prompt as build_feature_strategy_prompt
from backend.llm.guardrails import validate_llm_output, FeatureStrategyOutput
import pandas as pd
import numpy as np
import io
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class FeatureEngineeringAgent(BaseAgent):
    name: str = "feature_engineering_agent"
    phase: str = "phase2_preprocessing"

    def run(self, state: PipelineState) -> Dict[str, Any]:
        train_path = state["cleaned_train_path"].replace("cleaned_train", "scaled_train")
        val_path = state["cleaned_val_path"].replace("cleaned_val", "scaled_val")
        test_path = state["cleaned_test_path"].replace("cleaned_test", "scaled_test")
        
        # Load data with fallback
        try:
            train_df = pd.read_parquet(io.BytesIO(download_from_s3(train_path)))
            val_df = pd.read_parquet(io.BytesIO(download_from_s3(val_path)))
            test_df = pd.read_parquet(io.BytesIO(download_from_s3(test_path)))
        except Exception:
            train_path = state["cleaned_train_path"]
            val_path = state["cleaned_val_path"]
            test_path = state["cleaned_test_path"]
            train_df = pd.read_parquet(io.BytesIO(download_from_s3(train_path)))
            val_df = pd.read_parquet(io.BytesIO(download_from_s3(val_path)))
            test_df = pd.read_parquet(io.BytesIO(download_from_s3(test_path)))
        
        target_column = state.get("target_column")
        problem_type = state.get("problem_type", "")
        engineered_features = []
        
        # 1. Datetime decomposition
        datetime_cols = train_df.select_dtypes(include=['datetime64']).columns.tolist()
        for col in datetime_cols:
            new_features = self._decompose_datetime(train_df, val_df, test_df, col)
            engineered_features.extend(new_features)
        
        # 2. Numeric interaction terms (for regression)
        if problem_type == "regression" and target_column and target_column in train_df.columns:
            numeric_cols = train_df.select_dtypes(include=[np.number]).columns.tolist()
            if target_column in numeric_cols:
                numeric_cols.remove(target_column)
            
            if numeric_cols and pd.api.types.is_numeric_dtype(train_df[target_column]):
                # Correlations with target
                corr_matrix = train_df[numeric_cols + [target_column]].corr(numeric_only=True)
                if target_column in corr_matrix.columns:
                    correlations = corr_matrix[target_column].abs().sort_values(ascending=False)
                    top_corr = [c for c in correlations.head(6).index.tolist() if c != target_column][:5]
                    
                    # Pairwise interactions
                    for i, col1 in enumerate(top_corr):
                        for col2 in top_corr[i+1:]:
                            for df in [train_df, val_df, test_df]:
                                df[f"{col1}_x_{col2}"] = df[col1] * df[col2]
                            engineered_features.append(f"{col1}_x_{col2}")
                    
                    # Polynomial features (degree 2)
                    for col in top_corr:
                        for df in [train_df, val_df, test_df]:
                            df[f"{col}_sq"] = df[col] ** 2
                        engineered_features.append(f"{col}_sq")
        
        # 3. Ratio features (total_X / count_X)
        for col in list(train_df.columns):
            if col.startswith('total_'):
                base = col.replace('total_', '')
                count_col = f"count_{base}"
                if count_col in train_df.columns and pd.api.types.is_numeric_dtype(train_df[col]) and pd.api.types.is_numeric_dtype(train_df[count_col]):
                    for df in [train_df, val_df, test_df]:
                        df[f"{base}_per_unit"] = df[col] / (df[count_col] + 1e-8)
                    engineered_features.append(f"{base}_per_unit")
        
        # 4. Cyclical encoding for datetime parts
        cyclical_cols = [c for c in train_df.columns if pd.api.types.is_numeric_dtype(train_df[c]) and any(x in c.lower() for x in ['month', 'dayofweek', 'hour', 'day'])]
        for col in cyclical_cols:
            max_val = train_df[col].max()
            if max_val and max_val > 0:
                for df in [train_df, val_df, test_df]:
                    df[f"{col}_sin"] = np.sin(2 * np.pi * df[col] / max_val)
                    df[f"{col}_cos"] = np.cos(2 * np.pi * df[col] / max_val)
                engineered_features.extend([f"{col}_sin", f"{col}_cos"])
        
        # 5. LLM-suggested features
        llm_features = self._get_llm_features(train_df, val_df, test_df, state)
        for feat in llm_features:
            if feat not in engineered_features:
                engineered_features.append(feat)
        
        # Save engineered data
        base_path = train_path.replace("scaled_train.parquet", "").replace("cleaned_train.parquet", "") if ("scaled_train.parquet" in train_path or "cleaned_train.parquet" in train_path) else f"{train_path.rsplit('/', 1)[0]}/"
        engineered_train_path = upload_to_s3(train_df.to_parquet(index=False), f"{base_path}engineered_train.parquet")
        engineered_val_path = upload_to_s3(val_df.to_parquet(index=False), f"{base_path}engineered_val.parquet")
        engineered_test_path = upload_to_s3(test_df.to_parquet(index=False), f"{base_path}engineered_test.parquet")
        
        return {
            "engineered_features": engineered_features,
            "engineered_train_path": engineered_train_path,
            "engineered_val_path": engineered_val_path,
            "engineered_test_path": engineered_test_path,
            "cleaned_train_path": engineered_train_path,
            "cleaned_val_path": engineered_val_path,
            "cleaned_test_path": engineered_test_path,
            "current_agent": self.name,
            "progress_pct": 50,
        }
    
    def _decompose_datetime(self, train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame, col: str) -> List[str]:
        """Decompose datetime column into components"""
        new_features = []
        for df in [train_df, val_df, test_df]:
            df[f"{col}_year"] = df[col].dt.year
            df[f"{col}_month"] = df[col].dt.month
            df[f"{col}_day"] = df[col].dt.day
            df[f"{col}_dayofweek"] = df[col].dt.dayofweek
            df[f"{col}_is_weekend"] = (df[col].dt.dayofweek >= 5).astype(int)
            df[f"{col}_quarter"] = df[col].dt.quarter
            if df[col].dt.hour.nunique() > 1:
                df[f"{col}_hour"] = df[col].dt.hour
        
        new_features = [f"{col}_year", f"{col}_month", f"{col}_day", 
                       f"{col}_dayofweek", f"{col}_is_weekend", f"{col}_quarter"]
        if train_df[col].dt.hour.nunique() > 1:
            new_features.append(f"{col}_hour")
        
        # Drop original datetime column
        for df in [train_df, val_df, test_df]:
            df.drop(columns=[col], inplace=True)
        
        return new_features
    
    def _get_llm_features(self, train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame, state: dict) -> List[str]:
        """Get feature engineering suggestions from LLM"""
        try:
            llm = get_llm()
            target_col = state.get("target_column")
            numeric_corr = {}
            if target_col and target_col in train_df.columns and pd.api.types.is_numeric_dtype(train_df[target_col]):
                num_df = train_df.select_dtypes(include=[np.number])
                if target_col in num_df.columns:
                    numeric_corr = num_df.corr()[target_col].to_dict()
            
            sample_cols = list(train_df.columns)[:15]
            if target_col and target_col in train_df.columns and target_col not in sample_cols:
                sample_cols.append(target_col)

            prompt = build_feature_strategy_prompt({
                "columns": sample_cols,
                "problem_type": state.get("problem_type", ""),
                "target_column": target_col or "",
                "sample_rows": train_df[sample_cols].head(3).to_dict(orient='records'),
                "correlations": dict(list(numeric_corr.items())[:15]),
            })
            
            response = llm.invoke(prompt)
            llm_output = validate_llm_output(response, FeatureStrategyOutput)
            
            # Apply safe suggestions (interaction terms only for now)
            new_features = []
            for interaction in llm_output.interaction_terms:
                try:
                    # Parse interaction like "col1 * col2"
                    if '*' in interaction:
                        parts = interaction.split('*')
                        col1 = parts[0].strip()
                        col2 = parts[1].strip()
                        if col1 in train_df.columns and col2 in train_df.columns:
                            for df in [train_df, val_df, test_df]:
                                df[interaction.replace(' ', '_').replace('*', '_x_')] = df[col1] * df[col2]
                            new_features.append(interaction.replace(' ', '_').replace('*', '_x_'))
                except Exception:
                    continue
            
            return new_features
        except Exception as e:
            logger.warning(f"LLM feature engineering failed: {e}")
            return []


feature_engineering_agent = FeatureEngineeringAgent()