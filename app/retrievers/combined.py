from typing import List, Dict

from .base import BaseRetriever, SearchResult
from .bm25 import BM25Retriever
from .vector import VectorRetriever
from ..config.ai_config import get_ai_config, CombinationMethod

ai_config = get_ai_config()


class CombinedRetriever(BaseRetriever):
    """Combined retriever using either RRF or weighted average."""

    def __init__(self, k0: float = None):
        """
        Initialize combined retriever.

        Args:
            k0: Optional override for RRF k0 constant
        """
        self.vector_retriever = VectorRetriever()
        self.bm25_retriever = BM25Retriever()
        self.k0 = k0 or ai_config.retriever.rrf_k0

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

    def _compute_weighted_score(self, vector_results: List[dict], bm25_results: List[dict]) -> Dict[str, float]:
        """
        Compute weighted average scores for documents.

        Args:
            vector_results: Results from vector retriever
            bm25_results: Results from BM25 retriever

        Returns:
            Dict[str, float]: Weighted scores for each document
        """
        weighted_scores = {}
        vector_weight = ai_config.retriever.vector_weight
        bm25_weight = ai_config.retriever.bm25_weight
        total_weight = vector_weight + bm25_weight

        if total_weight <= 0:
            raise ValueError("Total weight must be greater than 0")

        # Normalize weights to sum to 1
        vector_weight = vector_weight / total_weight
        bm25_weight = bm25_weight / total_weight

        # Process vector results
        for result in vector_results:
            doc_id = result["metadata"]["note_id"]
            weighted_scores[doc_id] = result["score"] * vector_weight

        # Process BM25 results
        for result in bm25_results:
            doc_id = result["metadata"]["note_id"]
            if doc_id in weighted_scores:
                weighted_scores[doc_id] += result["score"] * bm25_weight
            else:
                weighted_scores[doc_id] = result["score"] * bm25_weight

        return weighted_scores

    async def add_document(self, content: str, metadata: dict) -> None:
        """
        Add a document to both retrievers.

        Args:
            content: Document content
            metadata: Document metadata
        """
        await self.vector_retriever.add_document(content, metadata)
        await self.bm25_retriever.add_document(content, metadata)

    async def search(self, query: str, k: int = None) -> List[SearchResult]:
        """
        Search using both retrievers and combine results.

        Args:
            query: Search query
            k: Number of results to return (defaults to config value)

        Returns:
            List[SearchResult]: Combined search results
        """
        k = k or ai_config.retriever.top_k
        search_k = k * 2  # Get more results for better fusion

        # Get results from both retrievers
        vector_results = await self.vector_retriever.search(query, k=search_k)
        bm25_results = await self.bm25_retriever.search(query, k=search_k)

        # Choose combination method
        if ai_config.retriever.combination_method == CombinationMethod.RRF:
            # Track ranks for each document
            ranks: Dict[str, List[int]] = {}
            content_map: Dict[str, dict] = {}

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

            # Compute scores
            scores = self._compute_rrf_score(ranks)
            doc_info = content_map

        else:  # Weighted average
            scores = self._compute_weighted_score(vector_results, bm25_results)
            # Create content map
            doc_info = {}
            for result in vector_results + bm25_results:
                doc_id = result["metadata"]["note_id"]
                if doc_id not in doc_info:
                    doc_info[doc_id] = {"content": result["content"], "metadata": result["metadata"]}

        # Create final results
        results = [
            {"content": doc_info[doc_id]["content"], "metadata": doc_info[doc_id]["metadata"], "score": score}
            for doc_id, score in scores.items()
            if score >= ai_config.retriever.min_score_threshold
        ]

        # Sort by score and take top k
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
