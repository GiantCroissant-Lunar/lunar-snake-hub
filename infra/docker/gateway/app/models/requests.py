from pydantic import BaseModel, Field
from typing import List, Optional, Any, Literal


class AskRequest(BaseModel):
    """Request for RAG query"""

    query: str = Field(..., description="Query to search for")
    repo: Optional[str] = Field(None, description="Repository name to search in")
    hints: Optional[List[str]] = Field(
        None, description="File path hints to narrow search"
    )
    top_k: Optional[int] = Field(
        5, ge=1, le=20, description="Number of results to return"
    )
    threshold: Optional[float] = Field(
        0.7, ge=0.0, le=1.0, description="Similarity threshold"
    )


class MemoryRequest(BaseModel):
    """Request for memory operations"""

    op: Literal["get", "put", "search", "delete"] = Field(
        ..., description="Operation type"
    )
    agent_id: str = Field(..., description="Agent identifier")
    key: Optional[str] = Field(None, description="Memory key (for get/put/delete)")
    value: Optional[Any] = Field(None, description="Memory value (for put)")
    query: Optional[str] = Field(None, description="Search query (for search)")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Search limit")


class NotesRequest(BaseModel):
    """Request for notes operations"""

    op: Literal["add", "search", "list", "delete"] = Field(
        ..., description="Operation type"
    )
    repo: Optional[str] = Field(None, description="Repository name")
    text: Optional[str] = Field(None, description="Note text (for add)")
    query: Optional[str] = Field(None, description="Search query (for search)")
    tags: Optional[List[str]] = Field(None, description="Note tags (for add/search)")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Search limit")


class SearchRequest(BaseModel):
    """Request for vector search only"""

    query: str = Field(..., description="Query to search for")
    repo: Optional[str] = Field(None, description="Repository name to search in")
    hints: Optional[List[str]] = Field(
        None, description="File path hints to narrow search"
    )
    top_k: Optional[int] = Field(
        5, ge=1, le=20, description="Number of results to return"
    )
    threshold: Optional[float] = Field(
        0.7, ge=0.0, le=1.0, description="Similarity threshold"
    )
    include_content: Optional[bool] = Field(
        True, description="Include content in results"
    )


class IndexRequest(BaseModel):
    """Request to index a repository"""

    repo_path: str = Field(..., description="Path to repository")
    collection_name: str = Field(..., description="Qdrant collection name")
    force_reindex: Optional[bool] = Field(
        False, description="Force reindex even if exists"
    )
    file_patterns: Optional[List[str]] = Field(
        None, description="File patterns to include"
    )
    exclude_patterns: Optional[List[str]] = Field(
        None, description="File patterns to exclude"
    )


class ReindexRequest(BaseModel):
    """Request to reindex changed files"""

    repo: str = Field(..., description="Repository name")
    ref: str = Field(..., description="Git reference")
    sha: str = Field(..., description="Git commit SHA")
    changed: List[str] = Field(..., description="List of changed file paths")
    collection_name: Optional[str] = Field(None, description="Qdrant collection name")
