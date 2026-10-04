from backend.agents.base_agent import BaseAgent
from backend.orchestrator.state import PipelineState
from backend.mlops.artifact_store import download_from_s3, upload_to_s3
import pandas as pd
import chardet
import io
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class IngestionAgent(BaseAgent):
    name: str = "ingestion_agent"
    phase: str = "phase1_understanding"

    def run(self, state: PipelineState) -> Dict[str, Any]:
        raw_data_path = state["raw_data_path"]
        data_source_type = state["data_source_type"]
        
        # Download file from S3
        file_bytes = download_from_s3(raw_data_path)
        
        if data_source_type == "csv":
            df = self._load_csv(file_bytes)
        elif data_source_type == "pdf":
            df = self._load_pdf(file_bytes)
        elif data_source_type == "url":
            df = self._load_url(state.get("url", ""))
        else:
            raise ValueError(f"Unknown data source type: {data_source_type}")
        
        # Infer schema
        schema = {col: str(dtype) for col, dtype in df.dtypes.items()}
        row_count = len(df)
        col_count = len(df.columns)
        
        # Save as parquet to S3
        parquet_buffer = io.BytesIO()
        df.to_parquet(parquet_buffer, index=False)
        parquet_buffer.seek(0)
        
        if "raw_data" in raw_data_path:
            dataframe_key = raw_data_path.replace("raw_data", "dataframe").replace(".csv", ".parquet").replace(".pdf", ".parquet").replace(".txt", ".parquet")
        else:
            base = raw_data_path.rsplit(".", 1)[0] if "." in raw_data_path else raw_data_path
            dataframe_key = f"{base}_dataframe.parquet"
        if not dataframe_key.endswith(".parquet"):
            dataframe_key += ".parquet"

        dataframe_path = upload_to_s3(parquet_buffer.getvalue(), dataframe_key)
        
        # Detect text columns for NLP agent
        text_columns = []
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].apply(lambda x: isinstance(x, str) and len(str(x).split()) > 5).mean() > 0.5:
                text_columns.append(col)
        
        return {
            "dataframe_path": dataframe_path,
            "schema": schema,
            "row_count": row_count,
            "col_count": col_count,
            "text_columns": text_columns,
            "current_agent": self.name,
            "progress_pct": 10,
        }
    
    def _load_csv(self, file_bytes: bytes) -> pd.DataFrame:
        # Detect encoding
        detected = chardet.detect(file_bytes)
        encoding = detected.get('encoding', 'utf-8')
        
        try:
            df = pd.read_csv(io.BytesIO(file_bytes), encoding=encoding)
        except UnicodeDecodeError:
            # Fallback to utf-8 with error handling
            df = pd.read_csv(io.BytesIO(file_bytes), encoding='utf-8', on_bad_lines='skip')
        
        return df
    
    def _load_pdf(self, file_bytes: bytes) -> pd.DataFrame:
        import pdfplumber
        import camelot
        
        # Try pdfplumber first (text-based PDFs)
        tables = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    tables.append(pd.DataFrame(table[1:], columns=table[0]))
        
        if tables:
            return pd.concat(tables, ignore_index=True)
        
        # Fallback to camelot for scanned tables
        try:
            camelot_tables = camelot.read_pdf(io.BytesIO(file_bytes), pages='all')
            if camelot_tables.n > 0:
                dfs = [t.df for t in camelot_tables]
                return pd.concat(dfs, ignore_index=True)
        except Exception as e:
            logger.warning(f"Camelot failed: {e}")
        
        # If no tables found, return empty dataframe
        return pd.DataFrame()
    
    def _load_url(self, url: str) -> pd.DataFrame:
        from playwright.sync_api import sync_playwright
        from bs4 import BeautifulSoup
        import requests
        
        # Try requests first (faster)
        try:
            response = requests.get(url, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            tables = soup.find_all('table')
            if tables:
                dfs = pd.read_html(str(tables[0]))
                if dfs:
                    return dfs[0]
        except Exception:
            pass
        
        # Fallback to playwright for JS-rendered pages
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until='networkidle')
                content = page.content()
                browser.close()
            
            soup = BeautifulSoup(content, 'html.parser')
            tables = soup.find_all('table')
            if tables:
                dfs = pd.read_html(str(tables[0]))
                if dfs:
                    return dfs[0]
        except Exception as e:
            logger.warning(f"Playwright table extraction failed: {e}")
        
        return pd.DataFrame()


ingestion_agent = IngestionAgent()