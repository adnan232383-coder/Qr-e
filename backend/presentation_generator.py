"""
Presentation and Audio Generator for Course Modules
Creates HTML presentations and MP3 audio narration
"""

import os
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# Directories
PRESENTATIONS_DIR = Path("/app/backend/presentations")
AUDIO_DIR = Path("/app/backend/audio")
PRESENTATIONS_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True)


def parse_script_to_slides(script_text: str, module_title: str) -> List[Dict]:
    """Parse a script into slide sections"""
    slides = []
    
    # Clean up script
    lines = script_text.strip().split('\n')
    current_slide = {"title": module_title, "content": [], "type": "title"}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for section markers
        if line.startswith('#'):
            # Save previous slide if has content
            if current_slide["content"] or current_slide["type"] == "title":
                slides.append(current_slide)
            # Start new slide
            title = line.replace('#', '').strip()
            current_slide = {"title": title, "content": [], "type": "section"}
        elif line.startswith('[') and line.endswith(']'):
            # Section marker like [INTRODUCTION]
            if current_slide["content"]:
                slides.append(current_slide)
            section_name = line[1:-1].replace('_', ' ').title()
            current_slide = {"title": section_name, "content": [], "type": "section"}
        elif line.startswith('-'):
            # Bullet point
            current_slide["content"].append({"type": "bullet", "text": line[1:].strip()})
        else:
            # Regular text
            current_slide["content"].append({"type": "text", "text": line})
    
    # Add last slide
    if current_slide["content"] or current_slide["type"] == "title":
        slides.append(current_slide)
    
    return slides


def generate_html_presentation(slides: List[Dict], module_id: str, module_title: str, course_name: str) -> str:
    """Generate an HTML presentation from slides"""
    
    slides_html = ""
    for i, slide in enumerate(slides):
        content_html = ""
        for item in slide.get("content", []):
            if item["type"] == "bullet":
                content_html += f'<li>{item["text"]}</li>\n'
            else:
                content_html += f'<p>{item["text"]}</p>\n'
        
        if slide.get("content") and any(c["type"] == "bullet" for c in slide["content"]):
            content_html = f'<ul>{content_html}</ul>'
        
        slide_class = "title-slide" if slide["type"] == "title" else "content-slide"
        
        slides_html += f'''
        <div class="slide {slide_class}" id="slide-{i}">
            <h2>{slide["title"]}</h2>
            <div class="slide-content">
                {content_html}
            </div>
            <div class="slide-number">{i + 1} / {len(slides)}</div>
        </div>
        '''
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{module_title} - {course_name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
        }}
        
        .presentation-container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            text-align: center;
            padding: 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            margin-bottom: 20px;
        }}
        
        .header h1 {{
            font-size: 1.8rem;
            color: #00d4ff;
            margin-bottom: 5px;
        }}
        
        .header p {{
            color: #888;
            font-size: 0.9rem;
        }}
        
        .audio-player {{
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
            text-align: center;
        }}
        
        .audio-player h3 {{
            margin-bottom: 15px;
            color: #00d4ff;
        }}
        
        audio {{
            width: 100%;
            max-width: 500px;
        }}
        
        .slides-container {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        
        .slide {{
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 40px;
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.3s ease;
        }}
        
        .slide:hover {{
            border-color: #00d4ff;
            transform: translateY(-2px);
        }}
        
        .title-slide {{
            text-align: center;
            background: linear-gradient(135deg, rgba(0,212,255,0.2) 0%, rgba(0,212,255,0.05) 100%);
        }}
        
        .title-slide h2 {{
            font-size: 2rem;
            color: #00d4ff;
        }}
        
        .slide h2 {{
            color: #00d4ff;
            margin-bottom: 20px;
            font-size: 1.5rem;
            border-bottom: 2px solid rgba(0,212,255,0.3);
            padding-bottom: 10px;
        }}
        
        .slide-content {{
            line-height: 1.8;
            font-size: 1.1rem;
        }}
        
        .slide-content p {{
            margin-bottom: 15px;
        }}
        
        .slide-content ul {{
            list-style: none;
            padding-left: 20px;
        }}
        
        .slide-content li {{
            margin-bottom: 12px;
            padding-left: 25px;
            position: relative;
        }}
        
        .slide-content li::before {{
            content: "▸";
            color: #00d4ff;
            position: absolute;
            left: 0;
        }}
        
        .slide-number {{
            text-align: right;
            color: #666;
            font-size: 0.8rem;
            margin-top: 20px;
        }}
        
        .navigation {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            display: flex;
            gap: 10px;
        }}
        
        .nav-btn {{
            background: #00d4ff;
            color: #1a1a2e;
            border: none;
            padding: 15px 25px;
            border-radius: 10px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
        }}
        
        .nav-btn:hover {{
            transform: scale(1.05);
            box-shadow: 0 5px 20px rgba(0,212,255,0.4);
        }}
        
        @media (max-width: 768px) {{
            .slide {{
                padding: 20px;
            }}
            .title-slide h2 {{
                font-size: 1.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="presentation-container">
        <div class="header">
            <h1>{module_title}</h1>
            <p>{course_name}</p>
        </div>
        
        <div class="audio-player" id="audio-section">
            <h3>Audio Narration</h3>
            <audio controls id="audioPlayer">
                <source src="/api/audio/{module_id}.mp3" type="audio/mpeg">
                Your browser does not support audio.
            </audio>
        </div>
        
        <div class="slides-container">
            {slides_html}
        </div>
    </div>
    
    <script>
        // Auto-scroll to current slide based on audio time (optional enhancement)
        const audio = document.getElementById('audioPlayer');
        const slides = document.querySelectorAll('.slide');
        
        // Simple keyboard navigation
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowRight') {{
                audio.currentTime += 10;
            }} else if (e.key === 'ArrowLeft') {{
                audio.currentTime -= 10;
            }} else if (e.key === ' ') {{
                e.preventDefault();
                if (audio.paused) audio.play();
                else audio.pause();
            }}
        }});
    </script>
</body>
</html>'''
    
    return html


async def generate_audio(script_text: str, module_id: str, voice: str = "nova") -> bool:
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
    clean_text = ' '.join(clean_text.split())  # Normalize whitespace
    
    # Split into chunks if too long (4096 char limit)
    chunks = []
    words = clean_text.split()
    current_chunk = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 > 3800:  # Leave margin
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
            current_length += len(word) + 1
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    print(f"  Generating audio in {len(chunks)} chunk(s)...")
    
    # Generate audio for each chunk
    all_audio = b''
    for i, chunk in enumerate(chunks):
        try:
            audio_bytes = await tts.generate_speech(
                text=chunk,
                model="tts-1",
                voice=voice,
                speed=1.0
            )
            all_audio += audio_bytes
            print(f"    Chunk {i+1}/{len(chunks)} done")
        except Exception as e:
            print(f"    Error on chunk {i+1}: {e}")
            return False
    
    # Save audio file
    output_path = AUDIO_DIR / f"{module_id}.mp3"
    with open(output_path, "wb") as f:
        f.write(all_audio)
    
    print(f"  Audio saved: {output_path} ({len(all_audio)/1024:.1f} KB)")
    return True


async def generate_module_presentation(module_id: str, db) -> Dict:
    """Generate presentation and audio for a single module"""
    
    # Get module info
    module = db.modules.find_one({"module_id": module_id})
    if not module:
        return {"success": False, "error": "Module not found"}
    
    # Get script
    script_doc = db.module_scripts.find_one({"module_id": module_id})
    if not script_doc:
        return {"success": False, "error": "Script not found"}
    
    # Get course info
    course = db.courses.find_one({"external_id": module.get("courseId")})
    course_name = course.get("course_name", "Course") if course else "Course"
    
    script_text = script_doc.get("script_text", "")
    module_title = module.get("title", module_id)
    
    print(f"\nGenerating for: {module_title}")
    
    # 1. Parse script into slides
    slides = parse_script_to_slides(script_text, module_title)
    print(f"  Created {len(slides)} slides")
    
    # 2. Generate HTML presentation
    html = generate_html_presentation(slides, module_id, module_title, course_name)
    html_path = PRESENTATIONS_DIR / f"{module_id}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Presentation saved: {html_path}")
    
    # 3. Generate audio
    audio_success = await generate_audio(script_text, module_id)
    
    return {
        "success": True,
        "module_id": module_id,
        "presentation_path": str(html_path),
        "audio_generated": audio_success,
        "slides_count": len(slides)
    }


async def generate_course_presentations(course_id: str) -> List[Dict]:
    """Generate presentations for all modules in a course"""
    
    client = MongoClient('mongodb://localhost:27017')
    db = client['test_database']
    
    # Get all modules for the course
    modules = list(db.modules.find({"courseId": course_id}).sort("order", 1))
    print(f"Found {len(modules)} modules for course {course_id}")
    
    results = []
    for module in modules:
        result = await generate_module_presentation(module["module_id"], db)
        results.append(result)
    
    return results


if __name__ == "__main__":
    # Test with one module
    async def main():
        client = MongoClient('mongodb://localhost:27017')
        db = client['test_database']
        result = await generate_module_presentation("UG_DENT_Y1_S1_C01_M01", db)
        print(f"\nResult: {result}")
    
    asyncio.run(main())
