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
  Target,
  FileText,
  ChevronDown,
  Loader2,
  XCircle,
  Sparkles,
  AlertCircle,
  Flag
} from 'lucide-react';
import clsx from 'clsx';
import { api, isDemoMode } from '../services/api';
import { domains, missionsByDomain, getTierProgress, isTierUnlocked, mockFoundFlags, verifyFlag as mockVerifyFlag } from '../mocks/data';

// Verification Result Component (for flag submission feedback)
function VerificationResult({ result, onDismiss }) {
  if (!result) return null;

  return (
    <div className={clsx(
      'mt-4 p-5 rounded-xl border animate-slide-up',
      result.valid 
        ? 'bg-pm-green/10 border-pm-green/30' 
        : 'bg-pm-red/10 border-pm-red/30'
    )}>
      <div className="flex items-start gap-4">
        <div className={clsx(
          'w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0',
          result.valid ? 'bg-pm-green/20' : 'bg-pm-red/20'
        )}>
          {result.valid ? (
            <Sparkles className="w-6 h-6 text-pm-green" />
          ) : (
            <XCircle className="w-6 h-6 text-pm-red" />
          )}
        </div>
        
        <div className="flex-1">
          <h3 className={clsx(
            'text-lg font-bold mb-1',
            result.valid ? 'text-pm-green' : 'text-pm-red'
          )}>
            {result.valid ? 'Флаг принят!' : 'Флаг отклонён'}
          </h3>
          <p className="text-pm-text-muted">{result.message}</p>
          
          {result.valid && result.points > 0 && (
            <div className="mt-4 flex items-center gap-4">
              <div className="flex items-center gap-2 px-4 py-2 bg-pm-yellow/20 rounded-lg">
                <Trophy className="w-5 h-5 text-pm-yellow" />
                <span className="text-lg font-bold text-pm-yellow">+{result.points} баллов</span>
              </div>
              {result.bug && (
                <div className="text-pm-text-muted">
                  <span className="text-pm-text">{result.bug}</span>
                  {result.missionId && <span> • {result.missionId}</span>}
                </div>
              )}
            </div>
          )}
        </div>
        
        <button
          onClick={onDismiss}
          className="text-pm-text-muted hover:text-pm-text transition-colors p-1"
        >
          ✕
        </button>
      </div>
    </div>
  );
}

// Requirements Section Component (T3 only)
function RequirementsSection({ requirements }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="bg-pm-bg-card rounded-xl border border-pm-border p-6">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between gap-3 mb-3 hover:opacity-80 transition-opacity"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-pm-blue/20">
            <FileText className="w-5 h-5 text-pm-blue" />
          </div>
          <h2 className="text-lg font-semibold text-pm-text">Требования</h2>
        </div>
        <ChevronDown
          className={clsx(
            "w-5 h-5 text-pm-text-muted transition-transform",
            isOpen && "transform rotate-180"
          )}
        />
      </button>
      {isOpen && (
        <div className="text-pm-text-muted leading-relaxed whitespace-pre-line text-sm mt-3">
          {requirements}
        </div>
      )}
    </div>
  );
}

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

// Tier Section Component (collapsible; missionsByDomainOverride: use when data from API)
function TierSection({ tier, missions, domainId, onSelectMission, missionsByDomainOverride, isExpanded, onToggle }) {
  const isUnlocked = isTierUnlocked(domainId, tier, missionsByDomainOverride);
  const progress = getTierProgress(domainId, tier, missionsByDomainOverride);

  const tierColors = {
    T1: { bg: 'bg-pm-green/10', border: 'border-pm-green/30', text: 'text-pm-green' },
    T2: { bg: 'bg-pm-blue/10', border: 'border-pm-blue/30', text: 'text-pm-blue' },
    T3: { bg: 'bg-pm-purple/10', border: 'border-pm-purple/30', text: 'text-pm-purple' },
    T4: { bg: 'bg-pm-orange/10', border: 'border-pm-orange/30', text: 'text-pm-orange' },
    T5: { bg: 'bg-pm-orange/10', border: 'border-pm-orange/30', text: 'text-pm-orange' },
  };

  const colors = tierColors[tier] || tierColors.T1;

  if (!missions || missions.length === 0) return null;

  return (
    <div className="mb-4 rounded-xl border border-pm-border bg-pm-bg-card overflow-hidden">
      <button
        type="button"
        onClick={onToggle}
        className={clsx(
          'w-full flex items-center justify-between gap-3 px-4 py-3 text-left transition-colors',
          'hover:bg-pm-bg-hover/50'
        )}
      >
        <div className="flex items-center gap-3">
          <ChevronDown
            className={clsx(
              'w-5 h-5 text-pm-text-muted transition-transform shrink-0',
              isExpanded && 'rotate-180'
            )}
          />
          <span className={clsx(
            'px-3 py-1.5 rounded-lg text-sm font-bold border',
            colors.bg, colors.border, colors.text
          )}>
            {tier}
          </span>
          <span className="text-pm-text-muted text-sm">
            {tier === 'T1' && 'Beginner'}
            {tier === 'T2' && 'Intermediate'}
            {tier === 'T3' && 'Advanced'}
            {(tier === 'T4' || tier === 'T5') && 'Expert'}
          </span>
          {!isUnlocked && (
            <span className="flex items-center gap-1 text-sm text-pm-text-dim">
              <Lock className="w-4 h-4" />
              Требуется 80% в T{parseInt(tier.slice(1)) - 1}
            </span>
          )}
        </div>
        <div className="text-sm text-pm-text-muted">
          {progress.foundBugs || 0}/{progress.totalBugs || 0} багов · {missions.length} миссий
        </div>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 pt-0 border-t border-pm-border">
          <div className="grid grid-cols-1 gap-4 pt-4">
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
      )}
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
function MissionDetail({ mission, domain, onBack, onFlagVerified }) {
  const [labStarted, setLabStarted] = useState(false);
  const [labSession, setLabSession] = useState(null);
  const [copied, setCopied] = useState(false);
  const [flagInput, setFlagInput] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);
  const [missionFlags, setMissionFlags] = useState([]);

  const baseUrl = labSession?.baseUrl ?? (labStarted ? mission.baseUrl : null);
  const fullEndpoint = baseUrl ? `${baseUrl}${mission.endpoint}` : '';

  useEffect(() => {
    if (isDemoMode) {
      const flags = mockFoundFlags.filter((f) => f.missionId === mission.id);
      setMissionFlags(flags);
      return;
    }
    let cancelled = false;
    api.getUserFlags().then((flags) => {
      if (cancelled) return;
      const arr = Array.isArray(flags) ? flags : (flags?.flags ?? []);
      setMissionFlags(arr.filter((f) => f.missionId === mission.id));
    });
    return () => { cancelled = true; };
  }, [mission.id]);

  const copyEndpoint = () => {
    navigator.clipboard.writeText(fullEndpoint);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleStartLab = async () => {
    if (isDemoMode) {
      setLabStarted(true);
      return;
    }
    const res = await api.startLab(mission.id);
    if (res.ok && res.data) {
      setLabSession(res.data);
      setLabStarted(true);
    } else {
      setLabStarted(true);
    }
  };

  const handleVerifyFlag = async () => {
    if (!flagInput.trim() || verifying) return;

    setVerifying(true);
    setVerificationResult(null);

    if (isDemoMode) {
      const result = await mockVerifyFlag(flagInput.trim());
      setVerificationResult({
        ...result,
        bug: result.bugTitle ?? result.bug,
        missionId: result.missionId ?? mission.id,
      });
      if (result.valid && result.newFlag) {
        setMissionFlags((prev) => [
          {
            id: `flag-${Date.now()}`,
            missionId: mission.id,
            missionTitle: mission.title,
            bugTitle: result.bugTitle || 'Demo Bug',
            flag: flagInput.trim(),
            points: result.points,
            foundAt: new Date().toISOString(),
          },
          ...prev,
        ]);
        setFlagInput('');
        onFlagVerified?.();
      }
      setVerifying(false);
      return;
    }

    const result = await api.verifyFlag(flagInput.trim());
    setVerificationResult(result);
    if (result.valid && result.isNew) {
      setFlagInput('');
      const flags = await api.getUserFlags();
      const arr = Array.isArray(flags) ? flags : (flags?.flags ?? []);
      setMissionFlags(arr.filter((f) => f.missionId === mission.id));
      onFlagVerified?.();
    }
    setVerifying(false);
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
        {/* Left Column - Task, Theory & Hints */}
        <div className="lg:col-span-2 space-y-6">
          {/* Только информация для студента: задача и подсказки */}
          {(mission.taskDescription || mission.description) && (
            <div className="bg-pm-orange/10 rounded-xl border border-pm-orange/30 p-6">
              <div className="flex items-center gap-3 mb-3">
                <Target className="w-5 h-5 text-pm-orange" />
                <h2 className="text-lg font-semibold text-pm-text">Задача для студента</h2>
              </div>
              <p className="text-pm-text-muted leading-relaxed whitespace-pre-line">
                {mission.taskDescription || mission.description}
              </p>
            </div>
          )}

          {/* Theory Block — из ECOMMERCE_THEORY_BLOCKS.md, соответствует миссии */}
          {(mission.theory?.title || mission.theory?.content) && (
            <div className="bg-pm-bg-card rounded-xl border border-pm-border p-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded-lg bg-pm-blue/20">
                  <BookOpen className="w-5 h-5 text-pm-blue" />
                </div>
                <h2 className="text-lg font-semibold text-pm-text">Теория</h2>
              </div>
              {mission.theory?.title && (
                <h3 className="text-base font-medium text-pm-text mb-2">{mission.theory.title}</h3>
              )}
              <div className="text-pm-text-muted leading-relaxed whitespace-pre-line text-sm">
                {mission.theory?.content}
              </div>
            </div>
          )}

          {/* Requirements Block - только для T3 миссий */}
          {mission.tier === 'T3' && mission.requirements && (
            <RequirementsSection requirements={mission.requirements} />
          )}

          {/* Hints Block */}
          <div className="bg-pm-bg-card rounded-xl border border-pm-border p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-pm-yellow/20">
                <Lightbulb className="w-5 h-5 text-pm-yellow" />
              </div>
              <h2 className="text-lg font-semibold text-pm-text">Подсказки</h2>
            </div>
            <div className="space-y-3">
              {(mission.hints || []).map((hint, index) => (
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
            
            <div className={clsx('space-y-3 relative', !labStarted && 'select-none')}>
              {!labStarted ? (
                <div className="p-6 bg-pm-bg rounded-lg text-center">
                  <p className="text-pm-text-muted">Запустите лабу, чтобы увидеть URL</p>
                </div>
              ) : (
                <>
                  <div>
                    <label className="text-xs text-pm-text-dim uppercase tracking-wide">Base URL</label>
                    <div className="mt-1 p-3 bg-pm-bg rounded-lg">
                      <code className="text-sm text-pm-green font-mono break-all">
                        {baseUrl}
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

                  {mission.requestBodyExample && (
                    <div>
                      <label className="text-xs text-pm-text-dim uppercase tracking-wide">Пример тела запроса</label>
                      <pre className="mt-1 p-3 bg-pm-bg rounded-lg text-sm text-pm-text-muted font-mono whitespace-pre-wrap break-words overflow-x-auto">
                        {mission.requestBodyExample}
                      </pre>
                    </div>
                  )}
                </>
              )}
              
              <div className="flex gap-2">
                <button
                  onClick={copyEndpoint}
                  disabled={!labStarted}
                  className={clsx(
                    'flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg transition-colors',
                    labStarted
                      ? 'bg-pm-bg-hover text-pm-text-muted hover:text-pm-text'
                      : 'bg-pm-bg-hover/50 text-pm-text-dim cursor-not-allowed'
                  )}
                >
                  {copied ? (
                    <>
                      <CheckCircle className="w-4 h-4 text-pm-green" />
                      <span className="text-pm-green">Скопировано!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4" />
                      <span>Копировать URL</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Flag verification form */}
          <div className="bg-pm-bg-card rounded-xl border border-pm-border p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-pm-orange/20">
                <Flag className="w-5 h-5 text-pm-orange" />
              </div>
              <h2 className="text-lg font-semibold text-pm-text">Ввод флага</h2>
            </div>
            <div className="flex gap-3">
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={flagInput}
                  onChange={(e) => setFlagInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleVerifyFlag()}
                  placeholder="QA_FLAG{your_flag_here}"
                  className="w-full px-4 py-3 bg-pm-bg border border-pm-border rounded-xl font-mono text-sm text-pm-text placeholder:text-pm-text-dim focus:border-pm-orange focus:ring-2 focus:ring-pm-orange/20 transition-all"
                  disabled={verifying}
                />
                {flagInput && !verifying && (
                  <button
                    onClick={() => setFlagInput('')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-pm-text-muted hover:text-pm-text transition-colors"
                  >
                    ✕
                  </button>
                )}
              </div>
              <button
                onClick={handleVerifyFlag}
                disabled={!flagInput.trim() || verifying}
                className="flex items-center gap-2 px-5 py-3 bg-pm-orange hover:bg-pm-orange-hover disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl font-medium transition-all"
              >
                {verifying ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Проверка...
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-5 h-5" />
                    Проверить
                  </>
                )}
              </button>
            </div>
            <VerificationResult
              result={verificationResult}
              onDismiss={() => setVerificationResult(null)}
            />
            <div className="flex items-center gap-2 mt-4 text-sm text-pm-text-muted">
              <AlertCircle className="w-4 h-4" />
              <span>Формат: <code className="px-1.5 py-0.5 bg-pm-bg rounded">QA_FLAG{'{...}'}</code></span>
            </div>
          </div>

          {/* Found flags for this mission */}
          {missionFlags.length > 0 && (
            <div className="bg-pm-bg-card rounded-xl border border-pm-border p-6">
              <h3 className="text-sm font-medium text-pm-text-muted mb-4">Найденные флаги</h3>
              <div className="space-y-3">
                {missionFlags.map((f) => (
                  <div
                    key={f.id}
                    className="flex items-center justify-between gap-2 p-3 bg-pm-bg rounded-lg border border-pm-border"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-pm-text truncate">{f.bugTitle}</p>
                      <code className="text-xs text-pm-text-muted font-mono truncate block">{f.flag}</code>
                    </div>
                    <span className="text-pm-yellow font-medium shrink-0">+{f.points}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Progress Block */}
          <div className="bg-pm-bg-card rounded-xl border border-pm-border p-6">
            <h3 className="text-sm font-medium text-pm-text-muted mb-4">Ваш прогресс</h3>
            <div className="text-center mb-4">
              <div className="text-4xl font-bold text-pm-orange mb-1">
                {Math.max(mission.foundBugs ?? 0, missionFlags.length)}/{mission.bugs}
              </div>
              <div className="text-sm text-pm-text-muted">багов найдено</div>
            </div>
            <div className="h-3 bg-pm-bg rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-pm-orange to-pm-orange-hover rounded-full transition-all"
                style={{ width: `${((mission.bugs || 1) > 0 ? (Math.max(mission.foundBugs ?? 0, missionFlags.length) / mission.bugs) * 100 : 0)}%` }}
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
              <p className="text-sm text-pm-text-muted">
                Используйте endpoint выше для отправки запросов. Найденные флаги вводите в поле ниже.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const TIER_ORDER = ['T1', 'T2', 'T3', 'T4', 'T5'];

// Main Lab Page Component
export default function Lab() {
  const [searchParams, setSearchParams] = useSearchParams();

  const [displayDomains, setDisplayDomains] = useState(isDemoMode ? domains : []);
  const [displayMissionsByDomain, setDisplayMissionsByDomain] = useState(isDemoMode ? missionsByDomain : {});
  const [view, setView] = useState('domains');
  const [selectedDomain, setSelectedDomain] = useState(null);
  const [selectedMission, setSelectedMission] = useState(null);
  const [loading, setLoading] = useState(!isDemoMode);
  const [expandedTiers, setExpandedTiers] = useState({ T1: true, T2: true, T3: true, T4: true, T5: true });

  const toggleTier = (tier) => {
    setExpandedTiers((prev) => ({ ...prev, [tier]: !prev[tier] }));
  };
  const expandAllTiers = () => setExpandedTiers({ T1: true, T2: true, T3: true, T4: true, T5: true });
  const collapseAllTiers = () => setExpandedTiers({ T1: false, T2: false, T3: false, T4: false, T5: false });

  // Load domains and missions from API when not in demo mode
  useEffect(() => {
    if (isDemoMode) return;
    let cancelled = false;
    console.log('Loading domains and missions from API...');
    api.loadDomainsAndMissions()
      .then((res) => {
        if (cancelled) return;
        console.log('API response received:', res);
        if (res?.domains) {
          console.log(`Setting ${res.domains.length} domains`);
          setDisplayDomains(res.domains);
          setDisplayMissionsByDomain(res.missionsByDomain || {});
        } else {
          console.warn('No domains received from API, res:', res);
        }
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        console.error('Error loading domains and missions:', err);
        setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  // Initialize from URL params (re-run when display data is loaded)
  useEffect(() => {
    const domainParam = searchParams.get('domain');
    const missionParam = searchParams.get('mission');

    if (missionParam) {
      for (const [domainId, tiers] of Object.entries(displayMissionsByDomain)) {
        for (const [tier, tierData] of Object.entries(tiers)) {
          // Поддержка нового формата (объект с полями missions, unlocked, progress) и старого (массив)
          let missions = [];
          if (tierData && typeof tierData === 'object' && 'missions' in tierData) {
            // Новый формат из API
            missions = Array.isArray(tierData.missions) ? tierData.missions : [];
          } else if (Array.isArray(tierData)) {
            // Старый формат (моки)
            missions = tierData;
          }
          
          const mission = missions.find((m) => m.id === missionParam);
          if (mission) {
            setSelectedDomain(displayDomains.find((d) => d.id === domainId));
            setSelectedMission(mission);
            setView('detail');
            return;
          }
        }
      }
    } else if (domainParam) {
      const domain = displayDomains.find((d) => d.id === domainParam);
      if (domain) {
        setSelectedDomain(domain);
        setView('missions');
      }
    }
  }, [searchParams, displayDomains, displayMissionsByDomain]);

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

  const handleFlagVerified = async () => {
    if (isDemoMode) return;
    const res = await api.loadDomainsAndMissions();
    if (res?.domains && selectedDomain && selectedMission) {
      setDisplayDomains(res.domains);
      setDisplayMissionsByDomain(res.missionsByDomain || {});
      for (const [domainId, tiers] of Object.entries(res.missionsByDomain || {})) {
        for (const [tier, tierData] of Object.entries(tiers)) {
          const missions = tierData?.missions || (Array.isArray(tierData) ? tierData : []);
          const mission = missions.find((m) => m.id === selectedMission.id);
          if (mission) {
            setSelectedMission(mission);
            return;
          }
        }
      }
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse flex space-y-4">
          <div className="h-8 bg-pm-bg-card rounded w-1/3" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-40 bg-pm-bg-card rounded-xl" />
            ))}
          </div>
        </div>
      </div>
    );
  }

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

          {displayDomains.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-pm-text-muted text-lg">Домены загружаются...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {displayDomains.map((domain) => (
                <DomainCard
                  key={domain.id}
                  domain={domain}
                  onClick={() => handleSelectDomain(domain)}
                />
              ))}
            </div>
          )}
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

          <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
            <div className="flex items-center gap-4">
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
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={expandAllTiers}
                className="px-3 py-1.5 text-sm rounded-lg bg-pm-bg-card border border-pm-border text-pm-text-muted hover:text-pm-text hover:border-pm-border/80 transition-colors"
              >
                Развернуть все
              </button>
              <button
                type="button"
                onClick={collapseAllTiers}
                className="px-3 py-1.5 text-sm rounded-lg bg-pm-bg-card border border-pm-border text-pm-text-muted hover:text-pm-text hover:border-pm-border/80 transition-colors"
              >
                Свернуть все
              </button>
            </div>
          </div>

          {/* Tier Sections (collapsible) */}
          {TIER_ORDER.map((tier) => {
            const tierData = displayMissionsByDomain[selectedDomain.id]?.[tier];
            // Поддержка нового формата (с полями unlocked, progress, missions) и старого (массив миссий)
            const missions = tierData?.missions || (Array.isArray(tierData) ? tierData : []);
            // Показываем тир даже если миссий нет, чтобы показать статус блокировки
            // Но не показываем пустые тиры, если нет данных вообще
            if (!tierData && missions.length === 0) return null;

            return (
              <TierSection
                key={tier}
                tier={tier}
                missions={missions}
                domainId={selectedDomain.id}
                onSelectMission={handleSelectMission}
                missionsByDomainOverride={displayMissionsByDomain}
                isExpanded={expandedTiers[tier] ?? true}
                onToggle={() => toggleTier(tier)}
              />
            );
          })}
          
          {/* Сообщение если нет миссий вообще */}
          {TIER_ORDER.every((tier) => {
            const tierData = displayMissionsByDomain[selectedDomain.id]?.[tier];
            const missions = tierData?.missions || (Array.isArray(tierData) ? tierData : []);
            return missions.length === 0;
          }) && (
            <div className="text-center py-12">
              <p className="text-pm-text-muted text-lg">
                Миссии для этого домена пока не добавлены.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Mission Detail View */}
      {view === 'detail' && selectedMission && selectedDomain && (
        <MissionDetail
          mission={selectedMission}
          domain={selectedDomain}
          onBack={handleBackToMissions}
          onFlagVerified={handleFlagVerified}
        />
      )}
    </div>
  );
}
