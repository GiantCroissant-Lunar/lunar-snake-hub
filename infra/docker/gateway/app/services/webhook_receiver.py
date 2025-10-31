"""
Webhook Receiver Service
Handles GitHub/GitLab webhooks for real-time repository updates
"""

import asyncio
import hashlib
import hmac
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WebhookEvent:
    """Webhook event data"""

    event_type: str
    repo_name: str
    repo_url: str
    branch: str
    commit_hash: str
    commit_message: str
    author: str
    timestamp: str
    changed_files: List[str]
    added_files: List[str]
    modified_files: List[str]
    deleted_files: List[str]


class WebhookReceiver:
    """Handles incoming webhooks from Git providers"""

    def __init__(self, secret_token: str):
        self.secret_token = secret_token
        self.supported_events = ["push", "pull_request", "merge_request", "release"]

    def verify_signature(
        self, payload: str, signature: str, secret: str = None
    ) -> bool:
        """Verify webhook signature for security"""
        try:
            secret = secret or self.secret_token
            if not secret:
                logger.warning("⚠️ No webhook secret configured")
                return False

            # Handle different signature formats
            if signature.startswith("sha256="):
                # GitHub format
                expected_sig = (
                    "sha256="
                    + hmac.new(
                        secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
                    ).hexdigest()
                )
                return hmac.compare_digest(expected_sig, signature)
            elif signature.startswith("sha1="):
                # GitLab format
                expected_sig = (
                    "sha1="
                    + hmac.new(
                        secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha1
                    ).hexdigest()
                )
                return hmac.compare_digest(expected_sig, signature)
            else:
                logger.warning(f"⚠️ Unknown signature format: {signature[:20]}...")
                return False

        except Exception as e:
            logger.error(f"❌ Signature verification failed: {e}")
            return False

    def parse_github_webhook(
        self, headers: Dict[str, str], body: str
    ) -> Optional[WebhookEvent]:
        """Parse GitHub webhook payload"""
        try:
            event_type = headers.get("X-GitHub-Event", "")
            if event_type not in self.supported_events:
                logger.info(f"⏭️ Unsupported GitHub event: {event_type}")
                return None

            payload = json.loads(body)

            if event_type == "push":
                return self._parse_github_push(payload)
            elif event_type == "pull_request":
                return self._parse_github_pull_request(payload)
            elif event_type == "release":
                return self._parse_github_release(payload)

            return None

        except Exception as e:
            logger.error(f"❌ GitHub webhook parsing failed: {e}")
            return None

    def parse_gitlab_webhook(
        self, headers: Dict[str, str], body: str
    ) -> Optional[WebhookEvent]:
        """Parse GitLab webhook payload"""
        try:
            event_type = headers.get("X-Gitlab-Event", "")
            if event_type not in self.supported_events:
                logger.info(f"⏭️ Unsupported GitLab event: {event_type}")
                return None

            payload = json.loads(body)

            if event_type == "Push Hook":
                return self._parse_gitlab_push(payload)
            elif event_type == "Merge Request Hook":
                return self._parse_gitlab_merge_request(payload)

            return None

        except Exception as e:
            logger.error(f"❌ GitLab webhook parsing failed: {e}")
            return None

    def _parse_github_push(self, payload: Dict[str, Any]) -> WebhookEvent:
        """Parse GitHub push event"""
        repo = payload.get("repository", {})
        head_commit = payload.get("head_commit", {})
        commits = payload.get("commits", [])

        # Collect all changed files from commits
        all_changed_files = set()
        all_added_files = set()
        all_modified_files = set()
        all_deleted_files = set()

        for commit in commits:
            if commit.get("added"):
                all_added_files.update(commit["added"])
            if commit.get("modified"):
                all_modified_files.update(commit["modified"])
            if commit.get("removed"):
                all_deleted_files.update(commit["removed"])

            all_changed_files.update(
                commit.get("added", [])
                + commit.get("modified", [])
                + commit.get("removed", [])
            )

        return WebhookEvent(
            event_type="push",
            repo_name=repo.get("full_name", ""),
            repo_url=repo.get("html_url", ""),
            branch=payload.get("ref", "").replace("refs/heads/", ""),
            commit_hash=head_commit.get("id", ""),
            commit_message=head_commit.get("message", ""),
            author=head_commit.get("author", {}).get("name", ""),
            timestamp=head_commit.get("timestamp", ""),
            changed_files=list(all_changed_files),
            added_files=list(all_added_files),
            modified_files=list(all_modified_files),
            deleted_files=list(all_deleted_files),
        )

    def _parse_github_pull_request(self, payload: Dict[str, Any]) -> WebhookEvent:
        """Parse GitHub pull request event"""
        repo = payload.get("repository", {})
        pr = payload.get("pull_request", {})
        head = pr.get("head", {})

        return WebhookEvent(
            event_type="pull_request",
            repo_name=repo.get("full_name", ""),
            repo_url=repo.get("html_url", ""),
            branch=head.get("ref", ""),
            commit_hash=head.get("sha", ""),
            commit_message=pr.get("title", ""),
            author=pr.get("user", {}).get("login", ""),
            timestamp=pr.get("updated_at", ""),
            changed_files=[],  # Would need to fetch PR diff
            added_files=[],
            modified_files=[],
            deleted_files=[],
        )

    def _parse_github_release(self, payload: Dict[str, Any]) -> WebhookEvent:
        """Parse GitHub release event"""
        repo = payload.get("repository", {})
        release = payload.get("release", "")

        return WebhookEvent(
            event_type="release",
            repo_name=repo.get("full_name", ""),
            repo_url=repo.get("html_url", ""),
            branch=release.get("target_commitish", ""),
            commit_hash=release.get("target_commitish", ""),
            commit_message=release.get("name", ""),
            author=release.get("author", {}).get("login", ""),
            timestamp=release.get("published_at", ""),
            changed_files=[],  # Release events don't include file changes
            added_files=[],
            modified_files=[],
            deleted_files=[],
        )

    def _parse_gitlab_push(self, payload: Dict[str, Any]) -> WebhookEvent:
        """Parse GitLab push event"""
        project = payload.get("project", {})
        commits = payload.get("commits", [])

        # Collect changed files
        all_changed_files = set()
        all_added_files = set()
        all_modified_files = set()
        all_deleted_files = set()

        for commit in commits:
            if commit.get("added"):
                all_added_files.update(commit["added"])
            if commit.get("modified"):
                all_modified_files.update(commit["modified"])
            if commit.get("removed"):
                all_deleted_files.update(commit["removed"])

            all_changed_files.update(
                commit.get("added", [])
                + commit.get("modified", [])
                + commit.get("removed", [])
            )

        return WebhookEvent(
            event_type="push",
            repo_name=project.get("path_with_namespace", ""),
            repo_url=project.get("web_url", ""),
            branch=payload.get("ref", "").replace("refs/heads/", ""),
            commit_hash=commits[-1].get("id", "") if commits else "",
            commit_message=commits[-1].get("message", "") if commits else "",
            author=commits[-1].get("author", {}).get("name", "") if commits else "",
            timestamp=commits[-1].get("timestamp", "") if commits else "",
            changed_files=list(all_changed_files),
            added_files=list(all_added_files),
            modified_files=list(all_modified_files),
            deleted_files=list(all_deleted_files),
        )

    def _parse_gitlab_merge_request(self, payload: Dict[str, Any]) -> WebhookEvent:
        """Parse GitLab merge request event"""
        project = payload.get("project", {})
        obj = payload.get("object_attributes", {})

        return WebhookEvent(
            event_type="merge_request",
            repo_name=project.get("path_with_namespace", ""),
            repo_url=project.get("web_url", ""),
            branch=obj.get("source_branch", ""),
            commit_hash=obj.get("last_commit", {}).get("id", ""),
            commit_message=obj.get("title", ""),
            author=obj.get("author", {}).get("name", ""),
            timestamp=obj.get("updated_at", ""),
            changed_files=[],
            added_files=[],
            modified_files=[],
            deleted_files=[],
        )


class WebhookProcessor:
    """Processes webhook events and triggers indexing"""

    def __init__(self, webhook_receiver: WebhookReceiver, indexer_service):
        self.webhook_receiver = webhook_receiver
        self.indexer_service = indexer_service
        self.processing_queue = asyncio.Queue()
        self.is_processing = False

    async def process_webhook(
        self, headers: Dict[str, str], body: str
    ) -> Dict[str, Any]:
        """Process incoming webhook"""
        try:
            # Verify webhook signature
            signature = headers.get("X-Hub-Signature-256") or headers.get(
                "X-Gitlab-Token", ""
            )

            if not self.webhook_receiver.verify_signature(body, signature):
                return {
                    "success": False,
                    "error": "Invalid signature",
                    "status_code": 401,
                }

            # Parse webhook based on provider
            if "X-GitHub-Event" in headers:
                event = self.webhook_receiver.parse_github_webhook(headers, body)
                provider = "github"
            elif "X-Gitlab-Event" in headers:
                event = self.webhook_receiver.parse_gitlab_webhook(headers, body)
                provider = "gitlab"
            else:
                return {
                    "success": False,
                    "error": "Unknown webhook provider",
                    "status_code": 400,
                }

            if not event:
                return {
                    "success": False,
                    "error": "Unsupported event type",
                    "status_code": 400,
                }

            # Queue for processing
            await self.processing_queue.put((event, provider))

            # Start processing if not already running
            if not self.is_processing:
                asyncio.create_task(self._process_queue())

            logger.info(f"🪝 Webhook queued: {event.event_type} for {event.repo_name}")

            return {
                "success": True,
                "message": f"Webhook received for {event.event_type}",
                "event_id": f"{event.repo_name}_{event.commit_hash[:8]}",
                "status_code": 200,
            }

        except Exception as e:
            logger.error(f"❌ Webhook processing failed: {e}")
            return {"success": False, "error": str(e), "status_code": 500}

    async def _process_queue(self):
        """Process queued webhook events"""
        self.is_processing = True

        try:
            while not self.processing_queue.empty():
                event, provider = await self.processing_queue.get()

                try:
                    await self._handle_webhook_event(event, provider)
                except Exception as e:
                    logger.error(f"❌ Failed to handle webhook event: {e}")

                # Mark task as done
                self.processing_queue.task_done()

        except Exception as e:
            logger.error(f"❌ Queue processing failed: {e}")
        finally:
            self.is_processing = False

    async def _handle_webhook_event(self, event: WebhookEvent, provider: str):
        """Handle individual webhook event"""
        logger.info(
            f"🔄 Processing {event.event_type} from {provider}: {event.repo_name}"
        )

        try:
            if event.event_type == "push":
                await self._handle_push_event(event)
            elif event.event_type == "pull_request":
                await self._handle_pull_request_event(event)
            elif event.event_type == "merge_request":
                await self._handle_merge_request_event(event)
            elif event.event_type == "release":
                await self._handle_release_event(event)

            logger.info(f"✅ Processed {event.event_type} for {event.repo_name}")

        except Exception as e:
            logger.error(f"❌ Event handling failed: {e}")
            raise

    async def _handle_push_event(self, event: WebhookEvent):
        """Handle push events - trigger incremental indexing"""
        if not event.changed_files:
            logger.info("📭 No files changed in push event")
            return

        # Trigger incremental indexing for changed files
        indexing_result = await self.indexer_service.incremental_index(
            repo_name=event.repo_name,
            changed_files=event.changed_files,
            added_files=event.added_files,
            modified_files=event.modified_files,
            deleted_files=event.deleted_files,
            branch=event.branch,
        )

        if indexing_result.get("success"):
            logger.info(
                f"✅ Indexed {len(event.changed_files)} files for {event.repo_name}"
            )
        else:
            logger.error(
                f"❌ Failed to index {event.repo_name}: {indexing_result.get('error')}"
            )

    async def _handle_pull_request_event(self, event: WebhookEvent):
        """Handle pull request events"""
        # For PRs, we might want to index the PR branch
        logger.info(
            f"🔀 Pull request detected for {event.repo_name}, branch: {event.branch}"
        )

        # Trigger full indexing of PR branch (simplified)
        # In practice, you'd fetch PR diff and index only changed files
        indexing_result = await self.indexer_service.index_repository(
            repo_path=f"/repos/{event.repo_name}",
            collection_name=f"{event.repo_name}_pr_{event.branch}",
            force_reindex=True,
        )

        logger.info(f"📊 PR indexing result: {indexing_result.get('success', False)}")

    async def _handle_merge_request_event(self, event: WebhookEvent):
        """Handle merge request events (GitLab)"""
        logger.info(f"🔀 Merge request detected for {event.repo_name}")

        # Similar to pull request handling
        indexing_result = await self.indexer_service.index_repository(
            repo_path=f"/repos/{event.repo_name}",
            collection_name=f"{event.repo_name}_mr_{event.branch}",
            force_reindex=True,
        )

        logger.info(f"📊 MR indexing result: {indexing_result.get('success', False)}")

    async def _handle_release_event(self, event: WebhookEvent):
        """Handle release events"""
        logger.info(
            f"🚀 Release detected for {event.repo_name}: {event.commit_message}"
        )

        # For releases, trigger full reindex of main branch
        indexing_result = await self.indexer_service.index_repository(
            repo_path=f"/repos/{event.repo_name}",
            collection_name=f"{event.repo_name}_release",
            force_reindex=True,
        )

        logger.info(
            f"📊 Release indexing result: {indexing_result.get('success', False)}"
        )

    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue processing status"""
        return {
            "queue_size": self.processing_queue.qsize(),
            "is_processing": self.is_processing,
            "supported_events": self.webhook_receiver.supported_events,
        }
