"""
Visual Presentation Generator - Creates rich presentations with images
"""

import os
import asyncio
import json
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

PRESENTATIONS_DIR = Path("/app/backend/presentations")
AUDIO_DIR = Path("/app/backend/audio")
PRESENTATIONS_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True)

# Topic to image mapping for educational content
TOPIC_IMAGES = {
    "cell": [
        "https://images.unsplash.com/photo-1767486366936-c41b4f767eb8?w=800",  # Plant cells
        "https://images.unsplash.com/photo-1647083701139-3930542304cf?w=800",  # Microscope view
        "https://images.unsplash.com/photo-1758206523826-a65d4cf070aa?w=800",  # Scientist microscope
    ],
    "dna": [
        "https://images.unsplash.com/photo-1705256811175-b1e3398d50e4?w=800",  # DNA helix blue
        "https://images.unsplash.com/photo-1702802120585-7b682d4e73de?w=800",  # DNA structure
        "https://images.unsplash.com/photo-1604538406338-d41ddc825eb3?w=800",  # DNA spiral
    ],
    "genetics": [
        "https://images.unsplash.com/photo-1705256811175-b1e3398d50e4?w=800",
        "https://images.unsplash.com/photo-1578496479914-7ef3b0193be3?w=800",
        "https://images.unsplash.com/photo-1702802120585-7b682d4e73de?w=800",
    ],
    "evolution": [
        "https://images.unsplash.com/photo-1758656803198-eeea35110219?w=800",  # Blood cells
        "https://images.unsplash.com/photo-1758702046109-1ca08784e691?w=800",  # Plant roots
        "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=800",
    ],
    "biology": [
        "https://images.unsplash.com/photo-1530026405186-ed1f139313f8?w=800",
        "https://images.unsplash.com/photo-1576086213369-97a306d36557?w=800",
        "https://images.unsplash.com/photo-1581093450021-4a7360e9a6b5?w=800",
    ],
    "anatomy": [
        "https://images.unsplash.com/photo-1559757175-7cb057fba93c?w=800",
        "https://images.unsplash.com/photo-1530497610245-94d3c16cda28?w=800",
        "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=800",
    ],
    "medical": [
        "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=800",
        "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=800",
        "https://images.unsplash.com/photo-1551076805-e1869033e561?w=800",
    ],
    "default": [
        "https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=800",  # Science lab
        "https://images.unsplash.com/photo-1507413245164-6160d8298b31?w=800",  # Laboratory
        "https://images.unsplash.com/photo-1518152006812-edab29b069ac?w=800",  # Research
    ]
}


def get_topic_images(title: str, content: str) -> List[str]:
    """Get relevant images based on topic keywords"""
    text = (title + " " + content).lower()
    
    for topic, images in TOPIC_IMAGES.items():
        if topic in text:
            return images
    
    return TOPIC_IMAGES["default"]


def parse_script_to_visual_slides(script_text: str, module_title: str) -> List[Dict]:
    """Parse script into visual slide sections with images"""
    slides = []
    
    lines = script_text.strip().split('\n')
    current_slide = {
        "title": module_title,
        "content": [],
        "type": "title",
        "key_points": []
    }
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('#'):
            if current_slide["content"] or current_slide["type"] == "title":
                slides.append(current_slide)
            title = line.replace('#', '').strip()
            current_slide = {"title": title, "content": [], "type": "section", "key_points": []}
            
        elif line.startswith('[') and line.endswith(']'):
            if current_slide["content"]:
                slides.append(current_slide)
            section_name = line[1:-1].replace('_', ' ').title()
            current_slide = {"title": section_name, "content": [], "type": "section", "key_points": []}
            
        elif line.startswith('-'):
            point = line[1:].strip()
            current_slide["key_points"].append(point)
            current_slide["content"].append({"type": "bullet", "text": point})
        else:
            current_slide["content"].append({"type": "text", "text": line})
    
    if current_slide["content"] or current_slide["type"] == "title":
        slides.append(current_slide)
    
    # Add images to each slide
    for i, slide in enumerate(slides):
        content_text = ' '.join([c["text"] for c in slide.get("content", [])])
        images = get_topic_images(slide["title"], content_text)
        slide["image"] = images[i % len(images)]
    
    return slides


def generate_visual_html(slides: List[Dict], module_id: str, module_title: str, course_name: str) -> str:
    """Generate visual HTML presentation with images"""
    
    slides_html = ""
    for i, slide in enumerate(slides):
        # Build content HTML
        content_html = ""
        bullet_items = [c for c in slide.get("content", []) if c["type"] == "bullet"]
        text_items = [c for c in slide.get("content", []) if c["type"] == "text"]
        
        if text_items:
            for item in text_items[:2]:  # Limit text to keep visual focus
                content_html += f'<p class="slide-text">{item["text"]}</p>\n'
        
        if bullet_items:
            content_html += '<ul class="key-points">\n'
            for item in bullet_items[:4]:  # Limit to 4 key points per slide
                content_html += f'<li>{item["text"]}</li>\n'
            content_html += '</ul>\n'
        
        image_url = slide.get("image", TOPIC_IMAGES["default"][0])
        slide_class = "title-slide" if slide["type"] == "title" else "content-slide"
        
        slides_html += f'''
        <section class="slide {slide_class}" id="slide-{i}" data-index="{i}">
            <div class="slide-image-container">
                <img src="{image_url}" alt="{slide['title']}" class="slide-image" loading="lazy">
                <div class="slide-overlay"></div>
            </div>
            <div class="slide-content-wrapper">
                <h2 class="slide-title">{slide["title"]}</h2>
                <div class="slide-content">
                    {content_html}
                </div>
            </div>
            <div class="slide-progress">
                <span class="current">{i + 1}</span>
                <span class="separator">/</span>
                <span class="total">{len(slides)}</span>
            </div>
        </section>
        '''
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{module_title} - {course_name}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        html {{
            scroll-behavior: smooth;
        }}
        
        body {{
            font-family: 'Poppins', sans-serif;
            background: #0a0a0f;
            color: #fff;
            overflow-x: hidden;
        }}
        
        /* Header */
        .presentation-header {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            background: rgba(10, 10, 15, 0.95);
            backdrop-filter: blur(20px);
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        
        .course-info h1 {{
            font-size: 1.2rem;
            font-weight: 600;
            color: #00d4ff;
        }}
        
        .course-info p {{
            font-size: 0.85rem;
            color: rgba(255,255,255,0.6);
        }}
        
        /* Audio Player */
        .audio-section {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .audio-section audio {{
            height: 40px;
            border-radius: 20px;
        }}
        
        .audio-label {{
            font-size: 0.8rem;
            color: #00d4ff;
        }}
        
        /* Slides Container */
        .slides-container {{
            padding-top: 80px;
        }}
        
        /* Individual Slide */
        .slide {{
            position: relative;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }}
        
        .slide-image-container {{
            position: absolute;
            inset: 0;
            z-index: 1;
        }}
        
        .slide-image {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            filter: brightness(0.4);
            transition: transform 0.5s ease;
        }}
        
        .slide:hover .slide-image {{
            transform: scale(1.02);
        }}
        
        .slide-overlay {{
            position: absolute;
            inset: 0;
            background: linear-gradient(
                135deg,
                rgba(0, 0, 0, 0.7) 0%,
                rgba(0, 0, 0, 0.3) 50%,
                rgba(0, 212, 255, 0.1) 100%
            );
        }}
        
        .slide-content-wrapper {{
            position: relative;
            z-index: 10;
            max-width: 900px;
            padding: 60px;
            background: rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.1);
            margin: 20px;
        }}
        
        .title-slide .slide-content-wrapper {{
            text-align: center;
            background: rgba(0, 212, 255, 0.1);
            border-color: rgba(0, 212, 255, 0.3);
        }}
        
        .slide-title {{
            font-size: 2.5rem;
            font-weight: 700;
            color: #fff;
            margin-bottom: 25px;
            text-shadow: 2px 2px 10px rgba(0,0,0,0.5);
        }}
        
        .title-slide .slide-title {{
            font-size: 3rem;
            color: #00d4ff;
        }}
        
        .slide-content {{
            font-size: 1.2rem;
            line-height: 1.8;
        }}
        
        .slide-text {{
            margin-bottom: 20px;
            color: rgba(255,255,255,0.9);
        }}
        
        .key-points {{
            list-style: none;
            padding: 0;
        }}
        
        .key-points li {{
            padding: 15px 0 15px 40px;
            position: relative;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            font-size: 1.1rem;
        }}
        
        .key-points li:last-child {{
            border-bottom: none;
        }}
        
        .key-points li::before {{
            content: "";
            position: absolute;
            left: 0;
            top: 50%;
            transform: translateY(-50%);
            width: 20px;
            height: 20px;
            background: linear-gradient(135deg, #00d4ff, #00ff88);
            border-radius: 50%;
            box-shadow: 0 0 15px rgba(0, 212, 255, 0.5);
        }}
        
        .slide-progress {{
            position: absolute;
            bottom: 30px;
            right: 40px;
            z-index: 20;
            background: rgba(0,0,0,0.5);
            padding: 10px 20px;
            border-radius: 30px;
            font-size: 0.9rem;
        }}
        
        .slide-progress .current {{
            color: #00d4ff;
            font-weight: 600;
        }}
        
        .slide-progress .separator {{
            color: rgba(255,255,255,0.3);
            margin: 0 5px;
        }}
        
        /* Navigation Dots */
        .nav-dots {{
            position: fixed;
            right: 30px;
            top: 50%;
            transform: translateY(-50%);
            z-index: 1000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        
        .nav-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: rgba(255,255,255,0.3);
            cursor: pointer;
            transition: all 0.3s ease;
            border: 2px solid transparent;
        }}
        
        .nav-dot:hover, .nav-dot.active {{
            background: #00d4ff;
            border-color: #fff;
            transform: scale(1.3);
        }}
        
        /* Controls */
        .controls {{
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1000;
            display: flex;
            gap: 15px;
            background: rgba(0,0,0,0.8);
            padding: 15px 25px;
            border-radius: 50px;
            backdrop-filter: blur(10px);
        }}
        
        .control-btn {{
            background: transparent;
            border: 2px solid rgba(255,255,255,0.3);
            color: #fff;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 1.2rem;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .control-btn:hover {{
            border-color: #00d4ff;
            color: #00d4ff;
            transform: scale(1.1);
        }}
        
        .control-btn.play-btn {{
            background: #00d4ff;
            border-color: #00d4ff;
            color: #0a0a0f;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .slide-content-wrapper {{
                padding: 30px;
                margin: 15px;
            }}
            
            .slide-title {{
                font-size: 1.8rem;
            }}
            
            .title-slide .slide-title {{
                font-size: 2rem;
            }}
            
            .slide-content {{
                font-size: 1rem;
            }}
            
            .nav-dots {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <header class="presentation-header">
        <div class="course-info">
            <h1>{module_title}</h1>
            <p>{course_name}</p>
        </div>
        <div class="audio-section">
            <span class="audio-label">Audio Narration</span>
            <audio id="audioPlayer" controls>
                <source src="/api/audio/{module_id}.mp3" type="audio/mpeg">
            </audio>
        </div>
    </header>
    
    <nav class="nav-dots" id="navDots"></nav>
    
    <main class="slides-container">
        {slides_html}
    </main>
    
    <div class="controls">
        <button class="control-btn" onclick="prevSlide()" title="Previous">&#9664;</button>
        <button class="control-btn play-btn" onclick="toggleAudio()" id="playBtn" title="Play/Pause">&#9658;</button>
        <button class="control-btn" onclick="nextSlide()" title="Next">&#9654;</button>
    </div>
    
    <script>
        const slides = document.querySelectorAll('.slide');
        const audio = document.getElementById('audioPlayer');
        const playBtn = document.getElementById('playBtn');
        const navDotsContainer = document.getElementById('navDots');
        let currentSlide = 0;
        
        // Create navigation dots
        slides.forEach((_, i) => {{
            const dot = document.createElement('div');
            dot.className = 'nav-dot' + (i === 0 ? ' active' : '');
            dot.onclick = () => goToSlide(i);
            navDotsContainer.appendChild(dot);
        }});
        
        function updateDots() {{
            document.querySelectorAll('.nav-dot').forEach((dot, i) => {{
                dot.classList.toggle('active', i === currentSlide);
            }});
        }}
        
        function goToSlide(index) {{
            currentSlide = index;
            slides[index].scrollIntoView({{ behavior: 'smooth' }});
            updateDots();
        }}
        
        function nextSlide() {{
            if (currentSlide < slides.length - 1) {{
                goToSlide(currentSlide + 1);
            }}
        }}
        
        function prevSlide() {{
            if (currentSlide > 0) {{
                goToSlide(currentSlide - 1);
            }}
        }}
        
        function toggleAudio() {{
            if (audio.paused) {{
                audio.play();
                playBtn.innerHTML = '&#10074;&#10074;';
            }} else {{
                audio.pause();
                playBtn.innerHTML = '&#9658;';
            }}
        }}
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowRight' || e.key === 'ArrowDown') nextSlide();
            if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') prevSlide();
            if (e.key === ' ') {{ e.preventDefault(); toggleAudio(); }}
        }});
        
        // Scroll detection
        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    currentSlide = parseInt(entry.target.dataset.index);
                    updateDots();
                }}
            }});
        }}, {{ threshold: 0.5 }});
        
        slides.forEach(slide => observer.observe(slide));
        
        // Audio state
        audio.addEventListener('play', () => playBtn.innerHTML = '&#10074;&#10074;');
        audio.addEventListener('pause', () => playBtn.innerHTML = '&#9658;');
    </script>
</body>
</html>'''
    
    return html


async def generate_audio_tts(script_text: str, module_id: str, voice: str = "nova") -> bool:
    """Generate audio narration using OpenAI TTS"""
    from emergentintegrations.llm.openai import OpenAITextToSpeech
    
    api_key = os.getenv("EMERGENT_LLM_KEY")
    if not api_key:
        print("Error: EMERGENT_LLM_KEY not found")
        return False
    
    tts = OpenAITextToSpeech(api_key=api_key)
    
    # Clean script for speech
    clean_text = script_text.replace('#', '').replace('[', '').replace(']', '')
    clean_text = clean_text.replace('INTRODUCTION', 'Introduction')
    clean_text = clean_text.replace('SECTION', 'Section')
    clean_text = clean_text.replace('CONCLUSION', 'Conclusion')
    clean_text = clean_text.replace('PAUSE', '...')
    clean_text = ' '.join(clean_text.split())
    
    # Split into chunks (4096 char limit)
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
                model="tts-1-hd",  # High quality
                voice=voice,
                speed=0.95  # Slightly slower for educational content
            )
            all_audio += audio_bytes
            print(f"    Chunk {i+1}/{len(chunks)} done")
        except Exception as e:
            print(f"    Error: {e}")
            return False
    
    output_path = AUDIO_DIR / f"{module_id}.mp3"
    with open(output_path, "wb") as f:
        f.write(all_audio)
    
    print(f"  Audio saved: {len(all_audio)/1024:.1f} KB")
    return True


async def generate_visual_presentation(module_id: str, db) -> Dict:
    """Generate visual presentation with images and audio"""
    
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
    print(f"Generating: {module_title}")
    print(f"{'='*50}")
    
    # 1. Parse and create visual slides
    slides = parse_script_to_visual_slides(script_text, module_title)
    print(f"  Created {len(slides)} visual slides")
    
    # 2. Generate HTML
    html = generate_visual_html(slides, module_id, module_title, course_name)
    html_path = PRESENTATIONS_DIR / f"{module_id}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Presentation saved")
    
    # 3. Generate audio
    audio_success = await generate_audio_tts(script_text, module_id)
    
    return {
        "success": True,
        "module_id": module_id,
        "module_title": module_title,
        "slides_count": len(slides),
        "audio_generated": audio_success
    }


async def generate_course_visual_presentations(course_id: str) -> List[Dict]:
    """Generate visual presentations for all modules in a course"""
    
    client = MongoClient('mongodb://localhost:27017')
    db = client['test_database']
    
    modules = list(db.modules.find({"courseId": course_id}).sort("order", 1))
    print(f"\nCourse: {course_id}")
    print(f"Modules to process: {len(modules)}")
    
    results = []
    for module in modules:
        result = await generate_visual_presentation(module["module_id"], db)
        results.append(result)
    
    return results


if __name__ == "__main__":
    async def main():
        client = MongoClient('mongodb://localhost:27017')
        db = client['test_database']
        result = await generate_visual_presentation("UG_DENT_Y1_S1_C01_M01", db)
        print(f"\nResult: {result}")
    
    asyncio.run(main())
