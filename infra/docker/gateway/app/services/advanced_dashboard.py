"""
Advanced Dashboard Service - Phase 4
Provides real-time dashboard engine, interactive analytics UI, and alert management
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
import logging
from enum import Enum
import uuid

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.utils import PlotlyJSONEncoder

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logging.warning("Plotly not available. Dashboard visualizations will be limited.")

logger = logging.getLogger(__name__)


class WidgetType(Enum):
    """Types of dashboard widgets"""

    METRIC_CHART = "metric_chart"
    KPI_CARD = "kpi_card"
    ALERT_PANEL = "alert_panel"
    SERVICE_MAP = "service_map"
    TREND_ANALYSIS = "trend_analysis"
    ANOMALY_DETECTION = "anomaly_detection"
    PERFORMANCE_TABLE = "performance_table"
    INSIGHT_PANEL = "insight_panel"


class ChartType(Enum):
    """Types of charts"""

    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


class TimeRange(Enum):
    """Time range options for dashboard"""

    LAST_HOUR = "1h"
    LAST_6_HOURS = "6h"
    LAST_24_HOURS = "24h"
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"
    CUSTOM = "custom"


@dataclass
class DashboardWidget:
    """Dashboard widget configuration"""

    widget_id: str
    widget_type: WidgetType
    title: str
    position: Dict[str, int]  # x, y, width, height
    data_source: str
    config: Dict[str, Any] = field(default_factory=dict)
    refresh_interval: int = 30  # seconds
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class DashboardConfig:
    """Dashboard configuration"""

    dashboard_id: str
    name: str
    description: str
    widgets: List[DashboardWidget] = field(default_factory=list)
    layout: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True


@dataclass
class ChartData:
    """Data for chart visualization"""

    chart_type: ChartType
    data: List[Dict[str, Any]]
    layout: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KPIData:
    """Key Performance Indicator data"""

    title: str
    value: Union[float, int, str]
    unit: str
    trend: str  # up, down, stable
    trend_percentage: float
    status: str  # good, warning, critical
    threshold: Dict[str, float] = field(default_factory=dict)


class AdvancedDashboardService:
    """Advanced dashboard service for real-time analytics"""

    def __init__(self, max_dashboards: int = 50, max_widgets_per_dashboard: int = 20):
        self.max_dashboards = max_dashboards
        self.max_widgets_per_dashboard = max_widgets_per_dashboard

        # Dashboard storage
        self.dashboards: Dict[str, DashboardConfig] = {}
        self.widgets: Dict[str, DashboardWidget] = {}

        # Data cache for widgets
        self.widget_data_cache: Dict[str, Dict[str, Any]] = {}
        self.data_cache_ttl = timedelta(minutes=5)

        # Real-time data streams
        self.active_streams: Dict[str, asyncio.Queue] = {}

        # Configuration
        self.default_time_range = TimeRange.LAST_24_HOURS
        self.auto_refresh_enabled = True
        self.refresh_interval = 30  # seconds

        # Background tasks
        self._refresh_task = None
        self._cleanup_task = None

        # Start background tasks
        self._start_background_tasks()

        logger.info("Advanced Dashboard Service initialized")

    def _start_background_tasks(self):
        """Start background dashboard tasks"""
        if self._refresh_task is None:
            self._refresh_task = asyncio.create_task(self._refresh_loop())

        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _refresh_loop(self):
        """Background data refresh loop"""
        while True:
            try:
                await asyncio.sleep(self.refresh_interval)
                if self.auto_refresh_enabled:
                    await self._refresh_all_widgets()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in refresh loop: {e}")

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

    async def _refresh_all_widgets(self):
        """Refresh data for all active widgets"""
        for widget in self.widgets.values():
            if widget.last_updated < datetime.now() - timedelta(
                seconds=widget.refresh_interval
            ):
                try:
                    await self._refresh_widget_data(widget)
                    widget.last_updated = datetime.now()
                except Exception as e:
                    logger.error(f"Error refreshing widget {widget.widget_id}: {e}")

    async def _refresh_widget_data(self, widget: DashboardWidget):
        """Refresh data for a specific widget"""
        # This would integrate with other services to get real data
        # For now, we'll generate sample data

        if widget.widget_type == WidgetType.METRIC_CHART:
            await self._generate_chart_data(widget)
        elif widget.widget_type == WidgetType.KPI_CARD:
            await self._generate_kpi_data(widget)
        elif widget.widget_type == WidgetType.ALERT_PANEL:
            await self._generate_alert_data(widget)
        elif widget.widget_type == WidgetType.SERVICE_MAP:
            await self._generate_service_map_data(widget)
        elif widget.widget_type == WidgetType.TREND_ANALYSIS:
            await self._generate_trend_data(widget)
        elif widget.widget_type == WidgetType.ANOMALY_DETECTION:
            await self._generate_anomaly_data(widget)
        elif widget.widget_type == WidgetType.PERFORMANCE_TABLE:
            await self._generate_performance_table_data(widget)
        elif widget.widget_type == WidgetType.INSIGHT_PANEL:
            await self._generate_insight_data(widget)

    async def _generate_chart_data(self, widget: DashboardWidget):
        """Generate chart data for metric chart widget"""
        try:
            # Sample time series data
            time_points = []
            values = []

            # Generate data based on time range
            hours = 24  # Default to 24 hours
            if self.default_time_range == TimeRange.LAST_HOUR:
                hours = 1
            elif self.default_time_range == TimeRange.LAST_6_HOURS:
                hours = 6
            elif self.default_time_range == TimeRange.LAST_7_DAYS:
                hours = 168
            elif self.default_time_range == TimeRange.LAST_30_DAYS:
                hours = 720

            for i in range(hours * 6):  # Every 10 minutes
                timestamp = (
                    datetime.now() - timedelta(hours=hours) + timedelta(minutes=i * 10)
                )
                value = (
                    50
                    + 20 * (0.5 + 0.5 * (i / (hours * 6)))
                    + 5 * (0.5 - 0.5 * (i / (hours * 6)))
                )
                time_points.append(timestamp.isoformat())
                values.append(value)

            chart_data = {
                "time": time_points,
                "value": values,
                "title": widget.title,
                "unit": widget.config.get("unit", ""),
            }

            if PLOTLY_AVAILABLE:
                # Create Plotly chart
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=time_points,
                        y=values,
                        mode="lines",
                        name=widget.title,
                        line=dict(color="#1f77b4", width=2),
                    )
                )

                fig.update_layout(
                    title=widget.title,
                    xaxis_title="Time",
                    yaxis_title=widget.config.get("unit", "Value"),
                    template="plotly_white",
                )

                chart_json = fig.to_json()
            else:
                # Simple JSON chart data
                chart_json = json.dumps(chart_data)

            self.widget_data_cache[widget.widget_id] = {
                "data": chart_json,
                "type": "chart",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating chart data for {widget.widget_id}: {e}")

    async def _generate_kpi_data(self, widget: DashboardWidget):
        """Generate KPI data for KPI card widget"""
        try:
            # Sample KPI calculation
            current_value = 85.7
            previous_value = 82.3
            trend = (
                "up"
                if current_value > previous_value
                else "down"
                if current_value < previous_value
                else "stable"
            )
            trend_percentage = (
                ((current_value - previous_value) / previous_value) * 100
                if previous_value != 0
                else 0
            )

            # Determine status based on thresholds
            warning_threshold = widget.config.get("warning_threshold", 80)
            critical_threshold = widget.config.get("critical_threshold", 90)

            if current_value >= critical_threshold:
                status = "critical"
            elif current_value >= warning_threshold:
                status = "warning"
            else:
                status = "good"

            kpi_data = KPIData(
                title=widget.title,
                value=current_value,
                unit=widget.config.get("unit", ""),
                trend=trend,
                trend_percentage=trend_percentage,
                status=status,
                threshold={
                    "warning": warning_threshold,
                    "critical": critical_threshold,
                },
            )

            self.widget_data_cache[widget.widget_id] = {
                "data": asdict(kpi_data),
                "type": "kpi",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating KPI data for {widget.widget_id}: {e}")

    async def _generate_alert_data(self, widget: DashboardWidget):
        """Generate alert data for alert panel widget"""
        try:
            # Sample alert data
            alerts = [
                {
                    "id": str(uuid.uuid4()),
                    "title": "High CPU Usage",
                    "description": "CPU usage exceeded 90% threshold",
                    "severity": "high",
                    "timestamp": (datetime.now() - timedelta(minutes=15)).isoformat(),
                    "status": "active",
                },
                {
                    "id": str(uuid.uuid4()),
                    "title": "Memory Pressure",
                    "description": "Memory usage is approaching limit",
                    "severity": "medium",
                    "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                    "status": "active",
                },
                {
                    "id": str(uuid.uuid4()),
                    "title": "Cache Hit Rate Low",
                    "description": "Cache hit rate below 70%",
                    "severity": "medium",
                    "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "status": "resolved",
                },
            ]

            self.widget_data_cache[widget.widget_id] = {
                "data": alerts,
                "type": "alerts",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating alert data for {widget.widget_id}: {e}")

    async def _generate_service_map_data(self, widget: DashboardWidget):
        """Generate service map data for service map widget"""
        try:
            # Sample service dependency data
            nodes = [
                {"id": "gateway", "label": "Context Gateway", "type": "service"},
                {"id": "qdrant", "label": "Qdrant", "type": "database"},
                {"id": "redis", "label": "Redis", "type": "cache"},
                {"id": "postgres", "label": "PostgreSQL", "type": "database"},
                {"id": "letta", "label": "Letta", "type": "service"},
            ]

            edges = [
                {
                    "source": "gateway",
                    "target": "qdrant",
                    "latency": 45,
                    "error_rate": 0.02,
                },
                {
                    "source": "gateway",
                    "target": "redis",
                    "latency": 12,
                    "error_rate": 0.001,
                },
                {
                    "source": "gateway",
                    "target": "postgres",
                    "latency": 23,
                    "error_rate": 0.005,
                },
                {
                    "source": "gateway",
                    "target": "letta",
                    "latency": 67,
                    "error_rate": 0.01,
                },
            ]

            service_map_data = {"nodes": nodes, "edges": edges, "layout": "force"}

            self.widget_data_cache[widget.widget_id] = {
                "data": service_map_data,
                "type": "service_map",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(
                f"Error generating service map data for {widget.widget_id}: {e}"
            )

    async def _generate_trend_data(self, widget: DashboardWidget):
        """Generate trend analysis data for trend analysis widget"""
        try:
            # Sample trend data
            trends = [
                {
                    "metric": "Response Time",
                    "current": 125.7,
                    "previous": 118.2,
                    "trend": "increasing",
                    "change_percentage": 6.3,
                    "data_points": [118.2, 120.1, 119.8, 122.5, 125.7],
                },
                {
                    "metric": "Throughput",
                    "current": 1250,
                    "previous": 1320,
                    "trend": "decreasing",
                    "change_percentage": -5.3,
                    "data_points": [1320, 1305, 1280, 1265, 1250],
                },
                {
                    "metric": "Error Rate",
                    "current": 0.8,
                    "previous": 1.2,
                    "trend": "decreasing",
                    "change_percentage": -33.3,
                    "data_points": [1.2, 1.1, 1.0, 0.9, 0.8],
                },
            ]

            self.widget_data_cache[widget.widget_id] = {
                "data": trends,
                "type": "trends",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating trend data for {widget.widget_id}: {e}")

    async def _generate_anomaly_data(self, widget: DashboardWidget):
        """Generate anomaly detection data for anomaly detection widget"""
        try:
            # Sample anomaly data
            anomalies = [
                {
                    "id": str(uuid.uuid4()),
                    "metric": "CPU Usage",
                    "type": "spike",
                    "severity": "high",
                    "detected_at": (datetime.now() - timedelta(minutes=25)).isoformat(),
                    "value": 94.5,
                    "expected": 65.2,
                    "confidence": 0.92,
                },
                {
                    "id": str(uuid.uuid4()),
                    "metric": "Memory Usage",
                    "type": "trend",
                    "severity": "medium",
                    "detected_at": (datetime.now() - timedelta(hours=3)).isoformat(),
                    "value": 78.9,
                    "expected": 72.1,
                    "confidence": 0.87,
                },
            ]

            self.widget_data_cache[widget.widget_id] = {
                "data": anomalies,
                "type": "anomalies",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating anomaly data for {widget.widget_id}: {e}")

    async def _generate_performance_table_data(self, widget: DashboardWidget):
        """Generate performance table data for performance table widget"""
        try:
            # Sample performance table data
            performance_data = [
                {
                    "service": "Context Gateway",
                    "operation": "Search",
                    "avg_response_time": 125.7,
                    "p95_response_time": 234.5,
                    "p99_response_time": 456.2,
                    "throughput": 1250,
                    "error_rate": 0.8,
                    "status": "healthy",
                },
                {
                    "service": "Qdrant",
                    "operation": "Vector Search",
                    "avg_response_time": 45.2,
                    "p95_response_time": 89.3,
                    "p99_response_time": 156.7,
                    "throughput": 3400,
                    "error_rate": 0.02,
                    "status": "healthy",
                },
                {
                    "service": "Redis",
                    "operation": "Cache Get",
                    "avg_response_time": 2.1,
                    "p95_response_time": 4.5,
                    "p99_response_time": 8.2,
                    "throughput": 12500,
                    "error_rate": 0.001,
                    "status": "healthy",
                },
            ]

            self.widget_data_cache[widget.widget_id] = {
                "data": performance_data,
                "type": "performance_table",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(
                f"Error generating performance table data for {widget.widget_id}: {e}"
            )

    async def _generate_insight_data(self, widget: DashboardWidget):
        """Generate insight data for insight panel widget"""
        try:
            # Sample insight data
            insights = [
                {
                    "id": str(uuid.uuid4()),
                    "title": "CPU Usage Trending Upward",
                    "description": "CPU usage has increased by 15% over the last 24 hours",
                    "type": "trend",
                    "priority": "medium",
                    "confidence": 0.85,
                    "generated_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "recommendations": [
                        "Investigate recent changes in workload",
                        "Consider scaling up resources",
                        "Monitor for continued growth",
                    ],
                },
                {
                    "id": str(uuid.uuid4()),
                    "title": "Cache Optimization Opportunity",
                    "description": "Cache hit rate could be improved by 20% with better key distribution",
                    "type": "optimization",
                    "priority": "low",
                    "confidence": 0.72,
                    "generated_at": (datetime.now() - timedelta(hours=6)).isoformat(),
                    "recommendations": [
                        "Review cache key patterns",
                        "Implement cache warming strategies",
                        "Consider cache partitioning",
                    ],
                },
            ]

            self.widget_data_cache[widget.widget_id] = {
                "data": insights,
                "type": "insights",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating insight data for {widget.widget_id}: {e}")

    async def _cleanup_old_data(self):
        """Clean up old widget data"""
        cutoff_time = datetime.now() - self.data_cache_ttl

        # Remove old cached data
        old_widget_ids = [
            widget_id
            for widget_id, data in self.widget_data_cache.items()
            if datetime.fromisoformat(data["timestamp"]) < cutoff_time
        ]

        for widget_id in old_widget_ids:
            del self.widget_data_cache[widget_id]

        if old_widget_ids:
            logger.debug(f"Cleaned up data for {len(old_widget_ids)} widgets")

    async def create_dashboard(
        self, name: str, description: str, widgets: List[DashboardWidget] = None
    ) -> str:
        """Create a new dashboard"""
        if len(self.dashboards) >= self.max_dashboards:
            raise ValueError(
                f"Maximum number of dashboards ({self.max_dashboards}) reached"
            )

        dashboard_id = str(uuid.uuid4())

        dashboard = DashboardConfig(
            dashboard_id=dashboard_id,
            name=name,
            description=description,
            widgets=widgets or [],
            layout={"grid": {"cols": 12, "rows": 8}},
            is_active=True,
        )

        self.dashboards[dashboard_id] = dashboard

        # Add widgets if provided
        if widgets:
            for widget in widgets:
                if len(dashboard.widgets) < self.max_widgets_per_dashboard:
                    dashboard.widgets.append(widget)
                    self.widgets[widget.widget_id] = widget
                else:
                    logger.warning(
                        f"Maximum widgets per dashboard reached for {dashboard_id}"
                    )

        logger.info(f"Created dashboard: {name} ({dashboard_id})")
        return dashboard_id

    async def add_widget_to_dashboard(
        self, dashboard_id: str, widget: DashboardWidget
    ) -> bool:
        """Add a widget to an existing dashboard"""
        if dashboard_id not in self.dashboards:
            return False

        dashboard = self.dashboards[dashboard_id]

        if len(dashboard.widgets) >= self.max_widgets_per_dashboard:
            logger.warning(f"Maximum widgets per dashboard reached for {dashboard_id}")
            return False

        dashboard.widgets.append(widget)
        dashboard.updated_at = datetime.now()
        self.widgets[widget.widget_id] = widget

        logger.info(f"Added widget {widget.widget_id} to dashboard {dashboard_id}")
        return True

    async def update_widget(self, widget_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing widget"""
        if widget_id not in self.widgets:
            return False

        widget = self.widgets[widget_id]

        # Update widget properties
        for key, value in updates.items():
            if hasattr(widget, key):
                setattr(widget, key, value)

        widget.last_updated = datetime.now()

        # Clear cached data to force refresh
        if widget_id in self.widget_data_cache:
            del self.widget_data_cache[widget_id]

        logger.info(f"Updated widget {widget_id}")
        return True

    async def remove_widget_from_dashboard(
        self, dashboard_id: str, widget_id: str
    ) -> bool:
        """Remove a widget from a dashboard"""
        if dashboard_id not in self.dashboards:
            return False

        dashboard = self.dashboards[dashboard_id]
        dashboard.widgets = [w for w in dashboard.widgets if w.widget_id != widget_id]
        dashboard.updated_at = datetime.now()

        # Remove widget from storage
        self.widgets.pop(widget_id, None)
        self.widget_data_cache.pop(widget_id, None)

        logger.info(f"Removed widget {widget_id} from dashboard {dashboard_id}")
        return True

    async def delete_dashboard(self, dashboard_id: str) -> bool:
        """Delete a dashboard"""
        if dashboard_id not in self.dashboards:
            return False

        dashboard = self.dashboards[dashboard_id]

        # Remove all widgets from the dashboard
        for widget in dashboard.widgets:
            self.widgets.pop(widget.widget_id, None)
            self.widget_data_cache.pop(widget.widget_id, None)

        # Remove dashboard
        del self.dashboards[dashboard_id]

        logger.info(f"Deleted dashboard {dashboard_id}")
        return True

    async def get_dashboard(self, dashboard_id: str) -> Optional[DashboardConfig]:
        """Get dashboard configuration"""
        return self.dashboards.get(dashboard_id)

    async def get_all_dashboards(self) -> List[DashboardConfig]:
        """Get all dashboards"""
        return list(self.dashboards.values())

    async def get_widget_data(self, widget_id: str) -> Optional[Dict[str, Any]]:
        """Get cached data for a widget"""
        if widget_id not in self.widget_data_cache:
            # Try to refresh the widget if data is not cached
            widget = self.widgets.get(widget_id)
            if widget:
                await self._refresh_widget_data(widget)

        return self.widget_data_cache.get(widget_id)

    async def get_dashboard_render_data(
        self, dashboard_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get all data needed to render a dashboard"""
        dashboard = self.dashboards.get(dashboard_id)
        if not dashboard:
            return None

        # Get data for all widgets in the dashboard
        widget_data = {}
        for widget in dashboard.widgets:
            data = await self.get_widget_data(widget.widget_id)
            if data:
                widget_data[widget.widget_id] = {"widget": asdict(widget), "data": data}

        return {
            "dashboard": asdict(dashboard),
            "widget_data": widget_data,
            "timestamp": datetime.now().isoformat(),
        }

    async def create_default_dashboard(self) -> str:
        """Create a default dashboard with common widgets"""
        default_widgets = [
            DashboardWidget(
                widget_id=str(uuid.uuid4()),
                widget_type=WidgetType.KPI_CARD,
                title="System Health",
                position={"x": 0, "y": 0, "width": 3, "height": 2},
                data_source="system",
                config={"unit": "%", "warning_threshold": 80, "critical_threshold": 90},
                refresh_interval=60,
            ),
            DashboardWidget(
                widget_id=str(uuid.uuid4()),
                widget_type=WidgetType.METRIC_CHART,
                title="Response Time",
                position={"x": 3, "y": 0, "width": 6, "height": 2},
                data_source="metrics",
                config={"unit": "ms", "chart_type": "line"},
                refresh_interval=30,
            ),
            DashboardWidget(
                widget_id=str(uuid.uuid4()),
                widget_type=WidgetType.ALERT_PANEL,
                title="Active Alerts",
                position={"x": 9, "y": 0, "width": 3, "height": 2},
                data_source="alerts",
                config={"max_alerts": 10},
                refresh_interval=60,
            ),
            DashboardWidget(
                widget_id=str(uuid.uuid4()),
                widget_type=WidgetType.SERVICE_MAP,
                title="Service Dependencies",
                position={"x": 0, "y": 2, "width": 6, "height": 4},
                data_source="tracing",
                config={"layout": "force"},
                refresh_interval=120,
            ),
            DashboardWidget(
                widget_id=str(uuid.uuid4()),
                widget_type=WidgetType.PERFORMANCE_TABLE,
                title="Service Performance",
                position={"x": 6, "y": 2, "width": 6, "height": 4},
                data_source="performance",
                config={"services": ["gateway", "qdrant", "redis"]},
                refresh_interval=60,
            ),
            DashboardWidget(
                widget_id=str(uuid.uuid4()),
                widget_type=WidgetType.INSIGHT_PANEL,
                title="AI Insights",
                position={"x": 0, "y": 6, "width": 12, "height": 2},
                data_source="intelligence",
                config={"max_insights": 5},
                refresh_interval=300,
            ),
        ]

        return await self.create_dashboard(
            name="Default Dashboard",
            description="Default monitoring dashboard with key metrics and insights",
            widgets=default_widgets,
        )

    async def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get summary of all dashboards"""
        try:
            # Dashboard statistics
            total_dashboards = len(self.dashboards)
            active_dashboards = len(
                [d for d in self.dashboards.values() if d.is_active]
            )
            total_widgets = len(self.widgets)

            # Widget type distribution
            widget_type_distribution = {}
            for widget in self.widgets.values():
                widget_type = widget.widget_type.value
                widget_type_distribution[widget_type] = (
                    widget_type_distribution.get(widget_type, 0) + 1
                )

            # Data cache statistics
            cached_widgets = len(self.widget_data_cache)
            stale_widgets = len(
                [
                    widget_id
                    for widget_id, data in self.widget_data_cache.items()
                    if datetime.fromisoformat(data["timestamp"])
                    < datetime.now() - self.data_cache_ttl
                ]
            )

            return {
                "timestamp": datetime.now().isoformat(),
                "dashboard_stats": {
                    "total_dashboards": total_dashboards,
                    "active_dashboards": active_dashboards,
                    "total_widgets": total_widgets,
                    "average_widgets_per_dashboard": total_widgets / total_dashboards
                    if total_dashboards > 0
                    else 0,
                },
                "widget_distribution": widget_type_distribution,
                "cache_stats": {
                    "cached_widgets": cached_widgets,
                    "stale_widgets": stale_widgets,
                    "cache_hit_rate": (cached_widgets - stale_widgets) / cached_widgets
                    if cached_widgets > 0
                    else 0,
                },
                "configuration": {
                    "auto_refresh_enabled": self.auto_refresh_enabled,
                    "refresh_interval": self.refresh_interval,
                    "default_time_range": self.default_time_range.value,
                    "plotly_available": PLOTLY_AVAILABLE,
                },
            }

        except Exception as e:
            logger.error(f"Error generating dashboard summary: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def health_check(self) -> Dict[str, Any]:
        """Health check for dashboard service"""
        return {
            "status": "healthy",
            "dashboards_loaded": len(self.dashboards),
            "widgets_loaded": len(self.widgets),
            "cached_data_items": len(self.widget_data_cache),
            "auto_refresh_enabled": self.auto_refresh_enabled,
            "plotly_available": PLOTLY_AVAILABLE,
            "background_tasks": {
                "refresh_task_running": self._refresh_task is not None
                and not self._refresh_task.done(),
                "cleanup_task_running": self._cleanup_task is not None
                and not self._cleanup_task.done(),
            },
        }

    async def set_time_range(self, time_range: TimeRange) -> None:
        """Set the default time range for all widgets"""
        self.default_time_range = time_range

        # Clear cached data to force refresh with new time range
        self.widget_data_cache.clear()

        logger.info(f"Time range changed to {time_range.value}")

    async def set_auto_refresh(self, enabled: bool, interval: int = None) -> None:
        """Configure auto refresh settings"""
        self.auto_refresh_enabled = enabled
        if interval is not None:
            self.refresh_interval = interval

        logger.info(
            f"Auto refresh set to {enabled}, interval: {self.refresh_interval}s"
        )


# Initialize function for dependency injection
async def init_advanced_dashboard_service(
    max_dashboards: int = 50, max_widgets_per_dashboard: int = 20
) -> AdvancedDashboardService:
    """Initialize advanced dashboard service"""
    service = AdvancedDashboardService(max_dashboards, max_widgets_per_dashboard)
    return service
