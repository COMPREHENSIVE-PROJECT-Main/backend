import unittest
from unittest.mock import patch

from app.ai.models.state import RetrievedDocument, RetrievalCollection
from app.ai.services.retrieval_service import (
    RetrievalError,
    format_rag_context,
    search_chromadb,
)


class _EmptyCollection:
    def query(self, query_texts, n_results):
        return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}


class RetrievalServiceTest(unittest.TestCase):
    def test_search_chromadb_raises_when_no_context(self):
        with patch("app.ai.services.retrieval_service.get_collection", return_value=_EmptyCollection()):
            with self.assertRaises(RetrievalError):
                search_chromadb("사건 설명", "검색 쿼리")

    def test_format_rag_context_includes_source_and_limits_length(self):
        docs = [
            RetrievedDocument(
                doc_id="doc-1",
                collection=RetrievalCollection.CASES,
                title="대법원 판례",
                content="본문" * 500,
            )
        ]

        rendered = format_rag_context(docs, max_docs=1, max_chars=200, per_doc_chars=50)

        self.assertIn("collection=cases", rendered)
        self.assertIn("title=대법원 판례", rendered)
        self.assertLessEqual(len(rendered), 200)


if __name__ == "__main__":
    unittest.main()
