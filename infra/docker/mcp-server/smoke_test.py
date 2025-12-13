import argparse
import json
import os
from pathlib import Path
from typing import Optional

import httpx
from openai import OpenAI
from qdrant_client import QdrantClient


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

    if context_collection in collections:
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
    else:
        print(f"  Context collection '{context_collection}' does not exist")
        if args.ensure_collection:
            from qdrant_client.http import models as qmodels

            qc.create_collection(
                collection_name=context_collection,
                vectors_config=qmodels.VectorParams(
                    size=dim, distance=qmodels.Distance.COSINE
                ),
            )
            print(f"  Created '{context_collection}'")

    print("\nSmoke test complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
