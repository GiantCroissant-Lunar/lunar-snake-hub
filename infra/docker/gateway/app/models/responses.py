from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChunkInfo(BaseModel):
    """Information about a retrieved chunk"""

    id: str = Field(..., description="Chunk ID")
    file_path: str = Field(..., description="File path")
    start_line: Optional[int] = Field(None, description="Start line number")
    end_line: Optional[int] = Field(None, description="End line number")
    content: str = Field(..., description="Chunk content")
    relevance: float = Field(..., description="Similarity score")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AskResponse(BaseModel):
    """Response for RAG query"""

    answer: str = Field(..., description="Generated answer")
    chunks: List[ChunkInfo] = Field(..., description="Retrieved chunks")
    model: str = Field(..., description="Model used")
    tokens_used: int = Field(..., description="Total tokens used")
    query_time_ms: int = Field(..., description="Query time in milliseconds")


class MemoryResponse(BaseModel):
    """Response for memory operations"""

    success: bool = Field(..., description="Operation success")
    data: Optional[Any] = Field(None, description="Returned data")
    message: Optional[str] = Field(None, description="Status message")


class NoteInfo(BaseModel):
    """Information about a note"""

    id: str = Field(..., description="Note ID")
    repo: Optional[str] = Field(None, description="Repository name")
    text: str = Field(..., description="Note text")
    tags: List[str] = Field(default_factory=list, description="Note tags")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")


class NotesResponse(BaseModel):
    """Response for notes operations"""

    success: bool = Field(..., description="Operation success")
    notes: Optional[List[NoteInfo]] = Field(None, description="Retrieved notes")
    message: Optional[str] = Field(None, description="Status message")


class SearchResponse(BaseModel):
    """Response for vector search"""

    chunks: List[ChunkInfo] = Field(..., description="Search results")
    total_found: int = Field(..., description="Total results found")
    query_time_ms: int = Field(..., description="Search time in milliseconds")


class IndexResponse(BaseModel):
    """Response for indexing operations"""

    success: bool = Field(..., description="Operation success")
    chunks_indexed: int = Field(..., description="Number of chunks indexed")
    files_processed: int = Field(..., description="Number of files processed")
    errors: List[str] = Field(
        default_factory=list, description="Any errors encountered"
    )
    indexing_time_ms: int = Field(..., description="Indexing time in milliseconds")


class HealthResponse(BaseModel):
    """Health check response"""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    services: Dict[str, bool] = Field(..., description="Service statuses")
    uptime_seconds: Optional[int] = Field(None, description="Service uptime")


class ErrorResponse(BaseModel):
    """Error response"""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )


class StatusResponse(BaseModel):
    """Generic status response"""

    success: bool = Field(..., description="Operation success")
    message: str = Field(..., description="Status message")
    data: Optional[Any] = Field(None, description="Additional data")
