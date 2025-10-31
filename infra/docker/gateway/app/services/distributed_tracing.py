"""
Distributed Tracing Service - Phase 4
Provides request flow tracking, service dependency mapping, and performance profiling
"""

import asyncio
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import logging
from enum import Enum
from contextlib import asynccontextmanager

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.semconv.resource import ResourceAttributes
    from opentelemetry.propagate import set_global_textmap
    from opentelemetry.propagators.b3 import B3MultiFormat

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    logging.warning("OpenTelemetry not available. Using mock distributed tracing.")

logger = logging.getLogger(__name__)


class SpanKind(Enum):
    """Types of spans"""

    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"
    INTERNAL = "internal"


class SpanStatus(Enum):
    """Span status codes"""

    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class TraceSpan:
    """Individual span in a trace"""

    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: Optional[float]
    status: SpanStatus
    service_name: str
    span_kind: SpanKind
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    children: List[str] = field(default_factory=list)


@dataclass
class ServiceDependency:
    """Service dependency relationship"""

    source_service: str
    target_service: str
    operation: str
    call_count: int
    total_duration_ms: float
    avg_duration_ms: float
    error_count: int
    last_seen: datetime


@dataclass
class PerformanceProfile:
    """Performance profile for an operation"""

    operation_name: str
    service_name: str
    total_calls: int
    total_duration_ms: float
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    p50_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    error_rate: float
    last_updated: datetime


class DistributedTracingService:
    """Distributed tracing service for request flow analysis"""

    def __init__(
        self, service_name: str = "context-gateway", jaeger_endpoint: str = None
    ):
        self.service_name = service_name
        self.jaeger_endpoint = jaeger_endpoint

        # Trace storage
        self.active_spans: Dict[str, TraceSpan] = {}
        self.completed_spans: Dict[str, TraceSpan] = {}
        self.trace_spans: Dict[str, List[str]] = defaultdict(
            list
        )  # trace_id -> span_ids

        # Service dependencies
        self.dependencies: Dict[str, ServiceDependency] = {}

        # Performance profiles
        self.performance_profiles: Dict[str, PerformanceProfile] = {}

        # Configuration
        self.max_spans = 10000
        self.max_traces = 1000
        self.profile_window_minutes = 60

        # OpenTelemetry setup
        self.tracer = None
        self._setup_opentelemetry()

        # Background tasks
        self._cleanup_task = None
        self._start_cleanup_task()

        logger.info(f"Distributed Tracing Service initialized for {service_name}")

    def _setup_opentelemetry(self):
        """Setup OpenTelemetry if available"""
        if not OPENTELEMETRY_AVAILABLE:
            logger.info("Using mock tracing implementation")
            return

        try:
            # Configure tracer provider
            resource = Resource.create(
                {
                    ResourceAttributes.SERVICE_NAME: self.service_name,
                    ResourceAttributes.SERVICE_VERSION: "1.0.0",
                }
            )

            trace.set_tracer_provider(TracerProvider(resource=resource))

            # Setup Jaeger exporter if endpoint provided
            if self.jaeger_endpoint:
                jaeger_exporter = JaegerExporter(
                    endpoint=self.jaeger_endpoint,
                    collector_endpoint=self.jaeger_endpoint,
                )

                span_processor = BatchSpanProcessor(jaeger_exporter)
                trace.get_tracer_provider().add_span_processor(span_processor)

                logger.info(f"Jaeger exporter configured: {self.jaeger_endpoint}")

            # Set global propagator
            set_global_textmap(B3MultiFormat())

            # Get tracer
            self.tracer = trace.get_tracer(__name__)

        except Exception as e:
            logger.error(f"Failed to setup OpenTelemetry: {e}")
            self.tracer = None

    def _start_cleanup_task(self):
        """Start background cleanup task"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self):
        """Background cleanup loop"""
        while True:
            try:
                await asyncio.sleep(300)  # Clean up every 5 minutes
                await self._cleanup_old_data()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def _cleanup_old_data(self):
        """Clean up old tracing data"""
        cutoff_time = datetime.now() - timedelta(hours=1)

        # Clean up old completed spans
        old_span_ids = [
            span_id
            for span_id, span in self.completed_spans.items()
            if span.end_time and span.end_time < cutoff_time
        ]

        for span_id in old_span_ids:
            span = self.completed_spans.pop(span_id, None)
            if span:
                # Remove from trace mapping
                if span.trace_id in self.trace_spans:
                    if span_id in self.trace_spans[span.trace_id]:
                        self.trace_spans[span.trace_id].remove(span_id)

                    # Remove empty traces
                    if not self.trace_spans[span.trace_id]:
                        del self.trace_spans[span.trace_id]

        # Clean up old traces
        if len(self.trace_spans) > self.max_traces:
            # Sort traces by last activity
            trace_activities = []
            for trace_id, span_ids in self.trace_spans.items():
                last_activity = max(
                    (
                        self.completed_spans.get(
                            span_id,
                            TraceSpan(
                                trace_id="",
                                span_id="",
                                parent_span_id=None,
                                operation_name="",
                                start_time=datetime.now(),
                                end_time=None,
                                duration_ms=None,
                                status=SpanStatus.OK,
                                service_name="",
                                span_kind=SpanKind.INTERNAL,
                            ),
                        ).end_time
                        or datetime.now()
                    )
                    for span_id in span_ids
                )
                trace_activities.append((trace_id, last_activity))

            # Sort by last activity and keep only recent traces
            trace_activities.sort(key=lambda x: x[1], reverse=True)
            traces_to_keep = set(
                trace_id for trace_id, _ in trace_activities[: self.max_traces]
            )

            # Remove old traces
            traces_to_remove = set(self.trace_spans.keys()) - traces_to_keep
            for trace_id in traces_to_remove:
                del self.trace_spans[trace_id]

        # Clean up old performance profiles
        profile_cutoff = datetime.now() - timedelta(minutes=self.profile_window_minutes)
        self.performance_profiles = {
            key: profile
            for key, profile in self.performance_profiles.items()
            if profile.last_updated > profile_cutoff
        }

        logger.debug(f"Cleanup completed. Removed {len(old_span_ids)} old spans")

    @asynccontextmanager
    async def start_span(
        self,
        operation_name: str,
        span_kind: SpanKind = SpanKind.INTERNAL,
        parent_span_id: str = None,
        tags: Dict[str, Any] = None,
    ) -> str:
        """Start a new span and return span ID"""
        span_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())  # In real implementation, this would be propagated

        # Create span
        span = TraceSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=datetime.now(),
            end_time=None,
            duration_ms=None,
            status=SpanStatus.OK,
            service_name=self.service_name,
            span_kind=span_kind,
            tags=tags or {},
        )

        # Store active span
        self.active_spans[span_id] = span
        self.trace_spans[trace_id].append(span_id)

        # Start OpenTelemetry span if available
        otel_span = None
        if self.tracer:
            try:
                otel_span = self.tracer.start_span(operation_name)
                # Set tags
                for key, value in (tags or {}).items():
                    otel_span.set_attribute(key, str(value))
            except Exception as e:
                logger.error(f"Error starting OpenTelemetry span: {e}")

        try:
            yield span_id
        except Exception as e:
            # Mark span as error
            span.status = SpanStatus.ERROR
            if otel_span:
                otel_span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise
        finally:
            # End span
            span.end_time = datetime.now()
            span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000

            # Move to completed spans
            self.active_spans.pop(span_id, None)
            self.completed_spans[span_id] = span

            # Update performance profile
            await self._update_performance_profile(span)

            # Update dependencies
            await self._update_dependencies(span)

            # End OpenTelemetry span
            if otel_span:
                try:
                    otel_span.end()
                except Exception as e:
                    logger.error(f"Error ending OpenTelemetry span: {e}")

    async def _update_performance_profile(self, span: TraceSpan):
        """Update performance profile for the operation"""
        if span.duration_ms is None:
            return

        profile_key = f"{span.service_name}:{span.operation_name}"

        if profile_key not in self.performance_profiles:
            self.performance_profiles[profile_key] = PerformanceProfile(
                operation_name=span.operation_name,
                service_name=span.service_name,
                total_calls=0,
                total_duration_ms=0,
                avg_duration_ms=0,
                min_duration_ms=float("inf"),
                max_duration_ms=0,
                p50_duration_ms=0,
                p95_duration_ms=0,
                p99_duration_ms=0,
                error_rate=0,
                last_updated=datetime.now(),
            )

        profile = self.performance_profiles[profile_key]

        # Get all durations for this operation
        operation_spans = [
            s
            for s in self.completed_spans.values()
            if s.service_name == span.service_name
            and s.operation_name == span.operation_name
            and s.duration_ms is not None
            and s.end_time
            and s.end_time
            > datetime.now() - timedelta(minutes=self.profile_window_minutes)
        ]

        durations = [s.duration_ms for s in operation_spans]

        if durations:
            profile.total_calls = len(operation_spans)
            profile.total_duration_ms = sum(durations)
            profile.avg_duration_ms = sum(durations) / len(durations)
            profile.min_duration_ms = min(durations)
            profile.max_duration_ms = max(durations)
            profile.p50_duration_ms = self._percentile(durations, 50)
            profile.p95_duration_ms = self._percentile(durations, 95)
            profile.p99_duration_ms = self._percentile(durations, 99)
            profile.error_rate = len(
                [s for s in operation_spans if s.status != SpanStatus.OK]
            ) / len(operation_spans)
            profile.last_updated = datetime.now()

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)

        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))

    async def _update_dependencies(self, span: TraceSpan):
        """Update service dependency mapping"""
        # Extract service information from tags
        target_service = span.tags.get("target_service")
        if not target_service:
            return

        dependency_key = f"{span.service_name}:{target_service}:{span.operation_name}"

        if dependency_key not in self.dependencies:
            self.dependencies[dependency_key] = ServiceDependency(
                source_service=span.service_name,
                target_service=target_service,
                operation=span.operation_name,
                call_count=0,
                total_duration_ms=0,
                avg_duration_ms=0,
                error_count=0,
                last_seen=datetime.now(),
            )

        dependency = self.dependencies[dependency_key]
        dependency.call_count += 1
        if span.duration_ms:
            dependency.total_duration_ms += span.duration_ms
            dependency.avg_duration_ms = (
                dependency.total_duration_ms / dependency.call_count
            )

        if span.status != SpanStatus.OK:
            dependency.error_count += 1

        dependency.last_seen = datetime.now()

    async def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get complete trace information"""
        if trace_id not in self.trace_spans:
            return None

        span_ids = self.trace_spans[trace_id]
        spans = []

        for span_id in span_ids:
            span = self.completed_spans.get(span_id) or self.active_spans.get(span_id)
            if span:
                spans.append(
                    {
                        "trace_id": span.trace_id,
                        "span_id": span.span_id,
                        "parent_span_id": span.parent_span_id,
                        "operation_name": span.operation_name,
                        "start_time": span.start_time.isoformat(),
                        "end_time": span.end_time.isoformat()
                        if span.end_time
                        else None,
                        "duration_ms": span.duration_ms,
                        "status": span.status.value,
                        "service_name": span.service_name,
                        "span_kind": span.span_kind.value,
                        "tags": span.tags,
                        "logs": span.logs,
                    }
                )

        # Sort spans by start time
        spans.sort(key=lambda x: x["start_time"])

        return {
            "trace_id": trace_id,
            "spans": spans,
            "total_spans": len(spans),
            "total_duration_ms": max(
                [s["duration_ms"] for s in spans if s["duration_ms"]] or [0]
            ),
            "services": list(set(s["service_name"] for s in spans)),
        }

    async def get_service_map(self) -> Dict[str, Any]:
        """Get service dependency map"""
        nodes = set()
        edges = []

        for dependency in self.dependencies.values():
            nodes.add(dependency.source_service)
            nodes.add(dependency.target_service)

            edges.append(
                {
                    "source": dependency.source_service,
                    "target": dependency.target_service,
                    "operation": dependency.operation,
                    "call_count": dependency.call_count,
                    "avg_duration_ms": dependency.avg_duration_ms,
                    "error_rate": dependency.error_count / dependency.call_count
                    if dependency.call_count > 0
                    else 0,
                    "last_seen": dependency.last_seen.isoformat(),
                }
            )

        return {
            "nodes": list(nodes),
            "edges": edges,
            "total_services": len(nodes),
            "total_dependencies": len(edges),
        }

    async def get_performance_profiles(
        self, service_name: str = None
    ) -> List[PerformanceProfile]:
        """Get performance profiles"""
        profiles = list(self.performance_profiles.values())

        if service_name:
            profiles = [p for p in profiles if p.service_name == service_name]

        # Sort by total calls (most active first)
        profiles.sort(key=lambda x: x.total_calls, reverse=True)
        return profiles

    async def get_slow_operations(
        self, threshold_ms: float = 1000, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get slow operations"""
        slow_spans = [
            span
            for span in self.completed_spans.values()
            if span.duration_ms and span.duration_ms > threshold_ms
        ]

        # Sort by duration (slowest first)
        slow_spans.sort(key=lambda x: x.duration_ms, reverse=True)

        return [
            {
                "trace_id": span.trace_id,
                "span_id": span.span_id,
                "operation_name": span.operation_name,
                "service_name": span.service_name,
                "duration_ms": span.duration_ms,
                "start_time": span.start_time.isoformat(),
                "status": span.status.value,
                "tags": span.tags,
            }
            for span in slow_spans[:limit]
        ]

    async def get_error_spans(
        self, since: datetime = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get error spans"""
        if since is None:
            since = datetime.now() - timedelta(hours=1)

        error_spans = [
            span
            for span in self.completed_spans.values()
            if span.status != SpanStatus.OK and span.end_time and span.end_time >= since
        ]

        # Sort by timestamp (most recent first)
        error_spans.sort(key=lambda x: x.end_time, reverse=True)

        return [
            {
                "trace_id": span.trace_id,
                "span_id": span.span_id,
                "operation_name": span.operation_name,
                "service_name": span.service_name,
                "status": span.status.value,
                "start_time": span.start_time.isoformat(),
                "end_time": span.end_time.isoformat(),
                "duration_ms": span.duration_ms,
                "tags": span.tags,
                "logs": span.logs,
            }
            for span in error_spans[:limit]
        ]

    async def get_tracing_summary(self) -> Dict[str, Any]:
        """Get comprehensive tracing summary"""
        # Recent activity
        recent_cutoff = datetime.now() - timedelta(hours=1)
        recent_spans = [
            span
            for span in self.completed_spans.values()
            if span.end_time and span.end_time >= recent_cutoff
        ]

        # Activity by service
        service_activity = defaultdict(
            lambda: {"spans": 0, "errors": 0, "total_duration": 0}
        )
        for span in recent_spans:
            service = span.service_name
            service_activity[service]["spans"] += 1
            if span.status != SpanStatus.OK:
                service_activity[service]["errors"] += 1
            if span.duration_ms:
                service_activity[service]["total_duration"] += span.duration_ms

        # Calculate averages
        for service in service_activity:
            if service_activity[service]["spans"] > 0:
                service_activity[service]["avg_duration"] = (
                    service_activity[service]["total_duration"]
                    / service_activity[service]["spans"]
                )
                service_activity[service]["error_rate"] = (
                    service_activity[service]["errors"]
                    / service_activity[service]["spans"]
                )
            else:
                service_activity[service]["avg_duration"] = 0
                service_activity[service]["error_rate"] = 0

        return {
            "timestamp": datetime.now().isoformat(),
            "active_spans": len(self.active_spans),
            "completed_spans": len(self.completed_spans),
            "total_traces": len(self.trace_spans),
            "recent_activity": {
                "spans_last_hour": len(recent_spans),
                "services_active": len(service_activity),
                "service_breakdown": dict(service_activity),
            },
            "dependencies": len(self.dependencies),
            "performance_profiles": len(self.performance_profiles),
            "opentelemetry_available": OPENTELEMETRY_AVAILABLE,
            "jaeger_configured": bool(self.jaeger_endpoint),
        }

    async def search_traces(
        self,
        operation_name: str = None,
        service_name: str = None,
        min_duration_ms: float = None,
        max_duration_ms: float = None,
        status: SpanStatus = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Search traces with filters"""
        filtered_spans = list(self.completed_spans.values())

        # Apply filters
        if operation_name:
            filtered_spans = [
                s for s in filtered_spans if operation_name in s.operation_name
            ]

        if service_name:
            filtered_spans = [
                s for s in filtered_spans if s.service_name == service_name
            ]

        if min_duration_ms is not None:
            filtered_spans = [
                s
                for s in filtered_spans
                if s.duration_ms and s.duration_ms >= min_duration_ms
            ]

        if max_duration_ms is not None:
            filtered_spans = [
                s
                for s in filtered_spans
                if s.duration_ms and s.duration_ms <= max_duration_ms
            ]

        if status:
            filtered_spans = [s for s in filtered_spans if s.status == status]

        # Sort by end time (most recent first)
        filtered_spans.sort(key=lambda x: x.end_time or datetime.min, reverse=True)

        return [
            {
                "trace_id": span.trace_id,
                "span_id": span.span_id,
                "operation_name": span.operation_name,
                "service_name": span.service_name,
                "start_time": span.start_time.isoformat(),
                "end_time": span.end_time.isoformat() if span.end_time else None,
                "duration_ms": span.duration_ms,
                "status": span.status.value,
                "span_kind": span.span_kind.value,
                "tags": span.tags,
            }
            for span in filtered_spans[:limit]
        ]

    async def health_check(self) -> Dict[str, Any]:
        """Health check for tracing service"""
        return {
            "status": "healthy",
            "opentelemetry_available": OPENTELEMETRY_AVAILABLE,
            "jaeger_configured": bool(self.jaeger_endpoint),
            "active_spans": len(self.active_spans),
            "completed_spans": len(self.completed_spans),
            "total_traces": len(self.trace_spans),
            "dependencies": len(self.dependencies),
            "performance_profiles": len(self.performance_profiles),
        }

    async def clear_old_data(self, older_than_hours: int = 24) -> Dict[str, int]:
        """Clear old tracing data"""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)

        # Clear old spans
        old_span_ids = [
            span_id
            for span_id, span in self.completed_spans.items()
            if span.end_time and span.end_time < cutoff_time
        ]

        for span_id in old_span_ids:
            self.completed_spans.pop(span_id, None)

        # Clear old dependencies
        old_dependencies = [
            key for key, dep in self.dependencies.items() if dep.last_seen < cutoff_time
        ]

        for key in old_dependencies:
            self.dependencies.pop(key, None)

        return {
            "spans_cleared": len(old_span_ids),
            "dependencies_cleared": len(old_dependencies),
        }


# Initialize function for dependency injection
async def init_distributed_tracing_service(
    service_name: str = "context-gateway", jaeger_endpoint: str = None
) -> DistributedTracingService:
    """Initialize distributed tracing service"""
    service = DistributedTracingService(service_name, jaeger_endpoint)
    return service


# Mock tracer for when OpenTelemetry is not available
class MockTracer:
    """Mock tracer for when OpenTelemetry is not available"""

    def __init__(self, name: str):
        self.name = name

    def start_span(self, operation_name: str, **kwargs):
        return MockSpan(operation_name)


class MockSpan:
    """Mock span for when OpenTelemetry is not available"""

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.attributes = {}

    def set_attribute(self, key: str, value: str):
        self.attributes[key] = value

    def set_status(self, status):
        pass

    def end(self):
        pass
