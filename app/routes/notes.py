from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import async_session
from ..schemas import NoteCreate, NoteRead
from ..services.note import NoteService
from ..retrievers.combined import CombinedRetriever

router = APIRouter(prefix="/notes", tags=["notes"])


async def get_db():
    """Get database session."""
    async with async_session() as session:
        yield session


async def get_note_service():
    """Get note service instance."""
    return NoteService(CombinedRetriever(vector_weight=0.7))


@router.post("/", response_model=NoteRead)
async def create_note(
    note_data: NoteCreate,
    db: AsyncSession = Depends(get_db),
    note_service: NoteService = Depends(get_note_service),
) -> NoteRead:
    """
    Create a new note.

    Args:
        note_data: Note data to create
        db: Database session
        note_service: Note service instance

    Returns:
        NoteRead: Created note
    """
    return await note_service.create_note(db, note_data)


@router.get("/", response_model=List[NoteRead])
async def get_notes(
    db: AsyncSession = Depends(get_db),
    note_service: NoteService = Depends(get_note_service),
) -> List[NoteRead]:
    """
    Get all notes.

    Args:
        db: Database session
        note_service: Note service instance

    Returns:
        List[NoteRead]: List of all notes
    """
    return await note_service.get_notes(db)


@router.get("/{note_id}", response_model=NoteRead)
async def get_note(
    note_id: UUID,
    db: AsyncSession = Depends(get_db),
    note_service: NoteService = Depends(get_note_service),
) -> NoteRead:
    """
    Get a note by ID.

    Args:
        note_id: ID of note to get
        db: Database session
        note_service: Note service instance

    Returns:
        NoteRead: Found note

    Raises:
        HTTPException: If note is not found
    """
    note = await note_service.get_note(db, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.delete("/{note_id}")
async def delete_note(
    note_id: UUID,
    db: AsyncSession = Depends(get_db),
    note_service: NoteService = Depends(get_note_service),
) -> dict:
    """
    Delete a note.

    Args:
        note_id: ID of note to delete
        db: Database session
        note_service: Note service instance

    Returns:
        dict: Success message

    Raises:
        HTTPException: If note is not found
    """
    success = await note_service.delete_note(db, note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"message": "Note deleted successfully"}


@router.post("/search")
async def search_notes(
    query: str,
    k: int = 4,
    note_service: NoteService = Depends(get_note_service),
) -> List[dict]:
    """
    Search notes by semantic similarity and BM25.

    Args:
        query: Search query
        k: Number of results to return
        note_service: Note service instance

    Returns:
        List[dict]: Similar notes with combined scores
    """
    return await note_service.search_notes(query, k)
