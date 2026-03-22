from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

DATABASE_URL = (
    f"postgresql://{settings.db_user}:{settings.db_password}"
    f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
)

try:
    engine = create_engine(DATABASE_URL)
    logger.info(f"DB 엔진 생성 성공: {settings.db_host}:{settings.db_port}/{settings.db_name}")
except Exception as e:
    logger.error(f"DB 엔진 생성 실패: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
