import time
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.models.requests import AskRequest
from app.models.responses import AskResponse, ChunkInfo
from app.services.embeddings import EmbeddingsService
from app.services.qdrant_client import QdrantClient

logger = logging.getLogger(__name__)
router = APIRouter()

# Global services (will be injected by main.py)
embeddings_service = None
qdrant_client = None


def init_services(embeddings: EmbeddingsService, qdrant: QdrantClient):
    """Initialize services (called from main.py)"""
    global embeddings_service, qdrant_client
    embeddings_service = embeddings
    qdrant_client = qdrant


async def call_glm_4_6(prompt: str) -> str:
    """Call GLM-4.6 for text generation"""
    try:
        import openai

        client = openai.OpenAI(
            api_key=embeddings_service.api_key, base_url=embeddings_service.base_url
        )

        response = client.chat.completions.create(
            model="glm-4.6",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Answer based on the provided context.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
            temperature=0.1,
        )

        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Failed to call GLM-4.6: {e}")
        raise HTTPException(status_code=500, detail=f"LLM call failed: {e}")


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
async def ask_rag(
    request: AskRequest,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPAuthorizationCredentials()),
) -> AskResponse:
    """RAG query endpoint"""
    start_time = time.time()

    try:
        # 1. Generate query embedding
        query_vector = embeddings_service.embed_query(request.query)

        # 2. Search Qdrant for relevant chunks
        search_results = qdrant_client.search(
            collection_name=request.repo or "default",
            query_vector=query_vector,
            limit=request.top_k,
            score_threshold=request.threshold,
            query_filter=build_filter(request.hints),
        )

        if not search_results:
            logger.warning(f"No results found for query: {request.query}")
            return AskResponse(
                answer="I couldn't find relevant information to answer your question.",
                chunks=[],
                model="glm-4.6",
                tokens_used=embeddings_service.estimate_tokens(request.query),
                query_time_ms=int((time.time() - start_time) * 1000),
            )

        # 3. Build context from chunks
        context_parts = []
        chunks = []

        for result in search_results:
            payload = result["payload"]
            context_parts.append(f"File: {payload['file_path']}\n{payload['content']}")

            chunks.append(
                ChunkInfo(
                    id=result["id"],
                    file_path=payload["file_path"],
                    start_line=payload.get("start_line"),
                    end_line=payload.get("end_line"),
                    content=payload["content"],
                    relevance=result["score"],
                    metadata={
                        k: v
                        for k, v in payload.items()
                        if k not in ["file_path", "content", "start_line", "end_line"]
                    },
                )
            )

        context = "\n\n---\n\n".join(context_parts)

        # 4. Call GLM-4.6 with context
        prompt = f"""Based on the following context, please answer this question: {request.query}

Context:
{context}

Please provide a comprehensive answer based on the context above. If the context doesn't contain enough information to fully answer the question, please indicate what information is missing."""

        answer = await call_glm_4_6(prompt)

        # 5. Calculate tokens used
        total_tokens = (
            embeddings_service.estimate_tokens(request.query)
            + embeddings_service.estimate_tokens(context)
            + embeddings_service.estimate_tokens(answer)
        )

        query_time_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"RAG query completed in {query_time_ms}ms, found {len(chunks)} chunks"
        )

        return AskResponse(
            answer=answer,
            chunks=chunks,
            model="glm-4.6",
            tokens_used=total_tokens,
            query_time_ms=query_time_ms,
        )

    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")
