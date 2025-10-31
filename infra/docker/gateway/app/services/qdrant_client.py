import os
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient as QdrantSDKClient, models
from qdrant_client.http.models import Distance, VectorParams

logger = logging.getLogger(__name__)


class QdrantClient:
    """Client for Qdrant vector database operations"""

    def __init__(self):
        self.url = os.getenv("QDRANT_URL", "http://qdrant:6333")
        self.api_key = os.getenv("QDRANT_API_KEY")  # Optional

        # Initialize Qdrant client
        self.client = QdrantSDKClient(url=self.url, api_key=self.api_key)

        logger.info(f"Initialized Qdrant client with URL: {self.url}")

    async def health_check(self) -> bool:
        """Check if Qdrant is accessible"""
        try:
            collections = self.client.get_collections().collections
            logger.info(
                f"Qdrant health check passed, found {len(collections)} collections"
            )
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False

    def create_collection(self, collection_name: str, vector_size: int) -> bool:
        """Create a new collection"""
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            logger.info(f"Created collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            return False

    def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists"""
        try:
            collections = self.client.get_collections().collections
            return any(c.name == collection_name for c in collections)
        except Exception as e:
            logger.error(f"Failed to check collection existence: {e}")
            return False

    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection"""
        try:
            self.client.delete_collection(collection_name=collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False

    def upsert_points(self, collection_name: str, points: List[Dict[str, Any]]) -> bool:
        """Insert or update points in collection"""
        try:
            # Convert dict points to Qdrant PointStruct
            qdrant_points = []
            for point in points:
                qdrant_points.append(
                    models.PointStruct(
                        id=point["id"], vector=point["vector"], payload=point["payload"]
                    )
                )

            self.client.upsert(collection_name=collection_name, points=qdrant_points)
            logger.info(f"Upserted {len(points)} points to {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to upsert points to {collection_name}: {e}")
            return False

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: float = 0.7,
        query_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        try:
            # Build filter if provided
            filter_obj = None
            if query_filter:
                filter_obj = models.Filter(**query_filter)

            # Perform search
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=filter_obj,
                with_payload=True,
                with_vectors=False,
            )

            # Convert results to standard format
            formatted_results = []
            for result in results:
                formatted_results.append(
                    {
                        "id": str(result.id),
                        "score": result.score,
                        "payload": result.payload,
                    }
                )

            logger.info(
                f"Search in {collection_name} returned {len(formatted_results)} results"
            )
            return formatted_results

        except Exception as e:
            logger.error(f"Failed to search in {collection_name}: {e}")
            return []

    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a collection"""
        try:
            info = self.client.get_collection(collection_name=collection_name)
            return {
                "name": collection_name,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "points_count": info.points_count,
                "status": info.status,
                "optimizer_status": info.optimizer_status,
                "vector_size": info.config.params.vectors.size
                if info.config.params.vectors
                else None,
            }
        except Exception as e:
            logger.error(f"Failed to get collection info for {collection_name}: {e}")
            return None

    def list_collections(self) -> List[str]:
        """List all collection names"""
        try:
            collections = self.client.get_collections().collections
            return [c.name for c in collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []

    def delete_points(self, collection_name: str, point_ids: List[str]) -> bool:
        """Delete specific points from collection"""
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(points=point_ids),
            )
            logger.info(f"Deleted {len(point_ids)} points from {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete points from {collection_name}: {e}")
            return False

    def count_points(self, collection_name: str) -> int:
        """Count points in collection"""
        try:
            result = self.client.count(collection_name=collection_name)
            return result.count
        except Exception as e:
            logger.error(f"Failed to count points in {collection_name}: {e}")
            return 0
