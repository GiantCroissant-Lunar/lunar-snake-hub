#!/usr/bin/env python3
"""
Phase 4 Validation Script - Advanced Monitoring & Analytics
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


def validate_requirements(filepath, required_packages):
    """Validate required packages exist in requirements.txt"""
    try:
        with open(filepath, "r") as f:
            content = f.read()

        all_found = True
        for package in required_packages:
            if package in content:
                print(f"✅ {package} package found in {filepath}")
            else:
                print(f"❌ {package} package missing in {filepath}")
                all_found = False

        return all_found
    except Exception as e:
        print(f"❌ Error validating {filepath}: {e}")
        return False


def main():
    """Main validation function"""
    print("🔧 Phase 4 Validation - Advanced Monitoring & Analytics")
    print("=" * 60)

    # Change to the correct directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    validation_results = []

    # 1. Validate File Structure
    print("\n🔍 Validating File Structure...")

    files_to_check = [
        ("gateway/app/services/advanced_analytics.py", "Advanced Analytics Service"),
        ("gateway/app/services/distributed_tracing.py", "Distributed Tracing Service"),
        ("gateway/app/services/intelligence_engine.py", "Intelligence Engine Service"),
        ("gateway/app/services/advanced_dashboard.py", "Advanced Dashboard Service"),
        ("gateway/app/routers/advanced_analytics.py", "Advanced Analytics Router"),
    ]

    for filepath, description in files_to_check:
        result = validate_file_exists(filepath, description)
        validation_results.append(result)

    # 2. Validate Advanced Analytics Service
    print("\n🏗️ Validating Advanced Analytics Service...")

    analytics_classes = [
        "AnomalyType",
        "AlertSeverity",
        "AnomalyDetection",
        "PerformancePrediction",
        "OptimizationRecommendation",
        "PatternInsight",
        "AdvancedAnalyticsService",
    ]
    result = validate_class_structure(
        "gateway/app/services/advanced_analytics.py", analytics_classes
    )
    validation_results.append(result)

    analytics_functions = [
        "add_metric_data",
        "_analyze_metric",
        "_detect_anomalies",
        "_predict_performance",
        "_analyze_patterns",
        "get_anomalies",
        "get_predictions",
        "get_patterns",
        "generate_optimization_recommendations",
        "get_analytics_summary",
        "health_check",
        "clear_anomalies",
        "clear_predictions",
    ]
    result = validate_function_structure(
        "gateway/app/services/advanced_analytics.py", analytics_functions
    )
    validation_results.append(result)

    # 3. Validate Distributed Tracing Service
    print("\n🏗️ Validating Distributed Tracing Service...")

    tracing_classes = [
        "SpanKind",
        "SpanStatus",
        "TraceSpan",
        "ServiceDependency",
        "PerformanceProfile",
        "DistributedTracingService",
    ]
    result = validate_class_structure(
        "gateway/app/services/distributed_tracing.py", tracing_classes
    )
    validation_results.append(result)

    tracing_functions = [
        "start_span",
        "_update_performance_profile",
        "_update_dependencies",
        "get_trace",
        "get_service_map",
        "get_performance_profiles",
        "get_slow_operations",
        "get_error_spans",
        "get_tracing_summary",
        "search_traces",
        "health_check",
        "clear_old_data",
    ]
    result = validate_function_structure(
        "gateway/app/services/distributed_tracing.py", tracing_functions
    )
    validation_results.append(result)

    # 4. Validate Intelligence Engine Service
    print("\n🏗️ Validating Intelligence Engine Service...")

    intelligence_classes = [
        "InsightType",
        "ModelType",
        "InsightPriority",
        "MLModel",
        "Insight",
        "KnowledgeEntry",
        "IntelligenceEngineService",
    ]
    result = validate_class_structure(
        "gateway/app/services/intelligence_engine.py", intelligence_classes
    )
    validation_results.append(result)

    intelligence_functions = [
        "add_training_data",
        "_train_model",
        "_retrain_models",
        "_generate_insights",
        "_generate_performance_insights",
        "_generate_anomaly_insights",
        "_generate_capacity_insights",
        "_generate_optimization_insights",
        "_generate_risk_insights",
        "_predict_with_model",
        "get_insights",
        "get_models",
        "add_knowledge_entry",
        "search_knowledge",
        "get_intelligence_summary",
        "health_check",
    ]
    result = validate_function_structure(
        "gateway/app/services/intelligence_engine.py", intelligence_functions
    )
    validation_results.append(result)

    # 5. Validate Advanced Dashboard Service
    print("\n🏗️ Validating Advanced Dashboard Service...")

    dashboard_classes = [
        "WidgetType",
        "ChartType",
        "TimeRange",
        "DashboardWidget",
        "DashboardConfig",
        "ChartData",
        "KPIData",
        "AdvancedDashboardService",
    ]
    result = validate_class_structure(
        "gateway/app/services/advanced_dashboard.py", dashboard_classes
    )
    validation_results.append(result)

    dashboard_functions = [
        "_refresh_widget_data",
        "_generate_chart_data",
        "_generate_kpi_data",
        "_generate_alert_data",
        "_generate_service_map_data",
        "_generate_trend_data",
        "_generate_anomaly_data",
        "_generate_performance_table_data",
        "_generate_insight_data",
        "create_dashboard",
        "add_widget_to_dashboard",
        "update_widget",
        "remove_widget_from_dashboard",
        "delete_dashboard",
        "get_dashboard",
        "get_all_dashboards",
        "get_widget_data",
        "get_dashboard_render_data",
        "create_default_dashboard",
        "get_dashboard_summary",
        "health_check",
    ]
    result = validate_function_structure(
        "gateway/app/services/advanced_dashboard.py", dashboard_functions
    )
    validation_results.append(result)

    # 6. Validate Advanced Analytics Router
    print("\n🏗️ Validating Advanced Analytics Router...")

    router_classes = [
        "AnomalyFilter",
        "PredictionFilter",
        "InsightFilter",
        "KnowledgeFilter",
        "TrainingDataRequest",
        "KnowledgeEntryRequest",
        "ModelRequest",
    ]
    result = validate_class_structure(
        "gateway/app/routers/advanced_analytics.py", router_classes
    )
    validation_results.append(result)

    router_functions = [
        "get_anomalies",
        "clear_anomalies",
        "get_predictions",
        "get_patterns",
        "get_recommendations",
        "get_analytics_summary",
        "add_training_data",
        "get_models",
        "add_knowledge_entry",
        "search_knowledge",
        "get_insights",
        "get_intelligence_summary",
        "get_analytics_dashboard",
        "health_check",
        "get_analytics_config",
    ]
    result = validate_function_structure(
        "gateway/app/routers/advanced_analytics.py", router_functions
    )
    validation_results.append(result)

    # 7. Validate Python Syntax
    print("\n✅ Validating Python Syntax...")
    python_files = [
        "gateway/app/services/advanced_analytics.py",
        "gateway/app/services/distributed_tracing.py",
        "gateway/app/services/intelligence_engine.py",
        "gateway/app/services/advanced_dashboard.py",
        "gateway/app/routers/advanced_analytics.py",
    ]

    for filepath in python_files:
        if os.path.exists(filepath):
            result = validate_python_syntax(filepath)
            validation_results.append(result)

    # 8. Validate Requirements.txt for new dependencies
    print("\n📦 Validating Requirements.txt...")

    # Check for Phase 4 specific packages
    phase4_packages = [
        "scikit-learn>=1.3.0",
        "pandas>=2.1.0",
        "numpy>=1.24.0",
        "plotly>=5.15.0",
        "opentelemetry-api>=1.20.0",
        "opentelemetry-sdk>=1.20.0",
        "opentelemetry-instrumentation>=0.41b0",
        "opentelemetry-exporter-jaeger>=1.20.0",
    ]

    result = validate_requirements("gateway/requirements.txt", phase4_packages)
    validation_results.append(result)

    # Summary
    print("\n📊 Validation Summary:")
    passed = sum(validation_results)
    total = len(validation_results)
    success_rate = (passed / total) * 100 if total > 0 else 0

    print(f"✅ Passed: {passed}/{total} ({success_rate:.1f}%)")
    print(f"❌ Failed: {total - passed}/{total} ({100 - success_rate:.1f}%)")

    if success_rate >= 90:
        print("\n🎉 Phase 4 Validation: PASSED")
        print("The advanced monitoring & analytics implementation is ready!")
        return True
    else:
        print("\n❌ Phase 4 Validation: FAILED")
        print("Please fix issues before proceeding.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
