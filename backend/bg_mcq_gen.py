#!/usr/bin/env python3
"""
Background MCQ Generator for UG courses
Run with: nohup python3 bg_mcq_gen.py > /tmp/mcq_gen.log 2>&1 &
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from pymongo import MongoClient
import uuid

client = MongoClient('mongodb://localhost:27017')
db = client['test_database']
API_KEY = 'sk-emergent-a5308B4287b53E8405'

async def gen_mcq(course_id, course_name, desc, count=25):
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    chat = LlmChat(
        api_key=API_KEY, 
        session_id=f"mcq_{uuid.uuid4().hex[:8]}",
        system_message="Create MCQ for medical education. Return JSON array only. No extra text."
    ).with_model("openai", "gpt-4o")
    
    # Determine answer distribution
    a_cnt = count // 4
    b_cnt = count // 4
    c_cnt = count // 4
    d_cnt = count - a_cnt - b_cnt - c_cnt
    
    prompt = f"""Generate exactly {count} MCQ questions for: {course_name}
Description: {desc}

IMPORTANT: Distribute answers: {a_cnt} with answer A, {b_cnt} with B, {c_cnt} with C, {d_cnt} with D

Return ONLY a JSON array:
[{{"question":"...","option_a":"...","option_b":"...","option_c":"...","option_d":"...","correct_answer":"A","explanation":"...","difficulty":"medium"}}]"""

    try:
        r = await chat.send_message(UserMessage(text=prompt))
        j1, j2 = r.find('['), r.rfind(']')+1
        if j1 >= 0 and j2 > j1:
            qs = json.loads(r[j1:j2])
            return qs
    except Exception as e:
        print(f"  Error: {e}")
    return []

async def complete_course_mcq(course):
    cid = course["external_id"]
    cname = course.get("course_name", cid)
    desc = course.get("course_description", "Medical education content")
    
    cur = db.mcq_questions.count_documents({"course_id": cid})
    needed = 200 - cur
    
    if needed <= 0:
        print(f"[SKIP] {cid}: already has {cur} MCQ")
        return 0
    
    print(f"[START] {cid}: {cur} -> 200 (need {needed})")
    
    added = 0
    batch_num = 0
    
    while added < needed:
        batch_num += 1
        size = min(25, needed - added)
        
        print(f"  Batch {batch_num}: generating {size} questions...")
        
        qs = await gen_mcq(cid, cname, desc, size)
        
        if qs:
            valid_qs = []
            for i, q in enumerate(qs):
                if all(k in q for k in ["question", "option_a", "option_b", "option_c", "option_d", "correct_answer"]):
                    q["question_id"] = f"q_{cid}_{cur+added+len(valid_qs):03d}"
                    q["course_id"] = cid
                    q["topic"] = cname
                    q["created_at"] = datetime.now(timezone.utc).isoformat()
                    valid_qs.append(q)
            
            if valid_qs:
                db.mcq_questions.insert_many(valid_qs)
                added += len(valid_qs)
                print(f"    +{len(valid_qs)} questions (total: {cur+added})")
        else:
            print(f"    Failed to generate batch")
        
        await asyncio.sleep(1)  # Rate limiting
    
    print(f"[DONE] {cid}: added {added} MCQ")
    return added

async def main():
    print("="*60)
    print("UG MCQ BACKGROUND GENERATOR")
    print("="*60)
    print(f"Started at: {datetime.now()}")
    
    # Get UG courses
    ug = list(db.courses.find({"university_id": "UG_TBILISI"}))
    
    # Filter courses under 200 MCQ
    under200 = []
    for c in ug:
        cnt = db.mcq_questions.count_documents({"course_id": c["external_id"]})
        if cnt < 200:
            under200.append((c, cnt))
    
    print(f"\nFound {len(under200)} courses needing MCQ completion")
    print("-"*60)
    
    total_added = 0
    
    for i, (course, current_cnt) in enumerate(under200):
        print(f"\n[{i+1}/{len(under200)}] Processing...")
        added = await complete_course_mcq(course)
        total_added += added
        
        # Progress checkpoint
        if (i + 1) % 5 == 0:
            print(f"\n*** CHECKPOINT: {i+1}/{len(under200)} courses, {total_added} MCQ added ***\n")
    
    print("\n" + "="*60)
    print(f"COMPLETE! Added {total_added} total MCQ questions")
    print(f"Finished at: {datetime.now()}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
