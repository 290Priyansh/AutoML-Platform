export function PlotsTab({ plots }: { plots: Record<string, string> }) {
  if (!plots || Object.keys(plots).length === 0) {
    return (
      <div className="text-center py-16">
        <div className="w-12 h-12 mx-auto text-gray-400 mb-4">
          <svg className="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-2-2l1.586-1.586a2 2 0 012.828 0L20 14" />
          </svg>
        </div>
        <p className="text-gray-500 dark:text-gray-400">No plots available for this job</p>
        <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">Plots are generated after model evaluation completes</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Visualizations</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">{Object.keys(plots).length} plots available</p>
      </div>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {Object.entries(plots).map(([name, url]) => (
          <div key={name} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 overflow-hidden rounded-xl hover:shadow-lg transition-shadow group">
            <div className="relative h-48 bg-gray-100 dark:bg-gray-700 overflow-hidden">
              <img 
                src={url} 
                alt={name} 
                className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                loading="lazy"
              />
            </div>
            <div className="p-4">
              <h4 className="font-medium text-gray-900 dark:text-white truncate mb-2">{name.replace(/_/g, ' ')}</h4>
              <a 
                href={url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-sm text-purple-600 dark:text-purple-400 hover:underline"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
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