# 데이터베이스 연결과 세션을 관리하는 파일
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings


# DB 연결 객체 - 앱 전체에서 하나만 만들어서 재사용함
# pool_pre_ping=True: 연결이 끊겼을 때 자동으로 다시 연결 시도
engine = create_engine(settings.database_url, pool_pre_ping=True)

# DB 작업할 때 사용하는 세션 팩토리
# autocommit=False: 명시적으로 commit 해야 DB에 반영됨
# autoflush=False: 명시적으로 flush 해야 쿼리가 나감
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 모든 테이블 모델이 상속받는 기본 클래스
class Base(DeclarativeBase):
    pass


def create_tables() -> None:
    # Base를 상속받은 모델들을 기준으로 테이블을 생성함
    # 이미 테이블이 있으면 건너뜀 (기존 데이터 삭제 안 함)
    Base.metadata.create_all(bind=engine)
