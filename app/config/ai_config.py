"""AI-related configuration settings."""

from enum import Enum
from functools import lru_cache
from typing import Dict, Literal

from pydantic import BaseModel, Field


class CombinationMethod(str, Enum):
    """Method for combining retriever results."""

    RRF = "rrf"  # Reciprocal Rank Fusion
    WEIGHTED = "weighted"  # Weighted average


class OpenAIConfig(BaseModel):
    """OpenAI-specific configuration."""

    model: str = Field(default="gpt-4o-mini", description="Model to use for chat completions")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature for response generation")
    max_tokens: int = Field(default=500, gt=0, description="Maximum number of tokens in the response")
    system_prompt: str = Field(
        default="You are a helpful assistant that answers questions based on the given context.",
        description="System prompt for chat completions",
    )


class RetrieverConfig(BaseModel):
    """Configuration for retrieval systems."""

    top_k: int = Field(default=4, gt=0, description="Number of documents to retrieve")
    combination_method: CombinationMethod = Field(
        default=CombinationMethod.RRF, description="Method to combine results from different retrievers"
    )
    rrf_k0: float = Field(default=60.0, gt=0.0, description="Constant for RRF calculation in combined retriever")
    vector_weight: float = Field(
        default=0.7, ge=0.0, description="Weight for vector retriever scores when using weighted average"
    )
    bm25_weight: float = Field(
        default=0.3, ge=0.0, description="Weight for BM25 retriever scores when using weighted average"
    )
    min_score_threshold: float = Field(
        default=0.001, ge=0.0, le=1.0, description="Minimum score threshold for retrieved documents"
    )

    class Config:
        """Pydantic config for validation."""

        @classmethod
        def validate_weights(cls, values):
            """Validate that weights are properly configured."""
            if (
                values.get("combination_method") == CombinationMethod.WEIGHTED
                and values.get("vector_weight", 0) + values.get("bm25_weight", 0) <= 0
            ):
                raise ValueError("At least one weight must be greater than 0 when using weighted average")
            return values


class EmbeddingsConfig(BaseModel):
    """Embeddings model configuration."""

    model_name: str = Field(default="all-MiniLM-L6-v2", description="Model name for embeddings")
    device: str = Field(default="cpu", description="Device to use for embeddings (cpu/cuda)")


class ChromaConfig(BaseModel):
    """Chroma vector store configuration."""

    collection_name: str = Field(default="notes", description="Name of the vector store collection")


class AIConfig(BaseModel):
    """Main AI configuration container."""

    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    retriever: RetrieverConfig = Field(default_factory=RetrieverConfig)
    embeddings: EmbeddingsConfig = Field(default_factory=EmbeddingsConfig)
    chroma: ChromaConfig = Field(default_factory=ChromaConfig)

    class Config:
        """Pydantic config."""

        env_prefix = "AI_"  # Environment variables prefix
        env_nested_delimiter = "__"  # Use double underscore for nested config


@lru_cache
def get_ai_config() -> AIConfig:
    """
    Get cached AI configuration with values from environment variables.

    Environment variables override default values when present.
    Examples:
        AI_OPENAI__MODEL=gpt-4 will override the default model
        AI_RETRIEVER__TOP_K=6 will override default top_k
        AI_RETRIEVER__COMBINATION_METHOD=weighted will use weighted average
        AI_RETRIEVER__VECTOR_WEIGHT=0.8 will set vector weight to 0.8
        AI_EMBEDDINGS__DEVICE=cuda will use GPU for embeddings

    Returns:
        AIConfig: Configuration instance
    """
    return AIConfig()
