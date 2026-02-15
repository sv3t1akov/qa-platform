import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { 
  Trophy, 
  Bug, 
  Target, 
  Clock, 
  ChevronRight, 
  ChevronDown,
  Lock,
  CheckCircle,
  Play,
  Zap,
  Flag,
  Gauge,
  UserX,
  Type,
  GitBranch,
  Timer,
  ShieldOff,
  ListOrdered,
  Rocket,
  BookOpen,
  Search,
  Send
} from 'lucide-react';
import clsx from 'clsx';
import { api, isDemoMode } from '../services/api';
import {
  domains,
  missionsByDomain,
  mockUserStats,
  mockFoundFlags,
  isTierUnlocked,
  landingTechniques,
  landingTiers,
  landingFlagExamples,
} from '../mocks/data';
import RankProgress from '../components/RankProgress';

const techniqueIcons = {
  boundary: Gauge,
  idor: UserX,
  fuzzing: Type,
  state: GitBranch,
  race: Timer,
  auth: ShieldOff,
};

const stepIcons = [ListOrdered, Rocket, BookOpen, Search, Send];
const stepLabels = [
  'Выбор миссии по домену и уровню сложности',
  'Запуск лаборатории и получение персонального API endpoint',
  'Изучение OpenAPI спецификации',
  'Поиск багов через тестирование edge cases',
  'Сдача найденного флага',
];

// Get all missions from all domains flattened (works with mock or API data)
function getAllMissions(domainsList, missionsByDomainMap) {
  const missions = [];
  for (const [domainId, tiers] of Object.entries(missionsByDomainMap || {})) {
    const domain = (domainsList || []).find((d) => d.id === domainId);
    for (const [tier, tierData] of Object.entries(tiers)) {
      // Поддержка нового формата (объект с полями missions, unlocked, progress) и старого (массив)
      let tierMissions = [];
      let tierUnlocked = false;
      
      if (tierData && typeof tierData === 'object' && 'missions' in tierData) {
        // Новый формат из API
        tierMissions = Array.isArray(tierData.missions) ? tierData.missions : [];
        tierUnlocked = tierData.unlocked ?? (tier === 'T1'); // T1 всегда разблокирован
      } else if (Array.isArray(tierData)) {
        // Старый формат (моки)
        tierMissions = tierData;
        tierUnlocked = isTierUnlocked(domainId, tier, missionsByDomainMap);
      }
      
      tierMissions.forEach((mission) => {
        missions.push({
          ...mission,
          tier,
          domain: domainId,
          domainName: domain?.name,
          domainIcon: domain?.icon,
          domainColor: domain?.color,
          tierUnlocked, // Добавляем информацию о разблокировке тира
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
  // Миссия заблокирована, если статус locked ИЛИ тир не разблокирован
  const isLocked = mission.status === 'locked' || !mission.tierUnlocked;

  const tierColors = {
    T1: 'bg-pm-green/20 text-pm-green',
    T2: 'bg-pm-blue/20 text-pm-blue',
    T3: 'bg-pm-purple/20 text-pm-purple',
    T4: 'bg-pm-orange/20 text-pm-orange',
    T5: 'bg-pm-orange/20 text-pm-orange',
  };

  return (
    <Link
      to={isLocked ? '#' : `/lab?domain=${mission.domain}&mission=${mission.id}`}
      onClick={(e) => {
        if (isLocked) {
          e.preventDefault();
        }
      }}
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
        to="/lab"
        className="block px-5 py-3 text-center text-sm text-pm-orange hover:bg-pm-bg-hover transition-colors"
      >
        К лабораториям →
      </Link>
    </div>
  );
}

export default function Dashboard() {
  const missionsRef = useRef(null);
  const [displayDomains, setDisplayDomains] = useState(isDemoMode ? domains : []);
  const [displayMissionsByDomain, setDisplayMissionsByDomain] = useState(isDemoMode ? missionsByDomain : {});
  const [missions, setMissions] = useState([]);
  const [stats, setStats] = useState(mockUserStats);
  const [recentFlags, setRecentFlags] = useState(mockFoundFlags);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  const scrollToMissions = () => {
    missionsRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    let cancelled = false;
    if (isDemoMode) {
      setMissions(getAllMissions(domains, missionsByDomain));
      setTimeout(() => {
        if (!cancelled) setLoading(false);
      }, 300);
      return () => { cancelled = true; };
    }
    async function load() {
      const [dataRes, statsRes, flagsRes] = await Promise.all([
        api.loadDomainsAndMissions(),
        api.getUserStats(),
        api.getUserFlags(),
      ]);
      if (cancelled) return;
      if (dataRes?.domains) {
        setDisplayDomains(dataRes.domains);
        setDisplayMissionsByDomain(dataRes.missionsByDomain || {});
        setMissions(getAllMissions(dataRes.domains, dataRes.missionsByDomain));
      }
      if (statsRes) {
        // Обработка новой структуры ранга (объект) или старой (строка)
        let rankData = statsRes.rank;
        if (typeof rankData === 'string') {
          // Старый формат - преобразуем в новый
          rankData = {
            id: rankData.toLowerCase().replace(/\s+/g, '_'),
            nameRu: rankData,
            nameEn: rankData,
            color: '#9CA3AF'
          };
        }
        
        setStats({
          totalPoints: statsRes.totalPoints ?? 0,
          rank: rankData,
          nextRank: statsRes.nextRank ?? null,
          rankProgress: statsRes.rankProgress ?? 0,
          pointsToNextRank: statsRes.pointsToNextRank ?? 0,
          completedMissions: statsRes.completedMissions ?? 0,
          foundBugs: statsRes.foundBugs ?? 0,
          totalBugs: statsRes.totalBugs ?? 0,
        });
      }
      // Обработка флагов - может быть массивом или объектом с полем flags
      let flagsArray = [];
      if (Array.isArray(flagsRes)) {
        flagsArray = flagsRes;
      } else if (flagsRes && Array.isArray(flagsRes.flags)) {
        flagsArray = flagsRes.flags;
      }
      
      if (flagsArray.length > 0) {
        setRecentFlags(
          flagsArray.map((f) => ({
            id: f.id,
            bugTitle: f.bugTitle || f.bugTitle || 'Unknown',
            missionTitle: f.missionTitle || f.missionId || 'Unknown',
            points: f.points || 0,
            foundAt: f.foundAt || new Date().toISOString(),
          }))
        );
      }
      setLoading(false);
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const filteredMissions = missions.filter(m => {
    if (filter === 'all') return true;
    if (filter === 'available') return m.status === 'available' || m.status === 'in_progress';
    if (filter === 'completed') return m.status === 'completed';
    if (['T1', 'T2', 'T3', 'T4', 'T5'].includes(filter)) return m.tier === filter;
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
      {/* Hero */}
      <section className="mb-16 text-center">
        <h1 className="text-3xl md:text-4xl font-bold text-pm-text mb-4">
          QA Training Platform
        </h1>
        <p className="text-lg text-pm-text-muted max-w-2xl mx-auto mb-8">
          Платформа в стиле CTF для практики тестирования API. Запускайте лаборатории, изучайте OpenAPI, находите баги и сдавайте флаги.
        </p>
        <button
          type="button"
          onClick={scrollToMissions}
          className="inline-flex items-center gap-2 px-6 py-3 bg-pm-orange hover:bg-pm-orange-hover text-white font-medium rounded-lg transition-colors"
        >
          К миссиям
          <ChevronDown className="w-5 h-5" />
        </button>
      </section>

      {/* 6 techniques */}
      <section className="mb-16">
        <h2 className="text-xl font-semibold text-pm-text mb-6">6 техник тестирования</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {landingTechniques.map((t) => {
            const Icon = techniqueIcons[t.id];
            return (
              <div
                key={t.id}
                className="bg-pm-bg-card rounded-xl border border-pm-border p-5"
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 rounded-lg bg-pm-orange/20">
                    <Icon className="w-5 h-5 text-pm-orange" />
                  </div>
                  <h3 className="font-semibold text-pm-text">{t.title}</h3>
                </div>
                <p className="text-sm text-pm-text-muted">{t.description}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* 6 domains */}
      <section className="mb-16">
        <h2 className="text-xl font-semibold text-pm-text mb-6">6 доменов для практики</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {(displayDomains.length ? displayDomains : domains).map((d) => (
            <div key={d.id} className="bg-pm-bg-card rounded-xl border border-pm-border p-5">
              <span className="text-2xl mb-2 block">{d.icon}</span>
              <h3 className="font-semibold text-pm-text">{d.name}</h3>
              <p className="text-sm text-pm-text-muted mt-1">{d.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 5 steps timeline */}
      <section className="mb-16">
        <h2 className="text-xl font-semibold text-pm-text mb-6">Инструкция по работе с лабораториями</h2>
        <div className="relative max-w-2xl">
          <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-pm-border" />
          {stepLabels.map((label, i) => {
            const StepIcon = stepIcons[i];
            return (
              <div key={i} className="relative flex gap-4 pb-8 last:pb-0">
                <div className="relative z-10 flex-shrink-0 w-10 h-10 rounded-full bg-pm-orange/20 border-2 border-pm-orange flex items-center justify-center">
                  <StepIcon className="w-5 h-5 text-pm-orange" />
                </div>
                <div className="pt-1">
                  <span className="text-sm font-medium text-pm-orange">Шаг {i + 1}</span>
                  <p className="text-pm-text mt-1">{label}</p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Flag format */}
      <section className="mb-16">
        <h2 className="text-xl font-semibold text-pm-text mb-4">Формат флагов</h2>
        <p className="text-pm-text-muted mb-4">
          Флаги имеют вид <strong className="text-pm-text">QA_FLAG&#123;...&#125;</strong>. Примеры формата (иллюстрация):
        </p>
        <div className="font-mono text-sm bg-pm-bg rounded-lg p-4 border border-pm-border space-y-2">
          {landingFlagExamples.map((ex) => (
            <div key={ex} className="text-pm-text-muted">{ex}</div>
          ))}
        </div>
      </section>

      {/* T1–T5 tiers */}
      <section className="mb-16">
        <h2 className="text-xl font-semibold text-pm-text mb-6">Система уровней T1 → T5</h2>
        <div className="overflow-x-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 min-w-[280px]">
            {landingTiers.map((t) => (
              <div key={t.tier} className="bg-pm-bg-card rounded-xl border border-pm-border p-4">
                <span className="inline-block px-2 py-0.5 rounded text-xs font-bold bg-pm-orange/20 text-pm-orange mb-3">
                  {t.tier}
                </span>
                <p className="text-sm text-pm-text font-medium mb-1">{t.focus}</p>
                <p className="text-xs text-pm-text-muted">{t.unlock}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Missions block */}
      <section id="missions" ref={missionsRef} className="scroll-mt-4">
        <h2 className="text-xl font-semibold text-pm-text mb-6">Ваши миссии</h2>
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
          <RankProgress
            rank={stats.rank}
            nextRank={stats.nextRank}
            progress={stats.rankProgress}
            pointsToNext={stats.pointsToNextRank}
            totalPoints={stats.totalPoints}
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
              { id: 'T4', label: 'T4' },
              { id: 'T5', label: 'T5' },
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
      </section>
    </div>
  );
}
