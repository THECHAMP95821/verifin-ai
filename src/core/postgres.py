from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from ..core.config import settings

engine = create_async_engine(
    str(settings.DATABASE_URL),
    pool_size=20,
    max_overflow=10,
    pool_recycle=1800,
    pool_pre_ping=True
)

AsyncSessionFactory  = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False
)

