import time
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException

from app.models.requests import SearchRequest, IndexRequest, ReindexRequest
from app.models.responses import SearchResponse, ChunkInfo, IndexResponse
from app.services.embeddings import EmbeddingsService
from app.services.qdrant_client import QdrantClient
from app.services.indexing import IndexingService

logger = logging.getLogger(__name__)
router = APIRouter()

# Global services (will be injected by main.py)
embeddings_service = None
qdrant_client = None
indexing_service = None


def init_services(
    embeddings: EmbeddingsService, qdrant: QdrantClient, indexing: IndexingService
):
    """Initialize services (called from main.py)"""
    global embeddings_service, qdrant_client, indexing_service
    embeddings_service = embeddings
    qdrant_client = qdrant
    indexing_service = indexing


def build_filter(hints: list = None) -> dict:
    """Build Qdrant filter from file path hints"""
    if not hints:
        return None

    # Convert file paths to filter
    should_conditions = []
    for hint in hints:
        should_conditions.append(
            {"key": "file_path", "match": {"any": [hint, f"*{hint}", f"{hint}*"]}}
        )

    return {"must": [{"should": should_conditions}]}


@router.post("")
async def vector_search(
    request: SearchRequest,
) -> SearchResponse:
    """Vector search endpoint (without LLM generation)"""
    start_time = time.time()

    try:
        # 1. Generate query embedding
        query_vector = embeddings_service.embed_query(request.query)

        # 2. Search Qdrant for similar vectors
        search_results = qdrant_client.search(
            collection_name=request.repo or "default",
            query_vector=query_vector,
            limit=request.top_k,
            score_threshold=request.threshold,
            query_filter=build_filter(request.hints),
        )

        # 3. Format results
        chunks = []
        for result in search_results:
            payload = result["payload"]

            # Include content if requested
            content = payload["content"] if request.include_content else None

            chunks.append(
                ChunkInfo(
                    id=result["id"],
                    file_path=payload["file_path"],
                    start_line=payload.get("start_line"),
                    end_line=payload.get("end_line"),
                    content=content or "",
                    relevance=result["score"],
                    metadata={
                        k: v
                        for k, v in payload.items()
                        if k not in ["file_path", "content", "start_line", "end_line"]
                    },
                )
            )

        query_time_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"Vector search completed in {query_time_ms}ms, found {len(chunks)} results"
        )

        return SearchResponse(
            chunks=chunks, total_found=len(chunks), query_time_ms=query_time_ms
        )

    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")


@router.get("/collections")
async def list_collections() -> dict:
    """List all available collections"""
    try:
        collections = qdrant_client.list_collections()
        collection_info = {}

        for collection_name in collections:
            info = qdrant_client.get_collection_info(collection_name)
            if info:
                collection_info[collection_name] = {
                    "points_count": info.get("points_count", 0),
                    "vector_size": info.get("vector_size"),
                    "status": info.get("status"),
                }

        return {"collections": collections, "info": collection_info}

    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list collections: {e}")


@router.get("/collections/{collection_name}")
async def get_collection_info(
    collection_name: str,
) -> dict:
    """Get detailed information about a collection"""
    try:
        info = qdrant_client.get_collection_info(collection_name)
        if info:
            return info
        else:
            raise HTTPException(
                status_code=404, detail=f"Collection not found: {collection_name}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get collection info: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get collection info: {e}"
        )


@router.post("/index")
async def index_repository(
    request: IndexRequest,
) -> IndexResponse:
    """Index a repository into Qdrant"""
    start_time = time.time()

    try:
        # Check if collection exists
        collection_exists = qdrant_client.collection_exists(request.collection_name)

        if collection_exists and not request.force_reindex:
            return IndexResponse(
                success=False,
                chunks_indexed=0,
                files_processed=0,
                errors=[
                    f"Collection {request.collection_name} already exists. Use force_reindex=true to overwrite."
                ],
                indexing_time_ms=0,
            )

        # Get embedding dimension
        vector_size = embeddings_service.get_embedding_dimension()

        # Create or recreate collection
        if collection_exists:
            qdrant_client.delete_collection(request.collection_name)

        if not qdrant_client.create_collection(request.collection_name, vector_size):
            raise HTTPException(status_code=500, detail="Failed to create collection")

        # Index repository
        indexing_result = await indexing_service.index_repository(
            request.repo_path, request.collection_name, request.force_reindex
        )

        if not indexing_result["success"]:
            return IndexResponse(
                success=False,
                chunks_indexed=0,
                files_processed=0,
                errors=[indexing_result["error"]],
                indexing_time_ms=indexing_result.get("indexing_time_ms", 0),
            )

        # Generate embeddings for all chunks
        chunks = indexing_result["chunks"]
        batch_size = 100
        all_points = []
        errors = []

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [chunk["content"] for chunk in batch]

            try:
                embeddings = embeddings_service.embed_texts(texts)

                for j, (chunk, embedding) in enumerate(zip(batch, embeddings)):
                    point = {
                        "id": chunk["id"],
                        "vector": embedding,
                        "payload": chunk.get("payload", {}),
                    }
                    all_points.append(point)

            except Exception as e:
                error_msg = f"Failed to embed batch {i // batch_size}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Store embeddings in Qdrant
        if all_points:
            if not qdrant_client.upsert_points(request.collection_name, all_points):
                errors.append("Failed to store embeddings in Qdrant")

        indexing_time_ms = int((time.time() - start_time) * 1000)

        return IndexResponse(
            success=len(errors) == 0,
            chunks_indexed=len(all_points),
            files_processed=indexing_result["files_processed"],
            errors=errors,
            indexing_time_ms=indexing_time_ms,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Repository indexing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {e}")


@router.post("/reindex")
async def reindex_changed_files(
    request: ReindexRequest,
) -> IndexResponse:
    """Reindex specific changed files"""
    start_time = time.time()

    try:
        # Check if collection exists
        if not qdrant_client.collection_exists(request.collection_name or request.repo):
            raise HTTPException(
                status_code=404,
                detail=f"Collection not found: {request.collection_name or request.repo}",
            )

        collection_name = request.collection_name or request.repo

        # Process changed files
        chunks_processed = 0
        errors = []
        points_to_add = []
        point_ids_to_delete = []

        for file_path in request.changed:
            try:
                # Delete existing points for this file
                # Note: In a real implementation, you'd query for exact matches
                # For now, we'll use a simple pattern
                point_ids_to_delete.append(f"{file_path}:*")

                # Chunk and embed the file
                full_path = Path(f"/repos/{request.repo}/{file_path}")
                if full_path.exists():
                    file_chunks = indexing_service.chunk_file(full_path)
                    texts = [chunk["content"] for chunk in file_chunks]

                    if texts:
                        embeddings = embeddings_service.embed_texts(texts)

                        for chunk, embedding in zip(file_chunks, embeddings):
                            point = {
                                "id": chunk["id"],
                                "vector": embedding,
                                "payload": chunk.get("payload", {}),
                            }
                            points_to_add.append(point)
                            chunks_processed += 1

            except Exception as e:
                error_msg = f"Failed to process file {file_path}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Delete old points (simplified - in real implementation you'd query first)
        if point_ids_to_delete:
            # This is a simplified approach
            logger.info(
                f"Would delete points for {len(point_ids_to_delete)} file patterns"
            )

        # Add new points
        if points_to_add:
            if not qdrant_client.upsert_points(collection_name, points_to_add):
                errors.append("Failed to store new embeddings in Qdrant")

        indexing_time_ms = int((time.time() - start_time) * 1000)

        return IndexResponse(
            success=len(errors) == 0,
            chunks_indexed=chunks_processed,
            files_processed=len(request.changed),
            errors=errors,
            indexing_time_ms=indexing_time_ms,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reindexing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reindexing failed: {e}")
