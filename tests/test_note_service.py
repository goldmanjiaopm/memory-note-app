from uuid import UUID
import shutil
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Note
from app.schemas import NoteCreate
from app.services.note import NoteService
from app.vector_store import VectorStore


@pytest.fixture
async def vector_store(tmp_path):
    """Create a temporary vector store for testing."""
    from app.config import get_settings

    settings = get_settings()

    # Create test directories
    test_dir = tmp_path / "test_data"
    test_dir.mkdir(exist_ok=True)
    vector_store_dir = test_dir / "test_vector_store"
    vector_store_dir.mkdir(exist_ok=True)

    # Override settings for testing
    settings.VECTOR_STORE_DIR = vector_store_dir

    store = VectorStore()
    yield store

    # Cleanup: Delete the temporary test directory
    try:
        store.store._collection = None  # Close Chroma collection
        shutil.rmtree(test_dir)
    except Exception as e:
        print(f"Warning: Failed to cleanup test directory: {e}")


@pytest.fixture
async def note_service(vector_store):
    """Create a note service instance."""
    return NoteService(vector_store)


@pytest.fixture
async def sample_note_data():
    """Sample note data for testing."""
    return NoteCreate(
        title="Test Note",
        content="This is a test note about machine learning and AI.",
    )


async def test_create_note(note_service: NoteService, db: AsyncSession, sample_note_data: NoteCreate):
    """Test creating a note."""
    note = await note_service.create_note(db, sample_note_data)

    assert isinstance(note, Note)
    assert isinstance(note.id, UUID)
    assert note.title == sample_note_data.title
    assert note.content == sample_note_data.content


async def test_get_note(note_service: NoteService, db: AsyncSession, sample_note_data: NoteCreate):
    """Test retrieving a note by ID."""
    # Create a note first
    created_note = await note_service.create_note(db, sample_note_data)

    # Get the note
    retrieved_note = await note_service.get_note(db, created_note.id)

    assert retrieved_note is not None
    assert retrieved_note.id == created_note.id
    assert retrieved_note.title == sample_note_data.title


async def test_get_notes(note_service: NoteService, db: AsyncSession, sample_note_data: NoteCreate):
    """Test retrieving all notes."""
    # Create two notes
    note1 = await note_service.create_note(db, sample_note_data)
    note2 = await note_service.create_note(db, NoteCreate(title="Another Note", content="More test content"))

    # Get all notes
    notes = await note_service.get_notes(db)

    assert len(notes) >= 2
    assert any(note.id == note1.id for note in notes)
    assert any(note.id == note2.id for note in notes)


async def test_search_notes(note_service: NoteService, db: AsyncSession):
    """Test searching notes by similarity."""
    # Create notes with different content
    await note_service.create_note(
        db, NoteCreate(title="AI Note", content="Artificial Intelligence and Machine Learning concepts.")
    )
    await note_service.create_note(
        db, NoteCreate(title="Weather Note", content="The weather is sunny today with clear skies.")
    )

    # Search for AI-related content
    results = await note_service.search_notes("machine learning concepts")

    assert len(results) > 0
    assert any("Intelligence" in result["content"] for result in results)
    assert all(isinstance(result["score"], float) for result in results)


async def test_delete_note(note_service: NoteService, db: AsyncSession, sample_note_data: NoteCreate):
    """Test deleting a note."""
    # Create a note
    note = await note_service.create_note(db, sample_note_data)

    # Delete the note
    success = await note_service.delete_note(db, note.id)
    assert success is True

    # Verify note is deleted
    deleted_note = await note_service.get_note(db, note.id)
    assert deleted_note is None

    # Verify deletion from vector store (should not raise errors)
    results = await note_service.search_notes(sample_note_data.content)
    assert not any(r["metadata"]["note_id"] == str(note.id) for r in results)


async def test_db_vector_store_sync(note_service: NoteService, db: AsyncSession):
    """Test synchronization between database and vector store."""
    # Clean up both stores
    await note_service.vector_store.reset()

    # Delete all notes from database using SQLAlchemy
    from sqlalchemy import delete
    from app.models import Note

    await db.execute(delete(Note))
    await db.commit()

    # Verify both stores are empty
    db_notes = await note_service.get_notes(db)
    assert len(db_notes) == 0, "Database should be empty at start"

    vector_results = await note_service.search_notes("", k=100)  # Try to get all notes
    assert len(vector_results) == 0, "Vector store should be empty at start"

    # Create multiple notes
    notes = [
        NoteCreate(title="Note 1", content="First note content"),
        NoteCreate(title="Note 2", content="Second note content"),
        NoteCreate(title="Note 3", content="Third note content"),
    ]

    created_notes = []
    for note_data in notes:
        note = await note_service.create_note(db, note_data)
        created_notes.append(note)

    # Verify each note exists in both stores with matching IDs
    for note in created_notes:
        # Check in database
        db_note = await note_service.get_note(db, note.id)
        assert db_note is not None, f"Note {note.id} not found in database"

        # Check in vector store
        vector_note = await note_service.vector_store.get_note(note.id)
        assert vector_note is not None, f"Note {note.id} not found in vector store"

        # Verify IDs match
        assert vector_note["metadata"]["note_id"] == str(note.id), "ID mismatch between stores"

        # Verify content matches
        assert vector_note["content"] == note.content, "Content mismatch between stores"

    # Verify total counts match
    db_notes = await note_service.get_notes(db)
    assert len(db_notes) == len(notes), "Database count mismatch"
