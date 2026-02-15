"""
Сервис авторизации
"""
import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional
import secrets
import hashlib
import logging
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.models.user import User, UserRole
from app.models.mission import UserSession

logger = logging.getLogger(__name__)
# Argon2 memory_cost: 65536=64MB (много для VM 256MB), 8192=8MB — безопасно для Fly.io
# Переменная ARGON2_MEMORY_COST позволяет снизить при OOM на проде
_argon2_memory = int(os.getenv("ARGON2_MEMORY_COST", "8192"))
_password_verify_timeout = float(os.getenv("PASSWORD_VERIFY_TIMEOUT_SECONDS", "8"))
# Используем Argon2 - современный алгоритм хеширования паролей без ограничений по длине
# Argon2 не имеет ограничения в 72 байта как bcrypt, поэтому не требуется двойное хеширование
# Argon2id - рекомендуемый вариант, устойчивый к side-channel атакам
# Поддерживаем bcrypt для обратной совместимости со старыми хешами
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],  # Поддержка обоих алгоритмов для миграции
    argon2__memory_cost=_argon2_memory,  # По умолчанию 8 MB — подходит для VM 256 MB
    argon2__parallelism=2,          # 2 потока
    argon2__rounds=3,              # 3 итерации
    deprecated="auto"
)

# Версия кода для проверки деплоя
AUTH_SERVICE_VERSION = "3.0.0-argon2"
logger.info(f"AuthService initialized with version: {AUTH_SERVICE_VERSION}")
logger.info(f"Password verify timeout configured: {_password_verify_timeout}s")


class AuthService:
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Хеширование пароля с использованием Argon2.
        Argon2 не имеет ограничений по длине пароля (в отличие от bcrypt с лимитом 72 байта),
        поэтому пароли любой длины обрабатываются напрямую без предварительного хеширования.
        """
        # #region agent log
        password_bytes = password.encode('utf-8')
        password_len_bytes = len(password_bytes)
        logger.info(f"hash_password called: password_len_bytes={password_len_bytes}, password_len_chars={len(password)}")
        # #endregion
        
        # Argon2 не имеет ограничения в 72 байта, поэтому можем хешировать пароль напрямую
        # Это устраняет проблемы с двойным хешированием и обеспечивает лучшую безопасность
        result = pwd_context.hash(password)
        # #region agent log
        logger.info(f"Password hashed successfully with Argon2 (length: {password_len_bytes} bytes)")
        # #endregion
        return result
    
    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        """
        Проверка пароля с использованием Argon2.
        Argon2 не имеет ограничений по длине пароля, поэтому проверка выполняется напрямую.
        
        Поддерживает автоматическое определение алгоритма хеширования из строки хеша,
        что позволяет проверять как старые bcrypt хеши (для миграции), так и новые Argon2 хеши.
        """
        # #region agent log
        password_bytes = plain.encode('utf-8')
        password_len_bytes = len(password_bytes)
        logger.debug(f"verify_password called: password_len_bytes={password_len_bytes}")
        # #endregion
        
        # Argon2 не имеет ограничения в 72 байта, поэтому проверяем пароль напрямую
        # passlib автоматически определяет алгоритм из строки хеша (благодаря schemes=["argon2", "bcrypt"])
        # Это позволяет проверять как старые bcrypt хеши (для миграции), так и новые Argon2 хеши
        
        # Проверяем, является ли хеш старым bcrypt хешем с возможным двойным хешированием
        if hashed.startswith("$2b$") or hashed.startswith("$2a$") or hashed.startswith("$2y$"):
            # Это старый bcrypt-хеш.
            # Важно: не делать повторную verify() в конце метода, иначе стоимость проверки удваивается.
            # #region agent log
            logger.debug("Detected bcrypt hash, checking with migration compatibility")
            # #endregion
            try:
                if pwd_context.verify(plain, hashed):
                    return True
            except Exception as e:
                logger.warning("Direct bcrypt verification failed: %s", e)
                return False
            
            # Для legacy-кейса с длинными паролями пробуем fallback с SHA-256 pre-hash.
            password_len_bytes = len(plain.encode('utf-8'))
            if password_len_bytes > 72:
                # #region agent log
                logger.debug("Password > 72 bytes, trying with SHA-256 pre-hash for bcrypt compatibility")
                # #endregion
                try:
                    prehashed = hashlib.sha256(plain.encode('utf-8')).hexdigest()
                    return pwd_context.verify(prehashed, hashed)
                except Exception as e:
                    logger.warning("Bcrypt pre-hash verification failed: %s", e)
                    return False
            
            return False
        
        # Для новых Argon2 хешей или если bcrypt проверка не сработала
        try:
            result = pwd_context.verify(plain, hashed)
            # #region agent log
            logger.debug(f"Password verification completed: {'success' if result else 'failed'}")
            # #endregion
            return result
        except Exception as e:
            # #region agent log
            logger.error(f"Password verification error: {e}")
            # #endregion
            return False
    
    @staticmethod
    def create_access_token(user_id: str, role: str) -> str:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": str(user_id),
            "role": role,
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    @staticmethod
    def create_refresh_token() -> tuple[str, str]:
        """Returns (token, token_hash)"""
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return token, token_hash
    
    @staticmethod
    def verify_access_token(token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            if payload.get("type") != "access":
                return None
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def generate_reset_token() -> str:
        return secrets.token_urlsafe(32)
    
    async def register(
        self, 
        db: AsyncSession, 
        email: str, 
        password: str, 
        display_name: Optional[str] = None
    ) -> User:
        # #region agent log
        logger.info(f"AuthService.register called: email={email}, display_name={display_name}, password_len={len(password) if password else 0}")
        # #endregion
        
        import asyncio
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                # Проверка существующего пользователя с блокировкой для защиты от race condition
                # Используем SELECT FOR UPDATE для блокировки строки до конца транзакции
                # #region agent log
                logger.info(f"AuthService.register: Attempt {attempt + 1}/{max_retries}: Checking if user exists with email={email.lower()} (with lock)")
                # #endregion
                result = await db.execute(
                    select(User)
                    .where(User.email == email.lower())
                    .with_for_update()  # Блокировка строки для защиты от race condition
                )
                # #region agent log
                logger.info("AuthService.register: Query executed successfully")
                # #endregion
                existing = result.scalar_one_or_none()
                if existing:
                    # #region agent log
                    logger.warning(f"AuthService.register: User already exists with email={email}")
                    # #endregion
                    raise ValueError("Пользователь с таким email уже существует")
                
                # #region agent log
                logger.info("AuthService.register: Creating new user object")
                password_bytes = password.encode('utf-8')
                logger.info(f"AuthService.register: Password length in bytes: {len(password_bytes)}, chars: {len(password)}")
                # #endregion
                
                # Хешируем пароль (hash_password сам обрабатывает длинные пароли)
                password_hash = self.hash_password(password)
                # #region agent log
                logger.info("AuthService.register: Password hashed successfully")
                # #endregion
                
                # Генерируем токен для верификации email
                verification_token = secrets.token_urlsafe(32)
                
                user = User(
                    email=email.lower(),
                    password_hash=password_hash,
                    display_name=display_name or email.split('@')[0],
                    role=UserRole.student,
                    email_verified='false',
                    verification_token=verification_token,
                    verification_token_expires_at=datetime.utcnow() + timedelta(days=7)  # Токен действителен 7 дней
                )
                # #region agent log
                logger.info("AuthService.register: Adding user to session")
                # #endregion
                db.add(user)
                # #region agent log
                logger.info("AuthService.register: Attempting to commit user to database")
                # #endregion
                await db.commit()
                # #region agent log
                logger.info("AuthService.register: Commit successful, refreshing user")
                # #endregion
                await db.refresh(user)
                # #region agent log
                logger.info(f"AuthService.register: User created successfully: id={user.id}, email={user.email}")
                # #endregion
                return user
                
            except ValueError as e:
                # ValueError не требует retry - это бизнес-логика
                # #region agent log
                logger.error(f"AuthService.register: ValueError: {e}")
                # #endregion
                raise
            except IntegrityError as e:
                # Ошибка уникальности (дубликат email) - не требует retry
                # #region agent log
                logger.warning(f"AuthService.register: IntegrityError (likely duplicate email): {e}")
                # #endregion
                await db.rollback()
                raise ValueError("Пользователь с таким email уже существует")
            except (ConnectionResetError, ConnectionError, OSError) as e:
                # Сетевые ошибки - пробуем retry
                if attempt < max_retries - 1:
                    # #region agent log
                    logger.warning(f"AuthService.register: Connection error on attempt {attempt + 1}: {type(e).__name__}: {e}. Retrying in {retry_delay}s...")
                    # #endregion
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    # Попробуем откатить транзакцию перед retry
                    try:
                        await db.rollback()
                    except:
                        pass
                else:
                    # #region agent log
                    logger.exception(f"AuthService.register: Connection error after {max_retries} attempts: {type(e).__name__}: {e}")
                    # #endregion
                    raise ValueError("Ошибка подключения к базе данных. Попробуйте позже.")
            except Exception as e:
                # Другие ошибки - не retry, просто логируем и пробрасываем
                # #region agent log
                logger.exception(f"AuthService.register: Unexpected error: {type(e).__name__}: {e}")
                # #endregion
                raise ValueError(f"Ошибка при регистрации: {str(e)}")
    
    async def authenticate(
        self, 
        db: AsyncSession, 
        email: str, 
        password: str
    ) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email.lower()))
        user = result.scalar_one_or_none()
        if not user or not user.password_hash:
            return None
        try:
            # Вынесено в отдельный thread + timeout, чтобы "тяжёлые" legacy-хеши
            # не блокировали event loop и не приводили к 502 на уровне прокси.
            password_ok = await asyncio.wait_for(
                asyncio.to_thread(self.verify_password, password, user.password_hash),
                timeout=_password_verify_timeout
            )
        except asyncio.TimeoutError:
            logger.warning(
                "Password verification timed out for user=%s after %.1fs",
                email.lower(),
                _password_verify_timeout
            )
            return None
        except Exception as e:
            logger.exception("Password verification failed for user=%s: %s", email.lower(), e)
            return None
        
        if not password_ok:
            return None
        user.last_login_at = datetime.utcnow()
        await db.commit()
        return user
    
    async def create_session(
        self,
        db: AsyncSession,
        user_id: str,
        refresh_token: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> UserSession:
        """Создать сессию с refresh token"""
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        session = UserSession(
            user_id=user_id,
            refresh_token_hash=token_hash,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session
    
    async def revoke_session(
        self,
        db: AsyncSession,
        refresh_token: str
    ) -> bool:
        """Отозвать сессию по refresh token"""
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        result = await db.execute(
            select(UserSession).where(
                UserSession.refresh_token_hash == token_hash,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > datetime.utcnow()
            )
        )
        session = result.scalar_one_or_none()
        if session:
            session.revoked_at = datetime.utcnow()
            await db.commit()
            return True
        return False
    
    async def revoke_all_user_sessions(
        self,
        db: AsyncSession,
        user_id: str
    ) -> int:
        """Отозвать все сессии пользователя"""
        result = await db.execute(
            select(UserSession).where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None)
            )
        )
        sessions = result.scalars().all()
        count = 0
        for session in sessions:
            session.revoked_at = datetime.utcnow()
            count += 1
        await db.commit()
        return count
    
    async def verify_refresh_token(
        self,
        db: AsyncSession,
        refresh_token: str
    ) -> Optional[User]:
        """Проверить refresh token и вернуть пользователя"""
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        result = await db.execute(
            select(UserSession).join(User).where(
                UserSession.refresh_token_hash == token_hash,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > datetime.utcnow()
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            return None
        
        # Получить пользователя
        user_result = await db.execute(select(User).where(User.id == session.user_id))
        return user_result.scalar_one_or_none()
    
    async def find_user_by_email(
        self,
        db: AsyncSession,
        email: str
    ) -> Optional[User]:
        """Найти пользователя по email"""
        result = await db.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()
    
    async def find_or_create_google_user(
        self,
        db: AsyncSession,
        google_id: str,
        email: str,
        display_name: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> User:
        """Найти или создать пользователя через Google OAuth"""
        # Сначала ищем по google_id
        result = await db.execute(select(User).where(User.google_id == google_id))
        user = result.scalar_one_or_none()
        
        if user:
            # Обновляем данные
            user.email = email.lower()
            if display_name:
                user.display_name = display_name
            if avatar_url:
                user.avatar_url = avatar_url
            user.last_login_at = datetime.utcnow()
            await db.commit()
            await db.refresh(user)
            return user
        
        # Ищем по email (может быть зарегистрирован через обычную регистрацию)
        result = await db.execute(select(User).where(User.email == email.lower()))
        user = result.scalar_one_or_none()
        
        if user:
            # Привязываем Google ID
            user.google_id = google_id
            if avatar_url:
                user.avatar_url = avatar_url
            user.last_login_at = datetime.utcnow()
            await db.commit()
            await db.refresh(user)
            return user
        
        # Создаем нового пользователя
        user = User(
            email=email.lower(),
            google_id=google_id,
            display_name=display_name or email.split('@')[0],
            avatar_url=avatar_url,
            role=UserRole.student,
            password_hash=None  # OAuth пользователь
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    async def set_reset_token(
        self,
        db: AsyncSession,
        user: User
    ) -> str:
        """Установить токен для сброса пароля"""
        token = self.generate_reset_token()
        user.reset_token = token
        user.reset_token_expires_at = datetime.utcnow() + timedelta(hours=1)
        await db.commit()
        return token
    
    async def reset_password(
        self,
        db: AsyncSession,
        token: str,
        new_password: str
    ) -> Optional[User]:
        """Сбросить пароль по токену"""
        result = await db.execute(
            select(User).where(
                User.reset_token == token,
                User.reset_token_expires_at > datetime.utcnow()
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        user.password_hash = self.hash_password(new_password)
        user.reset_token = None
        user.reset_token_expires_at = None
        await db.commit()
        await db.refresh(user)
        return user
    
    async def verify_email_token(
        self,
        db: AsyncSession,
        token: str
    ) -> Optional[User]:
        """Верифицировать email по токену"""
        result = await db.execute(
            select(User).where(
                User.verification_token == token,
                User.verification_token_expires_at > datetime.utcnow()
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        user.email_verified = 'true'
        user.verification_token = None
        user.verification_token_expires_at = None
        await db.commit()
        await db.refresh(user)
        return user
    
    async def set_verification_token(
        self,
        db: AsyncSession,
        user: User
    ) -> str:
        """Установить токен для верификации email"""
        token = secrets.token_urlsafe(32)
        user.verification_token = token
        user.verification_token_expires_at = datetime.utcnow() + timedelta(days=7)
        await db.commit()
        return token
