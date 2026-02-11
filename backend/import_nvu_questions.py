#!/usr/bin/env python3
"""
Import NVU MCQ questions from JSON files
"""
import asyncio
import json
import os
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime, timezone
import uuid

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

async def import_questions_from_file(file_path: str):
    """Import questions from a single JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    course_code = data.get('course_code')
    course_name = data.get('course_name')
    questions_data = data.get('questions', [])
    
    if not course_code or not questions_data:
        print(f"  Skipping {file_path}: No course_code or questions")
        return 0
    
    # Check if course exists
    course = await db.courses.find_one({"external_id": course_code})
    if not course:
        print(f"  Course {course_code} not found in DB, creating...")
        # Try to create the course
        await db.courses.insert_one({
            "external_id": course_code,
            "year_id": f"NVU_{course_code.split('_')[1]}_{course_code.split('_')[2]}",
            "semester": int(course_code.split('_')[3][1]) if len(course_code.split('_')) > 3 else 1,
            "course_name": course_name,
            "course_description": f"{course_name} - NVU Course",
            "university_id": "NVU_TBILISI"
        })
    
    # Prepare questions for import
    questions_to_import = []
    for i, q in enumerate(questions_data):
        question_doc = {
            "question_id": f"q_{course_code}_{i:03d}_{uuid.uuid4().hex[:6]}",
            "course_id": course_code,
            "question": q.get('question', ''),
            "option_a": q.get('option_a', ''),
            "option_b": q.get('option_b', ''),
            "option_c": q.get('option_c', ''),
            "option_d": q.get('option_d', ''),
            "correct_answer": q.get('correct_answer', 'A'),
            "explanation": q.get('explanation', ''),
            "difficulty": q.get('difficulty', 'medium'),
            "topic": course_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": "user_imported"
        }
        questions_to_import.append(question_doc)
    
    if questions_to_import:
        # Insert questions (don't delete existing, add to them)
        await db.mcq_questions.insert_many(questions_to_import)
        
        # Update course mcq count
        total_count = await db.mcq_questions.count_documents({"course_id": course_code})
        await db.courses.update_one(
            {"external_id": course_code},
            {"$set": {"mcq_count": total_count, "mcq_verified": True}}
        )
        
        print(f"  Imported {len(questions_to_import)} questions for {course_code} ({course_name})")
        print(f"  Total questions for this course: {total_count}")
        return len(questions_to_import)
    
    return 0

async def import_all_from_directory(directory: str):
    """Import all JSON files from a directory"""
    total_imported = 0
    files = list(Path(directory).glob("*.json"))
    
    print(f"\n=== Importing {len(files)} JSON files from {directory} ===\n")
    
    for file_path in sorted(files):
        print(f"Processing: {file_path.name}")
        try:
            count = await import_questions_from_file(str(file_path))
            total_imported += count
        except Exception as e:
            print(f"  ERROR: {e}")
    
    print(f"\n=== Total imported: {total_imported} questions ===")
    return total_imported

async def main():
    # Import from the extracted directory
    directory = "/tmp/nvu_import"
    await import_all_from_directory(directory)
    
    # Print summary
    print("\n=== Summary of NVU courses ===")
    pipeline = [
        {"$match": {"course_id": {"$regex": "^NVU_"}}},
        {"$group": {"_id": "$course_id", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    results = await db.mcq_questions.aggregate(pipeline).to_list(100)
    
    for r in results:
        print(f"  {r['_id']}: {r['count']} questions")
    
    print(f"\nTotal NVU courses with MCQs: {len(results)}")

if __name__ == "__main__":
    asyncio.run(main())
