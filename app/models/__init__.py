# 모델 파일들을 한곳에서 불러오는 파일
# 여기서 import 해야 create_tables()가 어떤 테이블을 만들지 알 수 있음
from app.models.case import Case

__all__ = ["Case"]
