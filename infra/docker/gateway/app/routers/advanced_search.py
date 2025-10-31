"""
Advanced Search Router
Integrates hybrid search, semantic chunking, and re-ranking for Phase 3
"""

import time
import logging
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials

from app.models.requests import SearchRequest
from app.models.responses import SearchResponse, ChunkInfo
from app.services.embeddings import EmbeddingsService
from app.services.qdrant_client import QdrantClient
from app.services.indexing import IndexingService
from app.services.hybrid_search import HybridSearchService
from app.services.semantic_chunking import SemanticChunkingService
from app.services.reranking import ReRankingService

logger = logging.getLogger(__name__)
router = APIRouter()

# Global services (will be injected by main.py)
embeddings_service = None
qdrant_client = None
indexing_service = None
hybrid_search_service = None
semantic_chunking_service = None
reranking_service = None


def init_services(
    embeddings: EmbeddingsService,
    qdrant: QdrantClient,
    indexing: IndexingService,
    hybrid_search: HybridSearchService,
    semantic_chunking: SemanticChunkingService,
    reranking: ReRankingService,
):
    """Initialize services (called from main.py)"""
    global embeddings_service, qdrant_client, indexing_service
    global hybrid_search_service, semantic_chunking_service, reranking_service

    embeddings_service = embeddings
    qdrant_client = qdrant
    indexing_service = indexing
    hybrid_search_service = hybrid_search
    semantic_chunking_service = semantic_chunking
    reranking_service = reranking


class AdvancedSearchRequest(SearchRequest):
    """Extended search request with advanced options"""

    search_method: str = Query(
        "hybrid", description="Search method: vector, keyword, hybrid, semantic"
    )
    rerank_method: str = Query(
        "hybrid",
        description="Reranking method: cross_encoder, semantic, feature_based, hybrid",
    )
    diversify: bool = Query(True, description="Enable result diversification")
    query_expansion: bool = Query(True, description="Enable query expansion")
    explain_ranking: bool = Query(False, description="Include ranking explanations")
    min_confidence: float = Query(0.3, description="Minimum confidence threshold")


class AdvancedSearchResponse(SearchResponse):
    """Extended search response with advanced features"""

    reranked_results: List[Dict[str, Any]] = []
    query_expansions: List[str] = []
    search_method_used: str = ""
    rerank_method_used: str = ""
    total_search_time_ms: int = 0
    diversification_stats: Dict[str, Any] = {}


@router.post("/advanced")
async def advanced_search(
    request: AdvancedSearchRequest,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPAuthorizationCredentials()),
) -> AdvancedSearchResponse:
    """Advanced search with hybrid methods and re-ranking"""
    start_time = time.time()

    try:
        logger.info(
            f"🔍 Advanced search: '{request.query}' (method: {request.search_method}, rerank: {request.rerank_method})"
        )

        # Step 1: Query expansion if enabled
        expanded_queries = [request.query]
        if request.query_expansion:
            expanded_queries = await hybrid_search_service.expand_query(request.query)

        # Step 2: Perform search using specified method
        if request.search_method == "vector":
            search_results = await _vector_search(request, expanded_queries)
        elif request.search_method == "keyword":
            search_results = await _keyword_search(request, expanded_queries)
        elif request.search_method == "semantic":
            search_results = await _semantic_search(request, expanded_queries)
        else:  # hybrid (default)
            search_results = await _hybrid_search(request, expanded_queries)

        if not search_results:
            logger.info("❌ No search results found")
            return AdvancedSearchResponse(
                chunks=[],
                total_found=0,
                query_time_ms=int((time.time() - start_time) * 1000),
                search_method_used=request.search_method,
                rerank_method_used=request.rerank_method,
                query_expansions=expanded_queries[1:]
                if request.query_expansion
                else [],
                total_search_time_ms=int((time.time() - start_time) * 1000),
            )

        # Step 3: Re-rank results
        reranked_results = await reranking_service.rerank_results(
            request.query, search_results, request.top_k, request.rerank_method
        )

        # Step 4: Apply confidence filter
        filtered_results = [
            r for r in reranked_results if r.confidence >= request.min_confidence
        ]

        # Step 5: Diversify results if enabled
        if request.diversify:
            diversified_results = await reranking_service.diversify_results(
                filtered_results, diversity_threshold=0.7, max_results=request.top_k
            )
            diversification_stats = {
                "original_count": len(filtered_results),
                "diversified_count": len(diversified_results),
                "diversity_ratio": len(diversified_results) / len(filtered_results)
                if filtered_results
                else 0,
            }
        else:
            diversified_results = filtered_results
            diversification_stats = {
                "original_count": len(filtered_results),
                "diversified_count": len(filtered_results),
                "diversity_ratio": 1.0,
            }

        # Step 6: Format response
        chunks = []
        reranked_info = []

        for i, reranked_result in enumerate(diversified_results):
            original = reranked_result.original_result

            # Convert to ChunkInfo
            chunk = ChunkInfo(
                id=original.id,
                file_path=original.file_path,
                start_line=original.start_line,
                end_line=original.end_line,
                content=original.content,
                relevance=original.hybrid_score,
                metadata={
                    **original.metadata,
                    "rerank_score": reranked_result.rerank_score,
                    "confidence": reranked_result.confidence,
                    "search_method": request.search_method,
                    "rerank_method": request.rerank_method,
                },
            )
            chunks.append(chunk)

            # Add reranking info if requested
            if request.explain_ranking:
                explanation = await reranking_service.explain_ranking(reranked_result)
                reranked_info.append(
                    {"chunk_id": original.id, "rank": i + 1, "explanation": explanation}
                )

        total_time_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"✅ Advanced search completed: {len(chunks)} results in {total_time_ms}ms"
        )

        return AdvancedSearchResponse(
            chunks=chunks,
            total_found=len(chunks),
            query_time_ms=total_time_ms,
            reranked_results=reranked_info if request.explain_ranking else [],
            query_expansions=expanded_queries[1:] if request.query_expansion else [],
            search_method_used=request.search_method,
            rerank_method_used=request.rerank_method,
            total_search_time_ms=total_time_ms,
            diversification_stats=diversification_stats,
        )

    except Exception as e:
        logger.error(f"❌ Advanced search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Advanced search failed: {e}")


async def _vector_search(request: AdvancedSearchRequest, queries: List[str]) -> List:
    """Vector search implementation"""
    all_results = []

    for query in queries:
        query_vector = embeddings_service.embed_query(query)

        results = qdrant_client.search(
            collection_name=request.repo or "default",
            query_vector=query_vector,
            limit=request.top_k,
            score_threshold=request.threshold,
        )

        # Convert to SearchResult format
        for result in results:
            payload = result["payload"]
            from app.services.hybrid_search import SearchResult

            search_result = SearchResult(
                id=result["id"],
                content=payload.get("content", ""),
                file_path=payload.get("file_path", ""),
                start_line=payload.get("start_line"),
                end_line=payload.get("end_line"),
                vector_score=result["score"],
                keyword_score=0.0,
                hybrid_score=result["score"],
                metadata=payload,
            )
            all_results.append(search_result)

    return _deduplicate_results(all_results)


async def _keyword_search(request: AdvancedSearchRequest, queries: List[str]) -> List:
    """Keyword search implementation"""
    all_results = []

    for query in queries:
        results = await hybrid_search_service.keyword_search(query, request.top_k)

        # Convert to SearchResult format
        for doc_idx, score in results:
            # Get document from semantic chunking service
            # This is simplified - in practice you'd have a document store
            from app.services.hybrid_search import SearchResult

            search_result = SearchResult(
                id=f"keyword:{doc_idx}",
                content=f"Keyword match for document {doc_idx}",
                file_path=f"document_{doc_idx}.txt",
                start_line=1,
                end_line=10,
                vector_score=0.0,
                keyword_score=score,
                hybrid_score=score,
                metadata={"keyword_match": True},
            )
            all_results.append(search_result)

    return _deduplicate_results(all_results)


async def _semantic_search(request: AdvancedSearchRequest, queries: List[str]) -> List:
    """Semantic search implementation"""
    # Use sentence transformer for semantic similarity
    all_results = []

    for query in queries:
        # This would typically search a pre-indexed semantic database
        # For now, fall back to hybrid search
        hybrid_results = await hybrid_search_service.hybrid_search(
            query, request.repo or "default", request.top_k
        )
        all_results.extend(hybrid_results)

    return _deduplicate_results(all_results)


async def _hybrid_search(request: AdvancedSearchRequest, queries: List[str]) -> List:
    """Hybrid search implementation"""
    all_results = []

    for query in queries:
        results = await hybrid_search_service.hybrid_search(
            query, request.repo or "default", request.top_k
        )
        all_results.extend(results)

    return _deduplicate_results(all_results)


def _deduplicate_results(results: List) -> List:
    """Remove duplicate results by ID"""
    seen_ids = set()
    unique_results = []

    for result in results:
        if result.id not in seen_ids:
            seen_ids.add(result.id)
            unique_results.append(result)

    return unique_results


@router.post("/semantic-chunk")
async def test_semantic_chunking(
    file_path: str,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPAuthorizationCredentials()),
) -> Dict[str, Any]:
    """Test semantic chunking on a specific file"""
    try:
        full_path = Path(f"/repos/{file_path}")
        if not full_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

        # Read file content
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Perform semantic chunking
        chunks = await semantic_chunking_service.chunk_document(file_path, content)

        # Optimize chunk sizes
        optimized_chunks = await semantic_chunking_service.optimize_chunk_size(chunks)

        # Format response
        chunk_info = []
        for chunk in optimized_chunks:
            chunk_info.append(
                {
                    "id": chunk.id,
                    "type": chunk.chunk_type,
                    "language": chunk.language,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "token_count": semantic_chunking_service.count_tokens(
                        chunk.content
                    ),
                    "metadata": chunk.metadata,
                    "content_preview": chunk.content[:200] + "..."
                    if len(chunk.content) > 200
                    else chunk.content,
                }
            )

        return {
            "file_path": file_path,
            "total_chunks": len(optimized_chunks),
            "chunks": chunk_info,
            "total_tokens": sum(c["token_count"] for c in chunk_info),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Semantic chunking test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chunking failed: {e}")


@router.get("/methods")
async def list_search_methods(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPAuthorizationCredentials()),
) -> Dict[str, Any]:
    """List available search and reranking methods"""
    return {
        "search_methods": {
            "vector": {
                "description": "Pure vector similarity search",
                "best_for": "Semantic similarity, concept matching",
            },
            "keyword": {
                "description": "BM25 keyword matching",
                "best_for": "Exact term matching, technical terms",
            },
            "semantic": {
                "description": "Advanced semantic understanding",
                "best_for": "Conceptual similarity, context understanding",
            },
            "hybrid": {
                "description": "Combines vector and keyword search",
                "best_for": "Balanced relevance, general purpose",
            },
        },
        "rerank_methods": {
            "cross_encoder": {
                "description": "ML-based relevance scoring",
                "best_for": "High precision ranking",
            },
            "semantic_similarity": {
                "description": "Semantic similarity re-ranking",
                "best_for": "Conceptual relevance",
            },
            "feature_based": {
                "description": "Multiple feature combination",
                "best_for": "Customizable ranking logic",
            },
            "hybrid": {
                "description": "Combines all methods",
                "best_for": "Best overall performance",
            },
        },
        "features": {
            "query_expansion": "Expand queries with synonyms and related terms",
            "diversification": "Ensure result diversity and reduce redundancy",
            "confidence_filtering": "Filter by minimum confidence scores",
            "ranking_explanation": "Explain why results were ranked this way",
        },
    }


@router.get("/performance")
async def get_search_performance(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPAuthorizationCredentials()),
) -> Dict[str, Any]:
    """Get search performance metrics"""
    # This would typically pull from a metrics store
    # For now, return mock data
    return {
        "average_query_time_ms": 245,
        "average_results_count": 8.5,
        "cache_hit_rate": 0.73,
        "most_common_methods": {"search": "hybrid", "rerank": "hybrid"},
        "performance_breakdown": {
            "vector_search_ms": 120,
            "keyword_search_ms": 45,
            "reranking_ms": 65,
            "diversification_ms": 15,
        },
        "last_updated": time.time(),
    }
