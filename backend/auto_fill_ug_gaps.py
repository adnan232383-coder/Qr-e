#!/usr/bin/env python3
"""
Autonomous MCQ Generator for UG courses with gaps.
Generates 276 questions per course to reach 300 total.
"""

import asyncio
import os
import json
import uuid
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']
api_key = os.environ.get('EMERGENT_LLM_KEY')

# Courses that need questions
COURSES_TO_FILL = [
    ("UG_DENT_Y1_S1_C01", "General Biology", "Cell biology, genetics, molecular biology, microbiology basics"),
    ("UG_DENT_Y1_S1_C02", "General Chemistry", "Atomic structure, chemical bonding, acids/bases, organic chemistry basics"),
    ("UG_DENT_Y1_S1_C03", "Medical Terminology", "Root words, prefixes, suffixes, anatomical terms, dental terminology"),
    ("UG_DENT_Y1_S1_C04", "Human Anatomy I", "Musculoskeletal system, bones, joints, muscles, head and neck anatomy"),
    ("UG_DENT_Y1_S1_C05", "Physics for Health Sciences", "Mechanics, radiation physics, X-ray physics for dental applications"),
    ("UG_DENT_Y1_S2_C06", "Organic Chemistry (Intro)", "Functional groups, carbohydrates, lipids, proteins"),
    ("UG_DENT_Y1_S2_C07", "Human Anatomy II", "Cardiovascular, respiratory, nervous, digestive systems"),
    ("UG_DENT_Y1_S2_C08", "Histology & Embryology", "Basic tissues, epithelium, connective tissue, embryonic development"),
    ("UG_DENT_Y1_S2_C09", "Biochemistry I", "Enzymes, metabolism, carbohydrate/lipid/protein metabolism"),
    ("UG_DENT_Y1_S2_C10", "Dental Anatomy (Intro)", "Tooth morphology, numbering systems, occlusion basics"),
    ("UG_DENT_Y2_S1_C01", "Physiology", "Cardiovascular, respiratory, renal, neurophysiology"),
    ("UG_DENT_Y2_S1_C02", "Microbiology", "Bacteria, viruses, fungi, oral microbiome, dental infections"),
    ("UG_DENT_Y2_S1_C03", "Pathology (Intro)", "Cell injury, inflammation, healing, neoplasia, oral pathology"),
    ("UG_DENT_Y2_S1_C04", "Pharmacology (Basics)", "Drug mechanisms, pharmacokinetics, analgesics, local anesthetics"),
    ("UG_DENT_Y2_S1_C05", "Oral Anatomy & Occlusion", "TMJ, muscles of mastication, occlusal relationships"),
    ("UG_DENT_Y2_S2_C06", "Immunology (Basics)", "Immune system, innate/adaptive immunity, hypersensitivity"),
    ("UG_DENT_Y2_S2_C07", "Preclinical Operative Dentistry I", "Cavity preparation, dental instruments, isolation techniques"),
    ("UG_DENT_Y2_S2_C08", "Dental Materials I", "Amalgam, composites, cements, impression materials"),
    ("UG_DENT_Y2_S2_C09", "Radiology (Basics)", "X-ray production, radiographic techniques, radiation safety"),
    ("UG_DENT_Y2_S2_C10", "Infection Control & Sterilization", "Sterilization methods, disinfection, PPE, cross-contamination"),
]

async def generate_questions_batch(course_id, course_name, topics, batch_num, batch_size=50):
    """Generate a batch of questions using LLM"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    # Vary the correct answer distribution
    answers = ["A", "B", "C", "D"]
    target_answer = answers[batch_num % 4]
    
    prompt = f"""Generate exactly {batch_size} multiple-choice questions for a dental school course.

Course: {course_name}
Topics: {topics}
Batch: {batch_num + 1}

CRITICAL REQUIREMENTS:
1. Each question MUST have exactly 4 options (A, B, C, D)
2. For this batch, approximately 25% of questions should have "{target_answer}" as the correct answer
3. Questions should be clinically relevant for dental students
4. Mix difficulty: 30% easy, 50% medium, 20% hard

Return ONLY a valid JSON array with this exact structure:
[
  {{
    "question": "Question text here?",
    "option_a": "First option",
    "option_b": "Second option",
    "option_c": "Third option",
    "option_d": "Fourth option",
    "correct_answer": "A",
    "explanation": "Brief explanation"
  }}
]

Generate {batch_size} unique, high-quality questions. Return ONLY the JSON array, no other text."""

    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"mcq_gen_{uuid.uuid4().hex[:8]}",
            system_message="You are a medical education expert. Return only valid JSON arrays."
        ).with_model("openai", "gpt-4o")
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        # Parse JSON from response
        json_start = response.find('[')
        json_end = response.rfind(']') + 1
        if json_start >= 0 and json_end > json_start:
            questions = json.loads(response[json_start:json_end])
            return questions
        return []
    except Exception as e:
        print(f"    Error generating batch {batch_num}: {e}")
        return []

async def fill_course_questions(db, course_id, course_name, topics, needed):
    """Fill questions for a single course"""
    print(f"\n{'='*60}")
    print(f"Course: {course_id} - {course_name}")
    print(f"Need to generate: {needed} questions")
    print('='*60)
    
    batch_size = 50
    num_batches = (needed + batch_size - 1) // batch_size
    
    all_questions = []
    
    for batch_num in range(num_batches):
        remaining = min(batch_size, needed - len(all_questions))
        if remaining <= 0:
            break
            
        print(f"  Generating batch {batch_num + 1}/{num_batches} ({remaining} questions)...")
        
        batch_questions = await generate_questions_batch(
            course_id, course_name, topics, batch_num, remaining
        )
        
        if batch_questions:
            for q in batch_questions:
                q['question_id'] = f"q_{uuid.uuid4().hex[:12]}"
                q['course_id'] = course_id
                q['created_at'] = datetime.now(timezone.utc).isoformat()
                q['difficulty'] = q.get('difficulty', 'medium')
            
            all_questions.extend(batch_questions)
            print(f"    Got {len(batch_questions)} questions (total: {len(all_questions)})")
        else:
            print(f"    Failed to generate batch {batch_num + 1}")
        
        # Small delay between batches
        await asyncio.sleep(1)
    
    # Insert questions to database
    if all_questions:
        await db.mcq_questions.insert_many(all_questions)
        
        # Update course mcq_count
        new_count = await db.mcq_questions.count_documents({'course_id': course_id})
        await db.courses.update_one(
            {'external_id': course_id},
            {'$set': {'mcq_count': new_count}}
        )
        
        print(f"  ✓ Inserted {len(all_questions)} questions. New total: {new_count}")
        return len(all_questions)
    
    return 0

async def main():
    print("="*60)
    print("AUTONOMOUS MCQ GENERATOR - UG Courses")
    print("="*60)
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    total_generated = 0
    courses_completed = 0
    
    for course_id, course_name, topics in COURSES_TO_FILL:
        # Check current count
        current = await db.mcq_questions.count_documents({'course_id': course_id})
        needed = 300 - current
        
        if needed <= 0:
            print(f"\n✓ {course_id}: Already has {current} questions, skipping")
            courses_completed += 1
            continue
        
        generated = await fill_course_questions(db, course_id, course_name, topics, needed)
        total_generated += generated
        
        if generated > 0:
            courses_completed += 1
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Courses processed: {courses_completed}/{len(COURSES_TO_FILL)}")
    print(f"Total questions generated: {total_generated}")
    
    # Final verification
    print("\nFinal verification:")
    for course_id, course_name, _ in COURSES_TO_FILL:
        count = await db.mcq_questions.count_documents({'course_id': course_id})
        status = "✓" if count >= 300 else "✗"
        print(f"  {status} {course_id}: {count} questions")

if __name__ == '__main__':
    asyncio.run(main())
