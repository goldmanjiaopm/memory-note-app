from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Note
from ..retrievers.base import BaseRetriever
from ..retrievers.combined import CombinedRetriever
from ..schemas import NoteCreate


class NoteService:
    """Service for managing notes with vector search capabilities."""

    def __init__(self, retriever: Optional[BaseRetriever] = None):
        """Initialize with retriever instance."""
        self.retriever = retriever or CombinedRetriever()

    async def create_note(self, db: AsyncSession, note_data: NoteCreate) -> Note:
        """
        Create a new note and add it to retrievers.

        Args:
            db: Database session
            note_data: Note data to create

        Returns:
            Note: Created note
        """
        # Create note in database
        note = Note(**note_data.model_dump())
        db.add(note)
        await db.commit()
        await db.refresh(note)

        # Add to retrievers
        metadata = {"note_id": str(note.id), "title": note.title}
        await self.retriever.add_document(note.content, metadata)

        return note

    async def get_notes(self, db: AsyncSession) -> List[Note]:
        """
        Get all notes.

        Args:
            db: Database session

        Returns:
            List[Note]: List of all notes
        """
        result = await db.execute(select(Note))
        return list(result.scalars().all())

    async def get_note(self, db: AsyncSession, note_id: UUID) -> Optional[Note]:
        """
        Get a note by ID.

        Args:
            db: Database session
            note_id: ID of note to get

        Returns:
            Optional[Note]: Found note or None
        """
        return await db.get(Note, note_id)

    async def search_notes(self, query: str, k: int = 4) -> List[dict]:
        """
        Search notes by semantic similarity and BM25.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List[dict]: Similar notes with combined scores
        """
        return await self.retriever.search(query, k)

    async def delete_note(self, db: AsyncSession, note_id: UUID) -> bool:
        """
        Delete a note.

        Args:
            db: Database session
            note_id: ID of note to delete

        Returns:
            bool: True if note was deleted
        """
        note = await self.get_note(db, note_id)
        if not note:
            return False

        await db.delete(note)
        await db.commit()

        # Remove from retrievers
        await self.retriever.delete_document(str(note_id))

        return True
