export function PlotsTab({ plots }: { plots: Record<string, string> }) {
  if (!plots || Object.keys(plots).length === 0) {
    return (
      <div className="surface-card squircle-lg border border-[var(--border)] text-center py-16 px-4">
        <div className="w-10 h-10 mx-auto text-[var(--text-muted)] mb-3">
          <svg className="w-full h-full" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-2-2l1.586-1.586a2 2 0 012.828 0L20 14" />
          </svg>
        </div>
        <p className="text-sm font-medium text-[var(--text)]">No plots available for this job</p>
        <p className="text-xs text-[var(--text-muted)] mt-1">Plots are generated after model evaluation completes</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-medium text-[var(--text)]">Visualizations</h3>
        <p className="font-mono text-xs tabular-nums text-[var(--text-muted)]">{Object.keys(plots).length} plots available</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {Object.entries(plots).map(([name, url]) => (
          <div key={name} className="surface-card squircle-lg border border-[var(--border)] overflow-hidden group">
            <div className="relative h-44 bg-[var(--surface-2)] overflow-hidden border-b border-[var(--border)]">
              <img 
                src={url} 
                alt={name} 
                className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-102"
                loading="lazy"
              />
            </div>
            <div className="p-3.5">
              <h4 className="text-xs font-medium text-[var(--text)] truncate mb-2">{name.replace(/_/g, ' ')}</h4>
              <a 
                href={url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 font-mono text-xs text-[var(--accent)] hover:underline"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                View full size
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}