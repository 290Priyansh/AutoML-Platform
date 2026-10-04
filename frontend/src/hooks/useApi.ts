import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import type { JobStatus, JobResult, RankedModel, ModelInfo, JobCreate } from '../types';

// Error class for API errors
export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export const queryKeys = {
  jobs: {
    all: ['jobs'] as const,
    detail: (jobId: string) => ['jobs', jobId] as const,
    results: (jobId: string) => ['jobs', jobId, 'results'] as const,
    models: (jobId: string) => ['jobs', jobId, 'models'] as const,
    plots: (jobId: string) => ['jobs', jobId, 'plots'] as const,
    report: (jobId: string) => ['jobs', jobId, 'report'] as const,
  },
  models: {
    available: ['models', 'available'] as const,
  },
  health: ['health'] as const,
};

// Default query options with retry logic
const defaultQueryOptions: Partial<UseQueryOptions<any, ApiError>> = {
  retry: (failureCount, error) => {
    // Don't retry on 4xx errors (client errors)
    if (error instanceof ApiError && error.status && error.status >= 400 && error.status < 500) {
      return false;
    }
    return failureCount < 3;
  },
  retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  refetchOnWindowFocus: false,
};

export function useHealthCheck(options?: UseQueryOptions) {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: () => apiClient.healthCheck(),
    refetchInterval: 30000,
    ...defaultQueryOptions,
    ...options,
  });
}

export function useAvailableModels(options?: UseQueryOptions<ModelInfo[], Error>) {
  return useQuery({
    queryKey: queryKeys.models.available,
    queryFn: () => apiClient.getAvailableModels(),
    staleTime: 5 * 60 * 1000,
    ...defaultQueryOptions,
    ...options,
  });
}


export function useJobsList(options?: UseQueryOptions<JobStatus[], Error>) {
  return useQuery({
    queryKey: queryKeys.jobs.all,
    queryFn: () => apiClient.listJobs(),
    refetchInterval: 5000,
    ...defaultQueryOptions,
    ...options,
  });
}

export function useJobStatus(jobId: string, enabled = true, options?: UseQueryOptions) {
  return useQuery({
    queryKey: queryKeys.jobs.detail(jobId),
    queryFn: () => apiClient.getJobStatus(jobId),
    enabled: enabled && !!jobId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.status === 'running' || data?.status === 'queued') {
        return 2000;
      }
      return false;
    },
    ...defaultQueryOptions,
    ...options,
  });
}

export function useJobResults(jobId: string, enabled = true, options?: UseQueryOptions) {
  return useQuery({
    queryKey: queryKeys.jobs.results(jobId),
    queryFn: () => apiClient.getJobResults(jobId),
    enabled: enabled && !!jobId,
    staleTime: 30000,
    ...defaultQueryOptions,
    ...options,
  });
}

export function useJobModels(jobId: string, enabled = true, options?: UseQueryOptions) {
  return useQuery({
    queryKey: queryKeys.jobs.models(jobId),
    queryFn: () => apiClient.getJobModels(jobId),
    enabled: enabled && !!jobId,
    ...defaultQueryOptions,
    ...options,
  });
}

export function useJobPlots(jobId: string, enabled = true, options?: UseQueryOptions) {
  return useQuery({
    queryKey: queryKeys.jobs.plots(jobId),
    queryFn: () => apiClient.getJobPlots(jobId),
    enabled: enabled && !!jobId,
    ...defaultQueryOptions,
    ...options,
  });
}

export function useJobReport(jobId: string, enabled = true, options?: UseQueryOptions) {
  return useQuery({
    queryKey: queryKeys.jobs.report(jobId),
    queryFn: () => apiClient.getJobReport(jobId),
    enabled: enabled && !!jobId,
    ...defaultQueryOptions,
    ...options,
  });
}

export function useCreateJob(options?: UseMutationOptions<{ job_id: string; status: string }, Error, JobCreate>) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ file, model, targetCol }: JobCreate) =>
      apiClient.createJob(file, model, targetCol),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.jobs.all });
    },
    onError: (error) => {
      console.error('Failed to create job:', error);
    },
    ...options,
  });
}


export function useDeployModel(options?: UseMutationOptions<any, Error, { jobId: string; modelIndex: number }>) {
  return useMutation({
    mutationFn: ({ jobId, modelIndex }: { jobId: string; modelIndex: number }) =>
      apiClient.deployModel(jobId, modelIndex),
    ...options,
  });
}

export function useDownloadReport(options?: UseMutationOptions<Blob, Error, { jobId: string; format: 'md' | 'pdf' }>) {
  return useMutation({
    mutationFn: ({ jobId, format }: { jobId: string; format: 'md' | 'pdf' }) =>
      apiClient.downloadReport(jobId, format),
    ...options,
  });
}

export function useDownloadModel(options?: UseMutationOptions<Blob, Error, { jobId: string; modelName: string; format: 'joblib' | 'onnx' }>) {
  return useMutation({
    mutationFn: ({ jobId, modelName, format }: { jobId: string; modelName: string; format: 'joblib' | 'onnx' }) =>
      apiClient.downloadModel(jobId, modelName, format),
    ...options,
  });
}

// Utility hook for handling API errors globally
export function useApiErrorHandler() {
  const handleError = (error: unknown) => {
    if (error instanceof ApiError) {
      switch (error.status) {
        case 400:
          return 'Invalid request. Please check your input.';
        case 401:
          return 'Session expired. Please log in again.';
        case 403:
          return 'You do not have permission to perform this action.';
        case 404:
          return 'Resource not found.';
        case 422:
          return 'Validation failed. Please check your input.';
        case 500:
          return 'Server error. Please try again later.';
        default:
          return error.message;
      }
    }
    return 'An unexpected error occurred';
  };
  return { handleError };
}