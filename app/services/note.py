from typing import Dict, List, Optional
from uuid import UUID

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..config.ai_config import get_ai_config
from ..config.prompts import REGENERATION_PROMPT, RELEVANCY_CHECK_PROMPT
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

    async def _check_response_quality(self, query: str, contexts: List[str], response: str) -> bool:
        """
        Check if response is relevant and not hallucinated.

        Args:
            query: Original query
            contexts: Context documents used
            response: Generated response to check

        Returns:
            bool: True if response is good, False if it needs regeneration
        """
        # Format the relevancy check prompt
        check_prompt = RELEVANCY_CHECK_PROMPT.format(
            query=query, contexts="\n".join(f"- {context}" for context in contexts), response=response
        )

        # Get the quality check response
        check_response = await self.openai_client.chat.completions.create(
            model=ai_config.openai.model,
            messages=[
                {"role": "system", "content": "You are a strict fact-checker. Only respond with 'yes' or 'no'."},
                {"role": "user", "content": check_prompt},
            ],
            temperature=0,  # Use 0 for consistent checking
            max_tokens=1,
        )

        return check_response.choices[0].message.content.lower().strip() == "yes"

    async def _regenerate_response(self, query: str, contexts: List[str], issue_type: str) -> str:
        """
        Regenerate a response that was found to be problematic.

        Args:
            query: Original query
            contexts: Context documents
            issue_type: Description of the issue ("hallucinated" or "not relevant")

        Returns:
            str: Regenerated response
        """
        regenerate_prompt = REGENERATION_PROMPT.format(
            issue_type=issue_type, contexts="\n".join(f"- {context}" for context in contexts), query=query
        )

        response = await self.openai_client.chat.completions.create(
            model=ai_config.openai.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions strictly based on the given context.",
                },
                {"role": "user", "content": regenerate_prompt},
            ],
            temperature=ai_config.openai.temperature / 2,  # Lower temperature for more focused response
            max_tokens=ai_config.openai.max_tokens,
        )

        return response.choices[0].message.content

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
        prompt = f"""Based on the following contexts, answer the query. If the contexts don't contain relevant information answer to the best of your ability but tell the user that you couldn't find relevant information.

Contexts:
{chr(10).join(f'- {context}' for context in contexts)}

Query: {query}

Please provide a clear and concise response using the information from the given contexts and if you don't have relevant information answer to the best of your ability but tell the user that you couldn't find relevant information."""

        # Generate initial response
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

        initial_response = response.choices[0].message.content

        # # Check response quality - rerank rag
        # is_good_response = await self._check_response_quality(query, contexts, initial_response)
        # for _ in range(5):
        #     if not is_good_response:
        #         # Regenerate response with stricter constraints
        #         final_response = await self._regenerate_response(
        #             query, contexts, "hallucinated or not fully relevant to the query"
        #         )
        #         is_good_response = await self._check_response_quality(query, contexts, final_response)
        #     else:
        #         final_response = initial_response
        #         break

        return {"response": initial_response, "sources": sources}
