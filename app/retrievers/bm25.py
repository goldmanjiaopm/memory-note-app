from typing import Dict, List
import numpy as np
from rank_bm25 import BM25Okapi

from ..config.ai_config import get_ai_config
from .base import BaseRetriever, SearchResult

ai_config = get_ai_config()


class BM25Retriever(BaseRetriever):
    """BM25 retriever implementation."""

    def __init__(self):
        """Initialize BM25 retriever."""
        self.documents: List[str] = []
        self.metadata: List[Dict] = []
        self.bm25: BM25Okapi | None = None

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text for BM25.

        Args:
            text: Text to tokenize

        Returns:
            List[str]: List of tokens
        """
        return text.lower().split()

    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """
        Normalize BM25 scores to [0, 1] range.

        Args:
            scores: Raw BM25 scores

        Returns:
            np.ndarray: Normalized scores
        """
        if len(scores) == 0 or np.all(scores == 0):
            return scores
        return scores / np.max(scores)

    def _update_index(self) -> None:
        """Update BM25 index with current documents."""
        if self.documents:
            tokenized_docs = [self._tokenize(doc) for doc in self.documents]
            self.bm25 = BM25Okapi(tokenized_docs)
        else:
            self.bm25 = None

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

    async def search(self, query: str, k: int = None) -> List[SearchResult]:
        """
        Search for documents using BM25.

        Args:
            query: Search query
            k: Number of results to return (defaults to config value)

        Returns:
            List[SearchResult]: Search results with scores
        """
        k = k or ai_config.retriever.top_k

        if not self.bm25 or not self.documents:
            return []

        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        scores = self._normalize_scores(scores)

        # Get top k results
        top_k_indices = np.argsort(scores)[-k:][::-1]

        results: List[SearchResult] = []
        for idx in top_k_indices:
            if scores[idx] >= ai_config.retriever.min_score_threshold:
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
