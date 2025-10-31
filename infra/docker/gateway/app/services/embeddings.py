import os
import logging
from typing import List
from openai import OpenAI

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Service for generating text embeddings using GLM-4.6"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv(
            "OPENAI_BASE_URL", "https://api.z.ai/api/coding/paas/v4"
        )
        self.model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        # Initialize OpenAI client with GLM-4.6 endpoint
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        logger.info(f"Initialized embeddings service with model: {self.model}")

    async def health_check(self) -> bool:
        """Check if embeddings service is working"""
        try:
            # Test with a simple embedding
            response = self.client.embeddings.create(
                model=self.model, input="test", encoding_format="float"
            )
            return len(response.data[0].embedding) > 0
        except Exception as e:
            logger.error(f"Embeddings health check failed: {e}")
            return False

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query text"""
        try:
            response = self.client.embeddings.create(
                model=self.model, input=text, encoding_format="float"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            raise

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts (batch processing)"""
        try:
            response = self.client.embeddings.create(
                model=self.model, input=texts, encoding_format="float"
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            logger.error(f"Failed to embed texts: {e}")
            raise

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        try:
            # Test embedding to get dimension
            embedding = self.embed_query("test")
            return len(embedding)
        except Exception as e:
            logger.error(f"Failed to get embedding dimension: {e}")
            # Default dimension for text-embedding-3-small
            return 1536

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        try:
            import tiktoken

            # Use cl100k_base encoding (compatible with many models)
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except ImportError:
            # Fallback: rough estimate (1 token ≈ 4 characters for English)
            return len(text) // 4
        except Exception as e:
            logger.warning(f"Token estimation failed: {e}, using fallback")
            return len(text) // 4
