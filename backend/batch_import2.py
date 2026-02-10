import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# Map files to course IDs based on what's missing
FILE_TO_COURSE = {
    '/app/mcq_pack2/Psychiatry_50.json': 'NVU_MD_Y4_S1_C31',  # Psychiatry - has 100, needs 100 more
    '/app/mcq_pack2/Radiology_50.json': 'NVU_MD_Y3_S1_C27',  # Radiology - has 50, needs 150 more
    '/app/mcq_pack2/Infectious_Diseases_50.json': 'NVU_MD_Y3_S2_C28',  # Infectious Diseases - has 50, needs 150
    '/app/mcq_pack2/Obstetrics_Gynecology_I_50.json': 'NVU_MD_Y4_S1_C32',  # OB/GYN I - has 100, needs 100
    '/app/mcq_pack2/Internal_Medicine_I_50.json': 'NVU_MD_Y3_S1_C28',  # Internal Med I -> use for empty course
    '/app/mcq_pack2/Internal_Medicine_II_50.json': 'NVU_MD_Y3_S2_C31',  # Internal Med II -> 0/200
    '/app/mcq_pack2/Neurology_50.json': 'NVU_MD_Y4_S2_C38',  # Neurology -> 0/200
    '/app/mcq_pack2/Pharmacology_50.json': 'NVU_MD_Y4_S2_C40',  # Pharmacology -> 0/200
    '/app/mcq_pack2/Pathology_50.json': 'NVU_MD_Y2_S1_C18',  # Pathology -> 67/200
    '/app/mcq_pack2/Emergency_Medicine_50.json': 'NVU_MD_Y5_S1_C41',  # Emergency -> 0/200
}

async def import_questions(file_path, course_id):
    with open(file_path, 'r') as f:
        questions_data = json.load(f)
    
    file_name = os.path.basename(file_path)
    print(f"\n{'='*50}")
    print(f"File: {file_name} -> Course: {course_id}")
    print(f"Questions in file: {len(questions_data)}")
    
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    
    current_count = await db.mcq_questions.count_documents({"course_id": course_id})
    print(f"Current in DB: {current_count}")
    
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
    print(f"Inserted: {len(result.inserted_ids)}")
    
    new_count = await db.mcq_questions.count_documents({"course_id": course_id})
    await db.courses.update_one(
        {"external_id": course_id},
        {"$set": {"mcq_count": new_count, "mcq_verified": True}}
    )
    
    remaining = 200 - new_count
    status = "✅ COMPLETE!" if remaining <= 0 else f"⏳ Need {remaining} more"
    print(f"New total: {new_count}/200 - {status}")

async def main():
    print("="*50)
    print("🏥 BATCH IMPORT - 10 Course Pack")
    print("="*50)
    
    # Import to courses that need questions most
    priority_imports = [
        ('/app/mcq_pack2/Psychiatry_50.json', 'NVU_MD_Y4_S1_C31'),
        ('/app/mcq_pack2/Radiology_50.json', 'NVU_MD_Y3_S1_C27'),
        ('/app/mcq_pack2/Obstetrics_Gynecology_I_50.json', 'NVU_MD_Y4_S1_C32'),
        ('/app/mcq_pack2/Infectious_Diseases_50.json', 'NVU_MD_Y3_S2_C28'),
        ('/app/mcq_pack2/Internal_Medicine_II_50.json', 'NVU_MD_Y3_S2_C31'),
        ('/app/mcq_pack2/Neurology_50.json', 'NVU_MD_Y4_S2_C38'),
        ('/app/mcq_pack2/Pharmacology_50.json', 'NVU_MD_Y4_S2_C40'),
        ('/app/mcq_pack2/Pathology_50.json', 'NVU_MD_Y2_S1_C18'),
        ('/app/mcq_pack2/Emergency_Medicine_50.json', 'NVU_MD_Y5_S1_C41'),
        ('/app/mcq_pack2/Internal_Medicine_I_50.json', 'NVU_MD_Y5_S1_C42'),
    ]
    
    for file_path, course_id in priority_imports:
        await import_questions(file_path, course_id)
    
    print("\n" + "="*50)
    print("🎉 IMPORT COMPLETE!")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())
