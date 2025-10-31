"""
Advanced Analytics Service - Phase 4
Provides ML-based performance optimization, anomaly detection, and predictive analytics
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
from enum import Enum

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_absolute_error

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning(
        "scikit-learn not available. Some advanced analytics features will be disabled."
    )

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """Types of anomalies that can be detected"""

    SPIKE = "spike"
    DROP = "drop"
    TREND = "trend"
    OUTLIER = "outlier"
    PATTERN_BREAK = "pattern_break"


class AlertSeverity(Enum):
    """Alert severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AnomalyDetection:
    """Anomaly detection result"""

    metric_name: str
    anomaly_type: AnomalyType
    severity: AlertSeverity
    timestamp: datetime
    value: float
    expected_value: float
    confidence: float
    description: str
    metadata: Dict[str, Any]


@dataclass
class PerformancePrediction:
    """Performance prediction result"""

    metric_name: str
    predicted_value: float
    confidence_interval: Tuple[float, float]
    prediction_horizon: timedelta
    model_accuracy: float
    timestamp: datetime
    factors: List[str]


@dataclass
class OptimizationRecommendation:
    """Optimization recommendation"""

    category: str  # cache, database, network, etc.
    priority: AlertSeverity
    description: str
    expected_improvement: str
    implementation_complexity: str
    estimated_effort: str
    related_metrics: List[str]


@dataclass
class PatternInsight:
    """Pattern analysis result"""

    pattern_type: str
    description: str
    confidence: float
    time_period: str
    impact_assessment: str
    recommendations: List[str]


class AdvancedAnalyticsService:
    """Advanced analytics service with ML-based optimization"""

    def __init__(self, history_window: int = 1000, prediction_horizon_hours: int = 24):
        self.history_window = history_window
        self.prediction_horizon = timedelta(hours=prediction_horizon_hours)

        # Data storage
        self.metrics_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=history_window)
        )
        self.anomalies: List[AnomalyDetection] = []
        self.predictions: Dict[str, PerformancePrediction] = {}
        self.patterns: List[PatternInsight] = []

        # ML models (initialized when data is available)
        self.anomaly_detectors: Dict[str, IsolationForest] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.prediction_models: Dict[str, LinearRegression] = {}

        # Configuration
        self.anomaly_threshold = 0.1  # Isolation Forest contamination
        self.min_data_points = 50  # Minimum data points for ML models

        # Analytics state
        self.last_analysis_time = datetime.now()
        self.analysis_interval = timedelta(minutes=5)

        logger.info("Advanced Analytics Service initialized")

    async def add_metric_data(
        self, metric_name: str, value: float, timestamp: datetime = None
    ) -> None:
        """Add metric data point for analysis"""
        if timestamp is None:
            timestamp = datetime.now()

        # Store in history
        self.metrics_history[metric_name].append(
            {"timestamp": timestamp, "value": value}
        )

        # Trigger analysis if enough data and interval has passed
        if (
            len(self.metrics_history[metric_name]) >= self.min_data_points
            and timestamp - self.last_analysis_time >= self.analysis_interval
        ):
            await self._analyze_metric(metric_name)

    async def _analyze_metric(self, metric_name: str) -> None:
        """Perform comprehensive analysis on a metric"""
        try:
            # Get historical data
            history = list(self.metrics_history[metric_name])
            if len(history) < self.min_data_points:
                return

            # Extract values and timestamps
            values = np.array([point["value"] for point in history])
            timestamps = np.array([point["timestamp"].timestamp() for point in history])

            # Detect anomalies
            anomalies = await self._detect_anomalies(metric_name, values, timestamps)
            self.anomalies.extend(anomalies)

            # Generate predictions
            if SKLEARN_AVAILABLE:
                prediction = await self._predict_performance(
                    metric_name, values, timestamps
                )
                if prediction:
                    self.predictions[metric_name] = prediction

            # Analyze patterns
            patterns = await self._analyze_patterns(metric_name, values, timestamps)
            self.patterns.extend(patterns)

            logger.debug(f"Completed analysis for metric: {metric_name}")

        except Exception as e:
            logger.error(f"Error analyzing metric {metric_name}: {e}")

    async def _detect_anomalies(
        self, metric_name: str, values: np.ndarray, timestamps: np.ndarray
    ) -> List[AnomalyDetection]:
        """Detect anomalies using multiple methods"""
        anomalies = []

        if not SKLEARN_AVAILABLE:
            # Simple statistical anomaly detection
            mean_val = np.mean(values)
            std_val = np.std(values)
            threshold = 3 * std_val

            for i, (value, timestamp) in enumerate(
                zip(values[-10:], timestamps[-10:])
            ):  # Check last 10 points
                if abs(value - mean_val) > threshold:
                    anomaly_type = (
                        AnomalyType.SPIKE if value > mean_val else AnomalyType.DROP
                    )
                    severity = (
                        AlertSeverity.HIGH
                        if abs(value - mean_val) > 2 * threshold
                        else AlertSeverity.MEDIUM
                    )

                    anomalies.append(
                        AnomalyDetection(
                            metric_name=metric_name,
                            anomaly_type=anomaly_type,
                            severity=severity,
                            timestamp=datetime.fromtimestamp(timestamp),
                            value=float(value),
                            expected_value=float(mean_val),
                            confidence=min(abs(value - mean_val) / threshold, 1.0),
                            description=f"Statistical anomaly detected: {value:.2f} vs expected {mean_val:.2f}",
                            metadata={
                                "method": "statistical",
                                "z_score": abs(value - mean_val) / std_val,
                            },
                        )
                    )
        else:
            # ML-based anomaly detection
            if metric_name not in self.anomaly_detectors:
                # Initialize and train anomaly detector
                detector = IsolationForest(
                    contamination=self.anomaly_threshold, random_state=42
                )
                scaler = StandardScaler()

                # Reshape data for sklearn
                X = values.reshape(-1, 1)
                X_scaled = scaler.fit_transform(X)
                detector.fit(X_scaled)

                self.anomaly_detectors[metric_name] = detector
                self.scalers[metric_name] = scaler

            # Detect anomalies
            detector = self.anomaly_detectors[metric_name]
            scaler = self.scalers[metric_name]

            X = values.reshape(-1, 1)
            X_scaled = scaler.transform(X)
            anomaly_scores = detector.decision_function(X_scaled)

            # Check recent points for anomalies
            for i, (score, value, timestamp) in enumerate(
                zip(anomaly_scores[-10:], values[-10:], timestamps[-10:])
            ):
                if score < 0:  # Anomaly detected
                    severity = (
                        AlertSeverity.CRITICAL
                        if score < -0.5
                        else AlertSeverity.HIGH
                        if score < -0.2
                        else AlertSeverity.MEDIUM
                    )

                    anomalies.append(
                        AnomalyDetection(
                            metric_name=metric_name,
                            anomaly_type=AnomalyType.OUTLIER,
                            severity=severity,
                            timestamp=datetime.fromtimestamp(timestamp),
                            value=float(value),
                            expected_value=float(
                                np.mean(values[:-10])
                            ),  # Excluding current point
                            confidence=float(abs(score)),
                            description=f"ML-based anomaly detected: score={score:.3f}",
                            metadata={
                                "method": "isolation_forest",
                                "anomaly_score": float(score),
                            },
                        )
                    )

        return anomalies

    async def _predict_performance(
        self, metric_name: str, values: np.ndarray, timestamps: np.ndarray
    ) -> Optional[PerformancePrediction]:
        """Predict future performance using time series analysis"""
        if not SKLEARN_AVAILABLE:
            return None

        try:
            # Prepare data for prediction
            if metric_name not in self.prediction_models:
                # Initialize prediction model
                model = LinearRegression()

                # Use time as feature
                X = timestamps.reshape(-1, 1)
                y = values

                # Train model
                model.fit(X, y)
                self.prediction_models[metric_name] = model
            else:
                model = self.prediction_models[metric_name]

            # Make prediction for future time
            future_timestamp = (datetime.now() + self.prediction_horizon).timestamp()
            future_time_features = np.array([[future_timestamp]])

            predicted_value = model.predict(future_time_features)[0]

            # Calculate confidence interval based on historical error
            X = timestamps.reshape(-1, 1)
            y = values
            predictions = model.predict(X)
            mae = mean_absolute_error(y, predictions)

            confidence_interval = (
                max(0, predicted_value - 2 * mae),
                predicted_value + 2 * mae,
            )

            # Calculate model accuracy
            model_accuracy = max(0, 1 - (mae / np.mean(values)))

            # Identify contributing factors
            factors = []
            if metric_name.lower().startswith("response"):
                factors = ["server_load", "database_performance", "cache_efficiency"]
            elif metric_name.lower().startswith("cache"):
                factors = ["data_access_patterns", "memory_usage", "ttl_settings"]
            elif metric_name.lower().startswith("cpu"):
                factors = ["request_volume", "compute_intensity", "resource_contention"]

            return PerformancePrediction(
                metric_name=metric_name,
                predicted_value=float(predicted_value),
                confidence_interval=tuple(map(float, confidence_interval)),
                prediction_horizon=self.prediction_horizon,
                model_accuracy=float(model_accuracy),
                timestamp=datetime.now(),
                factors=factors,
            )

        except Exception as e:
            logger.error(f"Error predicting performance for {metric_name}: {e}")
            return None

    async def _analyze_patterns(
        self, metric_name: str, values: np.ndarray, timestamps: np.ndarray
    ) -> List[PatternInsight]:
        """Analyze patterns in metric data"""
        patterns = []

        try:
            # Trend analysis
            if len(values) >= 20:
                # Simple linear trend
                x = np.arange(len(values))
                trend_slope = np.polyfit(x, values, 1)[0]

                if abs(trend_slope) > 0.01:  # Significant trend
                    trend_direction = "increasing" if trend_slope > 0 else "decreasing"
                    confidence = min(abs(trend_slope) * 100, 1.0)

                    patterns.append(
                        PatternInsight(
                            pattern_type="trend",
                            description=f"Metric shows {trend_direction} trend with slope {trend_slope:.4f}",
                            confidence=confidence,
                            time_period=f"last {len(values)} data points",
                            impact_assessment="high"
                            if abs(trend_slope) > 0.05
                            else "medium",
                            recommendations=[
                                f"Monitor {metric_name} closely for continued {trend_direction} trend",
                                "Investigate root cause of trend if it continues",
                            ],
                        )
                    )

            # Seasonality/cyclical patterns (simple approach)
            if len(values) >= 50:
                # Check for cyclical patterns using autocorrelation
                values_normalized = (values - np.mean(values)) / np.std(values)

                # Simple periodicity check
                for period in [7, 24, 168]:  # Weekly, daily, hourly patterns
                    if len(values) >= period * 2:
                        correlation = np.corrcoef(
                            values_normalized[:-period], values_normalized[period:]
                        )[0, 1]

                        if correlation > 0.7:
                            period_name = {7: "weekly", 24: "daily", 168: "hourly"}.get(
                                period, f"{period}-interval"
                            )

                            patterns.append(
                                PatternInsight(
                                    pattern_type="seasonality",
                                    description=f"Strong {period_name} cyclical pattern detected (correlation: {correlation:.3f})",
                                    confidence=float(correlation),
                                    time_period=f"analysis of {len(values)} data points",
                                    impact_assessment="medium",
                                    recommendations=[
                                        f"Consider {period_name} capacity planning",
                                        "Optimize resource allocation based on cyclical patterns",
                                    ],
                                )
                            )

            # Volatility analysis
            if len(values) >= 30:
                rolling_std = pd.Series(values).rolling(window=10).std().dropna()
                avg_volatility = np.mean(rolling_std)
                recent_volatility = (
                    rolling_std.iloc[-5:].mean()
                    if len(rolling_std) >= 5
                    else avg_volatility
                )

                if recent_volatility > avg_volatility * 1.5:
                    patterns.append(
                        PatternInsight(
                            pattern_type="volatility_spike",
                            description=f"Recent volatility spike detected: {recent_volatility:.3f} vs avg {avg_volatility:.3f}",
                            confidence=min(
                                (recent_volatility / avg_volatility - 1), 1.0
                            ),
                            time_period="last 30+ data points",
                            impact_assessment="high",
                            recommendations=[
                                "Investigate cause of increased volatility",
                                "Consider implementing stability measures",
                                "Monitor system stability closely",
                            ],
                        )
                    )

        except Exception as e:
            logger.error(f"Error analyzing patterns for {metric_name}: {e}")

        return patterns

    async def get_anomalies(
        self,
        metric_name: str = None,
        severity: AlertSeverity = None,
        since: datetime = None,
        limit: int = 100,
    ) -> List[AnomalyDetection]:
        """Get detected anomalies with filtering"""
        anomalies = self.anomalies

        # Apply filters
        if metric_name:
            anomalies = [a for a in anomalies if a.metric_name == metric_name]

        if severity:
            anomalies = [a for a in anomalies if a.severity == severity]

        if since:
            anomalies = [a for a in anomalies if a.timestamp >= since]

        # Sort by timestamp and limit
        anomalies.sort(key=lambda x: x.timestamp, reverse=True)
        return anomalies[:limit]

    async def get_predictions(
        self, metric_name: str = None
    ) -> Dict[str, PerformancePrediction]:
        """Get performance predictions"""
        if metric_name:
            return (
                {metric_name: self.predictions.get(metric_name)}
                if metric_name in self.predictions
                else {}
            )
        return self.predictions.copy()

    async def get_patterns(
        self, pattern_type: str = None, confidence_threshold: float = 0.5
    ) -> List[PatternInsight]:
        """Get detected patterns"""
        patterns = self.patterns

        if pattern_type:
            patterns = [p for p in patterns if p.pattern_type == pattern_type]

        patterns = [p for p in patterns if p.confidence >= confidence_threshold]

        # Sort by confidence and timestamp
        patterns.sort(key=lambda x: (x.confidence, x.timestamp), reverse=True)
        return patterns

    async def generate_optimization_recommendations(
        self,
    ) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on analysis"""
        recommendations = []

        try:
            # Analyze recent anomalies for optimization opportunities
            recent_anomalies = [
                a
                for a in self.anomalies
                if a.timestamp > datetime.now() - timedelta(hours=24)
            ]

            # Cache optimization recommendations
            cache_anomalies = [
                a for a in recent_anomalies if "cache" in a.metric_name.lower()
            ]
            if cache_anomalies:
                high_severity_cache = [
                    a
                    for a in cache_anomalies
                    if a.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]
                ]
                if high_severity_cache:
                    recommendations.append(
                        OptimizationRecommendation(
                            category="cache",
                            priority=AlertSeverity.HIGH,
                            description="Cache performance issues detected. Consider cache optimization.",
                            expected_improvement="20-40% reduction in response time",
                            implementation_complexity="medium",
                            estimated_effort="2-4 hours",
                            related_metrics=[
                                a.metric_name for a in high_severity_cache
                            ],
                        )
                    )

            # Performance optimization based on predictions
            for metric_name, prediction in self.predictions.items():
                if (
                    prediction.model_accuracy < 0.7
                ):  # Low prediction accuracy indicates instability
                    recommendations.append(
                        OptimizationRecommendation(
                            category="stability",
                            priority=AlertSeverity.MEDIUM,
                            description=f"Metric {metric_name} shows unstable behavior. Investigate root cause.",
                            expected_improvement="Improved system stability and predictability",
                            implementation_complexity="high",
                            estimated_effort="4-8 hours",
                            related_metrics=[metric_name],
                        )
                    )

            # Pattern-based recommendations
            trend_patterns = [
                p
                for p in self.patterns
                if p.pattern_type == "trend" and p.confidence > 0.8
            ]
            for pattern in trend_patterns:
                if (
                    "increasing" in pattern.description
                    and "response" in pattern.description
                ):
                    recommendations.append(
                        OptimizationRecommendation(
                            category="performance",
                            priority=AlertSeverity.MEDIUM,
                            description="Increasing response time trend detected. Proactive optimization recommended.",
                            expected_improvement="15-25% improvement in response times",
                            implementation_complexity="medium",
                            estimated_effort="2-6 hours",
                            related_metrics=["response_time", "throughput"],
                        )
                    )

            # Resource utilization recommendations
            for metric_name, history in self.metrics_history.items():
                if len(history) >= 100:
                    recent_values = [point["value"] for point in list(history)[-20:]]
                    avg_recent = np.mean(recent_values)

                    # High CPU usage
                    if "cpu" in metric_name.lower() and avg_recent > 80:
                        recommendations.append(
                            OptimizationRecommendation(
                                category="resource",
                                priority=AlertSeverity.HIGH,
                                description="High CPU usage detected. Consider scaling or optimization.",
                                expected_improvement="Reduced CPU utilization and better performance",
                                implementation_complexity="high",
                                estimated_effort="4-12 hours",
                                related_metrics=[
                                    metric_name,
                                    "response_time",
                                    "throughput",
                                ],
                            )
                        )

                    # Low cache hit rate
                    elif "cache_hit" in metric_name.lower() and avg_recent < 70:
                        recommendations.append(
                            OptimizationRecommendation(
                                category="cache",
                                priority=AlertSeverity.MEDIUM,
                                description="Low cache hit rate. Review caching strategy.",
                                expected_improvement="30-50% reduction in database load",
                                implementation_complexity="medium",
                                estimated_effort="2-4 hours",
                                related_metrics=[metric_name, "database_response_time"],
                            )
                        )

        except Exception as e:
            logger.error(f"Error generating optimization recommendations: {e}")

        return recommendations

    async def get_analytics_summary(self) -> Dict[str, Any]:
        """Get comprehensive analytics summary"""
        try:
            # Anomaly summary
            recent_anomalies = [
                a
                for a in self.anomalies
                if a.timestamp > datetime.now() - timedelta(hours=24)
            ]
            anomaly_summary = {
                "total_recent": len(recent_anomalies),
                "by_severity": {
                    severity.value: len(
                        [a for a in recent_anomalies if a.severity == severity]
                    )
                    for severity in AlertSeverity
                },
                "by_type": {
                    anomaly_type.value: len(
                        [a for a in recent_anomalies if a.anomaly_type == anomaly_type]
                    )
                    for anomaly_type in AnomalyType
                },
            }

            # Prediction summary
            prediction_summary = {
                "total_predictions": len(self.predictions),
                "average_accuracy": np.mean(
                    [p.model_accuracy for p in self.predictions.values()]
                )
                if self.predictions
                else 0,
                "metrics_predicted": list(self.predictions.keys()),
            }

            # Pattern summary
            pattern_summary = {
                "total_patterns": len(self.patterns),
                "by_type": {
                    pattern_type: len(
                        [p for p in self.patterns if p.pattern_type == pattern_type]
                    )
                    for pattern_type in set(p.pattern_type for p in self.patterns)
                },
                "high_confidence_patterns": len(
                    [p for p in self.patterns if p.confidence > 0.8]
                ),
            }

            # Metrics coverage
            metrics_summary = {
                "tracked_metrics": len(self.metrics_history),
                "metrics_with_predictions": len(self.predictions),
                "metrics_with_patterns": len(
                    set(p.pattern_type for p in self.patterns)
                ),
                "total_data_points": sum(
                    len(history) for history in self.metrics_history.values()
                ),
            }

            return {
                "timestamp": datetime.now().isoformat(),
                "anomaly_summary": anomaly_summary,
                "prediction_summary": prediction_summary,
                "pattern_summary": pattern_summary,
                "metrics_summary": metrics_summary,
                "ml_available": SKLEARN_AVAILABLE,
                "last_analysis": self.last_analysis_time.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating analytics summary: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def health_check(self) -> Dict[str, Any]:
        """Health check for the analytics service"""
        return {
            "status": "healthy",
            "ml_available": SKLEARN_AVAILABLE,
            "tracked_metrics": len(self.metrics_history),
            "anomalies_detected": len(self.anomalies),
            "predictions_available": len(self.predictions),
            "patterns_found": len(self.patterns),
            "last_analysis": self.last_analysis_time.isoformat(),
        }

    async def clear_anomalies(self, older_than_hours: int = 24) -> int:
        """Clear old anomalies"""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        initial_count = len(self.anomalies)
        self.anomalies = [a for a in self.anomalies if a.timestamp > cutoff_time]
        return initial_count - len(self.anomalies)

    async def clear_predictions(self, older_than_hours: int = 48) -> int:
        """Clear old predictions"""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        initial_count = len(self.predictions)
        self.predictions = {
            k: v for k, v in self.predictions.items() if v.timestamp > cutoff_time
        }
        return initial_count - len(self.predictions)


# Initialize function for dependency injection
async def init_advanced_analytics_service(
    history_window: int = 1000, prediction_horizon_hours: int = 24
) -> AdvancedAnalyticsService:
    """Initialize advanced analytics service"""
    service = AdvancedAnalyticsService(history_window, prediction_horizon_hours)
    return service
