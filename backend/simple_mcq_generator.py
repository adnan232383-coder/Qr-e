"""
Simple MCQ Generator - One course at a time, ensures 200+ before moving on
"""

import os
import asyncio
import logging
import json
import random
import uuid
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

QUESTIONS_PER_COURSE = 200
BATCH_SIZE = 25


class SimpleMCQGenerator:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        self._stop = False
    
    async def generate_all_courses(self, university_filter: str = None):
        """Generate MCQ for courses. If university_filter is set, only process those courses."""
        # Default: only UG courses (skip NVU Medicine - user provides those manually)
        query = {}
        if university_filter:
            query["external_id"] = {"$regex": f"^{university_filter}"}
        else:
            # By default, generate for UG only (skip NVU Medicine)
            query["$or"] = [
                {"external_id": {"$regex": "^UG_"}},
                {"university_id": "NVU", "program": {"$in": ["Dentistry", "Pharmacy"]}}
            ]
        
        courses = await self.db.courses.find(
            query, {"_id": 0, "external_id": 1, "course_name": 1, "university_id": 1, "program": 1}
        ).sort("external_id", 1).to_list(200)
        
        job_id = f"simple_mcq_{uuid.uuid4().hex[:8]}"
        await self.db.jobs.insert_one({
            "job_id": job_id,
            "job_type": "simple_mcq",
            "status": "running",
            "total": len(courses),
            "completed": 0,
            "current": None,
            "started_at": datetime.now(timezone.utc).isoformat()
        })
        
        completed = 0
        for course in courses:
            if self._stop:
                break
            
            cid = course["external_id"]
            cname = course["course_name"]
            
            await self.db.jobs.update_one(
                {"job_id": job_id},
                {"$set": {"current": cname}}
            )
            
            logger.info(f"📚 Starting: {cname}")
            
            # Generate until we have 200+
            success = await self._ensure_200_questions(cid, cname)
            
            if success:
                completed += 1
                await self.db.jobs.update_one(
                    {"job_id": job_id},
                    {"$set": {"completed": completed}}
                )
                logger.info(f"✅ Completed {completed}/{len(courses)}: {cname}")
            else:
                logger.warning(f"⚠️ Failed: {cname}")
        
        await self.db.jobs.update_one(
            {"job_id": job_id},
            {"$set": {"status": "done" if not self._stop else "cancelled"}}
        )
        
        return {"completed": completed, "total": len(courses)}
    
    async def _ensure_200_questions(self, course_id: str, course_name: str) -> bool:
        """Keep generating until we have 200+ questions"""
        max_attempts = 20
        
        for attempt in range(max_attempts):
            if self._stop:
                return False
            
            count = await self.db.mcq_questions.count_documents({"course_id": course_id})
            
            if count >= QUESTIONS_PER_COURSE:
                # Verify and mark complete
                await self.db.courses.update_one(
                    {"external_id": course_id},
                    {"$set": {"mcq_verified": True, "mcq_count": count}}
                )
                return True
            
            needed = QUESTIONS_PER_COURSE - count
            logger.info(f"[{course_id}] Have {count}, need {needed} more")
            
            # Generate a batch
            await self._generate_batch(course_id, course_name)
            
            await asyncio.sleep(1)
        
        return False
    
    async def _generate_batch(self, course_id: str, course_name: str):
        """Generate one batch of questions"""
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        def gen_sync():
            import asyncio as aio
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"mcq_{course_id}_{uuid.uuid4().hex[:4]}",
                system_message="Create MCQ questions. Return JSON array only."
            ).with_model("openai", "gpt-4o-mini")
            
            prompt = f"""Generate {BATCH_SIZE} MCQ questions for medical course: {course_name}

Return JSON array:
[{{"question": "...", "option_a": "...", "option_b": "...", "option_c": "...", "option_d": "...", "correct_answer": "A/B/C/D", "explanation": "..."}}]

IMPORTANT: Distribute correct answers evenly across A, B, C, D."""

            loop = aio.new_event_loop()
            try:
                aio.set_event_loop(loop)
                return loop.run_until_complete(chat.send_message(UserMessage(text=prompt)))
            finally:
                loop.close()
        
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(gen_sync),
                timeout=120
            )
            
            # Parse JSON
            start = response.find('[')
            end = response.rfind(']') + 1
            
            if start >= 0 and end > start:
                questions = json.loads(response[start:end])
                
                saved = 0
                for q in questions:
                    # Check duplicate
                    exists = await self.db.mcq_questions.find_one({
                        "course_id": course_id,
                        "question": q.get("question")
                    })
                    if exists:
                        continue
                    
                    # Shuffle answers
                    q = self._shuffle(q)
                    
                    q["question_id"] = f"q_{uuid.uuid4().hex[:12]}"
                    q["course_id"] = course_id
                    q["created_at"] = datetime.now(timezone.utc).isoformat()
                    
                    await self.db.mcq_questions.insert_one(q)
                    saved += 1
                
                logger.info(f"[{course_id}] Saved {saved} questions")
                
        except Exception as e:
            logger.warning(f"[{course_id}] Batch error: {e}")
    
    def _shuffle(self, q):
        opts = [q.get("option_a"), q.get("option_b"), q.get("option_c"), q.get("option_d")]
        correct = q.get("correct_answer", "A").upper()
        
        if correct not in ['A','B','C','D'] or not all(opts):
            return q
        
        idx = {'A':0,'B':1,'C':2,'D':3}[correct]
        correct_text = opts[idx]
        
        random.shuffle(opts)
        new_idx = opts.index(correct_text)
        
        q["option_a"], q["option_b"], q["option_c"], q["option_d"] = opts
        q["correct_answer"] = ['A','B','C','D'][new_idx]
        return q
    
    def stop(self):
        self._stop = True


_generator = None

def get_simple_generator(db):
    global _generator
    if _generator is None:
        _generator = SimpleMCQGenerator(db)
    return _generator
