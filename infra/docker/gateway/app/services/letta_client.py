import os
import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)


class LettaClient:
    """Client for Letta agent memory operations"""

    def __init__(self):
        self.base_url = os.getenv("LETTA_URL", "http://letta:8283")
        self.api_key = os.getenv("OPENAI_API_KEY")  # Letta uses same API key

        logger.info(f"Initialized Letta client with URL: {self.base_url}")

    async def health_check(self) -> bool:
        """Check if Letta is accessible"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/v1/health/", timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Letta health check passed: {data.get('status')}")
                    return True
                else:
                    logger.error(
                        f"Letta health check failed with status: {response.status_code}"
                    )
                    return False
        except Exception as e:
            logger.error(f"Letta health check failed: {e}")
            return False

    async def get_memory(self, agent_id: str, key: str) -> Optional[Any]:
        """Get memory value for agent"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v1/agents/{agent_id}/memory",
                    params={"key": key},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("value")
                else:
                    logger.error(f"Failed to get memory: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Failed to get memory: {e}")
            return None

    async def put_memory(self, agent_id: str, key: str, value: Any) -> bool:
        """Store memory value for agent"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/agents/{agent_id}/memory",
                    json={"key": key, "value": value},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    logger.info(f"Stored memory for {agent_id}: {key}")
                    return True
                else:
                    logger.error(f"Failed to store memory: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return False

    async def delete_memory(self, agent_id: str, key: str) -> bool:
        """Delete memory value for agent"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/v1/agents/{agent_id}/memory",
                    params={"key": key},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    logger.info(f"Deleted memory for {agent_id}: {key}")
                    return True
                else:
                    logger.error(f"Failed to delete memory: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            return False

    async def search_memory(self, agent_id: str, query: str, limit: int = 10) -> list:
        """Search agent memory"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v1/agents/{agent_id}/memory/search",
                    params={"query": query, "limit": limit},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("results", [])
                else:
                    logger.error(f"Failed to search memory: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"Failed to search memory: {e}")
            return []

    async def list_agents(self) -> list:
        """List all agents"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/v1/agents/", timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("agents", [])
                else:
                    logger.error(f"Failed to list agents: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            return []

    async def create_agent(self, agent_config: Dict[str, Any]) -> Optional[str]:
        """Create a new agent"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/agents/", json=agent_config, timeout=30.0
                )
                if response.status_code == 200:
                    data = response.json()
                    agent_id = data.get("agent_id")
                    logger.info(f"Created agent: {agent_id}")
                    return agent_id
                else:
                    logger.error(f"Failed to create agent: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            return None

    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent information"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v1/agents/{agent_id}", timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to get agent: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Failed to get agent: {e}")
            return None

    async def send_message(self, agent_id: str, message: str) -> Optional[str]:
        """Send message to agent"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/agents/{agent_id}/messages",
                    json={"message": message},
                    timeout=30.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response")
                else:
                    logger.error(f"Failed to send message: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return None
