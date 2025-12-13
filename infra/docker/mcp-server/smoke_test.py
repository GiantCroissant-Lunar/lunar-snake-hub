import argparse
import json
import os
import uuid
from pathlib import Path
from typing import Optional

import httpx
from openai import OpenAI
from qdrant_client import QdrantClient


def _chunk_text(text: str, chunk_lines: int = 200, overlap_lines: int = 20):
    lines = text.splitlines()
    if not lines:
        return []

    chunks = []
    start = 0
    while start < len(lines):
        end = min(start + chunk_lines, len(lines))
        content = "\n".join(lines[start:end])
        chunks.append((start + 1, end, content))
        if end >= len(lines):
            break
        start = max(0, end - overlap_lines)
    return chunks


def _iter_repo_files(repo_root: Path):
    ignored_dirs = {".git", ".venv", "venv", "node_modules", "bin", "obj", ".hub-cache"}
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


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


def _load_env_from_windsurf_mcp_config(
    config_path: Path, server_name: str
) -> dict[str, str]:
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    servers = data.get("mcpServers")
    if not isinstance(servers, dict):
        return {}

    server = servers.get(server_name)
    if not isinstance(server, dict):
        return {}

    env = server.get("env")
    if not isinstance(env, dict):
        return {}

    # Ensure all values are strings
    result: dict[str, str] = {}
    for k, v in env.items():
        if isinstance(v, str):
            result[k] = v
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ensure-collection",
        action="store_true",
        help="Create CONTEXT_COLLECTION in Qdrant if it does not exist.",
    )
    parser.add_argument(
        "--index-repo",
        default=None,
        help="Index a repository path into Qdrant (embeddings + upsert).",
    )
    parser.add_argument(
        "--embed-batch-size",
        type=int,
        default=64,
        help="How many chunks to embed per OpenAI request (default: 64).",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=0,
        help="Optional cap on number of files to index (0 = no limit).",
    )
    parser.add_argument(
        "--max-chunks",
        type=int,
        default=0,
        help="Optional cap on number of chunks to index (0 = no limit).",
    )
    parser.add_argument(
        "--search",
        default=None,
        help="Run a vector search query against CONTEXT_COLLECTION.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Search top_k (default: 5)",
    )
    parser.add_argument(
        "--list-repo-keys",
        action="store_true",
        help="List unique repo_key values found in CONTEXT_COLLECTION.",
    )
    parser.add_argument(
        "--purge-secrets-repo",
        default=None,
        help=(
            "Delete indexed points that belong to infra/secrets (and similar) for the given repo path. "
            "Use this if you accidentally indexed secrets before adding excludes."
        ),
    )
    parser.add_argument(
        "--from-windsurf-config",
        action="store_true",
        help="Load env vars from Windsurf mcp_config.json (hub-context entry) if not present in process env.",
    )
    parser.add_argument(
        "--windsurf-config-path",
        default=r"C:\Users\User\.codeium\windsurf-next\mcp_config.json",
        help="Path to Windsurf mcp_config.json",
    )
    parser.add_argument(
        "--windsurf-server-name",
        default="hub-context",
        help="Server name under mcpServers to load env from (default: hub-context)",
    )
    args = parser.parse_args()

    config_env: dict[str, str] = {}
    if args.from_windsurf_config:
        config_env = _load_env_from_windsurf_mcp_config(
            Path(args.windsurf_config_path), args.windsurf_server_name
        )

    letta_url = _env("LETTA_URL") or config_env.get("LETTA_URL")
    qdrant_url = _env("QDRANT_URL") or config_env.get("QDRANT_URL")
    openai_base_url = (
        _env("OPENAI_BASE_URL")
        or config_env.get("OPENAI_BASE_URL")
        or "https://api.openai.com/v1"
    )
    openai_api_key = _env("OPENAI_API_KEY") or config_env.get("OPENAI_API_KEY")
    embedding_model = (
        _env("EMBEDDING_MODEL")
        or config_env.get("EMBEDDING_MODEL")
        or "text-embedding-3-small"
    )
    context_collection = (
        _env("CONTEXT_COLLECTION")
        or config_env.get("CONTEXT_COLLECTION")
        or "hub-context"
    )

    print("Config:")
    print(f"  LETTA_URL: {letta_url}")
    print(f"  QDRANT_URL: {qdrant_url}")
    print(f"  OPENAI_BASE_URL: {openai_base_url}")
    print(f"  EMBEDDING_MODEL: {embedding_model}")
    print(f"  CONTEXT_COLLECTION: {context_collection}")
    print(f"  OPENAI_API_KEY: {'SET' if bool(openai_api_key) else 'MISSING'}")

    if not letta_url:
        raise SystemExit("LETTA_URL is missing")
    if not qdrant_url:
        raise SystemExit("QDRANT_URL is missing")
    if not openai_api_key:
        raise SystemExit("OPENAI_API_KEY is missing")

    print("\nHealth:")
    with httpx.Client(timeout=10.0, follow_redirects=True) as client:
        letta_health = client.get(letta_url.rstrip("/") + "/v1/health/")
        print(f"  Letta: {letta_health.status_code}")

        qdrant_health = client.get(qdrant_url.rstrip("/") + "/healthz")
        print(f"  Qdrant: {qdrant_health.status_code}")

    print("\nOpenAI embeddings:")
    oai = OpenAI(api_key=openai_api_key, base_url=openai_base_url)
    emb = oai.embeddings.create(
        model=embedding_model, input="ping", encoding_format="float"
    )
    vec = emb.data[0].embedding
    dim = len(vec)
    print(f"  OK (dim={dim})")

    print("\nQdrant:")
    qc = QdrantClient(url=qdrant_url)
    collections = [c.name for c in qc.get_collections().collections]
    print(f"  Collections: {collections}")

    if context_collection not in collections:
        print(f"  Context collection '{context_collection}' does not exist")
        if (
            args.ensure_collection
            or args.index_repo
            or args.search
            or args.list_repo_keys
        ):
            from qdrant_client.http import models as qmodels

            qc.create_collection(
                collection_name=context_collection,
                vectors_config=qmodels.VectorParams(
                    size=dim, distance=qmodels.Distance.COSINE
                ),
            )
            print(f"  Created '{context_collection}'")
    else:
        info = qc.get_collection(context_collection)
        size = info.config.params.vectors.size
        print(
            f"  Context collection '{context_collection}' exists (vector_size={size})"
        )
        if size != dim:
            print(
                "  WARNING: embedding dim does not match collection vector_size. "
                "You may need to recreate the collection."
            )

    if args.list_repo_keys:
        print("\nRepo keys:")
        seen = set()
        offset = None
        while len(seen) < 200:
            points, offset = qc.scroll(
                collection_name=context_collection,
                limit=256,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for p in points:
                payload = p.payload or {}
                rk = payload.get("repo_key")
                if rk:
                    seen.add(rk)
            if not offset:
                break
        for rk in sorted(seen):
            print(f"  {rk}")

    if args.purge_secrets_repo:
        repo_root = Path(args.purge_secrets_repo).expanduser().resolve()
        import hashlib
        from qdrant_client.http import models as qmodels

        repo_key = (
            f"{repo_root.name}-"
            f"{hashlib.sha1(str(repo_root).encode('utf-8')).hexdigest()[:10]}"
        )

        print("\nPurging indexed secrets:")
        print(f"  repo_key: {repo_key}")

        selector_ids = []
        offset = None
        while True:
            points, offset = qc.scroll(
                collection_name=context_collection,
                limit=256,
                offset=offset,
                with_payload=True,
                with_vectors=False,
                scroll_filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="repo_key", match=qmodels.MatchValue(value=repo_key)
                        )
                    ]
                ),
            )
            for p in points:
                payload = p.payload or {}
                file_path = (payload.get("file_path") or "").replace("\\", "/")
                if file_path.startswith("infra/secrets/") or file_path.startswith(
                    ".sops/"
                ):
                    selector_ids.append(p.id)
            if not offset:
                break

        if not selector_ids:
            print("  no secret points found")
        else:
            qc.delete(
                collection_name=context_collection,
                points_selector=qmodels.PointIdsList(points=selector_ids),
            )
            print(f"  deleted: {len(selector_ids)}")

    if args.index_repo:
        repo_root = Path(args.index_repo).expanduser().resolve()
        if not repo_root.exists() or not repo_root.is_dir():
            raise SystemExit(f"index repo path is not a directory: {repo_root}")

        max_file_bytes = 1_000_000
        docs = []
        files_seen = 0
        for file_path in _iter_repo_files(repo_root):
            files_seen += 1
            if args.max_files and files_seen > args.max_files:
                break
            try:
                if file_path.stat().st_size > max_file_bytes:
                    continue
                text = file_path.read_text(encoding="utf-8", errors="ignore")
                for start_line, end_line, content in _chunk_text(text):
                    rel = str(file_path.relative_to(repo_root)).replace("\\", "/")
                    docs.append((rel, start_line, end_line, content))
                    if args.max_chunks and len(docs) >= args.max_chunks:
                        break
            except Exception:
                continue
            if args.max_chunks and len(docs) >= args.max_chunks:
                break

        print(f"\nIndexing: {repo_root}")
        print(f"  chunks: {len(docs)}")
        if not docs:
            raise SystemExit("no indexable content found")

        import hashlib
        from qdrant_client.http import models as qmodels

        repo_key = f"{repo_root.name}-{hashlib.sha1(str(repo_root).encode('utf-8')).hexdigest()[:10]}"
        repo_ns = uuid.uuid5(uuid.NAMESPACE_URL, repo_key)
        batch_size = max(1, int(args.embed_batch_size))
        upserted = 0
        print(f"  embedding batches of {batch_size}")

        for i in range(0, len(docs), batch_size):
            batch = docs[i : i + batch_size]
            vectors = oai.embeddings.create(
                model=embedding_model,
                input=[d[3] for d in batch],
                encoding_format="float",
            ).data

            points = []
            for (rel, start_line, end_line, content), v in zip(batch, vectors):
                pid = str(uuid.uuid5(repo_ns, f"{rel}:{start_line}:{end_line}"))
                payload = {
                    "repo_key": repo_key,
                    "repo_path": str(repo_root),
                    "file_path": rel,
                    "start_line": start_line,
                    "end_line": end_line,
                    "content": content,
                }
                points.append(
                    qmodels.PointStruct(id=pid, vector=v.embedding, payload=payload)
                )

            qc.upsert(collection_name=context_collection, points=points)
            upserted += len(points)
            print(f"  upserted: {upserted}/{len(docs)}")

        print(f"  repo_key: {repo_key}")

    if args.search:
        query_vec = (
            oai.embeddings.create(
                model=embedding_model, input=args.search, encoding_format="float"
            )
            .data[0]
            .embedding
        )
        query_result = qc.query_points(
            collection_name=context_collection,
            query=query_vec,
            limit=args.top_k,
            with_payload=True,
        )

        print("\nSearch results:")
        for r in query_result.points:
            payload = r.payload or {}
            rk = payload.get("repo_key")
            fp = payload.get("file_path")
            sl = payload.get("start_line")
            el = payload.get("end_line")
            score = getattr(r, "score", None)
            score_str = f" score={score:.4f}" if score is not None else ""
            print(f"  [{rk}] {fp}:{sl}-{el}{score_str}")

    print("\nSmoke test complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
