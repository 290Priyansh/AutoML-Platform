from backend.agents.base_agent import BaseAgent
from backend.orchestrator.state import PipelineState
from backend.mlops.artifact_store import download_from_s3, upload_to_s3
from backend.llm.router import get_llm
import pandas as pd
import io
import json
import logging
import tempfile
import os
import subprocess
from typing import Dict, Any

logger = logging.getLogger(__name__)


class DeploymentAgent(BaseAgent):
    name: str = "deployment_agent"
    phase: str = "phase4_output"

    def run(self, state: PipelineState) -> Dict[str, Any]:
        # Only deploy top-1 model
        ranked_models = state["ranked_models"]
        if not ranked_models:
            return {
                "inference_endpoints": {},
                "current_agent": self.name,
                "progress_pct": 100,
            }
        
        top_model = ranked_models[0]
        model_name = top_model["model_name"]
        model_path = top_model.get("model_path", "")
        
        if model_name.startswith("Ensemble") or not model_path:
            logger.warning(f"Skipping deployment for {model_name}")
            return {
                "inference_endpoints": {},
                "current_agent": self.name,
                "progress_pct": 100,
            }
        
        logger.info(f"Deploying {model_name}...")
        
        # For now, generate the deployment artifacts and return a mock endpoint
        # In production, this would:
        # 1. Generate FastAPI serving code
        # 2. Build Docker image
        # 3. Push to ECR
        # 4. Deploy to EKS
        # 5. Return live HTTPS URL
        
        inference_endpoints = {}
        
        try:
            # Generate model server code
            server_code = self._generate_model_server(model_name, model_path)
            
            # Generate Dockerfile
            dockerfile = self._generate_dockerfile(model_name)
            
            # Generate Kubernetes manifests (using fine-tuned LLM)
            k8s_manifests = self._generate_k8s_manifests(model_name, model_path, state)
            
            # Save all artifacts
            base_path = model_path.rsplit('/', 1)[0]
            deploy_path = f"{base_path}/deployment/"
            
            upload_to_s3(server_code.encode(), f"{deploy_path}model_server.py")
            upload_to_s3(dockerfile.encode(), f"{deploy_path}Dockerfile")
            
            for name, content in k8s_manifests.items():
                upload_to_s3(content.encode(), f"{deploy_path}k8s/{name}.yaml")
            
            # Mock endpoint URL (in production, this would be the actual EKS URL)
            mock_endpoint = f"https://api.automl.example.com/models/{model_name}/{state['job_id']}"
            inference_endpoints[model_name] = mock_endpoint
            
            logger.info(f"Deployment artifacts generated for {model_name}")
            
        except Exception as e:
            logger.error(f"Deployment failed for {model_name}: {e}")
        
        return {
            "inference_endpoints": inference_endpoints,
            "current_agent": self.name,
            "progress_pct": 100,
        }
    
    def _generate_model_server(self, model_name: str, model_path: str) -> str:
        """Generate FastAPI model server code"""
        return f'''from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import joblib
import pandas as pd
import numpy as np
import boto3
import io

app = FastAPI(title="{model_name} Inference API")

# Load model on startup
model = None

@app.on_event("startup")
async def load_model():
    global model
    # Download model from S3
    s3 = boto3.client('s3')
    bucket, key = parse_s3_path("{model_path}")
    obj = s3.get_object(Bucket=bucket, Key=key)
    model = joblib.load(io.BytesIO(obj['Body'].read()))

def parse_s3_path(s3_path: str):
    if s3_path.startswith("s3://"):
        parts = s3_path.replace("s3://", "").split("/", 1)
        return parts[0], parts[1]
    import os
    bucket = os.environ.get("S3_BUCKET_NAME", "automl-artifacts")
    return bucket, s3_path

class PredictionRequest(BaseModel):
    data: Dict[str, Any]

class PredictionResponse(BaseModel):
    prediction: List[Any]
    probability: Optional[List[List[float]]] = None

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        df = pd.DataFrame([request.data])
        prediction = model.predict(df)
        
        proba = None
        if hasattr(model, 'predict_proba'):
            proba = model.predict_proba(df).tolist()
        
        return PredictionResponse(
            prediction=prediction.tolist(),
            probability=proba
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
async def health():
    return {{"status": "ok", "model": "{model_name}"}}

@app.get("/model-info")
async def model_info():
    return {{
        "model_name": "{model_name}",
        "model_path": "{model_path}",
    }}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
    
    def _generate_dockerfile(self, model_name: str) -> str:
        """Generate Dockerfile for model server"""
        return f'''FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY model_server.py .
EXPOSE 8000
CMD ["uvicorn", "model_server:app", "--host", "0.0.0.0", "--port", "8000"]
'''
    
    def _generate_k8s_manifests(self, model_name: str, model_path: str, state: PipelineState) -> Dict[str, str]:
        """Generate Kubernetes manifests using fine-tuned LLM"""
        # For now, generate template manifests
        # In production, use fine-tuned Qwen 2.5-Coder
        
        deployment = f'''apiVersion: apps/v1
kind: Deployment
metadata:
  name: {model_name.lower().replace("_", "-")}-inference
  labels:
    app: {model_name.lower().replace("_", "-")}-inference
    job_id: {state["job_id"]}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {model_name.lower().replace("_", "-")}-inference
  template:
    metadata:
      labels:
        app: {model_name.lower().replace("_", "-")}-inference
    spec:
      containers:
      - name: model-server
        image: YOUR_ECR_URI/{model_name.lower().replace("_", "-")}:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "1000m"
            memory: "1Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: {model_name.lower().replace("_", "-")}-inference
spec:
  selector:
    app: {model_name.lower().replace("_", "-")}-inference
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {model_name.lower().replace("_", "-")}-inference
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: api.automl.example.com
    http:
      paths:
      - path: /models/{model_name}/{state["job_id"]}
        pathType: Prefix
        backend:
          service:
            name: {model_name.lower().replace("_", "-")}-inference
            port:
              number: 80
'''
        
        return {
            "deployment": deployment,
        }


deployment_agent = DeploymentAgent()