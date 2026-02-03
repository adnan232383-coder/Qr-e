"""
Job Runner System - Modular Background Task Processing
Uses ProcessPoolExecutor for non-blocking execution.
Designed for easy migration to Celery/ARQ later.

Features:
- Status tracking (queued/running/done/failed)
- Progress updates
- Idempotency checks
- Retries with exponential backoff
- Rate limiting
- Per-course/job locking
- Decision logging for autonomous choices
"""

import os
import uuid
import asyncio
import logging
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ProcessPoolExecutor, Future
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from functools import partial
from decision_logger import get_decision_logger

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    MCQ_GENERATION = "mcq_generation"
    SCRIPT_GENERATION = "script_generation"
    VIDEO_GENERATION = "video_generation"
    BULK_MCQ = "bulk_mcq"
    BULK_SCRIPT = "bulk_script"
    BULK_VIDEO = "bulk_video"


@dataclass
class JobConfig:
    """Configuration for job execution"""
    max_retries: int = 3
    retry_base_delay: float = 2.0  # seconds
    retry_max_delay: float = 60.0  # seconds
    rate_limit_per_minute: int = 30  # API calls per minute
    batch_size: int = 25
    questions_per_course: int = 200


@dataclass
class JobProgress:
    """Progress tracking for a job"""
    total: int = 0
    completed: int = 0
    failed: int = 0
    current_item: str = ""
    last_update: str = ""
    
    @property
    def percentage(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.completed / self.total) * 100


class JobLockManager:
    """Manages per-course/job locks to prevent concurrent runs"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self._collection = db.job_locks
    
    async def acquire(self, resource_id: str, job_id: str, timeout_minutes: int = 60) -> bool:
        """Try to acquire a lock for a resource"""
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        locked_until = now + timedelta(minutes=timeout_minutes)
        
        # Try to acquire or update existing lock
        result = await self._collection.update_one(
            {
                "resource_id": resource_id,
                "$or": [
                    {"locked_until": {"$lt": now.isoformat()}},  # Lock expired
                    {"job_id": job_id}  # Same job
                ]
            },
            {
                "$set": {
                    "resource_id": resource_id,
                    "job_id": job_id,
                    "locked_at": now.isoformat(),
                    "locked_until": locked_until.isoformat()
                }
            },
            upsert=False
        )
        
        if result.modified_count > 0:
            return True
        
        # Try insert if no existing lock
        try:
            await self._collection.insert_one({
                "resource_id": resource_id,
                "job_id": job_id,
                "locked_at": now.isoformat(),
                "locked_until": locked_until.isoformat()
            })
            return True
        except Exception:
            return False
    
    async def release(self, resource_id: str, job_id: str):
        """Release a lock"""
        await self._collection.delete_one({
            "resource_id": resource_id,
            "job_id": job_id
        })
    
    async def is_locked(self, resource_id: str) -> bool:
        """Check if a resource is locked"""
        now = datetime.now(timezone.utc).isoformat()
        lock = await self._collection.find_one({
            "resource_id": resource_id,
            "locked_until": {"$gt": now}
        })
        return lock is not None
    
    async def get_lock_info(self, resource_id: str) -> Optional[Dict]:
        """Get lock info for a resource"""
        return await self._collection.find_one(
            {"resource_id": resource_id},
            {"_id": 0}
        )


class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, calls_per_minute: int = 30):
        self.calls_per_minute = calls_per_minute
        self.interval = 60.0 / calls_per_minute
        self.last_call = 0.0
        self._lock = asyncio.Lock()
    
    async def wait(self):
        """Wait if needed to respect rate limit"""
        async with self._lock:
            now = time.time()
            time_since_last = now - self.last_call
            if time_since_last < self.interval:
                await asyncio.sleep(self.interval - time_since_last)
            self.last_call = time.time()


# Synchronous worker functions (run in separate process)
def _generate_mcq_batch_sync(
    mongo_url: str,
    db_name: str,
    api_key: str,
    course_id: str,
    course_name: str,
    batch_num: int,
    batch_size: int,
    total_batches: int
) -> Dict[str, Any]:
    """
    Synchronous MCQ batch generation - runs in separate process.
    Returns generated questions or error info.
    """
    import json as json_module
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    from pymongo import MongoClient
    
    try:
        # Connect to MongoDB (sync client for subprocess)
        client = MongoClient(mongo_url)
        db = client[db_name]
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"mcq_{course_id}_{batch_num}",
            system_message="""You are a medical education expert creating high-quality MCQ questions.
Create questions suitable for medical/pharmacy board exam preparation.
Always return valid JSON array only, no other text."""
        ).with_model("openai", "gpt-5.2")
        
        prompt = f"""Generate {batch_size} multiple-choice questions for:
Course: {course_name}
Batch: {batch_num + 1}/{total_batches}

For each question provide:
1. question: The question text
2. option_a, option_b, option_c, option_d: Four answer options
3. correct_answer: The correct option letter (A, B, C, or D)
4. explanation: Detailed explanation (2-3 sentences)
5. difficulty: easy, medium, or hard

Format as JSON array ONLY, no other text:
[{{"question": "...", "option_a": "...", "option_b": "...", "option_c": "...", "option_d": "...", "correct_answer": "A", "explanation": "...", "difficulty": "medium"}}]

Create clinically relevant questions. Vary difficulty: 30% easy, 50% medium, 20% hard.
Cover different aspects of {course_name}."""

        # Use sync version
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(chat.send_message(UserMessage(text=prompt)))
        loop.close()
        
        # Parse JSON from response
        json_start = response.find('[')
        json_end = response.rfind(']') + 1
        
        if json_start >= 0 and json_end > json_start:
            questions = json_module.loads(response[json_start:json_end])
            
            # Add metadata to each question
            for i, q in enumerate(questions):
                q["question_id"] = f"q_{course_id}_{batch_num:02d}_{i:03d}"
                q["course_id"] = course_id
                q["topic"] = course_name
                q["created_at"] = datetime.now(timezone.utc).isoformat()
            
            return {
                "success": True,
                "questions": questions,
                "count": len(questions)
            }
        else:
            return {
                "success": False,
                "error": "Failed to parse JSON from response",
                "questions": []
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "questions": []
        }


class JobRunner:
    """
    Main job runner class that manages background task execution.
    Uses ProcessPoolExecutor for non-blocking execution.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, config: Optional[JobConfig] = None):
        self.db = db
        self.config = config or JobConfig()
        self.lock_manager = JobLockManager(db)
        self.rate_limiter = RateLimiter(self.config.rate_limit_per_minute)
        self._executor: Optional[ProcessPoolExecutor] = None
        self._running_jobs: Dict[str, Future] = {}
        self._shutdown = False
        self.decision_logger = get_decision_logger(db)
        
        # Get MongoDB connection info for subprocess
        self.mongo_url = os.environ.get('MONGO_URL')
        self.db_name = os.environ.get('DB_NAME')
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
    
    @property
    def executor(self) -> ProcessPoolExecutor:
        """Lazy-initialize the process pool"""
        if self._executor is None:
            # Use max 4 workers to avoid overwhelming the system
            self._executor = ProcessPoolExecutor(max_workers=4)
        return self._executor
    
    async def create_job(
        self,
        job_type: JobType,
        params: Dict[str, Any],
        resource_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new job with idempotency check.
        Returns existing job if one is already running for the resource.
        """
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        
        # Idempotency check - if resource has an active job, return it
        if resource_id:
            existing = await self.db.jobs.find_one({
                "resource_id": resource_id,
                "status": {"$in": [JobStatus.QUEUED, JobStatus.RUNNING]}
            }, {"_id": 0})
            
            if existing:
                await self.decision_logger.log(
                    component="job_runner",
                    chosen_option="return_existing_job",
                    reason=f"Active job already exists for resource {resource_id}",
                    context={"existing_job_id": existing['job_id'], "resource_id": resource_id},
                    job_id=existing['job_id']
                )
                logger.info(f"Found existing job {existing['job_id']} for resource {resource_id}")
                return existing
        
        job = {
            "job_id": job_id,
            "job_type": job_type,
            "resource_id": resource_id,
            "params": params,
            "status": JobStatus.QUEUED,
            "progress": asdict(JobProgress()),
            "retries": 0,
            "error": None,
            "created_at": now.isoformat(),
            "started_at": None,
            "completed_at": None,
            "updated_at": now.isoformat()
        }
        
        await self.db.jobs.insert_one(job)
        
        await self.decision_logger.log(
            component="job_runner",
            chosen_option="create_new_job",
            reason=f"No existing job for resource, creating new {job_type} job",
            context={"job_type": str(job_type), "resource_id": resource_id},
            job_id=job_id
        )
        logger.info(f"Created job {job_id} of type {job_type}")
        
        # Return without _id
        del job["_id"]
        return job
    
    async def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job by ID"""
        return await self.db.jobs.find_one({"job_id": job_id}, {"_id": 0})
    
    async def get_jobs_by_type(self, job_type: JobType, status: Optional[JobStatus] = None) -> List[Dict]:
        """Get all jobs of a type, optionally filtered by status"""
        query = {"job_type": job_type}
        if status:
            query["status"] = status
        return await self.db.jobs.find(query, {"_id": 0}).to_list(1000)
    
    async def update_job_status(self, job_id: str, status: JobStatus, error: Optional[str] = None):
        """Update job status"""
        update = {
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if status == JobStatus.RUNNING:
            update["started_at"] = datetime.now(timezone.utc).isoformat()
        elif status in [JobStatus.DONE, JobStatus.FAILED, JobStatus.CANCELLED]:
            update["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        if error:
            update["error"] = error
        
        await self.db.jobs.update_one({"job_id": job_id}, {"$set": update})
    
    async def update_job_progress(self, job_id: str, progress: JobProgress):
        """Update job progress"""
        progress.last_update = datetime.now(timezone.utc).isoformat()
        await self.db.jobs.update_one(
            {"job_id": job_id},
            {"$set": {"progress": asdict(progress), "updated_at": progress.last_update}}
        )
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job if it's queued or running"""
        job = await self.get_job(job_id)
        if not job:
            return False
        
        if job["status"] not in [JobStatus.QUEUED, JobStatus.RUNNING]:
            return False
        
        # Release lock if exists
        if job.get("resource_id"):
            await self.lock_manager.release(job["resource_id"], job_id)
        
        await self.update_job_status(job_id, JobStatus.CANCELLED)
        
        # Cancel future if running
        if job_id in self._running_jobs:
            self._running_jobs[job_id].cancel()
            del self._running_jobs[job_id]
        
        logger.info(f"Cancelled job {job_id}")
        return True
    
    async def start_mcq_generation(self, course_id: Optional[str] = None) -> Dict:
        """
        Start MCQ generation for a single course or all courses.
        Returns the created job info.
        """
        if course_id:
            # Single course
            course = await self.db.courses.find_one({"external_id": course_id}, {"_id": 0})
            if not course:
                raise ValueError(f"Course not found: {course_id}")
            
            job = await self.create_job(
                JobType.MCQ_GENERATION,
                {"course_id": course_id, "course_name": course["course_name"]},
                resource_id=f"mcq_{course_id}"
            )
        else:
            # All courses - bulk job
            courses = await self.db.courses.find({}, {"_id": 0, "external_id": 1}).to_list(100)
            job = await self.create_job(
                JobType.BULK_MCQ,
                {"course_ids": [c["external_id"] for c in courses]},
                resource_id="bulk_mcq_all"
            )
        
        # Start processing in background
        asyncio.create_task(self._process_job(job["job_id"]))
        return job
    
    async def _process_job(self, job_id: str):
        """Process a job based on its type"""
        job = await self.get_job(job_id)
        if not job or job["status"] != JobStatus.QUEUED:
            return
        
        job_type = job["job_type"]
        
        try:
            # Try to acquire lock
            resource_id = job.get("resource_id")
            if resource_id and not await self.lock_manager.acquire(resource_id, job_id):
                logger.warning(f"Could not acquire lock for {resource_id}")
                await self.update_job_status(job_id, JobStatus.FAILED, "Resource is locked by another job")
                return
            
            await self.update_job_status(job_id, JobStatus.RUNNING)
            
            if job_type == JobType.MCQ_GENERATION:
                await self._run_single_mcq_generation(job)
            elif job_type == JobType.BULK_MCQ:
                await self._run_bulk_mcq_generation(job)
            elif job_type == JobType.BULK_SCRIPT:
                await self._run_bulk_script_generation(job)
            elif job_type == JobType.SCRIPT_GENERATION:
                await self._run_single_script_generation(job)
            else:
                raise ValueError(f"Unknown job type: {job_type}")
            
            await self.update_job_status(job_id, JobStatus.DONE)
            logger.info(f"Job {job_id} completed successfully")
            
        except asyncio.CancelledError:
            await self.update_job_status(job_id, JobStatus.CANCELLED)
            logger.info(f"Job {job_id} was cancelled")
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            await self._handle_job_failure(job, str(e))
        finally:
            # Release lock
            resource_id = job.get("resource_id")
            if resource_id:
                await self.lock_manager.release(resource_id, job_id)
    
    async def _run_single_mcq_generation(self, job: Dict):
        """Generate MCQ for a single course"""
        job_id = job["job_id"]
        course_id = job["params"]["course_id"]
        course_name = job["params"]["course_name"]
        
        # Check existing questions
        existing_count = await self.db.mcq_questions.count_documents({"course_id": course_id})
        if existing_count >= self.config.questions_per_course:
            logger.info(f"Course {course_id} already has {existing_count} questions, skipping")
            return
        
        batch_size = self.config.batch_size
        total_needed = self.config.questions_per_course
        total_batches = (total_needed + batch_size - 1) // batch_size
        
        progress = JobProgress(total=total_batches, current_item=course_name)
        all_questions = []
        
        for batch_num in range(total_batches):
            if self._shutdown:
                raise asyncio.CancelledError()
            
            # Rate limiting
            await self.rate_limiter.wait()
            
            # Run batch generation in process pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                partial(
                    _generate_mcq_batch_sync,
                    self.mongo_url,
                    self.db_name,
                    self.api_key,
                    course_id,
                    course_name,
                    batch_num,
                    batch_size,
                    total_batches
                )
            )
            
            if result["success"]:
                all_questions.extend(result["questions"])
                progress.completed = batch_num + 1
                logger.info(f"Batch {batch_num + 1}/{total_batches} completed for {course_id}")
            else:
                progress.failed += 1
                logger.warning(f"Batch {batch_num + 1} failed: {result.get('error')}")
            
            await self.update_job_progress(job_id, progress)
        
        # Save all questions to database
        if all_questions:
            await self.db.mcq_questions.delete_many({"course_id": course_id})
            await self.db.mcq_questions.insert_many(all_questions)
            logger.info(f"Saved {len(all_questions)} questions for {course_id}")
    
    async def _run_bulk_mcq_generation(self, job: Dict):
        """Generate MCQ for all courses"""
        job_id = job["job_id"]
        course_ids = job["params"]["course_ids"]
        
        # Get course details
        courses = await self.db.courses.find(
            {"external_id": {"$in": course_ids}},
            {"_id": 0, "external_id": 1, "course_name": 1}
        ).to_list(100)
        
        course_map = {c["external_id"]: c["course_name"] for c in courses}
        
        # Initialize progress with total
        progress = JobProgress(total=len(course_ids))
        await self.update_job_progress(job_id, progress)
        
        await self.decision_logger.log(
            component="job_runner",
            chosen_option="start_bulk_mcq",
            reason=f"Starting bulk MCQ generation for {len(course_ids)} courses",
            context={"total_courses": len(course_ids), "questions_per_course": self.config.questions_per_course},
            job_id=job_id
        )
        
        for i, course_id in enumerate(course_ids):
            if self._shutdown:
                raise asyncio.CancelledError()
            
            # Check if cancelled
            current_job = await self.get_job(job_id)
            if current_job and current_job["status"] == JobStatus.CANCELLED:
                raise asyncio.CancelledError()
            
            course_name = course_map.get(course_id, course_id)
            progress.current_item = f"Processing: {course_name}"
            await self.update_job_progress(job_id, progress)  # Update immediately
            
            # Check existing questions
            existing_count = await self.db.mcq_questions.count_documents({"course_id": course_id})
            if existing_count >= self.config.questions_per_course:
                await self.decision_logger.log(
                    component="job_runner",
                    chosen_option="skip_course",
                    reason=f"Course already has {existing_count} questions (target: {self.config.questions_per_course})",
                    context={"course_id": course_id, "existing_count": existing_count},
                    job_id=job_id
                )
                logger.info(f"Course {course_id} already has {existing_count} questions, skipping")
                progress.completed = i + 1
                await self.update_job_progress(job_id, progress)
                continue
            
            # Generate for this course
            try:
                await self.decision_logger.log(
                    component="job_runner",
                    chosen_option="generate_course_mcq",
                    reason=f"Course needs MCQ generation (has {existing_count}, need {self.config.questions_per_course})",
                    context={"course_id": course_id, "course_name": course_name, "existing_count": existing_count},
                    job_id=job_id
                )
                await self._generate_mcq_for_course(job_id, course_id, course_name)
                progress.completed = i + 1
            except Exception as e:
                await self.decision_logger.log(
                    component="job_runner",
                    chosen_option="mark_course_failed",
                    reason=f"Course generation failed: {str(e)[:100]}",
                    context={"course_id": course_id, "error": str(e)[:200]},
                    job_id=job_id
                )
                logger.error(f"Failed to generate MCQ for {course_id}: {e}")
                progress.failed += 1
            
            await self.update_job_progress(job_id, progress)
            
            # Small delay between courses
            await asyncio.sleep(1)
        
        logger.info(f"Bulk MCQ generation completed: {progress.completed}/{progress.total}")
    
    async def _generate_mcq_for_course(self, job_id: str, course_id: str, course_name: str):
        """Generate MCQ questions for a single course - saves after EACH batch with idempotent upserts"""
        import json as json_module
        import hashlib
        
        batch_size = self.config.batch_size
        total_needed = self.config.questions_per_course
        total_batches = (total_needed + batch_size - 1) // batch_size
        
        # Check which batches are already complete by counting questions per batch
        existing_batches = set()
        for b in range(total_batches):
            batch_count = await self.db.mcq_questions.count_documents({
                "course_id": course_id,
                "batch_index": b
            })
            if batch_count >= batch_size - 5:  # Allow some tolerance
                existing_batches.add(b)
        
        start_batch = 0
        for b in range(total_batches):
            if b not in existing_batches:
                start_batch = b
                break
        else:
            # All batches complete
            logger.info(f"[{course_id}] All {total_batches} batches already complete")
            return
        
        if start_batch > 0:
            logger.info(f"[{course_id}] Resuming from batch {start_batch + 1}/{total_batches} (batches {list(existing_batches)} exist)")
        
        # Update progress tracker
        await self.db.bulk_tasks.update_one(
            {"job_id": job_id},
            {"$set": {
                "current_course_id": course_id,
                "current_course_name": course_name,
                "current_batch_index": start_batch,
                "total_batches": total_batches,
                "last_saved_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        
        def generate_batch_sync(batch_num: int) -> str:
            """Synchronous batch generation - runs in thread to avoid blocking event loop"""
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            import asyncio as async_lib
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"mcq_{course_id}_{batch_num}",
                system_message="""You are a medical education expert creating high-quality MCQ questions.
Create questions suitable for medical/pharmacy board exam preparation.
Always return valid JSON array only, no other text."""
            ).with_model("openai", "gpt-5.2")
            
            prompt = f"""Generate {batch_size} multiple-choice questions for:
Course: {course_name}
Batch: {batch_num + 1}/{total_batches}

For each question provide:
1. question: The question text
2. option_a, option_b, option_c, option_d: Four answer options
3. correct_answer: The correct option letter (A, B, C, or D)
4. explanation: Detailed explanation (2-3 sentences)
5. difficulty: easy, medium, or hard

Format as JSON array ONLY, no other text:
[{{"question": "...", "option_a": "...", "option_b": "...", "option_c": "...", "option_d": "...", "correct_answer": "A", "explanation": "...", "difficulty": "medium"}}]

Create clinically relevant questions. Vary difficulty: 30% easy, 50% medium, 20% hard.
Cover different aspects of {course_name}."""

            loop = async_lib.new_event_loop()
            try:
                async_lib.set_event_loop(loop)
                response = loop.run_until_complete(chat.send_message(UserMessage(text=prompt)))
                return response
            finally:
                loop.close()
        
        for batch_num in range(start_batch, total_batches):
            if self._shutdown:
                raise asyncio.CancelledError()
            
            # Skip if batch already exists
            if batch_num in existing_batches:
                logger.info(f"[{course_id}] Batch {batch_num + 1}/{total_batches} already exists, skipping")
                continue
            
            # Update progress tracker
            await self.db.bulk_tasks.update_one(
                {"job_id": job_id},
                {"$set": {
                    "current_batch_index": batch_num,
                    "last_saved_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Yield control frequently to keep server responsive
            await asyncio.sleep(0)
            await asyncio.sleep(0)
            
            # Rate limiting
            await self.rate_limiter.wait()
            
            # Generate batch in thread pool with timeout to prevent blocking
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(generate_batch_sync, batch_num),
                    timeout=300  # 5 minute timeout per batch (OpenAI high latency)
                )
                
                if response:
                    # Parse JSON from response
                    json_start = response.find('[')
                    json_end = response.rfind(']') + 1
                    
                    if json_start >= 0 and json_end > json_start:
                        questions = json_module.loads(response[json_start:json_end])
                        
                        # Add metadata to each question
                        for i, q in enumerate(questions):
                            q["question_id"] = f"q_{course_id}_{batch_num:02d}_{i:03d}"
                            q["course_id"] = course_id
                            q["topic"] = course_name
                            q["created_at"] = datetime.now(timezone.utc).isoformat()
                        
                        # SAVE IMMEDIATELY after each batch
                        if questions:
                            await self.db.mcq_questions.insert_many(questions)
                            logger.info(f"[{course_id}] Batch {batch_num + 1}/{total_batches}: SAVED {len(questions)} questions")
                    else:
                        await self.decision_logger.log(
                            component="content_generator",
                            chosen_option="skip_malformed_batch",
                            reason="LLM response did not contain valid JSON array",
                            context={"course_id": course_id, "batch_num": batch_num},
                            job_id=job_id
                        )
                        logger.warning(f"[{course_id}] Batch {batch_num + 1} - failed to parse JSON")
                        
            except asyncio.TimeoutError:
                await self.decision_logger.log(
                    component="content_generator",
                    chosen_option="timeout_batch",
                    reason=f"Batch timed out after 300s, proceeding to next batch",
                    context={"course_id": course_id, "batch_num": batch_num, "timeout_seconds": 300},
                    job_id=job_id
                )
                logger.warning(f"[{course_id}] Batch {batch_num + 1} timed out")
                    
            except Exception as e:
                await self.decision_logger.log(
                    component="content_generator",
                    chosen_option="skip_failed_batch",
                    reason=f"Batch failed with error, proceeding to next: {str(e)[:100]}",
                    context={"course_id": course_id, "batch_num": batch_num, "error": str(e)[:200]},
                    job_id=job_id
                )
                logger.warning(f"[{course_id}] Batch {batch_num + 1} failed: {e}")
            
            # Yield control to allow other async tasks (including API responses)
            await asyncio.sleep(0.1)
        
        # Log completion
        final_count = await self.db.mcq_questions.count_documents({"course_id": course_id})
        await self.decision_logger.log(
            component="content_generator",
            chosen_option="course_mcq_complete",
            reason=f"Course MCQ generation complete",
            context={"course_id": course_id, "total_questions": final_count},
            job_id=job_id
        )
        logger.info(f"[{course_id}] Complete: {final_count} questions total")
    
    async def _handle_job_failure(self, job: Dict, error: str):
        """Handle job failure with retry logic"""
        job_id = job["job_id"]
        retries = job.get("retries", 0)
        
        if retries < self.config.max_retries:
            # Schedule retry with exponential backoff
            delay = min(
                self.config.retry_base_delay * (2 ** retries),
                self.config.retry_max_delay
            )
            
            await self.db.jobs.update_one(
                {"job_id": job_id},
                {
                    "$set": {
                        "status": JobStatus.QUEUED,
                        "retries": retries + 1,
                        "error": f"Retry {retries + 1}: {error}",
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            logger.info(f"Scheduling retry {retries + 1} for job {job_id} in {delay}s")
            await asyncio.sleep(delay)
            asyncio.create_task(self._process_job(job_id))
        else:
            # Max retries exceeded
            await self.update_job_status(job_id, JobStatus.FAILED, error)
            logger.error(f"Job {job_id} failed after {retries} retries: {error}")
    
    async def get_all_jobs_status(self) -> Dict:
        """Get status summary of all jobs"""
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        result = await self.db.jobs.aggregate(pipeline).to_list(10)
        
        status_counts = {s: 0 for s in JobStatus}
        for r in result:
            if r["_id"] in JobStatus.__members__.values():
                status_counts[r["_id"]] = r["count"]
        
        # Get recent jobs
        recent_jobs = await self.db.jobs.find(
            {},
            {"_id": 0}
        ).sort("updated_at", -1).limit(10).to_list(10)
        
        return {
            "summary": status_counts,
            "recent_jobs": recent_jobs
        }
    
    async def start_script_generation(self, course_id: Optional[str] = None) -> Dict:
        """Start script generation for a single course or all courses."""
        if course_id:
            course = await self.db.courses.find_one({"external_id": course_id}, {"_id": 0})
            if not course:
                raise ValueError(f"Course not found: {course_id}")
            
            job = await self.create_job(
                JobType.SCRIPT_GENERATION,
                {"course_id": course_id, "course_name": course["course_name"]},
                resource_id=f"script_{course_id}"
            )
        else:
            courses = await self.db.courses.find({}, {"_id": 0, "external_id": 1}).to_list(100)
            job = await self.create_job(
                JobType.BULK_SCRIPT,
                {"course_ids": [c["external_id"] for c in courses]},
                resource_id="bulk_script_all"
            )
        
        asyncio.create_task(self._process_job(job["job_id"]))
        return job
    
    async def _run_bulk_script_generation(self, job: Dict):
        """Generate scripts for all modules across all courses"""
        job_id = job["job_id"]
        course_ids = job["params"]["course_ids"]
        
        # Get all modules
        all_modules = await self.db.modules.find(
            {"courseId": {"$in": course_ids}},
            {"_id": 0}
        ).to_list(500)
        
        progress = JobProgress(total=len(all_modules))
        await self.update_job_progress(job_id, progress)
        
        await self.decision_logger.log(
            component="job_runner",
            chosen_option="start_bulk_script",
            reason=f"Starting script generation for {len(all_modules)} modules",
            context={"total_modules": len(all_modules), "courses": len(course_ids)},
            job_id=job_id
        )
        
        for i, module in enumerate(all_modules):
            if self._shutdown:
                raise asyncio.CancelledError()
            
            current_job = await self.get_job(job_id)
            if current_job and current_job["status"] == JobStatus.CANCELLED:
                raise asyncio.CancelledError()
            
            module_id = module.get("module_id")
            module_title = module.get("title", module_id)
            progress.current_item = f"Processing: {module_title}"
            await self.update_job_progress(job_id, progress)
            
            # Check if script already exists
            existing = await self.db.module_scripts.find_one({"module_id": module_id})
            if existing:
                await self.decision_logger.log(
                    component="job_runner",
                    chosen_option="skip_module_script",
                    reason="Script already exists for module",
                    context={"module_id": module_id},
                    job_id=job_id
                )
                progress.completed = i + 1
                await self.update_job_progress(job_id, progress)
                continue
            
            try:
                await self._generate_module_script(job_id, module)
                progress.completed = i + 1
            except Exception as e:
                await self.decision_logger.log(
                    component="job_runner",
                    chosen_option="mark_module_failed",
                    reason=f"Script generation failed: {str(e)[:100]}",
                    context={"module_id": module_id, "error": str(e)[:200]},
                    job_id=job_id
                )
                logger.error(f"Failed to generate script for {module_id}: {e}")
                progress.failed += 1
            
            await self.update_job_progress(job_id, progress)
            await asyncio.sleep(1)
        
        logger.info(f"Bulk script generation completed: {progress.completed}/{progress.total}")
    
    async def _run_single_script_generation(self, job: Dict):
        """Generate scripts for a single course's modules"""
        job_id = job["job_id"]
        course_id = job["params"]["course_id"]
        
        modules = await self.db.modules.find(
            {"courseId": course_id},
            {"_id": 0}
        ).to_list(50)
        
        progress = JobProgress(total=len(modules))
        
        for i, module in enumerate(modules):
            if self._shutdown:
                raise asyncio.CancelledError()
            
            progress.current_item = module.get("title", module.get("module_id"))
            await self.update_job_progress(job_id, progress)
            
            existing = await self.db.module_scripts.find_one({"module_id": module["module_id"]})
            if not existing:
                await self._generate_module_script(job_id, module)
            
            progress.completed = i + 1
            await self.update_job_progress(job_id, progress)
    
    async def _generate_module_script(self, job_id: str, module: Dict):
        """Generate script for a single module using thread pool"""
        import json as json_module
        
        module_id = module.get("module_id")
        module_title = module.get("title", module_id)
        course_id = module.get("courseId")
        topics = module.get("topics", [])
        description = module.get("description", "")
        
        # Get course name for context
        course = await self.db.courses.find_one({"external_id": course_id}, {"_id": 0, "course_name": 1})
        course_name = course.get("course_name", course_id) if course else course_id
        
        def generate_script_sync() -> str:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            import asyncio as async_lib
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"script_{module_id}",
                system_message="""You are an expert medical educator creating video lecture scripts.
Write engaging, educational scripts suitable for text-to-speech avatar presentation.
Target duration: 12 minutes (~1800 words)."""
            ).with_model("openai", "gpt-5.2")
            
            topics_str = ", ".join(topics) if topics else "General topics"
            
            prompt = f"""Create a video lecture script for:
Course: {course_name}
Module: {module_title}
Description: {description}
Topics: {topics_str}
Target Duration: 12 minutes (approximately 1800 words)

Script Requirements:
1. Start with introduction and learning objectives
2. Present content in logical sections with transitions
3. Include clinical examples and case scenarios
4. Use conversational but professional tone
5. Add periodic summaries and key points
6. End with conclusion and key takeaways
7. Include [PAUSE] markers for visual transitions
8. Include [EMPHASIS] markers for key terms

Format with clear section headers."""
            
            loop = async_lib.new_event_loop()
            try:
                async_lib.set_event_loop(loop)
                return loop.run_until_complete(chat.send_message(UserMessage(text=prompt)))
            finally:
                loop.close()
        
        await self.rate_limiter.wait()
        
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(generate_script_sync),
                timeout=300  # 5 minute timeout (OpenAI high latency)
            )
            
            if response:
                word_count = len(response.split())
                duration_minutes = round(word_count / 150, 1)
                
                script_doc = {
                    "script_id": f"script_{uuid.uuid4().hex[:12]}",
                    "module_id": module_id,
                    "course_id": course_id,
                    "script_text": response,
                    "word_count": word_count,
                    "estimated_duration_minutes": duration_minutes,
                    "status": "reviewed",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                await self.db.module_scripts.update_one(
                    {"module_id": module_id},
                    {"$set": script_doc},
                    upsert=True
                )
                
                await self.decision_logger.log(
                    component="content_generator",
                    chosen_option="save_script",
                    reason=f"Generated {word_count} word script (~{duration_minutes} min)",
                    context={"module_id": module_id, "word_count": word_count},
                    job_id=job_id
                )
                logger.info(f"[{module_id}] Generated script: {word_count} words")
                
        except asyncio.TimeoutError:
            await self.decision_logger.log(
                component="content_generator",
                chosen_option="timeout_script",
                reason="Script generation timed out after 180s",
                context={"module_id": module_id},
                job_id=job_id
            )
            raise
        except Exception as e:
            await self.decision_logger.log(
                component="content_generator",
                chosen_option="failed_script",
                reason=f"Script generation failed: {str(e)[:100]}",
                context={"module_id": module_id},
                job_id=job_id
            )
            raise
    
    async def shutdown(self):
        """Graceful shutdown"""
        self._shutdown = True
        if self._executor:
            self._executor.shutdown(wait=False)
            self._executor = None
    
    async def resume_running_jobs(self):
        """Resume any jobs that were running when server restarted"""
        running_jobs = await self.db.jobs.find(
            {"status": {"$in": [JobStatus.RUNNING, JobStatus.QUEUED]}},
            {"_id": 0}
        ).to_list(100)
        
        for job in running_jobs:
            job_id = job["job_id"]
            logger.info(f"Resuming job {job_id} (was {job['status']})")
            
            # Reset status to queued for clean restart
            await self.db.jobs.update_one(
                {"job_id": job_id},
                {"$set": {"status": JobStatus.QUEUED}}
            )
            
            # Release any locks
            if job.get("resource_id"):
                await self.lock_manager.release(job["resource_id"], job_id)
            
            # Restart the job
            asyncio.create_task(self._process_job(job_id))
        
        if running_jobs:
            logger.info(f"Resumed {len(running_jobs)} jobs")


# Singleton instance
_job_runner: Optional[JobRunner] = None


def get_job_runner(db: AsyncIOMotorDatabase) -> JobRunner:
    """Get or create the global job runner instance"""
    global _job_runner
    if _job_runner is None:
        _job_runner = JobRunner(db)
    return _job_runner


async def init_job_runner(db: AsyncIOMotorDatabase):
    """Initialize job runner and resume any interrupted jobs"""
    runner = get_job_runner(db)
    await runner.resume_running_jobs()
    return runner
