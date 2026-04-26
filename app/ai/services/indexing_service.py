from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from app.ai.db.vector_db import get_collection
from app.ai.utils.text_splitter import split_text
from app.com.logger import get_logger

logger = get_logger(__name__)

_CASE_TYPE_BY_DIRECTORY = {
    "administration": "administrative",
    "civil": "civil",
    "detective": "criminal",
}
_DATASET_ROOT = Path(__file__).resolve().parents[2] / "dataset"
_CASE_LAW_DATASET_ROOT = _DATASET_ROOT / "case_law"
_STATUTES_DATASET_ROOT = _DATASET_ROOT / "statutes"
_SENTENCING_DATASET_ROOT = _DATASET_ROOT / "sentencing_guidelines"


def _format_progress(file_index: int, discovered_files: int) -> str:
    if discovered_files <= 0:
        return f"{file_index}/{discovered_files}"
    progress_percent = (file_index / discovered_files) * 100
    return f"{file_index}/{discovered_files} ({progress_percent:.1f}%)"


def _normalize_scalar(value: Any) -> str | int | float | bool | None:
    if isinstance(value, (str, int, float, bool)):
        return value
    if value is None:
        return None
    if isinstance(value, list):
        return ",".join(map(str, value))
    return str(value)


def _clean_metadata(metadata: dict[str, Any] | None) -> dict[str, str | int | float | bool]:
    cleaned: dict[str, str | int | float | bool] = {}
    for key, value in (metadata or {}).items():
        normalized = _normalize_scalar(value)
        if normalized is None:
            continue
        cleaned[key] = normalized
    return cleaned


def _resolve_case_type(file_path: str | Path) -> dict[str, str]:
    path = Path(file_path)
    for part in path.parts:
        if part in _CASE_TYPE_BY_DIRECTORY:
            return {
                "case_type": _CASE_TYPE_BY_DIRECTORY[part],
            }
    return {}


def _base_case_metadata(
    case_data: dict[str, Any],
    file_path: str | Path,
) -> dict[str, str | int | float | bool]:
    info = case_data.get("info", {})

    return _clean_metadata(
        {
            **_resolve_case_type(file_path),
            "case_name": info.get("caseNm"),
            "court_name": info.get("courtNm"),
            "judgment_date": info.get("judmnAdjuDe"),
            "case_no": info.get("caseNo"),
            "related_laws": info.get("relateLaword", []),
            "quoted_precedents": info.get("qotatPrcdnt", []),
        }
    )


def _case_document_id(case_data: dict[str, Any], file_path: str | Path) -> str:
    info = case_data.get("info", {})
    case_no = str(info.get("caseNo") or "").strip()
    if case_no:
        return case_no
    return Path(file_path).stem


def _build_section_records(
    case_id: str,
    entries: list[str],
    base_metadata: dict[str, str | int | float | bool],
    section: str,
    chunk_size: int,
    overlap: int,
    subsection: str | None = None,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    section_key = f"{section}:{subsection}" if subsection else section

    for entry_index, entry in enumerate(entries):
        if not isinstance(entry, str) or not entry.strip():
            continue

        entry_metadata = dict(base_metadata)
        entry_metadata["section"] = section
        if subsection:
            entry_metadata["subsection"] = subsection

        chunks = split_text(entry, chunk_size=chunk_size, overlap=overlap)
        for chunk_index, chunk in enumerate(chunks):
            chunk_metadata = dict(entry_metadata)
            chunk_metadata["chunk_index"] = chunk_index
            records.append(
                {
                    "id": f"{case_id}:{section_key}:{entry_index}:{chunk_index}",
                    "document": chunk,
                    "metadata": chunk_metadata,
                }
            )

    return records


def _build_text_records(
    document_id: str,
    texts: list[str],
    base_metadata: dict[str, str | int | float | bool],
    section: str,
    chunk_size: int,
    overlap: int,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    for entry_index, text in enumerate(texts):
        if not isinstance(text, str) or not text.strip():
            continue

        entry_metadata = dict(base_metadata)
        entry_metadata["section"] = section

        chunks = split_text(text, chunk_size=chunk_size, overlap=overlap)
        for chunk_index, chunk in enumerate(chunks):
            chunk_metadata = dict(entry_metadata)
            chunk_metadata["chunk_index"] = chunk_index
            records.append(
                {
                    "id": f"{document_id}:{section}:{entry_index}:{chunk_index}",
                    "document": chunk,
                    "metadata": chunk_metadata,
                }
            )

    return records


def _prepare_case_law_records(
    case_data: dict[str, Any],
    file_path: str | Path,
    chunk_size: int = 800,
    overlap: int = 150,
) -> list[dict[str, Any]]:
    case_id = _case_document_id(case_data, file_path)
    base_metadata = _base_case_metadata(case_data, file_path)
    records: list[dict[str, Any]] = []

    summary_parts = [
        f"사건명: {case_data.get('info', {}).get('caseNm', '')}",
        f"법원: {case_data.get('info', {}).get('courtNm', '')}",
        f"선고일: {case_data.get('info', {}).get('judmnAdjuDe', '')}",
        f"사건번호: {case_data.get('info', {}).get('caseNo', '')}",
    ]
    summary_text = "\n".join(part for part in summary_parts if part.split(": ", 1)[-1])
    if summary_text:
        summary_metadata = dict(base_metadata)
        summary_metadata["section"] = "summary"
        records.append(
            {
                "id": f"{case_id}:summary:0:0",
                "document": summary_text,
                "metadata": summary_metadata,
            }
        )

    records.extend(
        _build_section_records(
            case_id=case_id,
            entries=case_data.get("facts", {}).get("bsisFacts", []),
            base_metadata=base_metadata,
            section="facts",
            chunk_size=chunk_size,
            overlap=overlap,
        )
    )
    records.extend(
        _build_section_records(
            case_id=case_id,
            entries=case_data.get("assrs", {}).get("acusrAssrs", []),
            base_metadata=base_metadata,
            section="assrs",
            subsection="acusr",
            chunk_size=chunk_size,
            overlap=overlap,
        )
    )
    records.extend(
        _build_section_records(
            case_id=case_id,
            entries=case_data.get("assrs", {}).get("dedatAssrs", []),
            base_metadata=base_metadata,
            section="assrs",
            subsection="dedat",
            chunk_size=chunk_size,
            overlap=overlap,
        )
    )
    records.extend(
        _build_section_records(
            case_id=case_id,
            entries=case_data.get("dcss", {}).get("courtDcss", []),
            base_metadata=base_metadata,
            section="court_dcss",
            chunk_size=chunk_size,
            overlap=overlap,
        )
    )
    records.extend(
        _build_section_records(
            case_id=case_id,
            entries=case_data.get("mentionedItems", {}).get("rqestObjet", []),
            base_metadata=base_metadata,
            section="request_object",
            chunk_size=chunk_size,
            overlap=overlap,
        )
    )
    records.extend(
        _build_section_records(
            case_id=case_id,
            entries=case_data.get("disposal", {}).get("disposalcontent", []),
            base_metadata=base_metadata,
            section="disposal",
            chunk_size=chunk_size,
            overlap=overlap,
        )
    )
    records.extend(
        _build_section_records(
            case_id=case_id,
            entries=case_data.get("close", {}).get("cnclsns", []),
            base_metadata=base_metadata,
            section="close",
            chunk_size=chunk_size,
            overlap=overlap,
        )
    )
    return records


def _iter_case_law_files() -> list[Path]:
    return sorted(_CASE_LAW_DATASET_ROOT.rglob("*.json"))


def _iter_statutes_files() -> list[Path]:
    return sorted(_STATUTES_DATASET_ROOT.rglob("*.json"))


def _iter_sentencing_files() -> list[Path]:
    return sorted(_SENTENCING_DATASET_ROOT.rglob("*.json"))


def _prepare_statute_records(
    statute_items: list[dict[str, Any]],
    file_path: str | Path,
    chunk_size: int = 800,
    overlap: int = 150,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    file_stem = Path(file_path).stem

    for item_index, item in enumerate(statute_items):
        if not isinstance(item, dict):
            continue

        law_name = str(item.get("law_name") or "").strip()
        article_number = str(item.get("article_number") or "").strip()
        article_title = str(item.get("article_title") or "").strip()
        article_content = str(item.get("article_content") or "").strip()
        if not article_content:
            continue

        document_id = ":".join(
            part
            for part in [file_stem, str(item_index), law_name or None, article_number or None]
            if part
        )
        base_metadata = _clean_metadata(
            {
                "source_type": "statute",
                "law_name": law_name,
                "article_number": article_number,
                "article_title": article_title,
                "category": item.get("category"),
                "effective_date": item.get("effective_date"),
                "source_url": item.get("source_url"),
            }
        )
        text = "\n".join(
            part
            for part in [
                f"법률명: {law_name}" if law_name else "",
                f"조문번호: {article_number}" if article_number else "",
                f"조문제목: {article_title}" if article_title else "",
                f"조문내용: {article_content}",
            ]
            if part
        )
        records.extend(
            _build_text_records(
                document_id=document_id,
                texts=[text],
                base_metadata=base_metadata,
                section="article",
                chunk_size=chunk_size,
                overlap=overlap,
            )
        )

    return records


def _prepare_sentencing_records(
    sentencing_items: list[dict[str, Any]],
    file_path: str | Path,
    chunk_size: int = 800,
    overlap: int = 150,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    file_stem = Path(file_path).stem

    for item_index, item in enumerate(sentencing_items):
        if not isinstance(item, dict):
            continue

        crime_type = str(item.get("crime_type") or "").strip()
        sub_type = str(item.get("sub_type") or "").strip()
        sentencing_type = str(item.get("sentencing_type") or "").strip()
        if not any([crime_type, sub_type, sentencing_type]):
            continue

        document_id = ":".join(
            part
            for part in [file_stem, str(item_index), sub_type or None, sentencing_type or None]
            if part
        )
        base_metadata = _clean_metadata(
            {
                "source_type": "sentencing_guideline",
                "crime_type": crime_type,
                "sub_type": sub_type,
                "sentencing_type": sentencing_type,
                "sentencing_min": item.get("sentencing_min"),
                "sentencing_max": item.get("sentencing_max"),
                "source_url": item.get("source_url"),
            }
        )
        text = "\n".join(
            part
            for part in [
                f"범죄유형: {crime_type}" if crime_type else "",
                f"세부유형: {sub_type}" if sub_type else "",
                f"양형유형: {sentencing_type}" if sentencing_type else "",
                f"하한: {item.get('sentencing_min')}" if item.get("sentencing_min") else "",
                f"상한: {item.get('sentencing_max')}" if item.get("sentencing_max") else "",
                f"가중요소: {item.get('aggravating')}" if item.get("aggravating") else "",
                f"감경요소: {item.get('mitigating')}" if item.get("mitigating") else "",
                f"집행유예기준: {item.get('probation_criteria')}" if item.get("probation_criteria") else "",
            ]
            if part
        )
        records.extend(
            _build_text_records(
                document_id=document_id,
                texts=[text],
                base_metadata=base_metadata,
                section="guideline",
                chunk_size=chunk_size,
                overlap=overlap,
            )
        )

    return records


def _display_dataset_path(path: Path, dataset_root: Path) -> str:
    try:
        return str(path.relative_to(dataset_root))
    except ValueError:
        return str(path)


def _upsert_records(
    collection: Any,
    records: list[dict[str, Any]],
    batch_size: int,
) -> int:
    indexed_count = 0
    for start in range(0, len(records), batch_size):
        batch = records[start:start + batch_size]
        collection.upsert(
            ids=[record["id"] for record in batch],
            documents=[record["document"] for record in batch],
            metadatas=[_clean_metadata(record["metadata"]) for record in batch],
        )
        indexed_count += len(batch)
    return indexed_count


async def _index_json_dataset(
    dataset_root: Path,
    collection_name: str,
    batch_size: int,
    chunk_size: int,
    overlap: int,
    skip_if_collection_exists: bool,
    dataset_label: str,
    missing_message: str,
    invalid_message: str,
    recordless_message: str,
    loader: Callable[[], list[Path]],
    record_preparer: Callable[..., list[dict[str, Any]]],
) -> int:
    collection = get_collection(collection_name)

    if skip_if_collection_exists and collection.count() > 0:
        logger.info(
            "컬렉션에 데이터가 이미 존재해 인덱싱 건너뜀: "
            f"collection={collection_name}, root={dataset_root}"
        )
        return 0

    dataset_files = loader()
    if not dataset_files:
        logger.warning(f"{missing_message}: root={dataset_root}")
        return 0

    logger.info(
        f"{dataset_label} 데이터셋 인덱싱 시작: "
        f"root={dataset_root}, collection={collection_name}, files={len(dataset_files)}, "
        f"batch_size={batch_size}, chunk_size={chunk_size}, overlap={overlap}"
    )

    discovered_files = len(dataset_files)
    successful_files = 0
    skipped_files = 0
    failed_files = 0
    total_indexed = 0
    for file_index, path in enumerate(dataset_files, start=1):
        display_path = _display_dataset_path(path, dataset_root)
        logger.info(
            f"{dataset_label} JSON 인덱싱 시작: "
            f"file={display_path}, progress={_format_progress(file_index, discovered_files)}"
        )

        try:
            with path.open("r", encoding="utf-8") as fp:
                data = json.load(fp)
        except Exception as exc:
            failed_files += 1
            logger.exception(f"{dataset_label} JSON 로드 실패: file={display_path}, error={exc}")
            continue

        if not isinstance(data, list):
            skipped_files += 1
            logger.warning(f"{invalid_message}: file={display_path}")
            continue

        records = record_preparer(
            data,
            file_path=path,
            chunk_size=chunk_size,
            overlap=overlap,
        )
        if not records:
            skipped_files += 1
            logger.warning(f"{recordless_message}: file={display_path}")
            continue

        total_indexed += _upsert_records(collection, records, batch_size)
        successful_files += 1
        logger.info(
            f"{dataset_label} JSON 인덱싱 완료: "
            f"file={display_path}, indexed_chunks={len(records)}, "
            f"successful_files={successful_files}, total_indexed_chunks={total_indexed}\n"
        )

    logger.info(
        f"{dataset_label} 데이터셋 인덱싱 종료: "
        f"root={dataset_root}, collection={collection_name}, discovered_files={discovered_files}, "
        f"successful_files={successful_files}, skipped_files={skipped_files}, "
        f"failed_files={failed_files}, total_indexed_chunks={total_indexed}"
    )
    return total_indexed


async def index_case_law_dataset(
    collection_name: str = "cases",
    batch_size: int = 100,
    chunk_size: int = 800,
    overlap: int = 150,
    skip_if_collection_exists: bool = False,
) -> int:
    collection = get_collection(collection_name)

    if skip_if_collection_exists and collection.count() > 0:
        logger.info(
            "컬렉션에 데이터가 이미 존재해 인덱싱 건너뜀: "
            f"collection={collection_name}, root={_CASE_LAW_DATASET_ROOT}"
        )
        return 0

    dataset_files = _iter_case_law_files()
    if not dataset_files:
        logger.warning(f"인덱싱할 판례 JSON 파일이 없음: root={_CASE_LAW_DATASET_ROOT}")
        return 0

    logger.info(
        "판례 데이터셋 인덱싱 시작: "
        f"root={_CASE_LAW_DATASET_ROOT}, collection={collection_name}, files={len(dataset_files)}, "
        f"batch_size={batch_size}, chunk_size={chunk_size}, overlap={overlap}"
    )

    discovered_files = len(dataset_files)
    successful_files = 0
    skipped_files = 0
    failed_files = 0
    total_indexed = 0
    for file_index, path in enumerate(dataset_files, start=1):
        display_path = _display_dataset_path(path, _CASE_LAW_DATASET_ROOT)
        logger.info(
            "판례 JSON 인덱싱 시작: "
            f"file={display_path}, progress={_format_progress(file_index, discovered_files)}"
        )

        try:
            with path.open("r", encoding="utf-8") as fp:
                case_data = json.load(fp)
        except Exception as exc:
            failed_files += 1
            logger.exception(f"판례 JSON 로드 실패: file={display_path}, error={exc}")
            continue

        if not isinstance(case_data, dict):
            skipped_files += 1
            logger.warning(f"case_law JSON 형식이 아님: file={display_path}")
            continue

        if not isinstance(case_data.get("info"), dict):
            skipped_files += 1
            logger.warning(f"case_law JSON에 info 객체가 없음: file={display_path}")
            continue

        records = _prepare_case_law_records(
            case_data=case_data,
            file_path=path,
            chunk_size=chunk_size,
            overlap=overlap,
        )
        if not records:
            skipped_files += 1
            logger.warning(f"인덱싱할 판례 레코드가 없음: file={display_path}")
            continue

        total_indexed += _upsert_records(collection, records, batch_size)
        successful_files += 1
        logger.info(
            "판례 JSON 인덱싱 완료: "
            f"file={display_path}, indexed_chunks={len(records)}, "
            f"successful_files={successful_files}, total_indexed_chunks={total_indexed}\n"
        )

    logger.info(
        "판례 데이터셋 인덱싱 종료: "
        f"root={_CASE_LAW_DATASET_ROOT}, collection={collection_name}, discovered_files={discovered_files}, "
        f"successful_files={successful_files}, skipped_files={skipped_files}, "
        f"failed_files={failed_files}, total_indexed_chunks={total_indexed}"
    )
    return total_indexed


async def index_statutes_dataset(
    collection_name: str = "statutes",
    batch_size: int = 100,
    chunk_size: int = 800,
    overlap: int = 150,
    skip_if_collection_exists: bool = False,
) -> int:
    return await _index_json_dataset(
        dataset_root=_STATUTES_DATASET_ROOT,
        collection_name=collection_name,
        batch_size=batch_size,
        chunk_size=chunk_size,
        overlap=overlap,
        skip_if_collection_exists=skip_if_collection_exists,
        dataset_label="법조문",
        missing_message="인덱싱할 법조문 JSON 파일이 없음",
        invalid_message="statutes JSON 형식이 아님",
        recordless_message="인덱싱할 법조문 레코드가 없음",
        loader=_iter_statutes_files,
        record_preparer=_prepare_statute_records,
    )


async def index_sentencing_dataset(
    collection_name: str = "sentencing",
    batch_size: int = 100,
    chunk_size: int = 800,
    overlap: int = 150,
    skip_if_collection_exists: bool = False,
) -> int:
    return await _index_json_dataset(
        dataset_root=_SENTENCING_DATASET_ROOT,
        collection_name=collection_name,
        batch_size=batch_size,
        chunk_size=chunk_size,
        overlap=overlap,
        skip_if_collection_exists=skip_if_collection_exists,
        dataset_label="양형기준",
        missing_message="인덱싱할 양형기준 JSON 파일이 없음",
        invalid_message="sentencing_guidelines JSON 형식이 아님",
        recordless_message="인덱싱할 양형기준 레코드가 없음",
        loader=_iter_sentencing_files,
        record_preparer=_prepare_sentencing_records,
    )
