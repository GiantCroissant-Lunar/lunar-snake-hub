"""
Performance Monitor Service - Real-time performance monitoring and analytics
"""

import time
import asyncio
import psutil
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
import statistics
from enum import Enum

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricValue:
    """Single metric value with metadata"""

    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceMetric:
    """Performance metric definition"""

    name: str
    metric_type: MetricType
    description: str
    unit: str = ""
    tags: Dict[str, str] = field(default_factory=dict)

    # For histograms
    buckets: List[float] = field(
        default_factory=lambda: [0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
    )


class PerformanceMonitor:
    """Real-time performance monitoring service"""

    def __init__(self, retention_hours: int = 24, max_metrics_per_type: int = 10000):
        self.retention_hours = retention_hours
        self.max_metrics_per_type = max_metrics_per_type

        # Storage for metrics
        self.metrics: Dict[str, PerformanceMetric] = {}
        self.values: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_metrics_per_type)
        )

        # Aggregated statistics
        self.aggregated_stats: Dict[str, Dict[str, float]] = defaultdict(dict)

        # Alerts
        self.alerts: List[Dict[str, Any]] = []
        self.alert_thresholds: Dict[str, Dict[str, float]] = {}

        # System monitoring
        self.system_stats_enabled = True
        self.system_stats_interval = 30  # seconds

        # Background tasks
        self.cleanup_task: Optional[asyncio.Task] = None
        self.system_monitor_task: Optional[asyncio.Task] = None

        # Performance statistics
        self.performance_stats = {
            "metrics_collected": 0,
            "alerts_triggered": 0,
            "cleanup_runs": 0,
            "start_time": datetime.now(),
        }

    async def start(self):
        """Start performance monitoring"""
        # Start background cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_old_metrics())

        # Start system monitoring task
        if self.system_stats_enabled:
            self.system_monitor_task = asyncio.create_task(self._collect_system_stats())

        logger.info("🔍 Performance monitoring started")

    async def stop(self):
        """Stop performance monitoring"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        if self.system_monitor_task:
            self.system_monitor_task.cancel()
            try:
                await self.system_monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("🔍 Performance monitoring stopped")

    def register_metric(
        self,
        name: str,
        metric_type: MetricType,
        description: str,
        unit: str = "",
        tags: Dict[str, str] = None,
        buckets: List[float] = None,
    ) -> bool:
        """Register a new metric"""
        if name in self.metrics:
            logger.warning(f"Metric {name} already registered")
            return False

        metric = PerformanceMetric(
            name=name,
            metric_type=metric_type,
            description=description,
            unit=unit,
            tags=tags or {},
            buckets=buckets or [0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
        )

        self.metrics[name] = metric
        logger.info(f"✅ Registered metric: {name}")
        return True

    def record_metric(
        self, name: str, value: float, tags: Dict[str, str] = None
    ) -> bool:
        """Record a metric value"""
        if name not in self.metrics:
            logger.warning(f"Metric {name} not registered")
            return False

        timestamp = datetime.now()
        metric_tags = {**(self.metrics[name].tags), **(tags or {})}

        metric_value = MetricValue(timestamp=timestamp, value=value, tags=metric_tags)

        self.values[name].append(metric_value)
        self.performance_stats["metrics_collected"] += 1

        # Check alerts
        await self._check_alerts(name, value)

        # Update aggregated stats
        self._update_aggregated_stats(name, value)

        return True

    def increment_counter(
        self, name: str, value: float = 1.0, tags: Dict[str, str] = None
    ) -> bool:
        """Increment a counter metric"""
        return self.record_metric(name, value, tags)

    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None) -> bool:
        """Set a gauge metric"""
        return self.record_metric(name, value, tags)

    def record_timer(
        self, name: str, duration: float, tags: Dict[str, str] = None
    ) -> bool:
        """Record a timer metric"""
        return self.record_metric(name, duration, tags)

    def time_function(self, name: str, tags: Dict[str, str] = None):
        """Decorator to time function execution"""

        def decorator(func):
            if asyncio.iscoroutinefunction(func):

                async def async_wrapper(*args, **kwargs):
                    start_time = time.time()
                    try:
                        result = await func(*args, **kwargs)
                        return result
                    finally:
                        duration = time.time() - start_time
                        self.record_timer(name, duration, tags)

                return async_wrapper
            else:

                def sync_wrapper(*args, **kwargs):
                    start_time = time.time()
                    try:
                        result = func(*args, **kwargs)
                        return result
                    finally:
                        duration = time.time() - start_time
                        self.record_timer(name, duration, tags)

                return sync_wrapper

        return decorator

    def _update_aggregated_stats(self, name: str, value: float):
        """Update aggregated statistics for a metric"""
        values = [v.value for v in self.values[name]]

        if not values:
            return

        metric_type = self.metrics[name].metric_type

        if metric_type == MetricType.COUNTER:
            self.aggregated_stats[name]["total"] = sum(values)
            self.aggregated_stats[name]["rate_per_second"] = sum(values) / max(
                1, len(values)
            )

        elif metric_type == MetricType.GAUGE:
            self.aggregated_stats[name]["current"] = values[-1] if values else 0
            self.aggregated_stats[name]["min"] = min(values)
            self.aggregated_stats[name]["max"] = max(values)
            self.aggregated_stats[name]["avg"] = statistics.mean(values)

        elif metric_type in [MetricType.HISTOGRAM, MetricType.TIMER]:
            self.aggregated_stats[name]["count"] = len(values)
            self.aggregated_stats[name]["sum"] = sum(values)
            self.aggregated_stats[name]["min"] = min(values)
            self.aggregated_stats[name]["max"] = max(values)
            self.aggregated_stats[name]["avg"] = statistics.mean(values)
            self.aggregated_stats[name]["median"] = statistics.median(values)

            if len(values) > 1:
                self.aggregated_stats[name]["stddev"] = statistics.stdev(values)

            # Percentiles
            sorted_values = sorted(values)
            for p in [50, 90, 95, 99]:
                if p <= 100:
                    percentile = p / 100.0
                    index = int(len(sorted_values) * percentile)
                    if index < len(sorted_values):
                        self.aggregated_stats[name][f"p{p}"] = sorted_values[index]

    async def _check_alerts(self, name: str, value: float):
        """Check if any alerts should be triggered"""
        if name not in self.alert_thresholds:
            return

        thresholds = self.alert_thresholds[name]

        for threshold_name, threshold_value in thresholds.items():
            if threshold_name == "critical" and value > threshold_value:
                await self._trigger_alert(name, value, "critical", threshold_value)
            elif threshold_name == "warning" and value > threshold_value:
                await self._trigger_alert(name, value, "warning", threshold_value)
            elif threshold_name == "info" and value > threshold_value:
                await self._trigger_alert(name, value, "info", threshold_value)

    async def _trigger_alert(
        self, metric_name: str, value: float, severity: str, threshold: float
    ):
        """Trigger an alert"""
        alert = {
            "id": f"{metric_name}_{severity}_{int(time.time())}",
            "metric_name": metric_name,
            "value": value,
            "threshold": threshold,
            "severity": severity,
            "timestamp": datetime.now(),
            "description": f"{metric_name} exceeded {severity} threshold: {value} > {threshold}",
        }

        self.alerts.append(alert)
        self.performance_stats["alerts_triggered"] += 1

        logger.warning(f"🚨 Alert triggered: {alert['description']}")

    def set_alert_threshold(self, metric_name: str, severity: str, threshold: float):
        """Set alert threshold for a metric"""
        if metric_name not in self.alert_thresholds:
            self.alert_thresholds[metric_name] = {}

        self.alert_thresholds[metric_name][severity] = threshold
        logger.info(f"📊 Alert threshold set: {metric_name} {severity} = {threshold}")

    async def _cleanup_old_metrics(self):
        """Clean up old metrics based on retention policy"""
        while True:
            try:
                cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
                cleaned = 0

                for name, metric_values in self.values.items():
                    original_length = len(metric_values)

                    # Remove old values
                    while metric_values and metric_values[0].timestamp < cutoff_time:
                        metric_values.popleft()
                        cleaned += 1

                    if len(metric_values) != original_length:
                        logger.debug(
                            f"Cleaned {original_length - len(metric_values)} old values for {name}"
                        )

                if cleaned > 0:
                    self.performance_stats["cleanup_runs"] += 1
                    logger.info(f"🧹 Cleaned up {cleaned} old metric values")

                await asyncio.sleep(3600)  # Run every hour

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup task error: {e}")
                await asyncio.sleep(300)  # Retry after 5 minutes

    async def _collect_system_stats(self):
        """Collect system performance statistics"""
        while True:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.set_gauge("system_cpu_usage_percent", cpu_percent)

                # Memory usage
                memory = psutil.virtual_memory()
                self.set_gauge("system_memory_usage_percent", memory.percent)
                self.set_gauge(
                    "system_memory_available_gb", memory.available / (1024**3)
                )

                # Disk usage
                disk = psutil.disk_usage("/")
                self.set_gauge("system_disk_usage_percent", disk.percent)
                self.set_gauge("system_disk_free_gb", disk.free / (1024**3))

                # Network I/O
                network = psutil.net_io_counters()
                self.increment_counter("system_network_bytes_sent", network.bytes_sent)
                self.increment_counter("system_network_bytes_recv", network.bytes_recv)

                # Process-specific stats
                process = psutil.Process()
                self.set_gauge(
                    "process_memory_mb", process.memory_info().rss / (1024**2)
                )
                self.set_gauge("process_cpu_percent", process.cpu_percent())
                self.increment_counter(
                    "process_context_switches", process.num_ctx_switches()
                )

                await asyncio.sleep(self.system_stats_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute

    def get_metric_values(
        self,
        name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[MetricValue]:
        """Get metric values within time range"""
        if name not in self.values:
            return []

        values = list(self.values[name])

        if start_time:
            values = [v for v in values if v.timestamp >= start_time]

        if end_time:
            values = [v for v in values if v.timestamp <= end_time]

        return values

    def get_metric_stats(self, name: str) -> Dict[str, float]:
        """Get aggregated statistics for a metric"""
        return self.aggregated_stats.get(name, {})

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics and their statistics"""
        result = {
            "metrics": {},
            "aggregated_stats": dict(self.aggregated_stats),
            "alerts": self.alerts[-100:],  # Last 100 alerts
            "performance_stats": {
                **self.performance_stats,
                "uptime_seconds": (
                    datetime.now() - self.performance_stats["start_time"]
                ).total_seconds(),
            },
        }

        for name, metric in self.metrics.items():
            metric_info = {
                "name": metric.name,
                "type": metric.metric_type.value,
                "description": metric.description,
                "unit": metric.unit,
                "tags": metric.tags,
                "value_count": len(self.values[name]),
                "latest_value": self.values[name][-1].value
                if self.values[name]
                else None,
                "latest_timestamp": self.values[name][-1].timestamp.isoformat()
                if self.values[name]
                else None,
            }

            if name in self.alert_thresholds:
                metric_info["alert_thresholds"] = self.alert_thresholds[name]

            result["metrics"][name] = metric_info

        return result

    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format"""
        data = self.get_all_metrics()

        if format == "json":
            return json.dumps(data, default=str, indent=2)
        elif format == "prometheus":
            return self._export_prometheus_format(data)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _export_prometheus_format(self, data: Dict[str, Any]) -> str:
        """Export metrics in Prometheus format"""
        lines = []

        for name, metric_info in data["metrics"].items():
            if metric_info["latest_value"] is not None:
                # HELP and TYPE lines
                lines.append(f"# HELP {name} {metric_info['description']}")
                lines.append(f"# TYPE {name} {metric_info['type']}")

                # Metric value with tags
                tags_str = ""
                if metric_info["tags"]:
                    tags_str = (
                        "{"
                        + ",".join(
                            [f'{k}="{v}"' for k, v in metric_info["tags"].items()]
                        )
                        + "}"
                    )

                lines.append(f"{name}{tags_str} {metric_info['latest_value']}")

        return "\n".join(lines)

    async def health_check(self) -> Dict[str, Any]:
        """Health check for performance monitoring"""
        uptime = (datetime.now() - self.performance_stats["start_time"]).total_seconds()

        return {
            "status": "healthy",
            "uptime_seconds": uptime,
            "metrics_registered": len(self.metrics),
            "total_values_collected": self.performance_stats["metrics_collected"],
            "alerts_triggered": self.performance_stats["alerts_triggered"],
            "system_monitoring_enabled": self.system_stats_enabled,
            "cleanup_task_running": self.cleanup_task and not self.cleanup_task.done(),
            "system_monitor_task_running": self.system_monitor_task
            and not self.system_monitor_task.done(),
        }


# Global performance monitor instance
performance_monitor: Optional[PerformanceMonitor] = None


async def init_performance_monitor(
    retention_hours: int = 24, max_metrics_per_type: int = 10000
) -> PerformanceMonitor:
    """Initialize global performance monitor"""
    global performance_monitor

    performance_monitor = PerformanceMonitor(retention_hours, max_metrics_per_type)
    await performance_monitor.start()

    # Register default metrics
    performance_monitor.register_metric(
        "http_requests_total", MetricType.COUNTER, "Total HTTP requests"
    )
    performance_monitor.register_metric(
        "http_request_duration_seconds", MetricType.HISTOGRAM, "HTTP request duration"
    )
    performance_monitor.register_metric(
        "embedding_requests_total", MetricType.COUNTER, "Total embedding requests"
    )
    performance_monitor.register_metric(
        "search_requests_total", MetricType.COUNTER, "Total search requests"
    )
    performance_monitor.register_metric(
        "search_duration_seconds", MetricType.HISTOGRAM, "Search request duration"
    )

    # Set default alert thresholds
    performance_monitor.set_alert_threshold("system_cpu_usage_percent", "warning", 80.0)
    performance_monitor.set_alert_threshold(
        "system_cpu_usage_percent", "critical", 95.0
    )
    performance_monitor.set_alert_threshold(
        "system_memory_usage_percent", "warning", 85.0
    )
    performance_monitor.set_alert_threshold(
        "system_memory_usage_percent", "critical", 95.0
    )
    performance_monitor.set_alert_threshold(
        "http_request_duration_seconds", "warning", 5.0
    )
    performance_monitor.set_alert_threshold(
        "http_request_duration_seconds", "critical", 10.0
    )

    return performance_monitor


def get_performance_monitor() -> Optional[PerformanceMonitor]:
    """Get global performance monitor"""
    return performance_monitor
