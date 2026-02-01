import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Flag, 
  CheckCircle, 
  XCircle,
  Clock, 
  Trophy, 
  Search,
  Bug,
  Copy,
  AlertCircle,
  Loader2,
  ArrowRight,
  Sparkles
} from 'lucide-react';
import clsx from 'clsx';
import { api, isDemoMode } from '../services/api';
import { mockFoundFlags, mockUserStats, domains, verifyFlag } from '../mocks/data';

// ============= VERIFICATION RESULT =============
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
                  {result.mission && <span> • {result.mission}</span>}
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

// ============= FLAG CARD =============
function FlagCard({ flag }) {
  const [copied, setCopied] = useState(false);
  const domain = domains.find(d => d.id === flag.domain);

  const copyFlag = () => {
    navigator.clipboard.writeText(flag.flag);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (days > 0) return `${days} дн. назад`;
    if (hours > 0) return `${hours} ч. назад`;
    return 'недавно';
  };

  return (
    <div className="bg-pm-bg-card rounded-xl border border-pm-green/30 overflow-hidden hover:border-pm-green/50 transition-all">
      <div className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-pm-green/20 flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-pm-green" />
            </div>
            <div>
              <h3 className="font-semibold text-pm-green">{flag.bugTitle}</h3>
              <p className="text-sm text-pm-text-muted">{flag.missionTitle}</p>
            </div>
          </div>
          <span className="text-pm-yellow font-medium">+{flag.points}</span>
        </div>

        {/* Flag Value */}
        <div className="flex items-center gap-2 p-3 bg-pm-bg rounded-lg mb-3">
          <code className="flex-1 font-mono text-sm text-pm-green truncate">
            {flag.flag}
          </code>
          <button
            onClick={copyFlag}
            className="p-1.5 text-pm-text-muted hover:text-pm-text rounded transition-colors flex-shrink-0"
          >
            {copied ? (
              <CheckCircle className="w-4 h-4 text-pm-green" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-3 text-pm-text-muted">
            <span className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              {formatDate(flag.foundAt)}
            </span>
            {domain && (
              <span className="flex items-center gap-1">
                {domain.icon} {domain.name}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Map API flag to display shape (missionTitle from missionId if needed)
function mapFlag(f) {
  return {
    id: f.id,
    missionId: f.missionId,
    missionTitle: f.missionId,
    domain: f.missionId?.split('-')[0] ?? 'ecommerce',
    bugTitle: f.bugTitle,
    flag: f.flag,
    points: f.points,
    foundAt: f.foundAt,
  };
}

// ============= MAIN FLAGS PAGE =============
export default function Flags() {
  const [flagInput, setFlagInput] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);
  const [userFlags, setUserFlags] = useState(mockFoundFlags);
  const [stats, setStats] = useState(mockUserStats);
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(!isDemoMode);

  // Load flags and stats from API when not in demo mode
  const loadFromApi = async () => {
    const [flagsRes, statsRes] = await Promise.all([api.getUserFlags(), api.getUserStats()]);
    if (Array.isArray(flagsRes)) setUserFlags(flagsRes.map(mapFlag));
    if (statsRes) {
      setStats({
        totalPoints: statsRes.totalPoints ?? 0,
        rank: statsRes.rank ?? 'Newbie',
        completedMissions: statsRes.completedMissions ?? 0,
        foundBugs: statsRes.foundBugs ?? 0,
        totalBugs: statsRes.totalBugs ?? 0,
        foundFlags: statsRes.foundBugs ?? 0,
        totalFlags: statsRes.totalBugs ?? 0,
      });
    }
    setLoading(false);
  };

  useEffect(() => {
    if (isDemoMode) {
      setLoading(false);
      return;
    }
    loadFromApi();
  }, []);

  // Handle flag verification
  const handleVerifyFlag = async () => {
    if (!flagInput.trim() || verifying) return;

    setVerifying(true);
    setVerificationResult(null);

    if (isDemoMode) {
      await new Promise((r) => setTimeout(r, 800));
      const result = verifyFlag(flagInput.trim());
      setVerificationResult(result);
      if (result.valid && result.isNew) {
        const newFlag = {
          id: `flag-${Date.now()}`,
          missionId: 'demo',
          missionTitle: result.mission || 'Demo Mission',
          domain: 'fintech',
          bugId: 'demo',
          bugTitle: result.bug || 'Demo Bug',
          flag: flagInput.trim(),
          points: result.points,
          foundAt: new Date().toISOString(),
          verified: true,
        };
        setUserFlags((prev) => [newFlag, ...prev]);
        setStats((prev) => ({
          ...prev,
          totalPoints: prev.totalPoints + result.points,
          foundFlags: (prev.foundFlags ?? prev.foundBugs ?? 0) + 1,
        }));
        setFlagInput('');
      }
      setVerifying(false);
      return;
    }

    const result = await api.verifyFlag(flagInput.trim());
    setVerificationResult(result);
    if (result.valid && result.isNew) {
      setFlagInput('');
      await loadFromApi();
    }
    setVerifying(false);
  };

  // Filter flags
  const filteredFlags = userFlags.filter(flag => {
    if (search) {
      const searchLower = search.toLowerCase();
      if (!flag.bugTitle.toLowerCase().includes(searchLower) && 
          !flag.flag.toLowerCase().includes(searchLower) &&
          !flag.missionTitle.toLowerCase().includes(searchLower)) {
        return false;
      }
    }
    if (filter !== 'all' && flag.domain !== filter) {
      return false;
    }
    return true;
  });

  // Calculate total points from flags
  const totalPoints = userFlags.reduce((sum, f) => sum + f.points, 0);

  return (
    <div className="p-6 animate-fade-in">
      {/* ===== FLAG VERIFICATION FORM ===== */}
      <div className="bg-pm-bg-card rounded-xl border border-pm-border p-6 mb-8">
        <div className="flex items-center gap-4 mb-6">
          <div className="p-3 rounded-xl bg-pm-orange/20">
            <Flag className="w-6 h-6 text-pm-orange" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-pm-text">Регистрация флага</h2>
            <p className="text-sm text-pm-text-muted">
              Нашли флаг в API? Вставьте его сюда для проверки и получения баллов
            </p>
          </div>
        </div>
        
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <input
              type="text"
              value={flagInput}
              onChange={(e) => setFlagInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleVerifyFlag()}
              placeholder="QA_FLAG{your_flag_here}"
              className="w-full px-4 py-3.5 bg-pm-bg border border-pm-border rounded-xl font-mono text-pm-text placeholder:text-pm-text-dim focus:border-pm-orange focus:ring-2 focus:ring-pm-orange/20 transition-all"
              disabled={verifying}
            />
            {flagInput && !verifying && (
              <button
                onClick={() => setFlagInput('')}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-pm-text-muted hover:text-pm-text transition-colors"
              >
                ✕
              </button>
            )}
          </div>
          <button
            onClick={handleVerifyFlag}
            disabled={!flagInput.trim() || verifying}
            className="flex items-center gap-2 px-8 py-3.5 bg-pm-orange hover:bg-pm-orange-hover disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl font-medium transition-all"
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

        {/* Verification Result */}
        <VerificationResult 
          result={verificationResult} 
          onDismiss={() => setVerificationResult(null)} 
        />

        {/* Format Hint */}
        {!verificationResult && (
          <div className="flex items-center gap-2 mt-4 text-sm text-pm-text-muted">
            <AlertCircle className="w-4 h-4" />
            <span>Формат флага: <code className="px-1.5 py-0.5 bg-pm-bg rounded">QA_FLAG{'{...}'}</code></span>
          </div>
        )}
      </div>

      {/* ===== STATS ===== */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-pm-bg-card rounded-xl border border-pm-border p-5">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-gradient-to-br from-pm-green to-emerald-600">
              <Flag className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-sm text-pm-text-muted">Флагов найдено</p>
              <p className="text-2xl font-bold text-pm-text">{userFlags.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-pm-bg-card rounded-xl border border-pm-border p-5">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-gradient-to-br from-pm-yellow to-amber-600">
              <Trophy className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-sm text-pm-text-muted">Заработано баллов</p>
              <p className="text-2xl font-bold text-pm-text">{totalPoints}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-pm-bg-card rounded-xl border border-pm-border p-5">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-gradient-to-br from-pm-purple to-purple-600">
              <Bug className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-sm text-pm-text-muted">Общий прогресс</p>
              <p className="text-2xl font-bold text-pm-text">
                {stats.foundFlags ?? stats.foundBugs ?? 0}/{stats.totalFlags ?? stats.totalBugs ?? 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ===== FILTERS ===== */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-pm-text">Найденные флаги</h2>
        
        <div className="flex items-center gap-3">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-pm-text-muted" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Поиск..."
              className="pl-10 pr-4 py-2 bg-pm-bg-card border border-pm-border rounded-lg text-pm-text placeholder:text-pm-text-dim w-48 focus:border-pm-orange transition-colors"
            />
          </div>
          
          {/* Domain Filter */}
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-4 py-2 bg-pm-bg-card border border-pm-border rounded-lg text-pm-text cursor-pointer"
          >
            <option value="all">Все темы</option>
            {domains.map(d => (
              <option key={d.id} value={d.id}>{d.icon} {d.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* ===== FLAGS LIST ===== */}
      {filteredFlags.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredFlags.map((flag) => (
            <FlagCard key={flag.id} flag={flag} />
          ))}
        </div>
      ) : (
        <div className="text-center py-16 bg-pm-bg-card rounded-xl border border-pm-border">
          <Flag className="w-16 h-16 text-pm-text-dim mx-auto mb-4" />
          <h3 className="text-lg font-medium text-pm-text mb-2">
            {search || filter !== 'all' 
              ? 'Флаги не найдены'
              : 'У вас пока нет флагов'}
          </h3>
          <p className="text-pm-text-muted mb-6">
            {search || filter !== 'all'
              ? 'Попробуйте изменить параметры поиска'
              : 'Перейдите в лаборатории и начните искать баги!'}
          </p>
          {!search && filter === 'all' && (
            <Link
              to="/lab"
              className="inline-flex items-center gap-2 px-6 py-3 bg-pm-orange hover:bg-pm-orange-hover text-white rounded-lg font-medium transition-colors"
            >
              Перейти к лабораториям
              <ArrowRight className="w-4 h-4" />
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
