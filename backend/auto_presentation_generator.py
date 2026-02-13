"""
Auto-Playing Presentation Generator
Creates presentations that auto-sync with audio narration like a video
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
PRESENTATIONS_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True)

# Topic images
TOPIC_IMAGES = {
    "cell": [
        "https://images.unsplash.com/photo-1767486366936-c41b4f767eb8?w=1200",
        "https://images.unsplash.com/photo-1647083701139-3930542304cf?w=1200",
        "https://images.unsplash.com/photo-1758206523826-a65d4cf070aa?w=1200",
        "https://images.unsplash.com/photo-1576086213369-97a306d36557?w=1200",
    ],
    "dna": [
        "https://images.unsplash.com/photo-1705256811175-b1e3398d50e4?w=1200",
        "https://images.unsplash.com/photo-1702802120585-7b682d4e73de?w=1200",
        "https://images.unsplash.com/photo-1604538406338-d41ddc825eb3?w=1200",
    ],
    "genetics": [
        "https://images.unsplash.com/photo-1705256811175-b1e3398d50e4?w=1200",
        "https://images.unsplash.com/photo-1578496479914-7ef3b0193be3?w=1200",
        "https://images.unsplash.com/photo-1702802120585-7b682d4e73de?w=1200",
    ],
    "evolution": [
        "https://images.unsplash.com/photo-1758656803198-eeea35110219?w=1200",
        "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=1200",
        "https://images.unsplash.com/photo-1758702046109-1ca08784e691?w=1200",
    ],
    "biology": [
        "https://images.unsplash.com/photo-1530026405186-ed1f139313f8?w=1200",
        "https://images.unsplash.com/photo-1576086213369-97a306d36557?w=1200",
        "https://images.unsplash.com/photo-1581093450021-4a7360e9a6b5?w=1200",
    ],
    "default": [
        "https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=1200",
        "https://images.unsplash.com/photo-1507413245164-6160d8298b31?w=1200",
        "https://images.unsplash.com/photo-1518152006812-edab29b069ac?w=1200",
        "https://images.unsplash.com/photo-1576086213369-97a306d36557?w=1200",
    ]
}


def get_images_for_topic(text: str) -> List[str]:
    """Get relevant images based on content"""
    text_lower = text.lower()
    for topic, images in TOPIC_IMAGES.items():
        if topic in text_lower:
            return images
    return TOPIC_IMAGES["default"]


def parse_script_to_slides(script_text: str, module_title: str) -> List[Dict]:
    """Parse script into timed slides"""
    slides = []
    lines = script_text.strip().split('\n')
    current_slide = {"title": module_title, "content": [], "type": "title"}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('#'):
            if current_slide["content"] or current_slide["type"] == "title":
                slides.append(current_slide)
            title = line.replace('#', '').strip()
            current_slide = {"title": title, "content": [], "type": "section"}
        elif line.startswith('[') and line.endswith(']'):
            if current_slide["content"]:
                slides.append(current_slide)
            section_name = line[1:-1].replace('_', ' ').title()
            current_slide = {"title": section_name, "content": [], "type": "section"}
        elif line.startswith('-'):
            current_slide["content"].append({"type": "bullet", "text": line[1:].strip()})
        else:
            current_slide["content"].append({"type": "text", "text": line})
    
    if current_slide["content"] or current_slide["type"] == "title":
        slides.append(current_slide)
    
    # Add images
    all_text = module_title + " " + script_text
    images = get_images_for_topic(all_text)
    for i, slide in enumerate(slides):
        slide["image"] = images[i % len(images)]
    
    return slides


def generate_auto_presentation_html(slides: List[Dict], module_id: str, module_title: str, course_name: str) -> str:
    """Generate auto-playing presentation HTML"""
    
    slides_html = ""
    for i, slide in enumerate(slides):
        content_html = ""
        bullets = [c for c in slide.get("content", []) if c["type"] == "bullet"]
        texts = [c for c in slide.get("content", []) if c["type"] == "text"]
        
        if texts:
            for t in texts[:2]:
                content_html += f'<p class="slide-text">{t["text"]}</p>\n'
        
        if bullets:
            content_html += '<ul class="bullets">\n'
            for b in bullets[:4]:
                content_html += f'<li><span class="bullet-dot"></span>{b["text"]}</li>\n'
            content_html += '</ul>\n'
        
        slide_class = "title-slide" if slide["type"] == "title" else ""
        
        slides_html += f'''
        <div class="slide {slide_class}" data-index="{i}" style="background-image: url('{slide.get("image", "")}');">
            <div class="slide-overlay"></div>
            <div class="slide-box">
                <h2>{slide["title"]}</h2>
                <div class="slide-content">{content_html}</div>
            </div>
            <div class="slide-counter">{i + 1} / {len(slides)}</div>
        </div>
        '''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{module_title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Poppins', sans-serif;
            background: #000;
            color: #fff;
            overflow: hidden;
        }}
        
        /* Video-like container */
        .video-container {{
            position: fixed;
            inset: 0;
            display: flex;
            flex-direction: column;
        }}
        
        /* Slides wrapper */
        .slides-wrapper {{
            flex: 1;
            position: relative;
            overflow: hidden;
        }}
        
        .slide {{
            position: absolute;
            inset: 0;
            background-size: cover;
            background-position: center;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.8s ease;
            pointer-events: none;
        }}
        
        .slide.active {{
            opacity: 1;
            pointer-events: auto;
        }}
        
        .slide-overlay {{
            position: absolute;
            inset: 0;
            background: linear-gradient(135deg, rgba(0,0,0,0.75) 0%, rgba(0,0,0,0.4) 50%, rgba(0,50,80,0.3) 100%);
        }}
        
        .slide-box {{
            position: relative;
            z-index: 10;
            max-width: 800px;
            padding: 50px 60px;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(15px);
            border-radius: 20px;
            border: 1px solid rgba(0, 212, 255, 0.3);
            animation: slideIn 0.6s ease;
        }}
        
        @keyframes slideIn {{
            from {{ transform: translateY(30px); opacity: 0; }}
            to {{ transform: translateY(0); opacity: 1; }}
        }}
        
        .title-slide .slide-box {{
            text-align: center;
            background: rgba(0, 212, 255, 0.15);
        }}
        
        .slide-box h2 {{
            font-size: 2.2rem;
            font-weight: 700;
            color: #00d4ff;
            margin-bottom: 25px;
            line-height: 1.3;
        }}
        
        .title-slide .slide-box h2 {{
            font-size: 2.8rem;
        }}
        
        .slide-text {{
            font-size: 1.15rem;
            line-height: 1.8;
            color: rgba(255,255,255,0.9);
            margin-bottom: 15px;
        }}
        
        .bullets {{
            list-style: none;
            padding: 0;
        }}
        
        .bullets li {{
            display: flex;
            align-items: flex-start;
            gap: 15px;
            padding: 12px 0;
            font-size: 1.1rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        
        .bullets li:last-child {{
            border-bottom: none;
        }}
        
        .bullet-dot {{
            flex-shrink: 0;
            width: 12px;
            height: 12px;
            margin-top: 6px;
            background: linear-gradient(135deg, #00d4ff, #00ff88);
            border-radius: 50%;
            box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
        }}
        
        .slide-counter {{
            position: absolute;
            bottom: 100px;
            right: 40px;
            background: rgba(0,0,0,0.6);
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 0.9rem;
            color: rgba(255,255,255,0.7);
            z-index: 20;
        }}
        
        /* Control bar - video style */
        .control-bar {{
            height: 80px;
            background: rgba(10, 10, 15, 0.95);
            display: flex;
            align-items: center;
            padding: 0 30px;
            gap: 20px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }}
        
        .play-btn {{
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: #00d4ff;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s;
        }}
        
        .play-btn:hover {{
            transform: scale(1.1);
            box-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
        }}
        
        .play-btn svg {{
            width: 20px;
            height: 20px;
            fill: #0a0a0f;
        }}
        
        /* Progress bar */
        .progress-container {{
            flex: 1;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .progress-bar {{
            flex: 1;
            height: 6px;
            background: rgba(255,255,255,0.2);
            border-radius: 3px;
            cursor: pointer;
            position: relative;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #00d4ff, #00ff88);
            border-radius: 3px;
            width: 0%;
            transition: width 0.1s linear;
        }}
        
        .progress-bar:hover .progress-fill {{
            box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
        }}
        
        .time-display {{
            font-size: 0.9rem;
            color: rgba(255,255,255,0.7);
            min-width: 100px;
        }}
        
        .title-info {{
            display: flex;
            flex-direction: column;
            margin-left: 20px;
        }}
        
        .title-info h3 {{
            font-size: 1rem;
            color: #fff;
            font-weight: 600;
        }}
        
        .title-info p {{
            font-size: 0.8rem;
            color: rgba(255,255,255,0.5);
        }}
        
        /* Volume */
        .volume-control {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .volume-btn {{
            background: none;
            border: none;
            cursor: pointer;
            padding: 5px;
        }}
        
        .volume-btn svg {{
            width: 24px;
            height: 24px;
            fill: rgba(255,255,255,0.7);
        }}
        
        .volume-slider {{
            width: 80px;
            height: 4px;
            -webkit-appearance: none;
            background: rgba(255,255,255,0.3);
            border-radius: 2px;
            cursor: pointer;
        }}
        
        .volume-slider::-webkit-slider-thumb {{
            -webkit-appearance: none;
            width: 12px;
            height: 12px;
            background: #00d4ff;
            border-radius: 50%;
            cursor: pointer;
        }}
        
        /* Fullscreen */
        .fullscreen-btn {{
            background: none;
            border: none;
            cursor: pointer;
            padding: 10px;
        }}
        
        .fullscreen-btn svg {{
            width: 22px;
            height: 22px;
            fill: rgba(255,255,255,0.7);
            transition: fill 0.3s;
        }}
        
        .fullscreen-btn:hover svg {{
            fill: #00d4ff;
        }}
        
        /* Hidden audio */
        #audioPlayer {{
            display: none;
        }}
        
        /* Loading overlay */
        .loading-overlay {{
            position: fixed;
            inset: 0;
            background: #0a0a0f;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            transition: opacity 0.5s;
        }}
        
        .loading-overlay.hidden {{
            opacity: 0;
            pointer-events: none;
        }}
        
        .loading-spinner {{
            width: 60px;
            height: 60px;
            border: 4px solid rgba(0, 212, 255, 0.2);
            border-top-color: #00d4ff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        .loading-text {{
            margin-top: 20px;
            color: rgba(255,255,255,0.7);
        }}
    </style>
</head>
<body>
    <div class="loading-overlay" id="loadingOverlay">
        <div class="loading-spinner"></div>
        <p class="loading-text">Loading presentation...</p>
    </div>
    
    <div class="video-container">
        <div class="slides-wrapper">
            {slides_html}
        </div>
        
        <div class="control-bar">
            <button class="play-btn" id="playBtn" title="Play/Pause">
                <svg id="playIcon" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                <svg id="pauseIcon" style="display:none" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
            </button>
            
            <div class="title-info">
                <h3>{module_title}</h3>
                <p>{course_name}</p>
            </div>
            
            <div class="progress-container">
                <span class="time-display" id="currentTime">0:00</span>
                <div class="progress-bar" id="progressBar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <span class="time-display" id="totalTime">0:00</span>
            </div>
            
            <div class="volume-control">
                <button class="volume-btn" id="volumeBtn">
                    <svg viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/></svg>
                </button>
                <input type="range" class="volume-slider" id="volumeSlider" min="0" max="1" step="0.1" value="1">
            </div>
            
            <button class="fullscreen-btn" id="fullscreenBtn" title="Fullscreen">
                <svg viewBox="0 0 24 24"><path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/></svg>
            </button>
        </div>
    </div>
    
    <audio id="audioPlayer" preload="auto">
        <source src="/api/audio/{module_id}.mp3" type="audio/mpeg">
    </audio>
    
    <script>
        const audio = document.getElementById('audioPlayer');
        const playBtn = document.getElementById('playBtn');
        const playIcon = document.getElementById('playIcon');
        const pauseIcon = document.getElementById('pauseIcon');
        const progressBar = document.getElementById('progressBar');
        const progressFill = document.getElementById('progressFill');
        const currentTimeEl = document.getElementById('currentTime');
        const totalTimeEl = document.getElementById('totalTime');
        const volumeSlider = document.getElementById('volumeSlider');
        const fullscreenBtn = document.getElementById('fullscreenBtn');
        const loadingOverlay = document.getElementById('loadingOverlay');
        
        const slides = document.querySelectorAll('.slide');
        const totalSlides = slides.length;
        let currentSlide = 0;
        let isPlaying = false;
        
        // Format time
        function formatTime(seconds) {{
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${{mins}}:${{secs.toString().padStart(2, '0')}}`;
        }}
        
        // Show slide
        function showSlide(index) {{
            slides.forEach((s, i) => {{
                s.classList.toggle('active', i === index);
            }});
            currentSlide = index;
        }}
        
        // Calculate which slide to show based on audio time
        function updateSlideFromTime() {{
            if (!audio.duration) return;
            
            const progress = audio.currentTime / audio.duration;
            const slideIndex = Math.min(
                Math.floor(progress * totalSlides),
                totalSlides - 1
            );
            
            if (slideIndex !== currentSlide) {{
                showSlide(slideIndex);
            }}
        }}
        
        // Play/Pause
        function togglePlay() {{
            if (audio.paused) {{
                audio.play();
            }} else {{
                audio.pause();
            }}
        }}
        
        // Event listeners
        audio.addEventListener('loadedmetadata', () => {{
            totalTimeEl.textContent = formatTime(audio.duration);
            loadingOverlay.classList.add('hidden');
            showSlide(0);
        }});
        
        audio.addEventListener('timeupdate', () => {{
            const progress = (audio.currentTime / audio.duration) * 100;
            progressFill.style.width = `${{progress}}%`;
            currentTimeEl.textContent = formatTime(audio.currentTime);
            updateSlideFromTime();
        }});
        
        audio.addEventListener('play', () => {{
            isPlaying = true;
            playIcon.style.display = 'none';
            pauseIcon.style.display = 'block';
        }});
        
        audio.addEventListener('pause', () => {{
            isPlaying = false;
            playIcon.style.display = 'block';
            pauseIcon.style.display = 'none';
        }});
        
        audio.addEventListener('ended', () => {{
            showSlide(totalSlides - 1);
        }});
        
        playBtn.addEventListener('click', togglePlay);
        
        // Progress bar click
        progressBar.addEventListener('click', (e) => {{
            const rect = progressBar.getBoundingClientRect();
            const pos = (e.clientX - rect.left) / rect.width;
            audio.currentTime = pos * audio.duration;
        }});
        
        // Volume
        volumeSlider.addEventListener('input', (e) => {{
            audio.volume = e.target.value;
        }});
        
        // Fullscreen
        fullscreenBtn.addEventListener('click', () => {{
            if (!document.fullscreenElement) {{
                document.documentElement.requestFullscreen();
            }} else {{
                document.exitFullscreen();
            }}
        }});
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {{
            if (e.code === 'Space') {{
                e.preventDefault();
                togglePlay();
            }} else if (e.code === 'ArrowRight') {{
                audio.currentTime = Math.min(audio.currentTime + 5, audio.duration);
            }} else if (e.code === 'ArrowLeft') {{
                audio.currentTime = Math.max(audio.currentTime - 5, 0);
            }} else if (e.code === 'KeyF') {{
                fullscreenBtn.click();
            }}
        }});
        
        // Auto-start option (click anywhere to start)
        document.addEventListener('click', (e) => {{
            if (e.target.closest('.control-bar')) return;
            if (!isPlaying && audio.paused) {{
                togglePlay();
            }}
        }}, {{ once: true }});
        
        // Initialize
        showSlide(0);
    </script>
</body>
</html>'''
    
    return html


async def generate_audio_for_module(script_text: str, module_id: str) -> bool:
    """Generate TTS audio"""
    from emergentintegrations.llm.openai import OpenAITextToSpeech
    
    api_key = os.getenv("EMERGENT_LLM_KEY")
    if not api_key:
        return False
    
    tts = OpenAITextToSpeech(api_key=api_key)
    
    # Clean script
    clean_text = script_text.replace('#', '').replace('[', '').replace(']', '')
    clean_text = clean_text.replace('INTRODUCTION', 'Introduction')
    clean_text = clean_text.replace('SECTION', 'Section')
    clean_text = clean_text.replace('CONCLUSION', 'Conclusion')
    clean_text = clean_text.replace('PAUSE', '...')
    clean_text = ' '.join(clean_text.split())
    
    # Split into chunks
    chunks = []
    words = clean_text.split()
    current_chunk = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 > 3800:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
            current_length += len(word) + 1
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    print(f"  Generating audio ({len(chunks)} chunks)...")
    
    all_audio = b''
    for i, chunk in enumerate(chunks):
        try:
            audio_bytes = await tts.generate_speech(
                text=chunk,
                model="tts-1-hd",
                voice="nova",
                speed=0.95
            )
            all_audio += audio_bytes
        except Exception as e:
            print(f"    Error: {e}")
            return False
    
    output_path = AUDIO_DIR / f"{module_id}.mp3"
    with open(output_path, "wb") as f:
        f.write(all_audio)
    
    print(f"  Audio saved: {len(all_audio)/1024:.1f} KB")
    return True


async def create_auto_presentation(module_id: str, db) -> Dict:
    """Create auto-playing presentation for a module"""
    
    module = db.modules.find_one({"module_id": module_id})
    if not module:
        return {"success": False, "error": "Module not found"}
    
    script_doc = db.module_scripts.find_one({"module_id": module_id})
    if not script_doc:
        return {"success": False, "error": "Script not found"}
    
    course = db.courses.find_one({"external_id": module.get("courseId")})
    course_name = course.get("course_name", "Course") if course else "Course"
    
    script_text = script_doc.get("script_text", "")
    module_title = module.get("title", module_id)
    
    print(f"\n{'='*50}")
    print(f"Creating: {module_title}")
    print(f"{'='*50}")
    
    # 1. Parse slides
    slides = parse_script_to_slides(script_text, module_title)
    print(f"  {len(slides)} slides created")
    
    # 2. Generate HTML
    html = generate_auto_presentation_html(slides, module_id, module_title, course_name)
    html_path = PRESENTATIONS_DIR / f"{module_id}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Presentation saved")
    
    # 3. Generate audio if not exists
    audio_path = AUDIO_DIR / f"{module_id}.mp3"
    if not audio_path.exists():
        await generate_audio_for_module(script_text, module_id)
    else:
        print(f"  Audio exists")
    
    return {
        "success": True,
        "module_id": module_id,
        "title": module_title,
        "slides": len(slides)
    }


async def create_course_auto_presentations(course_id: str) -> List[Dict]:
    """Create auto presentations for all modules in a course"""
    
    client = MongoClient('mongodb://localhost:27017')
    db = client['test_database']
    
    modules = list(db.modules.find({"courseId": course_id}).sort("order", 1))
    print(f"Course: {course_id} - {len(modules)} modules")
    
    results = []
    for module in modules:
        result = await create_auto_presentation(module["module_id"], db)
        results.append(result)
    
    return results


if __name__ == "__main__":
    async def main():
        results = await create_course_auto_presentations("UG_DENT_Y1_S1_C01")
        print("\n" + "="*50)
        print("DONE")
        for r in results:
            print(f"  ✓ {r.get('title')} - {r.get('slides')} slides")
    
    asyncio.run(main())
