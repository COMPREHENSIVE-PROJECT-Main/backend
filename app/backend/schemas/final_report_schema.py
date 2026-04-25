# 종합 리포트 API 입출력 규격
from pydantic import BaseModel

from app.backend.schemas.vis_render_schema import GapAnalysis
from app.backend.schemas.summary_schema import RoundSummary


class CaseInfo(BaseModel):
    case_id: str
    case_type: str          # "형사" | "민사"
    case_description: str   # 원본 사건 설명
    created_at: str         # 사건 생성 일시


class VerdictInfo(BaseModel):
    sentence: str       # 선고 내용
    rationale: str      # 이유
    conclusion: str     # 결론 (200자 이내)
    decision: str       # "유죄" | "무죄" | "인용" | "기각"
    value: str          # 형량 또는 책임비율


class JudgeInfo(BaseModel):
    judge_type: str     # "원칙판사" | "형평판사" | "여론판사"
    decision: str
    value: str


class JudgeComparison(BaseModel):
    judges: list[JudgeInfo]
    gap: GapAnalysis


class ChartData(BaseModel):
    # 원그래프: 형사 = 유죄/무죄 정수 / 민사 = 인용/기각 정수
    decision_pie: dict
    # 막대그래프: 판사별 형량(소숫점 1자리, 단위: 개월|원|%)
    bar_chart: dict
    # 삼각형 그래프: 판사 간 차이(소숫점 1자리, 단위 동일)
    triangle_chart: dict


class DebateSummarySection(BaseModel):
    rounds: list[RoundSummary]
    key_issues: list[str]   # 핵심 쟁점 3~5개


class FinalReport(BaseModel):
    case_info: CaseInfo
    verdict: VerdictInfo
    judge_comparison: JudgeComparison
    charts: ChartData
    summary: DebateSummarySection


class ExportResponse(BaseModel):
    case_id: str
    report: FinalReport
    # 법원 표준 양식 텍스트 (주문/이유/결론 구분선 포함)
    verdict_text: str
    # PDF 다운로드 URL — HTML 템플릿 수령 후 실제 경로로 교체
    download_url: str | None = None
