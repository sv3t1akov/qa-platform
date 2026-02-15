"""
Скрипт для применения миграций к базе данных
Можно запустить локально или в контейнере после деплоя
"""
import asyncio
import os
import logging
from sqlalchemy import text
from app.db.session import engine
import asyncpg

logger = logging.getLogger(__name__)


async def run_migration():
    """Применить миграции из SQL файлов"""
    import logging
    logger = logging.getLogger(__name__)
    
    schema_file = os.path.join(os.path.dirname(__file__), 'schema.sql')
    seed_missions_file = os.path.join(os.path.dirname(__file__), 'seed_missions.sql')
    seed_bugs_file = os.path.join(os.path.dirname(__file__), 'seed_bugs.sql')
    seed_file = os.path.join(os.path.dirname(__file__), 'seed.sql')  # Fallback
    # Booking T1 seed files
    seed_booking_t1_missions_file = os.path.join(os.path.dirname(__file__), 'seed_booking_t1_missions.sql')
    seed_booking_t1_bugs_file = os.path.join(os.path.dirname(__file__), 'seed_booking_t1_bugs.sql')
    # Social T1 seed files
    seed_social_t1_missions_file = os.path.join(os.path.dirname(__file__), 'seed_social_t1_missions.sql')
    seed_social_t1_bugs_file = os.path.join(os.path.dirname(__file__), 'seed_social_t1_bugs.sql')
    
    if not engine:
        logger.error("Database engine is not initialized. Cannot run migrations.")
        return
    
    try:
        # Применить schema.sql - выполняем целиком, так как разбиение ломает dollar-quoted strings
        if os.path.exists(schema_file):
            logger.info(f"Applying {schema_file}...")
            try:
                with open(schema_file, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                
                # #region agent log
                logger.info(f"Schema SQL length: {len(schema_sql)} characters")
                # #endregion
                
                # Выполняем schema.sql используя asyncpg напрямую для лучшего контроля
                # Это позволяет игнорировать ошибки "already exists" без отката всей транзакции
                database_url = os.getenv("DATABASE_URL", "")
                if not database_url:
                    raise RuntimeError("DATABASE_URL not set")
                
                # Преобразуем DATABASE_URL для asyncpg
                if database_url.startswith("postgres://"):
                    database_url = database_url.replace("postgres://", "postgresql://", 1)
                
                # Парсим URL для получения параметров подключения
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(database_url)
                query_params = parse_qs(parsed.query)
                
                # Извлекаем параметры подключения
                host = parsed.hostname
                port = parsed.port or 5432
                user = parsed.username
                password = parsed.password
                database = parsed.path.lstrip('/')
                
                # Для Fly.io внутренних подключений используем ssl=False
                # #region agent log
                logger.info(f"Connecting to database for schema migration: host={host}, port={port}, database={database}")
                # #endregion
                
                # Пробуем подключиться через asyncpg с явными параметрами SSL
                # Для внутренних подключений Fly.io SSL не требуется
                try:
                    conn = await asyncpg.connect(
                        host=host,
                        port=port,
                        user=user,
                        password=password,
                        database=database,
                        ssl=False  # Для внутренних подключений Fly.io
                    )
                    try:
                        # Выполняем schema.sql - asyncpg позволяет лучше контролировать ошибки
                        # #region agent log
                        logger.info("Executing schema.sql via asyncpg...")
                        # #endregion
                        
                        # Выполняем SQL и игнорируем ошибки "already exists"
                        try:
                            await conn.execute(schema_sql)
                            # #region agent log
                            logger.info("Schema SQL executed successfully via asyncpg")
                            # #endregion
                        except Exception as sql_error:
                            error_msg = str(sql_error).lower()
                            # Игнорируем ошибки "already exists" - это нормально
                            if 'already exists' in error_msg or 'duplicate' in error_msg:
                                logger.info("Some schema objects already exist, this is expected")
                            else:
                                logger.warning(f"Schema execution had some errors: {type(sql_error).__name__}: {sql_error}")
                                logger.warning("Continuing to check if tables were created...")
                        
                    finally:
                        await conn.close()
                        
                except Exception as conn_error:
                    # Если asyncpg не работает, пробуем через SQLAlchemy engine
                    logger.warning(f"asyncpg connection failed: {conn_error}, trying SQLAlchemy engine...")
                    try:
                        async with engine.begin() as conn:
                            await conn.execute(text(schema_sql))
                        logger.info("Schema SQL executed successfully via SQLAlchemy")
                    except Exception as sql_error:
                        error_msg = str(sql_error).lower()
                        if 'already exists' in error_msg or 'duplicate' in error_msg:
                            logger.info("Some schema objects already exist, this is expected")
                        else:
                            logger.warning(f"Schema execution via SQLAlchemy had errors: {type(sql_error).__name__}: {sql_error}")
                
                # Проверяем, что таблицы созданы
                # #region agent log
                logger.info("Schema SQL executed, checking if tables exist...")
                # #endregion
                async with engine.begin() as conn:
                    result = await conn.execute(text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name IN ('users', 'domains', 'missions', 'bugs', 'user_mission_progress', 'user_found_flags', 'user_sessions')
                        ORDER BY table_name
                    """))
                    tables = [row[0] for row in result.fetchall()]
                    # #region agent log
                    logger.info(f"Tables found in database: {tables}")
                    # #endregion
                    required_tables = ['users', 'domains', 'missions', 'bugs']
                    missing_tables = [t for t in required_tables if t not in tables]
                    if missing_tables:
                        logger.error(f"CRITICAL: Missing tables: {missing_tables}")
                        # Попробуем создать недостающие таблицы вручную
                        logger.warning("Attempting to create missing tables...")
                        raise RuntimeError(f"Schema migration incomplete: missing tables {missing_tables}")
                    else:
                        logger.info("All required tables exist!")
                
                logger.info("Schema applied successfully!")
            except RuntimeError as e:
                # Пробрасываем RuntimeError (критические ошибки)
                logger.exception(f"Schema migration failed: {e}")
                raise
            except Exception as e:
                # Игнорируем другие ошибки, но логируем их
                error_msg = str(e).lower()
                if 'already exists' in error_msg or 'duplicate' in error_msg:
                    logger.info("Schema already exists, skipping...")
                else:
                    logger.exception(f"Schema migration error: {type(e).__name__}: {e}")
                    # Проверяем существующие таблицы даже при ошибках
                    try:
                        async with engine.begin() as conn:
                            result = await conn.execute(text("""
                                SELECT table_name 
                                FROM information_schema.tables 
                                WHERE table_schema = 'public' 
                                AND table_name IN ('users', 'bugs')
                            """))
                            tables = [row[0] for row in result.fetchall()]
                            logger.info(f"Existing tables after error: {tables}")
                            if 'users' not in tables:
                                logger.error("CRITICAL: 'users' table does not exist after migration!")
                    except:
                        pass
        
        # Применить миграцию для создания ENUM типов (должна быть первой)
        migration_enum_types_file = os.path.join(os.path.dirname(__file__), 'migrations', 'ensure_enum_types.sql')
        if os.path.exists(migration_enum_types_file):
            logger.info(f"Applying {migration_enum_types_file}...")
            try:
                async with engine.begin() as conn:
                    with open(migration_enum_types_file, 'r', encoding='utf-8') as f:
                        migration_sql = f.read()
                        await conn.execute(text(migration_sql))
                logger.info("Enum types migration applied successfully!")
            except Exception as e:
                error_msg = str(e).lower()
                if 'already exists' in error_msg or 'duplicate' in error_msg:
                    logger.info("Enum types already exist, skipping...")
                else:
                    logger.warning(f"Enum types migration warning: {e}")
        
        # Применить миграцию email-верификации
        migration_email_verification_file = os.path.join(os.path.dirname(__file__), 'migrations', 'add_email_verification.sql')
        if os.path.exists(migration_email_verification_file):
            logger.info(f"Applying {migration_email_verification_file}...")
            try:
                async with engine.begin() as conn:
                    with open(migration_email_verification_file, 'r', encoding='utf-8') as f:
                        migration_sql = f.read()
                        await conn.execute(text(migration_sql))
                logger.info("Email verification migration applied successfully!")
            except Exception as e:
                error_msg = str(e).lower()
                if 'already exists' in error_msg or 'duplicate' in error_msg:
                    logger.info("Email verification fields already exist, skipping...")
                else:
                    logger.warning(f"Email verification migration warning: {e}")
        
        # Применить миграцию: колонка requirements в missions (T3 и др.)
        migration_requirements_file = os.path.join(os.path.dirname(__file__), 'migrations', 'add_requirements_column.sql')
        if os.path.exists(migration_requirements_file):
            logger.info(f"Applying {migration_requirements_file}...")
            try:
                async with engine.begin() as conn:
                    with open(migration_requirements_file, 'r', encoding='utf-8') as f:
                        migration_sql = f.read()
                        await conn.execute(text(migration_sql))
                logger.info("Requirements column migration applied successfully!")
            except Exception as e:
                error_msg = str(e).lower()
                if 'already exists' in error_msg or 'duplicate' in error_msg:
                    logger.info("Requirements column already exists, skipping...")
                else:
                    logger.warning(f"Requirements column migration warning: {e}")
        
        # Применить seed.sql для доменов ПЕРЕД seed_missions.sql (так как миссии ссылаются на домены)
        if os.path.exists(seed_file):
            logger.info(f"Applying domains from {seed_file}...")
            try:
                async with engine.begin() as conn:
                    with open(seed_file, 'r', encoding='utf-8') as f:
                        seed_sql = f.read()
                        # Извлекаем только INSERT для доменов (до строки с миссиями)
                        lines = seed_sql.split('\n')
                        domain_lines = []
                        for line in lines:
                            domain_lines.append(line)
                            # Останавливаемся когда встречаем комментарий о миссиях
                            if '-- Миссии' in line or 'INSERT INTO missions' in line:
                                break
                        domain_seed = "\n".join(domain_lines)
                        if domain_seed.strip() and 'INSERT INTO domains' in domain_seed:
                            await conn.execute(text(domain_seed))
                            logger.info("Domains seed applied successfully!")
            except Exception as e:
                error_msg = str(e).lower()
                if 'already exists' in error_msg or 'duplicate' in error_msg or 'violates foreign key' in error_msg:
                    logger.info("Domains seed already exists or has conflicts, skipping...")
                else:
                    logger.warning(f"Domains seed migration warning: {e}")
        
        # Применить seed_missions.sql в отдельной транзакции
        if os.path.exists(seed_missions_file):
            logger.info(f"Applying {seed_missions_file}...")
            try:
                async with engine.begin() as conn:
                    with open(seed_missions_file, 'r', encoding='utf-8') as f:
                        seed_sql = f.read()
                        await conn.execute(text(seed_sql))
                logger.info("Seed missions applied successfully!")
            except Exception as e:
                error_msg = str(e).lower()
                if 'already exists' in error_msg or 'duplicate' in error_msg or 'violates foreign key' in error_msg:
                    logger.info("Seed missions already exist or have conflicts, skipping...")
                else:
                    logger.warning(f"Seed missions migration warning: {e}")
        
        # Применить seed_bugs.sql в отдельной транзакции
        if os.path.exists(seed_bugs_file):
            logger.info(f"Applying {seed_bugs_file}...")
            try:
                async with engine.begin() as conn:
                    with open(seed_bugs_file, 'r', encoding='utf-8') as f:
                        seed_sql = f.read()
                        await conn.execute(text(seed_sql))
                logger.info("Seed bugs applied successfully!")
            except Exception as e:
                error_msg = str(e).lower()
                if 'already exists' in error_msg or 'duplicate' in error_msg or 'violates foreign key' in error_msg:
                    logger.info("Seed bugs already exist or have conflicts, skipping...")
                else:
                    logger.warning(f"Seed bugs migration warning: {e}")
        
        # Применить seed_booking_t1_missions.sql (после основных seed файлов)
        if os.path.exists(seed_booking_t1_missions_file):
            logger.info(f"Applying {seed_booking_t1_missions_file}...")
            try:
                async with engine.begin() as conn:
                    with open(seed_booking_t1_missions_file, 'r', encoding='utf-8') as f:
                        seed_sql = f.read()
                        await conn.execute(text(seed_sql))
                logger.info("Booking T1 missions seed applied successfully!")
            except Exception as e:
                error_msg = str(e).lower()
                if 'already exists' in error_msg or 'duplicate' in error_msg or 'violates foreign key' in error_msg:
                    logger.info("Booking T1 missions seed already exists or has conflicts, skipping...")
                else:
                    logger.warning(f"Booking T1 missions seed migration warning: {e}")
        
        # Применить seed_booking_t1_bugs.sql (после миссий)
        if os.path.exists(seed_booking_t1_bugs_file):
            logger.info(f"Applying {seed_booking_t1_bugs_file}...")
            try:
                async with engine.begin() as conn:
                    with open(seed_booking_t1_bugs_file, 'r', encoding='utf-8') as f:
                        seed_sql = f.read()
                        await conn.execute(text(seed_sql))
                logger.info("Booking T1 bugs seed applied successfully!")
            except Exception as e:
                error_msg = str(e).lower()
                if 'already exists' in error_msg or 'duplicate' in error_msg or 'violates foreign key' in error_msg:
                    logger.info("Booking T1 bugs seed already exists or has conflicts, skipping...")
                else:
                    logger.warning(f"Booking T1 bugs seed migration warning: {e}")
        
        # Применить seed_social_t1_missions.sql (по одному INSERT для совместимости)
        if os.path.exists(seed_social_t1_missions_file):
            logger.info(f"Applying {seed_social_t1_missions_file}...")
            try:
                with open(seed_social_t1_missions_file, 'r', encoding='utf-8') as f:
                    seed_content = f.read()
                # Разбиваем на отдельные INSERT (каждый заканчивается на ); перед следующим INSERT)
                import re
                statements = re.split(r';\s*(?=INSERT INTO missions)', seed_content)
                statements = [s.strip() for s in statements if s.strip()]
                async with engine.begin() as conn:
                    for i, stmt in enumerate(statements):
                        if stmt:
                            stmt = stmt.rstrip()
                            if not stmt.endswith(';'):
                                stmt += ';'
                            await conn.execute(text(stmt))
                            logger.info(f"Social T1 mission {i+1}/{len(statements)} applied")
                logger.info("Social T1 missions seed applied successfully!")
            except Exception as e:
                logger.exception(f"Social T1 missions seed FAILED: {type(e).__name__}: {e}")
                error_msg = str(e).lower()
                if 'already exists' in error_msg or 'duplicate' in error_msg or 'violates foreign key' in error_msg:
                    logger.info("Social T1 missions seed already exists or has conflicts, skipping...")
                else:
                    logger.warning(f"Social T1 missions seed migration warning: {e}")
        
        # Применить seed_social_t1_bugs.sql
        if os.path.exists(seed_social_t1_bugs_file):
            logger.info(f"Applying {seed_social_t1_bugs_file}...")
            try:
                async with engine.begin() as conn:
                    with open(seed_social_t1_bugs_file, 'r', encoding='utf-8') as f:
                        seed_sql = f.read()
                        await conn.execute(text(seed_sql))
                logger.info("Social T1 bugs seed applied successfully!")
            except Exception as e:
                logger.exception(f"Social T1 bugs seed FAILED: {type(e).__name__}: {e}")
                error_msg = str(e).lower()
                if 'already exists' in error_msg or 'duplicate' in error_msg or 'violates foreign key' in error_msg:
                    logger.info("Social T1 bugs seed already exists or has conflicts, skipping...")
                else:
                    logger.warning(f"Social T1 bugs seed migration warning: {e}")
        
        # Phase2: колонка bugs.active и пометка убранных T2/T3 багов как неактивных
        # Выполняем по одному запросу — asyncpg выполняет только первую команду при передаче нескольких через один execute()
        migration_phase2_file = os.path.join(os.path.dirname(__file__), 'migrations', 'add_bugs_active_phase2.sql')
        if os.path.exists(migration_phase2_file):
            logger.info(f"Applying Phase2 migration (add_bugs_active_phase2.sql)...")
            try:
                with open(migration_phase2_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Убираем комментарии и разбиваем по ; (только на верхнем уровне — по строкам, заканчивающимся на ); или на ;)
                statements = []
                current = []
                for line in content.splitlines():
                    stripped = line.strip()
                    if not stripped or stripped.startswith('--'):
                        continue
                    current.append(line)
                    if stripped.endswith(';'):
                        stmt = '\n'.join(current).strip()
                        if stmt:
                            statements.append(stmt)
                        current = []
                if current:
                    stmt = '\n'.join(current).strip()
                    if stmt:
                        statements.append(stmt)
                if not statements:
                    logger.warning("Phase2 migration file produced no statements (check file format)")
                else:
                    async with engine.begin() as conn:
                        for i, stmt in enumerate(statements):
                            if not stmt.endswith(';'):
                                stmt = stmt + ';'
                            await conn.execute(text(stmt))
                            logger.info(f"Phase2 statement {i+1}/{len(statements)} applied")
                    logger.info("Phase2 bugs.active migration applied successfully!")
            except Exception as e:
                error_msg = str(e).lower()
                if 'already exists' in error_msg or 'duplicate' in error_msg:
                    logger.info("Phase2 migration already applied, skipping...")
                else:
                    logger.warning(f"Phase2 migration warning: {e}")
        else:
            logger.warning(f"Phase2 migration file not found: {migration_phase2_file}")
        
        # Fallback: применить весь seed.sql в отдельной транзакции (если существует и seed_missions.sql не применялся)
        if os.path.exists(seed_file) and not os.path.exists(seed_missions_file):
            logger.info(f"Applying full {seed_file}...")
            try:
                async with engine.begin() as conn:
                    with open(seed_file, 'r', encoding='utf-8') as f:
                        seed_sql = f.read()
                        await conn.execute(text(seed_sql))
                logger.info("Full seed data applied successfully!")
            except Exception as e:
                error_msg = str(e).lower()
                if 'already exists' in error_msg or 'duplicate' in error_msg or 'violates foreign key' in error_msg:
                    logger.info("Seed data already exists or has conflicts, skipping...")
                else:
                    logger.warning(f"Seed data migration warning: {e}")
        
        logger.info("Migration completed!")
    except Exception as e:
        logger.exception(f"Migration error: {type(e).__name__}: {e}")
        # Не пробрасываем исключение, чтобы приложение могло запуститься даже при ошибках миграций
        logger.warning("Continuing despite migration errors - some tables/data may be missing")


if __name__ == "__main__":
    if not os.getenv("DATABASE_URL"):
        print("ERROR: DATABASE_URL environment variable is not set")
        exit(1)
    
    asyncio.run(run_migration())
