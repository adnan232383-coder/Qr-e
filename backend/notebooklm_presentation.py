"""
NotebookLM Style Presentation Generator
Creates presentations with hand-drawn illustrations, infographics, and animations
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

# Generated illustration URLs - comprehensive library
ILLUSTRATIONS = {
    # Cell Biology
    "cell": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/8b3b9bc2921652d9a7d382da47f411eebdb611ef0920044f3dfe36f735e43e93.png",
    "cell_membrane": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/cb81ddda1ff60e878c1d4b90ba55b42579b1b6631f2a8e1d258f70e812d767c2.png",
    "mitochondria": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/a8e3ca2c395891a3f61c8696f4d0aaee9f13f544a38411d0eb23854d2a12e326.png",
    "nucleus": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/6147ec29bbf3d1f7ddd038a1b85ddfe6c4ecbd3daf6c4543d035516ee5f6d151.png",
    "cell_comparison": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/c77a7cf2bdb23050773632fc08281c958e2c054d025f7974aa221ba1d667a935.png",
    "microscope": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/76ee0be816211a9fb709210d6eca541ead88b348d0f8304dc0bdfe6fcfb97eea.png",
    
    # Genetics
    "dna": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/03fda0d7d0e11fe1aa768feab16f01f17e60b9c74cdb6c5fe6f99c8f00e9a235.png",
    "dna_replication": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/8bc00faae592d23a8f26156060081200e53f727040bcab90bb53cf4fca04871e.png",
    "gene_expression": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/c2c9932ea2abc61d19025bd4dc359cd1bc9c5bf56050dab793628cbf58e4d4af.png",
    
    # Evolution
    "evolution_tree": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/7d275c5e3de67ab648b80d4d9df7080a6651d86ca0e8348d6a10ae34e3e99c91.png",
    "natural_selection": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/8e70304b7d6e12c5b948cb2aca8e8215e6f108a1a110532907fd15519a7c1397.png",
    
    # General
    "icons": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/bc48f99a753b5699d104fe3caf5452877c8ce777c116a3ec53921f4d7c81715f.png",
}

# Topic to illustrations mapping
TOPIC_ILLUSTRATIONS = {
    "cell structure": ["cell", "cell_membrane", "cell_comparison"],
    "membrane": ["cell_membrane", "cell"],
    "mitochondria": ["mitochondria", "cell"],
    "nucleus": ["nucleus", "cell"],
    "organelle": ["cell", "mitochondria", "nucleus"],
    "dna": ["dna", "dna_replication", "nucleus"],
    "genetic": ["dna", "gene_expression", "dna_replication"],
    "replication": ["dna_replication", "dna"],
    "transcription": ["gene_expression", "dna"],
    "translation": ["gene_expression"],
    "evolution": ["evolution_tree", "natural_selection"],
    "natural selection": ["natural_selection", "evolution_tree"],
    "darwin": ["natural_selection"],
    "diversity": ["evolution_tree", "cell_comparison"],
    "introduction": ["microscope"],
    "learning": ["microscope", "icons"],
    "summary": ["icons"],
    "conclusion": ["icons"],
}


def get_illustration_for_content(title: str, content: str) -> str:
    """Get the best matching illustration for the slide content"""
    text = (title + " " + content).lower()
    
    # Check topic mappings
    for topic, illustrations in TOPIC_ILLUSTRATIONS.items():
        if topic in text:
            return ILLUSTRATIONS.get(illustrations[0], ILLUSTRATIONS["cell"])
    
    # Default based on keywords
    if any(word in text for word in ["cell", "organelle", "membrane"]):
        return ILLUSTRATIONS["cell"]
    elif any(word in text for word in ["dna", "gene", "genetic"]):
        return ILLUSTRATIONS["dna"]
    elif any(word in text for word in ["evolution", "darwin", "selection"]):
        return ILLUSTRATIONS["evolution_tree"]
    
    return ILLUSTRATIONS["microscope"]


def parse_script_to_notebooklm_slides(script_text: str, module_title: str) -> List[Dict]:
    """Parse script into NotebookLM-style slides with key points and stats"""
    slides = []
    
    # Determine module type for better illustration selection
    module_lower = module_title.lower()
    if "cell" in module_lower:
        hero_illustration = ILLUSTRATIONS["microscope"]
        default_illustration = ILLUSTRATIONS["cell"]
    elif "genetic" in module_lower:
        hero_illustration = ILLUSTRATIONS["dna"]
        default_illustration = ILLUSTRATIONS["dna_replication"]
    elif "evolution" in module_lower:
        hero_illustration = ILLUSTRATIONS["evolution_tree"]
        default_illustration = ILLUSTRATIONS["natural_selection"]
    else:
        hero_illustration = ILLUSTRATIONS["microscope"]
        default_illustration = ILLUSTRATIONS["cell"]
    
    # Title slide
    slides.append({
        "type": "title",
        "title": module_title,
        "subtitle": "Educational Module",
        "illustration": hero_illustration
    })
    
    # Parse sections from script
    lines = script_text.strip().split('\n')
    current_section = None
    current_points = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('#'):
            if current_section and current_points:
                # Get best illustration for this section
                content_text = ' '.join(current_points)
                illustration = get_illustration_for_content(current_section, content_text)
                slides.append({
                    "type": "content",
                    "title": current_section,
                    "points": current_points[:4],
                    "illustration": illustration
                })
            current_section = line.replace('#', '').strip()
            current_points = []
        elif line.startswith('[') and line.endswith(']'):
            section_name = line[1:-1].replace('_', ' ').title()
            if current_section and current_points:
                content_text = ' '.join(current_points)
                illustration = get_illustration_for_content(current_section, content_text)
                slides.append({
                    "type": "content",
                    "title": current_section,
                    "points": current_points[:4],
                    "illustration": illustration
                })
            current_section = section_name
            current_points = []
        elif line.startswith('-'):
            current_points.append(line[1:].strip())
        else:
            # Add as a point if it's substantial
            if len(line) > 20:
                current_points.append(line[:100])
    
    # Add remaining section
    if current_section and current_points:
        slides.append({
            "type": "content",
            "title": current_section,
            "points": current_points[:4],
            "illustration": ILLUSTRATIONS["icons"]
        })
    
    # Add statistics slide
    slides.append({
        "type": "stats",
        "title": "Key Numbers",
        "stats": [
            {"number": "3", "label": "Main Components"},
            {"number": "100%", "label": "Visual Learning"},
            {"number": "12", "label": "Minutes Duration"}
        ],
        "illustration": ILLUSTRATIONS["icons"]
    })
    
    # Add summary slide
    slides.append({
        "type": "summary",
        "title": "Key Takeaways",
        "points": [
            "Understanding cellular structure is fundamental",
            "Each organelle has a specific function",
            "Cells are the building blocks of life"
        ],
        "illustration": ILLUSTRATIONS["cell"]
    })
    
    return slides


def generate_notebooklm_html(slides: List[Dict], module_id: str, module_title: str, course_name: str) -> str:
    """Generate NotebookLM-style presentation HTML"""
    
    slides_html = ""
    for i, slide in enumerate(slides):
        if slide["type"] == "title":
            slides_html += f'''
            <div class="slide title-slide" data-index="{i}">
                <div class="slide-content-area">
                    <div class="title-content">
                        <h1 class="main-title">{slide["title"]}</h1>
                        <p class="subtitle">{slide.get("subtitle", course_name)}</p>
                    </div>
                </div>
                <div class="illustration-area">
                    <img src="{slide.get('illustration', '')}" alt="" class="main-illustration">
                </div>
            </div>
            '''
        elif slide["type"] == "stats":
            stats_html = ""
            for stat in slide.get("stats", []):
                stats_html += f'''
                <div class="stat-card">
                    <div class="stat-number">{stat["number"]}</div>
                    <div class="stat-label">{stat["label"]}</div>
                </div>
                '''
            slides_html += f'''
            <div class="slide stats-slide" data-index="{i}">
                <div class="slide-content-area">
                    <h2 class="section-title">{slide["title"]}</h2>
                    <div class="stats-grid">
                        {stats_html}
                    </div>
                </div>
                <div class="illustration-area">
                    <img src="{slide.get('illustration', '')}" alt="" class="main-illustration">
                </div>
            </div>
            '''
        else:  # content or summary
            points_html = ""
            for point in slide.get("points", []):
                points_html += f'''
                <div class="point-item">
                    <div class="point-icon">
                        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/></svg>
                    </div>
                    <div class="point-text">{point}</div>
                </div>
                '''
            slides_html += f'''
            <div class="slide content-slide" data-index="{i}">
                <div class="slide-content-area">
                    <h2 class="section-title">{slide["title"]}</h2>
                    <div class="points-container">
                        {points_html}
                    </div>
                </div>
                <div class="illustration-area">
                    <img src="{slide.get('illustration', '')}" alt="" class="main-illustration">
                </div>
            </div>
            '''
    
    total_slides = len(slides)
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{module_title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        :root {{
            --bg-primary: #fafafa;
            --bg-secondary: #ffffff;
            --text-primary: #1a1a2e;
            --text-secondary: #64748b;
            --accent: #0ea5e9;
            --accent-light: #e0f2fe;
            --success: #10b981;
        }}
        
        body {{
            font-family: 'Inter', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            overflow: hidden;
        }}
        
        .presentation-container {{
            height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        
        /* Slides Area */
        .slides-wrapper {{
            flex: 1;
            position: relative;
            overflow: hidden;
        }}
        
        .slide {{
            position: absolute;
            inset: 0;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 40px;
            padding: 60px 80px;
            opacity: 0;
            transform: translateX(50px);
            transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
            pointer-events: none;
        }}
        
        .slide.active {{
            opacity: 1;
            transform: translateX(0);
            pointer-events: auto;
        }}
        
        .slide.exit {{
            opacity: 0;
            transform: translateX(-50px);
        }}
        
        /* Content Area */
        .slide-content-area {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding-right: 40px;
        }}
        
        /* Title Slide */
        .title-slide .title-content {{
            text-align: left;
        }}
        
        .main-title {{
            font-size: 3.5rem;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1.2;
            margin-bottom: 20px;
        }}
        
        .subtitle {{
            font-size: 1.3rem;
            color: var(--text-secondary);
            font-weight: 400;
        }}
        
        /* Section Title */
        .section-title {{
            font-size: 2.2rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 40px;
            position: relative;
        }}
        
        .section-title::after {{
            content: '';
            position: absolute;
            bottom: -12px;
            left: 0;
            width: 60px;
            height: 4px;
            background: var(--accent);
            border-radius: 2px;
        }}
        
        /* Points */
        .points-container {{
            display: flex;
            flex-direction: column;
            gap: 24px;
        }}
        
        .point-item {{
            display: flex;
            align-items: flex-start;
            gap: 16px;
            animation: fadeInUp 0.5s ease forwards;
            opacity: 0;
        }}
        
        .slide.active .point-item:nth-child(1) {{ animation-delay: 0.2s; }}
        .slide.active .point-item:nth-child(2) {{ animation-delay: 0.4s; }}
        .slide.active .point-item:nth-child(3) {{ animation-delay: 0.6s; }}
        .slide.active .point-item:nth-child(4) {{ animation-delay: 0.8s; }}
        
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .point-icon {{
            flex-shrink: 0;
            width: 28px;
            height: 28px;
            background: var(--accent-light);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--accent);
        }}
        
        .point-icon svg {{
            width: 16px;
            height: 16px;
        }}
        
        .point-text {{
            font-size: 1.15rem;
            line-height: 1.6;
            color: var(--text-primary);
        }}
        
        /* Stats */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 30px;
        }}
        
        .stat-card {{
            background: var(--bg-secondary);
            padding: 30px;
            border-radius: 16px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
            animation: scaleIn 0.5s ease forwards;
            opacity: 0;
            transform: scale(0.9);
        }}
        
        .slide.active .stat-card:nth-child(1) {{ animation-delay: 0.2s; }}
        .slide.active .stat-card:nth-child(2) {{ animation-delay: 0.4s; }}
        .slide.active .stat-card:nth-child(3) {{ animation-delay: 0.6s; }}
        
        @keyframes scaleIn {{
            to {{ opacity: 1; transform: scale(1); }}
        }}
        
        .stat-number {{
            font-size: 3rem;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 8px;
        }}
        
        .stat-label {{
            font-size: 1rem;
            color: var(--text-secondary);
        }}
        
        /* Illustration Area */
        .illustration-area {{
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--bg-secondary);
            border-radius: 24px;
            padding: 40px;
            box-shadow: 0 4px 30px rgba(0,0,0,0.08);
        }}
        
        .main-illustration {{
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
            animation: illustrationIn 0.8s ease forwards;
        }}
        
        @keyframes illustrationIn {{
            from {{ opacity: 0; transform: scale(0.95); }}
            to {{ opacity: 1; transform: scale(1); }}
        }}
        
        /* Control Bar */
        .control-bar {{
            height: 80px;
            background: var(--bg-secondary);
            display: flex;
            align-items: center;
            padding: 0 40px;
            gap: 24px;
            border-top: 1px solid #e2e8f0;
        }}
        
        .play-btn {{
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: var(--accent);
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(14, 165, 233, 0.4);
        }}
        
        .play-btn:hover {{
            transform: scale(1.05);
            box-shadow: 0 6px 20px rgba(14, 165, 233, 0.5);
        }}
        
        .play-btn svg {{
            width: 24px;
            height: 24px;
            fill: white;
        }}
        
        .title-info {{
            flex: 0 0 auto;
        }}
        
        .title-info h3 {{
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-primary);
        }}
        
        .title-info p {{
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}
        
        /* Progress */
        .progress-container {{
            flex: 1;
            display: flex;
            align-items: center;
            gap: 16px;
        }}
        
        .progress-bar {{
            flex: 1;
            height: 6px;
            background: #e2e8f0;
            border-radius: 3px;
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--accent), var(--success));
            border-radius: 3px;
            width: 0%;
            transition: width 0.1s linear;
        }}
        
        .time-display {{
            font-size: 0.9rem;
            color: var(--text-secondary);
            font-variant-numeric: tabular-nums;
            min-width: 50px;
        }}
        
        /* Slide Counter */
        .slide-counter {{
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}
        
        .slide-counter .current {{
            color: var(--accent);
            font-weight: 600;
        }}
        
        /* Volume */
        .volume-control {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .volume-btn {{
            background: none;
            border: none;
            cursor: pointer;
            padding: 8px;
            color: var(--text-secondary);
            transition: color 0.3s;
        }}
        
        .volume-btn:hover {{
            color: var(--accent);
        }}
        
        .volume-btn svg {{
            width: 22px;
            height: 22px;
            fill: currentColor;
        }}
        
        .volume-slider {{
            width: 80px;
            height: 4px;
            -webkit-appearance: none;
            background: #e2e8f0;
            border-radius: 2px;
            cursor: pointer;
        }}
        
        .volume-slider::-webkit-slider-thumb {{
            -webkit-appearance: none;
            width: 14px;
            height: 14px;
            background: var(--accent);
            border-radius: 50%;
            cursor: pointer;
            transition: transform 0.2s;
        }}
        
        .volume-slider::-webkit-slider-thumb:hover {{
            transform: scale(1.2);
        }}
        
        /* Fullscreen */
        .fullscreen-btn {{
            background: none;
            border: none;
            cursor: pointer;
            padding: 8px;
            color: var(--text-secondary);
            transition: color 0.3s;
        }}
        
        .fullscreen-btn:hover {{
            color: var(--accent);
        }}
        
        .fullscreen-btn svg {{
            width: 22px;
            height: 22px;
            fill: currentColor;
        }}
        
        /* Loading */
        .loading-overlay {{
            position: fixed;
            inset: 0;
            background: var(--bg-primary);
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
            width: 50px;
            height: 50px;
            border: 3px solid #e2e8f0;
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        .loading-text {{
            margin-top: 20px;
            color: var(--text-secondary);
        }}
        
        /* Responsive */
        @media (max-width: 1024px) {{
            .slide {{
                grid-template-columns: 1fr;
                padding: 40px;
            }}
            
            .illustration-area {{
                display: none;
            }}
            
            .main-title {{
                font-size: 2.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="loading-overlay" id="loadingOverlay">
        <div class="loading-spinner"></div>
        <p class="loading-text">Loading presentation...</p>
    </div>
    
    <div class="presentation-container">
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
            
            <div class="slide-counter">
                <span class="current" id="currentSlide">1</span>
                <span>/</span>
                <span id="totalSlides">{total_slides}</span>
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
        const currentSlideEl = document.getElementById('currentSlide');
        const volumeSlider = document.getElementById('volumeSlider');
        const fullscreenBtn = document.getElementById('fullscreenBtn');
        const loadingOverlay = document.getElementById('loadingOverlay');
        
        const slides = document.querySelectorAll('.slide');
        const totalSlides = slides.length;
        let currentSlide = 0;
        let previousSlide = 0;
        
        function formatTime(seconds) {{
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${{mins}}:${{secs.toString().padStart(2, '0')}}`;
        }}
        
        function showSlide(index) {{
            if (index === currentSlide) return;
            
            previousSlide = currentSlide;
            currentSlide = index;
            
            slides.forEach((s, i) => {{
                s.classList.remove('active', 'exit');
                if (i === currentSlide) {{
                    s.classList.add('active');
                }} else if (i === previousSlide) {{
                    s.classList.add('exit');
                }}
            }});
            
            currentSlideEl.textContent = currentSlide + 1;
        }}
        
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
        
        function togglePlay() {{
            if (audio.paused) {{
                audio.play();
            }} else {{
                audio.pause();
            }}
        }}
        
        // Events
        audio.addEventListener('loadedmetadata', () => {{
            totalTimeEl.textContent = formatTime(audio.duration);
            loadingOverlay.classList.add('hidden');
            slides[0].classList.add('active');
        }});
        
        audio.addEventListener('timeupdate', () => {{
            const progress = (audio.currentTime / audio.duration) * 100;
            progressFill.style.width = `${{progress}}%`;
            currentTimeEl.textContent = formatTime(audio.currentTime);
            updateSlideFromTime();
        }});
        
        audio.addEventListener('play', () => {{
            playIcon.style.display = 'none';
            pauseIcon.style.display = 'block';
        }});
        
        audio.addEventListener('pause', () => {{
            playIcon.style.display = 'block';
            pauseIcon.style.display = 'none';
        }});
        
        playBtn.addEventListener('click', togglePlay);
        
        progressBar.addEventListener('click', (e) => {{
            const rect = progressBar.getBoundingClientRect();
            const pos = (e.clientX - rect.left) / rect.width;
            audio.currentTime = pos * audio.duration;
        }});
        
        volumeSlider.addEventListener('input', (e) => {{
            audio.volume = e.target.value;
        }});
        
        fullscreenBtn.addEventListener('click', () => {{
            if (!document.fullscreenElement) {{
                document.documentElement.requestFullscreen();
            }} else {{
                document.exitFullscreen();
            }}
        }});
        
        document.addEventListener('keydown', (e) => {{
            if (e.code === 'Space') {{ e.preventDefault(); togglePlay(); }}
            else if (e.code === 'ArrowRight') {{ audio.currentTime = Math.min(audio.currentTime + 5, audio.duration); }}
            else if (e.code === 'ArrowLeft') {{ audio.currentTime = Math.max(audio.currentTime - 5, 0); }}
            else if (e.code === 'KeyF') {{ fullscreenBtn.click(); }}
        }});
        
        // Initialize
        showSlide(0);
    </script>
</body>
</html>'''
    
    return html


async def create_notebooklm_presentation(module_id: str, db) -> Dict:
    """Create NotebookLM-style presentation"""
    
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
    
    print(f"Creating NotebookLM presentation: {module_title}")
    
    slides = parse_script_to_notebooklm_slides(script_text, module_title)
    html = generate_notebooklm_html(slides, module_id, module_title, course_name)
    
    html_path = PRESENTATIONS_DIR / f"{module_id}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    return {
        "success": True,
        "module_id": module_id,
        "title": module_title,
        "slides": len(slides)
    }


if __name__ == "__main__":
    async def main():
        client = MongoClient('mongodb://localhost:27017')
        db = client['test_database']
        
        for module_id in ["UG_DENT_Y1_S1_C01_M01", "UG_DENT_Y1_S1_C01_M02", "UG_DENT_Y1_S1_C01_M03"]:
            result = await create_notebooklm_presentation(module_id, db)
            print(f"  ✓ {result.get('title')} - {result.get('slides')} slides")
    
    asyncio.run(main())
