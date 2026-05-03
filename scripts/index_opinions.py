"""
여론 데이터를 ChromaDB opinion 컬렉션에 인덱싱하는 스크립트.

실행 방법 (backend/ 디렉토리에서):
    python scripts/index_opinions.py
    python scripts/index_opinions.py --force   # 기존 컬렉션 덮어쓰기
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai.services.indexing_service import index_opinions_dataset
from app.com.logger import get_logger

logger = get_logger("index_opinions")


def main() -> None:
    parser = argparse.ArgumentParser(description="여론 데이터 ChromaDB 인덱싱")
    parser.add_argument(
        "--force",
        action="store_true",
        help="기존 opinion 컬렉션이 있어도 재인덱싱",
    )
    args = parser.parse_args()

    total = index_opinions_dataset(skip_if_collection_exists=not args.force)
    if total == 0:
        logger.info("인덱싱된 항목 없음 (이미 존재하거나 파일 없음). --force 옵션으로 재인덱싱 가능")
    else:
        logger.info(f"인덱싱 완료: total={total}")


if __name__ == "__main__":
    main()
