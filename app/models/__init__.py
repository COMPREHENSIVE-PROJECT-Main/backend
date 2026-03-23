# 모델 파일들을 한곳에서 불러오는 파일
# 여기서 import 해야 create_tables()가 어떤 테이블을 만들지 알 수 있음
from app.models.cases import Cases
from app.models.cases_raw import CasesRaw
from app.models.sentencing import Sentencing
from app.models.statutes import Statutes
from app.models.user import User
from app.models.user_case import UserCase

__all__ = ["Cases", "CasesRaw", "Sentencing", "Statutes", "User", "UserCase"]
