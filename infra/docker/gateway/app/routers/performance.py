"""
Performance Router - Performance monitoring and optimization endpoints
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import PlainTextResponse
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import asyncio

from ..services.performance_monitor import MetricType

logger = logging.getLogger(__name__)

router = APIRouter()

# Service instances
perf_monitor = None
pool_service = None
cache_service = None


def init_services(monitor, pool, cache):
    """Initialize router with service instances"""
    global perf_monitor, pool_service, cache_service
    perf_monitor = monitor
    pool_service = pool
    cache_service = cache


@router.get("/metrics")
async def get_metrics(
    format: str = Query("json", description="Export format: json or prometheus"),
    metric_names: Optional[List[str]] = Query(
        None, description="Specific metric names to retrieve"
    ),
):
    """Get performance metrics"""
    if not perf_monitor:
        raise HTTPException(status_code=503, detail="Performance monitor not available")

    try:
        if metric_names:
            # Get specific metrics
            data = {}
            for name in metric_names:
                data[name] = perf_monitor.get_metric_stats(name)
            return {"metrics": data}
        else:
            # Get all metrics
            data = perf_monitor.get_all_metrics()

            if format.lower() == "prometheus":
                return PlainTextResponse(
                    content=perf_monitor.export_metrics("prometheus"),
                    media_type="text/plain",
                )

            return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/metrics/{metric_name}")
async def get_metric_details(
    metric_name: str,
    start_time: Optional[datetime] = Query(
        None, description="Start time for metric values"
    ),
    end_time: Optional[datetime] = Query(
        None, description="End time for metric values"
    ),
):
    """Get detailed information about a specific metric"""
    if not perf_monitor:
        raise HTTPException(status_code=503, detail="Performance monitor not available")

    try:
        # Get metric values
        values = perf_monitor.get_metric_values(metric_name, start_time, end_time)

        # Get aggregated statistics
        stats = perf_monitor.get_metric_stats(metric_name)

        return {
            "metric_name": metric_name,
            "statistics": stats,
            "values": [
                {"timestamp": v.timestamp.isoformat(), "value": v.value, "tags": v.tags}
                for v in values
            ],
            "value_count": len(values),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get metric details: {str(e)}"
        )


@router.post("/metrics/{metric_name}")
async def record_metric(
    metric_name: str, value: float, tags: Optional[Dict[str, str]] = None
):
    """Record a metric value"""
    if not perf_monitor:
        raise HTTPException(status_code=503, detail="Performance monitor not available")

    try:
        success = perf_monitor.record_metric(metric_name, value, tags)

        if not success:
            raise HTTPException(
                status_code=400, detail=f"Metric {metric_name} not registered"
            )

        return {"status": "success", "message": f"Metric {metric_name} recorded"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to record metric: {str(e)}"
        )


@router.post("/metrics/register")
async def register_metric(
    name: str,
    metric_type: str,
    description: str,
    unit: str = "",
    tags: Optional[Dict[str, str]] = None,
    buckets: Optional[List[float]] = None,
):
    """Register a new metric"""
    if not perf_monitor:
        raise HTTPException(status_code=503, detail="Performance monitor not available")

    try:
        # Convert string to enum
        try:
            type_enum = MetricType(metric_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid metric type: {metric_type}. Valid types: {[t.value for t in MetricType]}",
            )

        success = perf_monitor.register_metric(
            name=name,
            metric_type=type_enum,
            description=description,
            unit=unit,
            tags=tags,
            buckets=buckets,
        )

        if not success:
            raise HTTPException(
                status_code=400, detail=f"Metric {name} already registered"
            )

        return {"status": "success", "message": f"Metric {name} registered"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to register metric: {str(e)}"
        )


@router.get("/alerts")
async def get_alerts(
    severity: Optional[str] = Query(
        None, description="Filter by severity: info, warning, critical"
    ),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of alerts to return"
    ),
):
    """Get performance alerts"""
    if not perf_monitor:
        raise HTTPException(status_code=503, detail="Performance monitor not available")

    try:
        alerts = perf_monitor.alerts

        # Filter by severity
        if severity:
            alerts = [a for a in alerts if a.get("severity") == severity]

        # Sort by timestamp (newest first)
        alerts = sorted(
            alerts, key=lambda x: x.get("timestamp", datetime.min), reverse=True
        )

        # Limit results
        alerts = alerts[:limit]

        return {"alerts": alerts, "total_count": len(alerts)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router.post("/alerts/thresholds")
async def set_alert_threshold(metric_name: str, severity: str, threshold: float):
    """Set alert threshold for a metric"""
    if not perf_monitor:
        raise HTTPException(status_code=503, detail="Performance monitor not available")

    try:
        if severity not in ["info", "warning", "critical"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid severity. Must be: info, warning, or critical",
            )

        perf_monitor.set_alert_threshold(metric_name, severity, threshold)

        return {
            "status": "success",
            "message": f"Alert threshold set for {metric_name} {severity} = {threshold}",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to set alert threshold: {str(e)}"
        )


@router.get("/pools")
async def get_connection_pool_stats():
    """Get connection pool statistics"""
    if not pool_service:
        raise HTTPException(
            status_code=503, detail="Connection pool service not available"
        )

    try:
        stats = await pool_service.get_pool_stats()
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get pool stats: {str(e)}"
        )


@router.post("/pools/reset-stats")
async def reset_pool_stats():
    """Reset connection pool statistics"""
    if not pool_service:
        raise HTTPException(
            status_code=503, detail="Connection pool service not available"
        )

    try:
        await pool_service.reset_stats()
        return {"status": "success", "message": "Pool statistics reset"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to reset pool stats: {str(e)}"
        )


@router.get("/cache")
async def get_cache_stats():
    """Get cache statistics"""
    if not cache_service:
        raise HTTPException(status_code=503, detail="Cache service not available")

    try:
        stats = await cache_service.get_stats()
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get cache stats: {str(e)}"
        )


@router.post("/cache/clear")
async def clear_cache(
    prefix: Optional[str] = Query(
        None, description="Clear cache entries with specific prefix"
    ),
):
    """Clear cache entries"""
    if not cache_service:
        raise HTTPException(status_code=503, detail="Cache service not available")

    try:
        if prefix:
            count = await cache_service.clear_prefix(prefix)
            return {
                "status": "success",
                "message": f"Cleared {count} cache entries with prefix '{prefix}'",
            }
        else:
            # Clear all cache (would need to implement this in cache service)
            return {
                "status": "error",
                "message": "Clearing all cache not implemented. Use prefix parameter.",
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.post("/cache/warm")
async def warm_cache(background_tasks: BackgroundTasks, data: Dict[str, Any]):
    """Warm up cache with initial data"""
    if not cache_service:
        raise HTTPException(status_code=503, detail="Cache service not available")

    try:
        # Run cache warmup in background
        async def warmup_task():
            try:
                warmed = await cache_service.warm_cache(data.get("data", []))
                logger.info(f"Cache warmed with {warmed} entries")
            except Exception as e:
                logger.error(f"Cache warmup failed: {e}")

        background_tasks.add_task(warmup_task)

        return {"status": "success", "message": "Cache warmup started in background"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start cache warmup: {str(e)}"
        )


@router.get("/health")
async def get_performance_health():
    """Get health status of performance services"""
    health = {
        "performance_monitor": {"status": "unavailable"},
        "connection_pools": {"status": "unavailable"},
        "cache": {"status": "unavailable"},
        "overall_status": "unhealthy",
    }

    # Check performance monitor
    if perf_monitor:
        try:
            pm_health = await perf_monitor.health_check()
            health["performance_monitor"] = {
                "status": pm_health["status"],
                "details": pm_health,
            }
        except Exception as e:
            health["performance_monitor"] = {"status": "error", "error": str(e)}

    # Check connection pools
    if pool_service:
        try:
            pool_health = await pool_service.health_check()
            health["connection_pools"] = {
                "status": pool_health["overall_status"],
                "details": pool_health["services"],
            }
        except Exception as e:
            health["connection_pools"] = {"status": "error", "error": str(e)}

    # Check cache
    if cache_service:
        try:
            cache_health = await cache_service.health_check()
            health["cache"] = {
                "status": cache_health["overall_status"],
                "details": cache_health,
            }
        except Exception as e:
            health["cache"] = {"status": "error", "error": str(e)}

    # Determine overall status
    statuses = [
        health["performance_monitor"]["status"],
        health["connection_pools"]["status"],
        health["cache"]["status"],
    ]

    if all(s == "healthy" for s in statuses):
        health["overall_status"] = "healthy"
    elif any(s == "degraded" for s in statuses):
        health["overall_status"] = "degraded"
    else:
        health["overall_status"] = "unhealthy"

    return health


@router.get("/dashboard")
async def get_performance_dashboard():
    """Get performance dashboard data"""
    if not perf_monitor:
        raise HTTPException(status_code=503, detail="Performance monitor not available")

    try:
        # Get current time ranges
        now = datetime.now()
        last_hour = now - timedelta(hours=1)

        dashboard_data = {
            "timestamp": now.isoformat(),
            "system_metrics": {},
            "application_metrics": {},
            "alerts_summary": {
                "total": len(perf_monitor.alerts),
                "critical": len(
                    [a for a in perf_monitor.alerts if a.get("severity") == "critical"]
                ),
                "warning": len(
                    [a for a in perf_monitor.alerts if a.get("severity") == "warning"]
                ),
                "info": len(
                    [a for a in perf_monitor.alerts if a.get("severity") == "info"]
                ),
            },
        }

        # System metrics
        system_metrics = [
            "system_cpu_usage_percent",
            "system_memory_usage_percent",
            "system_disk_usage_percent",
        ]
        for metric in system_metrics:
            values = perf_monitor.get_metric_values(metric, last_hour)
            if values:
                dashboard_data["system_metrics"][metric] = {
                    "current": values[-1].value,
                    "avg": sum(v.value for v in values) / len(values),
                    "min": min(v.value for v in values),
                    "max": max(v.value for v in values),
                }

        # Application metrics
        app_metrics = [
            "http_requests_total",
            "http_request_duration_seconds",
            "search_requests_total",
        ]
        for metric in app_metrics:
            stats = perf_monitor.get_metric_stats(metric)
            if stats:
                dashboard_data["application_metrics"][metric] = stats

        # Add connection pool and cache stats if available
        if pool_service:
            pool_stats = await pool_service.get_pool_stats()
            dashboard_data["connection_pools"] = pool_stats

        if cache_service:
            cache_stats = await cache_service.get_stats()
            dashboard_data["cache"] = cache_stats

        return dashboard_data

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get dashboard data: {str(e)}"
        )


@router.post("/benchmark")
async def run_benchmark(
    background_tasks: BackgroundTasks,
    test_type: str = Query(
        "search", description="Benchmark type: search, embedding, cache"
    ),
    iterations: int = Query(100, ge=1, le=10000, description="Number of iterations"),
):
    """Run performance benchmark"""
    if not perf_monitor:
        raise HTTPException(status_code=503, detail="Performance monitor not available")

    try:
        # Run benchmark in background
        async def benchmark_task():
            try:
                import time
                import random

                start_time = time.time()

                for i in range(iterations):
                    iter_start = time.time()

                    if test_type == "search":
                        # Simulate search operation
                        await asyncio.sleep(0.01 + random.random() * 0.05)
                        perf_monitor.record_timer(
                            "benchmark_search_duration", time.time() - iter_start
                        )
                    elif test_type == "embedding":
                        # Simulate embedding operation
                        await asyncio.sleep(0.02 + random.random() * 0.1)
                        perf_monitor.record_timer(
                            "benchmark_embedding_duration", time.time() - iter_start
                        )
                    elif test_type == "cache":
                        # Simulate cache operation
                        await asyncio.sleep(0.001 + random.random() * 0.01)
                        perf_monitor.record_timer(
                            "benchmark_cache_duration", time.time() - iter_start
                        )

                total_time = time.time() - start_time
                avg_time = total_time / iterations

                logger.info(
                    f"Benchmark completed: {test_type}, {iterations} iterations, "
                    f"total: {total_time:.3f}s, avg: {avg_time:.3f}s"
                )

            except Exception as e:
                logger.error(f"Benchmark failed: {e}")

        background_tasks.add_task(benchmark_task)

        return {
            "status": "success",
            "message": f"Benchmark started for {test_type} with {iterations} iterations",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start benchmark: {str(e)}"
        )
