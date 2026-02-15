-- Миграция: добавление полей для email-верификации
-- Выполняется только если поля еще не существуют

-- Добавить поля для email-верификации, если их еще нет
DO $$
BEGIN
    -- Проверяем и добавляем email_verified
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'email_verified'
    ) THEN
        ALTER TABLE users ADD COLUMN email_verified VARCHAR(10) DEFAULT 'false' NOT NULL;
        -- Обновляем существующие записи
        UPDATE users SET email_verified = 'false' WHERE email_verified IS NULL;
    END IF;
    
    -- Проверяем и добавляем verification_token
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'verification_token'
    ) THEN
        ALTER TABLE users ADD COLUMN verification_token VARCHAR(255);
    END IF;
    
    -- Проверяем и добавляем verification_token_expires_at
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'verification_token_expires_at'
    ) THEN
        ALTER TABLE users ADD COLUMN verification_token_expires_at TIMESTAMP WITH TIME ZONE;
    END IF;
END $$;
