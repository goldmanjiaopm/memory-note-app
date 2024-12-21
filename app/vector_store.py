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

    async def add_note(self, note: Note) -> None:
        """Add a note to the vector store."""
        metadata = {"note_id": str(note.id), "title": note.title}
        self.store.add_texts(texts=[note.content], metadatas=[metadata], ids=[str(note.id)])
        self.store.persist()

    async def search_similar(self, query: str, k: int = 4) -> List[dict]:
        """Search for similar notes."""
        results = self.store.similarity_search_with_score(query=query, k=k)

        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": round((1 - score), 3),  # Convert distance to similarity score
            }
            for doc, score in results
        ]

    async def delete_note(self, note_id: UUID) -> None:
        """Delete a note from the vector store."""
        self.store.delete(ids=[str(note_id)])
        self.store.persist()

    async def reset(self) -> None:
        """Reset the vector store by recreating the collection."""
        self.store = Chroma(
            collection_name="notes",
            embedding_function=self.embeddings,
            persist_directory=str(settings.VECTOR_STORE_DIR),
        )
        self.store.persist()

    async def get_note(self, note_id: UUID) -> dict | None:
        """
        Get a note by ID from vector store.

        Args:
            note_id: ID of note to get

        Returns:
            dict | None: Note data if found, None otherwise
        """
        try:
            results = self.store.get(ids=[str(note_id)])
            if not results or not results["documents"]:
                return None

            return {"content": results["documents"][0], "metadata": results["metadatas"][0]}
        except:
            return None
