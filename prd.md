# Product Requirements Document (PRD)

## Overview

This PRD describes a prototype note-taking web application with contextual memory. Users can create, edit, delete notes, and query them contextually using a Retrieval Augmented Generation (RAG) approach. Development will proceed in modular steps, with testing conducted after each step to ensure reliability and correctness.

## Core Features

1. **User Authentication (Optional):**
   - Not mandatory for the prototype.
   - If implemented, allows multiple users to maintain separate notes.
   
2. **Notes Management:**
   - Create Notes
   - Edit Notes
   - Delete Notes

3. **Query & Retrieval:**
   - Query Endpoint (Accept user queries)
   - Retrieval & Ranking (Embed query, retrieve top chunks, optionally rank)
   - RAG Integration (Use retrieved chunks as context for LLM-based answer)

## Step-by-Step Development and Testing Approach

To ensure incremental development and testing, the project will follow these phases. After each phase, we will run unit and integration tests to validate functionality before proceeding.

**Phase 1: Database and Schemas Setup**
- Implement database schemas (Users, Notes).
- Write migration scripts (if needed).
- **Test:**  
  - Run unit tests to ensure the database connection and schema creation are correct.
  - Verify that you can create and retrieve test notes directly in the DB (no API).

**Phase 2: Note Creation (POST /notes)**
- Implement `POST /notes` endpoint.
- On note creation:
  - Store the note in the DB.
  - Chunk the content, embed, and store embeddings in vector DB.
- **Test:**  
  - Unit tests for chunking and embedding functions.
  - Integration test using `POST /notes` to create a note and verify DB and vector store entries.

**Phase 3: Retrieve All Notes (GET /notes)**
- Implement `GET /notes` endpoint.
- Retrieve all notes from the DB.
- **Test:**  
  - Integration test to ensure `GET /notes` returns the correct list.
  - Unit test on the note retrieval service logic.

**Phase 4: Edit Notes (PUT /notes/{note_id})**
- Implement `PUT /notes/{note_id}` endpoint.
- On edit:
  - Update note in DB.
  - Re-chunk and re-embed updated content.
  - Update vector store embeddings.
- **Test:**  
  - Unit tests for update logic and vector re-embedding.
  - Integration test to ensure edited note content is correctly reflected in the DB and vector store.

**Phase 5: Delete Notes (DELETE /notes/{note_id})**
- Implement `DELETE /notes/{note_id}` endpoint.
- On delete:
  - Remove note from DB.
  - Remove associated embeddings from vector DB.
- **Test:**
  - Integration test to confirm the note and its embeddings are removed.
  - Check that queries no longer return deleted notes.

**Phase 6: Query Notes (POST /query)**
- Implement `POST /query` endpoint.
- Process:
  - Embed the query.
  - Retrieve top `k` relevant note chunks.
  - (Optional) Rank these chunks.
  - Use LangChain to run a retrieval-augmented generation chain.
  - Return a response from LLM with query and retrieved chunks as context.
- **Test:**
  - Unit tests for query embedding and retrieval logic.
  - Integration test where a query returns the expected notes as context.
  - Verify the LLM-generated answer is coherent and uses retrieved context.

## Detailed Requirements

### Data Model

**User Table (optional):**
- `id`: UUID (primary key)
- `email`: string
- `password_hash`: string (if authentication)
- `created_at`: datetime

**Notes Table:**
- `id`: UUID (primary key)
- `user_id`: UUID (foreign key to User if implemented)
- `title`: string
- `content`: text
- `created_at`: datetime
- `updated_at`: datetime

**Vector Index (Vector DB):**
- `embedding`: vector
- `metadata`: { "note_id": UUID, "chunk_index": int }
- `text`: chunked note text

### API Endpoints

**POST /notes**
**Request:**
```json
{
  "title": "My First Note",
  "content": "This is the note content..."
}
```
**Process:**

- Create and store the note.
- Chunk and embed content.
- Store embeddings in vector DB.

**Response:**

json

Copy code

`{ "id": "<note_id>", "message": "Note created successfully" }`

2. **PUT /notes/{note_id}**  
    **Request:**
    
    json
    
    Copy code
    
    `{   "title": "Updated Title",   "content": "Updated note content..." }`
    
    **Process:**
    
    - Update note in DB.
    - Re-chunk and re-embed.
    - Update vector DB embeddings.
    
    **Response:**
    
    json
    
    Copy code
    
    `{ "message": "Note updated successfully" }`
    
3. **DELETE /notes/{note_id}**  
    **Process:**
    
    - Delete note from DB.
    - Remove embeddings from vector DB.
    
    **Response:**
    
    json
    
    Copy code
    
    `{ "message": "Note deleted successfully" }`
    
4. **GET /notes**  
    **Process:**
    
    - Retrieve all notes for a user.
    
    **Response:**
    
    json
    
    Copy code
    
    `[   {     "id": "<note_id>",     "title": "Title",     "content": "Full note content...",     "updated_at": "2024-12-19T12:34:56"   } ]`
    
5. **POST /query**  
    **Request:**
    
    json
    
    Copy code
    
    `{   "query": "What is the summary of my first note?" }`
    
    **Process:**
    
    - Embed the query.
    - Retrieve top `k` relevant note chunks.
    - (Optional) Rank results.
    - Use LangChain to run a retrieval-augmented generation chain.
    
    **Response:**
    
    json
    
    Copy code
    
    `{   "answer": "Your first note talks about..." }`
    

## Backend Implementation Details

**Tech Stack:**

- **Language:** Python 3.10+
- **Framework:** FastAPI
- **Database:** PostgreSQL or SQLite for relational data
- **Vector Store:** Chroma, FAISS, or Pinecone
- **Embeddings:** OpenAIEmbeddings (or another embedding model via LangChain)
- **LLM Integration:** OpenAI GPT-3.5/4 or local model via LangChain

**Libraries:**

- `fastapi`
- `sqlalchemy`
- `langchain`
- `pytest` for testing
- `httpx` or `requests` for integration tests

**Process:**

- Use LangChain’s `TextSplitter` to chunk notes.
- Use embeddings from `langchain.embeddings`.
- Store embeddings in `langchain.vectorstores`.
- For queries, perform similarity search and feed top documents into a retrieval chain.

## Frontend Implementation Details

**Tech Stack:**

- **Language:** JavaScript/TypeScript
- **Framework:** React
- **State Management:** React Hooks or Redux/Zustand
- **UI Components:**
    - `NoteList` (view notes)
    - `NoteEditor` (create/edit notes)
    - `QueryForm` (submit queries)
    - `QueryResponse` (display answers)

**API Integration:**

- Use `fetch` or `axios` to interact with the backend.
- Handle note CRUD and query retrieval.

## Suggested File Structure

**Backend (Python):**

backend/
    app/
        main.py              # FastAPI entry point
        config.py            # Config variables
        schemas.py           # Pydantic models
        database.py          # SQLAlchemy setup, DB session
        models.py            # SQLAlchemy models: User, Note
        vectorstore.py       # Vector DB setup (e.g., Chroma)
        embeddings.py        # Embedding functions
        chunking.py          # Text chunking functions
        routes/
            notes.py         # Note CRUD endpoints
            query.py         # Query endpoint
        services/
            note_service.py  # Note create/edit/delete logic
            query_service.py # Query retrieval and LLM logic
        tests/
            test_notes.py    # Tests for notes endpoints
            test_query.py    # Tests for query endpoint
            conftest.py      # pytest fixtures


**Frontend (React):**

frontend/
    src/
        index.js             # React entry point
        App.js               # Main App component
        components/
            NoteList.js      # Displays all notes
            NoteEditor.js    # Create/Edit form
            QueryForm.js     # Query input form
            QueryResponse.js # Displays query responses
        api/
            notes.js         # Functions to call /notes API
            query.js         # Functions to call /query API
        hooks/               # Custom React hooks if needed
        context/             # React contexts if needed
        styles/              # CSS or styled components
    public/
        index.html


## Testing Strategy

**Backend Tests (pytest):**

- **Unit Tests:**
    - Test `note_service.py` for create/edit/delete logic.
    - Test `query_service.py` for retrieval and ranking logic with mocks.
- **Integration Tests:**
    - Test API endpoints (`/notes`, `/query`) using `httpx` or `requests`.
    - Validate embedding storage, retrieval accuracy.

**Frontend Tests (Jest + React Testing Library):**

- Test `NoteList` to ensure notes display correctly.
- Test `NoteEditor` for creating and editing notes.
- Test `QueryForm` and `QueryResponse` for query/response flow.

## Documentation and References

- **FastAPI:**
    
    - Official Documentation
    - CRUD and DB Example
- **LangChain:**
    
    - Documentation
    - Retrieval QA Chain Example
- **Vector Stores:**
    
    - Chroma Docs
    - [FAISS GitHub](https://github.com/facebookresearch/faiss)
- **OpenAI API (if used):**
    
    - [OpenAI API Docs](https://platform.openai.com/docs/introduction)
- **React:**
    
    - [React Documentation](https://reactjs.org/)
    - React Testing Library
