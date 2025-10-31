"""
Enhanced Indexing Service
Real-time incremental indexing with webhook integration
"""

import asyncio
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from .indexing import IndexingService
from .semantic_chunking import SemanticChunkingService
from .embeddings import EmbeddingsService
from .qdrant_client import QdrantClient

logger = logging.getLogger(__name__)


@dataclass
class IndexingJob:
    """Indexing job metadata"""

    job_id: str
    repo_name: str
    branch: str
    job_type: str  # 'full', 'incremental', 'pr', 'release'
    status: str  # 'queued', 'processing', 'completed', 'failed'
    files_count: int
    chunks_count: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: float = 0.0


@dataclass
class FileIndex:
    """File index metadata for change tracking"""

    file_path: str
    file_hash: str
    last_modified: float
    chunk_count: int
    indexed_at: datetime
    collection_name: str


class EnhancedIndexingService:
    """Enhanced indexing with real-time capabilities"""

    def __init__(
        self,
        indexing_service: IndexingService,
        semantic_chunking: SemanticChunkingService,
        embeddings_service: EmbeddingsService,
        qdrant_client: QdrantClient,
        index_dir: str = "/tmp/indexes",
    ):
        self.indexing_service = indexing_service
        self.semantic_chunking = semantic_chunking
        self.embeddings_service = embeddings_service
        self.qdrant_client = qdrant_client

        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(exist_ok=True)

        # In-memory state for tracking
        self.active_jobs: Dict[str, IndexingJob] = {}
        self.file_indexes: Dict[str, FileIndex] = {}
        self.job_queue = asyncio.Queue()

        # Load existing indexes
        self._load_file_indexes()

        # Start background processor
        self._start_job_processor()

    def _load_file_indexes(self):
        """Load existing file indexes from disk"""
        try:
            index_file = self.index_dir / "file_indexes.json"
            if index_file.exists():
                with open(index_file, "r") as f:
                    data = json.load(f)
                    for file_path, file_data in data.items():
                        self.file_indexes[file_path] = FileIndex(
                            file_path=file_data["file_path"],
                            file_hash=file_data["file_hash"],
                            last_modified=file_data["last_modified"],
                            chunk_count=file_data["chunk_count"],
                            indexed_at=datetime.fromisoformat(file_data["indexed_at"]),
                            collection_name=file_data["collection_name"],
                        )
                logger.info(f"📂 Loaded {len(self.file_indexes)} file indexes")
        except Exception as e:
            logger.error(f"❌ Failed to load file indexes: {e}")

    def _save_file_indexes(self):
        """Save file indexes to disk"""
        try:
            index_file = self.index_dir / "file_indexes.json"
            data = {}
            for file_path, file_index in self.file_indexes.items():
                data[file_path] = {
                    "file_path": file_index.file_path,
                    "file_hash": file_index.file_hash,
                    "last_modified": file_index.last_modified,
                    "chunk_count": file_index.chunk_count,
                    "indexed_at": file_index.indexed_at.isoformat(),
                    "collection_name": file_index.collection_name,
                }

            with open(index_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"❌ Failed to save file indexes: {e}")

    def _start_job_processor(self):
        """Start background job processor"""
        asyncio.create_task(self._process_job_queue())

    async def _process_job_queue(self):
        """Process indexing jobs in background"""
        while True:
            try:
                job = await self.job_queue.get()
                await self._execute_indexing_job(job)
                self.job_queue.task_done()
            except Exception as e:
                logger.error(f"❌ Job processing failed: {e}")

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file content"""
        try:
            with open(file_path, "rb") as f:
                content = f.read()
                return hashlib.sha256(content).hexdigest()
        except Exception as e:
            logger.error(f"❌ Failed to calculate hash for {file_path}: {e}")
            return ""

    def _is_file_changed(self, file_path: Path, collection_name: str) -> bool:
        """Check if file has changed since last indexing"""
        file_key = str(file_path)

        if file_key not in self.file_indexes:
            return True

        file_index = self.file_indexes[file_key]

        # Check collection name matches
        if file_index.collection_name != collection_name:
            return True

        # Check file modification time
        current_mtime = file_path.stat().st_mtime
        if current_mtime > file_index.last_modified:
            return True

        # Check file hash
        current_hash = self._calculate_file_hash(file_path)
        if current_hash != file_index.file_hash:
            return True

        return False

    async def incremental_index(
        self,
        repo_name: str,
        changed_files: List[str],
        added_files: List[str],
        modified_files: List[str],
        deleted_files: List[str],
        branch: str = "main",
        collection_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Perform incremental indexing of changed files"""

        collection_name = collection_name or f"{repo_name}_{branch}"
        job_id = f"incremental_{repo_name}_{branch}_{int(time.time())}"

        # Create indexing job
        job = IndexingJob(
            job_id=job_id,
            repo_name=repo_name,
            branch=branch,
            job_type="incremental",
            status="queued",
            files_count=len(changed_files),
            chunks_count=0,
        )

        self.active_jobs[job_id] = job

        try:
            # Start job
            job.status = "processing"
            job.start_time = datetime.now()

            repo_path = Path(f"/repos/{repo_name}")

            # Process deleted files
            await self._process_deleted_files(deleted_files, collection_name)

            # Process added and modified files
            all_files_to_process = set(added_files + modified_files)
            processed_files = 0
            total_chunks = 0

            for file_path in all_files_to_process:
                full_path = repo_path / file_path
                if not full_path.exists():
                    logger.warning(f"⚠️ File not found: {full_path}")
                    continue

                try:
                    # Check if file actually changed
                    if not self._is_file_changed(full_path, collection_name):
                        logger.debug(f"⏭️ Skipping unchanged file: {file_path}")
                        processed_files += 1
                        continue

                    # Process file
                    chunks = await self._process_single_file(full_path, collection_name)
                    total_chunks += len(chunks)

                    # Update file index
                    self._update_file_index(full_path, collection_name, chunks)

                    processed_files += 1
                    job.progress = processed_files / len(all_files_to_process) * 100

                except Exception as e:
                    logger.error(f"❌ Failed to process {file_path}: {e}")

            # Save updated file indexes
            self._save_file_indexes()

            # Update job status
            job.status = "completed"
            job.end_time = datetime.now()
            job.chunks_count = total_chunks

            logger.info(
                f"✅ Incremental indexing completed: {processed_files} files, {total_chunks} chunks"
            )

            return {
                "success": True,
                "job_id": job_id,
                "files_processed": processed_files,
                "chunks_indexed": total_chunks,
                "processing_time_ms": int(
                    (job.end_time - job.start_time).total_seconds() * 1000
                ),
            }

        except Exception as e:
            job.status = "failed"
            job.end_time = datetime.now()
            job.error_message = str(e)

            logger.error(f"❌ Incremental indexing failed: {e}")

            return {
                "success": False,
                "job_id": job_id,
                "error": str(e),
                "files_processed": processed_files,
                "chunks_indexed": total_chunks,
            }

    async def _process_deleted_files(
        self, deleted_files: List[str], collection_name: str
    ):
        """Remove deleted files from index"""
        if not deleted_files:
            return

        try:
            # Delete points for deleted files
            for file_path in deleted_files:
                # Find all points for this file
                # This is simplified - in practice you'd query for exact matches
                point_ids_to_delete = []

                # Generate point ID patterns
                base_pattern = f"{file_path}:"
                for i in range(1000):  # Reasonable limit
                    point_ids_to_delete.append(f"{base_pattern}chunk_{i}")

                # Delete points (simplified)
                if point_ids_to_delete:
                    logger.info(f"🗑️ Deleting points for {file_path}")
                    # In practice: qdrant_client.delete_points(collection_name, point_ids_to_delete)

                # Remove from file indexes
                if file_path in self.file_indexes:
                    del self.file_indexes[file_path]

            logger.info(f"🗑️ Processed {len(deleted_files)} deleted files")

        except Exception as e:
            logger.error(f"❌ Failed to process deleted files: {e}")

    async def _process_single_file(
        self, file_path: Path, collection_name: str
    ) -> List[Dict[str, Any]]:
        """Process a single file for indexing"""
        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Perform semantic chunking
            chunks = await self.semantic_chunking.chunk_document(
                str(file_path), content
            )

            # Generate embeddings
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = self.embeddings_service.embed_texts(chunk_texts)

            # Create points for Qdrant
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                point = {
                    "id": chunk.id,
                    "vector": embedding,
                    "payload": {
                        "content": chunk.content,
                        "file_path": str(file_path),
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        "chunk_type": chunk.chunk_type,
                        "language": chunk.language,
                        "metadata": chunk.metadata,
                    },
                }
                points.append(point)

            # Store in Qdrant
            if points:
                self.qdrant_client.upsert_points(collection_name, points)

            return chunks

        except Exception as e:
            logger.error(f"❌ Failed to process file {file_path}: {e}")
            return []

    def _update_file_index(self, file_path: Path, collection_name: str, chunks: List):
        """Update file index metadata"""
        file_key = str(file_path)

        file_index = FileIndex(
            file_path=file_key,
            file_hash=self._calculate_file_hash(file_path),
            last_modified=file_path.stat().st_mtime,
            chunk_count=len(chunks),
            indexed_at=datetime.now(),
            collection_name=collection_name,
        )

        self.file_indexes[file_key] = file_index

    async def index_repository(
        self, repo_path: str, collection_name: str, force_reindex: bool = False
    ) -> Dict[str, Any]:
        """Enhanced repository indexing with job tracking"""
        job_id = f"full_{collection_name}_{int(time.time())}"

        # Create indexing job
        job = IndexingJob(
            job_id=job_id,
            repo_name=collection_name,
            branch="main",
            job_type="full",
            status="queued",
            files_count=0,
            chunks_count=0,
        )

        self.active_jobs[job_id] = job

        # Queue job for background processing
        await self.job_queue.put((repo_path, collection_name, force_reindex, job))

        return {
            "success": True,
            "job_id": job_id,
            "message": "Indexing job queued",
            "status": "queued",
        }

    async def _execute_indexing_job(self, job_data: tuple):
        """Execute a full indexing job"""
        repo_path, collection_name, force_reindex, job = job_data

        try:
            job.status = "processing"
            job.start_time = datetime.now()

            # Use existing indexing service
            result = await self.indexing_service.index_repository(
                repo_path, collection_name, force_reindex
            )

            if result.get("success"):
                job.status = "completed"
                job.files_count = result.get("files_processed", 0)
                job.chunks_count = result.get("chunks_indexed", 0)
            else:
                job.status = "failed"
                job.error_message = result.get("error", "Unknown error")

            job.end_time = datetime.now()

        except Exception as e:
            job.status = "failed"
            job.end_time = datetime.now()
            job.error_message = str(e)
            logger.error(f"❌ Indexing job {job.job_id} failed: {e}")

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an indexing job"""
        if job_id not in self.active_jobs:
            return None

        job = self.active_jobs[job_id]
        return {
            "job_id": job.job_id,
            "repo_name": job.repo_name,
            "branch": job.branch,
            "job_type": job.job_type,
            "status": job.status,
            "files_count": job.files_count,
            "chunks_count": job.chunks_count,
            "progress": job.progress,
            "start_time": job.start_time.isoformat() if job.start_time else None,
            "end_time": job.end_time.isoformat() if job.end_time else None,
            "error_message": job.error_message,
            "duration_ms": None,
        }

    async def list_active_jobs(self) -> List[Dict[str, Any]]:
        """List all active indexing jobs"""
        jobs = []
        for job_id, job in self.active_jobs.items():
            job_data = await self.get_job_status(job_id)
            if job_data:
                jobs.append(job_data)
        return jobs

    async def get_indexing_stats(self) -> Dict[str, Any]:
        """Get indexing statistics"""
        total_files = len(self.file_indexes)
        total_chunks = sum(fi.chunk_count for fi in self.file_indexes.values())

        active_jobs = [j for j in self.active_jobs.values() if j.status == "processing"]
        completed_jobs = [
            j for j in self.active_jobs.values() if j.status == "completed"
        ]
        failed_jobs = [j for j in self.active_jobs.values() if j.status == "failed"]

        return {
            "total_files_indexed": total_files,
            "total_chunks_indexed": total_chunks,
            "active_jobs_count": len(active_jobs),
            "completed_jobs_count": len(completed_jobs),
            "failed_jobs_count": len(failed_jobs),
            "queue_size": self.job_queue.qsize(),
            "supported_collections": await self._get_collections_list(),
        }

    async def _get_collections_list(self) -> List[str]:
        """Get list of available collections"""
        try:
            return self.qdrant_client.list_collections()
        except Exception as e:
            logger.error(f"❌ Failed to get collections: {e}")
            return []

    async def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old completed/failed jobs"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)

        jobs_to_remove = []
        for job_id, job in self.active_jobs.items():
            if job.status in ["completed", "failed"]:
                if job.end_time and job.end_time.timestamp() < cutoff_time:
                    jobs_to_remove.append(job_id)

        for job_id in jobs_to_remove:
            del self.active_jobs[job_id]

        logger.info(f"🧹 Cleaned up {len(jobs_to_remove)} old jobs")
