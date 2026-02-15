#!/usr/bin/env python3
"""
Complete UG Content Generator - Streamlined
Generates MCQ, Scripts, Audio, and Presentations for all UG courses
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from pymongo import MongoClient
import uuid

# Setup
client = MongoClient('mongodb://localhost:27017')
db = client['test_database']

API_KEY = os.environ.get('EMERGENT_LLM_KEY', 'sk-emergent-a5308B4287b53E8405')

async def generate_mcq_batch(course_id: str, course_name: str, description: str, count: int = 25):
    """Generate a batch of MCQ questions"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    chat = LlmChat(
        api_key=API_KEY,
        session_id=f"mcq_{uuid.uuid4().hex[:8]}",
        system_message="""You are a medical education expert creating MCQ questions.
IMPORTANT: Distribute correct answers evenly - 25% A, 25% B, 25% C, 25% D.
Return ONLY valid JSON array."""
    ).with_model("openai", "gpt-4o")
    
    prompt = f"""Generate {count} MCQ for {course_name}.
Description: {description}

Distribute answers: ~{count//4} A, ~{count//4} B, ~{count//4} C, ~{count//4} D.

JSON array only:
[{{"question": "...", "option_a": "...", "option_b": "...", "option_c": "...", "option_d": "...", "correct_answer": "A", "explanation": "...", "difficulty": "medium"}}]"""

    try:
        response = await chat.send_message(UserMessage(text=prompt))
        json_start = response.find('[')
        json_end = response.rfind(']') + 1
        if json_start >= 0 and json_end > json_start:
            return json.loads(response[json_start:json_end])
    except Exception as e:
        print(f"    MCQ error: {e}")
    return []

async def complete_mcq_for_course(course_id: str):
    """Complete MCQ to 200 for a course"""
    course = db.courses.find_one({"external_id": course_id})
    if not course:
        return 0
    
    current_count = db.mcq_questions.count_documents({"course_id": course_id})
    needed = 200 - current_count
    
    if needed <= 0:
        return 0
    
    print(f"  {course_id}: {current_count} -> 200 (need {needed})")
    
    course_name = course.get("course_name", course_id)
    description = course.get("course_description", "Medical course content")
    
    total_added = 0
    batches = (needed + 24) // 25
    
    for batch in range(batches):
        batch_size = min(25, needed - total_added)
        if batch_size <= 0:
            break
            
        questions = await generate_mcq_batch(course_id, course_name, description, batch_size)
        
        if questions:
            for i, q in enumerate(questions):
                q["question_id"] = f"q_{course_id}_{current_count + total_added + i:03d}"
                q["course_id"] = course_id
                q["topic"] = course_name
                q["created_at"] = datetime.now(timezone.utc).isoformat()
            
            db.mcq_questions.insert_many(questions)
            total_added += len(questions)
            print(f"    +{len(questions)} (total: {current_count + total_added})")
        
        await asyncio.sleep(0.3)
    
    return total_added

async def generate_script(course_name: str, module_title: str):
    """Generate a lecture script"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    chat = LlmChat(
        api_key=API_KEY,
        session_id=f"script_{uuid.uuid4().hex[:8]}",
        system_message="Create concise educational lecture scripts (400-600 words)."
    ).with_model("openai", "gpt-4o")
    
    prompt = f"""Write a 400-600 word lecture script for:
Course: {course_name}
Module: {module_title}

Include: introduction, 3 key points, conclusion. Professional tone for medical students.
Return only the script text."""

    try:
        response = await chat.send_message(UserMessage(text=prompt))
        return response.strip()
    except Exception as e:
        print(f"    Script error: {e}")
    return None

async def generate_audio(script_text: str, output_path: str):
    """Generate audio using TTS"""
    from emergentintegrations.llm.tts import text_to_speech
    import shutil
    
    try:
        audio_file = await text_to_speech(
            api_key=API_KEY,
            text=script_text,
            voice="nova",
            model="tts-1-hd"
        )
        shutil.copy(audio_file, output_path)
        return True
    except Exception as e:
        print(f"    Audio error: {e}")
    return False

def create_presentation(module_id: str, course_name: str, module_title: str, script_text: str):
    """Create HTML presentation"""
    
    # Split into sentences for slides
    sentences = [s.strip() + '.' for s in script_text.replace('\n', ' ').split('. ') if s.strip()]
    
    slides_html = f'''
    <div class="slide title-slide active" data-index="0">
        <div class="slide-inner">
            <h1>{module_title}</h1>
            <p class="course-name">{course_name}</p>
        </div>
    </div>'''
    
    # Create content slides (max 6)
    points_per_slide = max(2, len(sentences) // 5)
    slide_num = 1
    for i in range(0, len(sentences), points_per_slide):
        if slide_num > 5:
            break
        chunk = sentences[i:i+points_per_slide]
        points_html = "".join([f'<li><span class="bullet"></span>{s}</li>' for s in chunk[:3]])
        slides_html += f'''
    <div class="slide content-slide" data-index="{slide_num}">
        <div class="slide-inner">
            <h2>Key Points {slide_num}</h2>
            <ul class="points">{points_html}</ul>
        </div>
    </div>'''
        slide_num += 1
    
    # Summary slide
    slides_html += f'''
    <div class="slide content-slide" data-index="{slide_num}">
        <div class="slide-inner">
            <h2>Summary</h2>
            <ul class="points">
                <li><span class="bullet"></span>Key concepts covered in this module</li>
                <li><span class="bullet"></span>Clinical applications and relevance</li>
                <li><span class="bullet"></span>Review materials and practice questions</li>
            </ul>
        </div>
    </div>'''
    
    total_slides = slide_num + 1
    
    # Subtitles
    words = script_text.split()
    wps = 2.5
    subtitles = []
    for i in range(0, len(words), 12):
        subtitles.append({
            "start": round(i / wps, 2),
            "end": round(min((i + 12) / wps, len(words) / wps), 2),
            "text": " ".join(words[i:i+12])
        })
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{module_title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{ --bg: #0a0f1a; --card: #151d2e; --text: #f1f5f9; --accent: #38bdf8; }}
        body {{ font-family: 'Inter', system-ui, sans-serif; background: var(--bg); color: var(--text); height: 100vh; overflow: hidden; }}
        .container {{ display: flex; flex-direction: column; height: 100vh; }}
        .slides {{ flex: 1; position: relative; }}
        .slide {{ position: absolute; inset: 0; padding: 60px; opacity: 0; transform: translateX(50px); transition: all 0.5s; }}
        .slide.active {{ opacity: 1; transform: translateX(0); }}
        .slide-inner {{ height: 100%; display: flex; flex-direction: column; }}
        .title-slide .slide-inner {{ justify-content: center; align-items: center; text-align: center; }}
        .title-slide h1 {{ font-size: 3.5rem; background: linear-gradient(135deg, #38bdf8, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .course-name {{ font-size: 1.5rem; color: #94a3b8; margin-top: 20px; }}
        .content-slide h2 {{ font-size: 2.2rem; margin-bottom: 30px; border-bottom: 2px solid var(--card); padding-bottom: 15px; }}
        .points {{ list-style: none; }}
        .points li {{ display: flex; gap: 15px; padding: 18px 22px; background: var(--card); border-radius: 10px; font-size: 1.3rem; margin-bottom: 15px; border-left: 4px solid var(--accent); }}
        .bullet {{ width: 8px; height: 8px; background: var(--accent); border-radius: 50%; margin-top: 8px; flex-shrink: 0; }}
        .subtitles {{ position: absolute; bottom: 100px; left: 50%; transform: translateX(-50%); text-align: center; }}
        .subtitle-text {{ background: rgba(0,0,0,0.85); color: #fff; font-size: 1.3rem; padding: 12px 25px; border-radius: 8px; }}
        .controls {{ height: 70px; background: rgba(15,23,42,0.95); border-top: 1px solid rgba(255,255,255,0.1); display: flex; align-items: center; padding: 0 25px; gap: 15px; }}
        .btn {{ background: rgba(56,189,248,0.2); border: 1px solid rgba(56,189,248,0.3); color: var(--accent); width: 45px; height: 45px; border-radius: 10px; cursor: pointer; font-size: 1.1rem; }}
        .btn:hover {{ background: rgba(56,189,248,0.4); }}
        .progress {{ flex: 1; height: 6px; background: var(--card); border-radius: 3px; cursor: pointer; }}
        .progress-bar {{ height: 100%; background: linear-gradient(90deg, #38bdf8, #a78bfa); width: 0%; }}
        .time {{ color: #94a3b8; font-size: 0.85rem; min-width: 90px; text-align: center; }}
        .indicator {{ color: var(--text); font-weight: 600; }}
        .overlay {{ position: fixed; inset: 0; background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center; z-index: 100; }}
        .overlay.hidden {{ display: none; }}
        .start-btn {{ background: linear-gradient(135deg, #38bdf8, #a78bfa); color: #fff; border: none; padding: 20px 40px; font-size: 1.3rem; font-weight: 700; border-radius: 12px; cursor: pointer; }}
        .cc {{ position: absolute; top: 15px; right: 15px; z-index: 50; }}
        .cc.active {{ background: rgba(56,189,248,0.5); }}
    </style>
</head>
<body>
<div class="container">
    <div class="slides">
        {slides_html}
        <div class="subtitles" id="subs"><span class="subtitle-text" id="subText"></span></div>
        <button class="btn cc" id="ccBtn">CC</button>
    </div>
    <div class="controls">
        <button class="btn" id="playBtn">▶</button>
        <button class="btn" id="prevBtn">◀</button>
        <button class="btn" id="nextBtn">▶</button>
        <div class="progress" id="prog"><div class="progress-bar" id="progBar"></div></div>
        <span class="time" id="time">0:00 / 0:00</span>
        <span class="indicator" id="ind">1/{total_slides}</span>
        <button class="btn" id="volBtn">🔊</button>
        <button class="btn" id="fsBtn">⛶</button>
    </div>
</div>
<div class="overlay" id="overlay"><button class="start-btn" id="startBtn">🔊 Start Presentation</button></div>
<audio id="audio"><source src="/api/audio/{module_id}.mp3" type="audio/mpeg"></audio>
<script>
const a=document.getElementById('audio'),slides=document.querySelectorAll('.slide'),n={total_slides},subs={json.dumps(subtitles)};
let cur=0,cc=true;
const upd=i=>{{slides.forEach((s,j)=>s.classList.toggle('active',j===i));document.getElementById('ind').textContent=`${{i+1}}/${{n}}`;cur=i;}};
const fmt=s=>isNaN(s)?'0:00':`${{Math.floor(s/60)}}:${{String(Math.floor(s%60)).padStart(2,'0')}}`;
a.ontimeupdate=()=>{{
    const p=(a.currentTime/a.duration)*100||0;
    document.getElementById('progBar').style.width=`${{p}}%`;
    document.getElementById('time').textContent=`${{fmt(a.currentTime)}} / ${{fmt(a.duration)}}`;
    const si=Math.min(Math.floor(a.currentTime/(a.duration/n)),n-1);
    if(si!==cur)upd(si);
    if(cc){{const sub=subs.find(s=>a.currentTime>=s.start&&a.currentTime<s.end);document.getElementById('subText').textContent=sub?sub.text:'';}}
}};
document.getElementById('playBtn').onclick=()=>{{if(a.paused){{a.play();document.getElementById('playBtn').textContent='⏸';}}else{{a.pause();document.getElementById('playBtn').textContent='▶';}}}};
document.getElementById('prevBtn').onclick=()=>upd(Math.max(0,cur-1));
document.getElementById('nextBtn').onclick=()=>upd(Math.min(n-1,cur+1));
document.getElementById('ccBtn').onclick=function(){{cc=!cc;this.classList.toggle('active',cc);document.getElementById('subs').style.display=cc?'block':'none';}};
document.getElementById('volBtn').onclick=()=>{{a.muted=!a.muted;document.getElementById('volBtn').textContent=a.muted?'🔇':'🔊';}};
document.getElementById('fsBtn').onclick=()=>document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen();
document.getElementById('prog').onclick=e=>{{const r=e.target.getBoundingClientRect();a.currentTime=(e.clientX-r.left)/r.width*a.duration;}};
document.getElementById('startBtn').onclick=()=>{{a.muted=false;a.play();document.getElementById('overlay').classList.add('hidden');document.getElementById('playBtn').textContent='⏸';}};
a.muted=true;a.play().catch(()=>{{}});
</script>
</body>
</html>'''
    return html

async def main():
    print("=" * 60)
    print("UG CONTENT GENERATION")
    print("=" * 60)
    
    # Get UG courses
    ug_courses = list(db.courses.find({"university_id": "UG_TBILISI"}))
    print(f"\n📚 Found {len(ug_courses)} UG courses")
    
    audio_dir = Path("/app/backend/audio")
    pres_dir = Path("/app/backend/presentations")
    
    # Phase 1: MCQ
    print("\n📝 PHASE 1: MCQ Completion")
    print("-" * 40)
    
    mcq_added = 0
    for course in ug_courses:
        course_id = course["external_id"]
        current = db.mcq_questions.count_documents({"course_id": course_id})
        if current < 200:
            added = await complete_mcq_for_course(course_id)
            mcq_added += added
    
    print(f"\n✓ Added {mcq_added} MCQ questions")
    
    # Phase 2: Content Generation
    print("\n🎙️ PHASE 2: Scripts, Audio & Presentations")
    print("-" * 40)
    
    processed = 0
    
    for course in ug_courses:
        course_id = course["external_id"]
        course_name = course.get("course_name", course_id)
        
        # Ensure modules exist
        modules = list(db.modules.find({"courseId": course_id}))
        if not modules:
            for i in range(3):
                m = {
                    "module_id": f"{course_id}_M{i+1:02d}",
                    "courseId": course_id,
                    "title": f"{course_name} - Part {i+1}",
                    "order": i + 1
                }
                db.modules.update_one({"module_id": m["module_id"]}, {"$set": m}, upsert=True)
            modules = list(db.modules.find({"courseId": course_id}))
        
        for module in modules:
            module_id = module["module_id"]
            module_title = module.get("title", module_id)
            
            audio_path = audio_dir / f"{module_id}.mp3"
            pres_path = pres_dir / f"{module_id}.html"
            
            # Skip if complete
            if audio_path.exists() and pres_path.exists():
                continue
            
            print(f"  {module_id}...")
            
            # Get or generate script
            script_doc = db.module_scripts.find_one({"module_id": module_id})
            if script_doc and script_doc.get("script_text"):
                script = script_doc["script_text"]
            else:
                script = await generate_script(course_name, module_title)
                if script:
                    db.module_scripts.update_one(
                        {"module_id": module_id},
                        {"$set": {
                            "module_id": module_id,
                            "course_id": course_id,
                            "script_text": script,
                            "word_count": len(script.split()),
                            "status": "generated"
                        }},
                        upsert=True
                    )
            
            if not script:
                print(f"    ✗ No script")
                continue
            
            # Generate audio
            if not audio_path.exists():
                ok = await generate_audio(script, str(audio_path))
                if ok:
                    print(f"    ✓ Audio")
                else:
                    continue
            
            # Generate presentation
            if not pres_path.exists():
                html = create_presentation(module_id, course_name, module_title, script)
                with open(pres_path, "w") as f:
                    f.write(html)
                print(f"    ✓ Presentation")
            
            processed += 1
            await asyncio.sleep(0.5)
    
    print(f"\n{'='*60}")
    print(f"✅ COMPLETE! Processed {processed} modules")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(main())
