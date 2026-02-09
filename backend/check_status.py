from motor.motor_asyncio import AsyncIOMotorClient
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

async def main():
    # Get all courses with question counts
    courses = await db.courses.find({}, {"_id": 0}).to_list(500)

    # Get question counts per course
    pipeline = [
        {"$group": {"_id": "$course_id", "count": {"$sum": 1}}}
    ]
    question_counts = {item["_id"]: item["count"] async for item in db.mcq_questions.aggregate(pipeline)}

    # Organize by university
    nvu_courses = []
    ug_courses = []

    for course in courses:
        course_id = course.get("external_id", "")
        university_id = course.get("university_id", "")
        count = question_counts.get(course_id, 0)
        course_info = {
            "name": course.get("course_name", ""),
            "course_id": course_id,
            "questions": count
        }
        
        if "NVU" in university_id:
            nvu_courses.append(course_info)
        else:
            ug_courses.append(course_info)

    # Sort by name
    nvu_courses.sort(key=lambda x: x["name"])
    ug_courses.sort(key=lambda x: x["name"])

    print("=" * 60)
    print("NEW VISION UNIVERSITY (NVU)")
    print("=" * 60)
    nvu_total = 0
    nvu_empty = 0
    nvu_empty_list = []
    for c in nvu_courses:
        name = c["name"]
        questions = c["questions"]
        status = "✅" if questions > 0 else "❌"
        print(f"{status} {name}: {questions} שאלות")
        nvu_total += questions
        if questions == 0:
            nvu_empty += 1
            nvu_empty_list.append(name)

    print(f"\nסה\"כ NVU: {len(nvu_courses)} קורסים, {nvu_total} שאלות, {nvu_empty} ריקים")

    print("\n" + "=" * 60)
    print("UNIVERSITY OF GEORGIA (UG)")
    print("=" * 60)
    ug_total = 0
    ug_empty = 0
    ug_empty_list = []
    for c in ug_courses:
        name = c["name"]
        questions = c["questions"]
        status = "✅" if questions > 0 else "❌"
        print(f"{status} {name}: {questions} שאלות")
        ug_total += questions
        if questions == 0:
            ug_empty += 1
            ug_empty_list.append(name)

    print(f"\nסה\"כ UG: {len(ug_courses)} קורסים, {ug_total} שאלות, {ug_empty} ריקים")

    print("\n" + "=" * 60)
    print("📊 סיכום כללי")
    print("=" * 60)
    print(f"סה\"כ שאלות במערכת: {nvu_total + ug_total}")
    print(f"סה\"כ קורסים: {len(nvu_courses) + len(ug_courses)}")
    print(f"קורסים עם שאלות: {len(nvu_courses) + len(ug_courses) - nvu_empty - ug_empty}")
    print(f"קורסים ריקים: {nvu_empty + ug_empty}")

    if nvu_empty_list:
        print("\n" + "=" * 60)
        print("📋 קורסים ריקים של NVU (הבאים בתור)")
        print("=" * 60)
        for i, name in enumerate(nvu_empty_list, 1):
            print(f"{i}. {name}")

    if ug_empty_list:
        print("\n" + "=" * 60)
        print("📋 קורסים ריקים של UG")
        print("=" * 60)
        for i, name in enumerate(ug_empty_list, 1):
            print(f"{i}. {name}")

if __name__ == "__main__":
    asyncio.run(main())
