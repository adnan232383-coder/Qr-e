#!/usr/bin/env python3
"""
UG Content Generator - Complete Edition
Generates MCQ, Scripts, Audio, and Presentations for all UG courses
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from pymongo import MongoClient
import uuid
from dotenv import load_dotenv

load_dotenv()

# Setup
client = MongoClient('mongodb://localhost:27017')
db = client['test_database']

API_KEY = os.environ.get('EMERGENT_LLM_KEY', 'sk-emergent-a5308B4287b53E8405')

async def generate_mcq_batch(course_id: str, course_name: str, description: str, count: int = 25):
    """Generate MCQ questions"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    chat = LlmChat(
        api_key=API_KEY,
        session_id=f"mcq_{uuid.uuid4().hex[:8]}",
        system_message="Create MCQ for medical education. Return JSON array only."
    ).with_model("openai", "gpt-4o")
    
    prompt = f"""Generate {count} MCQ for {course_name}. {description}

Distribute answers evenly: A={count//4}, B={count//4}, C={count//4}, D={count//4}

JSON only:
[{{"question":"...","option_a":"...","option_b":"...","option_c":"...","option_d":"...","correct_answer":"A","explanation":"...","difficulty":"medium"}}]"""

    try:
        response = await chat.send_message(UserMessage(text=prompt))
        j1, j2 = response.find('['), response.rfind(']') + 1
        if j1 >= 0 and j2 > j1:
            return json.loads(response[j1:j2])
    except Exception as e:
        print(f"    MCQ err: {e}")
    return []

async def complete_mcq(course_id: str):
    """Complete MCQ to 200"""
    course = db.courses.find_one({"external_id": course_id})
    if not course:
        return 0
    
    current = db.mcq_questions.count_documents({"course_id": course_id})
    needed = 200 - current
    if needed <= 0:
        return 0
    
    print(f"  {course_id}: {current}->200")
    
    added = 0
    for batch in range((needed + 24) // 25):
        size = min(25, needed - added)
        if size <= 0:
            break
        
        qs = await generate_mcq_batch(course_id, course.get("course_name", ""), course.get("course_description", ""), size)
        if qs:
            for i, q in enumerate(qs):
                q["question_id"] = f"q_{course_id}_{current+added+i:03d}"
                q["course_id"] = course_id
                q["created_at"] = datetime.now(timezone.utc).isoformat()
            db.mcq_questions.insert_many(qs)
            added += len(qs)
            print(f"    +{len(qs)}")
        await asyncio.sleep(0.5)
    
    return added

async def generate_script(course_name: str, module_title: str):
    """Generate lecture script"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    chat = LlmChat(
        api_key=API_KEY,
        session_id=f"s_{uuid.uuid4().hex[:8]}",
        system_message="Write educational lecture scripts (400-600 words)."
    ).with_model("openai", "gpt-4o")
    
    prompt = f"Write a 400-600 word lecture for {course_name}: {module_title}. Include intro, 3 key points, conclusion. Return only the script."

    try:
        return (await chat.send_message(UserMessage(text=prompt))).strip()
    except Exception as e:
        print(f"    Script err: {e}")
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
        print(f"    Audio err: {e}")
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
<div class="ov" id="ov"><button class="sbtn" id="sb">🔊 Start</button></div>
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

async def main():
    print("="*50)
    print("UG CONTENT GENERATION")
    print("="*50)
    
    ug = list(db.courses.find({"university_id": "UG_TBILISI"}))
    print(f"\n📚 {len(ug)} UG courses")
    
    adir = Path("/app/backend/audio")
    pdir = Path("/app/backend/presentations")
    
    # MCQ
    print("\n📝 MCQ Generation")
    print("-"*40)
    
    total_mcq = 0
    for c in ug:
        cid = c["external_id"]
        cur = db.mcq_questions.count_documents({"course_id": cid})
        if cur < 200:
            total_mcq += await complete_mcq(cid)
    
    print(f"\n✓ Added {total_mcq} MCQ")
    
    # Content
    print("\n🎙️ Scripts, Audio & Presentations")
    print("-"*40)
    
    done = 0
    for c in ug:
        cid = c["external_id"]
        cname = c.get("course_name", cid)
        
        # Ensure modules
        mods = list(db.modules.find({"courseId": cid}))
        if not mods:
            for i in range(3):
                db.modules.update_one(
                    {"module_id": f"{cid}_M{i+1:02d}"},
                    {"$set": {"module_id": f"{cid}_M{i+1:02d}", "courseId": cid, "title": f"{cname} - Part {i+1}", "order": i+1}},
                    upsert=True
                )
            mods = list(db.modules.find({"courseId": cid}))
        
        for m in mods:
            mid = m["module_id"]
            mtitle = m.get("title", mid)
            
            apath = adir / f"{mid}.mp3"
            ppath = pdir / f"{mid}.html"
            
            if apath.exists() and ppath.exists():
                continue
            
            print(f"  {mid}...")
            
            # Script
            sd = db.module_scripts.find_one({"module_id": mid})
            if sd and sd.get("script_text"):
                script = sd["script_text"]
            else:
                script = await generate_script(cname, mtitle)
                if script:
                    db.module_scripts.update_one(
                        {"module_id": mid},
                        {"$set": {"module_id": mid, "course_id": cid, "script_text": script, "status": "done"}},
                        upsert=True
                    )
            
            if not script:
                print(f"    ✗ No script")
                continue
            
            # Audio
            if not apath.exists():
                if await generate_audio(script, str(apath)):
                    print(f"    ✓ Audio")
                else:
                    continue
            
            # HTML
            if not ppath.exists():
                with open(ppath, "w") as f:
                    f.write(create_html(mid, cname, mtitle, script))
                print(f"    ✓ HTML")
            
            done += 1
            await asyncio.sleep(0.3)
    
    print(f"\n{'='*50}")
    print(f"✅ Done! {done} modules processed")
    print(f"{'='*50}")

if __name__ == "__main__":
    asyncio.run(main())
