import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  BookOpen,
  Lock,
  ChevronDown,
  ChevronRight,
  CheckCircle,
  Target,
  Loader2,
  ArrowRight,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import clsx from 'clsx';
import { api } from '../services/api';
import { THEORY_CONTENT } from '../data/theory';

const TIER_ORDER = ['T1', 'T2', 'T3', 'T4', 'T5'];

const tierNames = {
  T1: { name: 'Основы тестирования REST API', level: 'Beginner' },
  T2: { name: 'Граничные значения и валидация', level: 'Intermediate' },
  T3: { name: 'Многошаговые сценарии и бизнес-логика', level: 'Advanced' },
  T4: { name: 'Безопасность и авторизация', level: 'Expert' },
  T5: { name: 'Продвинутые техники тестирования', level: 'Expert' },
};

const tierColors = {
  T1: { bg: 'bg-pm-green/10', border: 'border-pm-green/30', text: 'text-pm-green', badge: 'bg-pm-green/20 text-pm-green' },
  T2: { bg: 'bg-pm-blue/10', border: 'border-pm-blue/30', text: 'text-pm-blue', badge: 'bg-pm-blue/20 text-pm-blue' },
  T3: { bg: 'bg-pm-purple/10', border: 'border-pm-purple/30', text: 'text-pm-purple', badge: 'bg-pm-purple/20 text-pm-purple' },
  T4: { bg: 'bg-pm-orange/10', border: 'border-pm-orange/30', text: 'text-pm-orange', badge: 'bg-pm-orange/20 text-pm-orange' },
  T5: { bg: 'bg-pm-orange/10', border: 'border-pm-orange/30', text: 'text-pm-orange', badge: 'bg-pm-orange/20 text-pm-orange' },
};

function LockedSection({ tier, accessInfo, prevTier }) {
  const colors = tierColors[tier];
  const progress = accessInfo.progress ?? 0;
  const requiredProgress = accessInfo.requiredProgress ?? 80;
  const foundBugs = accessInfo.foundBugs ?? 0;
  const totalBugs = accessInfo.totalBugs ?? 0;
  const neededBugs = Math.ceil((totalBugs * requiredProgress) * 0.01) - foundBugs;

  return (
    <div className={clsx('rounded-xl border p-6 opacity-75', colors.bg, colors.border)}>
      <div className="flex items-start gap-4">
        <div className={clsx('w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0', colors.bg)}>
          <Lock className={clsx('w-6 h-6', colors.text)} />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <span className={clsx('px-3 py-1 rounded-lg text-sm font-bold', colors.badge)}>{tier}</span>
            <span className="text-sm text-pm-text-muted">{tierNames[tier].level}</span>
          </div>
          <h2 className="text-xl font-bold text-pm-text mb-2">{tierNames[tier].name}</h2>
          <div className="bg-pm-bg-card rounded-lg border border-pm-border p-4 mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-pm-text-muted">Прогресс в {prevTier}</span>
              <span className="text-sm font-medium text-pm-text">{`${progress}% / ${requiredProgress}%`}</span>
            </div>
            <div className="h-2 bg-pm-bg rounded-full overflow-hidden mb-2">
              <div
                className="h-full bg-gradient-to-r from-pm-orange to-pm-orange-hover rounded-full transition-all"
                style={{ width: `${Math.min(progress, 100)}%` }}
              />
            </div>
            <div className="flex items-center justify-between text-xs text-pm-text-muted">
              <span>Найдено: {`${foundBugs} / ${totalBugs}`} багов</span>
              {neededBugs > 0 && (
                <span className="text-pm-orange">Осталось: {neededBugs} багов</span>
              )}
            </div>
          </div>
          <p className="text-sm text-pm-text-muted mb-4">
            Для доступа к этому разделу теории необходимо найти {requiredProgress}% багов в разделе {prevTier} хотя бы в одном домене.
          </p>
          <Link
            to="/lab"
            className="inline-flex items-center gap-2 px-4 py-2 bg-pm-orange hover:bg-pm-orange-hover text-white rounded-lg text-sm font-medium transition-colors"
          >
            Перейти к миссиям {prevTier}
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}

function UnlockedSection({ tier, content, isExpanded, onToggle }) {
  const colors = tierColors[tier];

  const isValidLang = (str) => {
    if (!str || str.length === 0) return false;
    for (let i = 0; i < str.length; i++) {
      const c = str[i];
      const letter = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z');
      const digit = c >= '0' && c <= '9';
      const under = c === '_';
      if (!letter && !digit && !under) return false;
    }
    return true;
  };

  const markdownComponents = {
    code({ node, inline, className, children, ...props }) {
      let lang = null;
      if (className && String(className).startsWith('language-')) {
        const prefix = 'language-';
        const raw = String(className).slice(prefix.length);
        if (isValidLang(raw)) lang = raw;
      }
      if (!inline && lang) {
        return (
          <SyntaxHighlighter
            style={vscDarkPlus}
            language={lang}
            PreTag="div"
            className="rounded-lg !bg-pm-bg !my-4"
            {...props}
          >
            {String(children).trimEnd()}
          </SyntaxHighlighter>
        );
      }
      return (
        <code className="px-1.5 py-0.5 bg-pm-bg rounded text-sm font-mono text-pm-orange" {...props}>
          {children}
        </code>
      );
    },
    table({ children }) {
      return (
        <div className="my-6 overflow-x-auto">
          <table className="min-w-full border border-pm-border rounded-lg overflow-hidden bg-pm-bg-card">{children}</table>
        </div>
      );
    },
    thead({ children }) {
      return <thead className="bg-pm-bg-hover border-b-2 border-pm-border">{children}</thead>;
    },
    tbody({ children }) {
      return <tbody className="divide-y divide-pm-border bg-pm-bg-card">{children}</tbody>;
    },
    tr({ children }) {
      return <tr className="border-b border-pm-border/50">{children}</tr>;
    },
    th({ children }) {
      return (
        <th className="px-6 py-4 text-left text-sm font-semibold text-pm-text uppercase tracking-wide">
          {children}
        </th>
      );
    },
    td({ children }) {
      return (
        <td className="px-6 py-4 text-sm text-pm-text-muted align-top">
          <div className="break-words">{children}</div>
        </td>
      );
    },
    h1({ children }) {
      return <h1 className="text-3xl font-bold text-pm-text mt-8 mb-4">{children}</h1>;
    },
    h2({ children }) {
      return <h2 className="text-2xl font-bold text-pm-text mt-6 mb-3">{children}</h2>;
    },
    h3({ children }) {
      return <h3 className="text-xl font-semibold text-pm-text mt-4 mb-2">{children}</h3>;
    },
    p({ children }) {
      return <p className="text-pm-text-muted leading-relaxed mb-4">{children}</p>;
    },
    ul({ children }) {
      return <ul className="list-disc list-inside text-pm-text-muted mb-4 space-y-2">{children}</ul>;
    },
    ol({ children }) {
      return <ol className="list-decimal list-inside text-pm-text-muted mb-4 space-y-2">{children}</ol>;
    },
    li({ children }) {
      return <li className="text-pm-text-muted">{children}</li>;
    },
    blockquote({ children }) {
      return (
        <blockquote className="border-l-4 border-pm-orange pl-4 italic text-pm-text-muted my-4">
          {children}
        </blockquote>
      );
    },
    a({ href, children }) {
      return (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="text-pm-orange hover:text-pm-orange-hover underline"
        >
          {children}
        </a>
      );
    },
    hr() {
      return <hr className="border-pm-border my-6" />;
    },
  };

  if (!content) {
    return (
      <div className={clsx('rounded-xl border overflow-hidden', colors.border)}>
        <button
          type="button"
          onClick={onToggle}
          className={clsx(
            'w-full p-6 text-left transition-colors hover:bg-pm-bg-hover/50',
            colors.bg,
            colors.border
          )}
        >
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className={clsx('w-12 h-12 rounded-xl flex items-center justify-center', colors.bg)}>
                <BookOpen className={clsx('w-6 h-6', colors.text)} />
              </div>
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <span className={clsx('px-3 py-1 rounded-lg text-sm font-bold', colors.badge)}>{tier}</span>
                  <span className="text-sm text-pm-text-muted">{tierNames[tier].level}</span>
                </div>
                <h2 className="text-xl font-bold text-pm-text">{tierNames[tier].name}</h2>
              </div>
            </div>
            <ChevronDown
              className={clsx('w-5 h-5 text-pm-text-muted transition-transform shrink-0', isExpanded && 'rotate-180')}
            />
          </div>
        </button>
        {isExpanded && (
          <div className="p-6 border-t border-pm-border bg-pm-bg-card">
            <p className="text-pm-text-muted">Теоретический материал для этого раздела будет добавлен позже.</p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={clsx('rounded-xl border overflow-hidden', colors.border)}>
      <button
        type="button"
        onClick={onToggle}
        className={clsx(
          'w-full p-6 text-left transition-colors hover:bg-pm-bg-hover/50 border-b border-pm-border',
          colors.bg,
          colors.border
        )}
      >
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className={clsx('w-12 h-12 rounded-xl flex items-center justify-center', colors.bg)}>
              <BookOpen className={clsx('w-6 h-6', colors.text)} />
            </div>
            <div>
              <div className="flex items-center gap-3 mb-1">
                <span className={clsx('px-3 py-1 rounded-lg text-sm font-bold', colors.badge)}>{tier}</span>
                <span className="text-sm text-pm-text-muted">{tierNames[tier].level}</span>
                <span className="flex items-center gap-1 text-sm text-pm-green">
                  <CheckCircle className="w-4 h-4" />
                  Доступно
                </span>
              </div>
              <h2 className="text-xl font-bold text-pm-text">{tierNames[tier].name}</h2>
            </div>
          </div>
          <ChevronDown
            className={clsx('w-5 h-5 text-pm-text-muted transition-transform shrink-0', isExpanded && 'rotate-180')}
          />
        </div>
      </button>
      {isExpanded && (
        <div className="p-6 bg-pm-bg-card">
          <div className="prose prose-invert max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
              {content}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Theory() {
  const [accessInfo, setAccessInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expandedTiers, setExpandedTiers] = useState({
    T1: true,
    T2: false,
    T3: false,
    T4: false,
    T5: false,
  });

  const toggleTier = (tier) => {
    setExpandedTiers((prev) => ({ ...prev, [tier]: !prev[tier] }));
  };

  useEffect(() => {
    let cancelled = false;
    async function loadAccess() {
      try {
        const access = await api.getTheoryAccess();
        if (!cancelled) setAccessInfo(access);
      } catch (error) {
        console.error('Error loading theory access:', error);
        if (!cancelled) {
          setAccessInfo({
            T1: { unlocked: true, progress: 100, totalBugs: 0, foundBugs: 0, requiredProgress: 80 },
            T2: { unlocked: false, progress: 0, totalBugs: 0, foundBugs: 0, requiredProgress: 80 },
            T3: { unlocked: false, progress: 0, totalBugs: 0, foundBugs: 0, requiredProgress: 80 },
            T4: { unlocked: false, progress: 0, totalBugs: 0, foundBugs: 0, requiredProgress: 80 },
            T5: { unlocked: false, progress: 0, totalBugs: 0, foundBugs: 0, requiredProgress: 80 },
          });
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadAccess();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-pm-orange animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 animate-fade-in">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-3 rounded-xl bg-pm-blue/20">
            <BookOpen className="w-8 h-8 text-pm-blue" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-pm-text">Теория</h1>
            <p className="text-pm-text-muted mt-1">
              Изучайте теоретические материалы по мере прохождения миссий
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        {TIER_ORDER.map((tier) => {
          const access = accessInfo?.[tier];
          const content = THEORY_CONTENT[tier];
          const prevTier = tier === 'T1' ? null : `T${parseInt(tier[1], 10) - 1}`;
          const isExpanded = expandedTiers[tier] ?? false;

          if (!access) return null;

          if (access.unlocked) {
            return (
              <UnlockedSection
                key={tier}
                tier={tier}
                content={content}
                isExpanded={isExpanded}
                onToggle={() => toggleTier(tier)}
              />
            );
          }
          if (prevTier) {
            return (
              <LockedSection
                key={tier}
                tier={tier}
                accessInfo={access}
                prevTier={prevTier}
              />
            );
          }
          return null;
        })}
      </div>

      <div className="mt-12 p-6 bg-pm-bg-card rounded-xl border border-pm-border">
        <div className="flex items-start gap-4">
          <Target className="w-6 h-6 text-pm-orange flex-shrink-0 mt-1" />
          <div>
            <h3 className="font-semibold text-pm-text mb-2">Как открыть новые разделы?</h3>
            <p className="text-sm text-pm-text-muted leading-relaxed">
              Для доступа к теории следующего уровня необходимо найти {accessInfo?.T2?.requiredProgress ?? 80}% багов в
              предыдущем тире хотя бы в одном домене. Например, чтобы открыть теорию T2, нужно найти {accessInfo?.T2?.requiredProgress ?? 80}%
              багов в миссиях T1 в любом из доменов. Прогресс отображается в каждом заблокированном разделе.
            </p>
            <Link
              to="/lab"
              className="inline-flex items-center gap-2 mt-4 text-pm-orange hover:text-pm-orange-hover font-medium text-sm"
            >
              Перейти к миссиям
              <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
