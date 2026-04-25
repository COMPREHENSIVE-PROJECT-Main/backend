# 삼각 그래프 / 바 차트용 JSON 데이터 생성
# 프론트가 차트 라이브러리에 바로 넣을 수 있는 형태로 변환

from app.backend.schemas.vis_render_schema import (
    CivilVisData,
    CriminalVisData,
    GapAnalysis,
)


def build_bar_chart_data(vis_data: CriminalVisData | CivilVisData) -> dict:
    """
    바 차트용 데이터 생성

    반환 구조:
    {
        "labels": ["원칙판사", "형평판사", "여론판사"],
        "values": [24.0, 12.0, 18.0],
        "unit": "개월"
    }
    """
    if isinstance(vis_data, CriminalVisData):
        chart = vis_data.sentence_chart
        labels = list(chart.values_by_judge.keys())
        values = list(chart.values_by_judge.values())
        return {"labels": labels, "values": values, "unit": chart.unit}

    # 민사
    chart = vis_data.responsibility_chart
    labels = list(chart.values_by_judge.keys())
    values = list(chart.values_by_judge.values())
    return {"labels": labels, "values": values, "unit": chart.unit}


def build_triangle_chart_data(gap: GapAnalysis) -> dict:
    """
    삼각 그래프용 데이터 생성 (법리 / 형평 / 여론 3축)

    반환 구조:
    {
        "axes": ["원칙", "형평", "여론"],
        "deltas": {
            "principle_equity": 12.0,
            "equity_opinion": -6.0,
            "principle_opinion": 6.0
        },
        "unit": "개월"
    }
    """
    return {
        "axes": ["원칙", "형평", "여론"],
        "deltas": {
            "principle_equity": gap.delta_principle_equity,
            "equity_opinion": gap.delta_equity_opinion,
            "principle_opinion": gap.delta_principle_opinion,
        },
        "unit": gap.unit,
    }


def build_decision_pie_data(vis_data: CriminalVisData | CivilVisData) -> dict:
    """
    파이 차트용 판결 분포 데이터 생성

    형사 반환:
    { "labels": ["유죄", "무죄"], "values": [3, 0] }

    민사 반환:
    { "labels": ["인용", "기각"], "values": [2, 1] }
    """
    if isinstance(vis_data, CriminalVisData):
        dc = vis_data.decision_chart
        return {
            "labels": ["유죄", "무죄"],
            "values": [dc.guilty_count, dc.not_guilty_count],
        }

    dc = vis_data.decision_chart
    return {
        "labels": ["인용", "기각"],
        "values": [dc.upheld_count, dc.dismissed_count],
    }
