-- Скрипт для выдачи админских прав пользователю и открытия доступа ко всем заданиям
-- Использование: выполните этот SQL скрипт в вашей базе данных PostgreSQL

BEGIN;

-- 1. Установить роль admin для пользователя
UPDATE users 
SET role = 'admin'::user_role
WHERE email = 'alexandrsvet@gmail.com';

-- Проверить, что пользователь найден
DO $$
DECLARE
    user_found BOOLEAN;
    user_id_val UUID;
BEGIN
    SELECT EXISTS(SELECT 1 FROM users WHERE email = 'alexandrsvet@gmail.com') INTO user_found;
    IF NOT user_found THEN
        RAISE EXCEPTION 'Пользователь с email alexandrsvet@gmail.com не найден';
    END IF;
    
    SELECT id INTO user_id_val FROM users WHERE email = 'alexandrsvet@gmail.com';
    RAISE NOTICE 'Пользователь найден: ID = %', user_id_val;
END $$;

-- 2. Добавить все найденные флаги для всех багов
-- Это откроет доступ ко всем заданиям (прогресс 100% по всем тирам)
INSERT INTO user_found_flags (id, user_id, bug_id, found_at)
SELECT 
    gen_random_uuid(),
    (SELECT id FROM users WHERE email = 'alexandrsvet@gmail.com'),
    bugs.id,
    NOW()
FROM bugs
WHERE bugs.id NOT IN (
    SELECT bug_id 
    FROM user_found_flags 
    WHERE user_id = (SELECT id FROM users WHERE email = 'alexandrsvet@gmail.com')
)
ON CONFLICT DO NOTHING;

-- 3. Вывести статистику
DO $$
DECLARE
    total_bugs INTEGER;
    found_flags INTEGER;
    user_id_val UUID;
BEGIN
    SELECT id INTO user_id_val FROM users WHERE email = 'alexandrsvet@gmail.com';
    
    SELECT COUNT(*) INTO total_bugs FROM bugs;
    SELECT COUNT(*) INTO found_flags 
    FROM user_found_flags 
    WHERE user_id = user_id_val;
    
    RAISE NOTICE 'Статистика для пользователя alexandrsvet@gmail.com:';
    RAISE NOTICE '  - Всего багов в системе: %', total_bugs;
    RAISE NOTICE '  - Найдено флагов: %', found_flags;
    RAISE NOTICE '  - Роль: admin';
END $$;

COMMIT;

-- Проверка результата
SELECT 
    u.email,
    u.role,
    COUNT(DISTINCT uff.bug_id) as found_flags_count,
    (SELECT COUNT(*) FROM bugs) as total_bugs_count
FROM users u
LEFT JOIN user_found_flags uff ON uff.user_id = u.id
WHERE u.email = 'alexandrsvet@gmail.com'
GROUP BY u.email, u.role;
