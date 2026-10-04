from backend.agents.base_agent import BaseAgent
from backend.orchestrator.state import PipelineState
from backend.mlops.artifact_store import download_from_s3, upload_to_s3
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False
import pandas as pd
import numpy as np
import io
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class NLPAgent(BaseAgent):
    name: str = "nlp_agent"
    phase: str = "phase2_preprocessing"

    def run(self, state: PipelineState) -> Dict[str, Any]:
        text_columns = state.get("text_columns", [])
        
        if not text_columns:
            return {
                "text_columns": [],
                "embedding_columns": [],
                "current_agent": self.name,
                "progress_pct": 60,
            }
        
        # Load cleaned train data
        train_path = state["cleaned_train_path"]
        train_df = pd.read_parquet(io.BytesIO(download_from_s3(train_path)))
        
        embedding_columns = []
        model = None
        if SENTENCE_TRANSFORMERS_AVAILABLE and SentenceTransformer is not None:
            try:
                model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer: {e}")

        fitted_transformers = {}
        
        for col in text_columns:
            if col not in train_df.columns:
                continue
            
            unique_vals = train_df[col].nunique()
            
            if unique_vals < 100 or model is None:
                # Low cardinality or embedding fallback: TF-IDF
                from sklearn.feature_extraction.text import TfidfVectorizer
                tfidf = TfidfVectorizer(max_features=min(500, max(10, unique_vals * 2)), stop_words='english')
                tfidf_matrix = tfidf.fit_transform(train_df[col].fillna(''))
                col_names = [f"{col}_tfidf_{i}" for i in range(tfidf_matrix.shape[1])]
                
                tfidf_df = pd.DataFrame(
                    tfidf_matrix.toarray(),
                    columns=col_names,
                    index=train_df.index
                )
                train_df = pd.concat([train_df.drop(columns=[col]), tfidf_df], axis=1)
                embedding_columns.extend(col_names)
                fitted_transformers[col] = ('tfidf', tfidf, col_names)
            else:
                # High cardinality: embeddings
                embeddings = model.encode(train_df[col].fillna('').tolist(), show_progress_bar=False)
                col_names = [f"{col}_emb_{i}" for i in range(embeddings.shape[1])]
                emb_df = pd.DataFrame(
                    embeddings,
                    columns=col_names,
                    index=train_df.index
                )
                train_df = pd.concat([train_df.drop(columns=[col]), emb_df], axis=1)
                embedding_columns.extend(col_names)
                fitted_transformers[col] = ('embeddings', model, col_names)
        
        # Save updated train dataframe
        base_path = train_path.replace("cleaned_train.parquet", "")
        upload_to_s3(
            train_df.to_parquet(index=False),
            f"{base_path}cleaned_train.parquet"
        )
        
        # Process val and test with exact same fitted transformers
        for split_name, split_path in [("val", state.get("cleaned_val_path", "")), ("test", state.get("cleaned_test_path", ""))]:
            if not split_path:
                continue
            split_df = pd.read_parquet(io.BytesIO(download_from_s3(split_path)))
            
            for col, (t_type, transformer, col_names) in fitted_transformers.items():
                if col not in split_df.columns:
                    continue
                
                if t_type == 'tfidf':
                    tfidf_matrix = transformer.transform(split_df[col].fillna(''))
                    feat_df = pd.DataFrame(
                        tfidf_matrix.toarray(),
                        columns=col_names,
                        index=split_df.index
                    )
                else:
                    embeddings = transformer.encode(split_df[col].fillna('').tolist(), show_progress_bar=False)
                    feat_df = pd.DataFrame(
                        embeddings,
                        columns=col_names,
                        index=split_df.index
                    )
                split_df = pd.concat([split_df.drop(columns=[col]), feat_df], axis=1)
            
            upload_to_s3(
                split_df.to_parquet(index=False),
                f"{base_path}cleaned_{split_name}.parquet"
            )
        
        return {
            "text_columns": text_columns,
            "embedding_columns": embedding_columns,
            "current_agent": self.name,
            "progress_pct": 60,
        }


nlp_agent = NLPAgent()