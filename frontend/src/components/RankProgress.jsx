import { TrendingUp } from 'lucide-react';

/**
 * Компонент для отображения прогресса ранга пользователя
 * @param {Object} props
 * @param {Object} props.rank - Текущий ранг { id, nameRu, nameEn, color }
 * @param {Object|null} props.nextRank - Следующий ранг { nameRu, minPoints } или null
 * @param {number} props.progress - Прогресс до следующего ранга (0-100)
 * @param {number} props.pointsToNext - Количество баллов до следующего ранга
 * @param {number} props.totalPoints - Общее количество баллов пользователя
 */
export default function RankProgress({ 
  rank, 
  nextRank, 
  progress, 
  pointsToNext,
  totalPoints 
}) {
  // Если ранг не передан, показываем заглушку
  if (!rank) {
    return (
      <div className="bg-pm-bg-card rounded-xl border border-pm-border p-5">
        <div className="text-pm-text-muted text-sm">Загрузка ранга...</div>
      </div>
    );
  }

  return (
    <div className="bg-pm-bg-card rounded-xl border border-pm-border p-5">
      {/* Текущий ранг */}
      <div className="flex items-center gap-3 mb-3">
        <div 
          className="w-10 h-10 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: rank.color + '20' }}
        >
          <TrendingUp className="w-5 h-5" style={{ color: rank.color }} />
        </div>
        <div>
          <p className="text-gray-400 text-sm">Текущий ранг</p>
          <p className="text-white font-semibold" style={{ color: rank.color }}>
            {rank.nameRu}
          </p>
        </div>
      </div>

      {/* Прогресс-бар */}
      {nextRank ? (
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-pm-text-muted">{totalPoints} баллов</span>
            <span className="text-pm-text-muted">{nextRank.minPoints}</span>
          </div>
          <div className="h-2 bg-pm-bg rounded-full overflow-hidden">
            <div 
              className="h-full rounded-full transition-all duration-500"
              style={{ 
                width: `${Math.min(progress, 100)}%`,
                backgroundColor: rank.color 
              }}
            />
          </div>
          <p className="text-pm-text-muted text-xs">
            До ранга "{nextRank.nameRu}": {pointsToNext} баллов
          </p>
        </div>
      ) : (
        /* Максимальный ранг */
        <div className="text-center">
          <p className="text-yellow-500 text-sm mt-2">
            🏆 Максимальный ранг достигнут!
          </p>
        </div>
      )}
    </div>
  );
}
