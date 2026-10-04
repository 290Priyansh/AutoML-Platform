'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { cn } from '../../lib/utils';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';

interface SHAPFeatureImportanceProps {
  importance: Record<string, number>;
  topN?: number;
  height?: number;
}

export function SHAPFeatureImportance({ importance, topN = 15, height = 400 }: SHAPFeatureImportanceProps) {
  const sortedFeatures = Object.entries(importance)
    .sort(([, a], [, b]) => Math.abs(b) - Math.abs(a))
    .slice(0, topN)
    .map(([feature, value]) => ({
      feature: feature.length > 30 ? feature.substring(0, 30) + '...' : feature,
      fullFeature: feature,
      importance: value,
      absImportance: Math.abs(value),
      direction: value >= 0 ? 'positive' : 'negative',
    }));

  const maxAbs = Math.max(...sortedFeatures.map(f => f.absImportance));

  return (
    <div className="w-full h-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={sortedFeatures} layout="vertical" margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
          <XAxis 
            type="number" 
            domain={[-maxAbs * 1.1, maxAbs * 1.1]}
            tickFormatter={(v) => v.toFixed(3)}
            tick={{ fontSize: 11, fill: '#6b7280' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis 
            type="category" 
            dataKey="feature" 
            width={200}
            tick={{ fontSize: 11, fill: '#374151' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip 
            formatter={(value: any) => [typeof value === 'number' ? value.toFixed(4) : String(value), 'SHAP Value']}
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
            }}
            labelFormatter={(name) => sortedFeatures.find(f => f.feature === name)?.fullFeature || name}
          />
          <Bar 
            dataKey="absImportance" 
            radius={[0, 4, 4, 0]}
          >
            {sortedFeatures.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={entry.direction === 'positive' ? '#10b981' : '#ef4444'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

interface SHAPSummaryProps {
  shapValues: Array<{
    feature: string;
    shapValue: number;
    featureValue: number;
  }>;
  topN?: number;
}

export function SHAPSummaryPlot({ shapValues, topN = 20 }: SHAPSummaryProps) {
  // Group by feature and calculate mean |SHAP|
  const featureStats = shapValues.reduce((acc, { feature, shapValue, featureValue }) => {
    if (!acc[feature]) {
      acc[feature] = { values: [], featureValues: [] };
    }
    acc[feature].values.push(shapValue);
    acc[feature].featureValues.push(featureValue);
    return acc;
  }, {} as Record<string, { values: number[]; featureValues: number[] }>);

  const features = Object.entries(featureStats)
    .map(([feature, { values, featureValues }]) => ({
      feature,
      meanAbsShap: values.reduce((a, b) => a + Math.abs(b), 0) / values.length,
      meanShap: values.reduce((a, b) => a + b, 0) / values.length,
      meanFeatureValue: featureValues.reduce((a, b) => a + b, 0) / featureValues.length,
      count: values.length,
    }))
    .sort((a, b) => b.meanAbsShap - a.meanAbsShap)
    .slice(0, topN);

  return (
    <div className="space-y-2">
      {features.map((f, i) => (
        <div key={f.feature} className="flex items-center gap-3">
          <div className="w-48 text-right text-sm text-gray-600 dark:text-gray-400 truncate pr-2">
            {f.feature}
          </div>
          <div className="flex-1 h-6 relative">
            <div className="absolute inset-0 bg-gray-200 dark:bg-gray-700 rounded-full" />
            <div 
              className="absolute top-0 bottom-0 rounded-full transition-all duration-300"
              style={{
                left: '50%',
                width: `${Math.min(Math.abs(f.meanShap) / Math.max(...features.map(f => Math.abs(f.meanShap))) * 50, 50)}%`,
                background: f.meanShap >= 0 ? 'linear-gradient(to right, #10b981, #34d399)' : 'linear-gradient(to left, #ef4444, #f87171)',
                transform: f.meanShap >= 0 ? 'none' : 'translateX(-100%)',
              }}
            />
            <div className="absolute top-0 bottom-0 left-1/2 w-px bg-gray-400" />
          </div>
          <span className="w-16 text-sm text-gray-600 dark:text-gray-400 font-mono">
            {f.meanShap >= 0 ? '+' : ''}{f.meanShap.toFixed(3)}
          </span>
        </div>
      ))}
    </div>
  );
}

export function SHAPDashboard({ 
  featureImportance, 
  shapValues 
}: { 
  featureImportance: Record<string, number>;
  shapValues?: Array<{ feature: string; shapValue: number; featureValue: number }>;
}) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">SHAP Explainability</h3>
        <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-green-500" />
            Positive impact
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-red-500" />
            Negative impact
          </span>
        </div>
      </div>
      
      <Tabs defaultValue="importance" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="importance">Feature Importance</TabsTrigger>
          <TabsTrigger value="summary">Summary Plot</TabsTrigger>
          <TabsTrigger value="dependence">Dependence</TabsTrigger>
        </TabsList>
        
        <TabsContent value="importance" className="mt-4">
          <SHAPFeatureImportance importance={featureImportance} />
        </TabsContent>
        
        <TabsContent value="summary" className="mt-4">
          {shapValues ? (
            <SHAPSummaryPlot shapValues={shapValues} />
          ) : (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              SHAP summary data not available
            </div>
          )}
        </TabsContent>
        
        <TabsContent value="dependence" className="mt-4">
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            SHAP dependence plots require individual feature analysis
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}