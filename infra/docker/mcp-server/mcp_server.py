#!/usr/bin/env python3
"""
MCP Server for Context Gateway integration
Provides tools for RAG, memory, and notes operations
"""

import asyncio
import logging
import sys
from typing import Any, Dict
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ListToolsResult,
    Tool,
    TextContent,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContextGatewayMCP:
    """MCP Server for Context Gateway"""

    def __init__(self):
        self.gateway_url = "http://gateway:5057"
        self.gateway_token = "your-gateway-token"  # Should come from env
        self.server = Server("context-gateway-mcp")
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup MCP handlers"""

        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available tools"""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="ask_rag",
                        description="Ask a question using RAG (Retrieval-Augmented Generation)",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Question to ask",
                                },
                                "repo": {
                                    "type": "string",
                                    "description": "Repository name to search in (optional)",
                                },
                                "top_k": {
                                    "type": "integer",
                                    "description": "Number of results to return (default: 5)",
                                    "default": 5,
                                },
                            },
                            "required": ["query"],
                        },
                    ),
                    Tool(
                        name="search_vectors",
                        description="Search for similar content without LLM generation",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query",
                                },
                                "repo": {
                                    "type": "string",
                                    "description": "Repository name to search in (optional)",
                                },
                                "top_k": {
                                    "type": "integer",
                                    "description": "Number of results to return (default: 5)",
                                    "default": 5,
                                },
                                "include_content": {
                                    "type": "boolean",
                                    "description": "Include content in results (default: true)",
                                    "default": True,
                                },
                            },
                            "required": ["query"],
                        },
                    ),
                    Tool(
                        name="store_memory",
                        description="Store a value in agent memory",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "agent_id": {
                                    "type": "string",
                                    "description": "Agent identifier",
                                },
                                "key": {"type": "string", "description": "Memory key"},
                                "value": {
                                    "type": "string",
                                    "description": "Memory value",
                                },
                            },
                            "required": ["agent_id", "key", "value"],
                        },
                    ),
                    Tool(
                        name="get_memory",
                        description="Retrieve a value from agent memory",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "agent_id": {
                                    "type": "string",
                                    "description": "Agent identifier",
                                },
                                "key": {"type": "string", "description": "Memory key"},
                            },
                            "required": ["agent_id", "key"],
                        },
                    ),
                    Tool(
                        name="add_note",
                        description="Add a note with optional tags",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "text": {"type": "string", "description": "Note text"},
                                "repo": {
                                    "type": "string",
                                    "description": "Repository name (optional)",
                                },
                                "tags": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Note tags (optional)",
                                },
                            },
                            "required": ["text"],
                        },
                    ),
                    Tool(
                        name="search_notes",
                        description="Search notes by text or tags",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query",
                                },
                                "repo": {
                                    "type": "string",
                                    "description": "Repository name to filter by (optional)",
                                },
                                "tags": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Filter by tags (optional)",
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum results to return (default: 10)",
                                    "default": 10,
                                },
                            },
                            "required": ["query"],
                        },
                    ),
                    Tool(
                        name="list_collections",
                        description="List all available vector collections",
                        inputSchema={
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    ),
                    Tool(
                        name="index_repository",
                        description="Index a repository into vector database",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "repo_path": {
                                    "type": "string",
                                    "description": "Path to repository",
                                },
                                "collection_name": {
                                    "type": "string",
                                    "description": "Collection name for vectors",
                                },
                                "force_reindex": {
                                    "type": "boolean",
                                    "description": "Force reindex even if exists (default: false)",
                                    "default": False,
                                },
                            },
                            "required": ["repo_path", "collection_name"],
                        },
                    ),
                ]
            )

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls"""
            try:
                if name == "ask_rag":
                    return await self._ask_rag(arguments)
                elif name == "search_vectors":
                    return await self._search_vectors(arguments)
                elif name == "store_memory":
                    return await self._store_memory(arguments)
                elif name == "get_memory":
                    return await self._get_memory(arguments)
                elif name == "add_note":
                    return await self._add_note(arguments)
                elif name == "search_notes":
                    return await self._search_notes(arguments)
                elif name == "list_collections":
                    return await self._list_collections(arguments)
                elif name == "index_repository":
                    return await self._index_repository(arguments)
                else:
                    return CallToolResult(
                        content=[
                            TextContent(type="text", text=f"Unknown tool: {name}")
                        ],
                        isError=True,
                    )
            except Exception as e:
                logger.error(f"Tool call failed: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True,
                )

    async def _make_request(
        self, method: str, endpoint: str, data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to gateway"""
        headers = {
            "Authorization": f"Bearer {self.gateway_token}",
            "Content-Type": "application/json",
        }

        url = f"{self.gateway_url}{endpoint}"

        async with httpx.AsyncClient() as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, timeout=30.0)
                elif method.upper() == "POST":
                    response = await client.post(
                        url, json=data, headers=headers, timeout=30.0
                    )
                else:
                    raise ValueError(f"Unsupported method: {method}")

                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"HTTP request failed: {e}")
                raise
            except Exception as e:
                logger.error(f"Request failed: {e}")
                raise

    async def _ask_rag(self, args: Dict[str, Any]) -> CallToolResult:
        """Handle RAG query"""
        data = {"query": args["query"], "top_k": args.get("top_k", 5)}
        if "repo" in args:
            data["repo"] = args["repo"]

        result = await self._make_request("POST", "/ask", data)

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Answer: {result.get('answer', 'No answer')}\n\nSources:\n"
                    + "\n".join(
                        [
                            f"- {chunk.file_path}:{chunk.start_line}-{chunk.end_line}"
                            for chunk in result.get("chunks", [])
                        ]
                    ),
                )
            ]
        )

    async def _search_vectors(self, args: Dict[str, Any]) -> CallToolResult:
        """Handle vector search"""
        data = {
            "query": args["query"],
            "top_k": args.get("top_k", 5),
            "include_content": args.get("include_content", True),
        }
        if "repo" in args:
            data["repo"] = args["repo"]

        result = await self._make_request("POST", "/search", data)

        formatted_results = []
        for chunk in result.get("chunks", []):
            formatted_results.append(
                f"File: {chunk.file_path}:{chunk.start_line}-{chunk.end_line}\n"
                f"Score: {chunk.relevance:.3f}\n"
                f"Content: {chunk.content[:200]}...\n"
            )

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Found {len(formatted_results)} results:\n\n"
                    + "\n---\n".join(formatted_results),
                )
            ]
        )

    async def _store_memory(self, args: Dict[str, Any]) -> CallToolResult:
        """Handle memory storage"""
        data = {
            "op": "put",
            "agent_id": args["agent_id"],
            "key": args["key"],
            "value": args["value"],
        }

        result = await self._make_request("POST", "/memory", data)

        return CallToolResult(
            content=[
                TextContent(
                    type="text", text=f"Stored memory: {args['agent_id']}/{args['key']}"
                )
            ]
        )

    async def _get_memory(self, args: Dict[str, Any]) -> CallToolResult:
        """Handle memory retrieval"""
        data = {"op": "get", "agent_id": args["agent_id"], "key": args["key"]}

        result = await self._make_request("POST", "/memory", data)

        if result.get("success") and result.get("data"):
            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"Memory value: {result['data']}")
                ]
            )
        else:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Memory not found: {args['agent_id']}/{args['key']}",
                    )
                ]
            )

    async def _add_note(self, args: Dict[str, Any]) -> CallToolResult:
        """Handle note addition"""
        data = {"op": "add", "text": args["text"]}
        if "repo" in args:
            data["repo"] = args["repo"]
        if "tags" in args:
            data["tags"] = args["tags"]

        result = await self._make_request("POST", "/notes", data)

        return CallToolResult(
            content=[
                TextContent(
                    type="text", text=f"Added note: {result.get('message', 'Success')}"
                )
            ]
        )

    async def _search_notes(self, args: Dict[str, Any]) -> CallToolResult:
        """Handle note search"""
        data = {"op": "search", "query": args["query"], "limit": args.get("limit", 10)}
        if "repo" in args:
            data["repo"] = args["repo"]
        if "tags" in args:
            data["tags"] = args["tags"]

        result = await self._make_request("POST", "/notes", data)

        formatted_notes = []
        for note in result.get("notes", []):
            tags_str = ", ".join(note.tags) if note.tags else "none"
            formatted_notes.append(
                f"ID: {note.id}\n"
                f"Repo: {note.repo or 'none'}\n"
                f"Tags: {tags_str}\n"
                f"Created: {note.created_at}\n"
                f"Text: {note.text[:200]}...\n"
            )

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Found {len(formatted_notes)} notes:\n\n"
                    + "\n---\n".join(formatted_notes),
                )
            ]
        )

    async def _list_collections(self, args: Dict[str, Any]) -> CallToolResult:
        """Handle collection listing"""
        result = await self._make_request("GET", "/search/collections")

        collections = result.get("collections", [])
        info = result.get("info", {})

        formatted_collections = []
        for collection in collections:
            collection_info = info.get(collection, {})
            formatted_collections.append(
                f"Collection: {collection}\n"
                f"Points: {collection_info.get('points_count', 0)}\n"
                f"Vector Size: {collection_info.get('vector_size', 'unknown')}\n"
                f"Status: {collection_info.get('status', 'unknown')}\n"
            )

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text="Available collections:\n\n"
                    + "\n---\n".join(formatted_collections),
                )
            ]
        )

    async def _index_repository(self, args: Dict[str, Any]) -> CallToolResult:
        """Handle repository indexing"""
        data = {
            "repo_path": args["repo_path"],
            "collection_name": args["collection_name"],
            "force_reindex": args.get("force_reindex", False),
        }

        result = await self._make_request("POST", "/search/index", data)

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Indexing completed:\n"
                    f"Files processed: {result.get('files_processed', 0)}\n"
                    f"Chunks indexed: {result.get('chunks_indexed', 0)}\n"
                    f"Time: {result.get('indexing_time_ms', 0)}ms\n"
                    f"Errors: {len(result.get('errors', []))}",
                )
            ]
        )

    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, write_stream, self.server.create_initialization_options()
            )


async def main():
    """Main entry point"""
    import os

    # Get configuration from environment
    gateway_url = os.getenv("GATEWAY_URL", "http://gateway:5057")
    gateway_token = os.getenv("GATEWAY_TOKEN", "your-gateway-token")

    if not gateway_token or gateway_token == "your-gateway-token":
        logger.error("GATEWAY_TOKEN environment variable is required")
        sys.exit(1)

    # Create and run MCP server
    mcp_server = ContextGatewayMCP()
    mcp_server.gateway_url = gateway_url
    mcp_server.gateway_token = gateway_token

    logger.info("Starting Context Gateway MCP server")
    logger.info(f"Gateway URL: {gateway_url}")

    await mcp_server.run()


if __name__ == "__main__":
    asyncio.run(main())
