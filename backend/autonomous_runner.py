"""
Autonomous Runner - Runs MCQ generation and Video generation in background
"""
import os
import asyncio
import logging
import json
import requests
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/backend/autonomous_log.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# HeyGen config
HEYGEN_API_KEY = os.environ.get('HEYGEN_API_KEY', 'sk_V2_hgu_kXVuWJrQn74_2eBCQ3FvLT6LggmUwyoJOes2woHS61dM')
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# MongoDB
client = AsyncIOMotorClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]

# Progress tracking
progress = {
    'mcq': {'completed': 0, 'total': 0, 'courses': []},
    'videos': {'completed': 0, 'total': 0, 'modules': []},
    'started_at': None,
    'status': 'idle'
}

def save_progress():
    with open('/app/backend/autonomous_progress.json', 'w') as f:
        json.dump(progress, f, indent=2, default=str)

async def generate_mcq_for_course(course_id: str, course_name: str, target: int = 300):
    """Generate MCQ questions for a course using AI"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    current_count = await db.mcq_questions.count_documents({'course_id': course_id})
    needed = target - current_count
    
    if needed <= 0:
        logger.info(f"Course {course_id} already has {current_count} questions")
        return current_count
    
    logger.info(f"Generating {needed} questions for {course_name}")
    
    questions_generated = 0
    batch_size = 25
    
    while questions_generated < needed:
        remaining = min(batch_size, needed - questions_generated)
        
        try:
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"mcq_{course_id}_{questions_generated}",
                system_message="""You are a medical education expert creating MCQ questions.
Create high-quality questions for medical/dental board exam preparation.
Return ONLY a valid JSON array, no other text."""
            ).with_model("openai", "gpt-4o-mini")
            
            prompt = f"""Generate {remaining} multiple-choice questions for:
Course: {course_name}

For each question provide:
1. question: The question text
2. option_a, option_b, option_c, option_d: Four answer options  
3. correct_answer: A, B, C, or D
4. explanation: Brief explanation (1-2 sentences)
5. difficulty: easy, medium, or hard

Return as JSON array ONLY:
[{{"question": "...", "option_a": "...", "option_b": "...", "option_c": "...", "option_d": "...", "correct_answer": "A", "explanation": "...", "difficulty": "medium"}}]

Create clinically relevant questions. Vary difficulty: 30% easy, 50% medium, 20% hard."""
            
            response = await chat.send_message(UserMessage(text=prompt))
            
            # Parse JSON
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                batch_questions = json.loads(response[json_start:json_end])
                
                # Add metadata and save
                for q in batch_questions:
                    q['question_id'] = f"q_{course_id}_{current_count + questions_generated:04d}"
                    q['course_id'] = course_id
                    q['topic'] = course_name
                    q['created_at'] = datetime.now(timezone.utc).isoformat()
                    questions_generated += 1
                
                if batch_questions:
                    await db.mcq_questions.insert_many(batch_questions)
                    logger.info(f"  Added {len(batch_questions)} questions to {course_id}")
            
            await asyncio.sleep(2)  # Rate limiting
            
        except Exception as e:
            logger.error(f"Error generating MCQ batch: {e}")
            await asyncio.sleep(5)
    
    final_count = await db.mcq_questions.count_documents({'course_id': course_id})
    return final_count

async def generate_video_for_module(module_id: str, course_name: str, module_title: str):
    """Generate video using HeyGen"""
    
    # Check if video already exists
    existing = await db.module_videos.find_one({'module_id': module_id, 'status': 'completed'})
    if existing and existing.get('video_url'):
        logger.info(f"Video already exists for {module_id}")
        return existing.get('video_url')
    
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Api-Key': HEYGEN_API_KEY
    }
    
    # Create educational script
    script = f"""Welcome to this lecture on {module_title} from the course {course_name}. 

In this module, we will explore the key concepts and principles of {module_title}. 

This topic is essential for your medical education and will help you understand important clinical applications.

Let's begin our learning journey."""
    
    payload = {
        'video_inputs': [{
            'character': {
                'type': 'avatar',
                'avatar_id': 'Abigail_expressive_2024112501',
                'avatar_style': 'normal'
            },
            'voice': {
                'type': 'text',
                'input_text': script,
                'voice_id': '42d00d4aac5441279d8536cd6b52c53c',
                'speed': 0.95
            },
            'background': {
                'type': 'color',
                'value': '#1a365d'
            }
        }],
        'dimension': {'width': 1280, 'height': 720},
        'test': False
    }
    
    try:
        # Create video
        response = requests.post(
            'https://api.heygen.com/v2/video/generate',
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            logger.error(f"HeyGen error: {response.text}")
            return None
        
        result = response.json()
        video_id = result.get('data', {}).get('video_id')
        
        if not video_id:
            logger.error(f"No video_id returned for {module_id}")
            return None
        
        logger.info(f"Video queued for {module_id}: {video_id}")
        
        # Wait for completion (max 10 minutes)
        for i in range(60):
            await asyncio.sleep(10)
            
            status_response = requests.get(
                'https://api.heygen.com/v1/video_status.get',
                headers={'Accept': 'application/json', 'X-Api-Key': HEYGEN_API_KEY},
                params={'video_id': video_id}
            )
            
            status_data = status_response.json().get('data', {})
            status = status_data.get('status')
            
            if status == 'completed':
                video_url = status_data.get('video_url')
                duration = status_data.get('duration')
                
                # Save to database
                await db.module_videos.update_one(
                    {'module_id': module_id},
                    {'$set': {
                        'module_id': module_id,
                        'video_id': video_id,
                        'video_url': video_url,
                        'duration': duration,
                        'status': 'completed',
                        'created_at': datetime.now(timezone.utc).isoformat()
                    }},
                    upsert=True
                )
                
                logger.info(f"Video completed for {module_id}: {duration}s")
                return video_url
                
            elif status == 'failed':
                error = status_data.get('error')
                logger.error(f"Video failed for {module_id}: {error}")
                return None
        
        logger.warning(f"Video timeout for {module_id}")
        return None
        
    except Exception as e:
        logger.error(f"Error generating video for {module_id}: {e}")
        return None

async def run_mcq_generation():
    """Generate MCQs for all courses that need them"""
    logger.info("="*60)
    logger.info("STARTING MCQ GENERATION")
    logger.info("="*60)
    
    # Find courses under 300 questions
    pipeline = [
        {'$group': {'_id': '$course_id', 'count': {'$sum': 1}}}
    ]
    mcq_counts = {item['_id']: item['count'] for item in await db.mcq_questions.aggregate(pipeline).to_list(1000)}
    
    all_courses = await db.courses.find({}, {'_id': 0}).to_list(1000)
    
    courses_to_process = []
    for course in all_courses:
        course_id = course['external_id']
        current = mcq_counts.get(course_id, 0)
        if current < 300:
            courses_to_process.append({
                'id': course_id,
                'name': course['course_name'],
                'current': current,
                'needed': 300 - current
            })
    
    progress['mcq']['total'] = len(courses_to_process)
    progress['mcq']['courses'] = [c['id'] for c in courses_to_process]
    save_progress()
    
    logger.info(f"Found {len(courses_to_process)} courses needing MCQs")
    
    for i, course in enumerate(courses_to_process):
        logger.info(f"\n[{i+1}/{len(courses_to_process)}] Processing {course['id']}")
        
        final_count = await generate_mcq_for_course(
            course['id'], 
            course['name'],
            300
        )
        
        progress['mcq']['completed'] = i + 1
        save_progress()
        
        logger.info(f"  Final count: {final_count}/300")
        
        # Small delay between courses
        await asyncio.sleep(3)
    
    logger.info("\n" + "="*60)
    logger.info("MCQ GENERATION COMPLETE")
    logger.info("="*60)

async def run_video_generation():
    """Generate videos for all modules"""
    logger.info("="*60)
    logger.info("STARTING VIDEO GENERATION")
    logger.info("="*60)
    
    # Get all modules
    modules = await db.modules.find({}, {'_id': 0}).to_list(1000)
    
    # Get existing videos
    existing_videos = await db.module_videos.find(
        {'status': 'completed'},
        {'_id': 0, 'module_id': 1}
    ).to_list(1000)
    existing_ids = {v['module_id'] for v in existing_videos}
    
    # Filter modules without videos
    modules_to_process = [m for m in modules if m['module_id'] not in existing_ids]
    
    progress['videos']['total'] = len(modules_to_process)
    progress['videos']['modules'] = [m['module_id'] for m in modules_to_process[:50]]  # First 50
    save_progress()
    
    logger.info(f"Found {len(modules_to_process)} modules needing videos")
    
    for i, module in enumerate(modules_to_process):
        logger.info(f"\n[{i+1}/{len(modules_to_process)}] Processing {module['module_id']}")
        
        # Get course name
        course = await db.courses.find_one({'external_id': module['courseId']}, {'_id': 0})
        course_name = course['course_name'] if course else 'Course'
        
        video_url = await generate_video_for_module(
            module['module_id'],
            course_name,
            module.get('title', 'Module')
        )
        
        progress['videos']['completed'] = i + 1
        save_progress()
        
        if video_url:
            logger.info(f"  Video created successfully")
        else:
            logger.warning(f"  Video creation failed, continuing...")
        
        # Delay between videos to avoid rate limiting
        await asyncio.sleep(5)
    
    logger.info("\n" + "="*60)
    logger.info("VIDEO GENERATION COMPLETE")
    logger.info("="*60)

async def main():
    """Main autonomous runner"""
    progress['started_at'] = datetime.now(timezone.utc).isoformat()
    progress['status'] = 'running'
    save_progress()
    
    logger.info("="*60)
    logger.info("AUTONOMOUS RUNNER STARTED")
    logger.info(f"Time: {progress['started_at']}")
    logger.info("="*60)
    
    try:
        # Phase 1: Generate MCQs
        await run_mcq_generation()
        
        # Phase 2: Generate Videos
        await run_video_generation()
        
        progress['status'] = 'completed'
        
    except Exception as e:
        logger.error(f"Autonomous runner error: {e}")
        progress['status'] = 'error'
        progress['error'] = str(e)
    
    finally:
        progress['completed_at'] = datetime.now(timezone.utc).isoformat()
        save_progress()
        
        logger.info("\n" + "="*60)
        logger.info("AUTONOMOUS RUNNER FINISHED")
        logger.info(f"Status: {progress['status']}")
        logger.info("="*60)

if __name__ == "__main__":
    asyncio.run(main())
