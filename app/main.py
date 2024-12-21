from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import API_V1_PREFIX
from .database import init_db
from .routes import notes

app = FastAPI(
    title="Memory Note App",
    description="A note-taking application with semantic search capabilities",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    await init_db()


# Include routers
app.include_router(notes.router, prefix=API_V1_PREFIX)
