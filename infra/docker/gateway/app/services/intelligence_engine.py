"""
Intelligence Engine Service - Phase 4
Provides ML pipeline management, pattern recognition, and optimization recommendations
"""

import asyncio
import pickle
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
from enum import Enum
import uuid

try:
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, mean_squared_error
    from sklearn.decomposition import PCA

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning(
        "scikit-learn not available. Some intelligence features will be disabled."
    )

logger = logging.getLogger(__name__)


class InsightType(Enum):
    """Types of insights generated"""

    PERFORMANCE_PATTERN = "performance_pattern"
    ANOMALY_CORRELATION = "anomaly_correlation"
    CAPACITY_PREDICTION = "capacity_prediction"
    OPTIMIZATION_OPPORTUNITY = "optimization_opportunity"
    RISK_ASSESSMENT = "risk_assessment"
    BEHAVIORAL_CHANGE = "behavioral_change"


class ModelType(Enum):
    """Types of ML models"""

    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    ANOMALY_DETECTION = "anomaly_detection"
    TIME_SERIES = "time_series"


class InsightPriority(Enum):
    """Priority levels for insights"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MLModel:
    """Machine learning model metadata"""

    model_id: str
    name: str
    model_type: ModelType
    target_variable: str
    features: List[str]
    accuracy: float
    created_at: datetime
    last_trained: datetime
    training_samples: int
    model_data: Optional[bytes] = None
    is_active: bool = True


@dataclass
class Insight:
    """Generated insight from intelligence engine"""

    insight_id: str
    insight_type: InsightType
    priority: InsightPriority
    title: str
    description: str
    confidence: float
    impact_assessment: str
    recommendations: List[str]
    supporting_data: Dict[str, Any]
    generated_at: datetime
    expires_at: Optional[datetime] = None


@dataclass
class KnowledgeEntry:
    """Knowledge base entry"""

    entry_id: str
    category: str
    title: str
    content: str
    tags: List[str]
    confidence: float
    created_at: datetime
    last_validated: datetime
    validation_count: int = 0


class IntelligenceEngineService:
    """Intelligence engine for ML-based optimization and insights"""

    def __init__(self, knowledge_base_path: str = "/app/data/knowledge_base.pkl"):
        self.knowledge_base_path = knowledge_base_path

        # ML models storage
        self.models: Dict[str, MLModel] = {}
        self.model_performance: Dict[str, List[float]] = defaultdict(list)

        # Insights storage
        self.insights: Dict[str, Insight] = {}
        self.insight_history: List[Insight] = []

        # Knowledge base
        self.knowledge_base: Dict[str, KnowledgeEntry] = {}

        # Training data
        self.training_data = defaultdict(list)
        self.feature_history = defaultdict(lambda: deque(maxlen=1000))

        # Configuration
        self.min_training_samples = 100
        self.model_retrain_interval = timedelta(hours=6)
        self.insight_retention_days = 30

        # State
        self.last_model_training = datetime.now()
        self.last_insight_generation = datetime.now()
        self.learning_enabled = True

        # Background tasks
        self._training_task = None
        self._insight_task = None

        # Load existing knowledge base
        self._load_knowledge_base()

        # Start background tasks
        self._start_background_tasks()

        logger.info("Intelligence Engine Service initialized")

    def _load_knowledge_base(self):
        """Load knowledge base from file"""
        try:
            if os.path.exists(self.knowledge_base_path):
                with open(self.knowledge_base_path, "rb") as f:
                    data = pickle.load(f)
                    self.knowledge_base = data.get("knowledge_base", {})
                    self.models = data.get("models", {})
                    logger.info(
                        f"Loaded {len(self.knowledge_base)} knowledge entries and {len(self.models)} models"
                    )
        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}")

    def _save_knowledge_base(self):
        """Save knowledge base to file"""
        try:
            os.makedirs(os.path.dirname(self.knowledge_base_path), exist_ok=True)
            with open(self.knowledge_base_path, "wb") as f:
                data = {"knowledge_base": self.knowledge_base, "models": self.models}
                pickle.dump(data, f)
            logger.debug("Knowledge base saved")
        except Exception as e:
            logger.error(f"Failed to save knowledge base: {e}")

    def _start_background_tasks(self):
        """Start background learning tasks"""
        if self._training_task is None:
            self._training_task = asyncio.create_task(self._training_loop())

        if self._insight_task is None:
            self._insight_task = asyncio.create_task(self._insight_generation_loop())

    async def _training_loop(self):
        """Background model training loop"""
        while True:
            try:
                await asyncio.sleep(3600)  # Check every hour
                if (
                    datetime.now() - self.last_model_training
                    >= self.model_retrain_interval
                ):
                    await self._retrain_models()
                    self.last_model_training = datetime.now()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in training loop: {e}")

    async def _insight_generation_loop(self):
        """Background insight generation loop"""
        while True:
            try:
                await asyncio.sleep(1800)  # Generate insights every 30 minutes
                await self._generate_insights()
                self.last_insight_generation = datetime.now()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in insight generation loop: {e}")

    async def add_training_data(
        self,
        data_type: str,
        features: Dict[str, Any],
        target: Any = None,
        timestamp: datetime = None,
    ) -> None:
        """Add training data for model learning"""
        if timestamp is None:
            timestamp = datetime.now()

        # Store training data
        training_entry = {
            "timestamp": timestamp.isoformat(),
            "features": features,
            "target": target,
        }
        self.training_data[data_type].append(training_entry)

        # Update feature history
        for feature_name, value in features.items():
            if isinstance(value, (int, float)):
                self.feature_history[feature_name].append(
                    {"timestamp": timestamp, "value": value}
                )

        # Trigger model training if enough data
        if (
            len(self.training_data[data_type]) >= self.min_training_samples
            and SKLEARN_AVAILABLE
        ):
            await self._train_model(data_type)

    async def _train_model(self, data_type: str) -> Optional[MLModel]:
        """Train a new model for the given data type"""
        if not SKLEARN_AVAILABLE:
            return None

        try:
            data = self.training_data[data_type]
            if len(data) < self.min_training_samples:
                return None

            # Prepare training data
            df = pd.DataFrame(data)

            # Extract features and target
            feature_dicts = df["features"].tolist()
            targets = df["target"].tolist()

            if not feature_dicts or not any(t is not None for t in targets):
                return None

            # Convert to DataFrame
            features_df = pd.json_normalize(feature_dicts)

            # Handle missing values
            features_df = features_df.fillna(features_df.mean())

            # Determine model type based on target
            valid_targets = [t for t in targets if t is not None]
            if not valid_targets:
                return None

            # Check if classification or regression
            if (
                isinstance(valid_targets[0], (bool, str))
                or len(set(valid_targets)) <= 10
            ):
                model_type = ModelType.CLASSIFICATION
            else:
                model_type = ModelType.REGRESSION

            # Prepare target data
            valid_indices = [i for i, t in enumerate(targets) if t is not None]
            X = features_df.iloc[valid_indices]
            y = np.array([targets[i] for i in valid_indices])

            # Encode categorical targets
            if model_type == ModelType.CLASSIFICATION:
                label_encoder = LabelEncoder()
                y = label_encoder.fit_transform(y)

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # Train model
            if model_type == ModelType.CLASSIFICATION:
                model = RandomForestClassifier(n_estimators=100, random_state=42)
            else:
                model = GradientBoostingRegressor(n_estimators=100, random_state=42)

            model.fit(X_train_scaled, y_train)

            # Evaluate model
            if model_type == ModelType.CLASSIFICATION:
                y_pred = model.predict(X_test_scaled)
                accuracy = accuracy_score(y_test, y_pred)
            else:
                y_pred = model.predict(X_test_scaled)
                accuracy = 1 - (mean_squared_error(y_test, y_pred) / np.var(y_test))
                accuracy = max(0, min(1, accuracy))  # Clamp to [0,1]

            # Create model metadata
            model_id = str(uuid.uuid4())
            model_name = f"{data_type}_{model_type.value}_model"

            ml_model = MLModel(
                model_id=model_id,
                name=model_name,
                model_type=model_type,
                target_variable=data_type,
                features=list(features_df.columns),
                accuracy=accuracy,
                created_at=datetime.now(),
                last_trained=datetime.now(),
                training_samples=len(X_train),
                model_data=pickle.dumps(
                    {
                        "model": model,
                        "scaler": scaler,
                        "label_encoder": label_encoder
                        if model_type == ModelType.CLASSIFICATION
                        else None,
                        "feature_names": list(features_df.columns),
                    }
                ),
            )

            # Store model
            self.models[model_id] = ml_model

            # Update performance tracking
            self.model_performance[data_type].append(accuracy)

            logger.info(
                f"Trained {model_type.value} model for {data_type} with accuracy {accuracy:.3f}"
            )

            return ml_model

        except Exception as e:
            logger.error(f"Error training model for {data_type}: {e}")
            return None

    async def _retrain_models(self) -> Dict[str, int]:
        """Retrain all models with latest data"""
        retrained_count = 0

        for data_type in self.training_data.keys():
            if len(self.training_data[data_type]) >= self.min_training_samples:
                model = await self._train_model(data_type)
                if model:
                    retrained_count += 1

        logger.info(f"Retrained {retrained_count} models")
        self._save_knowledge_base()

        return {"retrained_models": retrained_count}

    async def _generate_insights(self) -> List[Insight]:
        """Generate insights from current data and models"""
        insights = []

        try:
            # Performance pattern insights
            pattern_insights = await self._generate_performance_insights()
            insights.extend(pattern_insights)

            # Anomaly correlation insights
            anomaly_insights = await self._generate_anomaly_insights()
            insights.extend(anomaly_insights)

            # Capacity prediction insights
            capacity_insights = await self._generate_capacity_insights()
            insights.extend(capacity_insights)

            # Optimization opportunity insights
            optimization_insights = await self._generate_optimization_insights()
            insights.extend(optimization_insights)

            # Risk assessment insights
            risk_insights = await self._generate_risk_insights()
            insights.extend(risk_insights)

            # Store insights
            for insight in insights:
                self.insights[insight.insight_id] = insight
                self.insight_history.append(insight)

            # Clean up old insights
            await self._cleanup_old_insights()

            logger.info(f"Generated {len(insights)} new insights")

        except Exception as e:
            logger.error(f"Error generating insights: {e}")

        return insights

    async def _generate_performance_insights(self) -> List[Insight]:
        """Generate performance pattern insights"""
        insights = []

        try:
            # Analyze feature trends
            for feature_name, history in self.feature_history.items():
                if len(history) < 50:
                    continue

                values = [point["value"] for point in list(history)]
                timestamps = [point["timestamp"] for point in list(history)]

                # Detect trends
                if len(values) >= 20:
                    x = np.arange(len(values))
                    trend_slope = np.polyfit(x, values, 1)[0]

                    if abs(trend_slope) > 0.01:  # Significant trend
                        trend_direction = (
                            "increasing" if trend_slope > 0 else "decreasing"
                        )
                        confidence = min(abs(trend_slope) * 100, 1.0)

                        insight = Insight(
                            insight_id=str(uuid.uuid4()),
                            insight_type=InsightType.PERFORMANCE_PATTERN,
                            priority=InsightPriority.MEDIUM
                            if abs(trend_slope) > 0.05
                            else InsightPriority.LOW,
                            title=f"{feature_name} shows {trend_direction} trend",
                            description=f"The metric {feature_name} shows a {trend_direction} trend with slope {trend_slope:.4f}",
                            confidence=confidence,
                            impact_assessment="medium"
                            if abs(trend_slope) > 0.05
                            else "low",
                            recommendations=[
                                f"Monitor {feature_name} closely for continued {trend_direction} trend",
                                "Investigate root cause if trend persists",
                            ],
                            supporting_data={
                                "feature_name": feature_name,
                                "trend_slope": float(trend_slope),
                                "data_points": len(values),
                                "recent_values": values[-10:],
                            },
                            generated_at=datetime.now(),
                        )
                        insights.append(insight)

        except Exception as e:
            logger.error(f"Error generating performance insights: {e}")

        return insights

    async def _generate_anomaly_insights(self) -> List[Insight]:
        """Generate anomaly correlation insights"""
        insights = []

        try:
            # Correlate anomalies across different metrics
            if len(self.feature_history) < 2:
                return insights

            feature_names = list(self.feature_history.keys())
            correlations = []

            for i, feature1 in enumerate(feature_names):
                for j, feature2 in enumerate(feature_names[i + 1 :], i + 1):
                    history1 = list(self.feature_history[feature1])
                    history2 = list(self.feature_history[feature2])

                    if len(history1) >= 30 and len(history2) >= 30:
                        values1 = [point["value"] for point in history1[-30:]]
                        values2 = [point["value"] for point in history2[-30:]]

                        correlation = np.corrcoef(values1, values2)[0, 1]
                        if not np.isnan(correlation) and abs(correlation) > 0.7:
                            correlations.append((feature1, feature2, correlation))

            # Generate insights for strong correlations
            for feature1, feature2, correlation in correlations:
                insight = Insight(
                    insight_id=str(uuid.uuid4()),
                    insight_type=InsightType.ANOMALY_CORRELATION,
                    priority=InsightPriority.MEDIUM,
                    title=f"Strong correlation between {feature1} and {feature2}",
                    description=f"Detected strong correlation ({correlation:.3f}) between {feature1} and {feature2}",
                    confidence=abs(correlation),
                    impact_assessment="medium",
                    recommendations=[
                        f"Investigate causal relationship between {feature1} and {feature2}",
                        "Consider joint optimization strategies",
                    ],
                    supporting_data={
                        "feature1": feature1,
                        "feature2": feature2,
                        "correlation": float(correlation),
                    },
                    generated_at=datetime.now(),
                )
                insights.append(insight)

        except Exception as e:
            logger.error(f"Error generating anomaly insights: {e}")

        return insights

    async def _generate_capacity_insights(self) -> List[Insight]:
        """Generate capacity prediction insights"""
        insights = []

        try:
            # Use trained models to predict future capacity needs
            for model_id, model in self.models.items():
                if (
                    model.model_type == ModelType.REGRESSION
                    and model.target_variable.startswith("capacity")
                ):
                    # Get recent feature data
                    recent_features = {}
                    for feature in model.features:
                        if (
                            feature in self.feature_history
                            and len(self.feature_history[feature]) > 0
                        ):
                            recent_values = [
                                point["value"]
                                for point in list(self.feature_history[feature])[-5:]
                            ]
                            recent_features[feature] = np.mean(recent_values)

                    if recent_features:
                        prediction = await self._predict_with_model(
                            model_id, recent_features
                        )
                        if prediction:
                            insight = Insight(
                                insight_id=str(uuid.uuid4()),
                                insight_type=InsightType.CAPACITY_PREDICTION,
                                priority=InsightPriority.HIGH
                                if prediction > 0.8
                                else InsightPriority.MEDIUM,
                                title=f"Capacity prediction for {model.target_variable}",
                                description=f"Predicted {model.target_variable}: {prediction:.2f}",
                                confidence=model.accuracy,
                                impact_assessment="high"
                                if prediction > 0.8
                                else "medium",
                                recommendations=[
                                    "Plan capacity expansion if prediction > 0.8",
                                    "Monitor resource utilization closely",
                                ],
                                supporting_data={
                                    "model_id": model_id,
                                    "prediction": float(prediction),
                                    "model_accuracy": model.accuracy,
                                },
                                generated_at=datetime.now(),
                            )
                            insights.append(insight)

        except Exception as e:
            logger.error(f"Error generating capacity insights: {e}")

        return insights

    async def _generate_optimization_insights(self) -> List[Insight]:
        """Generate optimization opportunity insights"""
        insights = []

        try:
            # Analyze model performance to identify optimization opportunities
            for data_type, accuracies in self.model_performance.items():
                if len(accuracies) >= 5:
                    recent_accuracy = np.mean(accuracies[-5:])
                    historical_accuracy = (
                        np.mean(accuracies[:-5])
                        if len(accuracies) > 5
                        else recent_accuracy
                    )

                    if recent_accuracy < historical_accuracy * 0.9:  # 10% drop
                        insight = Insight(
                            insight_id=str(uuid.uuid4()),
                            insight_type=InsightType.OPTIMIZATION_OPPORTUNITY,
                            priority=InsightPriority.MEDIUM,
                            title=f"Model performance degradation for {data_type}",
                            description=f"Model accuracy for {data_type} has dropped from {historical_accuracy:.3f} to {recent_accuracy:.3f}",
                            confidence=0.8,
                            impact_assessment="medium",
                            recommendations=[
                                f"Retrain {data_type} model with fresh data",
                                "Review feature engineering for {data_type}",
                                "Check for data quality issues",
                            ],
                            supporting_data={
                                "data_type": data_type,
                                "recent_accuracy": float(recent_accuracy),
                                "historical_accuracy": float(historical_accuracy),
                                "performance_drop": float(
                                    historical_accuracy - recent_accuracy
                                ),
                            },
                            generated_at=datetime.now(),
                        )
                        insights.append(insight)

        except Exception as e:
            logger.error(f"Error generating optimization insights: {e}")

        return insights

    async def _generate_risk_insights(self) -> List[Insight]:
        """Generate risk assessment insights"""
        insights = []

        try:
            # Analyze system stability and risk factors
            risk_factors = []

            # Check for high error rates in recent data
            for data_type, data in self.training_data.items():
                recent_data = [d for d in data[-50:] if d.get("target") is not None]
                if recent_data:
                    error_rate = sum(
                        1
                        for d in recent_data
                        if d["target"] in [False, "error", "failed"]
                    ) / len(recent_data)
                    if error_rate > 0.1:  # 10% error rate
                        risk_factors.append((data_type, error_rate, "high_error_rate"))

            # Check for data quality issues
            for feature_name, history in self.feature_history.items():
                if len(history) >= 100:
                    values = [point["value"] for point in list(history)]
                    if len(set(values)) == 1:  # No variation
                        risk_factors.append((feature_name, 1.0, "no_variation"))

            # Generate risk insights
            for risk_source, risk_score, risk_type in risk_factors:
                priority = (
                    InsightPriority.CRITICAL
                    if risk_score > 0.5
                    else InsightPriority.HIGH
                )

                insight = Insight(
                    insight_id=str(uuid.uuid4()),
                    insight_type=InsightType.RISK_ASSESSMENT,
                    priority=priority,
                    title=f"Risk detected: {risk_type} in {risk_source}",
                    description=f"Risk factor {risk_type} detected with score {risk_score:.3f}",
                    confidence=risk_score,
                    impact_assessment="high",
                    recommendations=[
                        f"Investigate {risk_type} in {risk_source} immediately",
                        "Implement mitigation strategies",
                        "Monitor closely for escalation",
                    ],
                    supporting_data={
                        "risk_source": risk_source,
                        "risk_type": risk_type,
                        "risk_score": float(risk_score),
                    },
                    generated_at=datetime.now(),
                )
                insights.append(insight)

        except Exception as e:
            logger.error(f"Error generating risk insights: {e}")

        return insights

    async def _predict_with_model(
        self, model_id: str, features: Dict[str, Any]
    ) -> Optional[float]:
        """Make prediction using a trained model"""
        if not SKLEARN_AVAILABLE or model_id not in self.models:
            return None

        try:
            model = self.models[model_id]
            if not model.model_data:
                return None

            # Load model
            model_data = pickle.loads(model.model_data)
            trained_model = model_data["model"]
            scaler = model_data["scaler"]
            label_encoder = model_data.get("label_encoder")
            feature_names = model_data["feature_names"]

            # Prepare features
            feature_vector = []
            for feature_name in feature_names:
                feature_vector.append(features.get(feature_name, 0))

            # Scale features
            feature_vector_scaled = scaler.transform([feature_vector])

            # Make prediction
            prediction = trained_model.predict(feature_vector_scaled)[0]

            # Inverse transform if classification
            if label_encoder:
                prediction = label_encoder.inverse_transform([prediction])[0]

            return (
                float(prediction)
                if isinstance(prediction, (int, float))
                else prediction
            )

        except Exception as e:
            logger.error(f"Error making prediction with model {model_id}: {e}")
            return None

    async def _cleanup_old_insights(self) -> int:
        """Clean up old insights"""
        cutoff_time = datetime.now() - timedelta(days=self.insight_retention_days)
        initial_count = len(self.insights)

        # Remove old insights
        old_insight_ids = [
            insight_id
            for insight_id, insight in self.insights.items()
            if insight.generated_at < cutoff_time
        ]

        for insight_id in old_insight_ids:
            del self.insights[insight_id]

        # Also clean up history
        self.insight_history = [
            insight
            for insight in self.insight_history
            if insight.generated_at >= cutoff_time
        ]

        cleaned_count = initial_count - len(self.insights)
        if cleaned_count > 0:
            logger.debug(f"Cleaned up {cleaned_count} old insights")

        return cleaned_count

    async def get_insights(
        self,
        insight_type: InsightType = None,
        priority: InsightPriority = None,
        limit: int = 100,
    ) -> List[Insight]:
        """Get insights with filtering"""
        insights = list(self.insights.values())

        # Apply filters
        if insight_type:
            insights = [i for i in insights if i.insight_type == insight_type]

        if priority:
            insights = [i for i in insights if i.priority == priority]

        # Sort by priority and generation time
        priority_order = {
            InsightPriority.CRITICAL: 0,
            InsightPriority.HIGH: 1,
            InsightPriority.MEDIUM: 2,
            InsightPriority.LOW: 3,
        }
        insights.sort(
            key=lambda x: (priority_order.get(x.priority, 4), x.generated_at),
            reverse=True,
        )

        return insights[:limit]

    async def get_models(
        self, model_type: ModelType = None, target_variable: str = None
    ) -> List[MLModel]:
        """Get trained models with filtering"""
        models = list(self.models.values())

        # Apply filters
        if model_type:
            models = [m for m in models if m.model_type == model_type]

        if target_variable:
            models = [m for m in models if m.target_variable == target_variable]

        # Sort by accuracy and last trained time
        models.sort(key=lambda x: (x.accuracy, x.last_trained), reverse=True)
        return models

    async def add_knowledge_entry(
        self,
        category: str,
        title: str,
        content: str,
        tags: List[str],
        confidence: float = 0.8,
    ) -> str:
        """Add entry to knowledge base"""
        entry = KnowledgeEntry(
            entry_id=str(uuid.uuid4()),
            category=category,
            title=title,
            content=content,
            tags=tags,
            confidence=confidence,
            created_at=datetime.now(),
            last_validated=datetime.now(),
        )

        self.knowledge_base[entry.entry_id] = entry
        self._save_knowledge_base()

        logger.info(f"Added knowledge entry: {title}")
        return entry.entry_id

    async def search_knowledge(
        self, query: str, category: str = None, tags: List[str] = None, limit: int = 20
    ) -> List[KnowledgeEntry]:
        """Search knowledge base"""
        entries = list(self.knowledge_base.values())

        # Apply filters
        if category:
            entries = [e for e in entries if e.category == category]

        if tags:
            entries = [e for e in entries if any(tag in e.tags for tag in tags)]

        # Simple text search
        if query:
            query_lower = query.lower()
            entries = [
                e
                for e in entries
                if query_lower in e.title.lower() or query_lower in e.content.lower()
            ]

        # Sort by confidence and creation time
        entries.sort(key=lambda x: (x.confidence, x.created_at), reverse=True)

        return entries[:limit]

    async def get_intelligence_summary(self) -> Dict[str, Any]:
        """Get comprehensive intelligence summary"""
        try:
            # Model summary
            model_summary = {
                "total_models": len(self.models),
                "by_type": {
                    model_type.value: len(
                        [m for m in self.models.values() if m.model_type == model_type]
                    )
                    for model_type in ModelType
                },
                "average_accuracy": np.mean([m.accuracy for m in self.models.values()])
                if self.models
                else 0,
                "active_models": len([m for m in self.models.values() if m.is_active]),
            }

            # Insight summary
            insight_summary = {
                "total_insights": len(self.insights),
                "by_type": {
                    insight_type.value: len(
                        [
                            i
                            for i in self.insights.values()
                            if i.insight_type == insight_type
                        ]
                    )
                    for insight_type in InsightType
                },
                "by_priority": {
                    priority.value: len(
                        [i for i in self.insights.values() if i.priority == priority]
                    )
                    for priority in InsightPriority
                },
                "recent_insights": len(
                    [
                        i
                        for i in self.insights.values()
                        if i.generated_at > datetime.now() - timedelta(hours=24)
                    ]
                ),
            }

            # Knowledge base summary
            knowledge_summary = {
                "total_entries": len(self.knowledge_base),
                "by_category": {
                    category: len(
                        [
                            e
                            for e in self.knowledge_base.values()
                            if e.category == category
                        ]
                    )
                    for category in set(
                        e.category for e in self.knowledge_base.values()
                    )
                },
                "average_confidence": np.mean(
                    [e.confidence for e in self.knowledge_base.values()]
                )
                if self.knowledge_base
                else 0,
            }

            # Learning summary
            learning_summary = {
                "training_data_types": list(self.training_data.keys()),
                "total_training_samples": sum(
                    len(data) for data in self.training_data.values()
                ),
                "features_tracked": len(self.feature_history),
                "last_model_training": self.last_model_training.isoformat(),
                "last_insight_generation": self.last_insight_generation.isoformat(),
                "learning_enabled": self.learning_enabled,
            }

            return {
                "timestamp": datetime.now().isoformat(),
                "model_summary": model_summary,
                "insight_summary": insight_summary,
                "knowledge_summary": knowledge_summary,
                "learning_summary": learning_summary,
                "sklearn_available": SKLEARN_AVAILABLE,
            }

        except Exception as e:
            logger.error(f"Error generating intelligence summary: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def health_check(self) -> Dict[str, Any]:
        """Health check for intelligence engine"""
        return {
            "status": "healthy",
            "sklearn_available": SKLEARN_AVAILABLE,
            "models_loaded": len(self.models),
            "insights_available": len(self.insights),
            "knowledge_entries": len(self.knowledge_base),
            "learning_enabled": self.learning_enabled,
            "last_training": self.last_model_training.isoformat(),
            "last_insight_generation": self.last_insight_generation.isoformat(),
        }


# Initialize function for dependency injection
async def init_intelligence_engine_service(
    knowledge_base_path: str = "/app/data/knowledge_base.pkl",
) -> IntelligenceEngineService:
    """Initialize intelligence engine service"""
    service = IntelligenceEngineService(knowledge_base_path)
    return service
