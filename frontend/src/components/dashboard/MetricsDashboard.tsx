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
    <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{displayTitle}</p>
            <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">{value}</p>
            {subtitle && <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{subtitle}</p>}
          </div>
          <div className={cn(
            'p-2 rounded-lg',
            trend === 'up' && 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
            trend === 'down' && 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
            trend === 'neutral' && 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
          )}>
            {icon}
          </div>
        </div>
        {change && (
          <div className="mt-4 flex items-center">
            <span className={cn(
              'text-sm font-medium',
              trend === 'up' && 'text-green-600 dark:text-green-400',
              trend === 'down' && 'text-red-600 dark:text-red-400',
              trend === 'neutral' && 'text-gray-500 dark:text-gray-400'
            )}>
              {change}
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400 ml-2">vs last month</span>
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
    <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
      <CardHeader>
        <CardTitle>Agent Training Duration</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
            <defs>
              <linearGradient id="colorTraining" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="agent" 
              tick={{ fontSize: 11, fill: '#6b7280' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis 
              tick={{ fontSize: 11, fill: '#6b7280' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `${Number(v).toFixed(0)}s`}
            />
            <Tooltip 
              formatter={(value: any) => [`${Number(value || 0).toFixed(1)}s`, 'Avg Duration']}
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
              }}
            />
            <Area 
              type="monotone" 
              dataKey="avgDuration" 
              stroke="#8b5cf6" 
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
  if (!data.length) return <div className="text-center py-8 text-gray-500">No trend data available</div>;

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

  return (
    <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
      <CardHeader>
        <CardTitle>Model Performance Trends ({metricName})</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="epoch" 
              tick={{ fontSize: 11, fill: '#6b7280' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => typeof v === 'number' && v > 1000000 ? new Date(v).toLocaleTimeString() : v}
            />
            <YAxis 
              tick={{ fontSize: 11, fill: '#6b7280' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => Number(v).toFixed(4)}
            />
            <Tooltip 
              formatter={(value: any) => [Number(value || 0).toFixed(4), metricName]}
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
              }}
            />
            {models.map((model, i) => (
              <Line
                key={model}
                type="monotone"
                dataKey={model}
                stroke={`hsl(${i * 60}, 70%, 50%)`}
                strokeWidth={2}
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
          <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
            <CardHeader>
              <CardTitle>Training Pipeline Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { phase: 'Understanding', agents: 5, avgTime: '2.3m' },
                  { phase: 'Preprocessing', agents: 7, avgTime: '4.1m' },
                  { phase: 'Modeling', agents: 6, avgTime: '12.5m' },
                  { phase: 'Output', agents: 6, avgTime: '3.2m' },
                ].map((p) => (
                  <div key={p.phase} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{p.phase}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">{p.agents} agents</p>
                    </div>
                    <div className="text-right">
                      <p className="font-mono text-lg text-purple-600 dark:text-purple-400">{p.avgTime}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">avg duration</p>
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
          <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
            <CardHeader>
              <CardTitle>Training Pipeline Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {trainingHistory?.slice(0, 10).map((h, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <div className="w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                      <span className="text-xs font-bold text-purple-600 dark:text-purple-400">{i + 1}</span>
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-gray-900 dark:text-white">{h.agent}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {new Date(h.timestamp).toLocaleString()} • {h.duration}s
                      </p>
                    </div>
                    <span className="px-2 py-1 text-xs bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 rounded">
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