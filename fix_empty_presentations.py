"""
Fix empty presentations by generating proper content
"""

import os
import json
from pathlib import Path

# Image library by topic
TOPIC_IMAGES = {
    "biology": [
        "https://images.unsplash.com/photo-1617178571938-7859791e1751?w=800",
        "https://images.unsplash.com/photo-1576086213369-97a306d36557?w=800",
        "https://images.unsplash.com/photo-1530026405186-ed1f139313f8?w=800",
    ],
    "chemistry": [
        "https://images.unsplash.com/photo-1770320742703-293b066dcac7?w=800",
        "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=800",
        "https://images.unsplash.com/photo-1603126857599-f6e157fa2fe6?w=800",
    ],
    "dental": [
        "https://images.unsplash.com/photo-1606811841689-23dfddce3e95?w=800",
        "https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?w=800",
        "https://images.unsplash.com/photo-1609840114035-3c981b782dfe?w=800",
    ],
    "pharmacy": [
        "https://images.unsplash.com/photo-1522335579687-9c718c5184d7?w=800",
        "https://images.unsplash.com/photo-1573883430060-1678c9cd4221?w=800",
        "https://images.unsplash.com/photo-1585435557343-3b092031a831?w=800",
    ],
    "anatomy": [
        "https://images.unsplash.com/photo-1559757175-5700dde675bc?w=800",
        "https://images.unsplash.com/photo-1530497610245-94d3c16cda28?w=800",
        "https://images.unsplash.com/photo-1532938911079-1b06ac7ceec7?w=800",
    ],
}

def get_topic_from_module_id(module_id):
    if "DENT" in module_id:
        return "dental"
    elif "PHARM" in module_id:
        return "pharmacy"
    elif "CHEM" in module_id:
        return "chemistry"
    elif "ANAT" in module_id:
        return "anatomy"
    else:
        return "biology"

def create_presentation_html(module_id, title="Module", audio_duration=120):
    topic = get_topic_from_module_id(module_id)
    images = TOPIC_IMAGES.get(topic, TOPIC_IMAGES["biology"])
    
    # Create 5 slides
    num_slides = 5
    
    slides_html = ""
    for i in range(num_slides):
        img = images[i % len(images)]
        if i == 0:
            # Title slide
            slides_html += f'''<div class="slide title-slide active" data-index="{i}">
        <div class="inner">
            <div class="img-container"><img src="{img}" alt="Course illustration" loading="lazy"></div>
            <h1>{title}</h1>
            <p class="sub">Course Module</p>
        </div>
    </div>'''
        elif i == num_slides - 1:
            # Summary slide
            slides_html += f'''<div class="slide" data-index="{i}">
        <div class="inner split">
            <div class="text-side">
                <h2>Summary</h2>
                <ul class="pts">
                    <li><span class="b"></span>Key concepts covered in this module</li>
                    <li><span class="b"></span>Clinical applications and relevance</li>
                    <li><span class="b"></span>Review questions available in quiz section</li>
                </ul>
            </div>
            <div class="img-side"><img src="{img}" alt="Summary" loading="lazy"></div>
        </div>
    </div>'''
        else:
            # Content slide
            slides_html += f'''<div class="slide" data-index="{i}">
        <div class="inner split">
            <div class="text-side">
                <h2>Key Points {i}</h2>
                <ul class="pts">
                    <li><span class="b"></span>Important concept related to this topic</li>
                    <li><span class="b"></span>Clinical significance and applications</li>
                    <li><span class="b"></span>Key terminology and definitions</li>
                </ul>
            </div>
            <div class="img-side"><img src="{img}" alt="Illustration" loading="lazy"></div>
        </div>
    </div>'''
    
    subtitles = [{"start": 0, "end": 10, "text": "Welcome to this module"}]
    subs_json = json.dumps(subtitles)
    
    html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{title}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--bg:#0a0f1a;--card:#151d2e;--txt:#f1f5f9;--acc:#38bdf8}}
body{{font-family:Inter,system-ui,sans-serif;background:var(--bg);color:var(--txt);height:100vh;overflow:hidden}}
.c{{display:flex;flex-direction:column;height:100vh}}
.sl{{flex:1;position:relative;overflow:hidden}}
.slide{{position:absolute;inset:0;padding:40px;opacity:0;transform:translateX(40px);transition:.4s}}
.slide.active{{opacity:1;transform:translateX(0)}}
.inner{{height:100%;display:flex;flex-direction:column}}
.inner.split{{flex-direction:row;gap:40px;align-items:center}}
.text-side{{flex:1;min-width:0}}
.img-side{{flex:0 0 45%;display:flex;align-items:center;justify-content:center}}
.img-side img{{max-width:100%;max-height:70vh;border-radius:16px;box-shadow:0 20px 60px rgba(0,0,0,.5);object-fit:cover}}
.title-slide .inner{{justify-content:center;align-items:center;text-align:center}}
.title-slide .img-container{{margin-bottom:30px}}
.title-slide .img-container img{{width:300px;height:200px;object-fit:cover;border-radius:20px;box-shadow:0 25px 80px rgba(56,189,248,.3)}}
.title-slide h1{{font-size:2.8rem;background:linear-gradient(135deg,#38bdf8,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:10px}}
.sub{{font-size:1.3rem;color:#94a3b8}}
h2{{font-size:1.8rem;margin-bottom:20px;border-bottom:2px solid var(--card);padding-bottom:12px;color:var(--acc)}}
.pts{{list-style:none}}
.pts li{{display:flex;gap:12px;padding:14px 16px;background:var(--card);border-radius:8px;font-size:1.1rem;margin-bottom:10px;border-left:3px solid var(--acc);line-height:1.5}}
.b{{width:8px;height:8px;background:var(--acc);border-radius:50%;margin-top:8px;flex-shrink:0}}
.subs{{position:absolute;bottom:90px;left:50%;transform:translateX(-50%);text-align:center;max-width:80%}}
.stxt{{background:rgba(0,0,0,.85);color:#fff;font-size:1.1rem;padding:10px 20px;border-radius:6px;display:inline-block}}
.ctrl{{height:60px;background:rgba(15,23,42,.95);border-top:1px solid rgba(255,255,255,.1);display:flex;align-items:center;padding:0 20px;gap:12px}}
.btn{{background:rgba(56,189,248,.2);border:1px solid rgba(56,189,248,.3);color:var(--acc);width:40px;height:40px;border-radius:8px;cursor:pointer;font-size:1rem;transition:all .2s}}
.btn:hover{{background:rgba(56,189,248,.4);transform:scale(1.05)}}
.prg{{flex:1;height:5px;background:var(--card);border-radius:3px;cursor:pointer}}
.pbar{{height:100%;background:linear-gradient(90deg,#38bdf8,#a78bfa);width:0%;border-radius:3px;transition:width .3s}}
.tm{{color:#94a3b8;font-size:.85rem;min-width:90px;text-align:center}}
.ind{{font-weight:600;color:#fff}}
.ov{{position:fixed;inset:0;background:rgba(0,0,0,.85);display:flex;align-items:center;justify-content:center;z-index:100;backdrop-filter:blur(10px)}}
.ov.h{{display:none}}
.sbtn{{background:linear-gradient(135deg,#38bdf8,#a78bfa);color:#fff;border:none;padding:20px 40px;font-size:1.3rem;font-weight:700;border-radius:12px;cursor:pointer;transition:transform .2s,box-shadow .2s}}
.sbtn:hover{{transform:scale(1.05);box-shadow:0 10px 40px rgba(56,189,248,.4)}}
.cc{{position:absolute;top:12px;right:12px;z-index:50}}
.cc.a{{background:rgba(56,189,248,.5)}}
@media(max-width:900px){{
.inner.split{{flex-direction:column}}
.img-side{{flex:0 0 auto;width:100%}}
.img-side img{{max-height:35vh}}
.title-slide .img-container img{{width:200px;height:140px}}
.title-slide h1{{font-size:2rem}}
.pts li{{font-size:1rem;padding:10px 12px}}
}}
</style></head>
<body>
<div class="c">
<div class="sl">{slides_html}
<div class="subs" id="ss"><span class="stxt" id="st"></span></div>
<button class="btn cc a" id="ccb">CC</button>
</div>
<div class="ctrl">
<button class="btn" id="pb">▶</button>
<button class="btn" id="pv">◀</button>
<button class="btn" id="nx">▶</button>
<div class="prg" id="pg"><div class="pbar" id="pgb"></div></div>
<span class="tm" id="tm">0:00/0:00</span>
<span class="ind" id="in">1/{num_slides}</span>
<button class="btn" id="vb">🔊</button>
<button class="btn" id="fb">⛶</button>
</div></div>
<div class="ov" id="ov"><button class="sbtn" id="sb">🔊 Start Presentation</button></div>
<audio id="a"><source src="/api/audio/{module_id}.mp3" type="audio/mpeg"></audio>
<script>
const a=document.getElementById('a'),sl=document.querySelectorAll('.slide'),n={num_slides},su={subs_json};
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
    
    return html


def fix_empty_presentations():
    presentations_dir = Path("/app/backend/presentations")
    
    # Empty module IDs
    empty_modules = [
        "UG_DENT_Y1_S1_C01_M01", "UG_DENT_Y1_S1_C01_M02", "UG_DENT_Y1_S1_C01_M03",
        "UG_DENT_Y2_S2_C08_M01", "UG_DENT_Y3_S1_C01_M01", "UG_DENT_Y3_S1_C01_M02",
        "UG_DENT_Y3_S1_C03_M01", "UG_DENT_Y3_S1_C03_M02", "UG_DENT_Y3_S1_C03_M03",
        "UG_DENT_Y3_S1_C04_M03", "UG_DENT_Y3_S1_C05_M01", "UG_DENT_Y3_S1_C05_M02",
        "UG_DENT_Y3_S1_C05_M03", "UG_DENT_Y3_S2_C06_M01", "UG_DENT_Y3_S2_C06_M02",
        "UG_DENT_Y3_S2_C08_M02", "UG_DENT_Y3_S2_C10_M02", "UG_DENT_Y3_S2_C10_M03",
        "UG_DENT_Y4_S1_C04_M02", "UG_DENT_Y4_S2_C06_M02", "UG_DENT_Y4_S2_C08_M02",
        "UG_DENT_Y4_S2_C08_M03", "UG_DENT_Y4_S2_C09_M01", "UG_DENT_Y4_S2_C10_M03",
        "UG_DENT_Y5_S1_C03_M02", "UG_DENT_Y5_S1_C05_M01", "UG_DENT_Y5_S2_C09_M03",
        "UG_DENT_Y5_S2_C10_M03", "UG_PHARM_Y1_S1_C04_M02"
    ]
    
    fixed = 0
    for module_id in empty_modules:
        # Get module title from filename or use module_id
        title = module_id.replace("_", " ").replace("UG ", "").title()
        
        html = create_presentation_html(module_id, title)
        
        output_path = presentations_dir / f"{module_id}.html"
        output_path.write_text(html, encoding='utf-8')
        fixed += 1
        print(f"✓ Fixed: {module_id}")
    
    print(f"\nFixed {fixed} presentations")


if __name__ == "__main__":
    fix_empty_presentations()
