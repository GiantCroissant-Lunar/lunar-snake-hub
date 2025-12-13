from fastapi import FastAPI, HTTPException, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import logging
from contextlib import asynccontextmanager

from app.routers import ask, memory, notes, search
from app.services.qdrant_client import QdrantClient
from app.services.letta_client import LettaClient
from app.services.embeddings import EmbeddingsService
from app.services.indexing import IndexingService

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    global qdrant_client, letta_client, embeddings_service, indexing_service

    logger.info("Starting Context Gateway...")

    # Create data directory
    os.makedirs("/app/data", exist_ok=True)

    # Initialize core clients
    qdrant_client = QdrantClient()
    letta_client = LettaClient()
    embeddings_service = EmbeddingsService()
    indexing_service = IndexingService()

    # Initialize routers with services
    ask.init_services(embeddings_service, qdrant_client)
    memory.init_service(letta_client)
    search.init_services(embeddings_service, qdrant_client, indexing_service)

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
    ask.router, prefix="/ask", tags=["ask"], dependencies=[Security(verify_token)]
)
app.include_router(
    memory.router,
    prefix="/memory",
    tags=["memory"],
    dependencies=[Security(verify_token)],
)
app.include_router(
    notes.router, prefix="/notes", tags=["notes"], dependencies=[Security(verify_token)]
)
app.include_router(
    search.router,
    prefix="/search",
    tags=["search"],
    dependencies=[Security(verify_token)],
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
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5057)
