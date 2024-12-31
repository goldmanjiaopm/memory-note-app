# Memory Note App

A smart note-taking application that uses AI to help you find and connect your notes. Built with FastAPI, SQLAlchemy, ChromaDB, and React.

## Features

- 📝 Create and manage notes with rich text
- 🔍 Smart search using hybrid retrieval (BM25 + Vector Search)
- 🤖 AI-powered question answering using your notes as context
- 🎯 Reciprocal Rank Fusion (RRF) for optimal search results
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

2. Create `.env` file:
```bash
cp .env.template .env
# Edit .env and add your OpenAI API key
```

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
├── frontend/              # React frontend
├── tests/                 # Test suite
├── docker-compose.yml     # Docker compose config
└── requirements.txt       # Python dependencies
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 