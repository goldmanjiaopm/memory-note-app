from typing import Dict, List
import numpy as np
from rank_bm25 import BM25Okapi
from .base import BaseRetriever, SearchResult


class BM25Retriever(BaseRetriever):
    """BM25 retriever implementation."""

    def __init__(self):
        """Initialize BM25 retriever."""
        self.documents: List[str] = []
        self.metadata: List[Dict] = []
        self.bm25: BM25Okapi | None = None

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words."""
        return text.lower().split()

    def _update_index(self) -> None:
        """Update BM25 index."""
        if self.documents:  # Only create index if there are documents
            tokenized_documents = [self._tokenize(doc) for doc in self.documents]
            self.bm25 = BM25Okapi(tokenized_documents)
        else:
            self.bm25 = None

    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """
        Normalize scores to [0, 1] range.

        Args:
            scores: Raw BM25 scores

        Returns:
            np.ndarray: Normalized scores
        """
        if len(scores) == 0:
            return scores

        max_score = np.max(scores)
        if max_score > 0:
            return scores / max_score
        return scores

    async def add_document(self, content: str, metadata: dict) -> None:
        """
        Add a document to the retriever.

        Args:
            content: Document content
            metadata: Document metadata
        """
        self.documents.append(content)
        self.metadata.append(metadata)
        self._update_index()

    async def search(self, query: str, k: int = 4) -> List[SearchResult]:
        """
        Search for documents using BM25.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List[SearchResult]: Search results with scores
        """
        if not self.bm25 or not self.documents:
            return []

        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        scores = self._normalize_scores(scores)

        # Get top k results
        top_k_indices = np.argsort(scores)[-k:][::-1]

        results: List[SearchResult] = []
        for idx in top_k_indices:
            if scores[idx] > 0:  # Only include results with non-zero scores
                results.append(
                    {"content": self.documents[idx], "metadata": self.metadata[idx], "score": float(scores[idx])}
                )

        return results

    async def delete_document(self, doc_id: str) -> None:
        """
        Delete a document from the retriever.

        Args:
            doc_id: Document ID to delete
        """
        # Find document by ID in metadata
        for idx, meta in enumerate(self.metadata):
            if meta.get("note_id") == doc_id:
                self.documents.pop(idx)
                self.metadata.pop(idx)
                self._update_index()
                break

    async def reset(self) -> None:
        """Reset the retriever."""
        self.documents = []
        self.metadata = []
        self.bm25 = None
