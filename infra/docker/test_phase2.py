#!/usr/bin/env python3
"""
Phase 2 Implementation Test Script
Tests the Context Gateway, Qdrant, and MCP integration
"""

import asyncio
import httpx
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Phase2Tester:
    """Test suite for Phase 2 implementation"""

    def __init__(self):
        self.gateway_url = "http://localhost:5057"
        self.gateway_token = os.getenv("GATEWAY_TOKEN", "test-token")
        self.test_results = []

    async def run_all_tests(self):
        """Run all Phase 2 tests"""
        logger.info("🚀 Starting Phase 2 Implementation Tests")

        # Test 1: Health checks
        await self.test_health_checks()

        # Test 2: Context Gateway endpoints
        await self.test_context_gateway()

        # Test 3: Vector search functionality
        await self.test_vector_search()

        # Test 4: Repository indexing
        await self.test_repository_indexing()

        # Test 5: Memory operations
        await self.test_memory_operations()

        # Test 6: Notes operations
        await self.test_notes_operations()

        # Summary
        self.print_summary()

    async def test_health_checks(self):
        """Test service health"""
        logger.info("📋 Testing Health Checks...")

        services = {
            "Gateway": f"{self.gateway_url}/health",
            "Qdrant": "http://localhost:6333/healthz",
            "Letta": "http://localhost:5055/v1/health",
        }

        for service, url in services.items():
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        self.test_results.append(f"✅ {service}: Healthy")
                        logger.info(f"  ✅ {service}: Healthy")
                    else:
                        self.test_results.append(
                            f"❌ {service}: HTTP {response.status_code}"
                        )
                        logger.error(f"  ❌ {service}: HTTP {response.status_code}")
            except Exception as e:
                self.test_results.append(f"❌ {service}: {str(e)}")
                logger.error(f"  ❌ {service}: {str(e)}")

    async def test_context_gateway(self):
        """Test Context Gateway API endpoints"""
        logger.info("🔗 Testing Context Gateway...")

        headers = {"Authorization": f"Bearer {self.gateway_token}"}

        # Test root endpoint
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.gateway_url}/")
                if response.status_code == 200:
                    data = response.json()
                    self.test_results.append("✅ Gateway Root: Working")
                    logger.info(f"  ✅ Gateway Root: {data.get('message')}")
                else:
                    self.test_results.append(
                        f"❌ Gateway Root: HTTP {response.status_code}"
                    )
        except Exception as e:
            self.test_results.append(f"❌ Gateway Root: {str(e)}")

        # Test collections listing
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.gateway_url}/search/collections", headers=headers
                )
                if response.status_code == 200:
                    data = response.json()
                    collections = data.get("collections", [])
                    self.test_results.append(
                        f"✅ Collections API: Found {len(collections)} collections"
                    )
                    logger.info(
                        f"  ✅ Collections API: Found {len(collections)} collections"
                    )
                else:
                    self.test_results.append(
                        f"❌ Collections API: HTTP {response.status_code}"
                    )
        except Exception as e:
            self.test_results.append(f"❌ Collections API: {str(e)}")

    async def test_vector_search(self):
        """Test vector search functionality"""
        logger.info("🔍 Testing Vector Search...")

        headers = {
            "Authorization": f"Bearer {self.gateway_token}",
            "Content-Type": "application/json",
        }

        # Test search query
        search_data = {
            "query": "test search query",
            "top_k": 3,
            "include_content": True,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.gateway_url}/search", json=search_data, headers=headers
                )
                if response.status_code == 200:
                    data = response.json()
                    chunks = data.get("chunks", [])
                    self.test_results.append(
                        f"✅ Vector Search: Found {len(chunks)} results"
                    )
                    logger.info(f"  ✅ Vector Search: Found {len(chunks)} results")
                else:
                    self.test_results.append(
                        f"❌ Vector Search: HTTP {response.status_code}"
                    )
        except Exception as e:
            self.test_results.append(f"❌ Vector Search: {str(e)}")

    async def test_repository_indexing(self):
        """Test repository indexing"""
        logger.info("📚 Testing Repository Indexing...")

        headers = {
            "Authorization": f"Bearer {self.gateway_token}",
            "Content-Type": "application/json",
        }

        # Create a test repository structure
        test_repo_path = "/tmp/test-repo"
        os.makedirs(test_repo_path, exist_ok=True)

        # Create test files
        with open(f"{test_repo_path}/test.py", "w") as f:
            f.write("""
def hello_world():
    print("Hello, World!")
    return "success"

class TestClass:
    def __init__(self):
        self.name = "test"

    def method(self):
        return self.name.upper()
""")

        with open(f"{test_repo_path}/README.md", "w") as f:
            f.write("""
# Test Repository

This is a test repository for Phase 2 implementation testing.

## Features
- Python code
- Markdown documentation
- Function and class definitions
""")

        # Test indexing
        index_data = {
            "repo_path": test_repo_path,
            "collection_name": "test-collection",
            "force_reindex": True,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.gateway_url}/search/index", json=index_data, headers=headers
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        chunks = data.get("chunks_indexed", 0)
                        files = data.get("files_processed", 0)
                        self.test_results.append(
                            f"✅ Repository Indexing: {files} files, {chunks} chunks"
                        )
                        logger.info(
                            f"  ✅ Repository Indexing: {files} files, {chunks} chunks"
                        )
                    else:
                        errors = data.get("errors", [])
                        self.test_results.append(
                            f"❌ Repository Indexing: {', '.join(errors)}"
                        )
                else:
                    self.test_results.append(
                        f"❌ Repository Indexing: HTTP {response.status_code}"
                    )
        except Exception as e:
            self.test_results.append(f"❌ Repository Indexing: {str(e)}")

        # Cleanup
        import shutil

        shutil.rmtree(test_repo_path, ignore_errors=True)

    async def test_memory_operations(self):
        """Test memory operations"""
        logger.info("🧠 Testing Memory Operations...")

        headers = {
            "Authorization": f"Bearer {self.gateway_token}",
            "Content-Type": "application/json",
        }

        # Test memory storage
        memory_data = {
            "op": "put",
            "agent_id": "test-agent",
            "key": "test-key",
            "value": "test-value",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.gateway_url}/memory", json=memory_data, headers=headers
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        self.test_results.append("✅ Memory Storage: Working")
                        logger.info("  ✅ Memory Storage: Working")
                    else:
                        self.test_results.append(
                            f"❌ Memory Storage: {data.get('message')}"
                        )
                else:
                    self.test_results.append(
                        f"❌ Memory Storage: HTTP {response.status_code}"
                    )
        except Exception as e:
            self.test_results.append(f"❌ Memory Storage: {str(e)}")

        # Test memory retrieval
        memory_data = {"op": "get", "agent_id": "test-agent", "key": "test-key"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.gateway_url}/memory", json=memory_data, headers=headers
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and data.get("data") == "test-value":
                        self.test_results.append("✅ Memory Retrieval: Working")
                        logger.info("  ✅ Memory Retrieval: Working")
                    else:
                        self.test_results.append(
                            f"❌ Memory Retrieval: {data.get('message')}"
                        )
                else:
                    self.test_results.append(
                        f"❌ Memory Retrieval: HTTP {response.status_code}"
                    )
        except Exception as e:
            self.test_results.append(f"❌ Memory Retrieval: {str(e)}")

    async def test_notes_operations(self):
        """Test notes operations"""
        logger.info("📝 Testing Notes Operations...")

        headers = {
            "Authorization": f"Bearer {self.gateway_token}",
            "Content-Type": "application/json",
        }

        # Test note addition
        note_data = {
            "op": "add",
            "text": "This is a test note for Phase 2 implementation",
            "repo": "test-repo",
            "tags": ["test", "phase2"],
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.gateway_url}/notes", json=note_data, headers=headers
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        self.test_results.append("✅ Notes Addition: Working")
                        logger.info("  ✅ Notes Addition: Working")
                    else:
                        self.test_results.append(
                            f"❌ Notes Addition: {data.get('message')}"
                        )
                else:
                    self.test_results.append(
                        f"❌ Notes Addition: HTTP {response.status_code}"
                    )
        except Exception as e:
            self.test_results.append(f"❌ Notes Addition: {str(e)}")

        # Test notes search
        search_data = {"op": "search", "query": "test", "limit": 5}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.gateway_url}/notes", json=search_data, headers=headers
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        notes = data.get("notes", [])
                        self.test_results.append(
                            f"✅ Notes Search: Found {len(notes)} notes"
                        )
                        logger.info(f"  ✅ Notes Search: Found {len(notes)} notes")
                    else:
                        self.test_results.append(
                            f"❌ Notes Search: {data.get('message')}"
                        )
                else:
                    self.test_results.append(
                        f"❌ Notes Search: HTTP {response.status_code}"
                    )
        except Exception as e:
            self.test_results.append(f"❌ Notes Search: {str(e)}")

    def print_summary(self):
        """Print test summary"""
        logger.info("\n" + "=" * 60)
        logger.info("🏁 PHASE 2 IMPLEMENTATION TEST SUMMARY")
        logger.info("=" * 60)

        passed = sum(1 for result in self.test_results if result.startswith("✅"))
        failed = sum(1 for result in self.test_results if result.startswith("❌"))
        total = len(self.test_results)

        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Success Rate: {passed / total * 100:.1f}%")

        logger.info("\nDetailed Results:")
        for result in self.test_results:
            logger.info(f"  {result}")

        if failed == 0:
            logger.info("\n🎉 ALL TESTS PASSED! Phase 2 implementation is complete.")
        else:
            logger.info(
                f"\n⚠️  {failed} tests failed. Check the detailed results above."
            )

        logger.info("=" * 60)


async def main():
    """Main entry point"""
    tester = Phase2Tester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
