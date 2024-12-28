from typing import List, Dict

from .base import BaseRetriever, SearchResult
from .bm25 import BM25Retriever
from .vector import VectorRetriever


class CombinedRetriever(BaseRetriever):
    """Combined retriever using Reciprocal Rank Fusion (RRF)."""

    def __init__(self, k0: float = 60.0):
        """
        Initialize combined retriever.

        Args:
            k0: Constant for RRF calculation. Higher values decrease the impact of rank differences.
                Default is 60 as used in many IR systems.
        """
        self.vector_retriever = VectorRetriever()
        self.bm25_retriever = BM25Retriever()
        self.k0 = k0

    def _compute_rrf_score(self, ranks: Dict[str, List[int]]) -> Dict[str, float]:
        """
        Compute RRF scores for documents based on their ranks in different result sets.

        Args:
            ranks: Dictionary mapping doc_id to list of ranks (one per retriever)

        Returns:
            Dict[str, float]: RRF scores for each document
        """
        rrf_scores = {}
        for doc_id, doc_ranks in ranks.items():
            # RRF score = sum(1 / (k0 + r)) for each rank r
            rrf_score = sum(1 / (self.k0 + r) for r in doc_ranks)
            rrf_scores[doc_id] = rrf_score
        return rrf_scores

    async def add_document(self, content: str, metadata: dict) -> None:
        """
        Add a document to both retrievers.

        Args:
            content: Document content
            metadata: Document metadata
        """
        await self.vector_retriever.add_document(content, metadata)
        await self.bm25_retriever.add_document(content, metadata)

    async def search(self, query: str, k: int = 4) -> List[SearchResult]:
        """
        Search using both retrievers and combine results using RRF.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List[SearchResult]: Combined search results
        """
        # Get results from both retrievers
        vector_results = await self.vector_retriever.search(query, k=k * 2)  # Get more results for better fusion
        bm25_results = await self.bm25_retriever.search(query, k=k * 2)

        # Track ranks for each document
        ranks: Dict[str, List[int]] = {}
        content_map: Dict[str, dict] = {}  # Store document content and metadata

        # Process vector results
        for rank, result in enumerate(vector_results):
            doc_id = result["metadata"]["note_id"]
            ranks.setdefault(doc_id, []).append(rank + 1)  # 1-based ranking
            content_map[doc_id] = {"content": result["content"], "metadata": result["metadata"]}

        # Process BM25 results
        for rank, result in enumerate(bm25_results):
            doc_id = result["metadata"]["note_id"]
            ranks.setdefault(doc_id, []).append(rank + 1)  # 1-based ranking
            content_map[doc_id] = {"content": result["content"], "metadata": result["metadata"]}

        # For documents found by only one retriever, assign a penalty rank
        max_rank = max(len(vector_results), len(bm25_results))
        penalty_rank = max_rank + 1
        for doc_id in ranks:
            if len(ranks[doc_id]) == 1:
                ranks[doc_id].append(penalty_rank)

        # Compute RRF scores
        rrf_scores = self._compute_rrf_score(ranks)

        # Create final results
        results = [
            {"content": content_map[doc_id]["content"], "metadata": content_map[doc_id]["metadata"], "score": score}
            for doc_id, score in rrf_scores.items()
        ]

        # Sort by RRF score and take top k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:k]

    async def delete_document(self, doc_id: str) -> None:
        """
        Delete a document from both retrievers.

        Args:
            doc_id: Document ID to delete
        """
        await self.vector_retriever.delete_document(doc_id)
        await self.bm25_retriever.delete_document(doc_id)

    async def reset(self) -> None:
        """Reset both retrievers."""
        await self.vector_retriever.reset()
        await self.bm25_retriever.reset()
