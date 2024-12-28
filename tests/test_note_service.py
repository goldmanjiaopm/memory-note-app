from uuid import UUID
import shutil
from pathlib import Path
from typing import List

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Note
from app.retrievers import BM25Retriever, CombinedRetriever, VectorRetriever
from app.schemas import NoteCreate
from app.services.note import NoteService


@pytest.fixture
async def vector_retriever(tmp_path):
    """Create a temporary vector retriever for testing."""
    from app.config import get_settings

    settings = get_settings()

    # Create test directories
    test_dir = tmp_path / "test_data"
    test_dir.mkdir(exist_ok=True)
    vector_store_dir = test_dir / "test_vector_store"
    vector_store_dir.mkdir(exist_ok=True)

    # Override settings for testing
    settings.VECTOR_STORE_DIR = vector_store_dir

    retriever = VectorRetriever()
    yield retriever

    # Cleanup: Delete the temporary test directory
    try:
        retriever.store._collection = None  # Close Chroma collection
        shutil.rmtree(test_dir)
    except Exception as e:
        print(f"Warning: Failed to cleanup test directory: {e}")


@pytest.fixture
async def bm25_retriever():
    """Create a BM25 retriever for testing."""
    return BM25Retriever()


@pytest.fixture
async def combined_retriever(vector_retriever, bm25_retriever):
    """Create a combined retriever for testing."""
    retriever = CombinedRetriever(vector_weight=0.7)
    retriever.vector_retriever = vector_retriever
    retriever.bm25_retriever = bm25_retriever
    return retriever


@pytest.fixture
async def note_service(combined_retriever):
    """Create a note service instance."""
    return NoteService(combined_retriever)


@pytest.fixture
async def sample_notes_data():
    """Sample notes data for testing."""
    return [
        NoteCreate(
            title="Machine Learning",
            content="Deep learning and neural networks are transforming AI applications.",
        ),
        NoteCreate(
            title="Python Programming",
            content="Python is a versatile language great for AI and web development.",
        ),
        NoteCreate(
            title="Web Development",
            content="Modern web apps use frameworks like React and FastAPI.",
        ),
    ]


async def test_create_note(note_service: NoteService, db: AsyncSession, sample_notes_data: List[NoteCreate]):
    """Test creating a note."""
    note = await note_service.create_note(db, sample_notes_data[0])

    assert isinstance(note, Note)
    assert isinstance(note.id, UUID)
    assert note.title == sample_notes_data[0].title
    assert note.content == sample_notes_data[0].content


async def test_vector_search(note_service: NoteService, db: AsyncSession, sample_notes_data: List[NoteCreate]):
    """Test vector search functionality."""
    # Create test notes
    for note_data in sample_notes_data:
        await note_service.create_note(db, note_data)

    # Search for AI-related content
    results = await note_service.retriever.vector_retriever.search("artificial intelligence")

    assert len(results) > 0
    # The ML note should be most relevant
    assert any("neural networks" in result["content"] for result in results)
    assert all(isinstance(result["score"], float) for result in results)


async def test_bm25_search(note_service: NoteService, db: AsyncSession, sample_notes_data: List[NoteCreate]):
    """Test BM25 search functionality."""
    # Create test notes
    for note_data in sample_notes_data:
        await note_service.create_note(db, note_data)

    # Search for Python-related content
    results = await note_service.retriever.bm25_retriever.search("python programming language")

    assert len(results) > 0
    # The Python note should be most relevant
    assert any("Python is a versatile language" in result["content"] for result in results)
    assert all(isinstance(result["score"], float) for result in results)


async def test_combined_search(note_service: NoteService, db: AsyncSession, sample_notes_data: List[NoteCreate]):
    """Test combined search functionality."""
    # Create test notes
    for note_data in sample_notes_data:
        await note_service.create_note(db, note_data)

    # Search that should benefit from both vector and keyword matching
    results = await note_service.search_notes("AI and Python")

    assert len(results) > 0
    # Should find both AI and Python related notes
    assert any("neural networks" in result["content"] for result in results)
    assert any("Python" in result["content"] for result in results)
    assert all(isinstance(result["score"], float) for result in results)


async def test_delete_note(note_service: NoteService, db: AsyncSession, sample_notes_data: List[NoteCreate]):
    """Test deleting a note."""
    # Create a note
    note = await note_service.create_note(db, sample_notes_data[0])

    # Delete the note
    success = await note_service.delete_note(db, note.id)
    assert success is True

    # Verify note is deleted from database
    deleted_note = await note_service.get_note(db, note.id)
    assert deleted_note is None

    # Verify deletion from retrievers
    vector_results = await note_service.retriever.vector_retriever.search(sample_notes_data[0].content)
    bm25_results = await note_service.retriever.bm25_retriever.search(sample_notes_data[0].content)

    assert not any(r["metadata"]["note_id"] == str(note.id) for r in vector_results)
    assert not any(r["metadata"]["note_id"] == str(note.id) for r in bm25_results)


async def test_search_empty_query(note_service: NoteService, db: AsyncSession, sample_notes_data: List[NoteCreate]):
    """Test searching with empty query."""
    # Create test notes
    for note_data in sample_notes_data:
        await note_service.create_note(db, note_data)

    # Search with empty query
    results = await note_service.search_notes("")

    # Should return results but with very low scores
    assert len(results) > 0
    assert all(isinstance(result["score"], float) for result in results)


async def test_search_no_results(note_service: NoteService, db: AsyncSession):
    """Test searching with no matching results."""
    results = await note_service.search_notes("completely unrelated query xyzabc")
    assert len(results) == 0
