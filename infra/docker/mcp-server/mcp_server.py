#!/usr/bin/env python3
"""
MCP Server for local context + memory
Provides tools for indexing and searching code context (backed by Qdrant)
and for agent memory operations (backed by Letta).
"""

import asyncio
import hashlib
import logging
import os
import sys
import uuid
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


MAX_EMBED_CHARS = 8_000


class ContextGatewayMCP:
    """Local MCP server that hides Qdrant/Letta behind tools."""

    def __init__(self):
        self.letta_url = os.getenv("LETTA_URL", "http://localhost:5055")
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")

        self.context_collection = os.getenv("CONTEXT_COLLECTION", "hub-context")

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
                                    "description": "Optional override for the Qdrant collection name (defaults to CONTEXT_COLLECTION)",
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
                                "embed_batch_size": {
                                    "type": "integer",
                                    "description": "How many chunks to embed per request (default: 64)",
                                    "default": 64,
                                },
                                "max_files": {
                                    "type": "integer",
                                    "description": "Optional cap on number of files to index (0 = no limit)",
                                    "default": 0,
                                },
                                "max_chunks": {
                                    "type": "integer",
                                    "description": "Optional cap on number of chunks to index (0 = no limit)",
                                    "default": 0,
                                },
                            },
                            "required": ["repo_path"],
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
                                    "description": "Optional override for the Qdrant collection name (defaults to CONTEXT_COLLECTION)",
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
                                "repo_key": {
                                    "type": "string",
                                    "description": "Optional filter to only search within an indexed repo_key (returned in results)",
                                },
                            },
                            "required": ["query"],
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
                        name="context_list_repo_keys",
                        description=(
                            "List repo_key values found in the shared context collection "
                            "(useful for optional filtering)"
                        ),
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "repo_id": {
                                    "type": "string",
                                    "description": "Optional override for the Qdrant collection name (defaults to CONTEXT_COLLECTION)",
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum unique repo_keys to return (default: 50)",
                                    "default": 50,
                                },
                            },
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
                if name == "context_list_repo_keys":
                    return await self._context_list_repo_keys(arguments)
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
        ignored_path_prefixes = {
            "infra/secrets/",
            ".sops/",
        }
        ignored_filenames = {
            ".env",
            ".env.example",
        }
        ignored_suffixes = {
            ".key",
            ".pem",
            ".pfx",
            ".p12",
            ".crt",
            ".cer",
            ".der",
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
            rel = str(path.relative_to(repo_root)).replace("\\", "/")
            if any(rel.startswith(prefix) for prefix in ignored_path_prefixes):
                continue
            if path.name in ignored_filenames:
                continue
            if path.name.startswith(".env."):
                continue
            if path.suffix.lower() in ignored_suffixes:
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
            if len(content) > MAX_EMBED_CHARS:
                content = content[:MAX_EMBED_CHARS]
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
        repo_id = args.get("repo_id") or self.context_collection
        repo_path = Path(args["repo_path"])
        force_reindex = bool(args.get("force_reindex", False))
        embed_batch_size = int(args.get("embed_batch_size", 64) or 64)
        max_files = int(args.get("max_files", 0) or 0)
        max_chunks = int(args.get("max_chunks", 0) or 0)
        embed_batch_size = max(1, embed_batch_size)

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
        files_seen = 0

        for file_path in self._iter_repo_files(repo_path):
            files_seen += 1
            if max_files and files_seen > max_files:
                break
            try:
                if file_path.stat().st_size > max_file_bytes:
                    continue
                text = file_path.read_text(encoding="utf-8", errors="ignore")
                for start_line, end_line, content in self._chunk_text(text):
                    rel_path = str(file_path.relative_to(repo_path)).replace("\\", "/")
                    docs.append((rel_path, start_line, end_line, content))
                    if max_chunks and len(docs) >= max_chunks:
                        break
            except Exception:
                continue
            if max_chunks and len(docs) >= max_chunks:
                break

        if not docs:
            return CallToolResult(
                content=[TextContent(type="text", text="No indexable files found.")],
                isError=False,
            )

        repo_key = self._repo_key(repo_path)
        repo_ns = uuid.uuid5(uuid.NAMESPACE_URL, repo_key)

        # Embed a small first batch to determine vector size / create collection.
        first_batch = docs[: min(len(docs), embed_batch_size)]
        first_embeddings = await self._embed_texts([d[3] for d in first_batch])
        vector_size = len(first_embeddings[0]) if first_embeddings else 0
        await self._ensure_collection(repo_id, vector_size, force_reindex)

        upserted = 0
        for i in range(0, len(docs), embed_batch_size):
            batch = docs[i : i + embed_batch_size]
            if i == 0:
                batch_embeddings = first_embeddings
            else:
                batch_embeddings = await self._embed_texts([d[3] for d in batch])

            points: List[qmodels.PointStruct] = []
            for (rel_path, start_line, end_line, content), vector in zip(
                batch, batch_embeddings
            ):
                point_id = str(
                    uuid.uuid5(repo_ns, f"{rel_path}:{start_line}:{end_line}")
                )
                payload = {
                    "repo_key": repo_key,
                    "repo_path": str(repo_path),
                    "file_path": rel_path,
                    "start_line": start_line,
                    "end_line": end_line,
                    "content": content,
                }
                points.append(
                    qmodels.PointStruct(id=point_id, vector=vector, payload=payload)
                )

            def _upsert_batch() -> None:
                self._qdrant.upsert(collection_name=repo_id, points=points)

            await asyncio.to_thread(_upsert_batch)
            upserted += len(points)

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=(
                        f"Indexed collection={repo_id}. repo_key={repo_key}. "
                        f"Files/chunks indexed: {upserted}. "
                        f"embed_batch_size={embed_batch_size}"
                    ),
                )
            ]
        )

    async def _context_search(self, args: Dict[str, Any]) -> CallToolResult:
        repo_id = args.get("repo_id") or self.context_collection
        query = args["query"]
        top_k = int(args.get("top_k", 5))
        include_content = bool(args.get("include_content", True))
        repo_key = args.get("repo_key")

        query_vec = (await self._embed_texts([query]))[0]

        def _query() -> List[qmodels.ScoredPoint]:
            result = self._qdrant.query_points(
                collection_name=repo_id,
                query=query_vec,
                limit=top_k,
                with_payload=True,
                filter=(
                    qmodels.Filter(
                        must=[
                            qmodels.FieldCondition(
                                key="repo_key",
                                match=qmodels.MatchValue(value=repo_key),
                            )
                        ]
                    )
                    if repo_key
                    else None
                ),
            )
            return list(result.points)

        points = await asyncio.to_thread(_query)

        lines: List[str] = []
        for p in points:
            payload = p.payload or {}
            payload_repo_key = payload.get("repo_key")
            file_path = payload.get("file_path", "unknown")
            start_line = payload.get("start_line")
            end_line = payload.get("end_line")
            score = getattr(p, "score", None)
            prefix = f"[{payload_repo_key}] " if payload_repo_key else ""
            header = (
                f"{prefix}{file_path}:{start_line}-{end_line} score={score:.4f}"
                if score is not None
                else f"{prefix}{file_path}:{start_line}-{end_line}"
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

        collections = await asyncio.to_thread(_call)
        text = "\n".join(collections) if collections else "(no collections)"
        return CallToolResult(content=[TextContent(type="text", text=text)])

    async def _context_list_repo_keys(self, args: Dict[str, Any]) -> CallToolResult:
        repo_id = args.get("repo_id") or self.context_collection
        limit = int(args.get("limit", 50))

        def _scroll_unique() -> List[Tuple[str, str]]:
            unique: Dict[str, str] = {}
            offset = None
            while len(unique) < limit:
                points, offset = self._qdrant.scroll(
                    collection_name=repo_id,
                    limit=256,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False,
                )
                for p in points:
                    payload = p.payload or {}
                    rk = payload.get("repo_key")
                    rp = payload.get("repo_path")
                    if rk and rk not in unique:
                        unique[rk] = rp or ""
                        if len(unique) >= limit:
                            break
                if not offset:
                    break
            return sorted(unique.items(), key=lambda kv: kv[0])

        items = await asyncio.to_thread(_scroll_unique)
        if not items:
            return CallToolResult(
                content=[TextContent(type="text", text="(no repo_keys found)")]
            )

        lines = [f"{rk}\t{rp}" if rp else rk for rk, rp in items]
        return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))])

    def _repo_key(self, repo_path: Path) -> str:
        resolved = str(repo_path.expanduser().resolve()).replace("\\", "/")
        base = repo_path.name
        digest = hashlib.sha1(resolved.encode("utf-8")).hexdigest()[:10]
        return f"{base}-{digest}"

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
    logger.info(f"CONTEXT_COLLECTION: {mcp_server.context_collection}")
    logger.info(f"MCP_REPO_ROOTS: {', '.join(str(p) for p in mcp_server.repo_roots)}")

    await mcp_server.run()


if __name__ == "__main__":
    asyncio.run(main())
