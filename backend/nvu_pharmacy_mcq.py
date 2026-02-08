"""
NVU Pharmacy MCQ Generator - Background Script
Run with: python3 nvu_pharmacy_mcq.py &
"""

import asyncio
import json
import random
import uuid
import os
import logging
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

QUESTIONS_PER_COURSE = 200
BATCH_SIZE = 25

async def generate_nvu_pharmacy():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client['test_database']
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    
    courses = await db.courses.find(
        {"university_id": "NVU", "program": "Pharmacy"},
        {"_id": 0}
    ).to_list(20)
    
    logger.info(f"Starting NVU Pharmacy MCQ: {len(courses)} courses")
    
    job_id = f"nvu_pharm_{uuid.uuid4().hex[:8]}"
    await db.jobs.insert_one({
        "job_id": job_id,
        "job_type": "nvu_pharmacy_mcq",
        "status": "running",
        "total": len(courses),
        "completed": 0,
        "started_at": datetime.now(timezone.utc).isoformat()
    })
    
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    for idx, course in enumerate(courses):
        cid = course["external_id"]
        cname = course["course_name"]
        
        logger.info(f"[{idx+1}/{len(courses)}] {cname}")
        
        existing = await db.mcq_questions.count_documents({"course_id": cid})
        
        while existing < QUESTIONS_PER_COURSE:
            def gen_sync():
                import asyncio as aio
                chat = LlmChat(
                    api_key=api_key,
                    session_id=f"nvu_{cid}_{uuid.uuid4().hex[:4]}",
                    system_message="Create pharmacy MCQ. Return JSON array only."
                ).with_model("openai", "gpt-4o-mini")
                
                prompt = f"""Generate {BATCH_SIZE} MCQ for Pharmacy: {cname}

Return JSON:
[{{"question": "...", "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}}, "correct_answer": "A/B/C/D", "difficulty": "easy/medium/hard", "explanation": "..."}}]

Distribute answers evenly across A,B,C,D."""

                loop = aio.new_event_loop()
                try:
                    aio.set_event_loop(loop)
                    return loop.run_until_complete(chat.send_message(UserMessage(text=prompt)))
                finally:
                    loop.close()
            
            try:
                response = await asyncio.wait_for(asyncio.to_thread(gen_sync), timeout=120)
                
                start = response.find('[')
                end = response.rfind(']') + 1
                
                if start >= 0 and end > start:
                    questions = json.loads(response[start:end])
                    
                    for q in questions:
                        exists = await db.mcq_questions.find_one({
                            "course_id": cid, "question": q.get("question")
                        })
                        if exists:
                            continue
                        
                        opts = q.get("options", {})
                        correct = q.get("correct_answer", "A")
                        if opts and correct in opts:
                            items = list(opts.items())
                            correct_text = opts[correct]
                            random.shuffle(items)
                            new_opts = dict(items)
                            new_correct = [k for k, v in new_opts.items() if v == correct_text][0]
                            q["options"] = new_opts
                            q["correct_answer"] = new_correct
                        
                        q["question_id"] = f"q_{uuid.uuid4().hex[:12]}"
                        q["course_id"] = cid
                        q["university_id"] = "NVU"
                        q["created_at"] = datetime.now(timezone.utc).isoformat()
                        
                        await db.mcq_questions.insert_one(q)
                        existing += 1
                    
                    logger.info(f"  {existing}/{QUESTIONS_PER_COURSE}")
                    
            except Exception as e:
                logger.warning(f"  Error: {e}")
            
            await asyncio.sleep(2)
        
        await db.jobs.update_one({"job_id": job_id}, {"$set": {"completed": idx + 1}})
    
    await db.jobs.update_one({"job_id": job_id}, {"$set": {"status": "done"}})
    logger.info("NVU Pharmacy Complete!")
    client.close()

if __name__ == "__main__":
    asyncio.run(generate_nvu_pharmacy())
