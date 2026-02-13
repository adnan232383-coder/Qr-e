"""
Avatar 50/50 Presentation Generator
Creates presentations with avatar on one side and slides on the other side
"""

import os
import asyncio
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

PRESENTATIONS_DIR = Path("/app/backend/presentations")
AUDIO_DIR = Path("/app/backend/audio")
VIDEOS_DIR = Path("/app/backend/heygen_videos")
IMAGES_DIR = Path("/app/backend/images")

HEYGEN_API_KEY = os.environ.get("HEYGEN_API_KEY")
HEYGEN_BASE_URL = "https://api.heygen.com"

# Approved avatar configuration
AVATAR_CONFIG = {
    "avatar_id": "Adriana_Nurse_Front_public",
    "avatar_name": "Adriana",
    "voice_id": "42d00d4aac5441279d8536cd6b52c53c",
    "voice_name": "Hope"
}

# Image collections by topic
IMAGE_COLLECTIONS = {
    "dental": {
        "root_canal": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/f49ac82dc9f54808b7c78b9749cd3f11790fdc8a7b561db105271f3a11361fce.png",
        "tooth_anatomy": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/de71f85ab3c53fb5fb0f037d7453bf194df5deb55fba729e8dc993eb6e7f3a77.png",
        "pulp_infection": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/16d68af7809ae10728ce9a12dda84359ab21d47bd2ee390673f3657650f9fc2e.png",
        "dental_xray": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/315479269c6bb29c3f481606593e121c4fc56736335527081d6699bc869d5996.png",
        "rubber_dam": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/9abba951790d8002ddd4c7f3df41b8dfe6efd5e7e4e301cc8daf2080bb09dc5d.png",
        "instruments": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/e73e57fdd4609ae5ea1f8a33bac8bece1e825a888e8051cc738b3c5f466d95a7.png",
        "restoration": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/91cb5fe80e7dc8ee4133cc77965249a28ce2dcaf407423c6ca1b2dd7008db76f.png",
        "crown": "https://static.prod-images.emergentagent.com/jobs/b0c52883-64de-42c1-88b8-e8437b2fa4c0/images/f58663c013b25905529c6d5b5d81747bd51d6327f9d93f890e905bcbee3ff39a.png",
    },
    "biology": {
        "cell": "https://images.unsplash.com/photo-1530026405186-ed1f139313f8?w=600",
        "dna": "https://images.unsplash.com/photo-1628595351029-c2bf17511435?w=600",
        "microscope": "https://images.unsplash.com/photo-1576086213369-97a306d36557?w=600",
    }
}


class HeyGenAvatarGenerator:
    """Generate avatar videos from audio files using HeyGen API"""
    
    def __init__(self):
        self.api_key = HEYGEN_API_KEY
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Api-Key": self.api_key
        }
    
    def upload_audio(self, audio_path: str) -> Optional[str]:
        """Upload audio file to HeyGen and return asset ID"""
        try:
            with open(audio_path, 'rb') as f:
                files = {"file": (Path(audio_path).name, f, "audio/mpeg")}
                response = requests.post(
                    f"{HEYGEN_BASE_URL}/v1/asset/upload",
                    headers={"X-Api-Key": self.api_key, "Accept": "application/json"},
                    files=files
                )
            
            if response.status_code == 200:
                data = response.json()
                asset_id = data.get("data", {}).get("asset_id")
                print(f"Audio uploaded, asset_id: {asset_id}")
                return asset_id
            else:
                print(f"Upload failed: {response.text}")
                return None
        except Exception as e:
            print(f"Upload error: {e}")
            return None
    
    def generate_avatar_video(self, audio_asset_id: str, title: str = "Lecture") -> Optional[str]:
        """Generate avatar video from audio asset with dark background"""
        payload = {
            "video_inputs": [{
                "character": {
                    "type": "avatar",
                    "avatar_id": AVATAR_CONFIG["avatar_id"],
                    "avatar_style": "normal"
                },
                "voice": {
                    "type": "audio",
                    "audio_asset_id": audio_asset_id
                },
                "background": {
                    "type": "color",
                    "value": "#0f172a"  # Dark blue matching presentation
                }
            }],
            "dimension": {"width": 720, "height": 1280},  # Portrait for side panel
            "test": False,
            "title": title
        }
        
        try:
            response = requests.post(
                f"{HEYGEN_BASE_URL}/v2/video/generate",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                video_id = data.get("data", {}).get("video_id")
                print(f"Video generation started, video_id: {video_id}")
                return video_id
            else:
                print(f"Generation failed: {response.text}")
                return None
        except Exception as e:
            print(f"Generation error: {e}")
            return None
    
    def check_status(self, video_id: str) -> Dict:
        """Check video generation status"""
        try:
            response = requests.get(
                f"{HEYGEN_BASE_URL}/v1/video_status.get",
                headers=self.headers,
                params={"video_id": video_id}
            )
            
            if response.status_code == 200:
                data = response.json().get("data", {})
                return {
                    "status": data.get("status"),
                    "video_url": data.get("video_url"),
                    "duration": data.get("duration"),
                    "error": data.get("error")
                }
            return {"status": "error", "error": response.text}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def wait_for_video(self, video_id: str, max_wait: int = 600) -> Optional[str]:
        """Wait for video to complete and return URL"""
        start = time.time()
        while time.time() - start < max_wait:
            status = self.check_status(video_id)
            print(f"Status: {status.get('status')}...")
            
            if status.get("status") == "completed":
                return status.get("video_url")
            elif status.get("status") == "failed":
                print(f"Failed: {status.get('error')}")
                return None
            
            time.sleep(10)
        
        print("Timeout waiting for video")
        return None
    
    def download_video(self, url: str, output_path: str) -> bool:
        """Download video to local path"""
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"Downloaded to: {output_path}")
                return True
            return False
        except Exception as e:
            print(f"Download error: {e}")
            return False


def parse_script_to_slides(script_text: str, title: str, topic: str = "dental") -> List[Dict]:
    """Parse script into slides with relevant images"""
    slides = []
    images = list(IMAGE_COLLECTIONS.get(topic, IMAGE_COLLECTIONS["dental"]).values())
    
    # Title slide
    slides.append({
        "type": "title",
        "title": title,
        "image": images[0] if images else None
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
        
        # Check for section headers
        if line.startswith('#') or (line.startswith('[') and line.endswith(']')):
            # Save previous section
            if current_section and current_points:
                slides.append({
                    "type": "content",
                    "title": current_section,
                    "points": current_points[:4],
                    "image": images[img_idx % len(images)] if images else None
                })
                img_idx += 1
            
            # Start new section
            if line.startswith('#'):
                current_section = line.replace('#', '').strip()
            else:
                current_section = line[1:-1].replace('_', ' ').title()
            current_points = []
        
        elif line.startswith('-'):
            current_points.append(line[1:].strip())
        elif len(line) > 20:
            current_points.append(line[:120])
    
    # Save last section
    if current_section and current_points:
        slides.append({
            "type": "content",
            "title": current_section,
            "points": current_points[:4],
            "image": images[img_idx % len(images)] if images else None
        })
    
    return slides


def generate_subtitles_from_script(script_text: str, num_slides: int) -> List[Dict]:
    """Generate timed subtitles from script text"""
    import json
    import re
    
    if not script_text:
        return []
    
    # Split script into sentences
    sentences = re.split(r'(?<=[.!?])\s+', script_text.strip())
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
    
    if not sentences:
        return []
    
    # Estimate video duration (approximately 150 words per minute for speech)
    total_words = len(script_text.split())
    estimated_duration = (total_words / 150) * 60  # in seconds
    
    # Calculate time per sentence
    time_per_sentence = estimated_duration / len(sentences) if sentences else 0
    
    subtitles = []
    current_time = 0
    
    for sentence in sentences:
        # Break long sentences into chunks of ~15 words
        words = sentence.split()
        if len(words) > 20:
            chunks = []
            for i in range(0, len(words), 15):
                chunk = ' '.join(words[i:i+15])
                if chunk:
                    chunks.append(chunk)
        else:
            chunks = [sentence]
        
        chunk_duration = time_per_sentence / len(chunks)
        
        for chunk in chunks:
            subtitles.append({
                "start": round(current_time, 1),
                "end": round(current_time + chunk_duration, 1),
                "text": chunk
            })
            current_time += chunk_duration
    
    return subtitles


def translate_subtitles_to_hebrew(subtitles_en: List[Dict]) -> List[Dict]:
    """Create Hebrew placeholder subtitles (would need actual translation API)"""
    # For now, return placeholders - in production, use translation API
    subtitles_he = []
    
    for sub in subtitles_en:
        subtitles_he.append({
            "start": sub["start"],
            "end": sub["end"],
            "text": f"[תרגום] {sub['text'][:50]}..." if len(sub['text']) > 50 else f"[תרגום] {sub['text']}"
        })
    
    return subtitles_he


def generate_50_50_html(slides: List[Dict], module_id: str, title: str, course: str, video_path: str, script_text: str = "") -> str:
    """Generate HTML presentation with 50/50 avatar layout"""
    
    total = len(slides)
    slides_html = ""
    
    for i, slide in enumerate(slides):
        if slide["type"] == "title":
            slides_html += f'''
            <div class="slide title-slide" data-index="{i}">
                <div class="slide-inner">
                    <h1>{slide["title"]}</h1>
                    <p class="course-name">{course}</p>
                    {f'<div class="title-image"><img src="{slide["image"]}" alt=""></div>' if slide.get("image") else ''}
                </div>
            </div>
            '''
        else:
            points_html = "".join([f'<li><span class="bullet"></span>{p}</li>' for p in slide.get("points", [])])
            slides_html += f'''
            <div class="slide content-slide" data-index="{i}">
                <div class="slide-inner">
                    <h2>{slide["title"]}</h2>
                    <div class="content-grid">
                        {f'<div class="slide-image"><img src="{slide["image"]}" alt=""></div>' if slide.get("image") else ''}
                        <ul class="points">{points_html}</ul>
                    </div>
                </div>
            </div>
            '''
    
    # Generate subtitles from script
    subtitles_en = generate_subtitles_from_script(script_text, total)
    subtitles_he = translate_subtitles_to_hebrew(subtitles_en)
    
    # Get base URL for video loading from frontend .env
    import os
    from pathlib import Path
    
    base_url = ''
    frontend_env = Path('/app/frontend/.env')
    if frontend_env.exists():
        with open(frontend_env) as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    base_url = line.strip().split('=', 1)[1]
                    break
    
    # Make video path absolute if it starts with /api
    abs_video_path = video_path
    if video_path.startswith('/api') and base_url:
        abs_video_path = base_url + video_path
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <base href="{base_url}/">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        :root {{
            --bg: #0a0f1a;
            --card: #151d2e;
            --card-hover: #1a2538;
            --text: #f1f5f9;
            --text-muted: #94a3b8;
            --accent: #38bdf8;
            --accent-secondary: #a78bfa;
            --gradient: linear-gradient(135deg, #38bdf8 0%, #a78bfa 100%);
        }}
        
        body {{
            font-family: 'Inter', sans-serif;
            background: var(--bg);
            color: var(--text);
            overflow: hidden;
            height: 100vh;
        }}
        
        /* Main 50/50 Layout */
        .presentation-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: 1fr 70px;
            height: 100vh;
        }}
        
        /* Avatar Panel - Left Side */
        .avatar-panel {{
            background: linear-gradient(180deg, #0f172a 0%, #0a0f1a 100%);
            display: flex;
            flex-direction: column;
            position: relative;
            border-right: 1px solid rgba(56, 189, 248, 0.1);
        }}
        
        .avatar-header {{
            padding: 20px 30px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        
        .instructor-badge {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: rgba(56, 189, 248, 0.1);
            border: 1px solid rgba(56, 189, 248, 0.2);
            padding: 8px 16px;
            border-radius: 30px;
        }}
        
        .instructor-badge .dot {{
            width: 8px;
            height: 8px;
            background: #22c55e;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        .instructor-badge span {{
            font-size: 0.85rem;
            color: var(--accent);
            font-weight: 500;
        }}
        
        .avatar-video-wrapper {{
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 30px;
        }}
        
        .avatar-video-container {{
            width: 100%;
            max-width: 400px;
            aspect-ratio: 9/16;
            background: #000;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 
                0 0 0 1px rgba(56, 189, 248, 0.2),
                0 20px 60px rgba(0,0,0,0.5),
                0 0 100px rgba(56, 189, 248, 0.1);
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
            gap: 15px;
        }}
        
        .avatar-placeholder svg {{
            width: 80px;
            height: 80px;
            opacity: 0.5;
        }}
        
        /* Slides Panel - Right Side */
        .slides-panel {{
            background: var(--bg);
            position: relative;
            overflow: hidden;
        }}
        
        .slide {{
            position: absolute;
            inset: 0;
            padding: 40px;
            opacity: 0;
            transform: translateX(60px);
            transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
            pointer-events: none;
            display: flex;
            flex-direction: column;
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
        
        /* Title Slide */
        .title-slide .slide-inner {{
            justify-content: center;
            align-items: center;
            text-align: center;
        }}
        
        .title-slide h1 {{
            font-size: 3.5rem;
            font-weight: 800;
            background: var(--gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 20px;
            text-shadow: 0 4px 30px rgba(56, 189, 248, 0.3);
        }}
        
        .course-name {{
            font-size: 1.5rem;
            color: var(--text-muted);
            margin-bottom: 40px;
            font-weight: 600;
        }}
        
        .title-image {{
            max-width: 400px;
            background: var(--card);
            border-radius: 16px;
            padding: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }}
        
        .title-image img {{
            width: 100%;
            border-radius: 10px;
        }}
        
        /* Content Slide */
        .content-slide h2 {{
            font-size: 2.2rem;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 2px solid var(--card);
            position: relative;
        }}
        
        .content-slide h2::after {{
            content: '';
            position: absolute;
            bottom: -2px;
            left: 0;
            width: 100px;
            height: 3px;
            background: var(--gradient);
        }}
        
        .content-grid {{
            display: flex;
            flex-direction: column;
            gap: 25px;
            flex: 1;
        }}
        
        .slide-image {{
            background: var(--card);
            border-radius: 12px;
            padding: 12px;
            max-width: 320px;
        }}
        
        .slide-image img {{
            width: 100%;
            border-radius: 8px;
        }}
        
        .points {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}
        
        .points li {{
            display: flex;
            align-items: flex-start;
            gap: 15px;
            padding: 18px 22px;
            background: var(--card);
            border-radius: 12px;
            font-size: 1.2rem;
            font-weight: 500;
            line-height: 1.6;
            animation: slideIn 0.4s ease forwards;
            opacity: 0;
            border-left: 4px solid var(--accent);
        }}
        
        .points li .bullet {{
            width: 8px;
            height: 8px;
            background: var(--accent);
            border-radius: 50%;
            margin-top: 10px;
            flex-shrink: 0;
        }}
        
        .slide.active .points li:nth-child(1) {{ animation-delay: 0.1s; }}
        .slide.active .points li:nth-child(2) {{ animation-delay: 0.2s; }}
        .slide.active .points li:nth-child(3) {{ animation-delay: 0.3s; }}
        .slide.active .points li:nth-child(4) {{ animation-delay: 0.4s; }}
        
        @keyframes slideIn {{
            from {{ opacity: 0; transform: translateX(20px); }}
            to {{ opacity: 1; transform: translateX(0); }}
        }}
        
        /* Subtitles Container */
        .subtitles-container {{
            position: absolute;
            bottom: 100px;
            left: 50%;
            transform: translateX(-50%);
            width: 90%;
            max-width: 700px;
            text-align: center;
            z-index: 50;
            pointer-events: none;
        }}
        
        .subtitle-text {{
            display: inline-block;
            background: rgba(0, 0, 0, 0.85);
            color: #ffffff;
            font-size: 1.4rem;
            font-weight: 600;
            padding: 15px 30px;
            border-radius: 10px;
            line-height: 1.5;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
            max-width: 100%;
        }}
        
        .subtitle-text.hebrew {{
            direction: rtl;
            font-family: 'Heebo', 'Arial Hebrew', sans-serif;
        }}
        
        .subtitles-toggle {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(0,0,0,0.7);
            border: 1px solid rgba(255,255,255,0.2);
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 500;
            z-index: 100;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .subtitles-toggle:hover {{
            background: rgba(56, 189, 248, 0.3);
        }}
        
        .subtitles-toggle.active {{
            background: rgba(56, 189, 248, 0.5);
            border-color: var(--accent);
        }}
        
        /* Language selector */
        .lang-selector {{
            position: absolute;
            top: 70px;
            right: 20px;
            background: rgba(0,0,0,0.7);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            overflow: hidden;
            z-index: 100;
            display: none;
        }}
        
        .lang-selector.show {{
            display: block;
        }}
        
        .lang-option {{
            padding: 12px 20px;
            cursor: pointer;
            font-size: 1rem;
            color: white;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        
        .lang-option:last-child {{
            border-bottom: none;
        }}
        
        .lang-option:hover {{
            background: rgba(56, 189, 248, 0.3);
        }}
        
        .lang-option.selected {{
            background: rgba(56, 189, 248, 0.5);
        }}
        
        /* Control Bar */
        .control-bar {{
            grid-column: 1 / -1;
            background: var(--card);
            display: flex;
            align-items: center;
            padding: 0 25px;
            gap: 20px;
            border-top: 1px solid rgba(255,255,255,0.05);
        }}
        
        .play-btn {{
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: var(--gradient);
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s;
            flex-shrink: 0;
        }}
        
        .play-btn:hover {{
            transform: scale(1.08);
            box-shadow: 0 0 25px rgba(56, 189, 248, 0.4);
        }}
        
        .play-btn svg {{
            width: 20px;
            height: 20px;
            fill: white;
        }}
        
        .info {{
            min-width: 180px;
        }}
        
        .info h4 {{
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
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
            font-size: 0.8rem;
            color: var(--text-muted);
            font-variant-numeric: tabular-nums;
            min-width: 42px;
        }}
        
        .progress-bar {{
            flex: 1;
            height: 5px;
            background: rgba(255,255,255,0.1);
            border-radius: 3px;
            cursor: pointer;
            overflow: hidden;
        }}
        
        .progress-fill {{
            height: 100%;
            background: var(--gradient);
            width: 0%;
            transition: width 0.1s;
            border-radius: 3px;
        }}
        
        .slide-indicator {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 14px;
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
        }}
        
        .slide-indicator .current {{
            color: var(--accent);
            font-weight: 600;
        }}
        
        .slide-indicator span {{
            font-size: 0.85rem;
            color: var(--text-muted);
        }}
        
        .control-btn {{
            background: none;
            border: none;
            cursor: pointer;
            padding: 10px;
            color: var(--text-muted);
            transition: all 0.3s;
            border-radius: 8px;
        }}
        
        .control-btn:hover {{
            color: var(--accent);
            background: rgba(56, 189, 248, 0.1);
        }}
        
        .control-btn svg {{
            width: 20px;
            height: 20px;
            fill: currentColor;
        }}
        
        .vol-slider {{
            width: 80px;
            height: 4px;
            -webkit-appearance: none;
            background: rgba(255,255,255,0.15);
            border-radius: 2px;
        }}
        
        .vol-slider::-webkit-slider-thumb {{
            -webkit-appearance: none;
            width: 14px;
            height: 14px;
            background: var(--accent);
            border-radius: 50%;
            cursor: pointer;
        }}
        
        /* Responsive */
        @media (max-width: 1200px) {{
            .presentation-container {{
                grid-template-columns: 45% 55%;
            }}
        }}
        
        @media (max-width: 900px) {{
            .presentation-container {{
                grid-template-columns: 1fr;
                grid-template-rows: 250px 1fr 70px;
            }}
            
            .avatar-panel {{
                border-right: none;
                border-bottom: 1px solid rgba(56, 189, 248, 0.1);
            }}
            
            .avatar-video-wrapper {{
                padding: 15px;
            }}
            
            .avatar-video-container {{
                max-width: 200px;
            }}
            
            .subtitle-text {{
                font-size: 1.1rem;
                padding: 10px 20px;
            }}
        }}
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <div class="presentation-container">
        <!-- Subtitles Toggle Button -->
        <button class="subtitles-toggle" id="subtitlesToggle" data-testid="subtitles-toggle">
            <span>CC</span> כתוביות
        </button>
        
        <!-- Language Selector -->
        <div class="lang-selector" id="langSelector">
            <div class="lang-option selected" data-lang="en">English</div>
            <div class="lang-option" data-lang="he">עברית</div>
        </div>
        
        <!-- Subtitles Display -->
        <div class="subtitles-container" id="subtitlesContainer" style="display:none;">
            <div class="subtitle-text" id="subtitleText"></div>
        </div>
        
        <!-- Avatar Panel - Left 50% -->
        <div class="avatar-panel">
            <div class="avatar-header">
                <div class="instructor-badge">
                    <div class="dot"></div>
                    <span>Virtual Instructor - Adriana</span>
                </div>
            </div>
            <div class="avatar-video-wrapper">
                <div class="avatar-video-container">
                    <video class="avatar-video" id="avatarVideo" playsinline preload="auto" autoplay muted src="{abs_video_path}">
                        Your browser does not support the video tag.
                    </video>
                    <div class="avatar-placeholder" id="avatarPlaceholder">
                        <svg viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                        </svg>
                        <span>Loading Avatar...</span>
                    </div>
                    <div class="unmute-overlay" id="unmuteOverlay" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);background:rgba(0,0,0,0.8);padding:20px 40px;border-radius:12px;cursor:pointer;z-index:100;display:none;">
                        <span style="color:white;font-size:24px;">🔊 לחץ להפעלת קול</span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Slides Panel - Right 50% -->
        <div class="slides-panel">
            {slides_html}
        </div>
        
        <!-- Control Bar -->
        <div class="control-bar">
            <button class="play-btn" id="playBtn" data-testid="play-btn">
                <svg id="playIcon" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                <svg id="pauseIcon" style="display:none" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
            </button>
            
            <div class="info">
                <h4>{title}</h4>
                <p>{course}</p>
            </div>
            
            <div class="progress-area">
                <span class="time" id="currentTime">0:00</span>
                <div class="progress-bar" id="progressBar" data-testid="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <span class="time" id="totalTime">0:00</span>
            </div>
            
            <div class="slide-indicator">
                <span class="current" id="slideNum">1</span>
                <span>/</span>
                <span>{total}</span>
            </div>
            
            <button class="control-btn" id="volBtn" data-testid="volume-btn">
                <svg viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/></svg>
            </button>
            <input type="range" class="vol-slider" id="volSlider" min="0" max="1" step="0.1" value="1" data-testid="volume-slider">
            
            <button class="control-btn" id="fsBtn" data-testid="fullscreen-btn">
                <svg viewBox="0 0 24 24"><path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/></svg>
            </button>
        </div>
    </div>
    
    <script>
        const video = document.getElementById('avatarVideo');
        const placeholder = document.getElementById('avatarPlaceholder');
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
        
        function formatTime(s) {{
            const m = Math.floor(s / 60);
            const sec = Math.floor(s % 60);
            return m + ':' + String(sec).padStart(2, '0');
        }}
        
        function showSlide(idx) {{
            slides.forEach((s, i) => s.classList.toggle('active', i === idx));
            current = idx;
            slideNumEl.textContent = idx + 1;
        }}
        
        function updateSlideFromTime() {{
            if (!video.duration) return;
            const progress = video.currentTime / video.duration;
            const idx = Math.min(Math.floor(progress * total), total - 1);
            if (idx !== current) showSlide(idx);
        }}
        
        // Video events
        video.addEventListener('loadedmetadata', () => {{
            console.log('Video metadata loaded, duration:', video.duration);
            placeholder.style.display = 'none';
            totalTimeEl.textContent = formatTime(video.duration);
        }});
        
        video.addEventListener('canplay', () => {{
            console.log('Video can play');
            placeholder.style.display = 'none';
        }});
        
        video.addEventListener('loadstart', () => {{
            console.log('Video load started');
            placeholder.querySelector('span').textContent = 'Loading video...';
        }});
        
        video.addEventListener('progress', () => {{
            if (video.buffered.length > 0) {{
                const buffered = video.buffered.end(0);
                console.log('Video buffered:', buffered, 'seconds');
            }}
        }});
        
        video.addEventListener('error', (e) => {{
            console.error('Video error:', video.error);
            placeholder.querySelector('span').textContent = 'Click Play to start';
            document.getElementById('videoLink').style.display = 'block';
        }});
        
        video.addEventListener('stalled', () => {{
            console.log('Video stalled, retrying...');
        }});
        
        // Force video load after short delay
        setTimeout(() => {{
            if (video.readyState >= 2) {{
                placeholder.style.display = 'none';
            }} else {{
                video.load();
            }}
        }}, 1000);
        
        // Unmute overlay
        const unmuteOverlay = document.getElementById('unmuteOverlay');
        
        // AUTO-PLAY: Start video automatically when page loads
        window.addEventListener('load', () => {{
            video.muted = true;
            video.play().then(() => {{
                console.log('Auto-play started (muted)');
                placeholder.style.display = 'none';
                // Show unmute overlay
                unmuteOverlay.style.display = 'block';
            }}).catch(e => {{
                console.log('Auto-play failed:', e);
                placeholder.querySelector('span').textContent = 'לחץ להפעלה';
                placeholder.style.cursor = 'pointer';
                placeholder.onclick = () => {{
                    video.muted = false;
                    video.play();
                    placeholder.style.display = 'none';
                }};
            }});
        }});
        
        // Click anywhere on video area to unmute
        unmuteOverlay.onclick = () => {{
            video.muted = false;
            unmuteOverlay.style.display = 'none';
            console.log('Audio enabled');
        }};
        
        // Also unmute on video click
        video.onclick = () => {{
            if (video.muted) {{
                video.muted = false;
                unmuteOverlay.style.display = 'none';
            }}
        }};
        
        video.addEventListener('timeupdate', () => {{
            const progress = (video.currentTime / video.duration) * 100;
            progressFill.style.width = progress + '%';
            currentTimeEl.textContent = formatTime(video.currentTime);
            updateSlideFromTime();
        }});
        
        video.addEventListener('play', () => {{
            playIcon.style.display = 'none';
            pauseIcon.style.display = 'block';
        }});
        
        video.addEventListener('pause', () => {{
            playIcon.style.display = 'block';
            pauseIcon.style.display = 'none';
        }});
        
        video.addEventListener('ended', () => {{
            playIcon.style.display = 'block';
            pauseIcon.style.display = 'none';
        }});
        
        // Controls
        playBtn.onclick = () => {{
            if (video.paused) {{
                // Start loading and playing
                if (video.readyState < 1) {{
                    video.load();
                }}
                video.play().catch(err => {{
                    console.error('Play error:', err);
                    placeholder.querySelector('span').textContent = 'Click again to play';
                }});
            }} else {{
                video.pause();
            }}
        }};
        
        progressBar.onclick = (e) => {{
            const rect = progressBar.getBoundingClientRect();
            const pos = (e.clientX - rect.left) / rect.width;
            video.currentTime = pos * video.duration;
        }};
        
        volSlider.oninput = (e) => video.volume = e.target.value;
        
        fsBtn.onclick = () => {{
            if (!document.fullscreenElement) {{
                document.documentElement.requestFullscreen();
            }} else {{
                document.exitFullscreen();
            }}
        }};
        
        // Keyboard controls
        document.onkeydown = (e) => {{
            if (e.code === 'Space') {{
                e.preventDefault();
                playBtn.click();
            }}
            if (e.code === 'ArrowRight') video.currentTime += 5;
            if (e.code === 'ArrowLeft') video.currentTime -= 5;
            if (e.code === 'ArrowUp') {{
                e.preventDefault();
                const next = Math.min(current + 1, total - 1);
                video.currentTime = (next / total) * video.duration;
            }}
            if (e.code === 'ArrowDown') {{
                e.preventDefault();
                const prev = Math.max(current - 1, 0);
                video.currentTime = (prev / total) * video.duration;
            }}
            if (e.code === 'KeyF') fsBtn.click();
            if (e.code === 'KeyC') subtitlesToggle.click();
        }};
        
        // ===== SUBTITLES SYSTEM =====
        const subtitlesToggle = document.getElementById('subtitlesToggle');
        const langSelector = document.getElementById('langSelector');
        const subtitlesContainer = document.getElementById('subtitlesContainer');
        const subtitleText = document.getElementById('subtitleText');
        
        let subtitlesEnabled = false;
        let currentLang = 'en';
        
        // Subtitles data - synced with video timestamps
        const subtitlesData = {{
            en: {script_subtitles_en},
            he: {script_subtitles_he}
        }};
        
        // Toggle subtitles
        subtitlesToggle.onclick = () => {{
            subtitlesEnabled = !subtitlesEnabled;
            subtitlesToggle.classList.toggle('active', subtitlesEnabled);
            subtitlesContainer.style.display = subtitlesEnabled ? 'block' : 'none';
            langSelector.classList.toggle('show', subtitlesEnabled);
        }};
        
        // Language selection
        document.querySelectorAll('.lang-option').forEach(opt => {{
            opt.onclick = () => {{
                document.querySelectorAll('.lang-option').forEach(o => o.classList.remove('selected'));
                opt.classList.add('selected');
                currentLang = opt.dataset.lang;
                subtitleText.classList.toggle('hebrew', currentLang === 'he');
                updateSubtitle();
            }};
        }});
        
        // Update subtitle based on video time
        function updateSubtitle() {{
            if (!subtitlesEnabled) return;
            
            const currentTime = video.currentTime;
            const subs = subtitlesData[currentLang];
            let currentSub = '';
            
            for (let i = 0; i < subs.length; i++) {{
                if (currentTime >= subs[i].start && currentTime < subs[i].end) {{
                    currentSub = subs[i].text;
                    break;
                }}
            }}
            
            subtitleText.textContent = currentSub;
        }}
        
        // Add subtitle update to timeupdate
        video.addEventListener('timeupdate', updateSubtitle);
        
        // Initialize
        showSlide(0);
    </script>
</body>
</html>'''
    
    return html


async def create_avatar_presentation_50_50(
    module_id: str, 
    db, 
    video_url: str = None,
    generate_new_video: bool = False
) -> Dict:
    """Create 50/50 avatar presentation for a module"""
    
    # Get module data
    module = db.modules.find_one({"module_id": module_id})
    if not module:
        return {"success": False, "error": "Module not found"}
    
    # Get script
    script = db.module_scripts.find_one({"module_id": module_id})
    if not script:
        return {"success": False, "error": "No script found"}
    
    # Get course info
    course = db.courses.find_one({"external_id": module.get("courseId")})
    course_name = course.get("course_name", "Course") if course else "Course"
    
    title = module.get("title", module_id)
    script_text = script.get("script_text", "")
    
    # Determine topic for images
    topic = "dental" if "DENT" in module_id or "dent" in course_name.lower() else "biology"
    
    # Parse slides
    slides = parse_script_to_slides(script_text, title, topic)
    
    # Video path
    if video_url:
        video_path = video_url
    else:
        # Check for existing video
        local_video = VIDEOS_DIR / f"{module_id}_avatar.mp4"
        if local_video.exists():
            video_path = f"/api/avatar-videos/{module_id}"
        else:
            # Check for any existing video
            for video_file in VIDEOS_DIR.glob(f"{module_id}*.mp4"):
                video_path = f"/api/avatar-videos/{video_file.stem}"
                break
            else:
                video_path = f"/api/avatar-videos/{module_id}"  # Will show placeholder
    
    # Generate HTML
    html = generate_50_50_html(slides, module_id, title, course_name, video_path)
    
    # Save presentation
    PRESENTATIONS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PRESENTATIONS_DIR / f"{module_id}_50_50.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"Created 50/50 presentation: {output_path}")
    
    return {
        "success": True,
        "title": title,
        "slides_count": len(slides),
        "presentation_path": str(output_path),
        "video_path": video_path
    }


async def generate_avatar_video_from_audio(module_id: str, db) -> Dict:
    """Generate HeyGen avatar video from existing audio file"""
    
    # Check for existing audio
    audio_path = AUDIO_DIR / f"{module_id}.mp3"
    if not audio_path.exists():
        return {"success": False, "error": f"No audio file found: {audio_path}"}
    
    # Get module title
    module = db.modules.find_one({"module_id": module_id})
    title = module.get("title", module_id) if module else module_id
    
    generator = HeyGenAvatarGenerator()
    
    # Upload audio
    print(f"Uploading audio: {audio_path}")
    asset_id = generator.upload_audio(str(audio_path))
    if not asset_id:
        return {"success": False, "error": "Failed to upload audio"}
    
    # Generate video
    print("Generating avatar video...")
    video_id = generator.generate_avatar_video(asset_id, title)
    if not video_id:
        return {"success": False, "error": "Failed to start video generation"}
    
    # Wait for completion
    print(f"Waiting for video (ID: {video_id})...")
    video_url = generator.wait_for_video(video_id, max_wait=600)
    if not video_url:
        return {"success": False, "error": "Video generation failed or timed out", "video_id": video_id}
    
    # Download video
    output_path = VIDEOS_DIR / f"{module_id}_avatar.mp4"
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    
    if generator.download_video(video_url, str(output_path)):
        return {
            "success": True,
            "video_id": video_id,
            "video_url": video_url,
            "local_path": str(output_path)
        }
    
    return {"success": False, "error": "Failed to download video", "video_url": video_url}


if __name__ == "__main__":
    # Test with existing module
    async def main():
        client = MongoClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
        db = client[os.environ.get('DB_NAME', 'test_database')]
        
        # Create 50/50 presentation using existing video
        result = await create_avatar_presentation_50_50(
            "UG_DENT_Y3_S1_C03_M01",
            db,
            video_url="/api/videos/UG_DENT_Y1_S1_C01_M01_5min/file"
        )
        print(result)
    
    asyncio.run(main())
