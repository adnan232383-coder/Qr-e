import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def check_courses():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    
    courses_to_check = [
        ("NVU_MD_Y4_S2_C39", "Emergency Medicine"),
        ("NVU_MD_Y3_S2_C30", "General Surgery II"),
        ("NVU_MD_Y3_S1_C26", "Radiology"),
        ("NVU_MD_Y3_S2_C32", "Infectious Diseases"),
        ("NVU_MD_Y3_S1_C25", "General Surgery I"),
    ]
    
    print("=" * 60)
    print("Course Question Count Verification")
    print("=" * 60)
    
    for course_id, name in courses_to_check:
        count = await db.mcq_questions.count_documents({"course_id": course_id})
        course = await db.courses.find_one({"external_id": course_id})
        stored_count = course.get("mcq_count", "N/A") if course else "N/A"
        print(f"{name:25} | ID: {course_id} | Actual: {count:3}/200 | Stored: {stored_count}")
    
    print("=" * 60)

asyncio.run(check_courses())
