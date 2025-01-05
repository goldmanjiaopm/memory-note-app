# Memory Note App

A smart note-taking application that uses RAG to help you find and connect your notes. Built with FastAPI, SQLAlchemy, ChromaDB, and React.

### RAG Question Answering
![Question Answering Demo](docs/images/qa-demo.gif)
*Ask questions about your notes and get accurate answers with source citations*

## Features

- 📝 Create and manage notes
- 🤖 AI-powered question answering using your notes as context
- 🔄 Real-time synchronization between database and vector store

## Tech Stack

### Backend
- FastAPI (API Framework)
- SQLAlchemy (Database ORM)
- ChromaDB (Vector Store)
- OpenAI (Embeddings & LLM)
- Pydantic (Data Validation)

### Frontend
- React
- TypeScript
- Vite
- TailwindCSS

## Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API Key

### Running with Docker

1. Clone the repository:
```bash
git clone https://github.com/yourusername/memory-note-app.git
cd memory-note-app
```

2. Create `.env` file

3. Start the application:
```bash
docker-compose up -d
```

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api/v1

### Development Setup

1. Backend Setup:
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run backend
uvicorn app.main:app --reload
```

2. Frontend Setup:
```bash
cd frontend
npm install
npm run dev
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

### Required Variables
- `OPENAI_API_KEY`: Your OpenAI API key

### Optional Variables
- `ENVIRONMENT`: `development` or `production` (default: `development`)
- `DEBUG`: Enable debug mode (default: `true`)
- `DATABASE_URL`: SQLite database URL (default: `sqlite+aiosqlite:///./data/notes.db`)
- `VECTOR_STORE_PATH`: ChromaDB storage location (default: `/app/data/vector_store`)
- `BM25_WEIGHT`: Weight for BM25 search (default: `0.3`)
- `VECTOR_WEIGHT`: Weight for vector search (default: `0.7`)
- `USE_RRF`: Use Reciprocal Rank Fusion instead of weighted average (default: `true`)
- `OPENAI_MODEL`: OpenAI model to use 
- `MAX_TOKENS`: Maximum tokens for OpenAI responses (default: `500`)
- `TEMPERATURE`: OpenAI temperature setting (default: `0.7`)

## Project Structure
```
memory-note-app/
├── app/                    # Backend application
│   ├── config/            # Configuration
│   ├── models/            # Database models
│   ├── retrievers/        # Search retrievers
│   ├── routes/            # API routes
│   ├── schemas/           # Pydantic schemas
│   └── services/          # Business logic
├── docker/                # Docker configuration
│   └── backend/          # Backend Docker files
├── frontend/              # React frontend
│   └── Dockerfile        # Frontend Docker configuration
├── tests/                 # Test suite
├── docker-compose.yml     # Docker compose config
└── requirements.txt       # Python dependencies
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
