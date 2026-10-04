from backend.agents.base_agent import BaseAgent
from backend.orchestrator.state import PipelineState
from backend.mlops.artifact_store import download_from_s3, upload_to_s3
from backend.llm.router import get_llm
from backend.llm.prompts.encoding_decision import build_prompt as build_encoding_prompt
from backend.llm.guardrails import validate_llm_output, EncodingDecisionOutput
try:
    import category_encoders as ce
    CATEGORY_ENCODERS_AVAILABLE = True
except ImportError:
    ce = None
    CATEGORY_ENCODERS_AVAILABLE = False
from sklearn.preprocessing import OrdinalEncoder, OneHotEncoder
try:
    from sklearn.preprocessing import TargetEncoder as SklearnTargetEncoder
except ImportError:
    SklearnTargetEncoder = None
from sklearn.compose import ColumnTransformer
import pandas as pd
import numpy as np
import io
import joblib
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class EncodingAgent(BaseAgent):
    name: str = "encoding_agent"
    phase: str = "phase2_preprocessing"

    def run(self, state: PipelineState) -> Dict[str, Any]:
        train_path = state["cleaned_train_path"]
        val_path = state["cleaned_val_path"]
        test_path = state["cleaned_test_path"]
        feature_columns = state["feature_columns"]
        problem_type = state["problem_type"]
        
        # Load data
        train_df = pd.read_parquet(io.BytesIO(download_from_s3(train_path)))
        val_df = pd.read_parquet(io.BytesIO(download_from_s3(val_path)))
        test_df = pd.read_parquet(io.BytesIO(download_from_s3(test_path)))
        
        # Identify categorical columns in feature_columns
        categorical_cols = []
        for col in feature_columns:
            if col in train_df.columns and train_df[col].dtype in ['object', 'category']:
                categorical_cols.append(col)
        
        target_column = state.get("target_column")
        y_train = train_df[target_column] if target_column and target_column in train_df.columns else None
        y_val = val_df[target_column] if target_column and target_column in val_df.columns else None
        y_test = test_df[target_column] if target_column and target_column in test_df.columns else None

        X_train = train_df.drop(columns=[target_column]) if target_column and target_column in train_df.columns else train_df
        X_val = val_df.drop(columns=[target_column]) if target_column and target_column in val_df.columns else val_df
        X_test = test_df.drop(columns=[target_column]) if target_column and target_column in test_df.columns else test_df

        encoding_map = {}
        transformers = []
        
        for col in categorical_cols:
            if col == target_column:
                continue
            cardinality = train_df[col].nunique()
            sample_values = train_df[col].dropna().unique()[:20].tolist()
            
            # Determine encoding strategy (heuristic + LLM for ambiguous cases)
            strategy = self._determine_encoding_strategy(
                col, cardinality, sample_values, problem_type, state.get("user_model_preference"), series=train_df[col]
            )
            # If target encoding selected but target is missing, fallback to binary
            if strategy == "target" and y_train is None:
                strategy = "binary"
            encoding_map[col] = strategy
            
            if strategy == "onehot":
                if CATEGORY_ENCODERS_AVAILABLE and ce is not None:
                    trans = ce.OneHotEncoder(cols=[col], use_cat_names=True)
                else:
                    trans = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
                transformers.append((f"onehot_{col}", trans, [col]))
            elif strategy == "target":
                if CATEGORY_ENCODERS_AVAILABLE and ce is not None:
                    trans = ce.TargetEncoder(cols=[col])
                elif SklearnTargetEncoder is not None:
                    trans = SklearnTargetEncoder(smooth="auto", cv=5)
                else:
                    trans = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
                transformers.append((f"target_{col}", trans, [col]))
            elif strategy == "binary":
                if CATEGORY_ENCODERS_AVAILABLE and ce is not None:
                    trans = ce.BinaryEncoder(cols=[col])
                else:
                    trans = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
                transformers.append((f"binary_{col}", trans, [col]))
            elif strategy == "ordinal":
                transformers.append((
                    f"ordinal_{col}",
                    OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1),
                    [col]
                ))
            elif strategy == "hash":
                if CATEGORY_ENCODERS_AVAILABLE and ce is not None:
                    trans = ce.HashingEncoder(cols=[col], n_components=8)
                else:
                    trans = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
                transformers.append((f"hash_{col}", trans, [col]))
        
        # Build and fit encoder pipeline
        if transformers:
            encoder = ColumnTransformer(transformers, remainder='passthrough', verbose_feature_names_out=False)
            try:
                encoder.fit(X_train, y=y_train)
            except Exception as e:
                logger.warning(f"Encoder fit with target failed ({e}), falling back to OrdinalEncoder")
                safe_transformers = []
                for name, trans, cols in transformers:
                    safe_transformers.append((
                        f"safe_ordinal_{cols[0]}",
                        OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1),
                        cols
                    ))
                encoder = ColumnTransformer(safe_transformers, remainder='passthrough', verbose_feature_names_out=False)
                encoder.fit(X_train)
            
            # Transform all splits
            train_encoded = self._transform_df(X_train, encoder)
            val_encoded = self._transform_df(X_val, encoder)
            test_encoded = self._transform_df(X_test, encoder)
            
            if y_train is not None:
                train_encoded[target_column] = y_train.values
            if y_val is not None:
                val_encoded[target_column] = y_val.values
            if y_test is not None:
                test_encoded[target_column] = y_test.values
            
            # Save encoded data
            base_path = train_path.replace("cleaned_train.parquet", "") if "cleaned_train.parquet" in train_path else f"{train_path.rsplit('/', 1)[0]}/"
            encoded_train_path = upload_to_s3(train_encoded.to_parquet(index=False), f"{base_path}encoded_train.parquet")
            encoded_val_path = upload_to_s3(val_encoded.to_parquet(index=False), f"{base_path}encoded_val.parquet")
            encoded_test_path = upload_to_s3(test_encoded.to_parquet(index=False), f"{base_path}encoded_test.parquet")
            
            # Save encoder
            encoder_buffer = io.BytesIO()
            joblib.dump(encoder, encoder_buffer)
            encoder_buffer.seek(0)
            encoder_path = upload_to_s3(encoder_buffer.getvalue(), f"{base_path}encoder.joblib")
        else:
            encoder_path = ""
            base_path = train_path.replace("cleaned_train.parquet", "") if "cleaned_train.parquet" in train_path else f"{train_path.rsplit('/', 1)[0]}/"
            encoded_train_path = upload_to_s3(train_df.to_parquet(index=False), f"{base_path}encoded_train.parquet")
            encoded_val_path = upload_to_s3(val_df.to_parquet(index=False), f"{base_path}encoded_val.parquet")
            encoded_test_path = upload_to_s3(test_df.to_parquet(index=False), f"{base_path}encoded_test.parquet")
        
        return {
            "encoding_map": encoding_map,
            "encoded_train_path": encoded_train_path,
            "encoded_val_path": encoded_val_path,
            "encoded_test_path": encoded_test_path,
            "cleaned_train_path": encoded_train_path,
            "cleaned_val_path": encoded_val_path,
            "cleaned_test_path": encoded_test_path,
            "preprocessor_path": encoder_path or state.get("preprocessor_path", ""),
            "current_agent": self.name,
            "progress_pct": 40,
        }
    
    def _determine_encoding_strategy(self, col: str, cardinality: int, sample_values: List, 
                                     problem_type: str, model_preference: str, series: pd.Series = None) -> str:
        """Determine encoding strategy using heuristic + LLM for ambiguous cases"""
        
        # Clear heuristic rules
        if cardinality <= 2:
            return "onehot"  # Binary categorical
        if cardinality <= 10:
            return "onehot"
        if cardinality > 100:
            return "hash"  # High cardinality - hashing
        
        # Ambiguous zone (10-100): use LLM for decision
        if 10 < cardinality <= 100:
            # Check if ordinal
            if self._is_ordinal(col, series):
                return "ordinal"
            
            # For tree models, target encoding often works well
            tree_models = ['randomforest', 'xgb', 'lgbm', 'gradientboosting', 'adaboost']
            if model_preference and any(m in model_preference.lower() for m in tree_models):
                return "target"
            
            # Use LLM for final decision
            try:
                llm = get_llm(task="reasoning")
                prompt = build_encoding_prompt({
                    "column_name": col,
                    "cardinality": cardinality,
                    "sample_values": sample_values,
                    "problem_type": problem_type,
                    "model_family": "tree" if model_preference and any(m in model_preference.lower() for m in tree_models) else "linear",
                })
                response = llm.invoke(prompt)
                from backend.llm.guardrails import validate_llm_output, EncodingDecisionOutput
                llm_output = validate_llm_output(response, EncodingDecisionOutput)
                return llm_output.encoding_strategy
            except Exception as e:
                logger.warning(f"LLM encoding decision failed for {col}: {e}")
        
        # Default fallback
        if cardinality <= 50:
            return "target"
        return "binary"
    
    def _is_ordinal(self, col_name: str, series: pd.Series = None) -> bool:
        """Detect if column is ordinal based on name and values"""
        ordinal_keywords = ['size', 'grade', 'level', 'rating', 'tier', 'rank', 'priority', 'severity', 'stage', 'phase']
        col_lower = col_name.lower()
        if any(kw in col_lower for kw in ordinal_keywords):
            return True
        if series is not None:
            # Check if values look ordered (e.g., low/medium/high)
            unique_vals = set(str(v).lower() for v in series.dropna().unique())
            ordered_sets = [
                {'low', 'medium', 'high'},
                {'small', 'medium', 'large'},
                {'poor', 'fair', 'good', 'excellent'},
                {'bronze', 'silver', 'gold', 'platinum'},
            ]
            for ordered in ordered_sets:
                if unique_vals.issubset(ordered) or ordered.issubset(unique_vals):
                    return True
        return False
    
    def _transform_df(self, df: pd.DataFrame, encoder) -> pd.DataFrame:
        transformed = encoder.transform(df)
        if hasattr(transformed, "toarray"):
            transformed = transformed.toarray()
        try:
            feature_names = encoder.get_feature_names_out()
        except Exception:
            feature_names = [f"col_{i}" for i in range(transformed.shape[1])]
        return pd.DataFrame(transformed, columns=feature_names, index=df.index)


encoding_agent = EncodingAgent()