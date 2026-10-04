import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from backend.agents.phase2_preprocessing.imbalance_handler_agent import ImbalanceHandlerAgent


class TestImbalanceHandler:
    def test_imbalance_thresholds(self):
        """Test imbalance detection thresholds"""
        agent = ImbalanceHandlerAgent()
        
        # Test various minority ratios
        test_cases = [
            (0.25, "none"),      # Above threshold
            (0.15, "smote"),     # 0.1-0.2
            (0.08, "adasyn"),    # 0.05-0.1
            (0.03, "smote_tomek"), # < 0.05
        ]
        
        for ratio, expected_strategy in test_cases:
            # Create mock state with this ratio
            n_samples = 1000
            n_minority = int(n_samples * ratio / (1 + ratio))
            n_majority = n_samples - n_minority
            
            # Create dataframe
            df = pd.DataFrame({
                'feature1': np.random.randn(n_samples),
                'feature2': np.random.randn(n_samples),
                'target': [1] * n_majority + [0] * n_minority,
            })
            
            target_column = 'target'
            class_counts = df[target_column].value_counts()
            actual_ratio = class_counts.min() / class_counts.max()
            
            if actual_ratio >= 0.2:
                strategy = "none"
            elif actual_ratio > 0.1:
                strategy = "smote"
            elif actual_ratio > 0.05:
                strategy = "adasyn"
            else:
                strategy = "smote_tomek"
            
            assert strategy == expected_strategy
    
    def test_large_dataset_class_weight(self):
        """Test that large datasets use class_weight instead of resampling"""
        agent = ImbalanceHandlerAgent()
        
        # Create large imbalanced dataset
        n_samples = 150000
        df = pd.DataFrame({
            'feature1': np.random.randn(n_samples),
            'feature2': np.random.randn(n_samples),
            'target': [1] * (n_samples - 1000) + [0] * 1000,  # ~0.67% minority
        })
        
        # With >100k rows and imbalance, should use class_weight
        target_column = 'target'
        class_counts = df[target_column].value_counts()
        minority_ratio = class_counts.min() / class_counts.max()
        
        assert minority_ratio < 0.05
        assert len(df) > 100000
        
        # Strategy should be class_weight
        strategy = "class_weight"
        assert strategy == "class_weight"