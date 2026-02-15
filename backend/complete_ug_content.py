#!/usr/bin/env python3
"""
Complete UG Content Generator
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
import random

# Setup
client = MongoClient('mongodb://localhost:27017')
db = client['test_database']

API_KEY = os.environ.get('EMERGENT_LLM_KEY', 'sk-emergent-a5308B4287b53E8405')

# Courses that need MCQ (under 200)
COURSES_NEED_MCQ = [
    "UG_DENT_Y1_S1_C01", "UG_DENT_Y1_S1_C02", "UG_DENT_Y1_S1_C03", 
    "UG_DENT_Y1_S1_C04", "UG_DENT_Y1_S1_C05", "UG_DENT_Y2_S1_C01",
    "UG_DENT_Y2_S1_C02", "UG_DENT_Y2_S1_C03", "UG_DENT_Y2_S1_C04",
    "UG_DENT_Y2_S1_C05", "UG_DENT_Y1_S2_C06", "UG_DENT_Y1_S2_C07",
    "UG_DENT_Y1_S2_C08", "UG_DENT_Y1_S2_C09", "UG_DENT_Y1_S2_C10",
    "UG_DENT_Y2_S2_C06", "UG_DENT_Y2_S2_C07", "UG_DENT_Y2_S2_C08",
    "UG_DENT_Y2_S2_C09", "UG_DENT_Y2_S2_C10"
]

async def generate_mcq_batch(course_id: str, course_name: str, description: str, count: int = 25):
    """Generate a batch of MCQ questions"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    chat = LlmChat(
        api_key=API_KEY,
        session_id=f"mcq_{uuid.uuid4().hex[:8]}",
        system_message="""You are a medical education expert creating high-quality MCQ questions.
Create questions suitable for medical/dental board exam preparation.
IMPORTANT: Distribute correct answers evenly - approximately 25% A, 25% B, 25% C, 25% D.
Always return valid JSON array only, no other text."""
    ).with_model("openai", "gpt-4o")
    
    prompt = f"""Generate {count} multiple-choice questions for:
Course: {course_name}
Description: {description}

Requirements:
1. Distribute correct answers: ~{count//4} should be A, ~{count//4} B, ~{count//4} C, ~{count//4} D
2. Vary difficulty: 30% easy, 50% medium, 20% hard
3. Cover different topics within {course_name}
4. Make questions clinically relevant

Format as JSON array ONLY:
[{{"question": "...", "option_a": "...", "option_b": "...", "option_c": "...", "option_d": "...", "correct_answer": "A", "explanation": "...", "difficulty": "medium"}}]"""

    try:
        response = await chat.send_message(UserMessage(text=prompt))
        json_start = response.find('[')
        json_end = response.rfind(']') + 1
        if json_start >= 0 and json_end > json_start:
            return json.loads(response[json_start:json_end])
    except Exception as e:
        print(f"  Error generating MCQ: {e}")
    return []

async def complete_mcq_for_course(course_id: str):
    """Complete MCQ to 200 for a course"""
    course = db.courses.find_one({"external_id": course_id})
    if not course:
        print(f"Course {course_id} not found!")
        return 0
    
    current_count = db.mcq_questions.count_documents({"course_id": course_id})
    needed = 200 - current_count
    
    if needed <= 0:
        print(f"  {course_id}: Already has {current_count} MCQ")
        return 0
    
    print(f"  {course_id}: Has {current_count}, need {needed} more")
    
    course_name = course.get("course_name", course_id)
    description = course.get("course_description", "")
    
    total_added = 0
    batches = (needed + 24) // 25  # 25 per batch
    
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
            print(f"    Batch {batch+1}: Added {len(questions)} questions (total: {current_count + total_added})")
        
        await asyncio.sleep(0.5)  # Rate limiting
    
    return total_added

async def generate_module_script(module_id: str, course_name: str, module_title: str, topics: list):
    """Generate a lecture script for a module"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    chat = LlmChat(
        api_key=API_KEY,
        session_id=f"script_{uuid.uuid4().hex[:8]}",
        system_message="""You are an expert medical educator creating engaging lecture scripts.
Write scripts that are clear, educational, and suitable for text-to-speech narration.
Scripts should be 3-5 minutes when read aloud (approximately 450-750 words)."""
    ).with_model("openai", "gpt-4o")
    
    topics_str = ", ".join(topics) if topics else module_title
    
    prompt = f"""Create a lecture script for:
Course: {course_name}
Module: {module_title}
Topics to cover: {topics_str}

Requirements:
1. Length: 450-750 words (3-5 minutes when spoken)
2. Structure: Introduction, main content (3-4 key points), conclusion
3. Tone: Professional but engaging, suitable for medical students
4. Include key definitions and clinical relevance
5. Do NOT include slide instructions or visual references

Return ONLY the script text, ready for text-to-speech."""

    try:
        response = await chat.send_message(UserMessage(text=prompt))
        return response.strip()
    except Exception as e:
        print(f"  Error generating script: {e}")
    return None

async def generate_audio_tts(script_text: str, output_path: str):
    """Generate audio using OpenAI TTS"""
    from emergentintegrations.llm.tts import text_to_speech
    
    try:
        audio_file = await text_to_speech(
            api_key=API_KEY,
            text=script_text,
            voice="nova",  # Professional female voice
            model="tts-1-hd"
        )
        
        # Copy to destination
        import shutil
        shutil.copy(audio_file, output_path)
        return True
    except Exception as e:
        print(f"  Error generating audio: {e}")
    return False

def create_presentation_html(module_id: str, course_name: str, module_title: str, script_text: str, slides_data: list):
    """Create HTML presentation with slides and audio"""
    
    # Split script into slide segments (roughly 4-7 slides)
    sentences = script_text.replace('\n\n', '\n').split('. ')
    sentences = [s.strip() + '.' for s in sentences if s.strip()]
    
    # Create slides from script
    slides_per_segment = max(1, len(sentences) // 6)
    slides = []
    
    # Title slide
    slides.append({
        "type": "title",
        "title": module_title,
        "subtitle": course_name
    })
    
    # Content slides
    current_points = []
    slide_num = 1
    for i, sentence in enumerate(sentences):
        current_points.append(sentence)
        if len(current_points) >= 3 or i == len(sentences) - 1:
            if current_points:
                slides.append({
                    "type": "content",
                    "title": f"Key Concepts {slide_num}",
                    "points": current_points[:3]
                })
                current_points = current_points[3:]
                slide_num += 1
                if slide_num > 6:  # Max 7 slides total
                    break
    
    # Summary slide
    slides.append({
        "type": "summary",
        "title": "Summary",
        "points": ["Key concepts covered", "Clinical applications", "Review and practice"]
    })
    
    # Generate HTML
    slides_html = ""
    for i, slide in enumerate(slides):
        if slide["type"] == "title":
            slides_html += f'''
            <div class="slide title-slide {'active' if i == 0 else ''}" data-index="{i}">
                <div class="slide-inner">
                    <h1>{slide["title"]}</h1>
                    <p class="course-name">{slide["subtitle"]}</p>
                </div>
            </div>'''
        else:
            points_html = "".join([f'<li><span class="bullet"></span>{p}</li>' for p in slide.get("points", [])])
            slides_html += f'''
            <div class="slide content-slide {'active' if i == 0 else ''}" data-index="{i}">
                <div class="slide-inner">
                    <h2>{slide["title"]}</h2>
                    <ul class="points">{points_html}</ul>
                </div>
            </div>'''
    
    # Calculate timing for subtitles
    words = script_text.split()
    words_per_second = 2.5
    total_duration = len(words) / words_per_second
    
    # Create subtitle segments
    subtitle_segments = []
    words_per_segment = 12
    for i in range(0, len(words), words_per_segment):
        segment_words = words[i:i+words_per_segment]
        start_time = i / words_per_second
        end_time = min((i + words_per_segment) / words_per_second, total_duration)
        subtitle_segments.append({
            "start": round(start_time, 2),
            "end": round(end_time, 2),
            "text": " ".join(segment_words)
        })
    
    subtitles_json = json.dumps(subtitle_segments)
    
    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{module_title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        :root {{
            --bg: #0a0f1a;
            --card: #151d2e;
            --text: #f1f5f9;
            --text-muted: #94a3b8;
            --accent: #38bdf8;
            --gradient: linear-gradient(135deg, #38bdf8 0%, #a78bfa 100%);
        }}
        
        body {{
            font-family: 'Inter', sans-serif;
            background: var(--bg);
            color: var(--text);
            overflow: hidden;
            height: 100vh;
        }}
        
        .presentation-container {{
            display: flex;
            flex-direction: column;
            height: 100vh;
        }}
        
        .slides-panel {{
            flex: 1;
            position: relative;
            overflow: hidden;
        }}
        
        .slide {{
            position: absolute;
            inset: 0;
            padding: 60px;
            opacity: 0;
            transform: translateX(60px);
            transition: all 0.6s ease;
            pointer-events: none;
            display: flex;
            flex-direction: column;
        }}
        
        .slide.active {{
            opacity: 1;
            transform: translateX(0);
            pointer-events: auto;
        }}
        
        .slide-inner {{
            height: 100%;
            display: flex;
            flex-direction: column;
        }}
        
        .title-slide .slide-inner {{
            justify-content: center;
            align-items: center;
            text-align: center;
        }}
        
        .title-slide h1 {{
            font-size: 4rem;
            font-weight: 800;
            background: var(--gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 20px;
        }}
        
        .course-name {{
            font-size: 1.8rem;
            color: var(--text-muted);
            font-weight: 600;
        }}
        
        .content-slide h2 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 40px;
            padding-bottom: 15px;
            border-bottom: 3px solid var(--card);
        }}
        
        .points {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        
        .points li {{
            display: flex;
            align-items: flex-start;
            gap: 15px;
            padding: 20px 25px;
            background: var(--card);
            border-radius: 12px;
            font-size: 1.4rem;
            font-weight: 500;
            line-height: 1.6;
            border-left: 4px solid var(--accent);
        }}
        
        .points li .bullet {{
            width: 10px;
            height: 10px;
            background: var(--accent);
            border-radius: 50%;
            margin-top: 10px;
            flex-shrink: 0;
        }}
        
        /* Subtitles */
        .subtitles-container {{
            position: absolute;
            bottom: 100px;
            left: 50%;
            transform: translateX(-50%);
            width: 90%;
            max-width: 800px;
            text-align: center;
            z-index: 50;
        }}
        
        .subtitle-text {{
            display: inline-block;
            background: rgba(0, 0, 0, 0.85);
            color: #ffffff;
            font-size: 1.5rem;
            font-weight: 600;
            padding: 15px 30px;
            border-radius: 10px;
            line-height: 1.5;
        }}
        
        /* Controls */
        .controls-bar {{
            height: 80px;
            background: rgba(15, 23, 42, 0.95);
            border-top: 1px solid rgba(255,255,255,0.1);
            display: flex;
            align-items: center;
            padding: 0 30px;
            gap: 20px;
        }}
        
        .control-btn {{
            background: rgba(56, 189, 248, 0.2);
            border: 1px solid rgba(56, 189, 248, 0.3);
            color: var(--accent);
            width: 50px;
            height: 50px;
            border-radius: 12px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            transition: all 0.2s;
        }}
        
        .control-btn:hover {{
            background: rgba(56, 189, 248, 0.4);
        }}
        
        .progress-container {{
            flex: 1;
            height: 8px;
            background: var(--card);
            border-radius: 4px;
            overflow: hidden;
            cursor: pointer;
        }}
        
        .progress-bar {{
            height: 100%;
            background: var(--gradient);
            width: 0%;
            transition: width 0.1s;
        }}
        
        .time-display {{
            color: var(--text-muted);
            font-size: 0.9rem;
            min-width: 100px;
            text-align: center;
        }}
        
        .slide-indicator {{
            color: var(--text);
            font-size: 1rem;
            font-weight: 600;
        }}
        
        /* Unmute overlay */
        .unmute-overlay {{
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }}
        
        .unmute-overlay.hidden {{
            display: none;
        }}
        
        .unmute-btn {{
            background: var(--gradient);
            color: white;
            border: none;
            padding: 25px 50px;
            font-size: 1.5rem;
            font-weight: 700;
            border-radius: 16px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .cc-btn {{
            position: absolute;
            top: 20px;
            right: 20px;
            z-index: 100;
        }}
        
        .cc-btn.active {{
            background: rgba(56, 189, 248, 0.5);
        }}
    </style>
</head>
<body>
    <div class="presentation-container">
        <div class="slides-panel">
            {slides_html}
            
            <div class="subtitles-container" id="subtitles">
                <span class="subtitle-text" id="subtitleText"></span>
            </div>
            
            <button class="control-btn cc-btn" id="ccBtn" title="Subtitles">CC</button>
        </div>
        
        <div class="controls-bar">
            <button class="control-btn" id="playBtn">▶</button>
            <button class="control-btn" id="prevBtn">◀</button>
            <button class="control-btn" id="nextBtn">▶</button>
            <div class="progress-container" id="progressContainer">
                <div class="progress-bar" id="progressBar"></div>
            </div>
            <span class="time-display" id="timeDisplay">0:00 / 0:00</span>
            <span class="slide-indicator" id="slideIndicator">1/{len(slides)}</span>
            <button class="control-btn" id="volumeBtn">🔊</button>
            <button class="control-btn" id="fullscreenBtn">⛶</button>
        </div>
    </div>
    
    <div class="unmute-overlay" id="unmuteOverlay">
        <button class="unmute-btn" id="unmuteBtn">
            🔊 Click to Start with Audio
        </button>
    </div>
    
    <audio id="audio" preload="auto">
        <source src="/api/audio/{module_id}.mp3" type="audio/mpeg">
    </audio>
    
    <script>
        const audio = document.getElementById('audio');
        const slides = document.querySelectorAll('.slide');
        const totalSlides = slides.length;
        const subtitles = {subtitles_json};
        
        let currentSlide = 0;
        let subtitlesEnabled = true;
        
        // Slide timing based on audio duration
        const slideDuration = audio.duration / totalSlides || 30;
        
        function updateSlide(index) {{
            slides.forEach((s, i) => s.classList.toggle('active', i === index));
            document.getElementById('slideIndicator').textContent = `${{index + 1}}/${{totalSlides}}`;
            currentSlide = index;
        }}
        
        function updateProgress() {{
            const progress = (audio.currentTime / audio.duration) * 100 || 0;
            document.getElementById('progressBar').style.width = `${{progress}}%`;
            
            const current = formatTime(audio.currentTime);
            const total = formatTime(audio.duration);
            document.getElementById('timeDisplay').textContent = `${{current}} / ${{total}}`;
            
            // Update slide based on audio time
            const slideIndex = Math.min(Math.floor(audio.currentTime / slideDuration), totalSlides - 1);
            if (slideIndex !== currentSlide) updateSlide(slideIndex);
            
            // Update subtitles
            if (subtitlesEnabled) {{
                const sub = subtitles.find(s => audio.currentTime >= s.start && audio.currentTime < s.end);
                document.getElementById('subtitleText').textContent = sub ? sub.text : '';
            }}
        }}
        
        function formatTime(s) {{
            if (isNaN(s)) return '0:00';
            const m = Math.floor(s / 60);
            const sec = Math.floor(s % 60);
            return `${{m}}:${{sec.toString().padStart(2, '0')}}`;
        }}
        
        // Event listeners
        document.getElementById('playBtn').onclick = () => {{
            if (audio.paused) {{
                audio.play();
                document.getElementById('playBtn').textContent = '⏸';
            }} else {{
                audio.pause();
                document.getElementById('playBtn').textContent = '▶';
            }}
        }};
        
        document.getElementById('prevBtn').onclick = () => updateSlide(Math.max(0, currentSlide - 1));
        document.getElementById('nextBtn').onclick = () => updateSlide(Math.min(totalSlides - 1, currentSlide + 1));
        
        document.getElementById('ccBtn').onclick = function() {{
            subtitlesEnabled = !subtitlesEnabled;
            this.classList.toggle('active', subtitlesEnabled);
            document.getElementById('subtitles').style.display = subtitlesEnabled ? 'block' : 'none';
        }};
        
        document.getElementById('volumeBtn').onclick = () => {{
            audio.muted = !audio.muted;
            document.getElementById('volumeBtn').textContent = audio.muted ? '🔇' : '🔊';
        }};
        
        document.getElementById('fullscreenBtn').onclick = () => {{
            if (document.fullscreenElement) {{
                document.exitFullscreen();
            }} else {{
                document.documentElement.requestFullscreen();
            }}
        }};
        
        document.getElementById('progressContainer').onclick = (e) => {{
            const rect = e.target.getBoundingClientRect();
            const pos = (e.clientX - rect.left) / rect.width;
            audio.currentTime = pos * audio.duration;
        }};
        
        document.getElementById('unmuteBtn').onclick = () => {{
            audio.muted = false;
            audio.play();
            document.getElementById('unmuteOverlay').classList.add('hidden');
            document.getElementById('playBtn').textContent = '⏸';
        }};
        
        audio.addEventListener('timeupdate', updateProgress);
        audio.addEventListener('loadedmetadata', updateProgress);
        
        // Auto-start muted
        audio.muted = true;
        audio.play().catch(() => {{}});
    </script>
</body>
</html>'''
    
    return html_template

async def process_all_ug_content():
    """Main function to process all UG content"""
    print("=" * 60)
    print("UG Content Generation - Starting")
    print("=" * 60)
    
    # Phase 1: MCQ Generation
    print("\n📝 PHASE 1: MCQ Generation")
    print("-" * 40)
    
    for course_id in COURSES_NEED_MCQ:
        added = await complete_mcq_for_course(course_id)
        if added > 0:
            print(f"  ✓ {course_id}: Added {added} MCQ")
    
    # Get all UG courses for script/audio/presentation generation
    ug_courses = list(db.courses.find({"external_id": {"$regex": "^UG_"}}))
    print(f"\n📚 Found {len(ug_courses)} UG courses")
    
    # Phase 2: Scripts & Audio & Presentations
    print("\n🎙️ PHASE 2: Scripts, Audio & Presentations")
    print("-" * 40)
    
    audio_dir = Path("/app/backend/audio")
    presentation_dir = Path("/app/backend/presentations")
    audio_dir.mkdir(exist_ok=True)
    presentation_dir.mkdir(exist_ok=True)
    
    total_processed = 0
    
    for course in ug_courses:
        course_id = course["external_id"]
        course_name = course.get("course_name", course_id)
        
        # Get or create modules for this course
        modules = list(db.modules.find({"courseId": course_id}))
        
        if not modules:
            # Create 3 modules for this course
            print(f"  Creating modules for {course_id}...")
            for i in range(3):
                module = {
                    "module_id": f"{course_id}_M{i+1:02d}",
                    "courseId": course_id,
                    "title": f"{course_name} - Part {i+1}",
                    "order": i + 1,
                    "topics": [course_name]
                }
                db.modules.update_one(
                    {"module_id": module["module_id"]},
                    {"$set": module},
                    upsert=True
                )
            modules = list(db.modules.find({"courseId": course_id}))
        
        # Process each module
        for module in modules:
            module_id = module["module_id"]
            module_title = module.get("title", module_id)
            topics = module.get("topics", [course_name])
            
            audio_path = audio_dir / f"{module_id}.mp3"
            presentation_path = presentation_dir / f"{module_id}.html"
            
            # Skip if already exists
            if audio_path.exists() and presentation_path.exists():
                continue
            
            print(f"  Processing {module_id}...")
            
            # Check if script exists
            existing_script = db.module_scripts.find_one({"module_id": module_id})
            
            if existing_script and existing_script.get("script_text"):
                script_text = existing_script["script_text"]
            else:
                # Generate script
                script_text = await generate_module_script(module_id, course_name, module_title, topics)
                if script_text:
                    db.module_scripts.update_one(
                        {"module_id": module_id},
                        {"$set": {
                            "module_id": module_id,
                            "course_id": course_id,
                            "script_text": script_text,
                            "word_count": len(script_text.split()),
                            "status": "generated",
                            "created_at": datetime.now(timezone.utc).isoformat()
                        }},
                        upsert=True
                    )
            
            if not script_text:
                print(f"    ✗ Failed to generate script for {module_id}")
                continue
            
            # Generate audio if not exists
            if not audio_path.exists():
                print(f"    Generating audio...")
                success = await generate_audio_tts(script_text, str(audio_path))
                if success:
                    print(f"    ✓ Audio generated")
                else:
                    print(f"    ✗ Audio failed")
                    continue
            
            # Generate presentation
            if not presentation_path.exists():
                print(f"    Generating presentation...")
                html = create_presentation_html(module_id, course_name, module_title, script_text, [])
                with open(presentation_path, "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"    ✓ Presentation generated")
            
            total_processed += 1
            
            # Rate limiting
            await asyncio.sleep(1)
    
    print("\n" + "=" * 60)
    print(f"✅ COMPLETE! Processed {total_processed} modules")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(process_all_ug_content())
