import json
import logging
import time
from datetime import datetime
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
import aiofiles
import os

from app.models.requests import NotesRequest
from app.models.responses import NotesResponse, NoteInfo

logger = logging.getLogger(__name__)
router = APIRouter()

# Simple in-memory notes storage (for Phase 2)
# In Phase 3, this could be moved to a proper database
NOTES_FILE = "/app/data/notes.json"


async def load_notes() -> Dict[str, Dict]:
    """Load notes from file"""
    try:
        if os.path.exists(NOTES_FILE):
            async with aiofiles.open(NOTES_FILE, "r") as f:
                content = await f.read()
                return json.loads(content)
        return {}
    except Exception as e:
        logger.error(f"Failed to load notes: {e}")
        return {}


async def save_notes(notes: Dict[str, Dict]) -> bool:
    """Save notes to file"""
    try:
        async with aiofiles.open(NOTES_FILE, "w") as f:
            await f.write(json.dumps(notes, indent=2, default=str))
        return True
    except Exception as e:
        logger.error(f"Failed to save notes: {e}")
        return False


def generate_note_id() -> str:
    """Generate unique note ID"""
    return f"note_{int(time.time() * 1000)}"


@router.post("")
async def notes_operations(
    request: NotesRequest,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPAuthorizationCredentials()),
) -> NotesResponse:
    """Notes operations endpoint"""
    try:
        notes = await load_notes()

        if request.op == "add":
            if not request.text:
                raise HTTPException(
                    status_code=400, detail="Text is required for add operation"
                )

            note_id = generate_note_id()
            now = datetime.utcnow()

            note = {
                "id": note_id,
                "repo": request.repo,
                "text": request.text,
                "tags": request.tags or [],
                "created_at": now.isoformat(),
                "updated_at": None,
            }

            notes[note_id] = note

            if await save_notes(notes):
                logger.info(f"Added note: {note_id}")
                return NotesResponse(
                    success=True,
                    notes=[NoteInfo(**note)],
                    message=f"Added note: {note_id}",
                )
            else:
                return NotesResponse(success=False, message="Failed to save note")

        elif request.op == "search":
            if not request.query:
                raise HTTPException(
                    status_code=400, detail="Query is required for search operation"
                )

            query_lower = request.query.lower()
            matching_notes = []

            for note_data in notes.values():
                # Skip if repo filter doesn't match
                if request.repo and note_data.get("repo") != request.repo:
                    continue

                # Search in text and tags
                text_match = query_lower in note_data["text"].lower()
                tag_match = any(
                    query_lower in tag.lower() for tag in note_data.get("tags", [])
                )

                if text_match or tag_match:
                    matching_notes.append(NoteInfo(**note_data))

            # Sort by created_at (newest first)
            matching_notes.sort(key=lambda x: x.created_at, reverse=True)

            # Limit results
            if request.limit:
                matching_notes = matching_notes[: request.limit]

            return NotesResponse(
                success=True,
                notes=matching_notes,
                message=f"Found {len(matching_notes)} matching notes",
            )

        elif request.op == "list":
            matching_notes = []

            for note_data in notes.values():
                # Filter by repo if specified
                if request.repo and note_data.get("repo") != request.repo:
                    continue

                matching_notes.append(NoteInfo(**note_data))

            # Sort by created_at (newest first)
            matching_notes.sort(key=lambda x: x.created_at, reverse=True)

            # Limit results
            if request.limit:
                matching_notes = matching_notes[: request.limit]

            return NotesResponse(
                success=True,
                notes=matching_notes,
                message=f"Listed {len(matching_notes)} notes",
            )

        elif request.op == "delete":
            # Note: This is a simplified delete by ID
            # In a real implementation, you might want delete by query or other criteria
            if not request.text:  # Using text field as note_id for delete
                raise HTTPException(
                    status_code=400, detail="Note ID is required for delete operation"
                )

            note_id = request.text
            if note_id in notes:
                del notes[note_id]

                if await save_notes(notes):
                    logger.info(f"Deleted note: {note_id}")
                    return NotesResponse(
                        success=True, message=f"Deleted note: {note_id}"
                    )
                else:
                    return NotesResponse(
                        success=False, message="Failed to save after delete"
                    )
            else:
                return NotesResponse(
                    success=False, message=f"Note not found: {note_id}"
                )

        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported operation: {request.op}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Notes operation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Notes operation failed: {e}")


@router.get("/stats")
async def notes_stats(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPAuthorizationCredentials()),
) -> NotesResponse:
    """Get notes statistics"""
    try:
        notes = await load_notes()

        # Calculate stats
        total_notes = len(notes)
        repos = set()
        all_tags = set()

        for note_data in notes.values():
            if note_data.get("repo"):
                repos.add(note_data["repo"])
            all_tags.update(note_data.get("tags", []))

        return NotesResponse(
            success=True,
            message=f"Statistics: {total_notes} notes across {len(repos)} repositories",
        )

    except Exception as e:
        logger.error(f"Failed to get notes stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {e}")
