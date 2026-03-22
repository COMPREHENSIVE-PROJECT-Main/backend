# 회원가입 / 로그인 관련 비즈니스 로직
import bcrypt
from sqlalchemy.orm import Session

from app.models.user import User
from app.utils.logger import get_logger

logger = get_logger("auth_service")


def hash_password(password: str) -> str:
    # 평문 비밀번호를 bcrypt로 암호화해서 반환
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # 입력한 비밀번호와 DB의 암호화된 비밀번호가 일치하는지 확인
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def get_user_by_username(db: Session, username: str) -> User | None:
    # username으로 유저 조회 - 없으면 None 반환
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, username: str, password: str) -> User:
    # username 중복 확인
    if get_user_by_username(db, username):
        logger.info(f"회원가입 실패 - 이미 사용 중인 아이디: {username}")
        raise ValueError("이미 사용 중인 아이디입니다")

    # 비밀번호 암호화 후 유저 생성
    user = User(
        username=username,
        hashed_password=hash_password(password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)  # DB에서 최신 상태 다시 읽어옴 (created_at 등 자동 생성 값 반영)

    logger.info(f"회원가입 완료 - username: {username}")
    return user
