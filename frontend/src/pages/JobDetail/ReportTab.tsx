export function ReportTab({ 
  report, 
  onDownload 
}: { 
  report?: { report_md: string; report_pdf_url?: string }; 
  onDownload: (format: 'md' | 'pdf') => Promise<void> 
}) {
  if (!report?.report_md) {
    return (
      <div className="text-center py-16">
        <svg className="w-12 h-12 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p className="text-gray-500 dark:text-gray-400">Report not yet generated</p>
        <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">Report is generated after pipeline completion</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">AutoML Report</h3>
        <div className="flex items-center gap-2">
          <button 
            type="button"
            className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2"
            onClick={() => onDownload('md')}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Download .md
          </button>
          <button 
            type="button"
            className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2"
            onClick={() => onDownload('pdf')}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Download .pdf
          </button>
        </div>
      </div>
      <div className="prose prose-gray dark:prose-invert max-w-none markdown-content border border-gray-200 dark:border-gray-700 rounded-xl p-6 bg-white dark:bg-gray-800 max-h-[70vh] overflow-y-auto whitespace-pre-wrap font-mono text-sm">
        {report.report_md}
      </div>
    </div>
  );
}