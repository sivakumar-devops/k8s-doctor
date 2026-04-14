"""
Rate limiting to prevent API quota exhaustion and control costs.
"""

import logging
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for API calls and diagnoses."""

    def __init__(self, max_diagnoses_per_hour: int = 30):
        """Initialize rate limiter."""
        self.max_diagnoses_per_hour = max_diagnoses_per_hour
        self.diagnosis_history = defaultdict(list)
        self.last_reset = datetime.now()

    def can_diagnose(self, resource_key: str) -> bool:
        """Check if resource can be diagnosed."""
        now = datetime.now()
        
        # Reset counter every hour
        if now - self.last_reset > timedelta(hours=1):
            self.diagnosis_history.clear()
            self.last_reset = now

        # Count diagnoses in last hour
        total_diagnoses = sum(len(v) for v in self.diagnosis_history.values())
        
        if total_diagnoses >= self.max_diagnoses_per_hour:
            logger.warning(
                f"Rate limit reached: {total_diagnoses}/{self.max_diagnoses_per_hour} diagnoses/hour"
            )
            return False

        return True

    def record_diagnosis(self, resource_key: str) -> None:
        """Record that a diagnosis was performed."""
        self.diagnosis_history[resource_key].append(datetime.now())

    def get_remaining_capacity(self) -> int:
        """Get remaining diagnosis capacity this hour."""
        total_diagnoses = sum(len(v) for v in self.diagnosis_history.values())
        return max(0, self.max_diagnoses_per_hour - total_diagnoses)

    def get_stats(self) -> dict:
        """Get rate limiting statistics."""
        total_diagnoses = sum(len(v) for v in self.diagnosis_history.values())
        return {
            "total_diagnoses_this_hour": total_diagnoses,
            "max_diagnoses_per_hour": self.max_diagnoses_per_hour,
            "remaining_capacity": self.get_remaining_capacity(),
            "reset_time": (self.last_reset + timedelta(hours=1)).isoformat(),
        }
