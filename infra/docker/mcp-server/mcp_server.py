#!/usr/bin/env python3
"""
MCP Server for local context + memory
Provides tools for indexing and searching code context (backed by Qdrant)
and for agent memory operations (backed by Letta).
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import httpx
from openai import OpenAI
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ListToolsResult,
    Tool,
    TextContent,
)
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContextGatewayMCP:
    """Local MCP server that hides Qdrant/Letta behind tools."""

    def __init__(self):
        self.letta_url = os.getenv("LETTA_URL", "http://localhost:5055")
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")

        self.embedding_api_key = os.getenv("OPENAI_API_KEY")
        self.embedding_base_url = os.getenv(
            "OPENAI_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"
        )
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

        self.repo_roots = self._parse_repo_roots(os.getenv("MCP_REPO_ROOTS", ""))
        if not self.repo_roots:
            self.repo_roots = [Path.home() / "repos"]

        self.server = Server("context-mcp")
        self._setup_handlers()

        if not self.embedding_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self._openai_client = OpenAI(
            api_key=self.embedding_api_key, base_url=self.embedding_base_url
        )
        self._qdrant = QdrantClient(url=self.qdrant_url)

    def _setup_handlers(self):
        """Setup MCP handlers"""

        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available tools"""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="context_index_repo",
                        description="Index a local repository into the context store",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "repo_id": {
                                    "type": "string",
                                    "description": "Logical repository identifier (collection name)",
                                },
                                "repo_path": {
                                    "type": "string",
                                    "description": "Absolute path to the repository to index",
                                },
                                "force_reindex": {
                                    "type": "boolean",
                                    "description": "Recreate collection before indexing (default: false)",
                                    "default": False,
                                },
                            },
                            "required": ["repo_id", "repo_path"],
                        },
                    ),
                    Tool(
                        name="context_search",
                        description="Search indexed context for relevant code/doc snippets",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "repo_id": {
                                    "type": "string",
                                    "description": "Logical repository identifier (collection name)",
                                },
                                "query": {
                                    "type": "string",
                                    "description": "Search query",
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
                            "required": ["repo_id", "query"],
                        },
                    ),
                    Tool(
                        name="context_list_repos",
                        description="List available context repositories (indexed collections)",
                        inputSchema={
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    ),
                    Tool(
                        name="memory_put",
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
                        name="memory_get",
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
                        name="memory_search",
                        description="Search agent memory",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "agent_id": {
                                    "type": "string",
                                    "description": "Agent identifier",
                                },
                                "query": {
                                    "type": "string",
                                    "description": "Search query",
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum results to return (default: 10)",
                                    "default": 10,
                                },
                            },
                            "required": ["agent_id", "query"],
                        },
                    ),
                ]
            )

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls"""
            try:
                if name == "context_index_repo":
                    return await self._context_index_repo(arguments)
                if name == "context_search":
                    return await self._context_search(arguments)
                if name == "context_list_repos":
                    return await self._context_list_repos()
                if name == "memory_put":
                    return await self._memory_put(arguments)
                if name == "memory_get":
                    return await self._memory_get(arguments)
                if name == "memory_search":
                    return await self._memory_search(arguments)
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

    def _parse_repo_roots(self, raw: str) -> List[Path]:
        parts: List[str] = []
        for chunk in raw.split(os.pathsep):
            parts.extend([p.strip() for p in chunk.split(",") if p.strip()])
        roots: List[Path] = []
        for part in parts:
            try:
                roots.append(Path(part).expanduser().resolve())
            except Exception:
                continue
        return roots

    def _is_allowed_repo_path(self, repo_path: Path) -> bool:
        try:
            resolved = repo_path.expanduser().resolve()
        except Exception:
            return False

        for root in self.repo_roots:
            try:
                if resolved.is_relative_to(root):
                    return True
            except Exception:
                # Python < 3.9 fallback not needed in our runtime, but keep safe
                if str(resolved).startswith(str(root)):
                    return True
        return False

    def _iter_repo_files(self, repo_root: Path) -> Iterable[Path]:
        ignored_dirs = {
            ".git",
            ".venv",
            "venv",
            "node_modules",
            "bin",
            "obj",
            ".hub-cache",
        }
        allowed_exts = {
            ".md",
            ".txt",
            ".py",
            ".cs",
            ".json",
            ".yml",
            ".yaml",
            ".toml",
            ".js",
            ".ts",
            ".tsx",
            ".jsx",
            ".java",
            ".kt",
            ".go",
            ".rs",
            ".c",
            ".cpp",
            ".h",
            ".hpp",
        }

        for path in repo_root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in ignored_dirs for part in path.parts):
                continue
            if path.suffix.lower() not in allowed_exts:
                continue
            yield path

    def _chunk_text(
        self, text: str, chunk_lines: int = 200, overlap_lines: int = 20
    ) -> List[Tuple[int, int, str]]:
        lines = text.splitlines()
        if not lines:
            return []

        chunks: List[Tuple[int, int, str]] = []
        start = 0
        while start < len(lines):
            end = min(start + chunk_lines, len(lines))
            content = "\n".join(lines[start:end])
            chunks.append((start + 1, end, content))
            if end >= len(lines):
                break
            start = max(0, end - overlap_lines)
        return chunks

    async def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        def _call() -> List[List[float]]:
            resp = self._openai_client.embeddings.create(
                model=self.embedding_model, input=texts, encoding_format="float"
            )
            return [d.embedding for d in resp.data]

        return await asyncio.to_thread(_call)

    async def _ensure_collection(
        self, repo_id: str, vector_size: int, force: bool
    ) -> None:
        def _call() -> None:
            exists = self._qdrant.collection_exists(repo_id)
            if exists and force:
                self._qdrant.delete_collection(repo_id)
                exists = False
            if not exists:
                self._qdrant.create_collection(
                    collection_name=repo_id,
                    vectors_config=qmodels.VectorParams(
                        size=vector_size, distance=qmodels.Distance.COSINE
                    ),
                )

        await asyncio.to_thread(_call)

    async def _context_index_repo(self, args: Dict[str, Any]) -> CallToolResult:
        repo_id = args["repo_id"]
        repo_path = Path(args["repo_path"])
        force_reindex = bool(args.get("force_reindex", False))

        if not repo_path.exists() or not repo_path.is_dir():
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text=f"repo_path is not a directory: {repo_path}"
                    )
                ],
                isError=True,
            )

        if not self._is_allowed_repo_path(repo_path):
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=(
                            "repo_path is not allowed. Configure MCP_REPO_ROOTS to allow indexing. "
                            f"repo_path={repo_path}"
                        ),
                    )
                ],
                isError=True,
            )

        max_file_bytes = 1_000_000
        docs: List[Tuple[str, int, int, str]] = []

        for file_path in self._iter_repo_files(repo_path):
            try:
                if file_path.stat().st_size > max_file_bytes:
                    continue
                text = file_path.read_text(encoding="utf-8", errors="ignore")
                for start_line, end_line, content in self._chunk_text(text):
                    rel_path = str(file_path.relative_to(repo_path)).replace("\\", "/")
                    docs.append((rel_path, start_line, end_line, content))
            except Exception:
                continue

        if not docs:
            return CallToolResult(
                content=[TextContent(type="text", text="No indexable files found.")],
                isError=False,
            )

        embeddings = await self._embed_texts([d[3] for d in docs])
        vector_size = len(embeddings[0]) if embeddings else 0
        await self._ensure_collection(repo_id, vector_size, force_reindex)

        points: List[qmodels.PointStruct] = []
        for (rel_path, start_line, end_line, content), vector in zip(docs, embeddings):
            point_id = f"{rel_path}:{start_line}:{end_line}"
            payload = {
                "file_path": rel_path,
                "start_line": start_line,
                "end_line": end_line,
                "content": content,
            }
            points.append(
                qmodels.PointStruct(id=point_id, vector=vector, payload=payload)
            )

        def _upsert() -> None:
            self._qdrant.upsert(collection_name=repo_id, points=points)

        await asyncio.to_thread(_upsert)

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Indexed repo_id={repo_id}. Files/chunks indexed: {len(points)}",
                )
            ]
        )

    async def _context_search(self, args: Dict[str, Any]) -> CallToolResult:
        repo_id = args["repo_id"]
        query = args["query"]
        top_k = int(args.get("top_k", 5))
        include_content = bool(args.get("include_content", True))

        query_vec = (await self._embed_texts([query]))[0]

        def _search() -> List[qmodels.ScoredPoint]:
            return self._qdrant.search(
                collection_name=repo_id,
                query_vector=query_vec,
                limit=top_k,
                with_payload=True,
            )

        points = await asyncio.to_thread(_search)

        lines: List[str] = []
        for p in points:
            payload = p.payload or {}
            file_path = payload.get("file_path", "unknown")
            start_line = payload.get("start_line")
            end_line = payload.get("end_line")
            score = getattr(p, "score", None)
            header = (
                f"{file_path}:{start_line}-{end_line} score={score:.4f}"
                if score is not None
                else f"{file_path}:{start_line}-{end_line}"
            )
            lines.append(header)
            if include_content:
                content = payload.get("content", "")
                lines.append(content)
                lines.append("---")

        return CallToolResult(
            content=[TextContent(type="text", text="\n".join(lines) or "No results.")]
        )

    async def _context_list_repos(self) -> CallToolResult:
        def _call() -> List[str]:
            return [c.name for c in self._qdrant.get_collections().collections]

        repos = await asyncio.to_thread(_call)
        text = "\n".join(repos) if repos else "(no indexed repos)"
        return CallToolResult(content=[TextContent(type="text", text=text)])

    async def _letta_request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Any = None,
    ) -> Dict[str, Any]:
        url = f"{self.letta_url.rstrip('/')}{path}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.request(method, url, params=params, json=json)
            resp.raise_for_status()
            return resp.json() if resp.content else {}

    async def _memory_put(self, args: Dict[str, Any]) -> CallToolResult:
        agent_id = args["agent_id"]
        key = args["key"]
        value = args["value"]
        await self._letta_request(
            "POST", f"/v1/agents/{agent_id}/memory", json={"key": key, "value": value}
        )
        return CallToolResult(
            content=[TextContent(type="text", text=f"Stored memory: {agent_id}/{key}")]
        )

    async def _memory_get(self, args: Dict[str, Any]) -> CallToolResult:
        agent_id = args["agent_id"]
        key = args["key"]
        data = await self._letta_request(
            "GET", f"/v1/agents/{agent_id}/memory", params={"key": key}
        )
        value = data.get("value")
        if value is None:
            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"Memory not found: {agent_id}/{key}")
                ]
            )
        return CallToolResult(content=[TextContent(type="text", text=str(value))])

    async def _memory_search(self, args: Dict[str, Any]) -> CallToolResult:
        agent_id = args["agent_id"]
        query = args["query"]
        limit = int(args.get("limit", 10))
        data = await self._letta_request(
            "GET",
            f"/v1/agents/{agent_id}/memory/search",
            params={"query": query, "limit": limit},
        )
        results = data.get("results", [])
        return CallToolResult(content=[TextContent(type="text", text=str(results))])

    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, write_stream, self.server.create_initialization_options()
            )


async def main():
    """Main entry point"""
    try:
        mcp_server = ContextGatewayMCP()
    except Exception as e:
        logger.error(f"Failed to initialize MCP server: {e}")
        sys.exit(1)

    logger.info("Starting local Context MCP server")
    logger.info(f"LETTA_URL: {mcp_server.letta_url}")
    logger.info(f"QDRANT_URL: {mcp_server.qdrant_url}")
    logger.info(f"MCP_REPO_ROOTS: {', '.join(str(p) for p in mcp_server.repo_roots)}")

    await mcp_server.run()


if __name__ == "__main__":
    asyncio.run(main())
