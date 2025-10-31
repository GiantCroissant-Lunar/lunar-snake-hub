"""
Connection Pool Service - Optimized database connection pooling
"""

import os
import time
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
import logging
import asyncpg
import aioredis
from qdrant_client.async_qdrant_client import AsyncQdrantClient
import httpx

logger = logging.getLogger(__name__)


@dataclass
class PoolConfig:
    """Connection pool configuration"""

    # PostgreSQL/asyncpg config
    postgres_min_size: int = 5
    postgres_max_size: int = 20
    postgres_max_queries: int = 50000
    postgres_max_inactive_connection_lifetime: float = 300.0

    # Redis config
    redis_max_connections: int = 20
    redis_pool_timeout: float = 5.0

    # HTTP client config
    http_max_connections: int = 100
    http_max_keepalive_connections: int = 20
    http_keepalive_expiry: float = 5.0
    http_timeout: float = 30.0

    # Qdrant config
    qdrant_timeout: float = 30.0
    qdrant_prefetch_count: int = 10


@dataclass
class PoolStats:
    """Connection pool statistics"""

    active_connections: int = 0
    idle_connections: int = 0
    total_connections: int = 0
    requests_served: int = 0
    errors: int = 0
    avg_response_time: float = 0.0
    last_reset: float = field(default_factory=time.time)


class ConnectionPoolService:
    """Optimized connection pooling for all services"""

    def __init__(self, config: PoolConfig):
        self.config = config
        self.postgres_pool: Optional[asyncpg.Pool] = None
        self.redis_pool: Optional[aioredis.ConnectionPool] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        self.qdrant_client: Optional[AsyncQdrantClient] = None

        # Statistics
        self.stats = {
            "postgres": PoolStats(),
            "redis": PoolStats(),
            "http": PoolStats(),
            "qdrant": PoolStats(),
        }

        # Health tracking
        self.health_status = {
            "postgres": False,
            "redis": False,
            "http": False,
            "qdrant": False,
        }

    async def initialize(
        self,
        postgres_url: Optional[str] = None,
        redis_url: Optional[str] = None,
        qdrant_url: Optional[str] = None,
    ):
        """Initialize all connection pools"""

        # Initialize PostgreSQL pool
        if postgres_url:
            await self._init_postgres_pool(postgres_url)

        # Initialize Redis pool
        if redis_url:
            await self._init_redis_pool(redis_url)

        # Initialize HTTP client
        await self._init_http_client()

        # Initialize Qdrant client
        if qdrant_url:
            await self._init_qdrant_client(qdrant_url)

        logger.info("✅ Connection pools initialized")

    async def _init_postgres_pool(self, url: str):
        """Initialize PostgreSQL connection pool"""
        try:
            self.postgres_pool = await asyncpg.create_pool(
                url,
                min_size=self.config.postgres_min_size,
                max_size=self.config.postgres_max_size,
                max_queries=self.config.postgres_max_queries,
                max_inactive_connection_lifetime=self.config.postgres_max_inactive_connection_lifetime,
                command_timeout=self.config.http_timeout,
                server_settings={
                    "application_name": "context_gateway",
                    "jit": "off",  # Disable JIT for better performance
                },
            )

            # Test connection
            async with self.postgres_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            self.health_status["postgres"] = True
            self.stats["postgres"].total_connections = self.config.postgres_min_size
            self.stats["postgres"].idle_connections = self.config.postgres_min_size

            logger.info(
                f"✅ PostgreSQL pool initialized ({self.config.postgres_min_size}-{self.config.postgres_max_size} connections)"
            )

        except Exception as e:
            logger.error(f"❌ PostgreSQL pool initialization failed: {e}")
            self.health_status["postgres"] = False

    async def _init_redis_pool(self, url: str):
        """Initialize Redis connection pool"""
        try:
            self.redis_pool = aioredis.ConnectionPool.from_url(
                url,
                max_connections=self.config.redis_max_connections,
                socket_timeout=self.config.redis_pool_timeout,
                socket_connect_timeout=self.config.redis_pool_timeout,
                retry_on_timeout=True,
                health_check_interval=30,
            )

            # Test connection
            redis_client = aioredis.Redis(connection_pool=self.redis_pool)
            await redis_client.ping()

            self.health_status["redis"] = True
            self.stats["redis"].total_connections = self.config.redis_max_connections

            logger.info(
                f"✅ Redis pool initialized ({self.config.redis_max_connections} connections)"
            )

        except Exception as e:
            logger.error(f"❌ Redis pool initialization failed: {e}")
            self.health_status["redis"] = False

    async def _init_http_client(self):
        """Initialize HTTP client with connection pooling"""
        try:
            limits = httpx.Limits(
                max_connections=self.config.http_max_connections,
                max_keepalive_connections=self.config.http_max_keepalive_connections,
            )

            timeout = httpx.Timeout(
                connect=self.config.http_timeout,
                read=self.config.http_timeout,
                write=self.config.http_timeout,
                pool=self.config.http_timeout,
            )

            self.http_client = httpx.AsyncClient(
                limits=limits,
                timeout=timeout,
                http2=True,  # Enable HTTP/2 for better performance
                follow_redirects=True,
            )

            self.health_status["http"] = True
            self.stats["http"].total_connections = self.config.http_max_connections

            logger.info(
                f"✅ HTTP client initialized ({self.config.http_max_connections} connections)"
            )

        except Exception as e:
            logger.error(f"❌ HTTP client initialization failed: {e}")
            self.health_status["http"] = False

    async def _init_qdrant_client(self, url: str):
        """Initialize Qdrant client with optimized settings"""
        try:
            self.qdrant_client = AsyncQdrantClient(
                url=url,
                timeout=self.config.qdrant_timeout,
                prefer_grpc=True,  # Use gRPC for better performance
                api_key=os.getenv("QDRANT_API_KEY")
                if os.getenv("QDRANT_API_KEY")
                else None,
            )

            # Test connection
            await self.qdrant_client.get_collections()

            self.health_status["qdrant"] = True

            logger.info("✅ Qdrant client initialized")

        except Exception as e:
            logger.error(f"❌ Qdrant client initialization failed: {e}")
            self.health_status["qdrant"] = False

    @asynccontextmanager
    async def get_postgres_connection(self):
        """Get PostgreSQL connection from pool"""
        if not self.postgres_pool or not self.health_status["postgres"]:
            raise RuntimeError("PostgreSQL pool not available")

        start_time = time.time()
        stats = self.stats["postgres"]

        try:
            stats.active_connections += 1
            stats.idle_connections -= 1
            stats.requests_served += 1

            async with self.postgres_pool.acquire() as conn:
                yield conn

        except Exception:
            stats.errors += 1
            raise
        finally:
            stats.active_connections -= 1
            stats.idle_connections += 1

            # Update average response time
            response_time = time.time() - start_time
            stats.avg_response_time = (
                stats.avg_response_time * (stats.requests_served - 1) + response_time
            ) / stats.requests_served

    @asynccontextmanager
    async def get_redis_client(self):
        """Get Redis client from pool"""
        if not self.redis_pool or not self.health_status["redis"]:
            raise RuntimeError("Redis pool not available")

        start_time = time.time()
        stats = self.stats["redis"]

        try:
            stats.active_connections += 1
            stats.requests_served += 1

            client = aioredis.Redis(connection_pool=self.redis_pool)
            yield client

        except Exception:
            stats.errors += 1
            raise
        finally:
            stats.active_connections -= 1

            # Update average response time
            response_time = time.time() - start_time
            stats.avg_response_time = (
                stats.avg_response_time * (stats.requests_served - 1) + response_time
            ) / stats.requests_served

    @asynccontextmanager
    async def get_http_client(self):
        """Get HTTP client"""
        if not self.http_client or not self.health_status["http"]:
            raise RuntimeError("HTTP client not available")

        start_time = time.time()
        stats = self.stats["http"]

        try:
            stats.active_connections += 1
            stats.requests_served += 1

            yield self.http_client

        except Exception:
            stats.errors += 1
            raise
        finally:
            stats.active_connections -= 1

            # Update average response time
            response_time = time.time() - start_time
            stats.avg_response_time = (
                stats.avg_response_time * (stats.requests_served - 1) + response_time
            ) / stats.requests_served

    @asynccontextmanager
    async def get_qdrant_client(self):
        """Get Qdrant client"""
        if not self.qdrant_client or not self.health_status["qdrant"]:
            raise RuntimeError("Qdrant client not available")

        start_time = time.time()
        stats = self.stats["qdrant"]

        try:
            stats.active_connections += 1
            stats.requests_served += 1

            yield self.qdrant_client

        except Exception:
            stats.errors += 1
            raise
        finally:
            stats.active_connections -= 1

            # Update average response time
            response_time = time.time() - start_time
            stats.avg_response_time = (
                stats.avg_response_time * (stats.requests_served - 1) + response_time
            ) / stats.requests_served

    async def get_pool_stats(self) -> Dict[str, Any]:
        """Get comprehensive pool statistics"""
        stats = {}

        for service_name, service_stats in self.stats.items():
            stats[service_name] = {
                "active_connections": service_stats.active_connections,
                "idle_connections": service_stats.idle_connections,
                "total_connections": service_stats.total_connections,
                "requests_served": service_stats.requests_served,
                "errors": service_stats.errors,
                "avg_response_time_ms": round(
                    service_stats.avg_response_time * 1000, 2
                ),
                "error_rate_percent": round(
                    (service_stats.errors / service_stats.requests_served * 100)
                    if service_stats.requests_served > 0
                    else 0,
                    2,
                ),
                "healthy": self.health_status[service_name],
            }

        return stats

    async def health_check(self) -> Dict[str, Any]:
        """Health check for all connection pools"""
        health = {"overall_status": "healthy", "services": {}}

        # Check PostgreSQL
        if self.postgres_pool:
            try:
                async with self.get_postgres_connection() as conn:
                    await conn.fetchval("SELECT 1")
                health["services"]["postgres"] = {"status": "healthy", "message": "OK"}
            except Exception as e:
                health["services"]["postgres"] = {
                    "status": "unhealthy",
                    "message": str(e),
                }
                health["overall_status"] = "degraded"
        else:
            health["services"]["postgres"] = {
                "status": "not_configured",
                "message": "Not initialized",
            }

        # Check Redis
        if self.redis_pool:
            try:
                async with self.get_redis_client() as client:
                    await client.ping()
                health["services"]["redis"] = {"status": "healthy", "message": "OK"}
            except Exception as e:
                health["services"]["redis"] = {"status": "unhealthy", "message": str(e)}
                health["overall_status"] = "degraded"
        else:
            health["services"]["redis"] = {
                "status": "not_configured",
                "message": "Not initialized",
            }

        # Check HTTP client
        if self.http_client:
            try:
                response = await self.http_client.get(
                    "https://httpbin.org/get", timeout=5.0
                )
                response.raise_for_status()
                health["services"]["http"] = {"status": "healthy", "message": "OK"}
            except Exception as e:
                health["services"]["http"] = {"status": "unhealthy", "message": str(e)}
                health["overall_status"] = "degraded"
        else:
            health["services"]["http"] = {
                "status": "not_configured",
                "message": "Not initialized",
            }

        # Check Qdrant
        if self.qdrant_client:
            try:
                await self.qdrant_client.get_collections()
                health["services"]["qdrant"] = {"status": "healthy", "message": "OK"}
            except Exception as e:
                health["services"]["qdrant"] = {
                    "status": "unhealthy",
                    "message": str(e),
                }
                health["overall_status"] = "degraded"
        else:
            health["services"]["qdrant"] = {
                "status": "not_configured",
                "message": "Not initialized",
            }

        return health

    async def reset_stats(self):
        """Reset pool statistics"""
        for stats in self.stats.values():
            stats.requests_served = 0
            stats.errors = 0
            stats.avg_response_time = 0.0
            stats.last_reset = time.time()

        logger.info("Pool statistics reset")

    async def close(self):
        """Close all connection pools"""
        if self.postgres_pool:
            await self.postgres_pool.close()
            logger.info("PostgreSQL pool closed")

        if self.redis_pool:
            await self.redis_pool.disconnect()
            logger.info("Redis pool closed")

        if self.http_client:
            await self.http_client.aclose()
            logger.info("HTTP client closed")

        if self.qdrant_client:
            await self.qdrant_client.close()
            logger.info("Qdrant client closed")

        logger.info("All connection pools closed")


# Global instance
pool_service: Optional[ConnectionPoolService] = None


async def init_pool_service(
    config: PoolConfig,
    postgres_url: Optional[str] = None,
    redis_url: Optional[str] = None,
    qdrant_url: Optional[str] = None,
) -> ConnectionPoolService:
    """Initialize global pool service"""
    global pool_service

    pool_service = ConnectionPoolService(config)
    await pool_service.initialize(postgres_url, redis_url, qdrant_url)

    return pool_service


def get_pool_service() -> Optional[ConnectionPoolService]:
    """Get global pool service"""
    return pool_service
