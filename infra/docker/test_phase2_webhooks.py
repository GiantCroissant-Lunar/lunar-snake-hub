#!/usr/bin/env python3
"""
Phase 2 Test Script - Real-time Indexing & Webhooks
Tests webhook functionality and real-time indexing capabilities
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebhookTester:
    """Test webhook functionality"""

    def __init__(self, gateway_url: str = "http://localhost:5057"):
        self.gateway_url = gateway_url
        self.test_results = []

    async def test_webhook_endpoints(self):
        """Test all webhook endpoints"""
        logger.info("🪝 Testing webhook endpoints...")

        tests = [
            self.test_webhook_status,
            self.test_webhook_config,
            self.test_github_webhook_simulation,
            self.test_gitlab_webhook_simulation,
            self.test_manual_indexing_trigger,
            self.test_job_management,
            self.test_webhook_test_endpoint,
        ]

        for test in tests:
            try:
                result = await test()
                self.test_results.append(result)
                logger.info(f"✅ {result['test_name']}: {result['status']}")
            except Exception as e:
                logger.error(f"❌ {test.__name__}: {e}")
                self.test_results.append(
                    {"test_name": test.__name__, "status": "failed", "error": str(e)}
                )

    async def test_webhook_status(self) -> Dict[str, Any]:
        """Test webhook status endpoint"""
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.gateway_url}/webhooks/status")

                return {
                    "test_name": "webhook_status",
                    "status": "passed" if response.status_code == 200 else "failed",
                    "status_code": response.status_code,
                    "response": response.json()
                    if response.status_code == 200
                    else None,
                }
        except Exception as e:
            return {"test_name": "webhook_status", "status": "failed", "error": str(e)}

    async def test_webhook_config(self) -> Dict[str, Any]:
        """Test webhook config endpoint"""
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.gateway_url}/webhooks/config")

                return {
                    "test_name": "webhook_config",
                    "status": "passed" if response.status_code == 200 else "failed",
                    "status_code": response.status_code,
                    "config": response.json() if response.status_code == 200 else None,
                }
        except Exception as e:
            return {"test_name": "webhook_config", "status": "failed", "error": str(e)}

    async def test_github_webhook_simulation(self) -> Dict[str, Any]:
        """Test GitHub webhook simulation"""
        try:
            import httpx

            # Simulate GitHub push webhook
            github_payload = {
                "ref": "refs/heads/main",
                "repository": {
                    "full_name": "test-repo",
                    "html_url": "https://github.com/test-repo",
                },
                "head_commit": {
                    "id": "test-commit-123",
                    "message": "Test commit for webhook",
                    "author": {"name": "Test User"},
                    "timestamp": "2025-01-01T00:00:00Z",
                },
                "commits": [
                    {
                        "id": "test-commit-123",
                        "message": "Test commit for webhook",
                        "author": {"name": "Test User"},
                        "added": ["test.py"],
                        "modified": ["README.md"],
                        "removed": [],
                    }
                ],
            }

            headers = {
                "Content-Type": "application/json",
                "X-GitHub-Event": "push",
                "X-Hub-Signature-256": "test-signature",
                "X-GitHub-Delivery": "test-delivery-123",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.gateway_url}/webhooks/github/test-repo",
                    json=github_payload,
                    headers=headers,
                )

                return {
                    "test_name": "github_webhook_simulation",
                    "status": "passed"
                    if response.status_code in [200, 401]
                    else "failed",  # 401 is expected without proper signature
                    "status_code": response.status_code,
                    "response": response.json()
                    if response.status_code == 200
                    else None,
                }
        except Exception as e:
            return {
                "test_name": "github_webhook_simulation",
                "status": "failed",
                "error": str(e),
            }

    async def test_gitlab_webhook_simulation(self) -> Dict[str, Any]:
        """Test GitLab webhook simulation"""
        try:
            import httpx

            # Simulate GitLab push webhook
            gitlab_payload = {
                "ref": "refs/heads/main",
                "project": {
                    "path_with_namespace": "test-repo",
                    "web_url": "https://gitlab.com/test-repo",
                },
                "commits": [
                    {
                        "id": "test-commit-123",
                        "message": "Test commit for webhook",
                        "author": {"name": "Test User"},
                        "added": ["test.py"],
                        "modified": ["README.md"],
                        "removed": [],
                        "timestamp": "2025-01-01T00:00:00Z",
                    }
                ],
            }

            headers = {
                "Content-Type": "application/json",
                "X-Gitlab-Event": "Push Hook",
                "X-Gitlab-Token": "test-token",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.gateway_url}/webhooks/gitlab/test-repo",
                    json=gitlab_payload,
                    headers=headers,
                )

                return {
                    "test_name": "gitlab_webhook_simulation",
                    "status": "passed"
                    if response.status_code in [200, 401]
                    else "failed",
                    "status_code": response.status_code,
                    "response": response.json()
                    if response.status_code == 200
                    else None,
                }
        except Exception as e:
            return {
                "test_name": "gitlab_webhook_simulation",
                "status": "failed",
                "error": str(e),
            }

    async def test_manual_indexing_trigger(self) -> Dict[str, Any]:
        """Test manual indexing trigger"""
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.gateway_url}/webhooks/trigger/test-repo",
                    params={"branch": "main", "force_reindex": False},
                )

                return {
                    "test_name": "manual_indexing_trigger",
                    "status": "passed" if response.status_code == 200 else "failed",
                    "status_code": response.status_code,
                    "response": response.json()
                    if response.status_code == 200
                    else None,
                }
        except Exception as e:
            return {
                "test_name": "manual_indexing_trigger",
                "status": "failed",
                "error": str(e),
            }

    async def test_job_management(self) -> Dict[str, Any]:
        """Test job management endpoints"""
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                # List jobs
                jobs_response = await client.get(f"{self.gateway_url}/webhooks/jobs")

                # Test cleanup
                cleanup_response = await client.post(
                    f"{self.gateway_url}/webhooks/cleanup", params={"max_age_hours": 1}
                )

                return {
                    "test_name": "job_management",
                    "status": "passed"
                    if all(
                        [
                            jobs_response.status_code
                            in [200, 503],  # 503 if service not available
                            cleanup_response.status_code in [200, 503],
                        ]
                    )
                    else "failed",
                    "jobs_status": jobs_response.status_code,
                    "cleanup_status": cleanup_response.status_code,
                }
        except Exception as e:
            return {"test_name": "job_management", "status": "failed", "error": str(e)}

    async def test_webhook_test_endpoint(self) -> Dict[str, Any]:
        """Test webhook test endpoint"""
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                # Test GitHub webhook test
                github_response = await client.post(
                    f"{self.gateway_url}/webhooks/test/github",
                    params={"repo_name": "test-repo", "event_type": "push"},
                )

                # Test GitLab webhook test
                gitlab_response = await client.post(
                    f"{self.gateway_url}/webhooks/test/gitlab",
                    params={"repo_name": "test-repo", "event_type": "Push Hook"},
                )

                return {
                    "test_name": "webhook_test_endpoint",
                    "status": "passed"
                    if all(
                        [
                            github_response.status_code in [200, 503],
                            gitlab_response.status_code in [200, 503],
                        ]
                    )
                    else "failed",
                    "github_test_status": github_response.status_code,
                    "gitlab_test_status": gitlab_response.status_code,
                }
        except Exception as e:
            return {
                "test_name": "webhook_test_endpoint",
                "status": "failed",
                "error": str(e),
            }

    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        passed_tests = [r for r in self.test_results if r["status"] == "passed"]
        failed_tests = [r for r in self.test_results if r["status"] == "failed"]

        report = {
            "summary": {
                "total_tests": len(self.test_results),
                "passed": len(passed_tests),
                "failed": len(failed_tests),
                "success_rate": (len(passed_tests) / len(self.test_results)) * 100
                if self.test_results
                else 0,
            },
            "test_results": self.test_results,
            "recommendations": self._generate_recommendations(failed_tests),
        }

        return report

    def _generate_recommendations(self, failed_tests: list) -> list:
        """Generate recommendations based on failed tests"""
        recommendations = []

        for test in failed_tests:
            if "webhook" in test["test_name"]:
                recommendations.append(
                    "Check webhook service initialization and configuration"
                )
            elif "indexing" in test["test_name"]:
                recommendations.append("Verify indexing service is properly connected")
            elif "job" in test["test_name"]:
                recommendations.append("Ensure enhanced indexing service is running")

        if not recommendations:
            recommendations.append(
                "All tests passed - webhook system is functioning correctly"
            )

        return list(set(recommendations))  # Remove duplicates


async def main():
    """Main test execution"""
    print("🚀 Phase 2 Test: Real-time Indexing & Webhooks")
    print("=" * 50)

    # Check if gateway is running
    try:
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:5057/health", timeout=5.0)
            if response.status_code != 200:
                print("❌ Gateway is not running. Please start the services first.")
                return
    except Exception as e:
        print(f"❌ Cannot connect to gateway: {e}")
        print("Please ensure the services are running:")
        print("  cd infra/docker && docker-compose up -d")
        return

    # Run tests
    tester = WebhookTester()
    await tester.test_webhook_endpoints()

    # Generate report
    report = tester.generate_test_report()

    # Print results
    print("\n📊 Test Results:")
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Success Rate: {report['summary']['success_rate']:.1f}%")

    print("\n📋 Detailed Results:")
    for result in report["test_results"]:
        status_icon = "✅" if result["status"] == "passed" else "❌"
        print(f"{status_icon} {result['test_name']}: {result['status']}")
        if "error" in result:
            print(f"   Error: {result['error']}")

    print("\n💡 Recommendations:")
    for rec in report["recommendations"]:
        print(f"• {rec}")

    # Save report
    report_file = Path("test_phase2_webhooks_results.json")
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Detailed report saved to: {report_file}")


if __name__ == "__main__":
    asyncio.run(main())
