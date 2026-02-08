"""
Full Course Pipeline - End-to-End Course Generation
1. Generate 200 MCQ questions
2. Verify quality (no duplicates, balanced distribution)
3. Generate avatar scripts (if not exist)
4. Generate avatar videos with Sora 2
"""

import os
import asyncio
import logging
import json
import random
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

QUESTIONS_PER_COURSE = 200
BATCH_SIZE = 25


class FullCoursePipeline:
    """Complete course generation pipeline"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        self._shutdown = False
    
    async def process_single_course(self, course_id: str) -> Dict:
        """
        Process a single course end-to-end:
        1. MCQ generation + verification
        2. Script generation
        3. Video generation
        """
        # Get course info
        course = await self.db.courses.find_one({"external_id": course_id}, {"_id": 0})
        if not course:
            return {"error": f"Course {course_id} not found"}
        
        course_name = course["course_name"]
        logger.info(f"🎯 Starting full pipeline for: {course_name}")
        
        result = {
            "course_id": course_id,
            "course_name": course_name,
            "steps": {}
        }
        
        # Step 1: MCQ Generation
        logger.info(f"📝 Step 1: MCQ Generation")
        mcq_result = await self._generate_mcq(course_id, course_name)
        result["steps"]["mcq"] = mcq_result
        
        if not mcq_result.get("success"):
            return result
        
        # Step 2: Script Generation
        logger.info(f"📜 Step 2: Script Generation")
        script_result = await self._generate_scripts(course_id, course_name)
        result["steps"]["scripts"] = script_result
        
        # Step 3: Video Generation
        logger.info(f"🎬 Step 3: Video Generation")
        video_result = await self._generate_videos(course_id)
        result["steps"]["videos"] = video_result
        
        result["success"] = True
        logger.info(f"✅ Pipeline complete for: {course_name}")
        
        return result
    
    async def _generate_mcq(self, course_id: str, course_name: str) -> Dict:
        """Generate and verify MCQ questions - COMPLETES missing, doesn't delete"""
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        # Check existing
        existing = await self.db.mcq_questions.count_documents({"course_id": course_id})
        
        if existing >= QUESTIONS_PER_COURSE:
            # Verify distribution
            is_valid = await self._verify_distribution(course_id)
            if is_valid:
                return {"success": True, "count": existing, "message": "Already complete"}
            else:
                # Fix distribution by reshuffling
                await self._reshuffle_all(course_id)
                return {"success": True, "count": existing, "message": "Reshuffled for balance"}
        
        # Calculate how many more needed
        needed = QUESTIONS_PER_COURSE - existing
        batches_needed = (needed + BATCH_SIZE - 1) // BATCH_SIZE
        start_batch = existing // BATCH_SIZE
        total_batches = start_batch + batches_needed
        
        logger.info(f"[{course_id}] Have {existing}, need {needed} more questions ({batches_needed} batches)")
        
        total_saved = 0
        
        def generate_sync(batch_num: int) -> str:
            import asyncio as aio
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"mcq_{course_id}_{batch_num}",
                system_message="""You are a medical education expert creating MCQ questions.
CRITICAL: Distribute correct answers EVENLY - about 6-7 each for A, B, C, D per batch.
Return valid JSON array only."""
            ).with_model("openai", "gpt-4o-mini")
            
            prompt = f"""Generate {BATCH_SIZE} MCQ questions for: {course_name}

IMPORTANT: Distribute correct answers evenly (6-7 each for A, B, C, D)

Format as JSON array:
[{{"question": "...", "option_a": "...", "option_b": "...", "option_c": "...", "option_d": "...", "correct_answer": "A/B/C/D", "explanation": "...", "difficulty": "easy/medium/hard"}}]"""

            loop = aio.new_event_loop()
            try:
                aio.set_event_loop(loop)
                return loop.run_until_complete(chat.send_message(UserMessage(text=prompt)))
            finally:
                loop.close()
        
        for batch_num in range(start_batch, total_batches):
            if self._shutdown:
                break
            
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(generate_sync, batch_num),
                    timeout=120
                )
                
                json_start = response.find('[')
                json_end = response.rfind(']') + 1
                
                if json_start >= 0 and json_end > json_start:
                    questions = json.loads(response[json_start:json_end])
                    
                    saved = 0
                    for i, q in enumerate(questions):
                        # Check duplicate
                        exists = await self.db.mcq_questions.find_one({
                            "course_id": course_id,
                            "question": q.get("question")
                        })
                        if exists:
                            continue
                        
                        # Shuffle options
                        q = self._shuffle_options(q)
                        
                        q["question_id"] = f"q_{course_id}_b{batch_num:02d}_i{i:03d}"
                        q["course_id"] = course_id
                        q["topic"] = course_name
                        q["created_at"] = datetime.now(timezone.utc).isoformat()
                        
                        await self.db.mcq_questions.insert_one(q)
                        saved += 1
                    
                    total_saved += saved
                    logger.info(f"[{course_id}] Batch {batch_num+1}/{total_batches}: {saved} questions")
                    
            except Exception as e:
                logger.warning(f"[{course_id}] Batch {batch_num+1} error: {e}")
            
            await asyncio.sleep(0.5)
        
        # Verify
        is_valid = await self._verify_distribution(course_id)
        final_count = await self.db.mcq_questions.count_documents({"course_id": course_id})
        
        return {
            "success": is_valid and final_count >= QUESTIONS_PER_COURSE,
            "count": final_count,
            "verified": is_valid
        }
    
    async def _reshuffle_all(self, course_id: str):
        """Reshuffle all questions for better distribution"""
        questions = await self.db.mcq_questions.find({"course_id": course_id}).to_list(300)
        for q in questions:
            shuffled = self._shuffle_options(q)
            await self.db.mcq_questions.update_one(
                {"_id": q["_id"]},
                {"$set": {
                    "option_a": shuffled["option_a"],
                    "option_b": shuffled["option_b"],
                    "option_c": shuffled["option_c"],
                    "option_d": shuffled["option_d"],
                    "correct_answer": shuffled["correct_answer"]
                }}
            )
        logger.info(f"[{course_id}] Reshuffled {len(questions)} questions")
    
    def _shuffle_options(self, q: Dict) -> Dict:
        """Shuffle answer options"""
        opts = [q.get("option_a"), q.get("option_b"), q.get("option_c"), q.get("option_d")]
        correct = q.get("correct_answer", "A").upper()
        
        if correct not in ['A','B','C','D'] or not all(opts):
            return q
        
        correct_idx = {'A':0,'B':1,'C':2,'D':3}[correct]
        correct_text = opts[correct_idx]
        
        random.shuffle(opts)
        new_idx = opts.index(correct_text)
        
        q["option_a"], q["option_b"], q["option_c"], q["option_d"] = opts
        q["correct_answer"] = ['A','B','C','D'][new_idx]
        return q
    
    async def _verify_distribution(self, course_id: str) -> bool:
        """Verify answer distribution is balanced"""
        total = await self.db.mcq_questions.count_documents({"course_id": course_id})
        if total < QUESTIONS_PER_COURSE:
            return False
        
        dist = await self.db.mcq_questions.aggregate([
            {"$match": {"course_id": course_id}},
            {"$group": {"_id": "$correct_answer", "count": {"$sum": 1}}}
        ]).to_list(10)
        
        for d in dist:
            pct = (d["count"] / total) * 100
            if pct < 15 or pct > 35:  # Allow 15-35% range
                return False
        
        return True
    
    async def _generate_scripts(self, course_id: str, course_name: str) -> Dict:
        """Generate avatar scripts for modules"""
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        modules = await self.db.modules.find({"courseId": course_id}, {"_id": 0}).to_list(20)
        
        generated = 0
        for module in modules:
            module_id = module.get("module_id")
            
            # Check if exists
            existing = await self.db.module_scripts.find_one({"module_id": module_id})
            if existing:
                generated += 1
                continue
            
            def gen_script_sync():
                import asyncio as aio
                
                chat = LlmChat(
                    api_key=self.api_key,
                    session_id=f"script_{module_id}",
                    system_message="Create a 12-minute educational video script for medical students."
                ).with_model("openai", "gpt-4o-mini")
                
                prompt = f"""Create a video lecture script for:
Course: {course_name}
Module: {module.get('title', module_id)}
Duration: ~12 minutes (~1800 words)

Include:
- Introduction with learning objectives
- Main content with clinical examples
- [PAUSE] markers for transitions
- Summary and key takeaways"""

                loop = aio.new_event_loop()
                try:
                    aio.set_event_loop(loop)
                    return loop.run_until_complete(chat.send_message(UserMessage(text=prompt)))
                finally:
                    loop.close()
            
            try:
                script_text = await asyncio.wait_for(
                    asyncio.to_thread(gen_script_sync),
                    timeout=120
                )
                
                await self.db.module_scripts.update_one(
                    {"module_id": module_id},
                    {"$set": {
                        "script_id": f"script_{uuid.uuid4().hex[:8]}",
                        "module_id": module_id,
                        "course_id": course_id,
                        "script_text": script_text,
                        "word_count": len(script_text.split()),
                        "status": "ready",
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }},
                    upsert=True
                )
                generated += 1
                logger.info(f"[{module_id}] Script generated")
                
            except Exception as e:
                logger.warning(f"[{module_id}] Script error: {e}")
        
        return {"success": True, "generated": generated, "total": len(modules)}
    
    async def _generate_videos(self, course_id: str) -> Dict:
        """Generate avatar videos with Sora 2"""
        from emergentintegrations.llm.video import generate_video
        
        scripts = await self.db.module_scripts.find(
            {"course_id": course_id},
            {"_id": 0}
        ).to_list(20)
        
        generated = 0
        for script in scripts:
            module_id = script.get("module_id")
            
            # Check if video exists
            existing = await self.db.module_videos.find_one({"module_id": module_id})
            if existing and existing.get("status") == "completed":
                generated += 1
                continue
            
            # Get first 500 chars of script for video prompt
            script_text = script.get("script_text", "")[:500]
            
            try:
                logger.info(f"[{module_id}] Generating video...")
                
                # Generate video with Sora 2
                video_url = await generate_video(
                    api_key=self.api_key,
                    prompt=f"Educational medical lecture video. Professional presenter explaining: {script_text}",
                    duration=10  # 10 seconds for demo
                )
                
                await self.db.module_videos.update_one(
                    {"module_id": module_id},
                    {"$set": {
                        "video_id": f"video_{uuid.uuid4().hex[:8]}",
                        "module_id": module_id,
                        "course_id": course_id,
                        "video_url": video_url,
                        "status": "completed",
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }},
                    upsert=True
                )
                generated += 1
                logger.info(f"[{module_id}] Video generated: {video_url}")
                
            except Exception as e:
                logger.warning(f"[{module_id}] Video error: {e}")
                await self.db.module_videos.update_one(
                    {"module_id": module_id},
                    {"$set": {
                        "module_id": module_id,
                        "course_id": course_id,
                        "status": "failed",
                        "error": str(e),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }},
                    upsert=True
                )
        
        return {"success": True, "generated": generated, "total": len(scripts)}
    
    def cancel(self):
        self._shutdown = True


# Singleton
_pipeline = None

def get_pipeline(db: AsyncIOMotorDatabase) -> FullCoursePipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = FullCoursePipeline(db)
    return _pipeline
