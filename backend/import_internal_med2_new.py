import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from datetime import datetime, timezone
import json

COURSE_ID = "NVU_MD_Y3_S2_C29"  # Internal Medicine II

async def main():
    with open('/app/internal_med2_batch1.json', 'r') as f:
        questions_data = json.load(f)
    
    print(f"Loaded {len(questions_data)} questions from JSON file")
    
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    
    current_count = await db.mcq_questions.count_documents({"course_id": COURSE_ID})
    print(f"Current questions for Internal Medicine II: {current_count}")
    
    questions_to_insert = []
    for q in questions_data:
        question_doc = {
            "question_id": f"q_{uuid.uuid4().hex[:12]}",
            "course_id": COURSE_ID,
            "question": q["question"],
            "option_a": q["option_a"],
            "option_b": q["option_b"],
            "option_c": q["option_c"],
            "option_d": q["option_d"],
            "correct_answer": q["correct_answer"],
            "explanation": q["explanation"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        questions_to_insert.append(question_doc)
    
    result = await db.mcq_questions.insert_many(questions_to_insert)
    print(f"Inserted: {len(result.inserted_ids)} questions")
    
    new_count = await db.mcq_questions.count_documents({"course_id": COURSE_ID})
    await db.courses.update_one(
        {"external_id": COURSE_ID},
        {"$set": {"mcq_count": new_count, "mcq_verified": True}}
    )
    print(f"Total questions for Internal Medicine II now: {new_count}")

if __name__ == "__main__":
    asyncio.run(main())
