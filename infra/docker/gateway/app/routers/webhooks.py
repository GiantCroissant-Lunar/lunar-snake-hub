"""
Webhooks Router
Handles GitHub/GitLab webhook endpoints for real-time indexing
"""

import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse

from ..services.webhook_receiver import WebhookProcessor
from ..services.enhanced_indexing import EnhancedIndexingService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Global services (will be injected by main.py)
webhook_processor: Optional[WebhookProcessor] = None
enhanced_indexing: Optional[EnhancedIndexingService] = None


def init_services(
    webhook_proc: WebhookProcessor, enhanced_idx: EnhancedIndexingService
):
    """Initialize services (called from main.py)"""
    global webhook_processor, enhanced_indexing
    webhook_processor = webhook_proc
    enhanced_indexing = enhanced_idx


@router.post("/github/{repo_name}")
async def github_webhook(
    request: Request,
    repo_name: str,
    x_github_event: str = Header(None, alias="X-GitHub-Event"),
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256"),
    x_github_delivery: str = Header(None, alias="X-GitHub-Delivery"),
):
    """Handle GitHub webhook events"""
    if not webhook_processor:
        raise HTTPException(status_code=503, detail="Webhook service not available")

    try:
        # Read request body
        body = await request.body()
        body_str = body.decode("utf-8")

        # Prepare headers for processing
        headers = {
            "X-GitHub-Event": x_github_event,
            "X-Hub-Signature-256": x_hub_signature_256,
            "X-GitHub-Delivery": x_github_delivery,
            "Content-Type": request.headers.get("content-type", ""),
        }

        logger.info(f"🪝 GitHub webhook: {x_github_event} for {repo_name}")

        # Process webhook
        result = await webhook_processor.process_webhook(headers, body_str)

        # Return appropriate response
        status_code = result.get("status_code", 200)

        return JSONResponse(
            content={
                "success": result.get("success", False),
                "message": result.get("message", ""),
                "event_id": result.get("event_id", ""),
                "provider": "github",
                "repo_name": repo_name,
                "event_type": x_github_event,
            },
            status_code=status_code,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ GitHub webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {e}")


@router.post("/gitlab/{repo_name}")
async def gitlab_webhook(
    request: Request,
    repo_name: str,
    x_gitlab_event: str = Header(None, alias="X-Gitlab-Event"),
    x_gitlab_token: str = Header(None, alias="X-Gitlab-Token"),
    x_gitlab_instance: str = Header(None, alias="X-Gitlab-Instance"),
):
    """Handle GitLab webhook events"""
    if not webhook_processor:
        raise HTTPException(status_code=503, detail="Webhook service not available")

    try:
        # Read request body
        body = await request.body()
        body_str = body.decode("utf-8")

        # Prepare headers for processing
        headers = {
            "X-Gitlab-Event": x_gitlab_event,
            "X-Gitlab-Token": x_gitlab_token,
            "X-Gitlab-Instance": x_gitlab_instance,
            "Content-Type": request.headers.get("content-type", ""),
        }

        logger.info(f"🪝 GitLab webhook: {x_gitlab_event} for {repo_name}")

        # Process webhook
        result = await webhook_processor.process_webhook(headers, body_str)

        # Return appropriate response
        status_code = result.get("status_code", 200)

        return JSONResponse(
            content={
                "success": result.get("success", False),
                "message": result.get("message", ""),
                "event_id": result.get("event_id", ""),
                "provider": "gitlab",
                "repo_name": repo_name,
                "event_type": x_gitlab_event,
            },
            status_code=status_code,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ GitLab webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {e}")


@router.get("/status")
async def webhook_status():
    """Get webhook processing status"""
    try:
        if not webhook_processor:
            return {
                "status": "unavailable",
                "message": "Webhook service not initialized",
            }

        # Get queue status
        queue_status = await webhook_processor.get_queue_status()

        # Get indexing stats
        indexing_stats = (
            await enhanced_indexing.get_indexing_stats() if enhanced_indexing else {}
        )

        return {
            "status": "active",
            "webhook_processor": queue_status,
            "indexing_stats": indexing_stats,
            "supported_events": queue_status.get("supported_events", []),
            "queue_size": queue_status.get("queue_size", 0),
            "is_processing": queue_status.get("is_processing", False),
        }

    except Exception as e:
        logger.error(f"❌ Webhook status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {e}")


@router.get("/jobs")
async def list_indexing_jobs():
    """List all indexing jobs"""
    if not enhanced_indexing:
        raise HTTPException(status_code=503, detail="Indexing service not available")

    try:
        jobs = await enhanced_indexing.list_active_jobs()

        return {"success": True, "jobs": jobs, "total_count": len(jobs)}

    except Exception as e:
        logger.error(f"❌ Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {e}")


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a specific indexing job"""
    if not enhanced_indexing:
        raise HTTPException(status_code=503, detail="Indexing service not available")

    try:
        job = await enhanced_indexing.get_job_status(job_id)

        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return {"success": True, "job": job}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get job status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {e}")


@router.post("/trigger/{repo_name}")
async def trigger_manual_indexing(
    repo_name: str, branch: str = "main", force_reindex: bool = False
):
    """Manually trigger indexing for a repository"""
    if not enhanced_indexing:
        raise HTTPException(status_code=503, detail="Indexing service not available")

    try:
        # Trigger indexing
        result = await enhanced_indexing.index_repository(
            repo_path=f"/repos/{repo_name}",
            collection_name=f"{repo_name}_{branch}",
            force_reindex=force_reindex,
        )

        return {
            "success": result.get("success", False),
            "job_id": result.get("job_id", ""),
            "message": result.get("message", ""),
            "status": result.get("status", "unknown"),
        }

    except Exception as e:
        logger.error(f"❌ Failed to trigger indexing: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger indexing: {e}")


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel an active indexing job (placeholder)"""
    if not enhanced_indexing:
        raise HTTPException(status_code=503, detail="Indexing service not available")

    try:
        # In a real implementation, you'd cancel the job
        # For now, just return a response
        return {
            "success": True,
            "message": f"Job {job_id} cancellation requested",
            "note": "Job cancellation not implemented yet",
        }

    except Exception as e:
        logger.error(f"❌ Failed to cancel job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {e}")


@router.post("/cleanup")
async def cleanup_old_jobs(max_age_hours: int = 24):
    """Clean up old completed/failed jobs"""
    if not enhanced_indexing:
        raise HTTPException(status_code=503, detail="Indexing service not available")

    try:
        await enhanced_indexing.cleanup_old_jobs(max_age_hours)

        return {
            "success": True,
            "message": f"Cleaned up jobs older than {max_age_hours} hours",
        }

    except Exception as e:
        logger.error(f"❌ Failed to cleanup jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup jobs: {e}")


@router.get("/config")
async def get_webhook_config():
    """Get webhook configuration information"""
    try:
        return {
            "supported_providers": {
                "github": {
                    "events": ["push", "pull_request", "release"],
                    "headers": [
                        "X-GitHub-Event",
                        "X-Hub-Signature-256",
                        "X-GitHub-Delivery",
                    ],
                    "signature_format": "sha256",
                    "endpoint": "/webhooks/github/{repo_name}",
                },
                "gitlab": {
                    "events": ["Push Hook", "Merge Request Hook"],
                    "headers": [
                        "X-Gitlab-Event",
                        "X-Gitlab-Token",
                        "X-Gitlab-Instance",
                    ],
                    "signature_format": "sha1",
                    "endpoint": "/webhooks/gitlab/{repo_name}",
                },
            },
            "security": {
                "signature_verification": True,
                "secret_required": True,
                "supported_algorithms": ["sha256", "sha1"],
            },
            "processing": {
                "queue_enabled": True,
                "async_processing": True,
                "retry_attempts": 3,
                "timeout_seconds": 300,
            },
        }

    except Exception as e:
        logger.error(f"❌ Failed to get webhook config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get config: {e}")


@router.post("/test/{provider}")
async def test_webhook(
    provider: str, repo_name: str = "test-repo", event_type: str = "push"
):
    """Test webhook processing with sample data"""
    if not webhook_processor:
        raise HTTPException(status_code=503, detail="Webhook service not available")

    try:
        if provider not in ["github", "gitlab"]:
            raise HTTPException(
                status_code=400, detail=f"Unsupported provider: {provider}"
            )

        # Generate test webhook payload
        if provider == "github":
            test_payload = _generate_github_test_payload(repo_name, event_type)
            test_headers = {
                "X-GitHub-Event": event_type,
                "X-Hub-Signature-256": "test-signature",
                "Content-Type": "application/json",
            }
        else:  # gitlab
            test_payload = _generate_gitlab_test_payload(repo_name, event_type)
            test_headers = {
                "X-Gitlab-Event": event_type,
                "X-Gitlab-Token": "test-token",
                "Content-Type": "application/json",
            }

        # Process test webhook
        result = await webhook_processor.process_webhook(
            test_headers, json.dumps(test_payload)
        )

        return {
            "success": True,
            "provider": provider,
            "event_type": event_type,
            "test_result": result,
            "payload_sample": test_payload,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Webhook test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook test failed: {e}")


def _generate_github_test_payload(repo_name: str, event_type: str) -> Dict[str, Any]:
    """Generate test GitHub webhook payload"""
    if event_type == "push":
        return {
            "ref": "refs/heads/main",
            "repository": {
                "full_name": repo_name,
                "html_url": f"https://github.com/{repo_name}",
            },
            "head_commit": {
                "id": "test-commit-123",
                "message": "Test commit for webhook",
                "author": {"name": "Test User"},
                "timestamp": "2025-01-01T00:00:00Z",
            },
            "commits": [
                {
                    "id": "test-commit-123",
                    "message": "Test commit for webhook",
                    "author": {"name": "Test User"},
                    "added": ["test.py"],
                    "modified": ["README.md"],
                    "removed": [],
                }
            ],
        }
    elif event_type == "pull_request":
        return {
            "action": "opened",
            "repository": {
                "full_name": repo_name,
                "html_url": f"https://github.com/{repo_name}",
            },
            "pull_request": {
                "title": "Test Pull Request",
                "user": {"login": "testuser"},
                "head": {"ref": "feature-branch", "sha": "test-pr-123"},
                "updated_at": "2025-01-01T00:00:00Z",
            },
        }
    else:  # release
        return {
            "action": "published",
            "repository": {
                "full_name": repo_name,
                "html_url": f"https://github.com/{repo_name}",
            },
            "release": {
                "name": "v1.0.0",
                "author": {"login": "testuser"},
                "target_commitish": "main",
                "published_at": "2025-01-01T00:00:00Z",
            },
        }


def _generate_gitlab_test_payload(repo_name: str, event_type: str) -> Dict[str, Any]:
    """Generate test GitLab webhook payload"""
    if event_type == "Push Hook":
        return {
            "ref": "refs/heads/main",
            "project": {
                "path_with_namespace": repo_name,
                "web_url": f"https://gitlab.com/{repo_name}",
            },
            "commits": [
                {
                    "id": "test-commit-123",
                    "message": "Test commit for webhook",
                    "author": {"name": "Test User"},
                    "added": ["test.py"],
                    "modified": ["README.md"],
                    "removed": [],
                    "timestamp": "2025-01-01T00:00:00Z",
                }
            ],
        }
    else:  # Merge Request Hook
        return {
            "object_attributes": {
                "action": "open",
                "title": "Test Merge Request",
                "source_branch": "feature-branch",
                "target_branch": "main",
                "author": {"name": "Test User"},
                "updated_at": "2025-01-01T00:00:00Z",
            },
            "project": {
                "path_with_namespace": repo_name,
                "web_url": f"https://gitlab.com/{repo_name}",
            },
            "object_kind": "merge_request",
        }
