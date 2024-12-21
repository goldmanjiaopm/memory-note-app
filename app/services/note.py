from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Note
from ..schemas import NoteCreate
from ..vector_store import VectorStore


class NoteService:
    """Service for managing notes with vector search capabilities."""

    def __init__(self, vector_store: VectorStore):
        """Initialize with vector store instance."""
        self.vector_store = vector_store

    async def create_note(self, db: AsyncSession, note_data: NoteCreate) -> Note:
        """
        Create a new note and add it to vector store.

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

        # Add to vector store
        await self.vector_store.add_note(note)

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
        Search notes by semantic similarity.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List[dict]: Similar notes with scores
        """
        return await self.vector_store.search_similar(query, k)

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

        # Remove from vector store
        await self.vector_store.delete_note(note_id)

        return True
