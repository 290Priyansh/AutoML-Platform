export function ReportTab({ 
  report, 
  onDownload 
}: { 
  report?: { report_md: string; report_pdf_url?: string }; 
  onDownload: (format: 'md' | 'pdf') => Promise<void> 
}) {
  if (!report?.report_md) {
    return (
      <div className="surface-card squircle-lg border border-[var(--border)] text-center py-16 px-4">
        <svg className="w-10 h-10 mx-auto text-[var(--text-muted)] mb-3" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p className="text-sm font-medium text-[var(--text)]">Report not yet generated</p>
        <p className="text-xs text-[var(--text-muted)] mt-1">Report is generated after pipeline completion</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-medium text-[var(--text)]">AutoML Report</h3>
        <div className="flex items-center gap-2">
          <button 
            type="button"
            className="h-8 px-3 border border-[var(--border)] rounded-[var(--r-sm)] squircle-sm bg-[var(--surface)] text-xs font-mono text-[var(--text)] hover:bg-[var(--surface-2)] flex items-center gap-1.5 transition-colors"
            onClick={() => onDownload('md')}
          >
            <svg className="w-3.5 h-3.5 text-[var(--text-muted)]" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Download .md
          </button>
          <button 
            type="button"
            className="h-8 px-3 border border-[var(--border)] rounded-[var(--r-sm)] squircle-sm bg-[var(--surface)] text-xs font-mono text-[var(--text)] hover:bg-[var(--surface-2)] flex items-center gap-1.5 transition-colors"
            onClick={() => onDownload('pdf')}
          >
            <svg className="w-3.5 h-3.5 text-[var(--text-muted)]" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Download .pdf
          </button>
        </div>
      </div>
      <div className="surface-card squircle-lg border border-[var(--border)] p-6 bg-[var(--surface)] text-[var(--text)] font-mono text-xs leading-relaxed max-h-[70vh] overflow-y-auto whitespace-pre-wrap">
        {report.report_md}
      </div>
    </div>
  );
}