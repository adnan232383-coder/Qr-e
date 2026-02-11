"""
Generate intro videos for all UG and NVU courses
Using only approved styles (Medical Dark, Presentation)
"""

import os
import time
import json
import requests
from datetime import datetime
from pymongo import MongoClient

HEYGEN_API_KEY = os.environ.get("HEYGEN_API_KEY", "sk_V2_hgu_kXVuWJrQn74_2eBCQ3FvLT6LggmUwyoJOes2woHS61dM")
BASE_URL = "https://api.heygen.com"
OUTPUT_BASE = "/app/frontend/public/videos/courses"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "X-Api-Key": HEYGEN_API_KEY
}

# MongoDB
client = MongoClient('mongodb://localhost:27017')
db = client['test_database']

# Approved styles only
APPROVED_STYLES = [
    {
        "id": "medical_dark",
        "name": "Medical Dark",
        "avatar_id": "Adriana_Nurse_Front_public",
        "voice_id": "42d00d4aac5441279d8536cd6b52c53c",
        "background": {"type": "color", "value": "#1a1a2e"},
    },
    {
        "id": "presentation", 
        "name": "Presentation",
        "avatar_id": "Adriana_Nurse_Front_public",
        "voice_id": "42d00d4aac5441279d8536cd6b52c53c",
        "background": {"type": "color", "value": "#1a1a2e"},
        "scale": 0.8,
        "offset": {"x": -0.3, "y": 0}
    }
]


def get_style_for_module(module_index):
    """Modules 1-4: Medical Dark, Modules 5-8: Presentation"""
    return APPROVED_STYLES[0] if module_index < 4 else APPROVED_STYLES[1]


def generate_intro_script(course_name, course_desc, mcq_count):
    """Generate intro script for a course"""
    return f"""Welcome to {course_name}. This course covers {course_desc or 'essential concepts for your medical education'}. 
You will find {mcq_count} practice questions to test your knowledge. 
Let's begin your learning journey."""


def create_video_payload(script, style):
    """Create HeyGen API payload"""
    character = {
        "type": "avatar",
        "avatar_id": style["avatar_id"],
        "avatar_style": "normal"
    }
    
    if style.get("scale"):
        character["scale"] = style["scale"]
    if style.get("offset"):
        character["offset"] = style["offset"]
    
    return {
        "video_inputs": [{
            "character": character,
            "voice": {
                "type": "text",
                "input_text": script,
                "voice_id": style["voice_id"],
                "speed": 1.0
            },
            "background": style["background"]
        }],
        "dimension": {"width": 1920, "height": 1080},
        "test": False
    }


def generate_video(script, style):
    """Submit video generation request"""
    payload = create_video_payload(script, style)
    
    try:
        response = requests.post(
            f"{BASE_URL}/v2/video/generate",
            headers=HEADERS,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json().get("data", {}).get("video_id")
        else:
            print(f"Error: {response.status_code} - {response.text[:100]}")
            return None
    except Exception as e:
        print(f"Request error: {e}")
        return None


def check_status(video_id):
    """Check video generation status"""
    try:
        response = requests.get(
            f"{BASE_URL}/v1/video_status.get",
            headers=HEADERS,
            params={"video_id": video_id},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json().get("data", {})
            return {
                "status": data.get("status"),
                "url": data.get("video_url"),
                "duration": data.get("duration")
            }
    except:
        pass
    return {"status": "error"}


def download_video(url, output_path):
    """Download video file"""
    try:
        response = requests.get(url, stream=True, timeout=120)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
    except Exception as e:
        print(f"Download error: {e}")
    return False


def process_university(university_id, max_courses=10):
    """Process courses for a university"""
    
    print(f"\n{'='*60}")
    print(f"Processing {university_id}")
    print(f"{'='*60}")
    
    # Get courses
    courses = list(db.courses.find(
        {'university_id': university_id},
        {'_id': 0, 'external_id': 1, 'course_name': 1, 'course_description': 1, 'mcq_count': 1}
    ).sort('external_id', 1).limit(max_courses))
    
    print(f"Found {len(courses)} courses")
    
    # Create output directory
    output_dir = f"{OUTPUT_BASE}/{university_id}"
    os.makedirs(output_dir, exist_ok=True)
    
    jobs = []
    style = APPROVED_STYLES[0]  # Medical Dark for intro
    
    for i, course in enumerate(courses):
        course_id = course['external_id']
        course_name = course['course_name']
        
        # Check if video already exists
        video_path = f"{output_dir}/{course_id}_intro.mp4"
        if os.path.exists(video_path):
            print(f"[{i+1}/{len(courses)}] {course_id} - Already exists, skipping")
            continue
        
        print(f"[{i+1}/{len(courses)}] Generating {course_id}...")
        
        # Generate script
        script = generate_intro_script(
            course_name,
            course.get('course_description'),
            course.get('mcq_count', 0)
        )
        
        # Submit video generation
        video_id = generate_video(script, style)
        
        if video_id:
            jobs.append({
                "course_id": course_id,
                "video_id": video_id,
                "output_path": video_path,
                "status": "pending"
            })
            print(f"  Video ID: {video_id}")
        else:
            print(f"  FAILED to generate")
        
        time.sleep(3)  # Rate limit
    
    # Save jobs
    jobs_file = f"{output_dir}/jobs.json"
    with open(jobs_file, 'w') as f:
        json.dump(jobs, f, indent=2)
    
    return jobs


def monitor_and_download(jobs, output_dir, max_wait=1800):
    """Monitor jobs and download completed videos"""
    
    if not jobs:
        return
    
    print(f"\nMonitoring {len(jobs)} video jobs...")
    
    completed = 0
    start_time = time.time()
    
    while completed < len(jobs) and (time.time() - start_time) < max_wait:
        for job in jobs:
            if job["status"] in ["completed", "failed", "downloaded"]:
                continue
            
            status = check_status(job["video_id"])
            
            if status["status"] == "completed":
                if download_video(status["url"], job["output_path"]):
                    job["status"] = "downloaded"
                    job["duration"] = status["duration"]
                    completed += 1
                    print(f"✓ Downloaded: {job['course_id']}")
                else:
                    job["status"] = "download_failed"
                    completed += 1
                    
            elif status["status"] == "failed":
                job["status"] = "failed"
                completed += 1
                print(f"✗ Failed: {job['course_id']}")
        
        pending = len([j for j in jobs if j["status"] == "pending"])
        if pending > 0:
            print(f"\rPending: {pending}, Completed: {completed}/{len(jobs)}", end="", flush=True)
            time.sleep(15)
    
    # Save final status
    jobs_file = f"{output_dir}/jobs.json"
    with open(jobs_file, 'w') as f:
        json.dump(jobs, f, indent=2)
    
    return jobs


def main():
    """Main function - process both universities"""
    
    print("=" * 60)
    print("COURSE VIDEO GENERATOR")
    print("Using approved styles: Medical Dark, Presentation")
    print("=" * 60)
    
    # Process UG_TBILISI - first 20 courses
    ug_jobs = process_university("UG_TBILISI", max_courses=20)
    
    # Process NVU - first 20 courses
    nvu_jobs = process_university("NVU", max_courses=20)
    
    # Monitor all jobs
    all_jobs = ug_jobs + nvu_jobs
    
    if all_jobs:
        print(f"\n{'='*60}")
        print(f"Total jobs: {len(all_jobs)}")
        print("Starting download monitoring...")
        print("=" * 60)
        
        # Monitor in batches
        monitor_and_download(ug_jobs, f"{OUTPUT_BASE}/UG_TBILISI")
        monitor_and_download(nvu_jobs, f"{OUTPUT_BASE}/NVU")
    
    print(f"\n{'='*60}")
    print("COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
