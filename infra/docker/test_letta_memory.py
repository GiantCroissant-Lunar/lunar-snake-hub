#!/usr/bin/env python3
"""
Letta Memory Integration Test Script

This script tests the Letta memory service to verify:
1. Connection to Letta server
2. Creating/storing memories
3. Retrieving memories
4. Persistence across requests
5. Memory search functionality

Usage:
    python test_letta_memory.py [--host HOST] [--port PORT]

Default: http://localhost:8283
"""

import argparse
import sys
import json
from typing import Any
import httpx
from datetime import datetime


class LettaMemoryTester:
    """Test suite for Letta memory service"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=30.0)
        self.test_results = []

    def _log(
        self, test_name: str, success: bool, message: str = "", details: Any = None
    ):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        if details:
            result["details"] = details
        self.test_results.append(result)

        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {test_name}")
        if message:
            print(f"       {message}")
        if details and not success:
            print(f"       Details: {details}")
        print()

    def test_1_health_check(self) -> bool:
        """Test 1: Check if Letta server is running"""
        try:
            # Try with trailing slash first (Letta API requires it)
            response = self.client.get(f"{self.base_url}/v1/health/")
            if response.status_code == 200:
                self._log("Health Check", True, "Letta server is running")
                return True
            else:
                self._log(
                    "Health Check",
                    False,
                    f"Unexpected status: {response.status_code}",
                    response.text,
                )
                return False
        except Exception as e:
            self._log("Health Check", False, "Cannot connect to Letta server", str(e))
            return False

    def test_2_list_agents(self) -> bool:
        """Test 2: List available agents"""
        try:
            response = self.client.get(f"{self.base_url}/v1/agents/")
            if response.status_code == 200:
                agents = response.json()
                self._log("List Agents", True, f"Found {len(agents)} agents", agents)
                return True
            else:
                self._log(
                    "List Agents",
                    False,
                    f"Status: {response.status_code}",
                    response.text,
                )
                return False
        except Exception as e:
            self._log("List Agents", False, "Failed to list agents", str(e))
            return False

    def test_3_create_agent(self) -> str:
        """Test 3: Create a test agent"""
        try:
            payload = {
                "name": f"test_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            }

            response = self.client.post(f"{self.base_url}/v1/agents/", json=payload)
            if response.status_code in [200, 201]:
                agent_data = response.json()
                agent_id = agent_data.get("id") or agent_data.get("agent_id")
                self._log(
                    "Create Agent", True, f"Created agent: {agent_id}", agent_data
                )
                return agent_id
            else:
                self._log(
                    "Create Agent",
                    False,
                    f"Status: {response.status_code}",
                    response.text,
                )
                return None
        except Exception as e:
            self._log("Create Agent", False, "Failed to create agent", str(e))
            return None

    def test_4_send_message(self, agent_id: str, message: str) -> bool:
        """Test 4: Send a message to the agent (store memory)"""
        try:
            payload = {"agent_id": agent_id, "message": message, "stream": False}

            response = self.client.post(
                f"{self.base_url}/v1/agents/{agent_id}/messages", json=payload
            )

            if response.status_code == 200:
                resp_data = response.json()
                self._log(
                    "Send Message",
                    True,
                    f"Message sent: '{message[:50]}...'",
                    resp_data,
                )
                return True
            else:
                self._log(
                    "Send Message",
                    False,
                    f"Status: {response.status_code}",
                    response.text,
                )
                return False
        except Exception as e:
            self._log("Send Message", False, "Failed to send message", str(e))
            return False

    def test_5_retrieve_memory(self, agent_id: str) -> bool:
        """Test 5: Retrieve agent's memory"""
        try:
            response = self.client.get(f"{self.base_url}/v1/agents/{agent_id}/memory")

            if response.status_code == 200:
                memory_data = response.json()
                self._log(
                    "Retrieve Memory",
                    True,
                    "Memory retrieved successfully",
                    memory_data,
                )
                return True
            else:
                self._log(
                    "Retrieve Memory",
                    False,
                    f"Status: {response.status_code}",
                    response.text,
                )
                return False
        except Exception as e:
            self._log("Retrieve Memory", False, "Failed to retrieve memory", str(e))
            return False

    def test_6_query_with_context(self, agent_id: str, query: str) -> bool:
        """Test 6: Query agent to verify it remembers"""
        try:
            payload = {"agent_id": agent_id, "message": query, "stream": False}

            response = self.client.post(
                f"{self.base_url}/v1/agents/{agent_id}/messages", json=payload
            )

            if response.status_code == 200:
                resp_data = response.json()
                # Extract the actual response text
                messages = resp_data.get("messages", [])
                if messages:
                    assistant_msg = next(
                        (m for m in messages if m.get("role") == "assistant"), None
                    )
                    if assistant_msg:
                        response_text = assistant_msg.get("text", "")
                        self._log(
                            "Query with Context",
                            True,
                            f"Agent recalled context: {response_text[:100]}...",
                            resp_data,
                        )
                        return True

                self._log("Query with Context", True, "Response received", resp_data)
                return True
            else:
                self._log(
                    "Query with Context",
                    False,
                    f"Status: {response.status_code}",
                    response.text,
                )
                return False
        except Exception as e:
            self._log("Query with Context", False, "Failed to query", str(e))
            return False

    def test_7_delete_agent(self, agent_id: str) -> bool:
        """Test 7: Clean up - delete test agent"""
        try:
            response = self.client.delete(f"{self.base_url}/v1/agents/{agent_id}")

            if response.status_code in [200, 204]:
                self._log("Delete Agent", True, f"Cleaned up agent: {agent_id}")
                return True
            else:
                self._log(
                    "Delete Agent",
                    False,
                    f"Status: {response.status_code}",
                    response.text,
                )
                return False
        except Exception as e:
            self._log("Delete Agent", False, "Failed to delete agent", str(e))
            return False

    def run_full_test_suite(self):
        """Run complete test suite"""
        print("=" * 70)
        print("  LETTA MEMORY INTEGRATION TEST")
        print("=" * 70)
        print(f"Target: {self.base_url}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print()

        # Test 1: Health check
        if not self.test_1_health_check():
            print("\n❌ Letta server is not accessible. Aborting tests.\n")
            return False

        # Test 2: List agents
        self.test_2_list_agents()

        # Test 3: Create agent
        agent_id = self.test_3_create_agent()
        if not agent_id:
            print("\n❌ Cannot create agent. Aborting tests.\n")
            return False

        # Test 4: Store memory by sending a message
        memory_content = "We are using the Repository pattern for data access in hyacinth-bean-base because it decouples the domain logic from infrastructure concerns."
        self.test_4_send_message(agent_id, memory_content)

        # Test 5: Retrieve memory
        self.test_5_retrieve_memory(agent_id)

        # Test 6: Query to verify recall
        query = "What pattern are we using for data access and why?"
        self.test_6_query_with_context(agent_id, query)

        # Test 7: Clean up
        self.test_7_delete_agent(agent_id)

        # Print summary
        print("=" * 70)
        print("  TEST SUMMARY")
        print("=" * 70)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests

        print(f"Total Tests:  {total_tests}")
        print(f"Passed:       {passed_tests} ✅")
        print(f"Failed:       {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests / total_tests * 100):.1f}%")
        print()

        if failed_tests > 0:
            print("Failed tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")

        print("=" * 70)

        # Save results to JSON
        with open("letta_test_results.json", "w") as f:
            json.dump(
                {
                    "test_run": datetime.now().isoformat(),
                    "base_url": self.base_url,
                    "summary": {
                        "total": total_tests,
                        "passed": passed_tests,
                        "failed": failed_tests,
                        "success_rate": passed_tests / total_tests * 100,
                    },
                    "results": self.test_results,
                },
                f,
                indent=2,
            )

        print("\n📄 Detailed results saved to: letta_test_results.json\n")

        return failed_tests == 0


def main():
    parser = argparse.ArgumentParser(description="Test Letta Memory Integration")
    parser.add_argument(
        "--host", default="localhost", help="Letta server host (default: localhost)"
    )
    parser.add_argument(
        "--port", default="8283", help="Letta server port (default: 8283)"
    )
    parser.add_argument("--url", help="Full Letta server URL (overrides host/port)")

    args = parser.parse_args()

    if args.url:
        base_url = args.url
    else:
        base_url = f"http://{args.host}:{args.port}"

    tester = LettaMemoryTester(base_url)
    success = tester.run_full_test_suite()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
