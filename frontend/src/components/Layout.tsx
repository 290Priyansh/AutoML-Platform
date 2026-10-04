import { Link, Outlet, useLocation } from 'react-router-dom';
import { cn } from '../lib/utils';
import {
  LayoutDashboard,
  Upload,
  ListChecks,
  BarChart2,
  Menu,
  X,
  ChevronDown,
  GitBranch,
} from 'lucide-react';
import { useState } from 'react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'New Job', href: '/jobs/new', icon: Upload },
  { name: 'Jobs', href: '/jobs', icon: ListChecks },
  { name: 'Models', href: '/models', icon: BarChart2 },
];

export function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const location = useLocation();

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-[2px] lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-[232px] bg-[var(--bg)] border-r border-[var(--border)] transform transition-transform duration-200 lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between h-14 px-5 border-b border-[var(--border)]">
            <Link to="/" className="flex items-center gap-2.5">
              <GitBranch className="w-5 h-5 text-[var(--accent)]" />
              <span className="text-base font-semibold tracking-tight text-[var(--text)]">AutoML</span>
            </Link>
            <button
              className="lg:hidden p-1.5 squircle-sm text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-2)]"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <nav className="flex-1 px-3 py-3 space-y-1 overflow-y-auto">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href || 
                (item.href !== '/' && location.pathname.startsWith(item.href));
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'relative flex items-center gap-3 px-3 h-9 squircle-sm text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-[var(--surface-2)] text-[var(--text)] font-semibold'
                      : 'text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-2)]/60'
                  )}
                >
                  {isActive && (
                    <span className="absolute left-0 top-1.5 bottom-1.5 w-[2px] bg-[var(--accent)] rounded-full" />
                  )}
                  <item.icon className="w-4 h-4 flex-shrink-0" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>

          <div className="p-4 border-t border-[var(--border)]">
            <div className="text-[11px] font-mono text-[var(--text-muted)] tracking-tight">
              AutoML Platform v0.1.0
            </div>
          </div>
        </div>
      </aside>

      <div className="lg:pl-[232px]">
        <header className="sticky top-0 z-30 bg-[var(--bg)]/90 backdrop-blur-sm border-b border-[var(--border)]">
          <div className="flex items-center justify-between h-14 px-4 sm:px-8">
            <button
              className="lg:hidden p-1.5 squircle-sm text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-2)]"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu className="w-5 h-5" />
            </button>

            <div className="flex-1 lg:flex-none" />

            <div className="flex items-center gap-4">
              <HealthIndicator />

              <div className="relative">
                <button
                  className="flex items-center gap-2 p-1.5 squircle-sm hover:bg-[var(--surface-2)] cursor-pointer"
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                >
                  <div className="w-7 h-7 squircle-sm bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center">
                    <span className="text-xs font-semibold text-[var(--text)]">U</span>
                  </div>
                  <span className="hidden md:block text-xs font-medium text-[var(--text)]">User</span>
                  <ChevronDown className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                </button>

                {userMenuOpen && (
                  <>
                    <div className="fixed inset-0 z-40" onClick={() => setUserMenuOpen(false)} />
                    <div className="absolute right-0 mt-2 w-48 bg-[var(--surface)] squircle-md shadow-[var(--shadow-subtle)] border border-[var(--border)] py-1 z-50">
                      <Link
                        to="/settings"
                        className="block px-3.5 py-1.5 text-xs text-[var(--text)] hover:bg-[var(--surface-2)]"
                        onClick={() => setUserMenuOpen(false)}
                      >
                        Settings
                      </Link>
                      <button
                        className="w-full text-left px-3.5 py-1.5 text-xs text-[var(--text)] hover:bg-[var(--surface-2)] cursor-pointer"
                        onClick={() => setUserMenuOpen(false)}
                      >
                        Sign out
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </header>

        <main className="p-4 sm:p-8 max-w-[1280px] mx-auto w-full">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

function HealthIndicator() {
  return (
    <div className="flex items-center gap-2">
      <span className="w-2 h-2 rounded-full bg-[var(--status-success)]" />
      <span className="text-[13px] text-[var(--text-muted)]">Healthy</span>
    </div>
  );
}