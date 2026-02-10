import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# Course mappings
COURSES = {
    'mcq_pack/OBGYN_II_50_Emergent.json': 'NVU_MD_Y4_S2_C35',  # OB/GYN II
    'mcq_pack/Psychiatry_Part_1_50_Emergent.json': 'NVU_MD_Y4_S1_C31',  # Psychiatry
    'mcq_pack/Psychiatry_Part_2_50_Emergent.json': 'NVU_MD_Y4_S1_C31',  # Psychiatry
    'mcq_pack/Radiology_50_Emergent.json': 'NVU_MD_Y3_S1_C27',  # Radiology
    'mcq_pack/Infectious_Diseases_50_Emergent.json': 'NVU_MD_Y3_S2_C28',  # Infectious Diseases
    'mcq_pack/OBGYN_I_50_Emergent.json': 'NVU_MD_Y4_S1_C32',  # OB/GYN I
}

async def import_questions(file_path, course_id, course_name):
    # Load questions from JSON file
    with open(file_path, 'r') as f:
        questions_data = json.load(f)
    
    print(f"\n{'='*60}")
    print(f"Importing: {course_name}")
    print(f"File: {file_path}")
    print(f"Questions in file: {len(questions_data)}")
    
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    
    # Get current count
    current_count = await db.mcq_questions.count_documents({"course_id": course_id})
    print(f"Current questions in DB: {current_count}")
    
    # Prepare questions for insertion
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
            "explanation": q["explanation"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        questions_to_insert.append(question_doc)
    
    # Insert questions
    result = await db.mcq_questions.insert_many(questions_to_insert)
    print(f"Inserted: {len(result.inserted_ids)} questions")
    
    # Update course mcq_count
    new_count = await db.mcq_questions.count_documents({"course_id": course_id})
    await db.courses.update_one(
        {"external_id": course_id},
        {"$set": {"mcq_count": new_count, "mcq_verified": True}}
    )
    
    remaining = 200 - new_count
    status = "✅ COMPLETE!" if remaining <= 0 else f"⏳ Need {remaining} more"
    print(f"New total: {new_count}/200 - {status}")
    
    return new_count

async def main():
    imports = [
        ('mcq_pack/OBGYN_II_50_Emergent.json', 'NVU_MD_Y4_S2_C35', 'OB/GYN II'),
        ('mcq_pack/Psychiatry_Part_1_50_Emergent.json', 'NVU_MD_Y4_S1_C31', 'Psychiatry (Part 1)'),
        ('mcq_pack/Psychiatry_Part_2_50_Emergent.json', 'NVU_MD_Y4_S1_C31', 'Psychiatry (Part 2)'),
        ('mcq_pack/Radiology_50_Emergent.json', 'NVU_MD_Y3_S1_C27', 'Radiology'),
        ('mcq_pack/Infectious_Diseases_50_Emergent.json', 'NVU_MD_Y3_S2_C28', 'Infectious Diseases'),
        ('mcq_pack/OBGYN_I_50_Emergent.json', 'NVU_MD_Y4_S1_C32', 'OB/GYN I'),
    ]
    
    print("=" * 60)
    print("🏥 BATCH IMPORT - Medical Quiz Questions")
    print("=" * 60)
    
    for file_path, course_id, course_name in imports:
        await import_questions(f'/app/{file_path}', course_id, course_name)
    
    print("\n" + "=" * 60)
    print("🎉 BATCH IMPORT COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
