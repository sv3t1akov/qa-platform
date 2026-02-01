import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Trophy, 
  Bug, 
  Target, 
  Clock, 
  ChevronRight, 
  Lock,
  CheckCircle,
  Play,
  Zap,
  TrendingUp,
  Flag
} from 'lucide-react';
import clsx from 'clsx';
import { api, isDemoMode } from '../services/api';
import { domains, missionsByDomain, mockUserStats, mockFoundFlags } from '../mocks/data';

// Get all missions from all domains flattened
function getAllMissions() {
  const missions = [];
  for (const [domainId, tiers] of Object.entries(missionsByDomain)) {
    const domain = domains.find(d => d.id === domainId);
    for (const [tier, tierMissions] of Object.entries(tiers)) {
      tierMissions.forEach(mission => {
        missions.push({
          ...mission,
          tier,
          domain: domainId,
          domainName: domain?.name,
          domainIcon: domain?.icon,
          domainColor: domain?.color,
        });
      });
    }
  }
  return missions;
}

const statusIcons = {
  available: Play,
  in_progress: Zap,
  completed: CheckCircle,
  locked: Lock,
};

function MissionCard({ mission }) {
  const StatusIcon = statusIcons[mission.status] || Play;
  const progress = mission.bugs > 0 ? (mission.foundBugs / mission.bugs) * 100 : 0;
  const isLocked = mission.status === 'locked';

  const tierColors = {
    T1: 'bg-pm-green/20 text-pm-green',
    T2: 'bg-pm-blue/20 text-pm-blue',
    T3: 'bg-pm-purple/20 text-pm-purple',
  };

  return (
    <Link
      to={isLocked ? '#' : `/lab?domain=${mission.domain}&mission=${mission.id}`}
      className={clsx(
        'group block bg-pm-bg-card rounded-xl border border-pm-border overflow-hidden transition-all duration-300',
        isLocked 
          ? 'opacity-60 cursor-not-allowed' 
          : 'hover:border-pm-orange/50 hover:shadow-lg hover:shadow-pm-orange/5'
      )}
    >
      {/* Header with gradient */}
      <div className={clsx('h-2 bg-gradient-to-r', mission.domainColor || 'from-pm-orange to-orange-600')} />
      
      <div className="p-5">
        {/* Title Row */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className={clsx('px-2 py-0.5 rounded text-xs font-bold', tierColors[mission.tier])}>
                {mission.tier}
              </span>
              <span className="text-xs text-pm-text-muted flex items-center gap-1">
                {mission.domainIcon} {mission.domainName}
              </span>
            </div>
            <h3 className="text-lg font-semibold text-pm-text group-hover:text-pm-orange transition-colors">
              {mission.title}
            </h3>
          </div>
          
          <div className={clsx(
            'p-2 rounded-lg',
            mission.status === 'completed' && 'bg-pm-green/20 text-pm-green',
            mission.status === 'in_progress' && 'bg-pm-yellow/20 text-pm-yellow',
            mission.status === 'available' && 'bg-pm-bg-hover text-pm-text-muted',
            mission.status === 'locked' && 'bg-pm-bg-hover text-pm-text-dim',
          )}>
            <StatusIcon className="w-5 h-5" />
          </div>
        </div>

        {/* Description */}
        <p className="text-sm text-pm-text-muted mb-4 line-clamp-2">
          {mission.description}
        </p>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-pm-text-muted">Bugs found</span>
            <span className="text-pm-text">{mission.foundBugs}/{mission.bugs}</span>
          </div>
          <div className="h-1.5 bg-pm-bg rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-pm-orange to-pm-orange-hover rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-pm-border">
          <div className="flex items-center gap-4 text-sm text-pm-text-muted">
            <div className="flex items-center gap-1">
              <Trophy className="w-4 h-4 text-pm-yellow" />
              <span>{mission.points} pts</span>
            </div>
            <div className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              <span>{mission.estimatedTime}</span>
            </div>
          </div>
          
          {!isLocked && (
            <ChevronRight className="w-5 h-5 text-pm-text-muted group-hover:text-pm-orange group-hover:translate-x-1 transition-all" />
          )}
        </div>
      </div>
    </Link>
  );
}

function StatsCard({ icon: Icon, label, value, color }) {
  return (
    <div className="bg-pm-bg-card rounded-xl border border-pm-border p-5">
      <div className="flex items-center gap-4">
        <div className={clsx('p-3 rounded-xl', color)}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        <div>
          <p className="text-sm text-pm-text-muted">{label}</p>
          <p className="text-2xl font-bold text-pm-text">{value}</p>
        </div>
      </div>
    </div>
  );
}

function RecentActivity({ flags }) {
  const formatTime = (isoString) => {
    const date = new Date(isoString);
    const now = new Date();
    const diff = now - date;
    
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (days > 0) return `${days} дн. назад`;
    if (hours > 0) return `${hours} ч. назад`;
    return 'недавно';
  };

  return (
    <div className="bg-pm-bg-card rounded-xl border border-pm-border overflow-hidden">
      <div className="px-5 py-4 border-b border-pm-border">
        <h3 className="font-semibold text-pm-text">Последняя активность</h3>
      </div>
      <div className="divide-y divide-pm-border">
        {flags.slice(0, 5).map((flag) => (
          <div key={flag.id} className="px-5 py-3 flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-pm-green/20 flex items-center justify-center">
              <Bug className="w-4 h-4 text-pm-green" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-pm-text truncate">{flag.bugTitle}</p>
              <p className="text-xs text-pm-text-muted">{flag.missionTitle}</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-pm-yellow">+{flag.points}</p>
              <p className="text-xs text-pm-text-muted">{formatTime(flag.foundAt)}</p>
            </div>
          </div>
        ))}
      </div>
      <Link 
        to="/flags"
        className="block px-5 py-3 text-center text-sm text-pm-orange hover:bg-pm-bg-hover transition-colors"
      >
        Все флаги →
      </Link>
    </div>
  );
}

export default function Dashboard() {
  const [missions, setMissions] = useState([]);
  const [stats, setStats] = useState(mockUserStats);
  const [recentFlags, setRecentFlags] = useState(mockFoundFlags);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    if (isDemoMode) {
      setTimeout(() => {
        if (!cancelled) {
          setMissions(getAllMissions());
          setLoading(false);
        }
      }, 300);
      return () => { cancelled = true; };
    }
    async function load() {
      setMissions(getAllMissions());
      const [statsRes, flagsRes] = await Promise.all([api.getUserStats(), api.getUserFlags()]);
      if (!cancelled && statsRes) {
        setStats({
          totalPoints: statsRes.totalPoints ?? 0,
          rank: statsRes.rank ?? 'Newbie',
          completedMissions: statsRes.completedMissions ?? 0,
          foundBugs: statsRes.foundBugs ?? 0,
          totalBugs: statsRes.totalBugs ?? 0,
        });
      }
      if (!cancelled && Array.isArray(flagsRes)) {
        setRecentFlags(flagsRes.map((f) => ({
          id: f.id,
          bugTitle: f.bugTitle,
          missionTitle: f.missionId,
          points: f.points,
          foundAt: f.foundAt,
        })));
      }
      if (!cancelled) setLoading(false);
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const filteredMissions = missions.filter(m => {
    if (filter === 'all') return true;
    if (filter === 'available') return m.status === 'available' || m.status === 'in_progress';
    if (filter === 'completed') return m.status === 'completed';
    if (['T1', 'T2', 'T3'].includes(filter)) return m.tier === filter;
    return m.domain === filter;
  });

  if (loading) {
    return (
      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 bg-pm-bg-card rounded-xl animate-shimmer" />
          ))}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-64 bg-pm-bg-card rounded-xl animate-shimmer" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 animate-fade-in">
      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatsCard 
          icon={Trophy}
          label="Всего баллов"
          value={stats.totalPoints}
          color="bg-gradient-to-br from-pm-yellow to-amber-600"
        />
        <StatsCard 
          icon={Target}
          label="Миссий завершено"
          value={stats.completedMissions}
          color="bg-gradient-to-br from-pm-green to-emerald-600"
        />
        <StatsCard 
          icon={Bug}
          label="Багов найдено"
          value={stats.foundBugs}
          color="bg-gradient-to-br from-pm-orange to-orange-600"
        />
        <StatsCard 
          icon={TrendingUp}
          label="Текущий ранг"
          value={stats.rank}
          color="bg-gradient-to-br from-pm-purple to-purple-600"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-3">
          {/* Filter Tabs */}
          <div className="flex items-center gap-2 mb-6 overflow-x-auto pb-2">
            {[
              { id: 'all', label: 'Все миссии' },
              { id: 'available', label: 'Доступные' },
              { id: 'T1', label: 'T1' },
              { id: 'T2', label: 'T2' },
              { id: 'T3', label: 'T3' },
              { id: 'completed', label: 'Завершённые' },
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setFilter(f.id)}
                className={clsx(
                  'px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all',
                  filter === f.id
                    ? 'bg-pm-orange text-white'
                    : 'bg-pm-bg-card text-pm-text-muted hover:bg-pm-bg-hover hover:text-pm-text'
                )}
              >
                {f.label}
              </button>
            ))}
          </div>

          {/* Missions Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {filteredMissions.map((mission) => (
              <MissionCard key={mission.id} mission={mission} />
            ))}
          </div>

          {filteredMissions.length === 0 && (
            <div className="text-center py-12 bg-pm-bg-card rounded-xl border border-pm-border">
              <Flag className="w-12 h-12 text-pm-text-dim mx-auto mb-4" />
              <p className="text-pm-text-muted">Миссии не найдены для выбранного фильтра.</p>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Start */}
          <div className="bg-pm-bg-card rounded-xl border border-pm-border p-5">
            <h3 className="font-semibold text-pm-text mb-4">Быстрый старт</h3>
            <Link
              to="/lab"
              className="flex items-center justify-between p-4 bg-pm-orange/10 border border-pm-orange/30 rounded-lg hover:bg-pm-orange/20 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-pm-orange/20">
                  <Play className="w-5 h-5 text-pm-orange" />
                </div>
                <div>
                  <p className="font-medium text-pm-text">API Labs</p>
                  <p className="text-xs text-pm-text-muted">Перейти к практике</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-pm-orange" />
            </Link>
          </div>

          {/* Recent Activity */}
          <RecentActivity flags={recentFlags} />
        </div>
      </div>
    </div>
  );
}
