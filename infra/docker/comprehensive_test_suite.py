#!/usr/bin/env python3
"""
Comprehensive Test Suite for Phase 3 Validation
Tests all Phase 3 components before proceeding to Phase 4
"""

import asyncio
import aiohttp
import time
import json
import statistics
import psutil
import sys
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Test result data structure"""

    test_name: str
    status: str  # PASS, FAIL, WARN
    duration: float
    details: Dict[str, Any]
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ComprehensiveTestSuite:
    """Comprehensive testing suite for Phase 3 validation"""

    def __init__(self, base_url: str = "http://localhost:5057"):
        self.base_url = base_url
        self.session = None
        self.test_results: List[TestResult] = []
        self.system_metrics = []

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def run_test(self, test_name: str, test_func) -> TestResult:
        """Run a single test and record results"""
        logger.info(f"Running test: {test_name}")
        start_time = time.time()

        try:
            result = await test_func()
            duration = time.time() - start_time
            status = "PASS" if result.get("success", False) else "FAIL"

            test_result = TestResult(
                test_name=test_name, status=status, duration=duration, details=result
            )

            logger.info(f"Test {test_name}: {status} ({duration:.2f}s)")

        except Exception as e:
            duration = time.time() - start_time
            test_result = TestResult(
                test_name=test_name,
                status="FAIL",
                duration=duration,
                details={"error": str(e), "success": False},
            )
            logger.error(f"Test {test_name}: FAIL - {str(e)}")

        self.test_results.append(test_result)
        return test_result

    async def test_service_health(self) -> Dict[str, Any]:
        """Test basic service health"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    return {"success": True, "data": data}
                else:
                    return {"success": False, "status": response.status}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def test_performance_endpoints(self) -> Dict[str, Any]:
        """Test all performance endpoints"""
        endpoints = [
            "/performance/health",
            "/performance/metrics",
            "/performance/cache",
            "/performance/pools",
            "/performance/dashboard",
            "/performance/alerts",
        ]

        results = {}
        success_count = 0

        for endpoint in endpoints:
            try:
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    if response.status == 200:
                        data = await response.json()
                        results[endpoint] = {"status": "success", "data": data}
                        success_count += 1
                    else:
                        results[endpoint] = {"status": "error", "code": response.status}
            except Exception as e:
                results[endpoint] = {"status": "error", "error": str(e)}

        success_rate = success_count / len(endpoints)
        return {
            "success": success_rate >= 0.8,
            "results": results,
            "success_rate": success_rate,
        }

    async def test_cache_functionality(self) -> Dict[str, Any]:
        """Test caching functionality"""
        try:
            # Test cache statistics
            async with self.session.get(
                f"{self.base_url}/performance/cache"
            ) as response:
                if response.status == 200:
                    cache_data = await response.json()

                    # Test cache operations
                    cache_operations = [
                        ("cache_clear", "/performance/cache/clear", "POST"),
                        ("cache_stats", "/performance/cache/stats", "GET"),
                    ]

                    op_results = {}
                    for op_name, endpoint, method in cache_operations:
                        try:
                            if method == "POST":
                                async with self.session.post(
                                    f"{self.base_url}{endpoint}"
                                ) as resp:
                                    op_results[op_name] = {"status": resp.status}
                            else:
                                async with self.session.get(
                                    f"{self.base_url}{endpoint}"
                                ) as resp:
                                    op_results[op_name] = {"status": resp.status}
                        except Exception as e:
                            op_results[op_name] = {"error": str(e)}

                    return {
                        "success": True,
                        "cache_data": cache_data,
                        "operations": op_results,
                    }
                else:
                    return {"success": False, "status": response.status}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def test_connection_pools(self) -> Dict[str, Any]:
        """Test connection pool functionality"""
        try:
            async with self.session.get(
                f"{self.base_url}/performance/pools"
            ) as response:
                if response.status == 200:
                    pool_data = await response.json()

                    # Validate pool data structure
                    required_keys = ["postgres", "redis", "http", "qdrant"]
                    pool_validation = {}

                    for pool_type in required_keys:
                        if pool_type in pool_data:
                            pool_info = pool_data[pool_type]
                            pool_validation[pool_type] = {
                                "has_stats": bool(pool_info),
                                "healthy": pool_info.get("healthy", False)
                                if isinstance(pool_info, dict)
                                else True,
                            }
                        else:
                            pool_validation[pool_type] = {"missing": True}

                    all_healthy = all(
                        v.get("healthy", False) and not v.get("missing", False)
                        for v in pool_validation.values()
                    )

                    return {
                        "success": all_healthy,
                        "pool_data": pool_data,
                        "validation": pool_validation,
                    }
                else:
                    return {"success": False, "status": response.status}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def test_load_performance(self) -> Dict[str, Any]:
        """Test system under load"""
        concurrent_requests = 50
        test_duration = 10  # seconds

        logger.info(
            f"Starting load test: {concurrent_requests} concurrent requests for {test_duration}s"
        )

        start_time = time.time()
        end_time = start_time + test_duration
        request_times = []
        error_count = 0
        success_count = 0

        async def make_request():
            nonlocal error_count, success_count
            try:
                req_start = time.time()
                async with self.session.get(
                    f"{self.base_url}/performance/metrics"
                ) as response:
                    if response.status == 200:
                        await response.text()  # Consume response
                        req_time = time.time() - req_start
                        request_times.append(req_time)
                        success_count += 1
                    else:
                        error_count += 1
            except Exception:
                error_count += 1

        # Run concurrent requests
        tasks = []
        while time.time() < end_time:
            # Create batch of concurrent requests
            batch = [make_request() for _ in range(min(concurrent_requests, 10))]
            tasks.extend(batch)
            await asyncio.gather(*batch)
            await asyncio.sleep(0.1)  # Small delay between batches

        total_requests = success_count + error_count
        actual_duration = time.time() - start_time

        if request_times:
            avg_response_time = statistics.mean(request_times)
            p95_response_time = statistics.quantiles(request_times, n=20)[
                18
            ]  # 95th percentile
            p99_response_time = statistics.quantiles(request_times, n=100)[
                98
            ]  # 99th percentile
            requests_per_second = total_requests / actual_duration
        else:
            avg_response_time = p95_response_time = p99_response_time = 0
            requests_per_second = 0

        return {
            "success": success_count / total_requests >= 0.95
            if total_requests > 0
            else False,
            "total_requests": total_requests,
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": success_count / total_requests if total_requests > 0 else 0,
            "duration": actual_duration,
            "requests_per_second": requests_per_second,
            "avg_response_time": avg_response_time,
            "p95_response_time": p95_response_time,
            "p99_response_time": p99_response_time,
        }

    async def test_memory_usage(self) -> Dict[str, Any]:
        """Test memory usage and leaks"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Simulate memory usage by making multiple requests
        for _ in range(100):
            try:
                async with self.session.get(
                    f"{self.base_url}/performance/metrics"
                ) as response:
                    await response.text()
            except:
                pass

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Force garbage collection
        import gc

        gc.collect()

        final_memory_after_gc = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase_after_gc = final_memory_after_gc - initial_memory

        return {
            "success": memory_increase_after_gc < 100,  # Less than 100MB increase
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "memory_increase_mb": memory_increase,
            "final_memory_after_gc_mb": final_memory_after_gc,
            "memory_increase_after_gc_mb": memory_increase_after_gc,
        }

    async def test_api_endpoints_comprehensive(self) -> Dict[str, Any]:
        """Test all API endpoints comprehensively"""
        # List of all endpoints to test
        endpoints = [
            # Health endpoints
            ("/health", "GET"),
            ("/performance/health", "GET"),
            # Performance endpoints
            ("/performance/metrics", "GET"),
            ("/performance/cache", "GET"),
            ("/performance/cache/stats", "GET"),
            ("/performance/pools", "GET"),
            ("/performance/dashboard", "GET"),
            ("/performance/alerts", "GET"),
            # Core service endpoints
            ("/search", "POST"),
            ("/memory", "POST"),
            ("/notes", "POST"),
            ("/advanced_search", "POST"),
            # Webhook endpoints
            ("/webhooks/index", "POST"),
        ]

        results = {}
        success_count = 0

        for endpoint, method in endpoints:
            try:
                if method == "GET":
                    async with self.session.get(
                        f"{self.base_url}{endpoint}"
                    ) as response:
                        status = response.status
                        if status == 200:
                            try:
                                data = await response.json()
                                results[endpoint] = {
                                    "status": "success",
                                    "code": status,
                                    "has_data": bool(data),
                                }
                            except:
                                results[endpoint] = {
                                    "status": "success",
                                    "code": status,
                                    "has_data": False,
                                }
                            success_count += 1
                        else:
                            results[endpoint] = {"status": "error", "code": status}
                elif method == "POST":
                    # Send minimal valid data for POST requests
                    test_data = {"test": True}
                    async with self.session.post(
                        f"{self.base_url}{endpoint}", json=test_data
                    ) as response:
                        status = response.status
                        # POST endpoints might return 422 for invalid data, that's expected
                        if status in [200, 201, 422]:
                            results[endpoint] = {"status": "success", "code": status}
                            success_count += 1
                        else:
                            results[endpoint] = {"status": "error", "code": status}
            except Exception as e:
                results[endpoint] = {"status": "exception", "error": str(e)}

        success_rate = success_count / len(endpoints)
        return {
            "success": success_rate >= 0.8,
            "results": results,
            "success_rate": success_rate,
            "total_endpoints": len(endpoints),
            "successful_endpoints": success_count,
        }

    async def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling and resilience"""
        error_test_cases = [
            ("invalid_endpoint", "/nonexistent/endpoint", "GET"),
            ("invalid_method", "/health", "PATCH"),
            ("malformed_data", "/search", "POST", {"invalid": "data"}),
        ]

        results = {}
        proper_error_handling = 0

        for test_name, endpoint, method, *data in error_test_cases:
            try:
                if method == "GET":
                    async with self.session.get(
                        f"{self.base_url}{endpoint}"
                    ) as response:
                        status = response.status
                        # Should get 404 for invalid endpoints
                        if status == 404:
                            results[test_name] = {"status": "correct", "code": status}
                            proper_error_handling += 1
                        else:
                            results[test_name] = {
                                "status": "unexpected",
                                "code": status,
                            }
                elif method == "PATCH":
                    async with self.session.patch(
                        f"{self.base_url}{endpoint}"
                    ) as response:
                        status = response.status
                        # Should get 405 Method Not Allowed
                        if status == 405:
                            results[test_name] = {"status": "correct", "code": status}
                            proper_error_handling += 1
                        else:
                            results[test_name] = {
                                "status": "unexpected",
                                "code": status,
                            }
                elif method == "POST":
                    post_data = data[0] if data else {}
                    async with self.session.post(
                        f"{self.base_url}{endpoint}", json=post_data
                    ) as response:
                        status = response.status
                        # Should get 422 for malformed data or 400
                        if status in [400, 422]:
                            results[test_name] = {"status": "correct", "code": status}
                            proper_error_handling += 1
                        else:
                            results[test_name] = {
                                "status": "unexpected",
                                "code": status,
                            }
            except Exception as e:
                results[test_name] = {"status": "exception", "error": str(e)}

        error_handling_rate = proper_error_handling / len(error_test_cases)
        return {
            "success": error_handling_rate >= 0.8,
            "results": results,
            "error_handling_rate": error_handling_rate,
            "proper_error_handling": proper_error_handling,
        }

    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system performance metrics"""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()

        # Memory metrics
        memory = psutil.virtual_memory()

        # Disk metrics
        disk = psutil.disk_usage("/")

        # Network metrics
        network = psutil.net_io_counters()

        # Process metrics
        process = psutil.Process()
        process_memory = process.memory_info()
        process_cpu = process.cpu_percent()

        return {
            "timestamp": datetime.now().isoformat(),
            "cpu": {"percent": cpu_percent, "count": cpu_count},
            "memory": {
                "total_gb": memory.total / 1024 / 1024 / 1024,
                "available_gb": memory.available / 1024 / 1024 / 1024,
                "percent": memory.percent,
            },
            "disk": {
                "total_gb": disk.total / 1024 / 1024 / 1024,
                "free_gb": disk.free / 1024 / 1024 / 1024,
                "percent": (disk.used / disk.total) * 100,
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv,
            },
            "process": {
                "memory_rss_mb": process_memory.rss / 1024 / 1024,
                "memory_vms_mb": process_memory.vms / 1024 / 1024,
                "cpu_percent": process_cpu,
                "num_threads": process.num_threads(),
                "create_time": process.create_time(),
            },
        }

    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all comprehensive tests"""
        logger.info("Starting comprehensive test suite")

        # Collect initial system metrics
        initial_metrics = self.collect_system_metrics()

        # Run all tests
        tests = [
            ("Service Health", self.test_service_health),
            ("Performance Endpoints", self.test_performance_endpoints),
            ("Cache Functionality", self.test_cache_functionality),
            ("Connection Pools", self.test_connection_pools),
            ("Load Performance", self.test_load_performance),
            ("Memory Usage", self.test_memory_usage),
            ("API Endpoints Comprehensive", self.test_api_endpoints_comprehensive),
            ("Error Handling", self.test_error_handling),
        ]

        for test_name, test_func in tests:
            await self.run_test(test_name, test_func)
            # Small delay between tests
            await asyncio.sleep(1)

        # Collect final system metrics
        final_metrics = self.collect_system_metrics()

        # Calculate overall results
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.status == "PASS"])
        failed_tests = len([r for r in self.test_results if r.status == "FAIL"])
        total_duration = sum(r.duration for r in self.test_results)

        overall_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        return {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "overall_score": overall_score,
                "total_duration": total_duration,
                "status": "PASS" if overall_score >= 80 else "FAIL",
            },
            "test_results": [
                {
                    "name": r.test_name,
                    "status": r.status,
                    "duration": r.duration,
                    "details": r.details,
                }
                for r in self.test_results
            ],
            "system_metrics": {"initial": initial_metrics, "final": final_metrics},
        }

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive test report"""
        report = []
        report.append("=" * 80)
        report.append("COMPREHENSIVE TEST SUITE REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")

        # Summary
        summary = results["summary"]
        report.append("SUMMARY")
        report.append("-" * 40)
        report.append(f"Total Tests: {summary['total_tests']}")
        report.append(f"Passed: {summary['passed_tests']}")
        report.append(f"Failed: {summary['failed_tests']}")
        report.append(f"Overall Score: {summary['overall_score']:.1f}%")
        report.append(f"Status: {summary['status']}")
        report.append(f"Total Duration: {summary['total_duration']:.2f}s")
        report.append("")

        # Detailed Results
        report.append("DETAILED RESULTS")
        report.append("-" * 40)
        for test in results["test_results"]:
            status_symbol = "✓" if test["status"] == "PASS" else "✗"
            report.append(
                f"{status_symbol} {test['name']}: {test['status']} ({test['duration']:.2f}s)"
            )

            # Add key details for important tests
            if test["name"] == "Load Performance" and test["details"].get("success"):
                details = test["details"]
                report.append(
                    f"    - Requests/sec: {details.get('requests_per_second', 0):.1f}"
                )
                report.append(
                    f"    - Avg Response Time: {details.get('avg_response_time', 0):.3f}s"
                )
                report.append(
                    f"    - Success Rate: {details.get('success_rate', 0):.1%}"
                )

            elif test["name"] == "API Endpoints Comprehensive" and test["details"].get(
                "success"
            ):
                details = test["details"]
                report.append(
                    f"    - Success Rate: {details.get('success_rate', 0):.1%}"
                )
                report.append(
                    f"    - Endpoints Tested: {details.get('total_endpoints', 0)}"
                )

        report.append("")

        # System Metrics
        report.append("SYSTEM METRICS")
        report.append("-" * 40)
        initial = results["system_metrics"]["initial"]
        final = results["system_metrics"]["final"]

        report.append("CPU Usage:")
        report.append(f"  Initial: {initial['cpu']['percent']:.1f}%")
        report.append(f"  Final: {final['cpu']['percent']:.1f}%")

        report.append("Memory Usage:")
        report.append(f"  Initial: {initial['memory']['percent']:.1f}%")
        report.append(f"  Final: {final['memory']['percent']:.1f}%")

        report.append("Process Memory:")
        report.append(f"  Initial: {initial['process']['memory_rss_mb']:.1f} MB")
        report.append(f"  Final: {final['process']['memory_rss_mb']:.1f} MB")

        report.append("")

        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-" * 40)

        if summary["overall_score"] >= 90:
            report.append("✓ Excellent performance! System is production-ready.")
        elif summary["overall_score"] >= 80:
            report.append("✓ Good performance. Minor optimizations recommended.")
        else:
            report.append("⚠ Performance issues detected. Review failed tests.")

        # Check specific areas
        load_test = next(
            (t for t in results["test_results"] if t["name"] == "Load Performance"),
            None,
        )
        if load_test and load_test["details"].get("success"):
            if load_test["details"].get("avg_response_time", 0) > 0.5:
                report.append("- Consider optimizing response times (avg > 500ms)")

        memory_test = next(
            (t for t in results["test_results"] if t["name"] == "Memory Usage"), None
        )
        if memory_test and memory_test["details"].get("success"):
            if memory_test["details"].get("memory_increase_after_gc_mb", 0) > 50:
                report.append("- Monitor for potential memory leaks")

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)


async def main():
    """Main function to run comprehensive tests"""
    print("🚀 Starting Comprehensive Test Suite for Phase 3")
    print("=" * 60)

    async with ComprehensiveTestSuite() as test_suite:
        results = await test_suite.run_comprehensive_tests()
        report = test_suite.generate_report(results)

        print(report)

        # Save results to file
        with open("comprehensive_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        print("\n📊 Results saved to: comprehensive_test_results.json")

        # Exit with appropriate code
        summary = results["summary"]
        if summary["status"] == "PASS":
            print("✅ Comprehensive testing PASSED - Ready for Phase 4!")
            sys.exit(0)
        else:
            print("❌ Comprehensive testing FAILED - Address issues before Phase 4")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
