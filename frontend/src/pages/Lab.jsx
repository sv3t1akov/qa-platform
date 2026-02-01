import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { 
  ArrowLeft, 
  Play, 
  Lock,
  CheckCircle,
  Clock, 
  Trophy,
  Bug,
  ChevronRight,
  BookOpen,
  Lightbulb,
  Copy,
  Zap,
  Target
} from 'lucide-react';
import clsx from 'clsx';
import { domains, missionsByDomain, getTierProgress, isTierUnlocked } from '../mocks/data';

// Domain Card Component
function DomainCard({ domain, onClick }) {
  const progress = domain.totalMissions > 0 
    ? Math.round((domain.completedMissions / domain.totalMissions) * 100) 
    : 0;

  return (
    <button
      onClick={onClick}
      className={clsx(
        'w-full text-left bg-pm-bg-card rounded-xl border overflow-hidden transition-all duration-300',
        'hover:scale-[1.02] hover:shadow-xl',
        domain.borderColor,
        'hover:border-opacity-70'
      )}
    >
      <div className={`h-2 bg-gradient-to-r ${domain.color}`} />
      <div className="p-6">
        <div className="flex items-start gap-4">
          <div className={clsx(
            'w-14 h-14 rounded-xl flex items-center justify-center text-3xl',
            domain.bgColor
          )}>
            {domain.icon}
          </div>
          <div className="flex-1">
            <h3 className="text-xl font-bold text-pm-text mb-1">{domain.name}</h3>
            <p className="text-sm text-pm-text-muted">{domain.description}</p>
          </div>
          <ChevronRight className="w-6 h-6 text-pm-text-muted" />
        </div>
        
        <div className="mt-5">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-pm-text-muted">Прогресс</span>
            <span className={domain.textColor}>
              {domain.completedMissions}/{domain.totalMissions} миссий
            </span>
          </div>
          <div className="h-2 bg-pm-bg rounded-full overflow-hidden">
            <div 
              className={`h-full bg-gradient-to-r ${domain.color} rounded-full transition-all duration-500`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>
    </button>
  );
}

// Tier Section Component
function TierSection({ tier, missions, domainId, onSelectMission }) {
  const isUnlocked = isTierUnlocked(domainId, tier);
  const progress = getTierProgress(domainId, tier);
  
  const tierColors = {
    T1: { bg: 'bg-pm-green/10', border: 'border-pm-green/30', text: 'text-pm-green' },
    T2: { bg: 'bg-pm-blue/10', border: 'border-pm-blue/30', text: 'text-pm-blue' },
    T3: { bg: 'bg-pm-purple/10', border: 'border-pm-purple/30', text: 'text-pm-purple' },
  };
  
  const colors = tierColors[tier] || tierColors.T1;

  if (!missions || missions.length === 0) return null;

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className={clsx(
            'px-3 py-1.5 rounded-lg text-sm font-bold',
            colors.bg, colors.border, colors.text,
            'border'
          )}>
            {tier}
          </span>
          <span className="text-pm-text-muted">
            {tier === 'T1' && 'Beginner'}
            {tier === 'T2' && 'Intermediate'}
            {tier === 'T3' && 'Advanced'}
          </span>
          {!isUnlocked && (
            <span className="flex items-center gap-1 text-sm text-pm-text-dim">
              <Lock className="w-4 h-4" />
              Требуется 80% в T{parseInt(tier.slice(1)) - 1}
            </span>
          )}
        </div>
        <div className="text-sm text-pm-text-muted">
          {progress.foundBugs || 0}/{progress.totalBugs || 0} багов найдено
        </div>
      </div>
      
      <div className="grid grid-cols-1 gap-4">
        {missions.map((mission) => (
          <MissionListItem 
            key={mission.id} 
            mission={mission} 
            tierUnlocked={isUnlocked}
            onClick={() => isUnlocked && mission.status !== 'locked' && onSelectMission(mission)}
          />
        ))}
      </div>
    </div>
  );
}

// Mission List Item Component
function MissionListItem({ mission, tierUnlocked, onClick }) {
  const isLocked = !tierUnlocked || mission.status === 'locked';
  const progress = mission.bugs > 0 ? (mission.foundBugs / mission.bugs) * 100 : 0;
  
  const statusConfig = {
    available: { icon: Play, color: 'text-pm-green', bg: 'bg-pm-green/20' },
    in_progress: { icon: Zap, color: 'text-pm-yellow', bg: 'bg-pm-yellow/20' },
    completed: { icon: CheckCircle, color: 'text-pm-green', bg: 'bg-pm-green/20' },
    locked: { icon: Lock, color: 'text-pm-text-dim', bg: 'bg-pm-bg-hover' },
  };
  
  const status = isLocked ? 'locked' : mission.status;
  const StatusIcon = statusConfig[status].icon;

  return (
    <button
      onClick={onClick}
      disabled={isLocked}
      className={clsx(
        'w-full text-left p-5 rounded-xl border transition-all duration-200',
        isLocked 
          ? 'bg-pm-bg-card/50 border-pm-border opacity-60 cursor-not-allowed' 
          : 'bg-pm-bg-card border-pm-border hover:border-pm-orange/50 hover:shadow-lg cursor-pointer'
      )}
    >
      <div className="flex items-start gap-4">
        <div className={clsx(
          'w-12 h-12 rounded-xl flex items-center justify-center',
          statusConfig[status].bg
        )}>
          <StatusIcon className={clsx('w-6 h-6', statusConfig[status].color)} />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-1">
            <h4 className="text-lg font-semibold text-pm-text">{mission.title}</h4>
            <span className={clsx(
              'px-2 py-0.5 rounded text-xs',
              mission.difficulty === 'Beginner' && 'bg-pm-green/20 text-pm-green',
              mission.difficulty === 'Intermediate' && 'bg-pm-yellow/20 text-pm-yellow',
              mission.difficulty === 'Advanced' && 'bg-pm-red/20 text-pm-red',
            )}>
              {mission.difficulty}
            </span>
          </div>
          <p className="text-sm text-pm-text-muted line-clamp-1">{mission.description}</p>
          
          <div className="flex items-center gap-6 mt-3">
            <div className="flex items-center gap-1 text-sm text-pm-text-muted">
              <Bug className="w-4 h-4" />
              <span>{mission.foundBugs}/{mission.bugs}</span>
            </div>
            <div className="flex items-center gap-1 text-sm text-pm-text-muted">
              <Trophy className="w-4 h-4 text-pm-yellow" />
              <span>{mission.points} pts</span>
            </div>
            <div className="flex items-center gap-1 text-sm text-pm-text-muted">
              <Clock className="w-4 h-4" />
              <span>{mission.estimatedTime}</span>
            </div>
          </div>
        </div>
        
        <div className="w-24 flex flex-col items-end">
          <span className="text-sm text-pm-text-muted mb-1">{Math.round(progress)}%</span>
          <div className="w-full h-2 bg-pm-bg rounded-full overflow-hidden">
            <div 
              className="h-full bg-pm-orange rounded-full"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>
    </button>
  );
}

// Mission Detail View Component
function MissionDetail({ mission, domain, onBack }) {
  const [labStarted, setLabStarted] = useState(false);
  const [copied, setCopied] = useState(false);
  
  const fullEndpoint = `${mission.baseUrl}${mission.endpoint}`;
  
  const copyEndpoint = () => {
    navigator.clipboard.writeText(fullEndpoint);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleStartLab = () => {
    setLabStarted(true);
  };

  return (
    <div className="animate-fade-in">
      {/* Back button */}
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-pm-text-muted hover:text-pm-text mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Назад к списку миссий</span>
      </button>

      {/* Mission Header */}
      <div className="bg-pm-bg-card rounded-xl border border-pm-border overflow-hidden mb-6">
        <div className={`h-2 bg-gradient-to-r ${domain.color}`} />
        <div className="p-6">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <span className={clsx(
                  'px-2 py-1 rounded text-xs font-bold',
                  domain.bgColor, domain.textColor
                )}>
                  {domain.name}
                </span>
                <span className={clsx(
                  'px-2 py-1 rounded text-xs',
                  mission.difficulty === 'Beginner' && 'bg-pm-green/20 text-pm-green',
                  mission.difficulty === 'Intermediate' && 'bg-pm-yellow/20 text-pm-yellow',
                  mission.difficulty === 'Advanced' && 'bg-pm-red/20 text-pm-red',
                )}>
                  {mission.difficulty}
                </span>
              </div>
              <h1 className="text-2xl font-bold text-pm-text mb-2">{mission.title}</h1>
              <p className="text-pm-text-muted max-w-2xl">{mission.description}</p>
            </div>

            <button
              onClick={handleStartLab}
              disabled={labStarted}
              className={clsx(
                'flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all',
                labStarted 
                  ? 'bg-pm-green text-white'
                  : 'bg-pm-orange hover:bg-pm-orange-hover text-white'
              )}
            >
              {labStarted ? (
                <>
                  <CheckCircle className="w-5 h-5" />
                  Лаба запущена
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" />
                  Запустить лабу
                </>
              )}
            </button>
          </div>

          {/* Stats */}
          <div className="flex items-center gap-6 mt-6 pt-6 border-t border-pm-border">
            <div className="flex items-center gap-2">
              <Trophy className="w-5 h-5 text-pm-yellow" />
              <span className="text-pm-text">{mission.points} баллов</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-pm-text-muted" />
              <span className="text-pm-text-muted">{mission.estimatedTime}</span>
            </div>
            <div className="flex items-center gap-2">
              <Bug className="w-5 h-5 text-pm-orange" />
              <span className="text-pm-text-muted">{mission.foundBugs}/{mission.bugs} багов найдено</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Theory & Hints */}
        <div className="lg:col-span-2 space-y-6">
          {/* Theory Block */}
          <div className="bg-pm-bg-card rounded-xl border border-pm-border p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-pm-blue/20">
                <BookOpen className="w-5 h-5 text-pm-blue" />
              </div>
              <h2 className="text-lg font-semibold text-pm-text">{mission.theory.title}</h2>
            </div>
            <div className="prose prose-invert max-w-none">
              <p className="text-pm-text-muted leading-relaxed whitespace-pre-line">
                {mission.theory.content}
              </p>
            </div>
          </div>

          {/* Hints Block */}
          <div className="bg-pm-bg-card rounded-xl border border-pm-border p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-pm-yellow/20">
                <Lightbulb className="w-5 h-5 text-pm-yellow" />
              </div>
              <h2 className="text-lg font-semibold text-pm-text">Подсказки</h2>
            </div>
            <div className="space-y-3">
              {mission.hints.map((hint, index) => (
                <div 
                  key={index}
                  className="flex items-start gap-3 p-4 bg-pm-yellow/5 rounded-lg border border-pm-yellow/20"
                >
                  <span className="text-pm-yellow">💡</span>
                  <p className="text-sm text-pm-text-muted">{hint}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column - Endpoint & Actions */}
        <div className="space-y-6">
          {/* Endpoint Block */}
          <div className="bg-pm-bg-card rounded-xl border border-pm-border p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-pm-green/20">
                <Target className="w-5 h-5 text-pm-green" />
              </div>
              <h2 className="text-lg font-semibold text-pm-text">API Endpoint</h2>
            </div>
            
            <div className="space-y-3">
              <div>
                <label className="text-xs text-pm-text-dim uppercase tracking-wide">Base URL</label>
                <div className="mt-1 p-3 bg-pm-bg rounded-lg">
                  <code className="text-sm text-pm-green font-mono break-all">
                    {mission.baseUrl}
                  </code>
                </div>
              </div>
              
              <div>
                <label className="text-xs text-pm-text-dim uppercase tracking-wide">Endpoint</label>
                <div className="mt-1 p-3 bg-pm-bg rounded-lg">
                  <code className="text-sm text-pm-blue font-mono">
                    {mission.endpoint}
                  </code>
                </div>
              </div>
              
              <button
                onClick={copyEndpoint}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-pm-bg-hover text-pm-text-muted hover:text-pm-text rounded-lg transition-colors"
              >
                {copied ? (
                  <>
                    <CheckCircle className="w-4 h-4 text-pm-green" />
                    <span className="text-pm-green">Скопировано!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    <span>Копировать полный URL</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Progress Block */}
          <div className="bg-pm-bg-card rounded-xl border border-pm-border p-6">
            <h3 className="text-sm font-medium text-pm-text-muted mb-4">Ваш прогресс</h3>
            <div className="text-center mb-4">
              <div className="text-4xl font-bold text-pm-orange mb-1">
                {mission.foundBugs}/{mission.bugs}
              </div>
              <div className="text-sm text-pm-text-muted">багов найдено</div>
            </div>
            <div className="h-3 bg-pm-bg rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-pm-orange to-pm-orange-hover rounded-full transition-all"
                style={{ width: `${(mission.foundBugs / mission.bugs) * 100}%` }}
              />
            </div>
          </div>

          {/* Lab Status */}
          {labStarted && (
            <div className="bg-pm-green/10 border border-pm-green/30 rounded-xl p-6 animate-fade-in">
              <div className="flex items-center gap-2 text-pm-green mb-3">
                <CheckCircle className="w-5 h-5" />
                <span className="font-semibold">Лаба активна</span>
              </div>
              <p className="text-sm text-pm-text-muted mb-4">
                Используйте endpoint выше для отправки запросов. Найденные флаги зарегистрируйте на странице "Flags".
              </p>
              <div className="flex items-center gap-2 text-sm text-pm-text-dim">
                <Clock className="w-4 h-4" />
                <span>Истекает через 2:00:00</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Main Lab Page Component
export default function Lab() {
  const [searchParams, setSearchParams] = useSearchParams();
  
  const [view, setView] = useState('domains');
  const [selectedDomain, setSelectedDomain] = useState(null);
  const [selectedMission, setSelectedMission] = useState(null);

  // Initialize from URL params
  useEffect(() => {
    const domainParam = searchParams.get('domain');
    const missionParam = searchParams.get('mission');
    
    if (missionParam) {
      for (const [domainId, tiers] of Object.entries(missionsByDomain)) {
        for (const [tier, missions] of Object.entries(tiers)) {
          const mission = missions.find(m => m.id === missionParam);
          if (mission) {
            setSelectedDomain(domains.find(d => d.id === domainId));
            setSelectedMission(mission);
            setView('detail');
            return;
          }
        }
      }
    } else if (domainParam) {
      const domain = domains.find(d => d.id === domainParam);
      if (domain) {
        setSelectedDomain(domain);
        setView('missions');
      }
    }
  }, [searchParams]);

  const handleSelectDomain = (domain) => {
    setSelectedDomain(domain);
    setView('missions');
    setSearchParams({ domain: domain.id });
  };

  const handleSelectMission = (mission) => {
    setSelectedMission(mission);
    setView('detail');
    setSearchParams({ domain: selectedDomain.id, mission: mission.id });
  };

  const handleBackToDomains = () => {
    setSelectedDomain(null);
    setView('domains');
    setSearchParams({});
  };

  const handleBackToMissions = () => {
    setSelectedMission(null);
    setView('missions');
    setSearchParams({ domain: selectedDomain.id });
  };

  return (
    <div className="p-6">
      {/* Domains View */}
      {view === 'domains' && (
        <div className="animate-fade-in">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-pm-text mb-2">API Testing Labs</h1>
            <p className="text-pm-text-muted">
              Выберите домен для начала практики. Каждый домен содержит миссии разного уровня сложности.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {domains.map((domain) => (
              <DomainCard 
                key={domain.id} 
                domain={domain} 
                onClick={() => handleSelectDomain(domain)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Missions List View */}
      {view === 'missions' && selectedDomain && (
        <div className="animate-fade-in">
          <button
            onClick={handleBackToDomains}
            className="flex items-center gap-2 text-pm-text-muted hover:text-pm-text mb-6 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Назад к доменам</span>
          </button>

          <div className="flex items-center gap-4 mb-8">
            <div className={clsx(
              'w-16 h-16 rounded-xl flex items-center justify-center text-4xl',
              selectedDomain.bgColor
            )}>
              {selectedDomain.icon}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-pm-text">{selectedDomain.name}</h1>
              <p className="text-pm-text-muted">{selectedDomain.description}</p>
            </div>
          </div>

          {/* Tier Sections */}
          {['T1', 'T2', 'T3'].map((tier) => {
            const missions = missionsByDomain[selectedDomain.id]?.[tier] || [];
            if (missions.length === 0) return null;
            
            return (
              <TierSection
                key={tier}
                tier={tier}
                missions={missions}
                domainId={selectedDomain.id}
                onSelectMission={handleSelectMission}
              />
            );
          })}
        </div>
      )}

      {/* Mission Detail View */}
      {view === 'detail' && selectedMission && selectedDomain && (
        <MissionDetail
          mission={selectedMission}
          domain={selectedDomain}
          onBack={handleBackToMissions}
        />
      )}
    </div>
  );
}
