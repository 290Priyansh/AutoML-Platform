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
    color: `hsl(${i * 60}, 70%, 50%)`,
  }));

  const maxValue = Math.max(...data.map(d => Number(d[metric]) || 0), 1);
  const minValue = Math.min(...data.map(d => Number(d[metric]) || 0), 0);

  return (
    <div className="w-full h-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
          <XAxis 
            type="number" 
            domain={[minValue * 0.9, maxValue * 1.1]}
            tickFormatter={(v) => (metric === 'composite_score' ? `${(Number(v) * 100).toFixed(1)}%` : Number(v).toFixed(3))}
            tick={{ fontSize: 12, fill: '#6b7280' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis 
            type="category" 
            dataKey="name" 
            width={180}
            tick={{ fontSize: 12, fill: '#374151' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip 
            formatter={(value: any) => [metric === 'composite_score' ? `${(Number(value || 0) * 100).toFixed(2)}%` : Number(value || 0).toFixed(4), metric]}
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
            }}
            labelFormatter={(name) => data.find(d => d.name === name)?.fullName || name}
          />
          <Legend />
          <Bar 
            dataKey={metric} 
            name={metric === 'composite_score' ? 'Composite Score' : metric}
            radius={[0, 4, 4, 0]}
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
  // Radar chart would need PolarAngleAxis, PolarRadiusAxis, Radar from recharts
  // Simplified version using grouped bar chart
  const data = models.flatMap((model, modelIndex) => 
    metrics.map((metric, metricIndex) => ({
      model: model.name,
      metric: metric.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      value: model.metrics?.[metric] ?? 0,
      modelColor: `hsl(${modelIndex * 60}, 70%, 50%)`,
    }))
  );

  return (
    <div className="w-full h-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
          <XAxis 
            type="number" 
            tickFormatter={(v) => v.toFixed(2)}
            tick={{ fontSize: 11, fill: '#6b7280' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis 
            type="category" 
            dataKey="metric" 
            width={140}
            tick={{ fontSize: 11, fill: '#374151' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip 
            formatter={(value: any) => [typeof value === 'number' ? value.toFixed(4) : String(value), 'Value']}
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
            }}
          />
          <Legend />
          <Bar 
            dataKey="value" 
            radius={[0, 4, 4, 0]}
          >
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill={`hsl(${Math.floor(index / metrics.length) * 60}, 70%, 50%)`} />
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
  const phaseColors = {
    phase1_understanding: 'bg-purple-500',
    phase2_preprocessing: 'bg-orange-500',
    phase3_modeling: 'bg-blue-500',
    phase4_output: 'bg-green-500',
  };

  const statusIcons = {
    pending: '⏳',
    running: '🔄',
    completed: '✅',
    failed: '❌',
  };

  return (
    <div className="space-y-3">
      {agents.map((agent, index) => (
        <div key={agent.name} className="relative flex items-center group">
          {/* Timeline line */}
          {index < agents.length - 1 && (
            <div className="absolute left-5 top-8 bottom-0 w-0.5 bg-gray-200 dark:bg-gray-700" />
          )}
          
          <div className="flex items-start gap-4 relative z-10">
            {/* Phase indicator & status */}
            <div className="flex flex-col items-center w-10">
              <div 
                className={cn(
                  'w-2.5 h-2.5 rounded-full border-2 border-white dark:border-gray-900 transition-colors',
                  agent.status === 'completed' && 'bg-green-500',
                  agent.status === 'running' && 'bg-blue-500 animate-pulse',
                  agent.status === 'failed' && 'bg-red-500',
                  agent.status === 'pending' && 'bg-gray-300 dark:bg-gray-600'
                )}
              />
              <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">{statusIcons[agent.status]}</span>
            </div>
            
            {/* Agent info */}
            <div className="flex-1 min-w-0 ml-2">
              <div className="flex items-center gap-2">
                <span className={cn(
                  'px-2 py-0.5 text-xs font-medium rounded-full',
                  phaseColors[agent.phase as keyof typeof phaseColors] || 'bg-gray-100 text-gray-700'
                )}>
                  {agent.phase.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
                </span>
                <h4 className="font-medium text-gray-900 dark:text-white truncate">{agent.label}</h4>
              </div>
              
              <div className="mt-1 flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
                <div className="w-48 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-purple-500 to-blue-500 rounded-full transition-all duration-500"
                    style={{ width: `${agent.progress}%` }}
                  />
                </div>
                <span className="w-12 text-right">{agent.progress}%</span>
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