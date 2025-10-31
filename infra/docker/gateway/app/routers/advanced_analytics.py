"""
Advanced Analytics Router - Phase 4
Provides API endpoints for advanced analytics, ML insights, and optimization recommendations
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from pydantic import BaseModel, Field

from app.services.advanced_analytics import AdvancedAnalyticsService, AlertSeverity
from app.services.intelligence_engine import (
    IntelligenceEngineService,
    InsightType,
    InsightPriority,
)
from app.services.distributed_tracing import DistributedTracingService

logger = logging.getLogger(__name__)


# Pydantic models for request/response
class AnomalyFilter(BaseModel):
    metric_name: Optional[str] = None
    severity: Optional[AlertSeverity] = None
    since: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)


class PredictionFilter(BaseModel):
    metric_name: Optional[str] = None


class InsightFilter(BaseModel):
    insight_type: Optional[InsightType] = None
    priority: Optional[InsightPriority] = None
    limit: int = Field(default=100, ge=1, le=1000)


class KnowledgeFilter(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = Field(default=20, ge=1, le=200)


class TrainingDataRequest(BaseModel):
    data_type: str = Field(..., description="Type of training data")
    features: Dict[str, Any] = Field(..., description="Feature data for training")
    target: Optional[Any] = Field(
        None, description="Target variable for supervised learning"
    )


class KnowledgeEntryRequest(BaseModel):
    category: str = Field(..., description="Knowledge entry category")
    title: str = Field(..., description="Knowledge entry title")
    content: str = Field(..., description="Knowledge entry content")
    tags: List[str] = Field(default=[], description="Tags for the knowledge entry")
    confidence: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Confidence level"
    )


class ModelRequest(BaseModel):
    model_type: Optional[str] = None
    target_variable: Optional[str] = None


# Initialize router
router = APIRouter(prefix="/advanced-analytics", tags=["advanced-analytics"])

# Service instances (will be injected via dependency injection)
analytics_service: AdvancedAnalyticsService = None
intelligence_service: IntelligenceEngineService = None
tracing_service: DistributedTracingService = None


def init_services(
    analytics: AdvancedAnalyticsService,
    intelligence: IntelligenceEngineService,
    tracing: DistributedTracingService,
):
    """Initialize services via dependency injection"""
    global analytics_service, intelligence_service, tracing_service
    analytics_service = analytics
    intelligence_service = intelligence
    tracing_service = tracing


# Anomaly Detection Endpoints
@router.get("/anomalies", summary="Get detected anomalies")
async def get_anomalies(
    metric_name: Optional[str] = Query(None),
    severity: Optional[AlertSeverity] = Query(None),
    since: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
) -> Dict[str, Any]:
    """Get detected anomalies with optional filtering"""
    try:
        anomalies = await analytics_service.get_anomalies(
            metric_name=metric_name, severity=severity, since=since, limit=limit
        )

        return {
            "anomalies": [
                {
                    "metric_name": a.metric_name,
                    "anomaly_type": a.anomaly_type.value,
                    "severity": a.severity.value,
                    "timestamp": a.timestamp.isoformat(),
                    "value": a.value,
                    "expected_value": a.expected_value,
                    "confidence": a.confidence,
                    "description": a.description,
                    "metadata": a.metadata,
                }
                for a in anomalies
            ],
            "total_count": len(anomalies),
            "filters_applied": {
                "metric_name": metric_name,
                "severity": severity.value if severity else None,
                "since": since.isoformat() if since else None,
                "limit": limit,
            },
        }
    except Exception as e:
        logger.error(f"Error getting anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/anomalies/clear", summary="Clear old anomalies")
async def clear_anomalies(
    older_than_hours: int = Query(
        24, ge=1, le=168, description="Clear anomalies older than N hours"
    ),
) -> Dict[str, Any]:
    """Clear old anomalies from the system"""
    try:
        cleared_count = await analytics_service.clear_anomalies(older_than_hours)

        return {
            "message": f"Cleared {cleared_count} old anomalies",
            "cleared_count": cleared_count,
            "older_than_hours": older_than_hours,
        }
    except Exception as e:
        logger.error(f"Error clearing anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Performance Prediction Endpoints
@router.get("/predictions", summary="Get performance predictions")
async def get_predictions(metric_name: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Get performance predictions"""
    try:
        predictions = await analytics_service.get_predictions(metric_name=metric_name)

        return {
            "predictions": {
                metric_name: {
                    "predicted_value": p.predicted_value,
                    "confidence_interval": p.confidence_interval,
                    "prediction_horizon": str(p.prediction_horizon),
                    "model_accuracy": p.model_accuracy,
                    "timestamp": p.timestamp.isoformat(),
                    "factors": p.factors,
                }
                for metric_name, p in predictions.items()
            },
            "total_count": len(predictions),
            "filters_applied": {"metric_name": metric_name},
        }
    except Exception as e:
        logger.error(f"Error getting predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Pattern Analysis Endpoints
@router.get("/patterns", summary="Get detected patterns")
async def get_patterns(
    pattern_type: Optional[str] = Query(None),
    confidence_threshold: float = Query(0.5, ge=0.0, le=1.0),
    limit: int = Query(100, ge=1, le=1000),
) -> Dict[str, Any]:
    """Get detected patterns"""
    try:
        patterns = await analytics_service.get_patterns(
            pattern_type=pattern_type, confidence_threshold=confidence_threshold
        )

        return {
            "patterns": [
                {
                    "pattern_type": p.pattern_type,
                    "description": p.description,
                    "confidence": p.confidence,
                    "time_period": p.time_period,
                    "impact_assessment": p.impact_assessment,
                    "recommendations": p.recommendations,
                }
                for p in patterns
            ],
            "total_count": len(patterns),
            "filters_applied": {
                "pattern_type": pattern_type,
                "confidence_threshold": confidence_threshold,
                "limit": limit,
            },
        }
    except Exception as e:
        logger.error(f"Error getting patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Optimization Recommendations Endpoints
@router.get("/recommendations", summary="Get optimization recommendations")
async def get_recommendations() -> Dict[str, Any]:
    """Get optimization recommendations"""
    try:
        recommendations = (
            await analytics_service.generate_optimization_recommendations()
        )

        return {
            "recommendations": [
                {
                    "category": r.category,
                    "priority": r.priority.value,
                    "description": r.description,
                    "expected_improvement": r.expected_improvement,
                    "implementation_complexity": r.implementation_complexity,
                    "estimated_effort": r.estimated_effort,
                    "related_metrics": r.related_metrics,
                }
                for r in recommendations
            ],
            "total_count": len(recommendations),
        }
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Analytics Summary Endpoints
@router.get("/summary", summary="Get analytics summary")
async def get_analytics_summary() -> Dict[str, Any]:
    """Get comprehensive analytics summary"""
    try:
        summary = await analytics_service.get_analytics_summary()
        return summary
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Intelligence Engine Endpoints
@router.post("/training-data", summary="Add training data")
async def add_training_data(request: TrainingDataRequest) -> Dict[str, Any]:
    """Add training data for ML models"""
    try:
        await intelligence_service.add_training_data(
            data_type=request.data_type,
            features=request.features,
            target=request.target,
        )

        return {
            "message": "Training data added successfully",
            "data_type": request.data_type,
            "feature_count": len(request.features),
        }
    except Exception as e:
        logger.error(f"Error adding training data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", summary="Get trained models")
async def get_models(
    model_type: Optional[str] = Query(None),
    target_variable: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
) -> Dict[str, Any]:
    """Get trained ML models"""
    try:
        models = await intelligence_service.get_models(
            model_type=model_type, target_variable=target_variable
        )

        return {
            "models": [
                {
                    "model_id": m.model_id,
                    "name": m.name,
                    "model_type": m.model_type.value,
                    "target_variable": m.target_variable,
                    "features": m.features,
                    "accuracy": m.accuracy,
                    "created_at": m.created_at.isoformat(),
                    "last_trained": m.last_trained.isoformat(),
                    "training_samples": m.training_samples,
                    "is_active": m.is_active,
                }
                for m in models[:limit]
            ],
            "total_count": len(models),
            "filters_applied": {
                "model_type": model_type,
                "target_variable": target_variable,
                "limit": limit,
            },
        }
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge", summary="Add knowledge entry")
async def add_knowledge_entry(request: KnowledgeEntryRequest) -> Dict[str, Any]:
    """Add entry to knowledge base"""
    try:
        entry_id = await intelligence_service.add_knowledge_entry(
            category=request.category,
            title=request.title,
            content=request.content,
            tags=request.tags,
            confidence=request.confidence,
        )

        return {
            "message": "Knowledge entry added successfully",
            "entry_id": entry_id,
            "category": request.category,
            "title": request.title,
        }
    except Exception as e:
        logger.error(f"Error adding knowledge entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge", summary="Search knowledge base")
async def search_knowledge(
    query: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),  # Comma-separated tags
    limit: int = Query(20, ge=1, le=200),
) -> Dict[str, Any]:
    """Search knowledge base"""
    try:
        tag_list = tags.split(",") if tags else None
        entries = await intelligence_service.search_knowledge(
            query=query, category=category, tags=tag_list, limit=limit
        )

        return {
            "entries": [
                {
                    "entry_id": e.entry_id,
                    "category": e.category,
                    "title": e.title,
                    "content": e.content,
                    "tags": e.tags,
                    "confidence": e.confidence,
                    "created_at": e.created_at.isoformat(),
                    "last_validated": e.last_validated.isoformat(),
                    "validation_count": e.validation_count,
                }
                for e in entries
            ],
            "total_count": len(entries),
            "filters_applied": {
                "query": query,
                "category": category,
                "tags": tag_list,
                "limit": limit,
            },
        }
    except Exception as e:
        logger.error(f"Error searching knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights", summary="Get AI insights")
async def get_insights(
    insight_type: Optional[InsightType] = Query(None),
    priority: Optional[InsightPriority] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
) -> Dict[str, Any]:
    """Get AI-generated insights"""
    try:
        insights = await intelligence_service.get_insights(
            insight_type=insight_type, priority=priority, limit=limit
        )

        return {
            "insights": [
                {
                    "insight_id": i.insight_id,
                    "insight_type": i.insight_type.value,
                    "priority": i.priority.value,
                    "title": i.title,
                    "description": i.description,
                    "confidence": i.confidence,
                    "impact_assessment": i.impact_assessment,
                    "recommendations": i.recommendations,
                    "supporting_data": i.supporting_data,
                    "generated_at": i.generated_at.isoformat(),
                    "expires_at": i.expires_at.isoformat() if i.expires_at else None,
                }
                for i in insights
            ],
            "total_count": len(insights),
            "filters_applied": {
                "insight_type": insight_type.value if insight_type else None,
                "priority": priority.value if priority else None,
                "limit": limit,
            },
        }
    except Exception as e:
        logger.error(f"Error getting insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intelligence/summary", summary="Get intelligence engine summary")
async def get_intelligence_summary() -> Dict[str, Any]:
    """Get comprehensive intelligence engine summary"""
    try:
        summary = await intelligence_service.get_intelligence_summary()
        return summary
    except Exception as e:
        logger.error(f"Error getting intelligence summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Combined Analytics Endpoints
@router.get("/dashboard", summary="Get comprehensive analytics dashboard data")
async def get_analytics_dashboard() -> Dict[str, Any]:
    """Get comprehensive dashboard data combining all analytics"""
    try:
        # Get data from all services
        analytics_summary = await analytics_service.get_analytics_summary()
        intelligence_summary = await intelligence_service.get_intelligence_summary()

        # Get recent anomalies and insights
        recent_anomalies = await analytics_service.get_anomalies(limit=10)
        recent_insights = await intelligence_service.get_insights(limit=5)
        recommendations = (
            await analytics_service.generate_optimization_recommendations()
        )

        return {
            "timestamp": datetime.now().isoformat(),
            "analytics_summary": analytics_summary,
            "intelligence_summary": intelligence_summary,
            "recent_anomalies": [
                {
                    "metric_name": a.metric_name,
                    "anomaly_type": a.anomaly_type.value,
                    "severity": a.severity.value,
                    "description": a.description,
                    "timestamp": a.timestamp.isoformat(),
                    "confidence": a.confidence,
                }
                for a in recent_anomalies
            ],
            "critical_insights": [
                {
                    "insight_id": i.insight_id,
                    "title": i.title,
                    "description": i.description,
                    "priority": i.priority.value,
                    "confidence": i.confidence,
                    "generated_at": i.generated_at.isoformat(),
                }
                for i in recent_insights
                if i.priority in [InsightPriority.HIGH, InsightPriority.CRITICAL]
            ],
            "top_recommendations": [
                {
                    "category": r.category,
                    "priority": r.priority.value,
                    "description": r.description,
                    "expected_improvement": r.expected_improvement,
                    "implementation_complexity": r.implementation_complexity,
                }
                for r in recommendations[:5]  # Top 5 recommendations
            ],
            "health_status": {
                "analytics_healthy": analytics_summary.get("error") is None,
                "intelligence_healthy": intelligence_summary.get("error") is None,
                "total_anomalies": analytics_summary.get("anomaly_summary", {}).get(
                    "total_recent", 0
                ),
                "active_insights": intelligence_summary.get("insight_summary", {}).get(
                    "total_insights", 0
                ),
            },
        }
    except Exception as e:
        logger.error(f"Error getting analytics dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health Check Endpoint
@router.get("/health", summary="Health check for advanced analytics")
async def health_check() -> Dict[str, Any]:
    """Health check for advanced analytics services"""
    try:
        analytics_health = await analytics_service.health_check()
        intelligence_health = await intelligence_service.health_check()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "analytics": analytics_health,
                "intelligence": intelligence_health,
            },
            "overall_health": (
                analytics_health.get("status") == "healthy"
                and intelligence_health.get("status") == "healthy"
            ),
        }
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }


# Configuration Endpoints
@router.get("/config", summary="Get analytics configuration")
async def get_analytics_config() -> Dict[str, Any]:
    """Get current analytics configuration"""
    try:
        return {
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "analytics_service": {
                    "ml_available": analytics_service.SKLEARN_AVAILABLE
                    if hasattr(analytics_service, "SKLEARN_AVAILABLE")
                    else False,
                    "history_window": analytics_service.history_window,
                    "prediction_horizon_hours": analytics_service.prediction_horizon.total_seconds()
                    / 3600,
                    "min_data_points": analytics_service.min_data_points,
                    "analysis_interval_minutes": analytics_service.analysis_interval.total_seconds()
                    / 60,
                }
                if analytics_service
                else None,
                "intelligence_service": {
                    "ml_available": intelligence_service.SKLEARN_AVAILABLE
                    if hasattr(intelligence_service, "SKLEARN_AVAILABLE")
                    else False,
                    "min_training_samples": intelligence_service.min_training_samples,
                    "model_retrain_interval_hours": intelligence_service.model_retrain_interval.total_seconds()
                    / 3600,
                    "insight_retention_days": intelligence_service.insight_retention_days,
                    "learning_enabled": intelligence_service.learning_enabled,
                }
                if intelligence_service
                else None,
            },
        }
    except Exception as e:
        logger.error(f"Error getting analytics config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
