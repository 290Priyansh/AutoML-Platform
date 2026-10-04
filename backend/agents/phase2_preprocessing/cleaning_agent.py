from backend.agents.base_agent import BaseAgent
from backend.orchestrator.state import PipelineState
from backend.mlops.artifact_store import download_from_s3, upload_to_s3
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
import pandas as pd
import numpy as np
import io
import joblib
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class OutlierCapper(BaseEstimator, TransformerMixin):
    """Cap outliers using IQR method"""
    def __init__(self, factor=1.5):
        self.factor = factor
        self.bounds_ = {}
        self.capped_columns_ = []
    
    def fit(self, X, y=None):
        self.bounds_ = {}
        self.capped_columns_ = []
        if isinstance(X, pd.DataFrame):
            X_df = X
            for col in X_df.columns:
                if pd.api.types.is_numeric_dtype(X_df[col]):
                    Q1 = X_df[col].quantile(0.25)
                    Q3 = X_df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower = float(Q1 - self.factor * IQR)
                    upper = float(Q3 + self.factor * IQR)
                    self.bounds_[col] = (lower, upper)
                    if ((X_df[col] < lower) | (X_df[col] > upper)).any():
                        self.capped_columns_.append(col)
        else:
            X_arr = np.asarray(X)
            for i in range(X_arr.shape[1]):
                col_vals = X_arr[:, i]
                if np.issubdtype(col_vals.dtype, np.number):
                    Q1 = np.nanpercentile(col_vals, 25)
                    Q3 = np.nanpercentile(col_vals, 75)
                    IQR = Q3 - Q1
                    lower = float(Q1 - self.factor * IQR)
                    upper = float(Q3 + self.factor * IQR)
                    self.bounds_[i] = (lower, upper)
                    if np.any((col_vals < lower) | (col_vals > upper)):
                        self.capped_columns_.append(i)
        return self
    
    def transform(self, X):
        if isinstance(X, pd.DataFrame):
            X_df = X.copy()
            for col, (lower, upper) in self.bounds_.items():
                if col in X_df.columns:
                    X_df[col] = X_df[col].clip(lower, upper)
            return X_df.values
        else:
            X_arr = np.array(X, copy=True)
            for idx, (lower, upper) in self.bounds_.items():
                if isinstance(idx, int) and idx < X_arr.shape[1]:
                    X_arr[:, idx] = np.clip(X_arr[:, idx], lower, upper)
            return X_arr

    def get_feature_names_out(self, input_features=None):
        if input_features is not None:
            return np.asarray(input_features, dtype=object)
        return np.array([f"x{i}" for i in range(len(self.bounds_))], dtype=object)


class CleaningAgent(BaseAgent):
    name: str = "cleaning_agent"
    phase: str = "phase2_preprocessing"

    def run(self, state: PipelineState) -> Dict[str, Any]:
        train_path = state["train_path"]
        val_path = state["val_path"]
        test_path = state["test_path"]
        target_column = state.get("target_column")
        
        # Load all splits
        train_df = pd.read_parquet(io.BytesIO(download_from_s3(train_path)))
        val_df = pd.read_parquet(io.BytesIO(download_from_s3(val_path)))
        test_df = pd.read_parquet(io.BytesIO(download_from_s3(test_path)))
        
        # Separate target from features
        X_train = train_df.drop(columns=[target_column]) if target_column and target_column in train_df.columns else train_df
        y_train = train_df[target_column] if target_column and target_column in train_df.columns else None
        
        X_val = val_df.drop(columns=[target_column]) if target_column and target_column in val_df.columns else val_df
        y_val = val_df[target_column] if target_column and target_column in val_df.columns else None
        
        X_test = test_df.drop(columns=[target_column]) if target_column and target_column in test_df.columns else test_df
        y_test = test_df[target_column] if target_column and target_column in test_df.columns else None
        
        # Build preprocessing pipeline fitted on train features only
        preprocessor = self._build_preprocessor(X_train)
        preprocessor.fit(X_train)
        
        # Transform all splits
        train_cleaned = self._apply_preprocessing(X_train, preprocessor)
        val_cleaned = self._apply_preprocessing(X_val, preprocessor)
        test_cleaned = self._apply_preprocessing(X_test, preprocessor)
        
        # Re-attach target column
        if y_train is not None:
            train_cleaned[target_column] = y_train.values
        if y_val is not None:
            val_cleaned[target_column] = y_val.values
        if y_test is not None:
            test_cleaned[target_column] = y_test.values
        
        # Save cleaned splits
        base_path = train_path.replace("train.parquet", "")
        cleaned_train_path = upload_to_s3(
            train_cleaned.to_parquet(index=False),
            f"{base_path}cleaned_train.parquet"
        )
        cleaned_val_path = upload_to_s3(
            val_cleaned.to_parquet(index=False),
            f"{base_path}cleaned_val.parquet"
        )
        cleaned_test_path = upload_to_s3(
            test_cleaned.to_parquet(index=False),
            f"{base_path}cleaned_test.parquet"
        )
        
        # Save preprocessor
        preprocessor_buffer = io.BytesIO()
        joblib.dump(preprocessor, preprocessor_buffer)
        preprocessor_buffer.seek(0)
        preprocessor_path = upload_to_s3(
            preprocessor_buffer.getvalue(),
            f"{base_path}preprocessor.joblib"
        )
        
        return {
            "cleaned_train_path": cleaned_train_path,
            "cleaned_val_path": cleaned_val_path,
            "cleaned_test_path": cleaned_test_path,
            "preprocessor_path": preprocessor_path,
            "current_agent": self.name,
            "progress_pct": 55,
        }
    
    def _build_preprocessor(self, train_df: pd.DataFrame) -> Pipeline:
        """Build sklearn pipeline for cleaning without duplicating columns"""
        numeric_cols = train_df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = train_df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        transformers = []
        
        if numeric_cols:
            missing_pct = train_df[numeric_cols].isnull().mean().max() if len(numeric_cols) > 0 else 0
            num_steps = []
            if missing_pct > 0.05:
                num_steps.append(('imputer', KNNImputer(n_neighbors=5)))
            else:
                num_steps.append(('imputer', SimpleImputer(strategy='median')))
            num_steps.append(('capper', OutlierCapper(factor=1.5)))
            transformers.append(('num_pipe', Pipeline(num_steps), numeric_cols))
        
        if categorical_cols:
            cat_pipe = Pipeline([
                ('imputer', SimpleImputer(strategy='most_frequent'))
            ])
            transformers.append(('cat_pipe', cat_pipe, categorical_cols))
        
        if transformers:
            return Pipeline([
                ('cleaner', ColumnTransformer(transformers, remainder='passthrough', verbose_feature_names_out=False))
            ])
        else:
            return Pipeline([('cleaner', 'passthrough')])
    
    def _apply_preprocessing(self, df: pd.DataFrame, preprocessor) -> pd.DataFrame:
        """Apply fitted preprocessor to dataframe while maintaining proper column names"""
        transformed = preprocessor.transform(df)
        try:
            feature_names = list(preprocessor.get_feature_names_out())
        except Exception:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            passthrough_cols = [c for c in df.columns if c not in numeric_cols and c not in categorical_cols]
            expected_cols = numeric_cols + categorical_cols + passthrough_cols
            if len(expected_cols) == transformed.shape[1]:
                feature_names = expected_cols
            else:
                feature_names = [f"col_{i}" for i in range(transformed.shape[1])]
        return pd.DataFrame(transformed, columns=feature_names, index=df.index)


cleaning_agent = CleaningAgent()