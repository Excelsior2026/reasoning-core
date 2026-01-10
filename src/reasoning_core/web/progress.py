"""Progress tracking for real-time updates."""

import asyncio
import logging
from typing import Dict, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Track progress for analysis tasks."""

    def __init__(self, task_id: str):
        """Initialize progress tracker.

        Args:
            task_id: Task identifier
        """
        self.task_id = task_id
        self.stage = "initializing"
        self.progress = 0
        self.message = ""
        self.started_at = datetime.now()
        self.updated_at = datetime.now()
        self._listeners: list[Callable] = []

    def add_listener(self, callback: Callable[[Dict], None]):
        """Add a progress update listener.

        Args:
            callback: Function to call with progress updates
        """
        self._listeners.append(callback)

    def update(self, stage: str, progress: int, message: str = ""):
        """Update progress.

        Args:
            stage: Current stage name
            progress: Progress percentage (0-100)
            message: Optional message
        """
        self.stage = stage
        self.progress = max(0, min(100, progress))  # Clamp between 0-100
        self.message = message
        self.updated_at = datetime.now()

        # Notify listeners
        update = {
            "task_id": self.task_id,
            "stage": self.stage,
            "progress": self.progress,
            "message": self.message,
            "timestamp": self.updated_at.isoformat(),
        }

        for listener in self._listeners:
            try:
                listener(update)
            except Exception as e:
                logger.warning(f"Error notifying progress listener: {e}")

    def to_dict(self) -> Dict:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "task_id": self.task_id,
            "stage": self.stage,
            "progress": self.progress,
            "message": self.message,
            "started_at": self.started_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# Global progress trackers
_progress_trackers: Dict[str, ProgressTracker] = {}


def get_progress_tracker(task_id: str) -> Optional[ProgressTracker]:
    """Get progress tracker for a task.

    Args:
        task_id: Task identifier

    Returns:
        ProgressTracker or None
    """
    return _progress_trackers.get(task_id)


def create_progress_tracker(task_id: str) -> ProgressTracker:
    """Create a new progress tracker.

    Args:
        task_id: Task identifier

    Returns:
        ProgressTracker instance
    """
    tracker = ProgressTracker(task_id)
    _progress_trackers[task_id] = tracker
    return tracker


def remove_progress_tracker(task_id: str):
    """Remove a progress tracker.

    Args:
        task_id: Task identifier
    """
    _progress_trackers.pop(task_id, None)
