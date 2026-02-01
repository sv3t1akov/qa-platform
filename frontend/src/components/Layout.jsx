import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FlaskConical, 
  Flag, 
  Settings, 
  ChevronLeft,
  ChevronRight,
  Bug,
  Zap,
  Trophy,
  HelpCircle,
  User
} from 'lucide-react';
import clsx from 'clsx';
import { mockUserStats } from '../mocks/data';

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/lab', icon: FlaskConical, label: 'API Lab' },
  { path: '/flags', icon: Flag, label: 'Flags' },
];

export default function Layout({ children }) {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const isDemoMode = !import.meta.env.VITE_API_URL;
  const stats = mockUserStats;

  return (
    <div className="flex h-screen bg-pm-bg">
      {/* Sidebar */}
      <aside 
        className={clsx(
          'flex flex-col bg-pm-bg-lighter border-r border-pm-border transition-all duration-300',
          collapsed ? 'w-16' : 'w-64'
        )}
      >
        {/* Logo */}
        <div className="flex items-center h-14 px-4 border-b border-pm-border">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-pm-orange to-pm-orange-dark flex items-center justify-center">
              <Bug className="w-5 h-5 text-white" />
            </div>
            {!collapsed && (
              <span className="font-semibold text-pm-text whitespace-nowrap">
                QA Platform
              </span>
            )}
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 px-2 space-y-1">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path || 
              (item.path !== '/' && location.pathname.startsWith(item.path));
            
            return (
              <Link
                key={item.path}
                to={item.path}
                className={clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200',
                  isActive 
                    ? 'bg-pm-orange/10 text-pm-orange' 
                    : 'text-pm-text-muted hover:bg-pm-bg-hover hover:text-pm-text'
                )}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                {!collapsed && <span className="font-medium">{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Demo Mode Badge */}
        {isDemoMode && !collapsed && (
          <div className="mx-3 mb-3 px-3 py-2 bg-pm-yellow/10 rounded-lg border border-pm-yellow/30">
            <div className="flex items-center gap-2 text-pm-yellow text-sm">
              <Zap className="w-4 h-4" />
              <span className="font-medium">Demo Mode</span>
            </div>
            <p className="text-xs text-pm-text-muted mt-1">
              Using mock data
            </p>
          </div>
        )}

        {/* Stats Summary */}
        {!collapsed && (
          <div className="mx-3 mb-3 p-3 bg-pm-bg-card rounded-lg">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-pm-text-muted">Баллы</span>
              <span className="text-pm-orange font-medium">{stats.totalPoints} pts</span>
            </div>
            <div className="flex items-center gap-2">
              <Trophy className="w-4 h-4 text-pm-yellow" />
              <span className="text-sm text-pm-text-muted">{stats.rank}</span>
            </div>
          </div>
        )}

        {/* Collapse Button */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center justify-center h-12 border-t border-pm-border text-pm-text-muted hover:text-pm-text hover:bg-pm-bg-hover transition-colors"
        >
          {collapsed ? (
            <ChevronRight className="w-5 h-5" />
          ) : (
            <ChevronLeft className="w-5 h-5" />
          )}
        </button>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <header className="h-14 flex items-center justify-between px-6 border-b border-pm-border bg-pm-bg-lighter">
          <div className="flex items-center gap-4">
            <h1 className="text-lg font-semibold text-pm-text">
              {navItems.find(item => 
                item.path === location.pathname || 
                (item.path !== '/' && location.pathname.startsWith(item.path))
              )?.label || 'QA Training'}
            </h1>
          </div>
          
          <div className="flex items-center gap-3">
            <button className="p-2 rounded-lg text-pm-text-muted hover:text-pm-text hover:bg-pm-bg-hover transition-colors">
              <HelpCircle className="w-5 h-5" />
            </button>
            <button className="p-2 rounded-lg text-pm-text-muted hover:text-pm-text hover:bg-pm-bg-hover transition-colors">
              <Settings className="w-5 h-5" />
            </button>
            
            {/* User Avatar */}
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-pm-blue to-pm-purple flex items-center justify-center text-white text-sm font-medium">
              QA
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 overflow-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
