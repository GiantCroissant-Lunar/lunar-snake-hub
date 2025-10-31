import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.models.requests import MemoryRequest
from app.models.responses import MemoryResponse
from app.services.letta_client import LettaClient

logger = logging.getLogger(__name__)
router = APIRouter()

# Global service (will be injected by main.py)
letta_client = None


def init_service(letta: LettaClient):
    """Initialize service (called from main.py)"""
    global letta_client
    letta_client = letta


@router.post("")
async def memory_operations(
    request: MemoryRequest,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPAuthorizationCredentials()),
) -> MemoryResponse:
    """Memory operations endpoint"""
    try:
        if request.op == "get":
            if not request.key:
                raise HTTPException(
                    status_code=400, detail="Key is required for get operation"
                )

            value = await letta_client.get_memory(request.agent_id, request.key)
            if value is not None:
                return MemoryResponse(
                    success=True,
                    data=value,
                    message=f"Retrieved memory for key: {request.key}",
                )
            else:
                return MemoryResponse(
                    success=False, message=f"Memory key not found: {request.key}"
                )

        elif request.op == "put":
            if not request.key or request.value is None:
                raise HTTPException(
                    status_code=400,
                    detail="Key and value are required for put operation",
                )

            success = await letta_client.put_memory(
                request.agent_id, request.key, request.value
            )
            if success:
                return MemoryResponse(
                    success=True, message=f"Stored memory for key: {request.key}"
                )
            else:
                return MemoryResponse(
                    success=False,
                    message=f"Failed to store memory for key: {request.key}",
                )

        elif request.op == "delete":
            if not request.key:
                raise HTTPException(
                    status_code=400, detail="Key is required for delete operation"
                )

            success = await letta_client.delete_memory(request.agent_id, request.key)
            if success:
                return MemoryResponse(
                    success=True, message=f"Deleted memory for key: {request.key}"
                )
            else:
                return MemoryResponse(
                    success=False,
                    message=f"Failed to delete memory for key: {request.key}",
                )

        elif request.op == "search":
            if not request.query:
                raise HTTPException(
                    status_code=400, detail="Query is required for search operation"
                )

            results = await letta_client.search_memory(
                request.agent_id, request.query, request.limit
            )
            return MemoryResponse(
                success=True,
                data=results,
                message=f"Found {len(results)} memory entries",
            )

        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported operation: {request.op}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Memory operation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Memory operation failed: {e}")


@router.get("/agents")
async def list_agents(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPAuthorizationCredentials()),
) -> MemoryResponse:
    """List all agents"""
    try:
        agents = await letta_client.list_agents()
        return MemoryResponse(
            success=True, data=agents, message=f"Found {len(agents)} agents"
        )
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {e}")


@router.get("/agents/{agent_id}")
async def get_agent_info(
    agent_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPAuthorizationCredentials()),
) -> MemoryResponse:
    """Get agent information"""
    try:
        agent_info = await letta_client.get_agent(agent_id)
        if agent_info:
            return MemoryResponse(
                success=True,
                data=agent_info,
                message=f"Retrieved agent info for: {agent_id}",
            )
        else:
            return MemoryResponse(success=False, message=f"Agent not found: {agent_id}")
    except Exception as e:
        logger.error(f"Failed to get agent info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent info: {e}")
