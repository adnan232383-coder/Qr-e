import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# Map files to course IDs
IMPORTS = [
    ('/app/mcq_pack3/Obstetrics_and_Gynecology_I_50.json', 'NVU_MD_Y4_S1_C32', 'OB/GYN I'),
    ('/app/mcq_pack3/Psychiatry_50.json', 'NVU_MD_Y4_S1_C31', 'Psychiatry'),
    ('/app/mcq_pack3/Radiology_100.json', 'NVU_MD_Y3_S1_C27', 'Radiology'),
    ('/app/mcq_pack3/Infectious_Diseases_100.json', 'NVU_MD_Y3_S2_C28', 'Infectious Diseases'),
    ('/app/mcq_pack3/Pathology_85.json', 'NVU_MD_Y2_S1_C18', 'Pathology'),
    ('/app/mcq_pack3/Internal_Medicine_II_150.json', 'NVU_MD_Y3_S2_C31', 'Internal Med II'),
    ('/app/mcq_pack3/Neurology_150.json', 'NVU_MD_Y4_S2_C38', 'Neurology'),
    ('/app/mcq_pack3/Pharmacology_150.json', 'NVU_MD_Y4_S2_C40', 'Pharmacology'),
    ('/app/mcq_pack3/Emergency_Medicine_150.json', 'NVU_MD_Y5_S1_C41', 'Emergency Medicine'),
    ('/app/mcq_pack3/Internal_Medicine_I_150.json', 'NVU_MD_Y5_S1_C42', 'Internal Med I'),
]

async def import_questions(file_path, course_id, course_name):
    with open(file_path, 'r') as f:
        questions_data = json.load(f)
    
    print(f"\n{'='*50}")
    print(f"{course_name}: {len(questions_data)} questions -> {course_id}")
    
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    
    current_count = await db.mcq_questions.count_documents({"course_id": course_id})
    print(f"Before: {current_count}/200")
    
    questions_to_insert = []
    for q in questions_data:
        question_doc = {
            "question_id": f"q_{uuid.uuid4().hex[:12]}",
            "course_id": course_id,
            "question": q["question"],
            "option_a": q["option_a"],
            "option_b": q["option_b"],
            "option_c": q["option_c"],
            "option_d": q["option_d"],
            "correct_answer": q["correct_answer"],
            "explanation": q.get("explanation", ""),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        questions_to_insert.append(question_doc)
    
    result = await db.mcq_questions.insert_many(questions_to_insert)
    
    new_count = await db.mcq_questions.count_documents({"course_id": course_id})
    await db.courses.update_one(
        {"external_id": course_id},
        {"$set": {"mcq_count": new_count, "mcq_verified": True}}
    )
    
    status = "✅ COMPLETE!" if new_count >= 200 else f"⏳ {200-new_count} more needed"
    print(f"After: {new_count}/200 - {status}")

async def main():
    print("="*50)
    print("🏥 MEGA IMPORT - 1,135 Questions")
    print("="*50)
    
    for file_path, course_id, course_name in IMPORTS:
        await import_questions(file_path, course_id, course_name)
    
    print("\n" + "="*50)
    print("🎉 IMPORT COMPLETE!")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())
