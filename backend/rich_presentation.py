"""
Rich Visual Presentation Generator
Creates presentations with multiple images integrated into content
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

# All generated illustrations
IMAGES = {
    # Cell Biology
    "cell_structure": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/8b3b9bc2921652d9a7d382da47f411eebdb611ef0920044f3dfe36f735e43e93.png",
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
    
    # Icons
    "icons": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/bc48f99a753b5699d104fe3caf5452877c8ce777c116a3ec53921f4d7c81715f.png",
    
    # DENTAL - Endodontics & Restorative
    "tooth_anatomy": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/de71f85ab3c53fb5fb0f037d7453bf194df5deb55fba729e8dc993eb6e7f3a77.png",
    "dental_instruments": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/e73e57fdd4609ae5ea1f8a33bac8bece1e825a888e8051cc738b3c5f466d95a7.png",
    "dental_restoration": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/91cb5fe80e7dc8ee4133cc77965249a28ce2dcaf407423c6ca1b2dd7008db76f.png",
    "root_canal": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/f49ac82dc9f54808b7c78b9749cd3f11790fdc8a7b561db105271f3a11361fce.png",
    "dental_xray": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/315479269c6bb29c3f481606593e121c4fc56736335527081d6699bc869d5996.png",
    "pulp_infection": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/16d68af7809ae10728ce9a12dda84359ab21d47bd2ee390673f3657650f9fc2e.png",
    "rubber_dam": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/9abba951790d8002ddd4c7f3df41b8dfe6efd5e7e4e301cc8daf2080bb09dc5d.png",
    "dental_crown": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/f58663c013b25905529c6d5b5d81747bd51d6327f9d93f890e905bcbee3ff39a.png",
}


def get_module_images(module_title: str) -> List[str]:
    """Get all relevant images for a module"""
    title_lower = module_title.lower()
    
    # Dental - Endodontics (Root Canal)
    if any(word in title_lower for word in ["endodon", "root canal", "pulp"]):
        return [
            IMAGES["root_canal"],
            IMAGES["tooth_anatomy"],
            IMAGES["pulp_infection"],
            IMAGES["dental_xray"],
            IMAGES["rubber_dam"],
            IMAGES["dental_instruments"],
        ]
    
    # Dental - Restorative
    if any(word in title_lower for word in ["restor", "operative", "filling", "composite"]):
        return [
            IMAGES["dental_restoration"],
            IMAGES["tooth_anatomy"],
            IMAGES["dental_instruments"],
            IMAGES["dental_crown"],
            IMAGES["rubber_dam"],
            IMAGES["dental_xray"],
        ]
    
    # Dental - General
    if any(word in title_lower for word in ["dent", "tooth", "oral"]):
        return [
            IMAGES["tooth_anatomy"],
            IMAGES["dental_instruments"],
            IMAGES["dental_restoration"],
            IMAGES["dental_crown"],
            IMAGES["dental_xray"],
            IMAGES["root_canal"],
        ]
    
    # Cell Biology
    if "cell" in title_lower:
        return [
            IMAGES["microscope"],
            IMAGES["cell_structure"],
            IMAGES["mitochondria"],
            IMAGES["nucleus"],
            IMAGES["cell_membrane"],
            IMAGES["cell_comparison"],
        ]
    
    # Genetics
    elif "genetic" in title_lower:
        return [
            IMAGES["dna"],
            IMAGES["dna_replication"],
            IMAGES["gene_expression"],
            IMAGES["nucleus"],
            IMAGES["cell_structure"],
        ]
    
    # Evolution
    elif "evolution" in title_lower:
        return [
            IMAGES["evolution_tree"],
            IMAGES["natural_selection"],
            IMAGES["dna"],
            IMAGES["cell_comparison"],
        ]
    
    # Default
    else:
        return list(IMAGES.values())[:6]


def parse_script_to_rich_slides(script_text: str, module_title: str) -> List[Dict]:
    """Parse script into slides with multiple images"""
    slides = []
    images = get_module_images(module_title)
    
    # Title slide with hero images
    slides.append({
        "type": "title",
        "title": module_title,
        "images": images[:3]  # 3 images for title
    })
    
    # Parse content
    lines = script_text.strip().split('\n')
    current_section = None
    current_content = []
    image_index = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('#') or (line.startswith('[') and line.endswith(']')):
            # Save previous section
            if current_section and current_content:
                # Assign 2 images per content slide
                slide_images = [
                    images[image_index % len(images)],
                    images[(image_index + 1) % len(images)]
                ]
                image_index += 2
                
                slides.append({
                    "type": "content",
                    "title": current_section,
                    "points": current_content[:4],
                    "images": slide_images
                })
            
            # Start new section
            if line.startswith('#'):
                current_section = line.replace('#', '').strip()
            else:
                current_section = line[1:-1].replace('_', ' ').title()
            current_content = []
            
        elif line.startswith('-'):
            current_content.append(line[1:].strip())
        else:
            if len(line) > 20:
                current_content.append(line[:120])
    
    # Add remaining section
    if current_section and current_content:
        slide_images = [
            images[image_index % len(images)],
            images[(image_index + 1) % len(images)]
        ]
        slides.append({
            "type": "content",
            "title": current_section,
            "points": current_content[:4],
            "images": slide_images
        })
    
    # Summary slide with all key images
    slides.append({
        "type": "summary",
        "title": "Key Concepts",
        "images": images[:4]
    })
    
    return slides


def generate_rich_html(slides: List[Dict], module_id: str, module_title: str, course_name: str) -> str:
    """Generate HTML with integrated images"""
    
    slides_html = ""
    total = len(slides)
    
    for i, slide in enumerate(slides):
        if slide["type"] == "title":
            # Title slide with 3 images in a row
            images_html = ""
            for img in slide.get("images", [])[:3]:
                images_html += f'<div class="hero-image"><img src="{img}" alt=""></div>'
            
            slides_html += f'''
            <div class="slide title-slide" data-index="{i}">
                <div class="title-content">
                    <h1>{slide["title"]}</h1>
                    <p class="subtitle">{course_name}</p>
                </div>
                <div class="hero-images-row">
                    {images_html}
                </div>
            </div>
            '''
            
        elif slide["type"] == "summary":
            # Summary with image grid
            images_html = ""
            for img in slide.get("images", [])[:4]:
                images_html += f'<div class="summary-image"><img src="{img}" alt=""></div>'
            
            slides_html += f'''
            <div class="slide summary-slide" data-index="{i}">
                <h2>{slide["title"]}</h2>
                <div class="summary-grid">
                    {images_html}
                </div>
            </div>
            '''
            
        else:
            # Content slide with 2 images and points
            img1 = slide.get("images", [""])[0] if slide.get("images") else ""
            img2 = slide.get("images", ["", ""])[1] if len(slide.get("images", [])) > 1 else ""
            
            points_html = ""
            for point in slide.get("points", []):
                points_html += f'''
                <div class="point">
                    <div class="point-bullet"></div>
                    <p>{point}</p>
                </div>
                '''
            
            slides_html += f'''
            <div class="slide content-slide" data-index="{i}">
                <div class="slide-header">
                    <h2>{slide["title"]}</h2>
                </div>
                <div class="content-layout">
                    <div class="left-image">
                        <img src="{img1}" alt="">
                    </div>
                    <div class="center-content">
                        {points_html}
                    </div>
                    <div class="right-image">
                        <img src="{img2}" alt="">
                    </div>
                </div>
            </div>
            '''
    
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
            --bg: #f8fafc;
            --card: #ffffff;
            --text: #1e293b;
            --text-light: #64748b;
            --accent: #0ea5e9;
            --accent-light: #e0f2fe;
        }}
        
        body {{
            font-family: 'Inter', sans-serif;
            background: var(--bg);
            color: var(--text);
            overflow: hidden;
        }}
        
        .presentation {{
            height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        
        .slides-area {{
            flex: 1;
            position: relative;
            overflow: hidden;
        }}
        
        /* Slides */
        .slide {{
            position: absolute;
            inset: 0;
            padding: 40px 60px;
            opacity: 0;
            transform: translateX(100px);
            transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            pointer-events: none;
            display: flex;
            flex-direction: column;
        }}
        
        .slide.active {{
            opacity: 1;
            transform: translateX(0);
            pointer-events: auto;
        }}
        
        /* Title Slide */
        .title-slide {{
            justify-content: center;
            align-items: center;
            text-align: center;
        }}
        
        .title-content {{
            margin-bottom: 50px;
        }}
        
        .title-slide h1 {{
            font-size: 3.5rem;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 15px;
        }}
        
        .subtitle {{
            font-size: 1.3rem;
            color: var(--text-light);
        }}
        
        .hero-images-row {{
            display: flex;
            gap: 30px;
            justify-content: center;
            max-width: 1200px;
        }}
        
        .hero-image {{
            flex: 1;
            max-width: 350px;
            background: var(--card);
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.08);
            animation: floatUp 0.6s ease forwards;
            opacity: 0;
        }}
        
        .hero-image:nth-child(1) {{ animation-delay: 0.2s; }}
        .hero-image:nth-child(2) {{ animation-delay: 0.4s; }}
        .hero-image:nth-child(3) {{ animation-delay: 0.6s; }}
        
        @keyframes floatUp {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .hero-image img {{
            width: 100%;
            height: auto;
            border-radius: 12px;
        }}
        
        /* Content Slide */
        .content-slide {{
            padding: 30px 40px;
        }}
        
        .slide-header {{
            margin-bottom: 30px;
        }}
        
        .slide-header h2 {{
            font-size: 2rem;
            font-weight: 600;
            color: var(--text);
            position: relative;
            display: inline-block;
        }}
        
        .slide-header h2::after {{
            content: '';
            position: absolute;
            bottom: -8px;
            left: 0;
            width: 60px;
            height: 4px;
            background: var(--accent);
            border-radius: 2px;
        }}
        
        .content-layout {{
            display: grid;
            grid-template-columns: 280px 1fr 280px;
            gap: 40px;
            flex: 1;
            align-items: center;
        }}
        
        .left-image, .right-image {{
            background: var(--card);
            border-radius: 20px;
            padding: 15px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.06);
            animation: slideIn 0.5s ease forwards;
            opacity: 0;
        }}
        
        .left-image {{ animation-delay: 0.2s; }}
        .right-image {{ animation-delay: 0.4s; }}
        
        @keyframes slideIn {{
            from {{ opacity: 0; transform: scale(0.9); }}
            to {{ opacity: 1; transform: scale(1); }}
        }}
        
        .left-image img, .right-image img {{
            width: 100%;
            height: auto;
            border-radius: 12px;
        }}
        
        .center-content {{
            display: flex;
            flex-direction: column;
            gap: 20px;
            padding: 20px 0;
        }}
        
        .point {{
            display: flex;
            align-items: flex-start;
            gap: 16px;
            padding: 20px 25px;
            background: var(--card);
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.04);
            animation: fadeInPoint 0.4s ease forwards;
            opacity: 0;
            border-left: 4px solid var(--accent);
        }}
        
        .slide.active .point:nth-child(1) {{ animation-delay: 0.3s; }}
        .slide.active .point:nth-child(2) {{ animation-delay: 0.5s; }}
        .slide.active .point:nth-child(3) {{ animation-delay: 0.7s; }}
        .slide.active .point:nth-child(4) {{ animation-delay: 0.9s; }}
        
        @keyframes fadeInPoint {{
            from {{ opacity: 0; transform: translateX(-20px); }}
            to {{ opacity: 1; transform: translateX(0); }}
        }}
        
        .point-bullet {{
            flex-shrink: 0;
            width: 10px;
            height: 10px;
            margin-top: 6px;
            background: var(--accent);
            border-radius: 50%;
        }}
        
        .point p {{
            font-size: 1.05rem;
            line-height: 1.6;
            color: var(--text);
        }}
        
        /* Summary Slide */
        .summary-slide {{
            justify-content: center;
            align-items: center;
        }}
        
        .summary-slide h2 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 50px;
            color: var(--text);
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 30px;
            max-width: 900px;
        }}
        
        .summary-image {{
            background: var(--card);
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.08);
            animation: zoomIn 0.5s ease forwards;
            opacity: 0;
        }}
        
        .summary-image:nth-child(1) {{ animation-delay: 0.1s; }}
        .summary-image:nth-child(2) {{ animation-delay: 0.2s; }}
        .summary-image:nth-child(3) {{ animation-delay: 0.3s; }}
        .summary-image:nth-child(4) {{ animation-delay: 0.4s; }}
        
        @keyframes zoomIn {{
            from {{ opacity: 0; transform: scale(0.8); }}
            to {{ opacity: 1; transform: scale(1); }}
        }}
        
        .summary-image img {{
            width: 100%;
            height: auto;
            border-radius: 12px;
        }}
        
        /* Control Bar */
        .control-bar {{
            height: 70px;
            background: var(--card);
            display: flex;
            align-items: center;
            padding: 0 30px;
            gap: 20px;
            border-top: 1px solid #e2e8f0;
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
            box-shadow: 0 4px 15px rgba(14, 165, 233, 0.3);
        }}
        
        .play-btn:hover {{
            transform: scale(1.05);
        }}
        
        .play-btn svg {{
            width: 22px;
            height: 22px;
            fill: white;
        }}
        
        .info {{
            min-width: 200px;
        }}
        
        .info h3 {{
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--text);
        }}
        
        .info p {{
            font-size: 0.8rem;
            color: var(--text-light);
        }}
        
        .progress-area {{
            flex: 1;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .time {{
            font-size: 0.85rem;
            color: var(--text-light);
            font-variant-numeric: tabular-nums;
        }}
        
        .progress-bar {{
            flex: 1;
            height: 6px;
            background: #e2e8f0;
            border-radius: 3px;
            cursor: pointer;
            overflow: hidden;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--accent), #10b981);
            width: 0%;
            transition: width 0.1s;
        }}
        
        .slide-num {{
            font-size: 0.9rem;
            color: var(--text-light);
        }}
        
        .slide-num .current {{
            color: var(--accent);
            font-weight: 600;
        }}
        
        .volume-area {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .vol-btn {{
            background: none;
            border: none;
            cursor: pointer;
            color: var(--text-light);
        }}
        
        .vol-btn svg {{
            width: 20px;
            height: 20px;
            fill: currentColor;
        }}
        
        .vol-slider {{
            width: 70px;
            height: 4px;
            -webkit-appearance: none;
            background: #e2e8f0;
            border-radius: 2px;
        }}
        
        .vol-slider::-webkit-slider-thumb {{
            -webkit-appearance: none;
            width: 12px;
            height: 12px;
            background: var(--accent);
            border-radius: 50%;
        }}
        
        .fs-btn {{
            background: none;
            border: none;
            cursor: pointer;
            color: var(--text-light);
            padding: 5px;
        }}
        
        .fs-btn svg {{
            width: 20px;
            height: 20px;
            fill: currentColor;
        }}
        
        /* Loading */
        .loading {{
            position: fixed;
            inset: 0;
            background: var(--bg);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 100;
            transition: opacity 0.4s;
        }}
        
        .loading.hidden {{
            opacity: 0;
            pointer-events: none;
        }}
        
        .spinner {{
            width: 40px;
            height: 40px;
            border: 3px solid #e2e8f0;
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        @media (max-width: 1200px) {{
            .content-layout {{
                grid-template-columns: 1fr;
            }}
            .left-image, .right-image {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="loading" id="loading">
        <div class="spinner"></div>
    </div>
    
    <div class="presentation">
        <div class="slides-area">
            {slides_html}
        </div>
        
        <div class="control-bar">
            <button class="play-btn" id="playBtn">
                <svg id="playIcon" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                <svg id="pauseIcon" style="display:none" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
            </button>
            
            <div class="info">
                <h3>{module_title}</h3>
                <p>{course_name}</p>
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
            
            <div class="volume-area">
                <button class="vol-btn">
                    <svg viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/></svg>
                </button>
                <input type="range" class="vol-slider" id="volSlider" min="0" max="1" step="0.1" value="1">
            </div>
            
            <button class="fs-btn" id="fsBtn">
                <svg viewBox="0 0 24 24"><path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/></svg>
            </button>
        </div>
    </div>
    
    <audio id="audio" preload="auto">
        <source src="/api/audio/{module_id}.mp3" type="audio/mpeg">
    </audio>
    
    <script>
        const audio = document.getElementById('audio');
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
        const loading = document.getElementById('loading');
        
        const slides = document.querySelectorAll('.slide');
        const total = slides.length;
        let current = 0;
        
        function fmt(s) {{
            return `${{Math.floor(s/60)}}:${{String(Math.floor(s%60)).padStart(2,'0')}}`;
        }}
        
        function show(idx) {{
            slides.forEach((s,i) => s.classList.toggle('active', i === idx));
            current = idx;
            slideNumEl.textContent = idx + 1;
        }}
        
        function updateFromTime() {{
            if (!audio.duration) return;
            const idx = Math.min(Math.floor((audio.currentTime / audio.duration) * total), total - 1);
            if (idx !== current) show(idx);
        }}
        
        audio.addEventListener('loadedmetadata', () => {{
            totalTimeEl.textContent = fmt(audio.duration);
            loading.classList.add('hidden');
            show(0);
        }});
        
        audio.addEventListener('timeupdate', () => {{
            progressFill.style.width = `${{(audio.currentTime / audio.duration) * 100}}%`;
            currentTimeEl.textContent = fmt(audio.currentTime);
            updateFromTime();
        }});
        
        audio.addEventListener('play', () => {{
            playIcon.style.display = 'none';
            pauseIcon.style.display = 'block';
        }});
        
        audio.addEventListener('pause', () => {{
            playIcon.style.display = 'block';
            pauseIcon.style.display = 'none';
        }});
        
        playBtn.onclick = () => audio.paused ? audio.play() : audio.pause();
        
        progressBar.onclick = (e) => {{
            const rect = progressBar.getBoundingClientRect();
            audio.currentTime = ((e.clientX - rect.left) / rect.width) * audio.duration;
        }};
        
        volSlider.oninput = (e) => audio.volume = e.target.value;
        
        fsBtn.onclick = () => {{
            if (!document.fullscreenElement) document.documentElement.requestFullscreen();
            else document.exitFullscreen();
        }};
        
        document.onkeydown = (e) => {{
            if (e.code === 'Space') {{ e.preventDefault(); playBtn.click(); }}
            if (e.code === 'ArrowRight') audio.currentTime += 5;
            if (e.code === 'ArrowLeft') audio.currentTime -= 5;
            if (e.code === 'KeyF') fsBtn.click();
        }};
        
        show(0);
    </script>
</body>
</html>'''
    
    return html


async def create_rich_presentation(module_id: str, db) -> Dict:
    """Create presentation with integrated images"""
    
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
    
    print(f"Creating: {module_title}")
    
    slides = parse_script_to_rich_slides(script_text, module_title)
    html = generate_rich_html(slides, module_id, module_title, course_name)
    
    path = PRESENTATIONS_DIR / f"{module_id}.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    
    return {"success": True, "title": module_title, "slides": len(slides)}


if __name__ == "__main__":
    async def main():
        client = MongoClient('mongodb://localhost:27017')
        db = client['test_database']
        
        for mid in ["UG_DENT_Y1_S1_C01_M01", "UG_DENT_Y1_S1_C01_M02", "UG_DENT_Y1_S1_C01_M03"]:
            r = await create_rich_presentation(mid, db)
            print(f"  ✓ {r.get('title')} - {r.get('slides')} slides")
    
    asyncio.run(main())
