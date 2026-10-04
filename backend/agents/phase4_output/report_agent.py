from backend.agents.base_agent import BaseAgent
from backend.orchestrator.state import PipelineState
from backend.mlops.artifact_store import download_from_s3, upload_to_s3
from backend.llm.router import get_llm
from backend.llm.prompts.report_writer import build_prompt as build_report_prompt
import pandas as pd
import io
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    logger.warning("weasyprint not available, PDF generation disabled")


class ReportAgent(BaseAgent):
    name: str = "report_agent"
    phase: str = "phase4_output"

    def run(self, state: PipelineState) -> Dict[str, Any]:
        # Gather all context for the report
        context = self._build_report_context(state)
        
        # Generate markdown report using LLM
        report_md = self._generate_report(context)
        
        # Save markdown to S3
        base_path = f"{state['cleaned_train_path'].rsplit('/', 1)[0]}/"
        md_path = upload_to_s3(report_md.encode(), f"{base_path}report.md")
        
        # Generate PDF
        pdf_path = ""
        if WEASYPRINT_AVAILABLE:
            try:
                pdf_path = self._generate_pdf(report_md, base_path)
            except Exception as e:
                logger.warning(f"PDF generation failed: {e}")
        
        return {
            "final_report_md": report_md,
            "report_md_path": md_path,
            "report_pdf_path": pdf_path,
            "current_agent": self.name,
            "progress_pct": 100,
        }
    
    def _build_report_context(self, state: PipelineState) -> Dict[str, Any]:
        """Build context dictionary for report generation"""
        
        # Dataset overview
        eda_report = state.get("eda_report", {})
        table_info = eda_report.get("table", {})
        
        # Preprocessing summary
        preprocessing_summary = self._build_preprocessing_summary(state)
        
        # Prune all_results to numeric summary metrics only (skip plot paths and heavy objects)
        clean_results = {}
        for m_name, res in state.get("evaluation_results", {}).items():
            if isinstance(res, dict):
                clean_results[m_name] = {k: round(v, 4) for k, v in res.items() if isinstance(v, (int, float))}
            else:
                clean_results[m_name] = str(res)

        # Prune feature importances to top 10 per model to prevent huge prompt tokens
        top_fi = {}
        for m_name, fi in state.get("feature_importance", {}).items():
            if isinstance(fi, dict):
                sorted_fi = sorted(fi.items(), key=lambda x: x[1], reverse=True)[:10]
                top_fi[m_name] = {k: round(v, 4) for k, v in sorted_fi}

        # Top 3 models summary
        top3_summary = [
            {
                "model_name": m.get("model_name"),
                "rank": m.get("rank"),
                "composite_score": round(m.get("composite_score", 0), 4),
                "metrics": {k: round(v, 4) for k, v in m.get("metrics", {}).items() if isinstance(v, (int, float))}
            }
            for m in state.get("ranked_models", [])[:3]
        ]

        # Bias report summary
        bias_report = state.get("bias_report", {})
        bias_summary = {
            "sensitive_columns_found": bias_report.get("sensitive_columns_found", False),
            "sensitive_columns": bias_report.get("sensitive_columns", []),
            "narrative": bias_report.get("narrative", "")
        }

        return {
            "row_count": state.get("row_count", 0),
            "col_count": state.get("col_count", 0),
            "problem_type": state.get("problem_type", ""),
            "target_column": state.get("target_column", ""),
            "data_quality_score": state.get("data_quality_score", 0.0),
            "quality_flags": state.get("data_quality_flags", []),
            "preprocessing_summary": preprocessing_summary,
            "all_results": clean_results,
            "top3_models": top3_summary,
            "feature_importances": top_fi,
            "bias_report": bias_summary,
        }
    
    def _build_preprocessing_summary(self, state: PipelineState) -> str:
        """Build human-readable preprocessing summary"""
        parts = []
        
        if state.get("encoding_map"):
            enc_types = set(state["encoding_map"].values())
            parts.append(f"Categorical encoding: {', '.join(enc_types)}")
        
        if state.get("scaler_type") and state["scaler_type"] != "none":
            parts.append(f"Feature scaling: {state['scaler_type']}")
        
        if state.get("imbalance_strategy") and state["imbalance_strategy"] != "none":
            parts.append(f"Imbalance handling: {state['imbalance_strategy']}")
        
        if state.get("engineered_features"):
            parts.append(f"Feature engineering: {len(state['engineered_features'])} new features created")
        
        if state.get("selected_features"):
            parts.append(f"Feature selection: {len(state['selected_features'])} features retained from {state['col_count']} original")
        
        return "; ".join(parts) if parts else "Standard preprocessing applied"
    
    def _generate_report(self, context: Dict[str, Any]) -> str:
        """Generate markdown report using LLM"""
        try:
            llm = get_llm()
            prompt = build_report_prompt(context)
            response = llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"LLM report generation failed: {e}")
            # Fallback: generate basic report
            return self._generate_fallback_report(context)
    
    def _generate_fallback_report(self, context: Dict[str, Any]) -> str:
        """Generate a basic fallback report if LLM fails"""
        lines = [
            "# AutoML Pipeline Report",
            "",
            "## Executive Summary",
            f"This report summarizes the AutoML pipeline run on a dataset with {context['row_count']} rows and {context['col_count']} columns. "
            f"The problem type is {context['problem_type']} with target column '{context['target_column']}'. "
            f"Data quality score: {context['data_quality_score']:.2f}/1.0.",
            "",
            "## Dataset Overview",
            f"- Rows: {context['row_count']}",
            f"- Columns: {context['col_count']}",
            f"- Problem Type: {context['problem_type']}",
            f"- Target: {context['target_column']}",
            "",
            "## Data Quality Assessment",
            f"- Quality Score: {context['data_quality_score']:.2f}/1.0",
            f"- Flags: {', '.join(context['quality_flags']) if context['quality_flags'] else 'None'}",
            "",
            "## Preprocessing Decisions and Rationale",
            context['preprocessing_summary'],
            "",
            "## Model Training Results",
        ]
        
        # Add model results table
        if context['all_results']:
            lines.append("| Model | Metrics |")
            lines.append("|-------|---------|")
            for model_name, metrics in context['all_results'].items():
                if 'error' not in metrics:
                    metric_str = ", ".join([f"{k}: {v:.4f}" for k, v in metrics.items() if isinstance(v, (int, float)) and k != 'plot_paths'])
                    lines.append(f"| {model_name} | {metric_str} |")
        
        lines.extend([
            "",
            "## Top 3 Recommended Models",
        ])
        
        for i, model in enumerate(context['top3_models'], 1):
            lines.append(f"### {i}. {model['model_name']} (Score: {model['composite_score']:.4f})")
            if 'metrics' in model:
                for k, v in model['metrics'].items():
                    if isinstance(v, (int, float)):
                        lines.append(f"- {k}: {v:.4f}")
        
        lines.extend([
            "",
            "## Feature Importance Analysis",
        ])
        
        for model_name, importance in context['feature_importances'].items():
            lines.append(f"### {model_name}")
            for feat, imp in list(importance.items())[:10]:
                lines.append(f"- {feat}: {imp:.4f}")
        
        lines.extend([
            "",
            "## Bias and Fairness Assessment",
        ])
        
        bias = context['bias_report']
        if bias.get('sensitive_columns_found'):
            lines.append(f"Sensitive columns detected: {', '.join(bias['sensitive_columns'])}")
            lines.append(f"Fairness narrative: {bias.get('narrative', 'N/A')}")
        else:
            lines.append(bias.get('message', 'No bias analysis performed.'))
        
        lines.extend([
            "",
            "## Recommendations for Production Deployment",
            "1. Monitor model performance in production",
            "2. Set up drift detection",
            "3. Establish retraining schedule",
            "4. Validate model on new data before deployment",
            "",
            "## Next Steps",
            "1. Deploy top model to production",
            "2. Set up monitoring dashboard",
            "3. Schedule periodic retraining",
        ])
        
        return "\n".join(lines)
    
    def _generate_pdf(self, report_md: str, base_path: str) -> str:
        """Convert markdown to PDF using weasyprint"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                h1, h2, h3 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                code {{ background-color: #f4f4f4; padding: 2px 4px; }}
                pre {{ background-color: #f4f4f4; padding: 10px; overflow-x: auto; }}
            </style>
        </head>
        <body>
        {self._markdown_to_html(report_md)}
        </body>
        </html>
        """
        
        pdf_buffer = io.BytesIO()
        HTML(string=html_content).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)
        
        return upload_to_s3(pdf_buffer.getvalue(), f"{base_path}report.pdf")
    
    def _markdown_to_html(self, md: str) -> str:
        """Simple markdown to HTML conversion"""
        import re
        
        html = md
        
        # Headers
        html = re.sub(r'^### (.*$)', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*$)', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*$)', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # Bold
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        
        # Lists
        html = re.sub(r'^- (.*$)', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', html)
        
        # Paragraphs
        html = re.sub(r'\n\n', '</p><p>', html)
        html = '<p>' + html + '</p>'
        
        # Fix nested tags
        html = html.replace('<p><h', '<h').replace('</h3></p>', '</h3>').replace('</h2></p>', '</h2>').replace('</h1></p>', '</h1>')
        html = html.replace('<p><ul>', '<ul>').replace('</ul></p>', '</ul>')
        
        return html


report_agent = ReportAgent()