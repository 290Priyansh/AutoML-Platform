'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  Legend,
} from 'recharts';
import { cn } from '../../lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';

interface MetricCardProps {
  title?: string;
  label?: string;
  value: string | number;
  change?: string;
  trend?: 'up' | 'down' | 'neutral';
  icon?: React.ReactNode;
  subtitle?: string;
}

export function MetricCard({ title, label, value, change, trend, icon, subtitle }: MetricCardProps) {
  const displayTitle = title || label || '';
  return (
    <Card className="surface-card squircle-lg border border-[var(--border)]">
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-mono uppercase tracking-wider text-[var(--text-muted)]">{displayTitle}</p>
            <p className="font-mono text-2xl font-semibold tabular-nums text-[var(--text)] mt-1.5">{value}</p>
            {subtitle && <p className="text-xs text-[var(--text-muted)] mt-1">{subtitle}</p>}
          </div>
          <div className={cn(
            'w-8 h-8 rounded-[var(--r-sm)] squircle-sm border border-[var(--border)] bg-[var(--surface-2)] flex items-center justify-center text-[var(--text-muted)]',
            trend === 'up' && 'text-[var(--status-success)]',
            trend === 'down' && 'text-[var(--status-error)]'
          )}>
            {icon}
          </div>
        </div>
        {change && (
          <div className="mt-3.5 flex items-center gap-1.5 font-mono text-xs">
            <span className={cn(
              'font-medium tabular-nums',
              trend === 'up' && 'text-[var(--status-success)]',
              trend === 'down' && 'text-[var(--status-error)]',
              trend === 'neutral' && 'text-[var(--text-muted)]'
            )}>
              {change}
            </span>
            <span className="text-[var(--text-muted)]">vs last month</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface TrainingMetricsChartProps {
  data: Array<{
    timestamp: string;
    agent: string;
    progress?: number;
    duration: number;
  }>;
  height?: number;
}

export function TrainingMetricsChart({ data, height = 300 }: TrainingMetricsChartProps) {
  if (!data.length) return <div className="text-center py-8 text-gray-500">No training data available</div>;

  // Group by agent and calculate average duration
  const agentStats = data.reduce((acc, d) => {
    if (!acc[d.agent]) {
      acc[d.agent] = { totalDuration: 0, count: 0 };
    }
    acc[d.agent].totalDuration += d.duration;
    acc[d.agent].count += 1;
    return acc;
  }, {} as Record<string, { totalDuration: number; count: number }>);

  const chartData = Object.entries(agentStats).map(([agent, stats]) => ({
    agent: agent.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    avgDuration: stats.totalDuration / stats.count,
    count: stats.count,
  }));

  return (
    <Card className="surface-card squircle-lg border border-[var(--border)]">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-[var(--text)]">Agent Training Duration</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
            <defs>
              <linearGradient id="colorTraining" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#1F5C46" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#1F5C46" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis 
              dataKey="agent" 
              tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis 
              tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `${Number(v).toFixed(0)}s`}
            />
            <Tooltip 
              formatter={(value: any) => [`${Number(value || 0).toFixed(1)}s`, 'Avg Duration']}
              contentStyle={{
                backgroundColor: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: '6px',
                color: 'var(--text)',
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '12px',
              }}
            />
            <Area 
              type="monotone" 
              dataKey="avgDuration" 
              stroke="#1F5C46" 
              strokeWidth={1.5}
              fillOpacity={1} 
              fill="url(#colorTraining)" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

interface ModelTrendsChartProps {
  data: Array<{
    epoch: number;
    metrics: Record<string, number>;
    modelName: string;
  } | {
    model: string;
    timestamp: string;
    metric: number;
  }>;
  metricName?: string;
  height?: number;
}

export function ModelTrendsChart({ data, metricName = 'accuracy', height = 300 }: ModelTrendsChartProps) {
  if (!data.length) return <div className="text-center py-8 text-[var(--text-muted)]">No trend data available</div>;

  const normalizedData = data.map((d: any) => {
    if ('model' in d && 'timestamp' in d && 'metric' in d) {
      return {
        epoch: new Date(d.timestamp).getTime(),
        modelName: d.model,
        metrics: { [metricName]: d.metric }
      };
    }
    return d;
  });

  const models = Array.from(new Set(normalizedData.map(d => d.modelName)));
  const epochs = Array.from(new Set(normalizedData.map(d => d.epoch))).sort((a, b) => a - b);

  const chartData = epochs.map(epoch => {
    const entry: Record<string, any> = { epoch };
    models.forEach(model => {
      const match = normalizedData.find(d => d.epoch === epoch && d.modelName === model);
      if (match && match.metrics[metricName] !== undefined) {
        entry[model] = match.metrics[metricName];
      }
    });
    return entry;
  });

  const palette = ['#1F5C46', '#2E7D4F', '#7A766D', '#B54708', '#026AA2', '#5F5E5B'];

  return (
    <Card className="surface-card squircle-lg border border-[var(--border)]">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-[var(--text)]">Model Performance Trends ({metricName})</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis 
              dataKey="epoch" 
              tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => typeof v === 'number' && v > 1000000 ? new Date(v).toLocaleTimeString() : v}
            />
            <YAxis 
              tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => Number(v).toFixed(4)}
            />
            <Tooltip 
              formatter={(value: any) => [Number(value || 0).toFixed(4), metricName]}
              contentStyle={{
                backgroundColor: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: '6px',
                color: 'var(--text)',
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '12px',
              }}
            />
            {models.map((model, i) => (
              <Line
                key={model}
                type="monotone"
                dataKey={model}
                stroke={palette[i % palette.length]}
                strokeWidth={1.5}
                dot={false}
                data={chartData.filter(d => d.model === model)}
              />
            ))}
            <Legend />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export function MetricsDashboard({ 
  jobMetrics,
  trainingHistory,
  modelTrends,
}: {
  jobMetrics?: {
    totalJobs: number;
    completedJobs: number;
    runningJobs: number;
    failedJobs: number;
    avgTrainingTime: number;
    successRate: number;
  };
  trainingHistory?: Array<{ agent: string; duration: number; timestamp: string }>;
  modelTrends?: Array<{ model: string; metric: number; timestamp: string }>;
}) {
  return (
    <div className="space-y-6">
      {/* Summary Metrics */}
      {jobMetrics && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Total Jobs"
            value={jobMetrics.totalJobs}
            icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>}
            subtitle="Total training jobs"
          />
          <MetricCard
            title="Completed"
            value={jobMetrics.completedJobs}
            change={`${jobMetrics.successRate.toFixed(1)}%`}
            trend="up"
            icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>}
            subtitle="Successfully completed"
          />
          <MetricCard
            title="Running"
            value={jobMetrics.runningJobs}
            trend="neutral"
            icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
            subtitle="Currently training"
          />
          <MetricCard
            title="Avg Training Time"
            value={`${(jobMetrics.avgTrainingTime / 60).toFixed(1)}m`}
            trend="neutral"
            icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
            subtitle="Average duration"
          />
        </div>
      )}

      {/* Training Charts */}
      <Tabs defaultValue="duration" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="duration">Agent Duration</TabsTrigger>
          <TabsTrigger value="trends">Model Trends</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
        </TabsList>

        <TabsContent value="duration" className="mt-4 grid gap-4 md:grid-cols-2">
          {trainingHistory && trainingHistory.length > 0 && (
            <TrainingMetricsChart data={trainingHistory} />
          )}
          <Card className="surface-card squircle-lg border border-[var(--border)]">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-[var(--text)]">Training Pipeline Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2.5">
                {[
                  { phase: 'Understanding', agents: 5, avgTime: '2.3m' },
                  { phase: 'Preprocessing', agents: 7, avgTime: '4.1m' },
                  { phase: 'Modeling', agents: 6, avgTime: '12.5m' },
                  { phase: 'Output', agents: 6, avgTime: '3.2m' },
                ].map((p) => (
                  <div key={p.phase} className="flex items-center justify-between p-3 bg-[var(--surface-2)] rounded-[var(--r-sm)] border border-[var(--border)]">
                    <div>
                      <p className="text-xs font-medium text-[var(--text)]">{p.phase}</p>
                      <p className="text-xs text-[var(--text-muted)] font-mono mt-0.5">{p.agents} agents</p>
                    </div>
                    <div className="text-right">
                      <p className="font-mono text-sm font-semibold tabular-nums text-[var(--accent)]">{p.avgTime}</p>
                      <p className="text-[11px] text-[var(--text-muted)]">avg duration</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trends" className="mt-4">
          {modelTrends && modelTrends.length > 0 && (
            <ModelTrendsChart 
              data={modelTrends} 
              metricName="Composite Score" 
            />
          )}
        </TabsContent>

        <TabsContent value="timeline" className="mt-4">
          <Card className="surface-card squircle-lg border border-[var(--border)]">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-[var(--text)]">Training Pipeline Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {trainingHistory?.slice(0, 10).map((h, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 bg-[var(--surface-2)] rounded-[var(--r-sm)] border border-[var(--border)]">
                    <div className="w-6 h-6 rounded-[var(--r-sm)] squircle-sm border border-[var(--border)] bg-[var(--surface)] flex items-center justify-center">
                      <span className="text-xs font-mono font-medium text-[var(--text-muted)]">{i + 1}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-[var(--text)] truncate">{h.agent}</p>
                      <p className="text-[11px] text-[var(--text-muted)] font-mono tabular-nums mt-0.5">
                        {new Date(h.timestamp).toLocaleString()} • {h.duration}s
                      </p>
                    </div>
                    <span className="h-5 px-2 rounded-xs border border-[var(--border)] bg-[var(--surface)] text-[var(--status-success)] text-[10px] font-mono flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-[var(--status-success)]" />
                      Completed
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}