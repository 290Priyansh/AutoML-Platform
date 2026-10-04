export interface PlotTabProps {
  plots: Record<string, string>;
}

export interface ExplainabilityTabProps {
  featureImportance: Record<string, number>;
  shapValues: any;
}

export interface ReportTabProps {
  report?: { report_md: string; report_pdf_url?: string };
  onDownload: (format: 'md' | 'pdf') => Promise<void>;
}

export interface DeploymentTabProps {
  jobId: string;
  models: any[];
  endpoints: Record<string, string>;
  onDeploy: (index: number) => Promise<void>;
  isDeploying: boolean;
}