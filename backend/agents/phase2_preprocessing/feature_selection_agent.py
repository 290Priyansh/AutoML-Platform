from backend.agents.base_agent import BaseAgent
from backend.orchestrator.state import PipelineState
from backend.mlops.artifact_store import download_from_s3, upload_to_s3
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression, RFECV, SelectFromModel
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LassoCV
from sklearn.feature_selection import VarianceThreshold
from statsmodels.stats.outliers_influence import variance_inflation_factor
import pandas as pd
import numpy as np
import io
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class FeatureSelectionAgent(BaseAgent):
    name: str = "feature_selection_agent"
    phase: str = "phase2_preprocessing"

    def run(self, state: PipelineState) -> Dict[str, Any]:
        train_path = state["cleaned_train_path"].replace("cleaned_train", "engineered_train")
        val_path = state["cleaned_val_path"].replace("cleaned_val", "engineered_val")
        test_path = state["cleaned_test_path"].replace("cleaned_test", "engineered_test")
        
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
        
        target_column = state["target_column"]
        problem_type = state["problem_type"]
        
        # Prepare X and y
        X_train = train_df.drop(columns=[target_column]) if target_column in train_df.columns else train_df
        y_train = train_df[target_column] if target_column in train_df.columns else None
        
        feature_names = X_train.columns.tolist()
        
        # Run all 5 selection methods
        votes = {feat: 0 for feat in feature_names}
        
        # 1. Mutual Information
        mi_features = self._mutual_info_selection(X_train, y_train, problem_type)
        for feat in mi_features:
            if feat in votes:
                votes[feat] += 1
        
        # 2. RFECV
        rfecv_features = self._rfecv_selection(X_train, y_train, problem_type)
        for feat in rfecv_features:
            if feat in votes:
                votes[feat] += 1
        
        # 3. LASSO
        lasso_features = self._lasso_selection(X_train, y_train)
        for feat in lasso_features:
            if feat in votes:
                votes[feat] += 1
        
        # 4. Correlation filter
        corr_features = self._correlation_filter(X_train, y_train)
        for feat in corr_features:
            if feat in votes:
                votes[feat] += 1
        
        # 5. VIF
        vif_features = self._vif_filter(X_train)
        for feat in vif_features:
            if feat in votes:
                votes[feat] += 1
        
        # Select features with >= 3 votes
        selected_features = [feat for feat, count in votes.items() if count >= 3]
        
        # Ensure minimum features retained (up to available features, target min 5)
        min_features = min(5, len(feature_names))
        if len(selected_features) < min_features:
            # Add top-voted features
            sorted_votes = sorted(votes.items(), key=lambda x: x[1], reverse=True)
            for feat, _ in sorted_votes:
                if feat not in selected_features:
                    selected_features.append(feat)
                if len(selected_features) >= min_features:
                    break
        
        # Keep only selected features + target
        keep_cols_train = [f for f in selected_features if f in train_df.columns]
        if target_column and target_column in train_df.columns:
            keep_cols_train.append(target_column)
            
        # Align val and test columns exactly to train_selected
        for col in keep_cols_train:
            if col not in val_df.columns:
                val_df[col] = 0.0
            if col not in test_df.columns:
                test_df[col] = 0.0
                
        train_selected = train_df[keep_cols_train]
        val_selected = val_df[keep_cols_train]
        test_selected = test_df[keep_cols_train]
        
        # Save selected data
        base_path = train_path.replace("engineered_train.parquet", "").replace("cleaned_train.parquet", "") if ("engineered_train.parquet" in train_path or "cleaned_train.parquet" in train_path) else f"{train_path.rsplit('/', 1)[0]}/"
        selected_train_path = upload_to_s3(train_selected.to_parquet(index=False), f"{base_path}selected_train.parquet")
        selected_val_path = upload_to_s3(val_selected.to_parquet(index=False), f"{base_path}selected_val.parquet")
        selected_test_path = upload_to_s3(test_selected.to_parquet(index=False), f"{base_path}selected_test.parquet")
        
        return {
            "selected_features": selected_features,
            "selected_train_path": selected_train_path,
            "selected_val_path": selected_val_path,
            "selected_test_path": selected_test_path,
            "cleaned_train_path": selected_train_path,
            "cleaned_val_path": selected_val_path,
            "cleaned_test_path": selected_test_path,
            "current_agent": self.name,
            "progress_pct": 80,
        }
    
    def _mutual_info_selection(self, X: pd.DataFrame, y: pd.Series, problem_type: str) -> List[str]:
        """Select features using mutual information"""
        if y is None:
            return X.columns.tolist()
        try:
            X_num = X.select_dtypes(include=[np.number])
            if X_num.shape[1] == 0:
                return X.columns.tolist()
            if problem_type == "classification":
                mi_scores = mutual_info_classif(X_num, y, random_state=42)
            else:
                mi_scores = mutual_info_regression(X_num, y, random_state=42)
            
            mi_df = pd.DataFrame({'feature': X_num.columns, 'score': mi_scores})
            mi_df = mi_df.sort_values('score', ascending=False)
            # Select top 50% or features with score > median
            threshold = mi_df['score'].median()
            return mi_df[mi_df['score'] >= threshold]['feature'].tolist()
        except Exception as e:
            logger.warning(f"Mutual info selection failed: {e}")
            return X.columns.tolist()
    
    def _rfecv_selection(self, X: pd.DataFrame, y: pd.Series, problem_type: str) -> List[str]:
        """Select features using RFECV"""
        if y is None:
            return X.columns.tolist()
        try:
            X_num = X.select_dtypes(include=[np.number])
            if X_num.shape[1] < 2:
                return X.columns.tolist()
            if problem_type == "classification":
                min_class_samples = y.value_counts().min() if hasattr(y, 'value_counts') else 2
                cv_splits = min(3, max(2, int(min_class_samples)))
                estimator = RandomForestClassifier(n_estimators=30, random_state=42, n_jobs=1)
            else:
                cv_splits = min(3, max(2, len(X) // 5))
                estimator = RandomForestRegressor(n_estimators=30, random_state=42, n_jobs=1)
            
            min_feat = min(5, X_num.shape[1])
            step = max(5, int(X_num.shape[1] * 0.1))
            selector = RFECV(estimator, step=step, cv=cv_splits, min_features_to_select=min_feat, n_jobs=1)
            selector.fit(X_num, y)
            return X_num.columns[selector.support_].tolist()
        except Exception as e:
            logger.warning(f"RFECV selection failed: {e}")
            return X.columns.tolist()
    
    def _lasso_selection(self, X: pd.DataFrame, y: pd.Series) -> List[str]:
        """Select features using LASSO"""
        if y is None:
            return X.columns.tolist()
        try:
            X_num = X.select_dtypes(include=[np.number])
            if X_num.shape[1] < 2:
                return X.columns.tolist()
            from sklearn.preprocessing import StandardScaler, LabelEncoder
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X_num)
            
            if not pd.api.types.is_numeric_dtype(y):
                y_lasso = LabelEncoder().fit_transform(y.astype(str))
            else:
                y_lasso = y
                
            lasso = LassoCV(cv=min(3, max(2, len(X) // 5)), random_state=42, max_iter=2000)
            lasso.fit(X_scaled, y_lasso)
            
            selector = SelectFromModel(lasso, prefit=True)
            selected = X_num.columns[selector.get_support()].tolist()
            if not selected and X_num.shape[1] > 0:
                best_idx = np.argmax(np.abs(lasso.coef_))
                selected = [X_num.columns[best_idx]]
            return selected
        except Exception as e:
            logger.warning(f"LASSO selection failed: {e}")
            return X.columns.tolist()
    
    def _correlation_filter(self, X: pd.DataFrame, y: pd.Series) -> List[str]:
        """Remove highly correlated features (|r| > 0.95)"""
        try:
            X_num = X.select_dtypes(include=[np.number])
            if X_num.shape[1] < 2:
                return X.columns.tolist()
            corr_matrix = X_num.corr().abs()
            upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
            
            y_is_num = y is not None and pd.api.types.is_numeric_dtype(y)
            
            to_drop = set()
            for col in upper.columns:
                if col in to_drop:
                    continue
                high_corr = upper[col][upper[col] > 0.95].index.tolist()
                for hc in high_corr:
                    corr_col_target = abs(X_num[col].corr(y)) if y_is_num else 0
                    corr_hc_target = abs(X_num[hc].corr(y)) if y_is_num else 0
                    if corr_col_target >= corr_hc_target:
                        to_drop.add(hc)
                    else:
                        to_drop.add(col)
            
            return [c for c in X.columns if c not in to_drop]
        except Exception as e:
            logger.warning(f"Correlation filter failed: {e}")
            return X.columns.tolist()
    
    def _vif_filter(self, X: pd.DataFrame) -> List[str]:
        """Remove features with VIF > 10"""
        try:
            X_numeric = X.select_dtypes(include=[np.number]).dropna(axis=1, how='any')
            if X_numeric.shape[1] < 2:
                return X.columns.tolist()
            if X_numeric.shape[1] > 50:
                # Correlation filter already pruned collinear pairs; VIF on >50 features is redundant and O(p^2)
                return X.columns.tolist()
            
            vif_data = pd.DataFrame()
            vif_data["feature"] = X_numeric.columns
            vif_data["VIF"] = [variance_inflation_factor(X_numeric.values, i) 
                              for i in range(X_numeric.shape[1])]
            
            keep = vif_data[vif_data["VIF"] <= 10]["feature"].tolist()
            return keep if keep else X.columns.tolist()
        except Exception as e:
            logger.warning(f"VIF filter failed: {e}")
            return X.columns.tolist()


feature_selection_agent = FeatureSelectionAgent()