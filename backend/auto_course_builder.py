"""
Autonomous Course Video Generator
Generates video courses with diverse avatar styles
"""

import os
import time
import json
import requests
from datetime import datetime
from pymongo import MongoClient

HEYGEN_API_KEY = os.environ.get("HEYGEN_API_KEY", "sk_V2_hgu_kXVuWJrQn74_2eBCQ3FvLT6LggmUwyoJOes2woHS61dM")
BASE_URL = "https://api.heygen.com"
OUTPUT_BASE = "/app/frontend/public/videos"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "X-Api-Key": HEYGEN_API_KEY
}

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017')
db = client['test_database']

# Style configurations - rotating every 2 modules
STYLE_CONFIGS = [
    {
        "avatar_id": "Adriana_Nurse_Front_public",
        "avatar_name": "Adriana Nurse",
        "voice_id": "42d00d4aac5441279d8536cd6b52c53c",
        "voice_name": "Hope",
        "background": {"type": "color", "value": "#1a1a2e"},
        "style_name": "Medical Dark"
    },
    {
        "avatar_id": "Abigail_standing_office_front",
        "avatar_name": "Abigail Office",
        "voice_id": "cef3bc4e0a84424cafcde6f2cf466c97",
        "voice_name": "Ivy",
        "background": {"type": "color", "value": "#f5f5f5"},
        "style_name": "Office Light"
    },
    {
        "avatar_id": "Adrian_public_2_20240312",
        "avatar_name": "Adrian Blue Suit",
        "voice_id": "6be73833ef9a4eb0aeee399b8fe9d62b",
        "voice_name": "Andrew",
        "background": {"type": "color", "value": "#263238"},
        "style_name": "Studio Dark"
    },
    {
        "avatar_id": "Adriana_Business_Front_public",
        "avatar_name": "Adriana Business",
        "voice_id": "42d00d4aac5441279d8536cd6b52c53c",
        "voice_name": "Hope",
        "background": {"type": "color", "value": "#1e3a5f"},
        "style_name": "Business Modern"
    }
]


def get_course_info(course_id):
    """Get course information from database"""
    course = db.courses.find_one({'external_id': course_id}, {'_id': 0})
    return course


def get_mcq_questions(course_id, limit=200):
    """Get MCQ questions for a course"""
    questions = list(db.mcq_questions.find(
        {'course_id': course_id}, 
        {'_id': 0, 'question': 1, 'topic': 1, 'subtopic': 1}
    ).limit(limit))
    return questions


def create_module_scripts(course_id, course_name, questions, num_modules=8):
    """Create educational scripts from MCQ questions"""
    
    # Group questions by topic
    topics = {}
    for q in questions:
        topic = q.get('topic', q.get('subtopic', 'General'))
        if topic not in topics:
            topics[topic] = []
        topics[topic].append(q.get('question', ''))
    
    # Create modules from topics
    topic_list = list(topics.keys())
    modules_per_topic = max(1, len(topic_list) // num_modules)
    
    scripts = []
    for i in range(num_modules):
        start_idx = i * modules_per_topic
        end_idx = min(start_idx + modules_per_topic, len(topic_list))
        module_topics = topic_list[start_idx:end_idx] if start_idx < len(topic_list) else [topic_list[-1]]
        
        # Generate script from questions in these topics
        module_questions = []
        for t in module_topics:
            module_questions.extend(topics[t][:5])  # Take up to 5 questions per topic
        
        # Create educational script
        topic_name = module_topics[0] if module_topics else f"Part {i+1}"
        script = generate_educational_script(course_name, topic_name, module_questions[:10], i+1)
        
        scripts.append({
            "module_id": f"module{i+1}",
            "module_number": i + 1,
            "title": f"{topic_name}",
            "topics": module_topics[:3],
            "script": script
        })
    
    return scripts


def generate_educational_script(course_name, topic, questions, module_num):
    """Generate an educational script from questions"""
    
    # Extract key concepts from questions
    concepts = []
    for q in questions[:5]:
        # Extract the main subject from the question
        if q:
            words = q.split()[:10]
            concepts.append(' '.join(words))
    
    intro = f"Welcome to Module {module_num} of {course_name}. Today we will explore {topic}."
    
    body = f"In this lecture, we will cover important concepts that every student should understand. "
    
    if concepts:
        body += f"Key topics include: {'. '.join(concepts[:3])}. "
    
    body += "Pay close attention to these fundamental principles as they form the foundation for advanced topics. "
    body += "Understanding these concepts will help you succeed in your examinations and clinical practice."
    
    conclusion = f"This concludes Module {module_num}. Review the key points and practice with the associated questions."
    
    return f"{intro} {body} {conclusion}"


def get_style_for_module(module_index):
    """Get style config based on module index"""
    style_index = (module_index // 2) % len(STYLE_CONFIGS)
    return STYLE_CONFIGS[style_index]


def generate_video(script_text, style_config):
    """Generate a video using HeyGen API"""
    payload = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": style_config["avatar_id"],
                    "avatar_style": "normal"
                },
                "voice": {
                    "type": "text",
                    "input_text": script_text,
                    "voice_id": style_config["voice_id"],
                    "speed": 1.0
                },
                "background": style_config["background"]
            }
        ],
        "dimension": {"width": 1920, "height": 1080},
        "test": False
    }
    
    response = requests.post(
        f"{BASE_URL}/v2/video/generate",
        headers=HEADERS,
        json=payload
    )
    
    if response.status_code == 200:
        return response.json().get("data", {}).get("video_id")
    else:
        print(f"Error: {response.text}")
        return None


def check_video_status(video_id):
    """Check video generation status"""
    response = requests.get(
        f"{BASE_URL}/v1/video_status.get",
        headers=HEADERS,
        params={"video_id": video_id}
    )
    
    if response.status_code == 200:
        data = response.json().get("data", {})
        return {
            "status": data.get("status"),
            "video_url": data.get("video_url"),
            "duration": data.get("duration")
        }
    return {"status": "error"}


def download_video(video_url, output_path):
    """Download video to local path"""
    response = requests.get(video_url, stream=True)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    return False


def build_course(course_id, num_modules=8):
    """Build a complete course with videos"""
    
    print(f"\n{'='*60}")
    print(f"Building Course: {course_id}")
    print(f"{'='*60}")
    
    # Get course info
    course = get_course_info(course_id)
    if not course:
        print(f"Course not found: {course_id}")
        return None
    
    course_name = course.get('course_name', course_id)
    print(f"Course: {course_name}")
    
    # Get questions
    questions = get_mcq_questions(course_id)
    print(f"Questions found: {len(questions)}")
    
    if len(questions) < 10:
        print("Not enough questions for course content")
        return None
    
    # Create output directory
    output_dir = f"{OUTPUT_BASE}/{course_id}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create module scripts
    scripts = create_module_scripts(course_id, course_name, questions, num_modules)
    
    # Save scripts
    scripts_file = f"{output_dir}/scripts.json"
    with open(scripts_file, 'w') as f:
        json.dump(scripts, f, indent=2)
    print(f"Scripts saved to: {scripts_file}")
    
    # Generate videos
    jobs = []
    print(f"\nGenerating {len(scripts)} videos...")
    
    for i, module in enumerate(scripts):
        style = get_style_for_module(i)
        print(f"\n[{i+1}/{len(scripts)}] {module['title']}")
        print(f"  Style: {style['style_name']} | Avatar: {style['avatar_name']}")
        
        video_id = generate_video(module['script'], style)
        
        if video_id:
            jobs.append({
                "module_id": module['module_id'],
                "title": module['title'],
                "video_id": video_id,
                "style": style['style_name'],
                "status": "pending",
                "output_file": f"{module['module_id']}.mp4"
            })
            print(f"  Video ID: {video_id}")
        else:
            print(f"  FAILED to start generation")
        
        time.sleep(2)  # Rate limiting
    
    # Save jobs
    jobs_file = f"{output_dir}/jobs.json"
    with open(jobs_file, 'w') as f:
        json.dump(jobs, f, indent=2)
    
    # Monitor and download
    print(f"\nMonitoring video generation...")
    completed = 0
    max_wait = 1800  # 30 minutes
    start_time = time.time()
    
    while completed < len(jobs) and (time.time() - start_time) < max_wait:
        for job in jobs:
            if job["status"] == "completed":
                continue
            
            status = check_video_status(job["video_id"])
            
            if status["status"] == "completed":
                output_path = f"{output_dir}/{job['output_file']}"
                if download_video(status["video_url"], output_path):
                    job["status"] = "completed"
                    job["duration"] = status["duration"]
                    completed += 1
                    print(f"\n✓ {job['title']} downloaded")
                else:
                    job["status"] = "download_failed"
                    
            elif status["status"] == "failed":
                job["status"] = "failed"
                completed += 1
                print(f"\n✗ {job['title']} FAILED")
        
        # Save progress
        with open(jobs_file, 'w') as f:
            json.dump(jobs, f, indent=2)
        
        pending = len([j for j in jobs if j["status"] == "pending"])
        if pending > 0:
            print(f"\rPending: {pending} | Completed: {completed}/{len(jobs)}", end="", flush=True)
            time.sleep(15)
    
    # Create frontend page data
    page_data = {
        "course_id": course_id,
        "course_name": course_name,
        "description": course.get('course_description', ''),
        "modules": []
    }
    
    for i, module in enumerate(scripts):
        job = next((j for j in jobs if j['module_id'] == module['module_id']), None)
        page_data["modules"].append({
            "id": module['module_id'],
            "title": module['title'],
            "topics": module['topics'],
            "videoFile": f"{course_id}/{module['module_id']}.mp4" if job and job['status'] == 'completed' else None,
            "style": get_style_for_module(i)
        })
    
    page_file = f"{output_dir}/page_data.json"
    with open(page_file, 'w') as f:
        json.dump(page_data, f, indent=2)
    
    # Summary
    print(f"\n\n{'='*60}")
    print(f"COURSE BUILD COMPLETE: {course_name}")
    print(f"{'='*60}")
    
    success = sum(1 for j in jobs if j['status'] == 'completed')
    failed = sum(1 for j in jobs if j['status'] in ['failed', 'download_failed'])
    
    print(f"✓ Completed: {success}/{len(jobs)}")
    print(f"✗ Failed: {failed}/{len(jobs)}")
    print(f"Output: {output_dir}")
    
    return {
        "course_id": course_id,
        "course_name": course_name,
        "total": len(jobs),
        "completed": success,
        "failed": failed,
        "output_dir": output_dir
    }


def build_multiple_courses(course_ids):
    """Build multiple courses"""
    results = []
    for cid in course_ids:
        result = build_course(cid)
        if result:
            results.append(result)
        time.sleep(5)  # Pause between courses
    return results


if __name__ == "__main__":
    # Build next course: General Chemistry
    result = build_course("UG_PHARM_Y1_S1_C01", num_modules=8)
    if result:
        print(f"\nCourse built successfully!")
        print(json.dumps(result, indent=2))
