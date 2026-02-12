#!/usr/bin/env python3
"""
Copy questions from AAU and IASI to An-Najah National University.
Mapping:
- NAJAH_DENT <- AAU_DENT (50 courses)
- NAJAH_PHARM <- AAU_PHARM (50 courses)
- NAJAH_MED <- IASI_MED (60 courses)
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
import uuid

load_dotenv('/app/backend/.env')
mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']


async def copy_questions_to_najah():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    total_copied = 0
    
    # Define mapping rules
    mappings = [
        # (source_prefix, target_prefix, description)
        ('AAU_DENT_', 'NAJAH_DENT_', 'Dentistry'),
        ('AAU_PHARM_', 'NAJAH_PHARM_', 'Pharmacy'),
        ('IASI_MED_', 'NAJAH_MED_', 'Medicine'),
    ]
    
    for source_prefix, target_prefix, desc in mappings:
        print(f"\n{'='*60}")
        print(f"Copying {desc}: {source_prefix} -> {target_prefix}")
        print('='*60)
        
        # Get all source courses with questions
        all_courses = await db.mcq_questions.distinct('course_id')
        source_courses = [c for c in all_courses if c.startswith(source_prefix)]
        print(f"Found {len(source_courses)} source courses")
        
        copied_in_section = 0
        
        for source_course in sorted(source_courses):
            # Calculate target course_id
            target_course = source_course.replace(source_prefix, target_prefix)
            
            # Check if target already has questions
            existing = await db.mcq_questions.count_documents({'course_id': target_course})
            if existing >= 300:
                print(f"  SKIP {target_course}: Already has {existing} questions")
                continue
            
            # Get source questions
            source_questions = await db.mcq_questions.find(
                {'course_id': source_course},
                {'_id': 0}
            ).to_list(500)
            
            if not source_questions:
                print(f"  WARN {source_course}: No questions found")
                continue
            
            # Create new questions for target
            new_questions = []
            for i, q in enumerate(source_questions):
                new_q = {
                    'question_id': f"q_{uuid.uuid4().hex[:12]}",
                    'course_id': target_course,
                    'question': q.get('question', ''),
                    'option_a': q.get('option_a', q.get('a', '')),
                    'option_b': q.get('option_b', q.get('b', '')),
                    'option_c': q.get('option_c', q.get('c', '')),
                    'option_d': q.get('option_d', q.get('d', '')),
                    'correct_answer': q.get('correct_answer', q.get('answer', '')),
                    'explanation': q.get('explanation', ''),
                    'difficulty': q.get('difficulty', 'medium'),
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'source': source_course  # Track source for reference
                }
                new_questions.append(new_q)
            
            # Insert questions
            if new_questions:
                # Delete any existing (partial) questions first
                if existing > 0:
                    await db.mcq_questions.delete_many({'course_id': target_course})
                
                await db.mcq_questions.insert_many(new_questions)
                copied_in_section += len(new_questions)
                total_copied += len(new_questions)
                print(f"  OK {target_course}: Copied {len(new_questions)} questions from {source_course}")
        
        print(f"\n{desc} complete: {copied_in_section} questions copied")
    
    print(f"\n{'='*60}")
    print(f"TOTAL: {total_copied} questions copied to An-Najah University")
    print('='*60)
    
    # Final verification
    all_najah = await db.mcq_questions.distinct('course_id')
    najah_courses = [c for c in all_najah if c.startswith('NAJAH_')]
    
    najah_total = await db.mcq_questions.count_documents({'course_id': {'$in': najah_courses}})
    print(f"\nVerification: NAJAH now has {najah_total} questions")
    
    # Show by program
    for prog in ['MED', 'DENT', 'PHARM']:
        prog_courses = [c for c in najah_courses if c.startswith(f'NAJAH_{prog}_')]
        count = await db.mcq_questions.count_documents({'course_id': {'$in': prog_courses}})
        print(f"  NAJAH_{prog}: {count} questions in {len(prog_courses)} courses")


if __name__ == '__main__':
    asyncio.run(copy_questions_to_najah())
