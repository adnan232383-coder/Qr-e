"""
Decision Logger - Tracks autonomous choices made by the system.
Logs: timestamp, component, chosen_option, reason
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class DecisionLogger:
    """
    Centralized decision logging for autonomous system choices.
    Persists to MongoDB for audit trail and debugging.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self._collection = db.decision_log
    
    async def log(
        self,
        component: str,
        chosen_option: str,
        reason: str,
        context: Optional[Dict[str, Any]] = None,
        job_id: Optional[str] = None
    ) -> str:
        """
        Log an autonomous decision.
        
        Args:
            component: System component making the decision (e.g., "job_runner", "content_generator")
            chosen_option: What was decided (e.g., "skip_course", "use_thread_pool", "retry_batch")
            reason: Why this choice was made
            context: Additional context data (optional)
            job_id: Associated job ID if applicable
        
        Returns:
            The inserted document ID as string
        """
        doc = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "component": component,
            "chosen_option": chosen_option,
            "reason": reason,
            "context": context or {},
            "job_id": job_id
        }
        
        result = await self._collection.insert_one(doc)
        logger.info(f"[DECISION] {component}: {chosen_option} - {reason}")
        
        return str(result.inserted_id)
    
    async def get_recent(self, limit: int = 50, component: Optional[str] = None) -> list:
        """Get recent decisions, optionally filtered by component."""
        query = {}
        if component:
            query["component"] = component
        
        cursor = self._collection.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(limit)
    
    async def get_by_job(self, job_id: str) -> list:
        """Get all decisions for a specific job."""
        cursor = self._collection.find(
            {"job_id": job_id},
            {"_id": 0}
        ).sort("timestamp", 1)
        return await cursor.to_list(1000)


# Singleton
_decision_logger: Optional[DecisionLogger] = None


def get_decision_logger(db: AsyncIOMotorDatabase) -> DecisionLogger:
    """Get or create the global decision logger instance."""
    global _decision_logger
    if _decision_logger is None:
        _decision_logger = DecisionLogger(db)
    return _decision_logger
