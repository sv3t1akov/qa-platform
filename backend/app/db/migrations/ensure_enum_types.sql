-- Миграция: убедиться, что типы ENUM существуют
-- Выполняется только если типы еще не существуют

DO $$
BEGIN
    -- Проверяем и создаем user_role
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
        CREATE TYPE user_role AS ENUM ('student', 'admin');
        RAISE NOTICE 'Created type user_role';
    ELSE
        RAISE NOTICE 'Type user_role already exists';
    END IF;
    
    -- Проверяем и создаем mission_status
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mission_status') THEN
        CREATE TYPE mission_status AS ENUM ('locked', 'available', 'in_progress', 'completed');
        RAISE NOTICE 'Created type mission_status';
    ELSE
        RAISE NOTICE 'Type mission_status already exists';
    END IF;
END $$;
