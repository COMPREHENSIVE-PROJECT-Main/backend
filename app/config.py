# 환경변수를 불러오고 관리하는 파일
# 서버가 시작될 때 필요한 설정값들이 제대로 있는지 자동으로 확인해줌
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 데이터베이스 연결 정보
    db_host: str
    db_port: int = 5432
    db_user: str
    db_password: str
    db_name: str

    # 레디스 연결 정보 (임시 데이터 저장용)
    redis_url: str = "redis://redis:6379"

    # 크로마DB 연결 정보 (판례 벡터 저장용)
    chroma_host: str = "chromadb"
    chroma_port: int = 8000

    # 올라마 연결 정보 (로컬 AI 모델 실행용)
    ollama_base_url: str = "http://ollama:11434"
    ollama_llm_model: str = "gemma3:4b"
    ollama_embed_model: str = "nomic-embed-text"

    # JWT 설정
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30   # 액세스 토큰 유효기간 (분)
    refresh_token_expire_days: int = 7      # 리프레시 토큰 유효기간 (일)

    @property
    def database_url(self) -> str:
        # SQLAlchemy가 DB에 연결할 때 쓰는 주소 문자열 조합
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


# 앱 전체에서 이 객체 하나를 가져다 씀
settings = Settings()
