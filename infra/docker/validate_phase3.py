#!/usr/bin/env python3
"""
Phase 3 Validation Script - Performance Optimization & Monitoring
"""

import ast
import os
import sys
from pathlib import Path


def validate_file_exists(filepath, description):
    """Validate that a file exists"""
    if os.path.exists(filepath):
        print(f"✅ {description} exists")
        return True
    else:
        print(f"❌ {description} missing: {filepath}")
        return False


def validate_python_syntax(filepath):
    """Validate Python syntax"""
    try:
        with open(filepath, "r") as f:
            content = f.read()
            ast.parse(content)
        print(f"✅ {filepath} has valid Python syntax")
        return True
    except SyntaxError as e:
        print(f"❌ {filepath} syntax error: {e}")
        return False
    except Exception as e:
        print(f"❌ {filepath} validation error: {e}")
        return False


def validate_class_structure(filepath, expected_classes):
    """Validate expected classes exist in file"""
    try:
        with open(filepath, "r") as f:
            content = f.read()
            tree = ast.parse(content)

        found_classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                found_classes.append(node.name)

        all_found = True
        for class_name in expected_classes:
            if class_name in found_classes:
                print(f"✅ {class_name} class found in {filepath}")
            else:
                print(f"❌ {class_name} class missing in {filepath}")
                all_found = False

        return all_found
    except Exception as e:
        print(f"❌ Error validating {filepath}: {e}")
        return False


def validate_function_structure(filepath, expected_functions):
    """Validate expected functions/methods exist in file"""
    try:
        with open(filepath, "r") as f:
            content = f.read()
            tree = ast.parse(content)

        found_functions = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                found_functions.append(node.name)

        all_found = True
        for func_name in expected_functions:
            if func_name in found_functions:
                print(f"✅ {func_name} function/method found in {filepath}")
            else:
                print(f"❌ {func_name} function/method missing in {filepath}")
                all_found = False

        return all_found
    except Exception as e:
        print(f"❌ Error validating {filepath}: {e}")
        return False


def validate_imports(filepath, expected_imports):
    """Validate expected imports exist in file"""
    try:
        with open(filepath, "r") as f:
            content = f.read()

        all_found = True
        for import_name in expected_imports:
            if import_name in content:
                print(f"✅ {import_name} import found in {filepath}")
            else:
                print(f"❌ {import_name} import missing in {filepath}")
                all_found = False

        return all_found
    except Exception as e:
        print(f"❌ Error validating {filepath}: {e}")
        return False


def main():
    """Main validation function"""
    print("🔧 Phase 3 Validation - Performance Optimization & Monitoring")
    print("=" * 60)

    # Change to the correct directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    validation_results = []

    # 1. Validate File Structure
    print("\n🔍 Validating File Structure...")

    files_to_check = [
        ("gateway/app/services/caching.py", "Caching Service"),
        ("gateway/app/services/connection_pool.py", "Connection Pool Service"),
        ("gateway/app/services/performance_monitor.py", "Performance Monitor Service"),
        ("gateway/app/routers/performance.py", "Performance Router"),
    ]

    for filepath, description in files_to_check:
        result = validate_file_exists(filepath, description)
        validation_results.append(result)

    # 2. Validate Caching Service
    print("\n🏗️ Validating Caching Service...")
    caching_classes = ["CacheConfig", "CacheEntry", "CachingService"]
    result = validate_class_structure(
        "gateway/app/services/caching.py", caching_classes
    )
    validation_results.append(result)

    caching_functions = [
        "get",
        "set",
        "delete",
        "clear_prefix",
        "get_stats",
        "health_check",
    ]
    result = validate_function_structure(
        "gateway/app/services/caching.py", caching_functions
    )
    validation_results.append(result)

    # 3. Validate Connection Pool Service
    print("\n🏗️ Validating Connection Pool Service...")
    pool_classes = ["PoolConfig", "PoolStats", "ConnectionPoolService"]
    result = validate_class_structure(
        "gateway/app/services/connection_pool.py", pool_classes
    )
    validation_results.append(result)

    pool_functions = [
        "initialize",
        "get_postgres_connection",
        "get_redis_client",
        "get_http_client",
        "get_qdrant_client",
    ]
    result = validate_function_structure(
        "gateway/app/services/connection_pool.py", pool_functions
    )
    validation_results.append(result)

    # 4. Validate Performance Monitor Service
    print("\n🏗️ Validating Performance Monitor Service...")
    monitor_classes = [
        "MetricType",
        "MetricValue",
        "PerformanceMetric",
        "PerformanceMonitor",
    ]
    result = validate_class_structure(
        "gateway/app/services/performance_monitor.py", monitor_classes
    )
    validation_results.append(result)

    monitor_functions = [
        "register_metric",
        "record_metric",
        "increment_counter",
        "set_gauge",
        "record_timer",
    ]
    result = validate_function_structure(
        "gateway/app/services/performance_monitor.py", monitor_functions
    )
    validation_results.append(result)

    # 5. Validate Performance Router
    print("\n🏗️ Validating Performance Router...")
    router_functions = [
        "get_metrics",
        "get_metric_details",
        "record_metric",
        "register_metric",
        "get_alerts",
        "set_alert_threshold",
        "get_connection_pool_stats",
        "get_cache_stats",
        "clear_cache",
        "warm_cache",
        "get_performance_health",
        "get_performance_dashboard",
        "run_benchmark",
    ]
    result = validate_function_structure(
        "gateway/app/routers/performance.py", router_functions
    )
    validation_results.append(result)

    # 6. Validate Main.py Integration
    print("\n🔗 Validating Main.py Integration...")

    main_imports = [
        "from app.services.caching import CachingService, CacheConfig",
        "from app.services.connection_pool import ConnectionPoolService, PoolConfig, init_pool_service",
        "from app.services.performance_monitor import init_performance_monitor",
        "from app.routers import performance",
    ]
    result = validate_imports("gateway/app/main.py", main_imports)
    validation_results.append(result)

    main_initializations = [
        "cache_service = CachingService(cache_config)",
        "pool_service = await init_pool_service(",
        "performance_monitor = await init_performance_monitor(",
        "performance.init_services(performance_monitor, pool_service, cache_service)",
        'app.include_router(performance.router, prefix="/performance"',
    ]
    result = validate_function_structure("gateway/app/main.py", main_initializations)
    validation_results.append(result)

    # 7. Validate Requirements.txt
    print("\n📦 Validating Requirements.txt...")
    required_packages = [
        "psutil>=5.9.0",
        "asyncpg>=0.29.0",
        "sqlalchemy[asyncio]>=2.0.23",
    ]
    result = validate_imports("gateway/requirements.txt", required_packages)
    validation_results.append(result)

    # 8. Validate Python Syntax
    print("\n✅ Validating Python Syntax...")
    python_files = [
        "gateway/app/services/caching.py",
        "gateway/app/services/connection_pool.py",
        "gateway/app/services/performance_monitor.py",
        "gateway/app/routers/performance.py",
        "gateway/app/main.py",
    ]

    for filepath in python_files:
        if os.path.exists(filepath):
            result = validate_python_syntax(filepath)
            validation_results.append(result)

    # Summary
    print("\n📊 Validation Summary:")
    passed = sum(validation_results)
    total = len(validation_results)
    success_rate = (passed / total) * 100 if total > 0 else 0

    print(f"✅ Passed: {passed}/{total} ({success_rate:.1f}%)")
    print(f"❌ Failed: {total - passed}/{total} ({100 - success_rate:.1f}%)")

    if success_rate >= 90:
        print("\n🎉 Phase 3 Validation: PASSED")
        print("The performance optimization implementation is ready!")
        return True
    else:
        print("\n❌ Phase 3 Validation: FAILED")
        print("Please fix the issues before proceeding.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
