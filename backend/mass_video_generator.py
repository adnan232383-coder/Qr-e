#!/usr/bin/env python3
"""
Mass Video Generator - Uses Avatar III (Unlimited) for free video generation
Generates educational videos for all courses
"""

import asyncio
import os
import time
import requests
import uuid
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

HEYGEN_API_KEY = os.environ.get("HEYGEN_API_KEY")
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")

# Avatar III configuration - FREE UNLIMITED
AVATARS = [
    {"id": "Abigail_standing_office_front", "name": "Abigail Office", "gender": "female"},
    {"id": "Adriana_Nurse_Front_public", "name": "Adriana Nurse", "gender": "female"},
    {"id": "Adrian_public_2_20240312", "name": "Adrian Blue Suit", "gender": "male"},
]

VOICES = [
    {"id": "42d00d4aac5441279d8536cd6b52c53c", "name": "Hope", "gender": "female"},
    {"id": "cef3bc4e0a84424cafcde6f2cf466c97", "name": "Ivy", "gender": "female"},
    {"id": "6be73833ef9a4eb0aeee399b8fe9d62b", "name": "Andrew", "gender": "male"},
]

BACKGROUNDS = [
    {"type": "color", "value": "#1a1a2e"},  # Dark blue
    {"type": "color", "value": "#f5f5f5"},  # Light gray
    {"type": "color", "value": "#e8f5e9"},  # Medical green
    {"type": "color", "value": "#263238"},  # Dark studio
]


class VideoGenerator:
    def __init__(self):
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Api-Key": HEYGEN_API_KEY
        }
        self.base_url = "https://api.heygen.com"
    
    def get_config(self, module_index: int):
        """Get avatar/voice config based on module for variety"""
        avatar = AVATARS[module_index % len(AVATARS)]
        # Match voice gender with avatar
        voices = [v for v in VOICES if v["gender"] == avatar["gender"]]
        voice = voices[module_index % len(voices)] if voices else VOICES[0]
        background = BACKGROUNDS[module_index % len(BACKGROUNDS)]
        return avatar, voice, background
    
    def create_video(self, script: str, module_index: int = 0) -> dict:
        """Create a video using Avatar III (unlimited)"""
        avatar, voice, background = self.get_config(module_index)
        
        payload = {
            "video_inputs": [
                {
                    "character": {
                        "type": "avatar",
                        "avatar_id": avatar["id"],
                        "avatar_style": "normal"  # Avatar III
                    },
                    "voice": {
                        "type": "text",
                        "input_text": script,
                        "voice_id": voice["id"],
                        "speed": 1.0
                    },
                    "background": background
                }
            ],
            "dimension": {"width": 1280, "height": 720},
            "test": False
        }
        
        response = requests.post(
            f"{self.base_url}/v2/video/generate",
            headers=self.headers,
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "video_id": data.get("data", {}).get("video_id"),
                "avatar": avatar["name"],
                "voice": voice["name"]
            }
        else:
            return {
                "success": False,
                "error": response.text
            }
    
    def check_status(self, video_id: str) -> dict:
        """Check video generation status"""
        response = requests.get(
            f"{self.base_url}/v1/video_status.get",
            headers=self.headers,
            params={"video_id": video_id}
        )
        return response.json() if response.status_code == 200 else {"error": response.text}
    
    def wait_for_completion(self, video_id: str, max_wait: int = 600) -> dict:
        """Wait for video to complete"""
        start = time.time()
        while time.time() - start < max_wait:
            status = self.check_status(video_id)
            state = status.get("data", {}).get("status", "unknown")
            
            if state == "completed":
                return {
                    "success": True,
                    "video_url": status.get("data", {}).get("video_url"),
                    "duration": status.get("data", {}).get("duration")
                }
            elif state == "failed":
                return {
                    "success": False,
                    "error": status.get("data", {}).get("error", {})
                }
            
            time.sleep(15)
        
        return {"success": False, "error": "Timeout"}


async def generate_course_scripts(course_id: str, course_name: str, num_modules: int = 8):
    """Generate educational scripts for a course using LLM"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    
    scripts = []
    for i in range(num_modules):
        prompt = f"""Create a 2-minute educational video script for dental students.

Course: {course_name}
Module: {i + 1} of {num_modules}

The script should:
1. Be spoken naturally (no stage directions)
2. Cover a specific topic from this course
3. Include key facts and clinical relevance
4. Be engaging and educational
5. Be approximately 250-300 words (2 minutes when spoken)

Return ONLY the script text, nothing else."""

        chat = LlmChat(
            api_key=api_key,
            session_id=f"script_{uuid.uuid4().hex[:8]}",
            system_message="You are a medical education expert creating video scripts."
        ).with_model("openai", "gpt-4o-mini")
        
        response = await chat.send_message(UserMessage(text=prompt))
        scripts.append({
            "module_number": i + 1,
            "script": response.strip()
        })
    
    return scripts


async def process_course(course_id: str, course_name: str):
    """Process a single course - generate scripts and videos"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print(f"\n{'='*60}")
    print(f"Processing: {course_id} - {course_name}")
    print('='*60)
    
    # Check if videos already exist
    existing = await db.course_videos.count_documents({"course_id": course_id})
    if existing >= 8:
        print(f"  Already has {existing} videos, skipping")
        return
    
    # Generate scripts
    print("  Generating scripts...")
    scripts = await generate_course_scripts(course_id, course_name)
    
    # Create videos
    generator = VideoGenerator()
    
    for script_data in scripts:
        module_num = script_data["module_number"]
        script = script_data["script"]
        
        print(f"  Creating video for module {module_num}...")
        result = generator.create_video(script, module_num - 1)
        
        if result["success"]:
            video_id = result["video_id"]
            print(f"    Video ID: {video_id}")
            
            # Save to database
            await db.course_videos.insert_one({
                "course_id": course_id,
                "module_number": module_num,
                "video_id": video_id,
                "avatar": result["avatar"],
                "voice": result["voice"],
                "script": script,
                "status": "processing",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            
            # Wait a bit between requests
            await asyncio.sleep(5)
        else:
            print(f"    Failed: {result.get('error', 'Unknown error')}")
            break
    
    print(f"  Done processing {course_id}")


async def main():
    """Main function to process all courses"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Get all courses
    courses = await db.courses.find(
        {},
        {"_id": 0, "external_id": 1, "course_name": 1}
    ).to_list(1000)
    
    print(f"Found {len(courses)} courses to process")
    
    # Process each course
    for course in courses[:5]:  # Start with first 5 as test
        await process_course(course["external_id"], course["course_name"])


if __name__ == "__main__":
    asyncio.run(main())
