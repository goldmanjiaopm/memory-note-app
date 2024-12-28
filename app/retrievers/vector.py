from typing import List
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

from ..config import get_settings
from .base import BaseRetriever, SearchResult

settings = get_settings()


class VectorRetriever(BaseRetriever):
    """Vector store retriever implementation."""

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

    async def add_document(self, content: str, metadata: dict) -> None:
        """
        Add a document to the retriever.

        Args:
            content: Document content
            metadata: Document metadata
        """
        self.store.add_texts(texts=[content], metadatas=[metadata], ids=[metadata["note_id"]])
        self.store.persist()

    async def search(self, query: str, k: int = 4) -> List[SearchResult]:
        """
        Search for documents using vector similarity.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List[SearchResult]: Search results with scores
        """
        results = self.store.similarity_search_with_score(query=query, k=k)

        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": round(score, 4),
            }
            for doc, score in results
        ]

    async def delete_document(self, doc_id: str) -> None:
        """
        Delete a document from the retriever.

        Args:
            doc_id: Document ID to delete
        """
        self.store.delete(ids=[doc_id])
        self.store.persist()

    async def reset(self) -> None:
        """Reset the retriever."""
        self.store = Chroma(
            collection_name="notes",
            embedding_function=self.embeddings,
            persist_directory=str(settings.VECTOR_STORE_DIR),
        )
        self.store.persist()
