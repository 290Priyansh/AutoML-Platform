from backend.agents.base_agent import BaseAgent
from backend.orchestrator.state import PipelineState
from backend.mlops.artifact_store import download_from_s3, upload_to_s3
try:
    from imblearn.over_sampling import SMOTE, ADASYN
    from imblearn.combine import SMOTETomek
    from imblearn.under_sampling import TomekLinks
    IMBLEARN_AVAILABLE = True
except ImportError:
    SMOTE, ADASYN, SMOTETomek, TomekLinks = None, None, None, None
    IMBLEARN_AVAILABLE = False
import pandas as pd
import numpy as np
import io
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ImbalanceHandlerAgent(BaseAgent):
    name: str = "imbalance_handler_agent"
    phase: str = "phase2_preprocessing"

    def run(self, state: PipelineState) -> Dict[str, Any]:
        problem_type = state["problem_type"]
        train_path = state.get("selected_train_path") or state["cleaned_train_path"].replace("cleaned_train", "selected_train")
        base_path = train_path.replace("selected_train.parquet", "")
        resampled_path = f"{base_path}resampled_train.parquet"
        
        # Only handle classification
        if problem_type != "classification":
            try:
                train_bytes = download_from_s3(train_path)
                upload_to_s3(train_bytes, resampled_path)
            except Exception as e:
                logger.warning(f"Could not copy train data for non-classification: {e}")
            return {
                "imbalance_strategy": "none",
                "resampled_train_path": resampled_path,
                "current_agent": self.name,
                "progress_pct": 85,
            }
        
        # Load train data with fallback
        try:
            train_bytes = download_from_s3(train_path)
        except Exception:
            train_path = state["cleaned_train_path"]
            train_bytes = download_from_s3(train_path)
            
        train_df = pd.read_parquet(io.BytesIO(train_bytes))
        target_column = state["target_column"]
        
        # Check class balance
        class_counts = train_df[target_column].value_counts()
        if len(class_counts) < 2 or class_counts.max() == 0:
            upload_to_s3(train_bytes, resampled_path)
            return {
                "imbalance_strategy": "none",
                "resampled_train_path": resampled_path,
                "current_agent": self.name,
                "progress_pct": 85,
            }
            
        minority_ratio = class_counts.min() / class_counts.max()
        
        # Only activate if minority ratio < 0.2
        if minority_ratio >= 0.2:
            upload_to_s3(train_bytes, resampled_path)
            return {
                "imbalance_strategy": "none",
                "resampled_train_path": resampled_path,
                "current_agent": self.name,
                "progress_pct": 85,
            }
        
        # Determine strategy
        n_samples = len(train_df)
        
        if not IMBLEARN_AVAILABLE or n_samples > 100000:
            # Too large or library not available, use class weights
            strategy = "class_weight"
        elif minority_ratio > 0.1:
            strategy = "smote"
        elif minority_ratio > 0.05:
            strategy = "adasyn"
        else:
            strategy = "smote_tomek"
        
        # Apply resampling (only to training set)
        X = train_df.drop(columns=[target_column])
        y = train_df[target_column]
        
        try:
            if strategy == "smote" and SMOTE is not None:
                sampler = SMOTE(random_state=42)
                X_resampled, y_resampled = sampler.fit_resample(X, y)
            elif strategy == "adasyn" and ADASYN is not None:
                sampler = ADASYN(random_state=42)
                X_resampled, y_resampled = sampler.fit_resample(X, y)
            elif strategy == "smote_tomek" and SMOTETomek is not None:
                sampler = SMOTETomek(random_state=42)
                X_resampled, y_resampled = sampler.fit_resample(X, y)
            else:
                # class_weight - no resampling
                strategy = "class_weight"
                X_resampled, y_resampled = X, y
        except Exception as e:
            logger.warning(f"Resampling failed with {strategy}, falling back to class_weight: {e}")
            strategy = "class_weight"
            X_resampled, y_resampled = X, y
        
        # Reconstruct dataframe
        if strategy != "class_weight":
            resampled_df = pd.DataFrame(X_resampled, columns=X.columns).copy()
            resampled_df[target_column] = y_resampled
            
            # Save resampled train data
            upload_to_s3(resampled_df.to_parquet(index=False), resampled_path)
            
            # Log class distribution
            logger.info(f"Class distribution before: {class_counts.to_dict()}")
            logger.info(f"Class distribution after: {resampled_df[target_column].value_counts().to_dict()}")
        else:
            # Just use original train path
            upload_to_s3(train_df.to_parquet(index=False), resampled_path)
        
        return {
            "imbalance_strategy": strategy,
            "resampled_train_path": resampled_path,
            "cleaned_train_path": resampled_path,
            "current_agent": self.name,
            "progress_pct": 85,
        }


imbalance_handler_agent = ImbalanceHandlerAgent()