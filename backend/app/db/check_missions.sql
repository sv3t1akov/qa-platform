-- Проверка наличия миссий
SELECT COUNT(*) as mission_count FROM missions;
SELECT id, title FROM missions ORDER BY id LIMIT 5;
