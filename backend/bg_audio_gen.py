#!/usr/bin/env python3
"""
Background Audio & Presentation Generator for UG courses
Run with: nohup python3 bg_audio_gen.py > /tmp/audio_gen.log 2>&1 &
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from pymongo import MongoClient
import uuid

client = MongoClient('mongodb://localhost:27017')
db = client['test_database']
API_KEY = 'sk-emergent-a5308B4287b53E8405'

AUDIO_DIR = Path("/app/backend/audio")
PRES_DIR = Path("/app/backend/presentations")

async def generate_script(course_name: str, module_title: str):
    """Generate lecture script"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    chat = LlmChat(
        api_key=API_KEY,
        session_id=f"s_{uuid.uuid4().hex[:8]}",
        system_message="Write educational lecture scripts (400-600 words). Professional tone."
    ).with_model("openai", "gpt-4o")
    
    prompt = f"Write a 400-600 word lecture for {course_name}: {module_title}. Include intro, 3 key points with clinical relevance, conclusion. Return only the script text."

    try:
        return (await chat.send_message(UserMessage(text=prompt))).strip()
    except Exception as e:
        print(f"    Script error: {e}")
    return None

async def generate_audio(script: str, output_path: str):
    """Generate TTS audio"""
    from emergentintegrations.llm.openai import OpenAITextToSpeech
    
    try:
        tts = OpenAITextToSpeech(api_key=API_KEY)
        audio_bytes = await tts.generate_speech(
            text=script[:4096],
            model="tts-1-hd",
            voice="nova"
        )
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        return True
    except Exception as e:
        print(f"    Audio error: {e}")
    return False

def create_html(module_id: str, course_name: str, module_title: str, script: str):
    """Create presentation HTML"""
    sentences = [s.strip()+'.' for s in script.replace('\n',' ').split('. ') if s.strip()]
    
    slides = f'''<div class="slide title-slide active" data-index="0">
        <div class="inner"><h1>{module_title}</h1><p class="sub">{course_name}</p></div></div>'''
    
    idx = 1
    for i in range(0, min(len(sentences), 15), 3):
        chunk = sentences[i:i+3]
        pts = "".join([f'<li><span class="b"></span>{s}</li>' for s in chunk])
        slides += f'''<div class="slide" data-index="{idx}">
            <div class="inner"><h2>Key Points {idx}</h2><ul class="pts">{pts}</ul></div></div>'''
        idx += 1
        if idx > 5:
            break
    
    slides += f'''<div class="slide" data-index="{idx}">
        <div class="inner"><h2>Summary</h2><ul class="pts">
            <li><span class="b"></span>Key concepts covered</li>
            <li><span class="b"></span>Clinical applications</li>
            <li><span class="b"></span>Review and practice</li></ul></div></div>'''
    
    total = idx + 1
    words = script.split()
    subs = [{"start": round(i/2.5,2), "end": round(min((i+12)/2.5, len(words)/2.5),2), "text": " ".join(words[i:i+12])} for i in range(0, len(words), 12)]
    
    return f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{module_title}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--bg:#0a0f1a;--card:#151d2e;--txt:#f1f5f9;--acc:#38bdf8}}
body{{font-family:Inter,system-ui,sans-serif;background:var(--bg);color:var(--txt);height:100vh;overflow:hidden}}
.c{{display:flex;flex-direction:column;height:100vh}}
.sl{{flex:1;position:relative}}
.slide{{position:absolute;inset:0;padding:50px;opacity:0;transform:translateX(40px);transition:.4s}}
.slide.active{{opacity:1;transform:translateX(0)}}
.inner{{height:100%;display:flex;flex-direction:column}}
.title-slide .inner{{justify-content:center;align-items:center;text-align:center}}
.title-slide h1{{font-size:3.2rem;background:linear-gradient(135deg,#38bdf8,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.sub{{font-size:1.4rem;color:#94a3b8;margin-top:15px}}
h2{{font-size:2rem;margin-bottom:25px;border-bottom:2px solid var(--card);padding-bottom:12px}}
.pts{{list-style:none}}
.pts li{{display:flex;gap:12px;padding:15px 18px;background:var(--card);border-radius:8px;font-size:1.2rem;margin-bottom:12px;border-left:3px solid var(--acc)}}
.b{{width:8px;height:8px;background:var(--acc);border-radius:50%;margin-top:8px;flex-shrink:0}}
.subs{{position:absolute;bottom:90px;left:50%;transform:translateX(-50%);text-align:center}}
.stxt{{background:rgba(0,0,0,.85);color:#fff;font-size:1.2rem;padding:10px 20px;border-radius:6px}}
.ctrl{{height:60px;background:rgba(15,23,42,.95);border-top:1px solid rgba(255,255,255,.1);display:flex;align-items:center;padding:0 20px;gap:12px}}
.btn{{background:rgba(56,189,248,.2);border:1px solid rgba(56,189,248,.3);color:var(--acc);width:40px;height:40px;border-radius:8px;cursor:pointer;font-size:1rem}}
.btn:hover{{background:rgba(56,189,248,.4)}}
.prg{{flex:1;height:5px;background:var(--card);border-radius:3px;cursor:pointer}}
.pbar{{height:100%;background:linear-gradient(90deg,#38bdf8,#a78bfa);width:0%}}
.tm{{color:#94a3b8;font-size:.8rem;min-width:80px;text-align:center}}
.ind{{font-weight:600}}
.ov{{position:fixed;inset:0;background:rgba(0,0,0,.8);display:flex;align-items:center;justify-content:center;z-index:100}}
.ov.h{{display:none}}
.sbtn{{background:linear-gradient(135deg,#38bdf8,#a78bfa);color:#fff;border:none;padding:18px 35px;font-size:1.2rem;font-weight:700;border-radius:10px;cursor:pointer}}
.cc{{position:absolute;top:12px;right:12px;z-index:50}}
.cc.a{{background:rgba(56,189,248,.5)}}
</style></head>
<body>
<div class="c">
<div class="sl">{slides}
<div class="subs" id="ss"><span class="stxt" id="st"></span></div>
<button class="btn cc a" id="ccb">CC</button>
</div>
<div class="ctrl">
<button class="btn" id="pb">▶</button>
<button class="btn" id="pv">◀</button>
<button class="btn" id="nx">▶</button>
<div class="prg" id="pg"><div class="pbar" id="pgb"></div></div>
<span class="tm" id="tm">0:00/0:00</span>
<span class="ind" id="in">1/{total}</span>
<button class="btn" id="vb">🔊</button>
<button class="btn" id="fb">⛶</button>
</div></div>
<div class="ov" id="ov"><button class="sbtn" id="sb">🔊 Start Presentation</button></div>
<audio id="a"><source src="/api/audio/{module_id}.mp3" type="audio/mpeg"></audio>
<script>
const a=document.getElementById('a'),sl=document.querySelectorAll('.slide'),n={total},su={json.dumps(subs)};
let c=0,cc=true;
const up=i=>{{sl.forEach((s,j)=>s.classList.toggle('active',j===i));document.getElementById('in').textContent=`${{i+1}}/${{n}}`;c=i;}};
const ft=s=>isNaN(s)?'0:00':`${{Math.floor(s/60)}}:${{String(Math.floor(s%60)).padStart(2,'0')}}`;
a.ontimeupdate=()=>{{
const p=(a.currentTime/a.duration)*100||0;
document.getElementById('pgb').style.width=`${{p}}%`;
document.getElementById('tm').textContent=`${{ft(a.currentTime)}}/${{ft(a.duration)}}`;
const si=Math.min(Math.floor(a.currentTime/(a.duration/n)),n-1);
if(si!==c)up(si);
if(cc){{const s=su.find(x=>a.currentTime>=x.start&&a.currentTime<x.end);document.getElementById('st').textContent=s?s.text:'';}}
}};
document.getElementById('pb').onclick=()=>{{if(a.paused){{a.play();document.getElementById('pb').textContent='⏸';}}else{{a.pause();document.getElementById('pb').textContent='▶';}}}};
document.getElementById('pv').onclick=()=>up(Math.max(0,c-1));
document.getElementById('nx').onclick=()=>up(Math.min(n-1,c+1));
document.getElementById('ccb').onclick=function(){{cc=!cc;this.classList.toggle('a',cc);document.getElementById('ss').style.display=cc?'block':'none';}};
document.getElementById('vb').onclick=()=>{{a.muted=!a.muted;document.getElementById('vb').textContent=a.muted?'🔇':'🔊';}};
document.getElementById('fb').onclick=()=>document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen();
document.getElementById('pg').onclick=e=>{{const r=e.target.getBoundingClientRect();a.currentTime=(e.clientX-r.left)/r.width*a.duration;}};
document.getElementById('sb').onclick=()=>{{a.muted=false;a.play();document.getElementById('ov').classList.add('h');document.getElementById('pb').textContent='⏸';}};
a.muted=true;a.play().catch(()=>{{}});
</script></body></html>'''

async def process_module(course, module):
    """Process a single module"""
    cid = course["external_id"]
    cname = course.get("course_name", cid)
    mid = module["module_id"]
    mtitle = module.get("title", mid)
    
    apath = AUDIO_DIR / f"{mid}.mp3"
    ppath = PRES_DIR / f"{mid}.html"
    
    # Skip if both exist
    if apath.exists() and ppath.exists():
        return "skip"
    
    print(f"  {mid}...")
    
    # Get or generate script
    sd = db.module_scripts.find_one({"module_id": mid})
    if sd and sd.get("script_text"):
        script = sd["script_text"]
    else:
        script = await generate_script(cname, mtitle)
        if script:
            db.module_scripts.update_one(
                {"module_id": mid},
                {"$set": {
                    "module_id": mid, 
                    "course_id": cid, 
                    "script_text": script, 
                    "word_count": len(script.split()),
                    "status": "generated"
                }},
                upsert=True
            )
    
    if not script:
        print(f"    ✗ No script")
        return "fail"
    
    # Generate audio
    if not apath.exists():
        if await generate_audio(script, str(apath)):
            print(f"    ✓ Audio")
        else:
            return "fail"
    
    # Generate presentation
    if not ppath.exists():
        with open(ppath, "w") as f:
            f.write(create_html(mid, cname, mtitle, script))
        print(f"    ✓ HTML")
    
    return "done"

async def main():
    print("="*60)
    print("UG AUDIO & PRESENTATION GENERATOR")
    print("="*60)
    print(f"Started at: {datetime.now()}")
    
    AUDIO_DIR.mkdir(exist_ok=True)
    PRES_DIR.mkdir(exist_ok=True)
    
    # Get UG courses
    ug = list(db.courses.find({"university_id": "UG_TBILISI"}))
    print(f"\nProcessing {len(ug)} UG courses")
    print("-"*60)
    
    total_done = 0
    total_skip = 0
    total_fail = 0
    
    for i, course in enumerate(ug):
        cid = course["external_id"]
        cname = course.get("course_name", cid)
        
        # Ensure modules exist
        mods = list(db.modules.find({"courseId": cid}))
        if not mods:
            print(f"\n[{i+1}/{len(ug)}] Creating modules for {cid}...")
            for j in range(3):
                db.modules.update_one(
                    {"module_id": f"{cid}_M{j+1:02d}"},
                    {"$set": {
                        "module_id": f"{cid}_M{j+1:02d}", 
                        "courseId": cid, 
                        "title": f"{cname} - Part {j+1}", 
                        "order": j+1
                    }},
                    upsert=True
                )
            mods = list(db.modules.find({"courseId": cid}))
        
        print(f"\n[{i+1}/{len(ug)}] {cid} ({len(mods)} modules)")
        
        for mod in mods:
            result = await process_module(course, mod)
            if result == "done":
                total_done += 1
            elif result == "skip":
                total_skip += 1
            else:
                total_fail += 1
            
            await asyncio.sleep(0.5)
        
        # Checkpoint every 10 courses
        if (i + 1) % 10 == 0:
            print(f"\n*** CHECKPOINT: {i+1}/{len(ug)} courses ***")
            print(f"    Done: {total_done}, Skip: {total_skip}, Fail: {total_fail}\n")
    
    print("\n" + "="*60)
    print(f"COMPLETE!")
    print(f"  Generated: {total_done}")
    print(f"  Skipped (already exist): {total_skip}")
    print(f"  Failed: {total_fail}")
    print(f"Finished at: {datetime.now()}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
