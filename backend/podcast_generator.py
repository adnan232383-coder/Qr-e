#!/usr/bin/env python3
"""
Podcast Generator for UG Courses
Creates conversational podcast-style content with two speakers
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from pymongo import MongoClient
import uuid

client = MongoClient('mongodb://localhost:27017')
db = client['test_database']
API_KEY = 'sk-emergent-a5308B4287b53E8405'

AUDIO_DIR = Path("/app/backend/audio")
PRES_DIR = Path("/app/backend/presentations")

async def generate_podcast_script(course_name: str, module_title: str):
    """Generate a podcast-style conversational script"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    chat = LlmChat(
        api_key=API_KEY,
        session_id=f"pod_{uuid.uuid4().hex[:8]}",
        system_message="""You write engaging educational podcast scripts with two hosts discussing medical topics.
Host 1 (Dr. Sarah) - Expert, explains concepts clearly
Host 2 (Mike) - Curious learner, asks good questions

Keep it conversational, educational, and engaging. 400-600 words total."""
    ).with_model("openai", "gpt-4o")
    
    prompt = f"""Write a podcast script for:
Topic: {course_name} - {module_title}

Format:
- Start with brief intro
- Natural conversation between Dr. Sarah (expert) and Mike (learner)
- Cover 3-4 key concepts
- End with summary

Return ONLY the script text (no speaker labels for TTS), making it flow naturally as narration."""

    try:
        return (await chat.send_message(UserMessage(text=prompt))).strip()
    except Exception as e:
        print(f"    Script error: {e}")
    return None

async def generate_audio(script: str, output_path: str, voice: str = "nova"):
    """Generate TTS audio"""
    from emergentintegrations.llm.openai import OpenAITextToSpeech
    
    try:
        tts = OpenAITextToSpeech(api_key=API_KEY)
        audio = await tts.generate_speech(
            text=script[:4096],
            model="tts-1-hd",
            voice=voice
        )
        with open(output_path, "wb") as f:
            f.write(audio)
        return True
    except Exception as e:
        print(f"    Audio error: {e}")
    return False

def create_podcast_html(module_id: str, course_name: str, module_title: str, script: str):
    """Create podcast player HTML"""
    
    # Create simple segments for display
    paragraphs = [p.strip() for p in script.split('\n\n') if p.strip()]
    
    # Estimate timing
    words = script.split()
    wps = 2.5
    total_duration = len(words) / wps
    
    # Create transcript segments
    segments = []
    words_per_seg = 30
    for i in range(0, len(words), words_per_seg):
        seg_words = words[i:i+words_per_seg]
        segments.append({
            "start": round(i / wps, 2),
            "end": round(min((i + words_per_seg) / wps, total_duration), 2),
            "text": " ".join(seg_words)
        })
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{module_title} - Podcast</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{ --bg: #0f0f23; --card: #1a1a2e; --text: #eaeaea; --accent: #00d9ff; --accent2: #ff6b9d; }}
        body {{ font-family: 'Inter', system-ui, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }}
        
        .container {{ max-width: 900px; margin: 0 auto; padding: 40px 20px; }}
        
        .podcast-header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        
        .podcast-badge {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: linear-gradient(135deg, var(--accent), var(--accent2));
            padding: 8px 20px;
            border-radius: 30px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 20px;
        }}
        
        .podcast-title {{
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--accent), var(--accent2));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        
        .podcast-subtitle {{
            font-size: 1.2rem;
            color: #888;
        }}
        
        .player-card {{
            background: var(--card);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }}
        
        .waveform {{
            height: 60px;
            background: linear-gradient(90deg, var(--accent) 0%, var(--accent2) 50%, var(--accent) 100%);
            border-radius: 10px;
            margin-bottom: 20px;
            opacity: 0.3;
            position: relative;
            overflow: hidden;
        }}
        
        .waveform::after {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            height: 100%;
            width: var(--progress, 0%);
            background: linear-gradient(90deg, var(--accent), var(--accent2));
            opacity: 1;
            transition: width 0.1s;
        }}
        
        .player-controls {{
            display: flex;
            align-items: center;
            gap: 20px;
        }}
        
        .play-btn {{
            width: 70px;
            height: 70px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--accent), var(--accent2));
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8rem;
            color: #fff;
            transition: transform 0.2s;
        }}
        
        .play-btn:hover {{ transform: scale(1.1); }}
        
        .time-info {{
            flex: 1;
        }}
        
        .time-display {{
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 5px;
        }}
        
        .progress-bar {{
            height: 6px;
            background: #333;
            border-radius: 3px;
            cursor: pointer;
            overflow: hidden;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--accent), var(--accent2));
            width: 0%;
            transition: width 0.1s;
        }}
        
        .speed-btn {{
            background: #333;
            border: none;
            color: var(--text);
            padding: 10px 15px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }}
        
        .transcript {{
            background: var(--card);
            border-radius: 20px;
            padding: 30px;
        }}
        
        .transcript-title {{
            font-size: 1.3rem;
            font-weight: 700;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .transcript-content {{
            max-height: 400px;
            overflow-y: auto;
            line-height: 1.8;
            font-size: 1.05rem;
            color: #bbb;
        }}
        
        .transcript-segment {{
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 5px;
            transition: background 0.3s;
        }}
        
        .transcript-segment.active {{
            background: rgba(0, 217, 255, 0.1);
            color: var(--text);
        }}
        
        .overlay {{
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 100;
        }}
        
        .overlay.hidden {{ display: none; }}
        
        .start-btn {{
            background: linear-gradient(135deg, var(--accent), var(--accent2));
            color: #fff;
            border: none;
            padding: 25px 50px;
            font-size: 1.4rem;
            font-weight: 700;
            border-radius: 50px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="podcast-header">
            <div class="podcast-badge">🎙️ MEDICAL PODCAST</div>
            <h1 class="podcast-title">{module_title}</h1>
            <p class="podcast-subtitle">{course_name}</p>
        </div>
        
        <div class="player-card">
            <div class="waveform" id="waveform"></div>
            <div class="player-controls">
                <button class="play-btn" id="playBtn">▶</button>
                <div class="time-info">
                    <div class="time-display" id="timeDisplay">0:00 / 0:00</div>
                    <div class="progress-bar" id="progressBar">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                </div>
                <button class="speed-btn" id="speedBtn">1x</button>
            </div>
        </div>
        
        <div class="transcript">
            <div class="transcript-title">📝 Transcript</div>
            <div class="transcript-content" id="transcript">
                {"".join([f'<div class="transcript-segment" data-start="{s["start"]}" data-end="{s["end"]}">{s["text"]}</div>' for s in segments])}
            </div>
        </div>
    </div>
    
    <div class="overlay" id="overlay">
        <button class="start-btn" id="startBtn">🎧 Start Listening</button>
    </div>
    
    <audio id="audio" preload="auto">
        <source src="/api/audio/{module_id}.mp3" type="audio/mpeg">
    </audio>
    
    <script>
        const audio = document.getElementById('audio');
        const segments = document.querySelectorAll('.transcript-segment');
        const speeds = [1, 1.25, 1.5, 2];
        let speedIdx = 0;
        
        const fmt = s => isNaN(s) ? '0:00' : `${{Math.floor(s/60)}}:${{String(Math.floor(s%60)).padStart(2,'0')}}`;
        
        audio.ontimeupdate = () => {{
            const p = (audio.currentTime / audio.duration) * 100 || 0;
            document.getElementById('progressFill').style.width = `${{p}}%`;
            document.getElementById('waveform').style.setProperty('--progress', `${{p}}%`);
            document.getElementById('timeDisplay').textContent = `${{fmt(audio.currentTime)}} / ${{fmt(audio.duration)}}`;
            
            // Highlight current segment
            segments.forEach(seg => {{
                const start = parseFloat(seg.dataset.start);
                const end = parseFloat(seg.dataset.end);
                seg.classList.toggle('active', audio.currentTime >= start && audio.currentTime < end);
                if (seg.classList.contains('active')) {{
                    seg.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                }}
            }});
        }};
        
        document.getElementById('playBtn').onclick = () => {{
            if (audio.paused) {{
                audio.play();
                document.getElementById('playBtn').textContent = '⏸';
            }} else {{
                audio.pause();
                document.getElementById('playBtn').textContent = '▶';
            }}
        }};
        
        document.getElementById('progressBar').onclick = e => {{
            const rect = e.target.getBoundingClientRect();
            audio.currentTime = ((e.clientX - rect.left) / rect.width) * audio.duration;
        }};
        
        document.getElementById('speedBtn').onclick = () => {{
            speedIdx = (speedIdx + 1) % speeds.length;
            audio.playbackRate = speeds[speedIdx];
            document.getElementById('speedBtn').textContent = `${{speeds[speedIdx]}}x`;
        }};
        
        document.getElementById('startBtn').onclick = () => {{
            audio.play();
            document.getElementById('overlay').classList.add('hidden');
            document.getElementById('playBtn').textContent = '⏸';
        }};
        
        segments.forEach(seg => {{
            seg.onclick = () => {{
                audio.currentTime = parseFloat(seg.dataset.start);
                if (audio.paused) audio.play();
            }};
        }});
    </script>
</body>
</html>'''

async def process_remaining_courses():
    """Process all courses that don't have audio yet"""
    print("="*60)
    print("🎙️ PODCAST GENERATOR")
    print("="*60)
    print(f"Started: {datetime.now()}")
    
    AUDIO_DIR.mkdir(exist_ok=True)
    PRES_DIR.mkdir(exist_ok=True)
    
    # Get UG courses
    ug = list(db.courses.find({"university_id": "UG_TBILISI"}))
    
    # Find courses without complete audio
    courses_todo = []
    for c in ug:
        cid = c["external_id"]
        # Check if all 3 modules have audio
        has_all = all((AUDIO_DIR / f"{cid}_M{i:02d}.mp3").exists() for i in range(1, 4))
        if not has_all:
            courses_todo.append(c)
    
    print(f"\nCourses needing podcasts: {len(courses_todo)}")
    print("-"*60)
    
    done = 0
    failed = 0
    
    for i, course in enumerate(courses_todo):
        cid = course["external_id"]
        cname = course.get("course_name", cid)
        
        print(f"\n[{i+1}/{len(courses_todo)}] {cid}")
        
        # Ensure modules exist
        mods = list(db.modules.find({"courseId": cid}))
        if not mods:
            for j in range(3):
                db.modules.update_one(
                    {"module_id": f"{cid}_M{j+1:02d}"},
                    {"$set": {"module_id": f"{cid}_M{j+1:02d}", "courseId": cid, "title": f"{cname} - Part {j+1}", "order": j+1}},
                    upsert=True
                )
            mods = list(db.modules.find({"courseId": cid}))
        
        for mod in mods:
            mid = mod["module_id"]
            mtitle = mod.get("title", mid)
            
            apath = AUDIO_DIR / f"{mid}.mp3"
            ppath = PRES_DIR / f"{mid}.html"
            
            if apath.exists() and ppath.exists():
                continue
            
            print(f"  {mid}...")
            
            # Get or generate podcast script
            sd = db.module_scripts.find_one({"module_id": mid})
            script = sd.get("script_text") if sd else None
            
            if not script:
                script = await generate_podcast_script(cname, mtitle)
                if script:
                    db.module_scripts.update_one(
                        {"module_id": mid},
                        {"$set": {"module_id": mid, "course_id": cid, "script_text": script, "type": "podcast", "status": "done"}},
                        upsert=True
                    )
            
            if not script:
                print(f"    ✗ No script")
                failed += 1
                continue
            
            # Generate audio
            if not apath.exists():
                if await generate_audio(script, str(apath)):
                    print(f"    ✓ Audio")
                else:
                    failed += 1
                    continue
            
            # Generate podcast HTML
            if not ppath.exists():
                with open(ppath, "w") as f:
                    f.write(create_podcast_html(mid, cname, mtitle, script))
                print(f"    ✓ HTML")
            
            done += 1
            await asyncio.sleep(0.3)
        
        # Checkpoint
        if (i + 1) % 10 == 0:
            print(f"\n*** CHECKPOINT: {i+1}/{len(courses_todo)} courses ***")
            print(f"    Done: {done}, Failed: {failed}\n")
    
    print("\n" + "="*60)
    print(f"✅ COMPLETE!")
    print(f"   Generated: {done}")
    print(f"   Failed: {failed}")
    print(f"Finished: {datetime.now()}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(process_remaining_courses())
