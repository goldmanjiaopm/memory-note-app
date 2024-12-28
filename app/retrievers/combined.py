from typing import List

from .base import BaseRetriever, SearchResult
from .bm25 import BM25Retriever
from .vector import VectorRetriever


class CombinedRetriever(BaseRetriever):
    """Combined retriever using both BM25 and vector search."""

    def __init__(self, vector_weight: float = 0.5):
        """
        Initialize combined retriever.

        Args:
            vector_weight: Weight for vector search scores (0 to 1).
                         BM25 weight will be (1 - vector_weight).
        """
        self.vector_retriever = VectorRetriever()
        self.bm25_retriever = BM25Retriever()
        self.vector_weight = vector_weight
        self.bm25_weight = 1.0 - vector_weight

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
        Search using both retrievers and combine results.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List[SearchResult]: Combined search results
        """
        # Get results from both retrievers
        vector_results = await self.vector_retriever.search(query, k=k)
        bm25_results = await self.bm25_retriever.search(query, k=k)

        # Create a map of document ID to combined result
        combined_results: dict[str, dict] = {}

        # Process vector results
        for result in vector_results:
            doc_id = result["metadata"]["note_id"]
            combined_results[doc_id] = {
                "content": result["content"],
                "metadata": result["metadata"],
                "vector_score": result["score"],
                "bm25_score": 0.0,
            }

        # Process BM25 results
        for result in bm25_results:
            doc_id = result["metadata"]["note_id"]
            if doc_id in combined_results:
                combined_results[doc_id]["bm25_score"] = result["score"]
            else:
                combined_results[doc_id] = {
                    "content": result["content"],
                    "metadata": result["metadata"],
                    "vector_score": 0.0,
                    "bm25_score": result["score"],
                }

        # Calculate combined scores
        results = []
        for doc_data in combined_results.values():
            combined_score = self.vector_weight * doc_data["vector_score"] + self.bm25_weight * doc_data["bm25_score"]
            results.append(
                {
                    "content": doc_data["content"],
                    "metadata": doc_data["metadata"],
                    "score": round(combined_score, 4),
                }
            )

        # Sort by combined score and take top k
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
