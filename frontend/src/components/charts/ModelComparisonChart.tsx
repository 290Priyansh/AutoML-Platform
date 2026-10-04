'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { cn } from '../../lib/utils';

interface ModelComparisonChartProps {
  models: Array<{
    name: string;
    score: number;
    metrics: Record<string, number>;
  }>;
  metric?: string;
  height?: number;
}

const PALETTE = ['#1F5C46', '#2E7D4F', '#3B6B56', '#4E7866', '#5F8573', '#7A766D', '#4A4843', '#8C8980'];

export function ModelComparisonChart({ 
  models, 
  metric = 'composite_score',
  height = 300 
}: ModelComparisonChartProps) {
  const data = models.map((m, i) => ({
    name: m.name.length > 20 ? m.name.substring(0, 20) + '...' : m.name,
    fullName: m.name,
    [metric]: m.metrics?.[metric] ?? m.score ?? 0,
    rank: i + 1,
    color: PALETTE[i % PALETTE.length],
  }));

  const maxValue = Math.max(...data.map(d => Number(d[metric]) || 0), 1);
  const minValue = Math.min(...data.map(d => Number(d[metric]) || 0), 0);

  return (
    <div className="w-full h-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
          <XAxis 
            type="number" 
            domain={[minValue * 0.9, maxValue * 1.1]}
            tickFormatter={(v) => (metric === 'composite_score' ? `${(Number(v) * 100).toFixed(1)}%` : Number(v).toFixed(3))}
            tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis 
            type="category" 
            dataKey="name" 
            width={180}
            tick={{ fontSize: 11, fill: 'var(--text)' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip 
            formatter={(value: any) => [metric === 'composite_score' ? `${(Number(value || 0) * 100).toFixed(2)}%` : Number(value || 0).toFixed(4), metric]}
            contentStyle={{
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              color: 'var(--text)',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '12px',
            }}
            labelFormatter={(name) => data.find(d => d.name === name)?.fullName || name}
          />
          <Legend />
          <Bar 
            dataKey={metric} 
            name={metric === 'composite_score' ? 'Composite Score' : metric}
            radius={[0, 2, 2, 0]}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

interface MetricRadarChartProps {
  models: Array<{
    name: string;
    metrics: Record<string, number>;
  }>;
  metrics: string[];
  height?: number;
}

export function MetricRadarChart({ models, metrics, height = 300 }: MetricRadarChartProps) {
  // Simplified version using grouped bar chart
  const data = models.flatMap((model, modelIndex) => 
    metrics.map((metric) => ({
      model: model.name,
      metric: metric.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      value: model.metrics?.[metric] ?? 0,
      modelColor: PALETTE[modelIndex % PALETTE.length],
    }))
  );

  return (
    <div className="w-full h-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
          <XAxis 
            type="number" 
            tickFormatter={(v) => v.toFixed(2)}
            tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis 
            type="category" 
            dataKey="metric" 
            width={140}
            tick={{ fontSize: 11, fill: 'var(--text)' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip 
            formatter={(value: any) => [typeof value === 'number' ? value.toFixed(4) : String(value), 'Value']}
            contentStyle={{
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              color: 'var(--text)',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '12px',
            }}
          />
          <Legend />
          <Bar 
            dataKey="value" 
            radius={[0, 2, 2, 0]}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.modelColor} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

interface TrainingTimelineProps {
  agents: Array<{
    name: string;
    label: string;
    phase: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    progress: number;
    startTime?: Date;
    endTime?: Date;
  }>;
}

export function TrainingTimeline({ agents }: TrainingTimelineProps) {
  return (
    <div className="space-y-3">
      {agents.map((agent, index) => (
        <div key={agent.name} className="relative flex items-center group">
          {/* Timeline line */}
          {index < agents.length - 1 && (
            <div className="absolute left-3.5 top-6 bottom-0 w-px bg-[var(--border)]" />
          )}
          
          <div className="flex items-start gap-3 relative z-10 w-full">
            {/* Status dot */}
            <div className="flex flex-col items-center w-7 pt-1">
              <div 
                className={cn(
                  'w-2 h-2 rounded-full',
                  agent.status === 'completed' && 'bg-[var(--status-success)]',
                  agent.status === 'running' && 'bg-[var(--accent)] animate-pulse',
                  agent.status === 'failed' && 'bg-[var(--status-error)]',
                  agent.status === 'pending' && 'bg-[var(--border)]'
                )}
              />
            </div>
            
            {/* Agent info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="px-1.5 py-0.5 text-[10px] font-mono rounded-[var(--r-xs)] border border-[var(--border)] bg-[var(--surface-2)] text-[var(--text-muted)]">
                  {agent.phase.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
                </span>
                <h4 className="text-xs font-medium text-[var(--text)] truncate">{agent.label}</h4>
              </div>
              
              <div className="mt-1.5 flex items-center gap-3 text-xs font-mono tabular-nums text-[var(--text-muted)]">
                <div className="w-36 h-1 bg-[var(--surface-2)] rounded-xs overflow-hidden border border-[var(--border)]">
                  <div 
                    className="h-full bg-[var(--accent)] rounded-xs transition-all duration-300"
                    style={{ width: `${agent.progress}%` }}
                  />
                </div>
                <span className="w-10 text-right">{agent.progress}%</span>
                {agent.startTime && (
                  <span>
                    Started: {agent.startTime.toLocaleTimeString()}
                  </span>
                )}
                {agent.endTime && (
                  <span>
                    Ended: {agent.endTime.toLocaleTimeString()}
                    ({(agent.endTime.getTime() - (agent.startTime?.getTime() || 0)) / 1000}s)
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}