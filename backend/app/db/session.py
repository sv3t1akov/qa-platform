"""
Database session management for SQLAlchemy async
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import os
import logging

logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "")

# #region agent log
logger.info(f"session.py: Initializing with DATABASE_URL check. Length: {len(DATABASE_URL) if DATABASE_URL else 0}. Starts with postgres://: {DATABASE_URL.startswith('postgres://') if DATABASE_URL else 'N/A'}")
# #endregion

# Convert postgres:// to postgresql+asyncpg:// for async support
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    # #region agent log
    logger.info(f"session.py: Converted postgres:// to postgresql+asyncpg://")
    # #endregion

# Process DATABASE_URL to handle SSL parameters for asyncpg
# asyncpg uses 'ssl' parameter in connect_args, not 'sslmode' in URL
# For Fly.io, we need to configure SSL properly
connect_args = {}
if DATABASE_URL:
    try:
        parsed = urlparse(DATABASE_URL)
        query_params = parse_qs(parsed.query)
        
        # Handle sslmode parameter
        sslmode = None
        if 'sslmode' in query_params:
            sslmode = query_params.pop('sslmode')[0]
            # #region agent log
            logger.info(f"session.py: Found sslmode={sslmode} in URL")
            # #endregion
            
            # Configure SSL for asyncpg based on sslmode
            # For Fly.io internal connections, we can use ssl=False or ssl='prefer'
            if sslmode == 'require' or sslmode == 'prefer':
                # For Fly.io, we'll use ssl='prefer' which allows non-SSL fallback
                # This helps avoid SSL handshake issues
                connect_args['ssl'] = 'prefer'
                # #region agent log
                logger.info(f"session.py: Setting asyncpg ssl='prefer' for sslmode={sslmode}")
                # #endregion
            elif sslmode == 'disable':
                connect_args['ssl'] = False
                # #region agent log
                logger.info(f"session.py: Setting asyncpg ssl=False for sslmode={sslmode}")
                # #endregion
            else:
                # For other modes (verify-ca, verify-full), use prefer to avoid handshake issues
                connect_args['ssl'] = 'prefer'
                # #region agent log
                logger.info(f"session.py: Using ssl='prefer' for sslmode={sslmode} to avoid SSL handshake issues")
                # #endregion
        
        # Reconstruct URL without sslmode
        new_query = urlencode(query_params, doseq=True)
        new_parsed = parsed._replace(query=new_query)
        DATABASE_URL = urlunparse(new_parsed)
        # #region agent log
        logger.info(f"session.py: Processed DATABASE_URL, connect_args={connect_args}")
        # #endregion
    except Exception as e:
        # #region agent log
        logger.warning(f"session.py: Error processing DATABASE_URL: {e}, using URL as-is")
        # #endregion

# Create async engine only if DATABASE_URL is set
if DATABASE_URL:
    try:
        # #region agent log
        logger.info(f"session.py: Creating async engine with URL (masked): {DATABASE_URL[:20]}...{DATABASE_URL[-10:] if len(DATABASE_URL) > 30 else ''}")
        # #endregion
        engine = create_async_engine(
            DATABASE_URL,
            echo=False,  # Set to True for SQL logging
            future=True,
            pool_pre_ping=True,  # Verify connections before using
            pool_size=5,  # Number of connections to maintain
            max_overflow=10,  # Maximum overflow connections
            pool_timeout=30,  # Timeout for getting connection from pool
            pool_recycle=3600,  # Recycle connections after 1 hour
            connect_args=connect_args if connect_args else {}  # SSL configuration for asyncpg
        )
        AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        # #region agent log
        logger.info("session.py: SQLAlchemy engine and sessionmaker successfully initialized.")
        # #endregion
    except Exception as e:
        # #region agent log
        logger.exception(f"session.py: ERROR during SQLAlchemy engine initialization: {type(e).__name__}: {e}")
        # #endregion
        engine = None
        AsyncSessionLocal = None
else:
    # Fallback для случаев когда DATABASE_URL не установлен (например, при старте без БД)
    logger.warning("DATABASE_URL not set, database features will be disabled")
    engine = None
    AsyncSessionLocal = None


# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Dependency for FastAPI to get database session
    """
    # #region agent log
    has_db_url = bool(DATABASE_URL)
    logger.info(f"get_db called: hasDatabaseUrl={has_db_url}, databaseUrlLength={len(DATABASE_URL) if DATABASE_URL else 0}")
    # #endregion
    if not AsyncSessionLocal:
        # #region agent log
        logger.error("get_db: AsyncSessionLocal is not configured. DATABASE_URL might be missing or invalid.")
        # #endregion
        raise RuntimeError("DATABASE_URL is not configured. Please set DATABASE_URL environment variable.")
    try:
        # #region agent log
        logger.info("get_db: Attempting to create DB session")
        # #endregion
        async with AsyncSessionLocal() as session:
            try:
                # #region agent log
                logger.info("get_db: DB session created successfully. Yielding session.")
                # #endregion
                yield session
                # #region agent log
                logger.info("get_db: Session yielded, attempting commit")
                # #endregion
                await session.commit()
                # #region agent log
                logger.info("get_db: Session committed successfully.")
                # #endregion
            except Exception as e:
                # #region agent log
                logger.exception(f"get_db: DB session error during yield or commit: {type(e).__name__}: {e}")
                # #endregion
                await session.rollback()
                raise
            finally:
                # #region agent log
                logger.info("get_db: Closing DB session.")
                # #endregion
                await session.close()
    except Exception as e:
        # #region agent log
        logger.exception(f"get_db: ERROR creating DB session: {type(e).__name__}: {e}")
        # #endregion
        raise
