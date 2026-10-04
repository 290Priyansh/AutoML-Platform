import axios, { type AxiosInstance, type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import type { ModelInfo, RankedModel, JobResult, JobStatus } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';

// Type for API error responses
export interface ApiError {
  detail: string;
  code?: string;
  timestamp: string;
}

// Retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

class ApiClient {
  private client: AxiosInstance;
  private wsConnections: Map<string, WebSocket> = new Map();

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 300000, // 5 minutes for long-running requests
    });

    // Request interceptor for auth
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        // Add request ID for tracing
        config.headers['X-Request-ID'] = crypto.randomUUID();
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor with retry logic
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError<ApiError>) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retryCount?: number };
        
        // Handle 401 - unauthorized
        if (error.response?.status === 401) {
          localStorage.removeItem('auth_token');
          if (!window.location.pathname.includes('/login')) {
            window.location.href = '/login';
          }
          return Promise.reject(this.formatError(error));
        }

        // Handle network errors with retry
        if (!error.response && (originalRequest._retryCount || 0) < MAX_RETRIES) {
          const retries = (originalRequest._retryCount || 0) + 1;
          originalRequest._retryCount = retries;
          await new Promise(resolve => setTimeout(resolve, RETRY_DELAY * retries));
          return this.client.request(originalRequest);
        }

        return Promise.reject(this.formatError(error));
      }
    );
  }

  private formatError(error: AxiosError<ApiError>): Error & { code?: string; status?: number } {
    const message = error.response?.data?.detail 
      || error.message 
      || 'An unexpected error occurred';
    const err = new Error(message) as Error & { code?: string; status?: number };
    err.code = error.response?.data?.code;
    err.status = error.response?.status;
    return err;
  }

  // Job endpoints
  async createJob(file: File, model?: string, targetCol?: string): Promise<{ job_id: string; status: string }> {
    const formData = new FormData();
    formData.append('file', file);
    if (model) formData.append('model', model);
    if (targetCol) formData.append('target_col', targetCol);

    const response = await this.client.post<{ job_id: string; status: string }>('/jobs', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  }

  async listJobs(): Promise<JobStatus[]> {
    const response = await this.client.get<JobStatus[]>('/jobs');
    return response.data;
  }

  async getJobStatus(jobId: string): Promise<JobStatus> {
    const response = await this.client.get<JobStatus>(`/jobs/${jobId}`);
    return response.data;
  }

  async getJobResults(jobId: string): Promise<JobResult> {
    const response = await this.client.get<JobResult>(`/jobs/${jobId}/results`);
    return response.data;
  }

  async getJobReport(jobId: string) {
    const response = await this.client.get(`/jobs/${jobId}/report`);
    return response.data;
  }

  async getJobModels(jobId: string): Promise<{ models: RankedModel[] }> {
    const response = await this.client.get(`/jobs/${jobId}/models`);
    return response.data;
  }

  async getJobPlots(jobId: string) {
    const response = await this.client.get(`/jobs/${jobId}/plots`);
    return response.data;
  }

  async deployModel(jobId: string, modelIndex: number) {
    const response = await this.client.post(`/jobs/${jobId}/deploy`, { model_index: modelIndex });
    return response.data;
  }

  async getAvailableModels(): Promise<ModelInfo[]> {
    const response = await this.client.get<ModelInfo[]>('/models/available');
    return response.data;
  }

  async healthCheck() {
    const response = await this.client.get('/health');
    return response.data;
  }

  // WebSocket with automatic reconnection
  createWebSocket(jobId: string, onMessage?: (data: any) => void, onError?: (error: Event) => void, onClose?: () => void): WebSocket {
    const wsUrl = `${WS_BASE_URL}/api/v1/ws/${jobId}`;
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log(`WebSocket connected for job ${jobId}`);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage?.(data);
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    ws.onerror = (error) => {
      console.error(`WebSocket error for job ${jobId}:`, error);
      onError?.(error);
    };

    ws.onclose = () => {
      console.log(`WebSocket closed for job ${jobId}`);
      this.wsConnections.delete(jobId);
      onClose?.();
    };

    // Store connection for cleanup
    this.wsConnections.set(jobId, ws);
    return ws;
  }

  closeWebSocket(jobId: string) {
    const ws = this.wsConnections.get(jobId);
    if (ws) {
      ws.close();
      this.wsConnections.delete(jobId);
    }
  }

  closeAllWebSockets() {
    this.wsConnections.forEach((ws) => ws.close());
    this.wsConnections.clear();
  }

  async downloadReport(jobId: string, format: 'md' | 'pdf' = 'pdf'): Promise<Blob> {
    const response = await this.client.get(`/jobs/${jobId}/report`, {
      responseType: 'blob',
      params: { format },
    });
    return response.data;
  }

  async downloadModel(jobId: string, modelName: string, format: 'joblib' | 'onnx' = 'joblib'): Promise<Blob> {
    const response = await this.client.get(`/jobs/${jobId}/models/${modelName}/download`, {
      responseType: 'blob',
      params: { format },
    });
    return response.data;
  }
}

export const apiClient = new ApiClient();
export default apiClient;