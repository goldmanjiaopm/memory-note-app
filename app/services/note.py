from typing import Dict, List, Optional
from uuid import UUID

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..config.ai_config import get_ai_config
from ..models import Note
from ..retrievers.base import BaseRetriever
from ..retrievers.combined import CombinedRetriever
from ..schemas import NoteCreate

settings = get_settings()
ai_config = get_ai_config()


class NoteService:
    """Service for managing notes with vector search capabilities."""

    def __init__(self, retriever: Optional[BaseRetriever] = None):
        """Initialize with retriever instance."""
        self.retriever = retriever or CombinedRetriever(k0=ai_config.retriever.rrf_k0)
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

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

    async def search_notes(self, query: str, k: int = None) -> List[dict]:
        """
        Search notes by semantic similarity and BM25.

        Args:
            query: Search query
            k: Number of results to return (defaults to config value)

        Returns:
            List[dict]: Similar notes with combined scores
        """
        k = k or ai_config.retriever.top_k
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

    async def generate_response(self, query: str, k: int = None) -> Dict[str, str]:
        """
        Generate a response to a query using relevant notes as context.

        Args:
            query: User's query
            k: Number of relevant notes to use as context (defaults to config value)

        Returns:
            Dict[str, str]: Dictionary containing the response and sources
        """
        # Get relevant notes
        k = k or ai_config.retriever.top_k
        search_results = await self.search_notes(query, k)

        if not search_results:
            return {"response": "I couldn't find any relevant information to answer your query.", "sources": []}

        # Prepare context from search results
        contexts = []
        sources = []
        for result in search_results:
            if result["score"] >= ai_config.retriever.min_score_threshold:
                contexts.append(result["content"])
                sources.append({"content": result["content"], "metadata": result["metadata"]})

        if not contexts:
            return {
                "response": "I couldn't find any sufficiently relevant information to answer your query.",
                "sources": [],
            }

        # Create prompt with context
        prompt = f"""Based on the following contexts, answer the query. If the contexts don't contain relevant information, say so.

Contexts:
{chr(10).join(f'- {context}' for context in contexts)}

Query: {query}

Please provide a clear and concise response using only the information from the given contexts."""

        # Generate response using OpenAI
        response = await self.openai_client.chat.completions.create(
            model=ai_config.openai.model,
            messages=[
                {
                    "role": "system",
                    "content": ai_config.openai.system_prompt,
                },
                {"role": "user", "content": prompt},
            ],
            temperature=ai_config.openai.temperature,
            max_tokens=ai_config.openai.max_tokens,
        )

        return {"response": response.choices[0].message.content, "sources": sources}
