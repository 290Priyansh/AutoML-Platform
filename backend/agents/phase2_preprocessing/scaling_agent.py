from backend.agents.base_agent import BaseAgent
from backend.orchestrator.state import PipelineState
from backend.mlops.artifact_store import download_from_s3, upload_to_s3
from backend.llm.router import get_llm
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.compose import ColumnTransformer
import pandas as pd
import numpy as np
import io
import joblib
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ScalingAgent(BaseAgent):
    name: str = "scaling_agent"
    phase: str = "phase2_preprocessing"

    def run(self, state: PipelineState) -> Dict[str, Any]:
        train_path = state["cleaned_train_path"].replace("cleaned_train", "encoded_train")
        val_path = state["cleaned_val_path"].replace("cleaned_val", "encoded_val")
        test_path = state["cleaned_test_path"].replace("cleaned_test", "encoded_test")
        
        # Load data with fallback to cleaned_train if encoded_train is not present
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
        
        # Get numeric feature columns (excluding target)
        target_column = state["target_column"]
        numeric_cols = train_df.select_dtypes(include=[np.number]).columns.tolist()
        feature_cols = [c for c in numeric_cols if c != target_column]
        
        base_path = train_path.replace("encoded_train.parquet", "").replace("cleaned_train.parquet", "")
        
        if not feature_cols:
            scaled_train_path = upload_to_s3(train_df.to_parquet(index=False), f"{base_path}scaled_train.parquet")
            scaled_val_path = upload_to_s3(val_df.to_parquet(index=False), f"{base_path}scaled_val.parquet")
            scaled_test_path = upload_to_s3(test_df.to_parquet(index=False), f"{base_path}scaled_test.parquet")
            return {
                "scaler_type": "none",
                "scaled_train_path": scaled_train_path,
                "scaled_val_path": scaled_val_path,
                "scaled_test_path": scaled_test_path,
                "cleaned_train_path": scaled_train_path,
                "cleaned_val_path": scaled_val_path,
                "cleaned_test_path": scaled_test_path,
                "preprocessor_path": state.get("preprocessor_path", ""),
                "current_agent": self.name,
                "progress_pct": 45,
            }
        
        # Determine scaler type using LLM for nuanced decision
        user_model_preference = state.get("user_model_preference")
        eda_report = state.get("eda_report", {})
        problem_type = state.get("problem_type", "")
        
        scaler_type = self._choose_scaler_with_llm(
            user_model_preference, eda_report, train_df[feature_cols], problem_type
        )
        
        if scaler_type == "none":
            scaler = None
            scaled_train = train_df
            scaled_val = val_df
            scaled_test = test_df
        else:
            if scaler_type == "standard":
                scaler = StandardScaler()
            elif scaler_type == "minmax":
                scaler = MinMaxScaler()
            elif scaler_type == "robust":
                scaler = RobustScaler()
            else:
                scaler = StandardScaler()
            
            scaler.fit(train_df[feature_cols])
            
            scaled_train = train_df.copy()
            scaled_val = val_df.copy()
            scaled_test = test_df.copy()
            
            scaled_train[feature_cols] = scaler.transform(train_df[feature_cols])
            scaled_val[feature_cols] = scaler.transform(val_df[feature_cols])
            scaled_test[feature_cols] = scaler.transform(test_df[feature_cols])
        
        # Save scaled data
        scaled_train_path = upload_to_s3(scaled_train.to_parquet(index=False), f"{base_path}scaled_train.parquet")
        scaled_val_path = upload_to_s3(scaled_val.to_parquet(index=False), f"{base_path}scaled_val.parquet")
        scaled_test_path = upload_to_s3(scaled_test.to_parquet(index=False), f"{base_path}scaled_test.parquet")
        
        # Save scaler
        if scaler:
            scaler_buffer = io.BytesIO()
            joblib.dump(scaler, scaler_buffer)
            scaler_buffer.seek(0)
            scaler_path = upload_to_s3(scaler_buffer.getvalue(), f"{base_path}scaler.joblib")
        else:
            scaler_path = ""
        
        return {
            "scaler_type": scaler_type,
            "scaled_train_path": scaled_train_path,
            "scaled_val_path": scaled_val_path,
            "scaled_test_path": scaled_test_path,
            "cleaned_train_path": scaled_train_path,
            "cleaned_val_path": scaled_val_path,
            "cleaned_test_path": scaled_test_path,
            "preprocessor_path": scaler_path or state.get("preprocessor_path", ""),
            "current_agent": self.name,
            "progress_pct": 45,
        }
    
    def _choose_scaler_with_llm(self, model_preference: str, eda_report: dict, 
                                 features: pd.DataFrame, problem_type: str) -> str:
        """Choose scaler using heuristic + LLM for nuanced decisions"""
        
        # Quick heuristic for clear cases
        tree_models = ['randomforest', 'xgb', 'lgbm', 'adaboost', 'gradientboosting', 'decisiontree']
        if model_preference and any(m in model_preference.lower() for m in tree_models):
            return "none"
        
        # If model preference specifies linear/NN, use appropriate scaler
        linear_models = ['logistic', 'linear', 'ridge', 'lasso', 'svm', 'svr', 'knn']
        if model_preference and any(m in model_preference.lower() for m in linear_models):
            if self._has_heavy_outliers(features):
                return "robust"
            return "standard"
        
        nn_models = ['mlp', 'neural']
        if model_preference and any(m in model_preference.lower() for m in nn_models):
            return "minmax"
        
        # Auto mode: use LLM to decide based on data characteristics
        try:
            llm = get_llm(task="reasoning")
            
            # Summarize data for LLM (compact summary to respect token budget)
            sub_cols = list(features.columns)[:15]
            outlier_info = {}
            for col in sub_cols:
                Q1 = features[col].quantile(0.25)
                Q3 = features[col].quantile(0.75)
                IQR = Q3 - Q1
                if IQR > 0:
                    outliers = ((features[col] < Q1 - 1.5*IQR) | (features[col] > Q3 + 1.5*IQR)).sum()
                    outlier_info[col] = round(float(outliers / len(features)), 3)
            
            skew_info = {c: round(float(v), 3) for c, v in features[sub_cols].skew().items()}
            
            prompt = f"""You are an ML preprocessing expert. Choose the best scaler for this dataset.

Problem Type: {problem_type}
Model Family: Auto (will train Linear, Tree, and Neural models)
Total features: {len(features.columns)}
Sample feature names: {sub_cols}

Sample Data Characteristics:
- Outlier ratios: {outlier_info}
- Skewness: {skew_info}
- Dtypes: {str({c: str(t) for c, t in features[sub_cols].dtypes.items()})}

Available scalers:
1. "none" - No scaling (for tree-based models: RF, XGB, LGBM)
2. "standard" - StandardScaler (zero mean, unit variance) - best for linear models, SVMs
3. "minmax" - MinMaxScaler (0-1 range) - best for neural networks, when bounds matter
4. "robust" - RobustScaler (median/IQR) - best when heavy outliers present

Respond with JSON:
{{
  "scaler": "standard|minmax|robust|none",
  "reasoning": "explanation"
}}"""
            
            response = llm.invoke(prompt)
            import json
            content = response.content if hasattr(response, "content") else str(response)
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(content[start:end])
                scaler = result.get("scaler", "standard")
                logger.info(f"LLM chose scaler: {scaler} - {result.get('reasoning', '')}")
                return scaler
        except Exception as e:
            logger.warning(f"LLM scaler selection failed: {e}")
        
        # Fallback heuristic
        return self._fallback_scaler_choice(features)
    
    def _fallback_scaler_choice(self, features: pd.DataFrame) -> str:
        if self._has_heavy_outliers(features):
            return "robust"
        return "standard"
    
    def _has_heavy_outliers(self, features: pd.DataFrame) -> bool:
        outlier_ratios = []
        for col in features.columns:
            Q1 = features[col].quantile(0.25)
            Q3 = features[col].quantile(0.75)
            IQR = Q3 - Q1
            if IQR > 0:
                outliers = ((features[col] < Q1 - 1.5*IQR) | (features[col] > Q3 + 1.5*IQR)).sum()
                outlier_ratios.append(outliers / len(features))
        return np.mean(outlier_ratios) > 0.05 if outlier_ratios else False


scaling_agent = ScalingAgent()