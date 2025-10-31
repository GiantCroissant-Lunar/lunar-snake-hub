from fastapi import FastAPI, HTTPException, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import logging
from contextlib import asynccontextmanager

from app.routers import ask, memory, notes, search, advanced_search
from app.routers import webhooks
from app.routers import performance
from app.services.qdrant_client import QdrantClient
from app.services.letta_client import LettaClient
from app.services.embeddings import EmbeddingsService
from app.services.indexing import IndexingService
from app.services.hybrid_search import HybridSearchService
from app.services.semantic_chunking import SemanticChunkingService
from app.services.reranking import ReRankingService
from app.services.webhook_receiver import WebhookReceiver, WebhookProcessor
from app.services.enhanced_indexing import EnhancedIndexingService
from app.services.caching import CachingService, CacheConfig
from app.services.connection_pool import PoolConfig, init_pool_service
from app.services.performance_monitor import init_performance_monitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()
GATEWAY_TOKEN = os.getenv("GATEWAY_TOKEN")

# Global clients
qdrant_client = None
letta_client = None
embeddings_service = None
indexing_service = None
hybrid_search_service = None
semantic_chunking_service = None
reranking_service = None
enhanced_indexing_service = None
webhook_receiver = None
webhook_processor = None

# Performance optimization services
cache_service = None
pool_service = None
performance_monitor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    global qdrant_client, letta_client, embeddings_service, indexing_service
    global hybrid_search_service, semantic_chunking_service, reranking_service
    global enhanced_indexing_service, webhook_receiver, webhook_processor
    global cache_service, pool_service, performance_monitor

    logger.info("Starting Context Gateway...")

    # Create data directory
    os.makedirs("/app/data", exist_ok=True)

    # Initialize core clients
    qdrant_client = QdrantClient()
    letta_client = LettaClient()
    embeddings_service = EmbeddingsService()
    indexing_service = IndexingService()

    # Initialize Phase 3 services
    semantic_chunking_service = SemanticChunkingService()
    hybrid_search_service = HybridSearchService(qdrant_client, embeddings_service)
    reranking_service = ReRankingService()
    enhanced_indexing_service = EnhancedIndexingService(
        indexing_service=indexing_service,
        semantic_chunking=semantic_chunking_service,
        embeddings_service=embeddings_service,
        qdrant_client=qdrant_client,
    )

    # Initialize webhook services
    webhook_secret = os.getenv("WEBHOOK_SECRET", "default-secret")
    webhook_receiver = WebhookReceiver(webhook_secret)
    webhook_processor = WebhookProcessor(webhook_receiver, enhanced_indexing_service)

    # Initialize performance optimization services
    cache_config = CacheConfig(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        enable_redis=os.getenv("ENABLE_REDIS_CACHE", "true").lower() == "true",
        enable_memory=os.getenv("ENABLE_MEMORY_CACHE", "true").lower() == "true",
    )
    cache_service = CachingService(cache_config)
    await cache_service.initialize()

    pool_config = PoolConfig(
        postgres_min_size=int(os.getenv("POSTGRES_MIN_SIZE", "5")),
        postgres_max_size=int(os.getenv("POSTGRES_MAX_SIZE", "20")),
        redis_max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "20")),
        http_max_connections=int(os.getenv("HTTP_MAX_CONNECTIONS", "100")),
    )
    pool_service = await init_pool_service(
        config=pool_config,
        postgres_url=os.getenv("POSTGRES_URL"),
        redis_url=os.getenv("REDIS_URL"),
        qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
    )

    performance_monitor = await init_performance_monitor(
        retention_hours=int(os.getenv("METRICS_RETENTION_HOURS", "24")),
        max_metrics_per_type=int(os.getenv("MAX_METRICS_PER_TYPE", "10000")),
    )

    # Initialize routers with services
    ask.init_services(embeddings_service, qdrant_client)
    memory.init_service(letta_client)
    search.init_services(embeddings_service, qdrant_client, indexing_service)
    advanced_search.init_services(
        embeddings_service,
        qdrant_client,
        indexing_service,
        hybrid_search_service,
        semantic_chunking_service,
        reranking_service,
    )
    webhooks.init_services(webhook_processor, enhanced_indexing_service)
    performance.init_services(performance_monitor, pool_service, cache_service)

    # Test connections
    try:
        await qdrant_client.health_check()
        logger.info("✅ Qdrant client connected")
    except Exception as e:
        logger.error(f"❌ Qdrant connection failed: {e}")

    try:
        await letta_client.health_check()
        logger.info("✅ Letta client connected")
    except Exception as e:
        logger.error(f"❌ Letta connection failed: {e}")

    try:
        await embeddings_service.health_check()
        logger.info("✅ Embeddings service ready")
    except Exception as e:
        logger.error(f"❌ Embeddings service failed: {e}")

    yield

    # Cleanup
    logger.info("Shutting down Context Gateway...")


# Create FastAPI app
app = FastAPI(
    title="Context Gateway",
    description="RAG and Memory API for AI Agents",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify gateway token"""
    if not GATEWAY_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gateway token not configured",
        )

    if credentials.credentials != GATEWAY_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    return credentials.credentials


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "qdrant": qdrant_client is not None,
            "letta": letta_client is not None,
            "embeddings": embeddings_service is not None,
        },
    }


# Include routers with token verification
app.include_router(
    ask.router, prefix="/ask", tags=["ask"], dependencies=[Security(security)]
)
app.include_router(
    memory.router, prefix="/memory", tags=["memory"], dependencies=[Security(security)]
)
app.include_router(
    notes.router, prefix="/notes", tags=["notes"], dependencies=[Security(security)]
)
app.include_router(
    search.router, prefix="/search", tags=["search"], dependencies=[Security(security)]
)
app.include_router(
    advanced_search.router,
    prefix="/advanced",
    tags=["advanced-search"],
    dependencies=[Security(security)],
)
app.include_router(
    webhooks.router, prefix="/webhooks", tags=["webhooks"]
)  # Webhooks have their own auth
app.include_router(
    performance.router,
    prefix="/performance",
    tags=["performance"],
    dependencies=[Security(security)],
)


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Context Gateway API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "ask": "/ask",
            "memory": "/memory",
            "notes": "/notes",
            "search": "/search",
            "advanced": "/advanced",
            "webhooks": "/webhooks",
            "performance": "/performance",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5057)
