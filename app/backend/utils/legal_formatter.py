# 법률 문서 포맷터
# 판결문 텍스트 → 주문 / 이유 / 법령 적용 표준 레이아웃 변환

from app.backend.schemas.verdict_schema import VerdictDocument


def format_verdict_text(verdict: VerdictDocument) -> str:
    """
    VerdictDocument → 법원 표준 텍스트 레이아웃 변환

    출력 형식:
    ────────────────────────────────
    주    문
    ────────────────────────────────
    {order}

    이    유
    ────────────────────────────────
    {rationale}

    결    론
    ────────────────────────────────
    {conclusion}
    """
    separator = "─" * 40

    sections = [
        f"{separator}",
        "주    문",
        f"{separator}",
        verdict.order,
        "",
        f"{separator}",
        "이    유",
        f"{separator}",
        verdict.rationale,
        "",
        f"{separator}",
        "결    론",
        f"{separator}",
        verdict.conclusion,
    ]

    return "\n".join(sections)


def format_verdict_html(verdict: VerdictDocument) -> str:
    """
    VerdictDocument → HTML 레이아웃 변환 (PDF 렌더링용)
    Phase 5 리포트 생성 시 사용
    """
    return f"""
<div class="verdict-document">
    <section class="verdict-order">
        <h2>주 문</h2>
        <p>{verdict.order}</p>
    </section>
    <section class="verdict-rationale">
        <h2>이 유</h2>
        <p>{verdict.rationale}</p>
    </section>
    <section class="verdict-conclusion">
        <h2>결 론</h2>
        <p>{verdict.conclusion}</p>
    </section>
</div>
"""
