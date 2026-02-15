-- Миграция: создание таблицы ranks и заполнение данными
-- Выполняется только если таблица еще не существует

-- Создать таблицу ranks, если её еще нет
CREATE TABLE IF NOT EXISTS ranks (
    id VARCHAR(50) PRIMARY KEY,
    name_ru VARCHAR(100) NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    min_points INTEGER NOT NULL,
    color VARCHAR(7) NOT NULL,
    sort_order INTEGER NOT NULL
);

-- Заполнить данными 16 рангов (используем INSERT ... ON CONFLICT для идемпотентности)
INSERT INTO ranks (id, name_ru, name_en, min_points, color, sort_order) VALUES
    ('newbie', 'Новичок', 'Newbie', 0, '#9CA3AF', 1),
    ('trainee', 'Стажёр', 'Trainee', 30, '#6B7280', 2),
    ('seeker', 'Искатель', 'Seeker', 75, '#22C55E', 3),
    ('tracker', 'Следопыт', 'Tracker', 140, '#16A34A', 4),
    ('tester', 'Тестировщик', 'Tester', 230, '#3B82F6', 5),
    ('bug_hunter', 'Охотник за багами', 'Bug Hunter', 350, '#2563EB', 6),
    ('explorer', 'Исследователь', 'Explorer', 500, '#8B5CF6', 7),
    ('qa_engineer', 'QA-инженер', 'QA Engineer', 700, '#7C3AED', 8),
    ('detective', 'Детектив', 'Detective', 950, '#F59E0B', 9),
    ('specialist', 'Специалист', 'Specialist', 1250, '#D97706', 10),
    ('bug_slayer', 'Истребитель багов', 'Bug Slayer', 1650, '#EF4444', 11),
    ('expert', 'Эксперт', 'Expert', 2150, '#DC2626', 12),
    ('senior_tester', 'Старший тестировщик', 'Senior Tester', 2800, '#EC4899', 13),
    ('test_architect', 'Архитектор тестов', 'Test Architect', 3650, '#DB2777', 14),
    ('qa_master', 'Мастер QA', 'QA Master', 4750, '#F97316', 15),
    ('legend', 'Легенда', 'Legend', 6500, '#FBBF24', 16)
ON CONFLICT (id) DO NOTHING;

-- Добавить опциональное поле current_rank_id в таблицу users (для кэширования)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'current_rank_id'
    ) THEN
        ALTER TABLE users ADD COLUMN current_rank_id VARCHAR(50) REFERENCES ranks(id);
    END IF;
END $$;

-- Создать индекс для быстрого поиска по баллам (если будет использоваться поле total_points в users)
-- Пока оставляем без этого, так как баллы рассчитываются динамически
