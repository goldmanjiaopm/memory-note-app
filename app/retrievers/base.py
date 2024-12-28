from abc import ABC, abstractmethod
from typing import List, TypedDict


class SearchResult(TypedDict):
    """Search result type."""

    content: str
    metadata: dict
    score: float


class BaseRetriever(ABC):
    """Base class for all retrievers."""

    @abstractmethod
    async def add_document(self, content: str, metadata: dict) -> None:
        """Add a document to the retriever."""
        pass

    @abstractmethod
    async def search(self, query: str, k: int = 4) -> List[SearchResult]:
        """Search for documents."""
        pass

    @abstractmethod
    async def delete_document(self, doc_id: str) -> None:
        """Delete a document from the retriever."""
        pass

    @abstractmethod
    async def reset(self) -> None:
        """Reset the retriever."""
        pass
