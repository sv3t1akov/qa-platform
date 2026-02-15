-- Добавить колонку requirements в missions (для T3 и др.).
-- Идемпотентно: если колонка уже есть, ошибка игнорируется в migrate.py.
ALTER TABLE missions ADD COLUMN IF NOT EXISTS requirements TEXT;
