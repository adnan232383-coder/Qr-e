"""
Presentation with Avatar - Picture-in-Picture style
Combines slides with HeyGen avatar video
"""

import os
import asyncio
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

PRESENTATIONS_DIR = Path("/app/backend/presentations")
AUDIO_DIR = Path("/app/backend/audio")
VIDEOS_DIR = Path("/app/backend/heygen_videos")

# Dental illustrations
DENTAL_IMAGES = {
    "root_canal": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/f49ac82dc9f54808b7c78b9749cd3f11790fdc8a7b561db105271f3a11361fce.png",
    "tooth_anatomy": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/de71f85ab3c53fb5fb0f037d7453bf194df5deb55fba729e8dc993eb6e7f3a77.png",
    "pulp_infection": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/16d68af7809ae10728ce9a12dda84359ab21d47bd2ee390673f3657650f9fc2e.png",
    "dental_xray": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/315479269c6bb29c3f481606593e121c4fc56736335527081d6699bc869d5996.png",
    "rubber_dam": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/9abba951790d8002ddd4c7f3df41b8dfe6efd5e7e4e301cc8daf2080bb09dc5d.png",
    "dental_instruments": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/e73e57fdd4609ae5ea1f8a33bac8bece1e825a888e8051cc738b3c5f466d95a7.png",
    "dental_restoration": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/91cb5fe80e7dc8ee4133cc77965249a28ce2dcaf407423c6ca1b2dd7008db76f.png",
    "dental_crown": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/f58663c013b25905529c6d5b5d81747bd51d6327f9d93f890e905bcbee3ff39a.png",
}


def parse_to_slides(script_text: str, title: str) -> List[Dict]:
    """Parse script into simple slides"""
    slides = []
    images = list(DENTAL_IMAGES.values())
    
    # Title slide
    slides.append({
        "type": "title",
        "title": title,
        "image": images[0]
    })
    
    # Parse content
    lines = script_text.strip().split('\n')
    current_section = None
    current_points = []
    img_idx = 1
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('#') or (line.startswith('[') and line.endswith(']')):
            if current_section and current_points:
                slides.append({
                    "type": "content",
                    "title": current_section,
                    "points": current_points[:4],
                    "image": images[img_idx % len(images)]
                })
                img_idx += 1
            
            if line.startswith('#'):
                current_section = line.replace('#', '').strip()
            else:
                current_section = line[1:-1].replace('_', ' ').title()
            current_points = []
        elif line.startswith('-'):
            current_points.append(line[1:].strip())
        elif len(line) > 20:
            current_points.append(line[:100])
    
    if current_section and current_points:
        slides.append({
            "type": "content",
            "title": current_section,
            "points": current_points[:4],
            "image": images[img_idx % len(images)]
        })
    
    return slides


def generate_avatar_presentation_html(slides: List[Dict], module_id: str, title: str, course: str, video_url: str = None) -> str:
    """Generate presentation HTML with avatar video"""
    
    slides_html = ""
    total = len(slides)
    
    for i, slide in enumerate(slides):
        if slide["type"] == "title":
            slides_html += f'''
            <div class="slide title-slide" data-index="{i}">
                <div class="slide-inner">
                    <h1>{slide["title"]}</h1>
                    <p class="course-name">{course}</p>
                    <div class="title-image">
                        <img src="{slide.get('image', '')}" alt="">
                    </div>
                </div>
            </div>
            '''
        else:
            points_html = ""
            for p in slide.get("points", []):
                points_html += f'<li>{p}</li>'
            
            slides_html += f'''
            <div class="slide content-slide" data-index="{i}">
                <div class="slide-inner">
                    <h2>{slide["title"]}</h2>
                    <div class="content-grid">
                        <div class="slide-image">
                            <img src="{slide.get('image', '')}" alt="">
                        </div>
                        <ul class="points">{points_html}</ul>
                    </div>
                </div>
            </div>
            '''
    
    # Video source - use local if exists, otherwise placeholder
    video_src = video_url or f"/api/videos/{module_id}/file"
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        :root {{
            --bg: #0f172a;
            --card: #1e293b;
            --text: #f1f5f9;
            --text-muted: #94a3b8;
            --accent: #38bdf8;
            --accent-glow: rgba(56, 189, 248, 0.3);
        }}
        
        body {{
            font-family: 'Inter', sans-serif;
            background: var(--bg);
            color: var(--text);
            overflow: hidden;
            height: 100vh;
        }}
        
        .presentation-container {{
            display: grid;
            grid-template-columns: 1fr 320px;
            grid-template-rows: 1fr 80px;
            height: 100vh;
            gap: 0;
        }}
        
        /* Main slides area */
        .slides-area {{
            position: relative;
            overflow: hidden;
            background: var(--bg);
        }}
        
        .slide {{
            position: absolute;
            inset: 0;
            padding: 40px 50px;
            opacity: 0;
            transform: translateX(50px);
            transition: all 0.5s ease;
            pointer-events: none;
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
        
        /* Title slide */
        .title-slide {{
            justify-content: center;
            align-items: center;
            text-align: center;
        }}
        
        .title-slide .slide-inner {{
            justify-content: center;
            align-items: center;
        }}
        
        .title-slide h1 {{
            font-size: 3rem;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 10px;
        }}
        
        .course-name {{
            font-size: 1.2rem;
            color: var(--accent);
            margin-bottom: 40px;
        }}
        
        .title-image {{
            max-width: 500px;
            background: var(--card);
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 0 40px var(--accent-glow);
        }}
        
        .title-image img {{
            width: 100%;
            border-radius: 12px;
        }}
        
        /* Content slide */
        .content-slide h2 {{
            font-size: 1.8rem;
            font-weight: 600;
            color: var(--accent);
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 2px solid var(--card);
        }}
        
        .content-grid {{
            display: grid;
            grid-template-columns: 350px 1fr;
            gap: 40px;
            flex: 1;
            align-items: start;
        }}
        
        .slide-image {{
            background: var(--card);
            border-radius: 16px;
            padding: 15px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }}
        
        .slide-image img {{
            width: 100%;
            border-radius: 10px;
        }}
        
        .points {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}
        
        .points li {{
            padding: 18px 24px;
            background: var(--card);
            border-radius: 12px;
            font-size: 1.05rem;
            line-height: 1.6;
            border-left: 4px solid var(--accent);
            animation: fadeIn 0.4s ease forwards;
            opacity: 0;
        }}
        
        .slide.active .points li:nth-child(1) {{ animation-delay: 0.1s; }}
        .slide.active .points li:nth-child(2) {{ animation-delay: 0.2s; }}
        .slide.active .points li:nth-child(3) {{ animation-delay: 0.3s; }}
        .slide.active .points li:nth-child(4) {{ animation-delay: 0.4s; }}
        
        @keyframes fadeIn {{
            to {{ opacity: 1; }}
        }}
        
        /* Avatar panel */
        .avatar-panel {{
            background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
            border-left: 1px solid #334155;
            display: flex;
            flex-direction: column;
            padding: 20px;
        }}
        
        .avatar-header {{
            text-align: center;
            margin-bottom: 15px;
        }}
        
        .avatar-header h3 {{
            font-size: 0.9rem;
            color: var(--text-muted);
            font-weight: 500;
        }}
        
        .avatar-video-container {{
            flex: 1;
            background: #000;
            border-radius: 16px;
            overflow: hidden;
            position: relative;
            box-shadow: 0 0 30px rgba(56, 189, 248, 0.2);
        }}
        
        .avatar-video {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .avatar-placeholder {{
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #1e293b, #0f172a);
            color: var(--text-muted);
        }}
        
        .avatar-placeholder svg {{
            width: 60px;
            height: 60px;
            margin-bottom: 15px;
            opacity: 0.5;
        }}
        
        .avatar-status {{
            text-align: center;
            margin-top: 15px;
            font-size: 0.8rem;
            color: var(--accent);
        }}
        
        /* Control bar */
        .control-bar {{
            grid-column: 1 / -1;
            background: var(--card);
            display: flex;
            align-items: center;
            padding: 0 30px;
            gap: 20px;
            border-top: 1px solid #334155;
        }}
        
        .play-btn {{
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: var(--accent);
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s;
        }}
        
        .play-btn:hover {{
            transform: scale(1.05);
            box-shadow: 0 0 20px var(--accent-glow);
        }}
        
        .play-btn svg {{
            width: 22px;
            height: 22px;
            fill: var(--bg);
        }}
        
        .info {{
            min-width: 180px;
        }}
        
        .info h4 {{
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--text);
        }}
        
        .info p {{
            font-size: 0.8rem;
            color: var(--text-muted);
        }}
        
        .progress-area {{
            flex: 1;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .time {{
            font-size: 0.85rem;
            color: var(--text-muted);
            font-variant-numeric: tabular-nums;
            min-width: 45px;
        }}
        
        .progress-bar {{
            flex: 1;
            height: 6px;
            background: rgba(255,255,255,0.1);
            border-radius: 3px;
            cursor: pointer;
            overflow: hidden;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--accent), #a78bfa);
            width: 0%;
            transition: width 0.1s;
        }}
        
        .slide-num {{
            font-size: 0.9rem;
            color: var(--text-muted);
        }}
        
        .slide-num .current {{
            color: var(--accent);
            font-weight: 600;
        }}
        
        .vol-btn, .fs-btn {{
            background: none;
            border: none;
            cursor: pointer;
            padding: 8px;
            color: var(--text-muted);
            transition: color 0.3s;
        }}
        
        .vol-btn:hover, .fs-btn:hover {{
            color: var(--accent);
        }}
        
        .vol-btn svg, .fs-btn svg {{
            width: 20px;
            height: 20px;
            fill: currentColor;
        }}
        
        .vol-slider {{
            width: 70px;
            height: 4px;
            -webkit-appearance: none;
            background: rgba(255,255,255,0.2);
            border-radius: 2px;
        }}
        
        .vol-slider::-webkit-slider-thumb {{
            -webkit-appearance: none;
            width: 12px;
            height: 12px;
            background: var(--accent);
            border-radius: 50%;
        }}
    </style>
</head>
<body>
    <div class="presentation-container">
        <div class="slides-area">
            {slides_html}
        </div>
        
        <div class="avatar-panel">
            <div class="avatar-header">
                <h3>Instructor</h3>
            </div>
            <div class="avatar-video-container">
                <video class="avatar-video" id="avatarVideo" playsinline>
                    <source src="{video_src}" type="video/mp4">
                </video>
                <div class="avatar-placeholder" id="avatarPlaceholder">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                    </svg>
                    <span>Avatar Video</span>
                </div>
            </div>
            <div class="avatar-status" id="avatarStatus">Ready to play</div>
        </div>
        
        <div class="control-bar">
            <button class="play-btn" id="playBtn">
                <svg id="playIcon" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                <svg id="pauseIcon" style="display:none" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
            </button>
            
            <div class="info">
                <h4>{title}</h4>
                <p>{course}</p>
            </div>
            
            <div class="progress-area">
                <span class="time" id="currentTime">0:00</span>
                <div class="progress-bar" id="progressBar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <span class="time" id="totalTime">0:00</span>
            </div>
            
            <div class="slide-num">
                <span class="current" id="slideNum">1</span> / {total}
            </div>
            
            <button class="vol-btn">
                <svg viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/></svg>
            </button>
            <input type="range" class="vol-slider" id="volSlider" min="0" max="1" step="0.1" value="1">
            
            <button class="fs-btn" id="fsBtn">
                <svg viewBox="0 0 24 24"><path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/></svg>
            </button>
        </div>
    </div>
    
    <script>
        const avatarVideo = document.getElementById('avatarVideo');
        const avatarPlaceholder = document.getElementById('avatarPlaceholder');
        const avatarStatus = document.getElementById('avatarStatus');
        const playBtn = document.getElementById('playBtn');
        const playIcon = document.getElementById('playIcon');
        const pauseIcon = document.getElementById('pauseIcon');
        const progressBar = document.getElementById('progressBar');
        const progressFill = document.getElementById('progressFill');
        const currentTimeEl = document.getElementById('currentTime');
        const totalTimeEl = document.getElementById('totalTime');
        const slideNumEl = document.getElementById('slideNum');
        const volSlider = document.getElementById('volSlider');
        const fsBtn = document.getElementById('fsBtn');
        
        const slides = document.querySelectorAll('.slide');
        const total = slides.length;
        let current = 0;
        let videoLoaded = false;
        
        function fmt(s) {{
            return `${{Math.floor(s/60)}}:${{String(Math.floor(s%60)).padStart(2,'0')}}`;
        }}
        
        function show(idx) {{
            slides.forEach((s,i) => s.classList.toggle('active', i === idx));
            current = idx;
            slideNumEl.textContent = idx + 1;
        }}
        
        function updateFromTime() {{
            if (!avatarVideo.duration) return;
            const idx = Math.min(Math.floor((avatarVideo.currentTime / avatarVideo.duration) * total), total - 1);
            if (idx !== current) show(idx);
        }}
        
        // Video events
        avatarVideo.addEventListener('loadedmetadata', () => {{
            videoLoaded = true;
            avatarPlaceholder.style.display = 'none';
            totalTimeEl.textContent = fmt(avatarVideo.duration);
            avatarStatus.textContent = 'Video ready';
        }});
        
        avatarVideo.addEventListener('error', () => {{
            avatarStatus.textContent = 'Using audio only';
        }});
        
        avatarVideo.addEventListener('timeupdate', () => {{
            progressFill.style.width = `${{(avatarVideo.currentTime / avatarVideo.duration) * 100}}%`;
            currentTimeEl.textContent = fmt(avatarVideo.currentTime);
            updateFromTime();
        }});
        
        avatarVideo.addEventListener('play', () => {{
            playIcon.style.display = 'none';
            pauseIcon.style.display = 'block';
            avatarStatus.textContent = 'Playing...';
        }});
        
        avatarVideo.addEventListener('pause', () => {{
            playIcon.style.display = 'block';
            pauseIcon.style.display = 'none';
            avatarStatus.textContent = 'Paused';
        }});
        
        playBtn.onclick = () => avatarVideo.paused ? avatarVideo.play() : avatarVideo.pause();
        
        progressBar.onclick = (e) => {{
            const rect = progressBar.getBoundingClientRect();
            avatarVideo.currentTime = ((e.clientX - rect.left) / rect.width) * avatarVideo.duration;
        }};
        
        volSlider.oninput = (e) => avatarVideo.volume = e.target.value;
        
        fsBtn.onclick = () => {{
            if (!document.fullscreenElement) document.documentElement.requestFullscreen();
            else document.exitFullscreen();
        }};
        
        document.onkeydown = (e) => {{
            if (e.code === 'Space') {{ e.preventDefault(); playBtn.click(); }}
            if (e.code === 'ArrowRight') avatarVideo.currentTime += 5;
            if (e.code === 'ArrowLeft') avatarVideo.currentTime -= 5;
            if (e.code === 'KeyF') fsBtn.click();
        }};
        
        show(0);
    </script>
</body>
</html>'''
    
    return html


async def create_avatar_presentation(module_id: str, db, video_url: str = None) -> Dict:
    """Create presentation with avatar"""
    
    module = db.modules.find_one({"module_id": module_id})
    if not module:
        return {"success": False, "error": "Module not found"}
    
    script = db.module_scripts.find_one({"module_id": module_id})
    if not script:
        return {"success": False, "error": "No script"}
    
    course = db.courses.find_one({"external_id": module.get("courseId")})
    course_name = course.get("course_name", "") if course else ""
    
    title = module.get("title", module_id)
    script_text = script.get("script_text", "")
    
    slides = parse_to_slides(script_text, title)
    html = generate_avatar_presentation_html(slides, module_id, title, course_name, video_url)
    
    path = PRESENTATIONS_DIR / f"{module_id}_avatar.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"Created: {title} with avatar layout")
    return {"success": True, "title": title, "slides": len(slides)}


if __name__ == "__main__":
    async def main():
        client = MongoClient('mongodb://localhost:27017')
        db = client['test_database']
        
        # Create avatar presentation for Endodontics
        result = await create_avatar_presentation(
            "UG_DENT_Y3_S1_C03_M01", 
            db,
            "/api/videos/UG_DENT_Y1_S1_C01_M01_5min/file"  # Use existing video
        )
        print(result)
    
    asyncio.run(main())
