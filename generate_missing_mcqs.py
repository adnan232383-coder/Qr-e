"""
Generate missing MCQ questions for courses that have less than 200
"""

import os
import sys
import time
import json
import uuid
from datetime import datetime

# Add backend to path
sys.path.insert(0, '/app/backend')
os.chdir('/app/backend')

from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient
from emergentintegrations.llm.chat import LlmChat, UserMessage

# MongoDB connection
client = MongoClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]

EMERGENT_API_KEY = os.environ.get('EMERGENT_API_KEY', '')

def generate_mcqs_batch(course_name: str, course_description: str, num_questions: int = 24) -> list:
    """Generate a batch of MCQ questions using LLM"""
    
    llm = LlmChat(
        api_key=EMERGENT_API_KEY,
        model="gpt-4o-mini",
        temperature=0.7
    )
    
    prompt = f"""Generate {num_questions} multiple choice questions for a university course.

Course: {course_name}
Description: {course_description if course_description else 'A comprehensive university course covering fundamental concepts and clinical applications.'}

Requirements:
1. Questions should cover different topics within the subject
2. Mix of difficulty levels: approximately 8 Easy, 12 Medium, 4 Hard questions
3. Each question must have exactly 4 options (A, B, C, D)
4. One correct answer per question
5. Provide brief explanation for the correct answer

Return ONLY valid JSON array with this structure:
[
  {{
    "question": "The question text here?",
    "option_a": "First option",
    "option_b": "Second option", 
    "option_c": "Third option",
    "option_d": "Fourth option",
    "correct_answer": "A",
    "explanation": "Brief explanation why this is correct",
    "difficulty": "easy|medium|hard"
  }}
]

Generate exactly {num_questions} questions. Return ONLY the JSON array, no other text."""

    try:
        response = llm.chat([UserMessage(content=prompt)])
        
        # Parse JSON from response
        text = response.content.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        questions = json.loads(text.strip())
        return questions
    except Exception as e:
        print(f"  Error generating questions: {e}")
        return []


def main():
    print("=" * 60)
    print("Starting MCQ Generation for Courses with < 200 Questions")
    print("=" * 60)
    
    # Find courses needing questions
    courses = list(db.courses.find({"external_id": {"$regex": "^UG_"}}, {"_id": 0}))
    
    courses_needing_mcq = []
    for course in courses:
        count = db.mcq_questions.count_documents({"course_id": course["external_id"]})
        if count < 200:
            courses_needing_mcq.append({
                "course": course,
                "current": count,
                "needed": 200 - count
            })
    
    print(f"\nFound {len(courses_needing_mcq)} courses needing questions")
    total_needed = sum(c['needed'] for c in courses_needing_mcq)
    print(f"Total questions to generate: {total_needed}")
    
    for i, item in enumerate(courses_needing_mcq):
        course = item["course"]
        current = item["current"]
        needed = item["needed"]
        
        print(f"\n[{i+1}/{len(courses_needing_mcq)}] {course['course_name']}")
        print(f"  Current: {current}, Needed: {needed}")
        
        # Generate in batches of 24
        questions_generated = 0
        batch_num = 0
        
        while questions_generated < needed:
            batch_size = min(24, needed - questions_generated)
            batch_num += 1
            
            print(f"  Batch {batch_num}: Generating {batch_size} questions...")
            
            questions = generate_mcqs_batch(
                course['course_name'],
                course.get('course_description', ''),
                batch_size
            )
            
            if questions:
                # Insert into database
                for q in questions:
                    q["question_id"] = f"mcq_{uuid.uuid4().hex[:12]}"
                    q["course_id"] = course["external_id"]
                    q["created_at"] = datetime.utcnow().isoformat()
                    
                    # Normalize difficulty
                    diff = q.get("difficulty", "medium").lower()
                    if diff not in ["easy", "medium", "hard"]:
                        diff = "medium"
                    q["difficulty"] = diff
                
                db.mcq_questions.insert_many(questions)
                questions_generated += len(questions)
                print(f"  Generated and saved {len(questions)} questions")
            else:
                print(f"  Failed to generate questions, retrying in 5 seconds...")
                time.sleep(5)
                continue
            
            # Rate limiting
            time.sleep(2)
        
        # Verify final count
        final_count = db.mcq_questions.count_documents({"course_id": course["external_id"]})
        print(f"  Final count: {final_count}/200")
    
    print("\n" + "=" * 60)
    print("MCQ Generation Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
