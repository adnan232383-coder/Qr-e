#!/usr/bin/env python3
"""
Podcast Generator with Retry Logic
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from pymongo import MongoClient
import uuid
import sys

client = MongoClient('mongodb://localhost:27017')
db = client['test_database']
API_KEY = 'sk-emergent-a5308B4287b53E8405'

AUDIO_DIR = Path("/app/backend/audio")
PRES_DIR = Path("/app/backend/presentations")

async def generate_podcast_script(course_name: str, module_title: str):
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    for attempt in range(3):
        try:
            chat = LlmChat(
                api_key=API_KEY,
                session_id=f"pod_{uuid.uuid4().hex[:8]}",
                system_message="Write 400-600 word educational podcast scripts about medical topics. Make it conversational and engaging."
            ).with_model("openai", "gpt-4o")
            
            result = await chat.send_message(UserMessage(text=f"Write a podcast script about {course_name}: {module_title}. Cover key concepts in a conversational way."))
            return result.strip()
        except Exception as e:
            print(f"    Script attempt {attempt+1} failed: {e}")
            await asyncio.sleep(2)
    return None

async def generate_audio(script: str, output_path: str):
    from emergentintegrations.llm.openai import OpenAITextToSpeech
    
    for attempt in range(3):
        try:
            tts = OpenAITextToSpeech(api_key=API_KEY)
            audio = await tts.generate_speech(text=script[:4096], model="tts-1-hd", voice="nova")
            with open(output_path, "wb") as f:
                f.write(audio)
            return True
        except Exception as e:
            print(f"    Audio attempt {attempt+1} failed: {e}")
            await asyncio.sleep(3)
    return False

def create_podcast_html(module_id, course_name, module_title, script):
    words = script.split()
    wps = 2.5
    segments = []
    for i in range(0, len(words), 30):
        segments.append({"start": round(i/wps,2), "end": round(min((i+30)/wps, len(words)/wps),2), "text": " ".join(words[i:i+30])})
    
    return f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{module_title} - Podcast</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}:root{{--bg:#0f0f23;--card:#1a1a2e;--text:#eaeaea;--acc:#00d9ff;--acc2:#ff6b9d}}body{{font-family:Inter,system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh}}.c{{max-width:900px;margin:0 auto;padding:40px 20px}}.hdr{{text-align:center;margin-bottom:40px}}.badge{{display:inline-flex;align-items:center;gap:8px;background:linear-gradient(135deg,var(--acc),var(--acc2));padding:8px 20px;border-radius:30px;font-size:.85rem;font-weight:600;margin-bottom:20px}}.title{{font-size:2.5rem;font-weight:800;background:linear-gradient(135deg,var(--acc),var(--acc2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:10px}}.sub{{font-size:1.2rem;color:#888}}.player{{background:var(--card);border-radius:20px;padding:30px;margin-bottom:30px}}.wave{{height:60px;background:linear-gradient(90deg,var(--acc),var(--acc2));border-radius:10px;margin-bottom:20px;opacity:.3;position:relative}}.wave::after{{content:'';position:absolute;top:0;left:0;height:100%;width:var(--p,0%);background:linear-gradient(90deg,var(--acc),var(--acc2));opacity:1}}.ctrl{{display:flex;align-items:center;gap:20px}}.play{{width:70px;height:70px;border-radius:50%;background:linear-gradient(135deg,var(--acc),var(--acc2));border:none;cursor:pointer;font-size:1.8rem;color:#fff}}.play:hover{{transform:scale(1.1)}}.info{{flex:1}}.time{{font-size:1.1rem;font-weight:600;margin-bottom:5px}}.prog{{height:6px;background:#333;border-radius:3px;cursor:pointer}}.fill{{height:100%;background:linear-gradient(90deg,var(--acc),var(--acc2));width:0%}}.spd{{background:#333;border:none;color:var(--text);padding:10px 15px;border-radius:8px;cursor:pointer;font-weight:600}}.trans{{background:var(--card);border-radius:20px;padding:30px}}.trans-title{{font-size:1.3rem;font-weight:700;margin-bottom:20px}}.trans-content{{max-height:400px;overflow-y:auto;line-height:1.8;font-size:1.05rem;color:#bbb}}.seg{{padding:10px;border-radius:8px;margin-bottom:5px;cursor:pointer}}.seg.active{{background:rgba(0,217,255,.1);color:var(--text)}}.ov{{position:fixed;inset:0;background:rgba(0,0,0,.9);display:flex;align-items:center;justify-content:center;z-index:100}}.ov.h{{display:none}}.start{{background:linear-gradient(135deg,var(--acc),var(--acc2));color:#fff;border:none;padding:25px 50px;font-size:1.4rem;font-weight:700;border-radius:50px;cursor:pointer}}</style></head>
<body><div class="c"><div class="hdr"><div class="badge">🎙️ MEDICAL PODCAST</div><h1 class="title">{module_title}</h1><p class="sub">{course_name}</p></div><div class="player"><div class="wave" id="wave"></div><div class="ctrl"><button class="play" id="pb">▶</button><div class="info"><div class="time" id="tm">0:00 / 0:00</div><div class="prog" id="pg"><div class="fill" id="fl"></div></div></div><button class="spd" id="sp">1x</button></div></div><div class="trans"><div class="trans-title">📝 Transcript</div><div class="trans-content" id="tr">{"".join([f'<div class="seg" data-s="{s["start"]}" data-e="{s["end"]}">{s["text"]}</div>' for s in segments])}</div></div></div><div class="ov" id="ov"><button class="start" id="st">🎧 Start</button></div><audio id="a"><source src="/api/audio/{module_id}.mp3" type="audio/mpeg"></audio>
<script>const a=document.getElementById('a'),segs=document.querySelectorAll('.seg'),spds=[1,1.25,1.5,2];let si=0;const fmt=s=>isNaN(s)?'0:00':`${{Math.floor(s/60)}}:${{String(Math.floor(s%60)).padStart(2,'0')}}`;a.ontimeupdate=()=>{{const p=(a.currentTime/a.duration)*100||0;document.getElementById('fl').style.width=`${{p}}%`;document.getElementById('wave').style.setProperty('--p',`${{p}}%`);document.getElementById('tm').textContent=`${{fmt(a.currentTime)}} / ${{fmt(a.duration)}}`;segs.forEach(s=>{{const st=parseFloat(s.dataset.s),en=parseFloat(s.dataset.e);s.classList.toggle('active',a.currentTime>=st&&a.currentTime<en);if(s.classList.contains('active'))s.scrollIntoView({{behavior:'smooth',block:'center'}})}});}};document.getElementById('pb').onclick=()=>{{if(a.paused){{a.play();document.getElementById('pb').textContent='⏸'}}else{{a.pause();document.getElementById('pb').textContent='▶'}}}};document.getElementById('pg').onclick=e=>{{const r=e.target.getBoundingClientRect();a.currentTime=((e.clientX-r.left)/r.width)*a.duration}};document.getElementById('sp').onclick=()=>{{si=(si+1)%4;a.playbackRate=spds[si];document.getElementById('sp').textContent=`${{spds[si]}}x`}};document.getElementById('st').onclick=()=>{{a.play();document.getElementById('ov').classList.add('h');document.getElementById('pb').textContent='⏸'}};segs.forEach(s=>s.onclick=()=>{{a.currentTime=parseFloat(s.dataset.s);if(a.paused)a.play()}});</script></body></html>'''

async def main():
    print("="*60, flush=True)
    print("🎙️ PODCAST GENERATOR (with retry)", flush=True)
    print("="*60, flush=True)
    print(f"Started: {datetime.now()}", flush=True)
    sys.stdout.flush()
    
    AUDIO_DIR.mkdir(exist_ok=True)
    PRES_DIR.mkdir(exist_ok=True)
    
    ug = list(db.courses.find({"university_id": "UG_TBILISI"}))
    
    # Find incomplete
    todo = []
    for c in ug:
        cid = c["external_id"]
        if not all((AUDIO_DIR / f"{cid}_M{i:02d}.mp3").exists() for i in range(1, 4)):
            todo.append(c)
    
    print(f"\nCourses to process: {len(todo)}", flush=True)
    print("-"*60, flush=True)
    sys.stdout.flush()
    
    done = 0
    fail = 0
    
    for i, course in enumerate(todo):
        cid = course["external_id"]
        cname = course.get("course_name", cid)
        
        print(f"\n[{i+1}/{len(todo)}] {cid}", flush=True)
        sys.stdout.flush()
        
        mods = list(db.modules.find({"courseId": cid}))
        if not mods:
            for j in range(3):
                db.modules.update_one({"module_id": f"{cid}_M{j+1:02d}"}, {"$set": {"module_id": f"{cid}_M{j+1:02d}", "courseId": cid, "title": f"{cname} - Part {j+1}", "order": j+1}}, upsert=True)
            mods = list(db.modules.find({"courseId": cid}))
        
        for mod in mods:
            mid = mod["module_id"]
            mtitle = mod.get("title", mid)
            
            apath = AUDIO_DIR / f"{mid}.mp3"
            ppath = PRES_DIR / f"{mid}.html"
            
            if apath.exists() and ppath.exists():
                continue
            
            print(f"  {mid}...", flush=True)
            sys.stdout.flush()
            
            sd = db.module_scripts.find_one({"module_id": mid})
            script = sd.get("script_text") if sd else None
            
            if not script:
                script = await generate_podcast_script(cname, mtitle)
                if script:
                    db.module_scripts.update_one({"module_id": mid}, {"$set": {"module_id": mid, "course_id": cid, "script_text": script, "type": "podcast"}}, upsert=True)
            
            if not script:
                print(f"    ✗ Script failed", flush=True)
                fail += 1
                continue
            
            if not apath.exists():
                if await generate_audio(script, str(apath)):
                    print(f"    ✓ Audio", flush=True)
                else:
                    print(f"    ✗ Audio failed", flush=True)
                    fail += 1
                    continue
            
            if not ppath.exists():
                with open(ppath, "w") as f:
                    f.write(create_podcast_html(mid, cname, mtitle, script))
                print(f"    ✓ HTML", flush=True)
            
            done += 1
            sys.stdout.flush()
            await asyncio.sleep(0.5)
        
        if (i+1) % 5 == 0:
            print(f"\n*** CHECKPOINT: {i+1}/{len(todo)}, Done: {done}, Fail: {fail} ***\n", flush=True)
            sys.stdout.flush()
    
    print(f"\n{'='*60}", flush=True)
    print(f"✅ COMPLETE! Done: {done}, Failed: {fail}", flush=True)
    print(f"Finished: {datetime.now()}", flush=True)
    sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main())
