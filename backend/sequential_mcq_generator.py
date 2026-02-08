"""
Sequential MCQ Generator - Course-by-Course with Quality Verification

Process:
1. Process ONE course at a time
2. Generate all 200 questions for that course
3. Verify quality:
   - Total count >= 200
   - Answer distribution balanced (A, B, C, D each ~25%)
4. Only after passing verification, move to next course

No avatars/videos - MCQ only.
"""

import os
import uuid
import asyncio
import logging
import json
import random
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from decision_logger import get_decision_logger

logger = logging.getLogger(__name__)

# Configuration
QUESTIONS_PER_COURSE = 200
BATCH_SIZE = 25
MAX_RETRIES_PER_BATCH = 3
MIN_DISTRIBUTION_PERCENT = 20  # Each answer option should be at least 20%
MAX_DISTRIBUTION_PERCENT = 30  # Each answer option should be at most 30%


class SequentialMCQGenerator:
    """
    Generates MCQs course-by-course with quality verification.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        self.decision_logger = get_decision_logger(db)
        self._shutdown = False
        self._current_job_id = None
    
    async def start_sequential_generation(self) -> Dict:
        """Start sequential MCQ generation for all courses"""
        job_id = f"seq_mcq_{uuid.uuid4().hex[:8]}"
        self._current_job_id = job_id
        
        # Get all courses
        courses = await self.db.courses.find(
            {}, 
            {"_id": 0, "external_id": 1, "course_name": 1}
        ).sort("external_id", 1).to_list(100)
        
        # Create job record
        job = {
            "job_id": job_id,
            "job_type": "sequential_mcq",
            "status": "running",
            "total_courses": len(courses),
            "completed_courses": 0,
            "current_course": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await self.db.jobs.insert_one(job)
        
        logger.info(f"Starting sequential MCQ generation: {len(courses)} courses")
        
        # Start processing in background
        asyncio.create_task(self._process_all_courses(job_id, courses))
        
        return {"job_id": job_id, "total_courses": len(courses), "status": "started"}
    
    async def _process_all_courses(self, job_id: str, courses: List[Dict]):
        """Process all courses sequentially"""
        completed = 0
        
        for course in courses:
            if self._shutdown:
                break
            
            # Check if job was cancelled
            job = await self.db.jobs.find_one({"job_id": job_id})
            if job and job.get("status") == "cancelled":
                logger.info(f"Job {job_id} was cancelled")
                break
            
            course_id = course["external_id"]
            course_name = course["course_name"]
            
            # Update current course
            await self.db.jobs.update_one(
                {"job_id": job_id},
                {"$set": {
                    "current_course": course_name,
                    "current_course_id": course_id,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Process this course completely
            success = await self._process_single_course(job_id, course_id, course_name)
            
            if success:
                completed += 1
                await self.db.jobs.update_one(
                    {"job_id": job_id},
                    {"$set": {
                        "completed_courses": completed,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                logger.info(f"✅ Course {completed}/{len(courses)} complete: {course_name}")
            else:
                logger.warning(f"⚠️ Course failed verification: {course_name}")
        
        # Mark job complete
        final_status = "done" if not self._shutdown else "cancelled"
        await self.db.jobs.update_one(
            {"job_id": job_id},
            {"$set": {
                "status": final_status,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        logger.info(f"Sequential MCQ generation complete: {completed}/{len(courses)} courses")
    
    async def _process_single_course(self, job_id: str, course_id: str, course_name: str) -> bool:
        """
        Process a single course end-to-end:
        1. Check existing questions
        2. Generate missing questions
        3. Verify quality
        4. Return True only if verified
        """
        logger.info(f"📚 Processing: {course_name} ({course_id})")
        
        # Check existing questions
        existing_count = await self.db.mcq_questions.count_documents({"course_id": course_id})
        
        if existing_count >= QUESTIONS_PER_COURSE:
            # Already has enough questions, verify distribution
            is_valid = await self._verify_course_quality(course_id, course_name)
            if is_valid:
                logger.info(f"✅ {course_name}: Already complete and verified ({existing_count} questions)")
                return True
            else:
                # Has questions but distribution is bad - need to regenerate
                logger.warning(f"⚠️ {course_name}: Has {existing_count} questions but failed verification - regenerating")
                await self.db.mcq_questions.delete_many({"course_id": course_id})
                existing_count = 0
        
        # Generate questions in batches
        total_batches = (QUESTIONS_PER_COURSE + BATCH_SIZE - 1) // BATCH_SIZE
        
        for batch_num in range(total_batches):
            if self._shutdown:
                return False
            
            # Check current count
            current_count = await self.db.mcq_questions.count_documents({"course_id": course_id})
            if current_count >= QUESTIONS_PER_COURSE:
                break
            
            # Generate batch
            await self._generate_batch(job_id, course_id, course_name, batch_num, total_batches)
            
            # Small delay between batches
            await asyncio.sleep(0.5)
        
        # Final verification
        is_valid = await self._verify_course_quality(course_id, course_name)
        
        if is_valid:
            # Mark course as verified in DB
            await self.db.courses.update_one(
                {"external_id": course_id},
                {"$set": {
                    "mcq_verified": True,
                    "mcq_verified_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        
        return is_valid
    
    async def _generate_batch(self, job_id: str, course_id: str, course_name: str, batch_num: int, total_batches: int):
        """Generate a single batch of MCQ questions - runs LLM call in separate thread"""
        
        def generate_sync():
            """Synchronous LLM call to run in thread"""
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            import asyncio as aio
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"mcq_{course_id}_{batch_num}",
                system_message="""You are a medical education expert creating high-quality MCQ questions.
Create questions suitable for medical/dental/pharmacy board exam preparation.
IMPORTANT: Distribute correct answers EVENLY across A, B, C, D (about 6-7 of each per batch).
Always return valid JSON array only, no other text."""
            ).with_model("openai", "gpt-4o-mini")
            
            prompt = f"""Generate {BATCH_SIZE} multiple-choice questions for:
Course: {course_name}
Batch: {batch_num + 1}/{total_batches}

CRITICAL: Distribute correct answers evenly:
- About 6-7 questions should have correct answer A
- About 6-7 questions should have correct answer B  
- About 6-7 questions should have correct answer C
- About 6-7 questions should have correct answer D

For each question provide:
1. question: The question text
2. option_a, option_b, option_c, option_d: Four answer options
3. correct_answer: VARY THIS - use A, B, C, D evenly distributed
4. explanation: Detailed explanation (2-3 sentences)
5. difficulty: easy, medium, or hard

Format as JSON array ONLY:
[{{"question": "...", "option_a": "...", "option_b": "...", "option_c": "...", "option_d": "...", "correct_answer": "B", "explanation": "...", "difficulty": "medium"}}]

Vary difficulty: 30% easy, 50% medium, 20% hard.
Make questions clinically relevant for {course_name}."""

            # Run async in new event loop
            loop = aio.new_event_loop()
            try:
                aio.set_event_loop(loop)
                return loop.run_until_complete(chat.send_message(UserMessage(text=prompt)))
            finally:
                loop.close()
        
        for retry in range(MAX_RETRIES_PER_BATCH):
            try:
                # Run in thread to not block event loop
                response = await asyncio.wait_for(
                    asyncio.to_thread(generate_sync),
                    timeout=300  # 5 min timeout
                )
                
                # Parse JSON
                json_start = response.find('[')
                json_end = response.rfind(']') + 1
                
                if json_start >= 0 and json_end > json_start:
                    questions = json.loads(response[json_start:json_end])
                    
                    # Process and shuffle each question
                    saved = 0
                    skipped_duplicates = 0
                    
                    for i, q in enumerate(questions):
                        # Check for duplicate question text
                        existing = await self.db.mcq_questions.find_one({
                            "course_id": course_id,
                            "question": q.get("question")
                        })
                        
                        if existing:
                            skipped_duplicates += 1
                            continue  # Skip duplicate
                        
                        # Shuffle options for random distribution
                        q = self._shuffle_options(q)
                        
                        q["question_id"] = f"q_{course_id}_b{batch_num:02d}_i{i:03d}"
                        q["course_id"] = course_id
                        q["batch_index"] = batch_num
                        q["topic"] = course_name
                        q["created_at"] = datetime.now(timezone.utc).isoformat()
                        
                        # Upsert to avoid duplicates
                        await self.db.mcq_questions.update_one(
                            {"question_id": q["question_id"]},
                            {"$set": q},
                            upsert=True
                        )
                        saved += 1
                    
                    log_msg = f"[{course_id}] Batch {batch_num + 1}/{total_batches}: Saved {saved} questions"
                    if skipped_duplicates > 0:
                        log_msg += f" (skipped {skipped_duplicates} duplicates)"
                    logger.info(log_msg)
                    return  # Success
                    
            except asyncio.TimeoutError:
                logger.warning(f"[{course_id}] Batch {batch_num + 1} timeout (retry {retry + 1})")
            except Exception as e:
                logger.warning(f"[{course_id}] Batch {batch_num + 1} error (retry {retry + 1}): {e}")
            
            await asyncio.sleep(2 ** retry)  # Exponential backoff
    
    def _shuffle_options(self, question: Dict) -> Dict:
        """Shuffle answer options to ensure random distribution"""
        opts = [
            question.get("option_a"),
            question.get("option_b"),
            question.get("option_c"),
            question.get("option_d")
        ]
        
        correct_letter = question.get("correct_answer", "A").upper()
        if correct_letter not in ['A', 'B', 'C', 'D'] or not all(opts):
            return question
        
        # Find correct answer text
        correct_idx = {'A': 0, 'B': 1, 'C': 2, 'D': 3}[correct_letter]
        correct_text = opts[correct_idx]
        
        # Shuffle options
        random.shuffle(opts)
        
        # Find new position of correct answer
        new_idx = opts.index(correct_text)
        
        # Update question
        question["option_a"] = opts[0]
        question["option_b"] = opts[1]
        question["option_c"] = opts[2]
        question["option_d"] = opts[3]
        question["correct_answer"] = ['A', 'B', 'C', 'D'][new_idx]
        
        return question
    
    async def _verify_course_quality(self, course_id: str, course_name: str) -> bool:
        """
        Verify course MCQ quality:
        1. Total count >= 200
        2. Answer distribution balanced (each option 20-30%)
        
        Returns True if verified, False if needs regeneration.
        """
        # Count total questions
        total = await self.db.mcq_questions.count_documents({"course_id": course_id})
        
        if total < QUESTIONS_PER_COURSE:
            logger.warning(f"❌ {course_name}: Only {total} questions (need {QUESTIONS_PER_COURSE})")
            return False
        
        # Check answer distribution
        pipeline = [
            {"$match": {"course_id": course_id}},
            {"$group": {"_id": "$correct_answer", "count": {"$sum": 1}}}
        ]
        distribution = await self.db.mcq_questions.aggregate(pipeline).to_list(10)
        
        dist_map = {d["_id"]: d["count"] for d in distribution}
        
        # Calculate percentages
        percentages = {}
        for letter in ['A', 'B', 'C', 'D']:
            count = dist_map.get(letter, 0)
            pct = (count / total) * 100 if total > 0 else 0
            percentages[letter] = pct
        
        # Log distribution
        dist_str = ", ".join([f"{k}: {v:.1f}%" for k, v in percentages.items()])
        logger.info(f"📊 {course_name} distribution: {dist_str}")
        
        # Check if balanced (each should be 20-30%)
        for letter, pct in percentages.items():
            if pct < MIN_DISTRIBUTION_PERCENT or pct > MAX_DISTRIBUTION_PERCENT:
                logger.warning(f"❌ {course_name}: Answer {letter} is {pct:.1f}% (should be {MIN_DISTRIBUTION_PERCENT}-{MAX_DISTRIBUTION_PERCENT}%)")
                
                # Try to fix by reshuffling
                fixed = await self._fix_distribution(course_id, course_name)
                return fixed
        
        logger.info(f"✅ {course_name}: Verified - {total} questions, balanced distribution")
        return True
    
    async def _fix_distribution(self, course_id: str, course_name: str) -> bool:
        """
        Try to fix unbalanced distribution by reshuffling all questions.
        """
        logger.info(f"🔧 {course_name}: Attempting to fix distribution by reshuffling...")
        
        # Get all questions for this course
        questions = await self.db.mcq_questions.find({"course_id": course_id}).to_list(300)
        
        if not questions:
            return False
        
        # Reshuffle each question
        for q in questions:
            shuffled = self._shuffle_options(q)
            await self.db.mcq_questions.update_one(
                {"_id": q["_id"]},
                {"$set": {
                    "option_a": shuffled["option_a"],
                    "option_b": shuffled["option_b"],
                    "option_c": shuffled["option_c"],
                    "option_d": shuffled["option_d"],
                    "correct_answer": shuffled["correct_answer"],
                    "reshuffled_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        
        # Re-verify
        return await self._verify_distribution_only(course_id, course_name)
    
    async def _verify_distribution_only(self, course_id: str, course_name: str) -> bool:
        """Quick distribution check without count check"""
        total = await self.db.mcq_questions.count_documents({"course_id": course_id})
        
        pipeline = [
            {"$match": {"course_id": course_id}},
            {"$group": {"_id": "$correct_answer", "count": {"$sum": 1}}}
        ]
        distribution = await self.db.mcq_questions.aggregate(pipeline).to_list(10)
        
        dist_map = {d["_id"]: d["count"] for d in distribution}
        
        for letter in ['A', 'B', 'C', 'D']:
            count = dist_map.get(letter, 0)
            pct = (count / total) * 100 if total > 0 else 0
            if pct < MIN_DISTRIBUTION_PERCENT or pct > MAX_DISTRIBUTION_PERCENT:
                return False
        
        return True
    
    async def get_status(self) -> Dict:
        """Get current generation status"""
        # Find active job
        job = await self.db.jobs.find_one(
            {"job_type": "sequential_mcq", "status": "running"},
            {"_id": 0}
        )
        
        if not job:
            job = await self.db.jobs.find_one(
                {"job_type": "sequential_mcq"},
                {"_id": 0},
                sort=[("created_at", -1)]
            )
        
        # Get overall stats
        total_mcq = await self.db.mcq_questions.count_documents({})
        verified_courses = await self.db.courses.count_documents({"mcq_verified": True})
        total_courses = await self.db.courses.count_documents({})
        
        return {
            "job": job,
            "total_mcq": total_mcq,
            "verified_courses": verified_courses,
            "total_courses": total_courses
        }
    
    def cancel(self):
        """Cancel current generation"""
        self._shutdown = True


# Singleton instance
_generator: Optional[SequentialMCQGenerator] = None


def get_sequential_generator(db: AsyncIOMotorDatabase) -> SequentialMCQGenerator:
    """Get or create the generator instance"""
    global _generator
    if _generator is None:
        _generator = SequentialMCQGenerator(db)
    return _generator
