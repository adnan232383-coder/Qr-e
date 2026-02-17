"""
Add Images to Existing Presentations
Upgrades HTML presentations with relevant stock images based on course topic
"""

import os
import re
from pathlib import Path
from typing import Dict, List

# Image library by topic
TOPIC_IMAGES = {
    # Chemistry
    "chemistry": [
        "https://images.unsplash.com/photo-1770320742703-293b066dcac7?w=800",  # Purple test tube
        "https://images.unsplash.com/photo-1770320742705-a1aa0bd9364d?w=800",  # Pink test tube
        "https://images.unsplash.com/photo-1758876569703-ea9b21463691?w=800",  # Chemistry books
        "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=800",  # Laboratory
        "https://images.unsplash.com/photo-1603126857599-f6e157fa2fe6?w=800",  # Molecules
    ],
    # Anatomy
    "anatomy": [
        "https://images.unsplash.com/photo-1768644675721-2e468ec8c72c?w=800",  # Arm anatomy
        "https://images.unsplash.com/photo-1768644675767-40b294727e10?w=800",  # Body anatomy
        "https://images.unsplash.com/photo-1559757175-5700dde675bc?w=800",  # Skeleton
        "https://images.unsplash.com/photo-1530497610245-94d3c16cda28?w=800",  # Medical model
        "https://images.unsplash.com/photo-1532938911079-1b06ac7ceec7?w=800",  # Medical study
    ],
    # Dental
    "dental": [
        "https://images.unsplash.com/photo-1758205307912-5896ff0c65ae?w=800",  # Dentist
        "https://images.unsplash.com/photo-1606811841689-23dfddce3e95?w=800",  # Dental tools
        "https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?w=800",  # Teeth model
        "https://images.unsplash.com/photo-1609840114035-3c981b782dfe?w=800",  # Dental care
        "https://images.unsplash.com/photo-1598256989800-fe5f95da9787?w=800",  # Dental equipment
    ],
    # Pharmacy
    "pharmacy": [
        "https://images.unsplash.com/photo-1522335579687-9c718c5184d7?w=800",  # Pills
        "https://images.unsplash.com/photo-1573883430060-1678c9cd4221?w=800",  # White pills
        "https://images.unsplash.com/photo-1596522016734-8e6136fe5cfa?w=800",  # Blister pack
        "https://images.unsplash.com/photo-1471864190281-a93a3070b6de?w=800",  # Pharmacy
        "https://images.unsplash.com/photo-1585435557343-3b092031a831?w=800",  # Medicine bottles
    ],
    # Biology/Cells
    "biology": [
        "https://images.unsplash.com/photo-1758656803198-eeea35110219?w=800",  # Blood cells
        "https://images.unsplash.com/photo-1617178571938-7859791e1751?w=800",  # Cell microscope
        "https://images.unsplash.com/photo-1576086213369-97a306d36557?w=800",  # DNA
        "https://images.unsplash.com/photo-1530026405186-ed1f139313f8?w=800",  # Microscope
        "https://images.unsplash.com/photo-1507413245164-6160d8298b31?w=800",  # Lab
    ],
    # Medical/General
    "medical": [
        "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=800",  # Stethoscope
        "https://images.unsplash.com/photo-1551076805-e1869033e561?w=800",  # Medical team
        "https://images.unsplash.com/photo-1516549655169-df83a0774514?w=800",  # Hospital
        "https://images.unsplash.com/photo-1631217868264-e5b90bb7e133?w=800",  # Doctor
        "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=800",  # Medical research
    ],
    # Physics
    "physics": [
        "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=800",  # Physics equations
        "https://images.unsplash.com/photo-1636466497217-26a8cbeaf0aa?w=800",  # Light physics
        "https://images.unsplash.com/photo-1507413245164-6160d8298b31?w=800",  # Science lab
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800",  # Technology
        "https://images.unsplash.com/photo-1628595351029-c2bf17511435?w=800",  # Scientific
    ],
    # Default/General Science
    "default": [
        "https://images.unsplash.com/photo-1507413245164-6160d8298b31?w=800",  # Lab
        "https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=800",  # Research
        "https://images.unsplash.com/photo-1576319155264-99536e0be1ee?w=800",  # Science
        "https://images.unsplash.com/photo-1518152006812-edab29b069ac?w=800",  # Books
        "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=800",  # Study
    ]
}

# Keywords mapping to topics
KEYWORD_MAP = {
    "chemistry": ["chemistry", "organic", "inorganic", "biochem", "stoichiometry", "molecule", "reaction"],
    "anatomy": ["anatomy", "histology", "embryology", "physiology", "body", "muscle", "bone", "organ"],
    "dental": ["dental", "tooth", "teeth", "oral", "occlusion", "dent", "orthodont"],
    "pharmacy": ["pharm", "drug", "medicine", "dosage", "therapeutic", "prescription"],
    "biology": ["biology", "cell", "microb", "immun", "genetic", "dna", "rna", "pathology"],
    "physics": ["physics", "radiation", "radiology", "imaging", "x-ray", "ultrasound"],
    "medical": ["medical", "clinical", "patient", "health", "disease", "infection", "steriliz"]
}


def detect_topic(course_name: str, module_title: str) -> str:
    """Detect the topic based on course name and module title"""
    text = f"{course_name} {module_title}".lower()
    
    for topic, keywords in KEYWORD_MAP.items():
        for keyword in keywords:
            if keyword in text:
                return topic
    
    return "default"


def get_images_for_topic(topic: str, count: int = 3) -> List[str]:
    """Get images for a specific topic"""
    images = TOPIC_IMAGES.get(topic, TOPIC_IMAGES["default"])
    # Cycle through images if we need more
    result = []
    for i in range(count):
        result.append(images[i % len(images)])
    return result


def create_enhanced_presentation(module_id: str, module_title: str, course_name: str, 
                                  slides_data: List[Dict], audio_path: str,
                                  subtitles: List[Dict]) -> str:
    """Create an enhanced HTML presentation with images"""
    
    topic = detect_topic(course_name, module_title)
    images = get_images_for_topic(topic, len(slides_data))
    
    # Build slides HTML
    slides_html = ""
    for i, (slide, img_url) in enumerate(zip(slides_data, images + images)):  # Double images to cover all slides
        content_items = slide.get("content", [])
        
        # Build bullet points
        bullets_html = ""
        for item in content_items[:4]:  # Limit to 4 bullets per slide
            text = item.get("text", "")
            # Clean up markdown markers
            text = re.sub(r'\[PAUSE\]', '', text)
            text = re.sub(r'\[EMPHASIS\](.*?)\[/EMPHASIS\]', r'<strong>\1</strong>', text)
            text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
            text = re.sub(r'#{1,3}\s*', '', text)
            if text.strip():
                bullets_html += f'<li><span class="b"></span>{text.strip()}</li>'
        
        if i == 0:
            # Title slide
            slides_html += f'''<div class="slide title-slide active" data-index="{i}">
        <div class="inner">
            <div class="img-container"><img src="{images[0]}" alt="Course illustration" loading="lazy"></div>
            <h1>{module_title}</h1>
            <p class="sub">{course_name}</p>
        </div>
    </div>'''
        elif i == len(slides_data) - 1:
            # Summary slide
            slides_html += f'''<div class="slide" data-index="{i}">
        <div class="inner split">
            <div class="text-side">
                <h2>Summary</h2>
                <ul class="pts">
                    <li><span class="b"></span>Key concepts covered</li>
                    <li><span class="b"></span>Clinical applications</li>
                    <li><span class="b"></span>Review and practice</li>
                </ul>
            </div>
            <div class="img-side"><img src="{images[i % len(images)]}" alt="Summary" loading="lazy"></div>
        </div>
    </div>'''
        else:
            # Content slide with image
            slides_html += f'''<div class="slide" data-index="{i}">
        <div class="inner split">
            <div class="text-side">
                <h2>{slide.get("title", f"Key Points {i}")}</h2>
                <ul class="pts">{bullets_html}</ul>
            </div>
            <div class="img-side"><img src="{images[i % len(images)]}" alt="Illustration" loading="lazy"></div>
        </div>
    </div>'''
    
    n = len(slides_data)
    subs_json = str(subtitles).replace("'", '"')
    
    html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{module_title}</title>
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
<span class="ind" id="in">1/{n}</span>
<button class="btn" id="vb">🔊</button>
<button class="btn" id="fb">⛶</button>
</div></div>
<div class="ov" id="ov"><button class="sbtn" id="sb">🔊 Start Presentation</button></div>
<audio id="a"><source src="{audio_path}" type="audio/mpeg"></audio>
<script>
const a=document.getElementById('a'),sl=document.querySelectorAll('.slide'),n={n},su={subs_json};
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


def upgrade_existing_presentation(html_path: str) -> bool:
    """Upgrade an existing presentation by parsing and regenerating with images"""
    path = Path(html_path)
    if not path.exists():
        return False
    
    # Read existing HTML
    content = path.read_text(encoding='utf-8')
    
    # Extract module info from filename
    module_id = path.stem
    
    # Extract title
    title_match = re.search(r'<title>(.*?)</title>', content)
    title = title_match.group(1) if title_match else module_id
    
    # Split title if it contains course name
    parts = title.split(' - ')
    module_title = parts[0] if parts else title
    course_name = parts[1] if len(parts) > 1 else "Course"
    
    # Extract slides data by finding slide divs
    slide_matches = re.findall(r'<div class="slide[^"]*"[^>]*data-index="(\d+)"[^>]*>(.*?)</div>(?=<div class="slide|<div class="subs")', content, re.DOTALL)
    
    slides_data = []
    for idx, slide_content in slide_matches:
        # Extract title
        h1_match = re.search(r'<h1>(.*?)</h1>', slide_content)
        h2_match = re.search(r'<h2>(.*?)</h2>', slide_content)
        slide_title = h1_match.group(1) if h1_match else (h2_match.group(1) if h2_match else f"Slide {idx}")
        
        # Extract content
        li_matches = re.findall(r'<li>.*?<span class="b"></span>(.*?)</li>', slide_content, re.DOTALL)
        content_items = [{"type": "bullet", "text": t.strip()} for t in li_matches]
        
        slide_type = "title" if int(idx) == 0 else "content"
        slides_data.append({"title": slide_title, "content": content_items, "type": slide_type})
    
    # Extract subtitles
    subs_match = re.search(r'su=(\[.*?\]);', content, re.DOTALL)
    subtitles = []
    if subs_match:
        import json
        try:
            subtitles = json.loads(subs_match.group(1).replace("'", '"'))
        except:
            subtitles = [{"start": 0, "end": 10, "text": "Welcome"}]
    
    # Extract audio path
    audio_match = re.search(r'<source src="([^"]+)"', content)
    audio_path = audio_match.group(1) if audio_match else f"/api/audio/{module_id}.mp3"
    
    # Generate new HTML with images
    new_html = create_enhanced_presentation(
        module_id=module_id,
        module_title=module_title,
        course_name=course_name,
        slides_data=slides_data,
        audio_path=audio_path,
        subtitles=subtitles
    )
    
    # Save
    path.write_text(new_html, encoding='utf-8')
    return True


def upgrade_all_presentations():
    """Upgrade all existing presentations"""
    presentations_dir = Path("/app/backend/presentations")
    
    upgraded = 0
    errors = 0
    
    for html_file in sorted(presentations_dir.glob("*.html")):
        if "_50_50" in html_file.name:
            continue  # Skip special formats
        
        try:
            if upgrade_existing_presentation(str(html_file)):
                upgraded += 1
                print(f"✓ Upgraded: {html_file.name}")
            else:
                errors += 1
                print(f"✗ Failed: {html_file.name}")
        except Exception as e:
            errors += 1
            print(f"✗ Error upgrading {html_file.name}: {e}")
    
    print(f"\nDone! Upgraded: {upgraded}, Errors: {errors}")


if __name__ == "__main__":
    upgrade_all_presentations()
