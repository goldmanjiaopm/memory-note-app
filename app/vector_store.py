from typing import Dict, List
from uuid import UUID

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

from .config import get_settings
from .models import Note

settings = get_settings()


class VectorStore:
    """Service for managing document embeddings and similarity search using Chroma."""

    def __init__(self):
        """Initialize vector store with HuggingFace embeddings."""
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
        )
        self.store = Chroma(
            collection_name="notes",
            embedding_function=self.embeddings,
            persist_directory=str(settings.VECTOR_STORE_DIR),
        )
        self.weights = {
            "cosine": 0.7,  # Higher weight: Better for semantic similarity
            "l2": 0.3,  # Lower weight: Good for finding near-exact matches
        }

    def _normalize_score(self, score: float, metric: str) -> float:
        """Normalize similarity score based on metric type."""
        if metric == "cosine":
            return (1 + score) / 2
        else:  # l2
            return max(0, 1 - (score / 10))

    async def add_note(self, note: Note) -> None:
        """Add a note to the vector store."""
        metadata = {"note_id": str(note.id), "title": note.title}
        self.store.add_texts(texts=[note.content], metadatas=[metadata], ids=[str(note.id)])
        self.store.persist()

    async def search_similar(self, query: str, k: int = 4) -> List[dict]:
        """Search for similar notes using weighted average of different metrics."""
        all_results = {}

        # Search with both metrics
        for metric in ["cosine", "l2"]:
            results = self.store.similarity_search_with_score(
                query=query,
                k=k * 2,
                distance_metric=metric,
            )
            for doc, score in results:
                note_id = doc.metadata["note_id"]
                normalized_score = self._normalize_score(score, metric)

                if note_id not in all_results:
                    all_results[note_id] = {
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "weighted_score": 0,
                        "scores": {},
                    }

                all_results[note_id]["scores"][metric] = normalized_score
                all_results[note_id]["weighted_score"] += normalized_score * self.weights[metric]

        sorted_results = sorted(all_results.values(), key=lambda x: x["weighted_score"], reverse=True)[:k]

        return [
            {
                "content": r["content"],
                "metadata": r["metadata"],
                "score": round(r["weighted_score"], 3),
                "individual_scores": r["scores"],
            }
            for r in sorted_results
        ]

    async def delete_note(self, note_id: UUID) -> None:
        """Delete a note from the vector store."""
        self.store.delete(ids=[str(note_id)])
        self.store.persist()
