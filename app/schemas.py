from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class NoteBase(BaseModel):
    """Base schema with shared note attributes."""

    title: str
    content: str


class NoteCreate(NoteBase):
    """Schema for creating a new note."""

    pass


class NoteUpdate(NoteBase):
    """Schema for updating an existing note."""

    title: str | None = None
    content: str | None = None


class NoteRead(NoteBase):
    """Schema for reading a note, includes all fields."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        """Configure Pydantic to work with SQLAlchemy models."""

        from_attributes = True
