from __future__ import annotations

import asyncio
import argparse
import json
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from app.ai.core import initialize_runtime
from app.ai.db.vector_db import get_collection
from app.ai.services import (
    index_case_law_dataset,
    index_sentencing_dataset,
    index_statutes_dataset,
)

if TYPE_CHECKING:
    from app.ai.models import TrialState


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CLI entrypoint for AI trial state bootstrap.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Path to a JSON file containing an existing TrialState payload.",
    )
    parser.add_argument(
        "--index-case-law",
        action="store_true",
        help="Index all case law JSON files under app/dataset/case_law into ChromaDB.",
    )
    parser.add_argument(
        "--index-statutes",
        action="store_true",
        help="Index all statutes JSON files under app/dataset/statutes into ChromaDB.",
    )
    parser.add_argument(
        "--index-sentencing",
        action="store_true",
        help="Index all sentencing guideline JSON files under app/dataset/sentencing_guidelines into ChromaDB.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Index case law, statutes, and sentencing datasets in parallel.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the resulting TrialState JSON.",
    )
    parser.add_argument(
        "--init-runtime",
        action="store_true",
        help="Initialize Redis, vector collections, and model runtime before continuing.",
    )
    parser.add_argument(
        "--case-id",
        help="Case identifier used when creating a new TrialState.",
    )
    parser.add_argument(
        "--case-type",
        default="unknown",
        choices=["unknown", "criminal", "civil"],
        help="Case type for a new TrialState.",
    )
    parser.add_argument(
        "--case-summary",
        default="",
        help="Case summary for a new TrialState.",
    )
    parser.add_argument(
        "--fact",
        action="append",
        default=[],
        help="Repeatable fact entry for a new TrialState.",
    )
    parser.add_argument(
        "--round-limit",
        type=int,
        default=3,
        help="Maximum number of argument rounds for a new TrialState.",
    )
    parser.add_argument(
        "--collection-name",
        default="cases",
        help="Chroma collection name used for indexing.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size used for case law indexing.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=800,
        help="Chunk size used for case law indexing.",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=150,
        help="Chunk overlap used for case law indexing.",
    )
    parser.add_argument(
        "--skip-if-collection-exists",
        action="store_true",
        help="Skip indexing when the target collection already contains data.",
    )
    return parser


def load_state(args: argparse.Namespace) -> "TrialState":
    from app.ai.models import TrialState

    if args.input:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        return TrialState.model_validate(payload)

    if not args.case_id:
        raise SystemExit("--case-id is required when --input is not provided")

    return TrialState(
        case_id=args.case_id,
        case_type=args.case_type,
        case_summary=args.case_summary,
        facts=args.fact,
        round_limit=args.round_limit,
    )


def emit_state(state: "TrialState", output_path: Optional[Path]) -> None:
    rendered = json.dumps(state.model_dump(mode="json"), ensure_ascii=False, indent=2)
    if output_path:
        output_path.write_text(rendered + "\n", encoding="utf-8")
        return
    print(rendered)


async def run_case_law_indexing(args: argparse.Namespace) -> None:
    indexed_count = await index_case_law_dataset(
        collection_name=args.collection_name,
        batch_size=args.batch_size,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        skip_if_collection_exists=args.skip_if_collection_exists,
    )
    print(
        json.dumps(
            {
                "indexed_root": "app/dataset/case_law",
                "collection_name": args.collection_name,
                "indexed_chunks": indexed_count,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


async def run_statutes_indexing(args: argparse.Namespace) -> None:
    indexed_count = await index_statutes_dataset(
        collection_name=args.collection_name,
        batch_size=args.batch_size,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        skip_if_collection_exists=args.skip_if_collection_exists,
    )
    print(
        json.dumps(
            {
                "indexed_root": "app/dataset/statutes",
                "collection_name": args.collection_name,
                "indexed_chunks": indexed_count,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


async def run_sentencing_indexing(args: argparse.Namespace) -> None:
    indexed_count = await index_sentencing_dataset(
        collection_name=args.collection_name,
        batch_size=args.batch_size,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        skip_if_collection_exists=args.skip_if_collection_exists,
    )
    print(
        json.dumps(
            {
                "indexed_root": "app/dataset/sentencing_guidelines",
                "collection_name": args.collection_name,
                "indexed_chunks": indexed_count,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _run_async_indexer(indexer, **kwargs) -> int:
    return asyncio.run(indexer(**kwargs))


def _prepare_all_collections() -> None:
    for collection_name in ("cases", "statutes", "sentencing"):
        get_collection(collection_name)


async def run_all_indexing(args: argparse.Namespace) -> None:
    common_kwargs = {
        "batch_size": args.batch_size,
        "chunk_size": args.chunk_size,
        "overlap": args.overlap,
        "skip_if_collection_exists": args.skip_if_collection_exists,
    }
    _prepare_all_collections()
    results = await asyncio.gather(
        asyncio.to_thread(
            _run_async_indexer,
            index_case_law_dataset,
            collection_name="cases",
            **common_kwargs,
        ),
        asyncio.to_thread(
            _run_async_indexer,
            index_statutes_dataset,
            collection_name="statutes",
            **common_kwargs,
        ),
        asyncio.to_thread(
            _run_async_indexer,
            index_sentencing_dataset,
            collection_name="sentencing",
            **common_kwargs,
        ),
    )
    print(
        json.dumps(
            {
                "all": True,
                "results": [
                    {
                        "indexed_root": "app/dataset/case_law",
                        "collection_name": "cases",
                        "indexed_chunks": results[0],
                    },
                    {
                        "indexed_root": "app/dataset/statutes",
                        "collection_name": "statutes",
                        "indexed_chunks": results[1],
                    },
                    {
                        "indexed_root": "app/dataset/sentencing_guidelines",
                        "collection_name": "sentencing",
                        "indexed_chunks": results[2],
                    },
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.init_runtime:
        asyncio.run(initialize_runtime())
    if args.all:
        asyncio.run(run_all_indexing(args))
        return
    if args.index_case_law:
        asyncio.run(run_case_law_indexing(args))
        return
    if args.index_statutes:
        asyncio.run(run_statutes_indexing(args))
        return
    if args.index_sentencing:
        asyncio.run(run_sentencing_indexing(args))
        return
    state = load_state(args)
    emit_state(state, args.output)


if __name__ == "__main__":
    main()
