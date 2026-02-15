-- Расширения
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Перечисления (с проверкой существования для идемпотентности)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
        CREATE TYPE user_role AS ENUM ('student', 'admin');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mission_status') THEN
        CREATE TYPE mission_status AS ENUM ('locked', 'available', 'in_progress', 'completed');
    END IF;
END $$;

-- Таблица пользователей
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255), -- NULL для OAuth пользователей
    role user_role DEFAULT 'student',
    
    -- OAuth данные
    google_id VARCHAR(255) UNIQUE,
    
    -- Профиль
    display_name VARCHAR(100),
    avatar_url VARCHAR(500),
    
    -- Метаданные
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    
    -- Для восстановления пароля
    reset_token VARCHAR(255),
    reset_token_expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Email верификация
    email_verified VARCHAR(10) DEFAULT 'false' NOT NULL,
    verification_token VARCHAR(255),
    verification_token_expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Домены (справочник)
CREATE TABLE domains (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    icon VARCHAR(10),
    description TEXT,
    sort_order INTEGER DEFAULT 0
);

-- Миссии (справочник)
CREATE TABLE missions (
    id VARCHAR(100) PRIMARY KEY,
    domain_id VARCHAR(50) REFERENCES domains(id),
    tier VARCHAR(5) NOT NULL CHECK (tier IN ('T1', 'T2', 'T3', 'T4', 'T5')),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    difficulty VARCHAR(20) CHECK (difficulty IN ('Beginner', 'Intermediate', 'Advanced', 'Expert', 'Hard')),
    estimated_time VARCHAR(50),
    points INTEGER DEFAULT 0,
    bugs INTEGER DEFAULT 0,
    endpoint VARCHAR(255),
    base_url VARCHAR(255),
    theory_title VARCHAR(200),
    theory_content TEXT,
    hints TEXT[], -- Массив подсказок
    task_description TEXT,
    request_body_example TEXT,
    requirements TEXT, -- Бизнес-правила и требования для T3 миссий
    sort_order INTEGER DEFAULT 0
);

-- Баги в миссиях (справочник) - захардкоженные флаги
-- active: false = Phase 2 dropped (injection/duplicates), not counted in progress
CREATE TABLE bugs (
    id VARCHAR(100) PRIMARY KEY,
    mission_id VARCHAR(100) REFERENCES missions(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    flag VARCHAR(100) UNIQUE NOT NULL, -- Захардкоженный флаг типа QA_FLAG{...}
    points INTEGER DEFAULT 0,
    difficulty VARCHAR(20) CHECK (difficulty IN ('Easy', 'Medium', 'Hard')),
    sort_order INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT true NOT NULL
);

-- Прогресс пользователя по миссиям
CREATE TABLE user_mission_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    mission_id VARCHAR(100) REFERENCES missions(id) ON DELETE CASCADE,
    status mission_status DEFAULT 'available',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(user_id, mission_id)
);

-- Найденные флаги пользователя
CREATE TABLE user_found_flags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    bug_id VARCHAR(100) REFERENCES bugs(id) ON DELETE CASCADE,
    found_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, bug_id) -- Один флаг на пользователя
);

-- Сессии (для JWT refresh tokens)
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash VARCHAR(255) NOT NULL,
    user_agent TEXT,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE
);

-- Индексы (IF NOT EXISTS для идемпотентности)
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
CREATE INDEX IF NOT EXISTS idx_user_mission_progress_user ON user_mission_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_user_found_flags_user ON user_found_flags(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_refresh_token ON user_sessions(refresh_token_hash);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at) WHERE revoked_at IS NULL;

-- Триггер для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Удалить триггер если существует, затем создать заново
DROP TRIGGER IF EXISTS users_updated_at ON users;
CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
