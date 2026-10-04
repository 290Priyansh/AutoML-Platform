import { useEffect, useRef, useState, useCallback } from 'react';
import { apiClient } from '../api/client';
import type { WebSocketMessage, AgentProgress } from '../types';

export function useJobWebSocket(jobId: string | null, onMessage?: (message: WebSocketMessage) => void) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [agentProgress, setAgentProgress] = useState<Record<string, AgentProgress>>({});
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttempts = useRef(0);

  const connect = useCallback(() => {
    if (!jobId) return;

    try {
      const ws = apiClient.createWebSocket(jobId);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected for job:', jobId);
        setIsConnected(true);
        reconnectAttempts.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          onMessage?.(message);

          setAgentProgress(prev => ({
            ...prev,
            [message.current_agent]: {
              name: message.current_agent,
              label: message.current_agent.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
              phase: getAgentPhase(message.current_agent),
              status: message.status === 'running' ? 'running' : 
                     message.status === 'completed' ? 'completed' :
                     message.status === 'failed' ? 'failed' : 'pending',
              progress: message.progress_pct,
              startTime: prev[message.current_agent]?.startTime || new Date(),
              endTime: message.status === 'completed' || message.status === 'failed' ? new Date() : undefined,
            }
          }));
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected for job:', jobId);
        setIsConnected(false);
        
        if (reconnectAttempts.current < 5) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, delay);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
    }
  }, [jobId, onMessage]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  useEffect(() => {
    if (jobId) {
      connect();
    }
    return () => disconnect();
  }, [jobId, connect, disconnect]);

  useEffect(() => {
    if (!isConnected) return;
    
    const interval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [isConnected]);

  return {
    isConnected,
    lastMessage,
    agentProgress,
    connect,
    disconnect,
  };
}

function getAgentPhase(agentName: string): string {
  if (['ingestion', 'eda', 'problem_classifier', 'data_quality', 'split'].includes(agentName)) {
    return 'phase1_understanding';
  }
  if (['cleaning', 'nlp', 'encoding', 'scaling', 'feature_engineering', 'feature_selection', 'imbalance_handler'].includes(agentName)) {
    return 'phase2_preprocessing';
  }
  if (['cv_strategy', 'training', 'hpo', 'evaluation', 'ranking', 'ensemble'].includes(agentName)) {
    return 'phase3_modeling';
  }
  if (['explainability', 'bias_fairness', 'report', 'packaging', 'deployment', 'drift_monitor'].includes(agentName)) {
    return 'phase4_output';
  }
  return 'unknown';
}

export function useAgentProgress(agentProgress: Record<string, AgentProgress>) {
  const agents = [
    { name: 'ingestion', label: 'Data Ingestion', phase: 'phase1_understanding' },
    { name: 'eda', label: 'Exploratory Data Analysis', phase: 'phase1_understanding' },
    { name: 'problem_classifier', label: 'Problem Classification', phase: 'phase1_understanding' },
    { name: 'data_quality', label: 'Data Quality Assessment', phase: 'phase1_understanding' },
    { name: 'split', label: 'Train/Val/Test Split', phase: 'phase1_understanding' },
    { name: 'cleaning', label: 'Data Cleaning', phase: 'phase2_preprocessing' },
    { name: 'nlp', label: 'NLP Processing', phase: 'phase2_preprocessing' },
    { name: 'encoding', label: 'Feature Encoding', phase: 'phase2_preprocessing' },
    { name: 'scaling', label: 'Feature Scaling', phase: 'phase2_preprocessing' },
    { name: 'feature_engineering', label: 'Feature Engineering', phase: 'phase2_preprocessing' },
    { name: 'feature_selection', label: 'Feature Selection', phase: 'phase2_preprocessing' },
    { name: 'imbalance_handler', label: 'Imbalance Handling', phase: 'phase2_preprocessing' },
    { name: 'cv_strategy', label: 'CV Strategy', phase: 'phase3_modeling' },
    { name: 'training', label: 'Model Training', phase: 'phase3_modeling' },
    { name: 'hpo', label: 'Hyperparameter Optimization', phase: 'phase3_modeling' },
    { name: 'evaluation', label: 'Model Evaluation', phase: 'phase3_modeling' },
    { name: 'ranking', label: 'Model Ranking', phase: 'phase3_modeling' },
    { name: 'ensemble', label: 'Ensemble Building', phase: 'phase3_modeling' },
    { name: 'explainability', label: 'Explainability', phase: 'phase4_output' },
    { name: 'bias_fairness', label: 'Bias & Fairness', phase: 'phase4_output' },
    { name: 'report', label: 'Report Generation', phase: 'phase4_output' },
    { name: 'packaging', label: 'Model Packaging', phase: 'phase4_output' },
    { name: 'deployment', label: 'Model Deployment', phase: 'phase4_output' },
    { name: 'drift_monitor', label: 'Drift Monitoring Setup', phase: 'phase4_output' },
  ];

  const progressByPhase = agents.reduce((acc, agent) => {
    const progress = agentProgress[agent.name];
    if (!acc[agent.phase]) acc[agent.phase] = [];
    acc[agent.phase].push({
      ...agent,
      status: progress?.status || 'pending',
      progress: progress?.progress || 0,
      error: progress?.error,
    });
    return acc;
  }, {} as Record<string, Array<{ name: string; label: string; phase: string; status: AgentProgress['status']; progress: number; error?: string }>>);

  const overallProgress = agents.reduce((sum, agent) => {
    const progress = agentProgress[agent.name];
    return sum + (progress?.progress || 0);
  }, 0) / agents.length;

  const currentAgent = agents.find(a => agentProgress[a.name]?.status === 'running')?.label || 'Waiting...';

  return {
    progressByPhase,
    overallProgress,
    currentAgent,
    agents,
  };
}