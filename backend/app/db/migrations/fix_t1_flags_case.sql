-- Миграция: Исправление регистра флагов T1
-- Проблема: Флаги в базе данных хранятся с маленькими буквами в суффиксе (a1b2c3),
-- но система валидации приводит их к верхнему регистру (A1B2C3)
-- Решение: Обновить все флаги T1 в верхний регистр

-- Обновление флагов T1 миссий
UPDATE bugs 
SET flag = UPPER(flag)
WHERE mission_id IN (
    SELECT id FROM missions WHERE tier = 'T1'
)
AND flag != UPPER(flag); -- Обновляем только те, которые отличаются

-- Проверка: все флаги T1 должны быть в верхнем регистре
-- SELECT mission_id, flag FROM bugs 
-- WHERE mission_id IN (SELECT id FROM missions WHERE tier = 'T1')
-- ORDER BY mission_id, sort_order;
