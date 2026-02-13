from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx
from contextlib import asynccontextmanager

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup: Resume any interrupted jobs
    from job_runner import init_job_runner
    logger.info("Starting server - checking for interrupted jobs...")
    await init_job_runner(db)
    yield
    # Shutdown
    from job_runner import get_job_runner
    runner = get_job_runner(db)
    await runner.shutdown()
    logger.info("Server shutdown complete")


# Create the main app with lifespan
app = FastAPI(title="UG University Assistant API", lifespan=lifespan)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ==================== MODELS ====================

class University(BaseModel):
    model_config = ConfigDict(extra="ignore")
    external_id: str
    name: str
    country: str
    city: str
    language: str
    type: str
    description: Optional[str] = None

class Faculty(BaseModel):
    model_config = ConfigDict(extra="ignore")
    external_id: str
    university_id: str
    name: str

class Major(BaseModel):
    model_config = ConfigDict(extra="ignore")
    external_id: str
    faculty_id: str
    name: str
    degree: str
    years: int
    image_url: Optional[str] = None

class Year(BaseModel):
    model_config = ConfigDict(extra="ignore")
    external_id: str
    major_id: str
    year_number: int
    year_title: str

class Course(BaseModel):
    model_config = ConfigDict(extra="ignore")
    external_id: str
    year_id: str
    semester: int
    course_name: str
    course_description: Optional[str] = None
    mcq_count: Optional[int] = 0
    mcq_verified: Optional[bool] = False

class CourseContent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    course_id: str
    summary: Optional[str] = None
    chapters: Optional[List[Dict[str, Any]]] = None

class Module(BaseModel):
    model_config = ConfigDict(extra="ignore")
    module_id: str
    courseId: str  # Links to course.external_id
    title: str
    description: Optional[str] = None
    order: int
    duration_hours: Optional[float] = None
    topics: Optional[List[str]] = None

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    course_id: Optional[str] = None
    history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    response: str

class MCQQuestion(BaseModel):
    model_config = ConfigDict(extra="ignore")
    question_id: str
    course_id: str
    question: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str
    explanation: str
    difficulty: Optional[str] = "medium"
    topic: Optional[str] = None

class ModuleScript(BaseModel):
    model_config = ConfigDict(extra="ignore")
    script_id: str
    module_id: str
    course_id: str
    script_text: str
    word_count: int
    estimated_duration_minutes: float
    status: str

class ContentStatusModel(BaseModel):
    course_id: str
    status: str
    updated_at: Optional[str] = None
    published_at: Optional[str] = None

class GenerateContentRequest(BaseModel):
    course_id: str

# ==================== AUTH HELPERS ====================

async def get_current_user(request: Request) -> Optional[User]:
    """Get current user from session token in cookie or header"""
    session_token = request.cookies.get("session_token")
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header[7:]
    
    if not session_token:
        return None
    
    session = await db.user_sessions.find_one(
        {"session_token": session_token},
        {"_id": 0}
    )
    
    if not session:
        return None
    
    # Check expiry with timezone awareness
    expires_at = session.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None
    
    user = await db.users.find_one(
        {"user_id": session["user_id"]},
        {"_id": 0}
    )
    
    if not user:
        return None
    
    if isinstance(user.get("created_at"), str):
        user["created_at"] = datetime.fromisoformat(user["created_at"])
    
    return User(**user)

async def require_auth(request: Request) -> User:
    """Require authentication - raises 401 if not authenticated"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/session")
async def create_session(request: Request, response: Response):
    """Exchange session_id from Emergent Auth for session_token"""
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    # Call Emergent Auth to get user data
    async with httpx.AsyncClient() as client_http:
        try:
            auth_response = await client_http.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id},
                timeout=10.0
            )
            if auth_response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid session_id")
            
            user_data = auth_response.json()
        except Exception as e:
            logger.error(f"Auth error: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")
    
    email = user_data.get("email")
    name = user_data.get("name")
    picture = user_data.get("picture")
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": email}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        # Update user info if changed
        await db.users.update_one(
            {"email": email},
            {"$set": {"name": name, "picture": picture}}
        )
    else:
        # Create new user
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        await db.users.insert_one({
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Create session
    session_token = f"sess_{uuid.uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return user

@api_router.get("/auth/me")
async def get_me(request: Request):
    """Get current authenticated user"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user.model_dump()

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout user"""
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie(key="session_token", path="/")
    return {"message": "Logged out"}

# ==================== CATALOG ROUTES ====================

@api_router.get("/universities", response_model=List[University])
async def get_universities():
    """Get all universities"""
    universities = await db.universities.find({}, {"_id": 0}).to_list(100)
    return universities

@api_router.get("/universities/{external_id}", response_model=University)
async def get_university(external_id: str):
    """Get university by external_id"""
    university = await db.universities.find_one({"external_id": external_id}, {"_id": 0})
    if not university:
        raise HTTPException(status_code=404, detail="University not found")
    return university

@api_router.get("/majors", response_model=List[Major])
async def get_majors(university_id: Optional[str] = None):
    """Get all majors, optionally filtered by university"""
    query = {}
    if university_id:
        # Get faculties for this university first
        faculties = await db.faculties.find({"university_id": university_id}, {"_id": 0}).to_list(100)
        faculty_ids = [f["external_id"] for f in faculties]
        query["faculty_id"] = {"$in": faculty_ids}
    
    majors = await db.majors.find(query, {"_id": 0}).to_list(100)
    return majors

@api_router.get("/majors/{external_id}", response_model=Major)
async def get_major(external_id: str):
    """Get major by external_id"""
    major = await db.majors.find_one({"external_id": external_id}, {"_id": 0})
    if not major:
        raise HTTPException(status_code=404, detail="Major not found")
    return major

@api_router.get("/years", response_model=List[Year])
async def get_years(major_id: str):
    """Get all years for a major"""
    years = await db.years.find({"major_id": major_id}, {"_id": 0}).to_list(100)
    years.sort(key=lambda x: x["year_number"])
    return years

@api_router.get("/courses", response_model=List[Course])
async def get_courses(year_id: Optional[str] = None, semester: Optional[int] = None, university_id: Optional[str] = None):
    """Get all courses, filtered by year_id, semester, or university_id"""
    query = {}
    if year_id:
        query["year_id"] = year_id
    if semester:
        query["semester"] = semester
    if university_id:
        query["university_id"] = university_id
    
    courses = await db.courses.find(query, {"_id": 0}).to_list(200)
    return courses

@api_router.get("/courses/by-university/{university_id}")
async def get_courses_by_university(university_id: str):
    """Get all courses for a university"""
    courses = await db.courses.find(
        {"university_id": university_id}, 
        {"_id": 0}
    ).sort([("program", 1), ("year", 1), ("semester", 1)]).to_list(200)
    
    # Add MCQ count for each course
    for course in courses:
        mcq_count = await db.mcq_questions.count_documents({"course_id": course["external_id"]})
        course["mcq_count"] = mcq_count
    
    return courses

@api_router.get("/courses/{external_id}", response_model=Course)
async def get_course(external_id: str):
    """Get course by external_id"""
    course = await db.courses.find_one({"external_id": external_id}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@api_router.get("/courses/{external_id}/content")
async def get_course_content(external_id: str):
    """Get course content (summary, chapters)"""
    content = await db.course_content.find_one({"course_id": external_id}, {"_id": 0})
    if not content:
        # Return empty content if not exists
        return {"course_id": external_id, "summary": None, "chapters": None}
    return content

@api_router.get("/courses/{external_id}/modules", response_model=List[Module])
async def get_course_modules(external_id: str):
    """Get all modules for a course by courseId"""
    # Query modules by courseId (string match with course external_id)
    modules = await db.modules.find({"courseId": external_id}, {"_id": 0}).to_list(100)
    # Sort by order
    modules.sort(key=lambda x: x.get("order", 0))
    return modules

@api_router.get("/courses/{external_id}/status")
async def get_course_content_status(external_id: str):
    """Get content generation status for a course"""
    from content_generator import ContentGenerator
    generator = ContentGenerator(db)
    status = await generator.get_content_status(external_id)
    
    # Also get counts
    questions_count = await db.mcq_questions.count_documents({"course_id": external_id})
    scripts_count = await db.module_scripts.count_documents({"course_id": external_id})
    content = await db.course_content.find_one({"course_id": external_id}, {"_id": 0})
    
    return {
        **status,
        "has_summary": bool(content and content.get("summary")),
        "questions_count": questions_count,
        "scripts_count": scripts_count
    }

@api_router.get("/courses/{external_id}/questions")
async def get_course_questions(external_id: str, limit: int = 50, offset: int = 0, difficulty: Optional[str] = None):
    """Get MCQ questions for a course"""
    query = {"course_id": external_id}
    if difficulty:
        query["difficulty"] = difficulty
    
    total = await db.mcq_questions.count_documents(query)
    questions = await db.mcq_questions.find(query, {"_id": 0}).skip(offset).limit(limit).to_list(limit)
    
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "questions": questions
    }

@api_router.get("/courses/{external_id}/scripts")
async def get_course_scripts(external_id: str):
    """Get all module scripts for a course"""
    scripts = await db.module_scripts.find({"course_id": external_id}, {"_id": 0}).to_list(100)
    return scripts

@api_router.get("/modules/{module_id}/script")
async def get_module_script(module_id: str):
    """Get script for a specific module"""
    script = await db.module_scripts.find_one({"module_id": module_id}, {"_id": 0})
    if not script:
        return {"module_id": module_id, "status": "pending", "script_text": None}
    return script

@api_router.get("/courses/{external_id}/logs")
async def get_generation_logs(external_id: str):
    """Get content generation logs for a course"""
    from content_generator import ContentGenerator
    generator = ContentGenerator(db)
    logs = await generator.get_generation_logs(external_id)
    return {"course_id": external_id, "logs": logs}

# ==================== CONTENT GENERATION ROUTES ====================

@api_router.post("/content/generate")
async def generate_content(request: GenerateContentRequest, background_tasks: BackgroundTasks):
    """Start content generation for a course (async)"""
    from content_generator import ContentGenerationQueue
    
    course = await db.courses.find_one({"external_id": request.course_id}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    queue = ContentGenerationQueue(db)
    task = await queue.enqueue(request.course_id)
    
    # Start processing in background
    background_tasks.add_task(queue.process_queue)
    
    return {"message": "Content generation queued", "task": task}

@api_router.post("/content/generate-sync/{course_id}")
async def generate_content_sync(course_id: str):
    """Generate content for a course synchronously (for testing)"""
    from content_generator import ContentGenerator
    
    course = await db.courses.find_one({"external_id": course_id}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    generator = ContentGenerator(db)
    result = await generator.generate_course_content(course_id)
    return result

@api_router.post("/content/publish/{course_id}")
async def publish_content(course_id: str):
    """Publish reviewed content"""
    from content_generator import ContentGenerator
    generator = ContentGenerator(db)
    success = await generator.publish_content(course_id)
    if not success:
        raise HTTPException(status_code=400, detail="Content not ready for publishing or already published")
    return {"message": "Content published", "course_id": course_id}

@api_router.get("/content/queue-status")
async def get_queue_status():
    """Get content generation queue status"""
    from content_generator import ContentGenerationQueue
    queue = ContentGenerationQueue(db)
    return await queue.get_queue_status()

@api_router.post("/content/generate-all")
async def generate_all_content(background_tasks: BackgroundTasks, limit: int = 5):
    """Queue content generation for all courses without content"""
    from content_generator import ContentGenerationQueue, ContentStatus
    
    # Find courses without generated content
    all_courses = await db.courses.find({}, {"_id": 0, "external_id": 1}).to_list(1000)
    
    queued = []
    queue = ContentGenerationQueue(db)
    
    for course in all_courses[:limit]:
        course_id = course["external_id"]
        status = await db.content_status.find_one({"course_id": course_id})
        
        if not status or status.get("status") == ContentStatus.PENDING:
            task = await queue.enqueue(course_id)
            queued.append(course_id)
    
    # Start processing
    if queued:
        background_tasks.add_task(queue.process_queue)
    
    return {"message": f"Queued {len(queued)} courses for content generation", "courses": queued}

# ==================== VIDEO GENERATION ROUTES ====================

@api_router.post("/video/generate/{module_id}")
async def generate_module_video(module_id: str, background_tasks: BackgroundTasks):
    """Generate video for a module script"""
    from video_generator import VideoGenerationQueue
    
    module = await db.modules.find_one({"module_id": module_id}, {"_id": 0})
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    script = await db.module_scripts.find_one({"module_id": module_id}, {"_id": 0})
    if not script:
        raise HTTPException(status_code=400, detail="Module script not found. Generate content first.")
    
    queue = VideoGenerationQueue(db)
    task = await queue.enqueue(module_id)
    
    background_tasks.add_task(queue.process_queue)
    
    return {"message": "Video generation queued", "task": task}

@api_router.get("/video/status/{module_id}")
async def get_video_status(module_id: str):
    """Get video generation status for a module"""
    from video_generator import VideoGenerator
    generator = VideoGenerator(db)
    return await generator.get_video_status(module_id)

@api_router.get("/video/{module_id}")
async def get_module_video(module_id: str):
    """Get video info for a module"""
    from video_generator import VideoGenerator
    generator = VideoGenerator(db)
    video = await generator.get_module_video(module_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video

@api_router.get("/videos/{module_id}")
async def serve_module_video(module_id: str):
    """Serve video file for a module"""
    # Check multiple video locations
    video_paths = [
        Path(f"/app/backend/heygen_videos/{module_id}.mp4"),
        Path(f"/app/generated_videos/{module_id}.mp4"),
    ]
    
    for video_path in video_paths:
        if video_path.exists():
            return FileResponse(
                video_path,
                media_type="video/mp4",
                filename=f"{module_id}.mp4",
                headers={"Accept-Ranges": "bytes"}
            )
    
    raise HTTPException(status_code=404, detail="Video file not found")

# ==================== PRESENTATION & AUDIO ROUTES ====================

@api_router.get("/presentations/{module_id}")
async def get_presentation(module_id: str):
    """Get HTML presentation for a module"""
    from starlette.responses import HTMLResponse
    
    presentation_path = Path(f"/app/backend/presentations/{module_id}.html")
    
    if not presentation_path.exists():
        raise HTTPException(status_code=404, detail="Presentation not found")
    
    # Read and return as HTML content (not download)
    with open(presentation_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    return HTMLResponse(content=html_content, media_type="text/html")

@api_router.api_route("/audio/{filename:path}", methods=["GET", "HEAD"])
async def get_audio(filename: str, request: Request):
    """Get audio narration for a module"""
    # Remove .mp3 extension if present to get module_id
    module_id = filename.replace('.mp3', '')
    audio_path = Path(f"/app/backend/audio/{module_id}.mp3")
    
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio not found")
    
    file_size = audio_path.stat().st_size
    
    # Handle HEAD request
    if request.method == "HEAD":
        return Response(
            content=b"",
            media_type="audio/mpeg",
            headers={
                "Content-Length": str(file_size),
                "Accept-Ranges": "bytes",
                "Content-Type": "audio/mpeg"
            }
        )
    
    return FileResponse(
        audio_path,
        media_type="audio/mpeg",
        filename=f"{module_id}.mp3",
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600"
        }
    )

@api_router.get("/module/{module_id}/content")
async def get_module_content(module_id: str):
    """Get available content (presentation, audio, video) for a module"""
    presentation_exists = Path(f"/app/backend/presentations/{module_id}.html").exists()
    audio_exists = Path(f"/app/backend/audio/{module_id}.mp3").exists()
    video_exists = (
        Path(f"/app/backend/heygen_videos/{module_id}.mp4").exists() or
        Path(f"/app/generated_videos/{module_id}.mp4").exists()
    )
    
    # Get script info
    script = await db.module_scripts.find_one({"module_id": module_id}, {"_id": 0})
    
    return {
        "module_id": module_id,
        "has_presentation": presentation_exists,
        "has_audio": audio_exists,
        "has_video": video_exists,
        "has_script": script is not None,
        "urls": {
            "presentation": f"/api/presentations/{module_id}" if presentation_exists else None,
            "audio": f"/api/audio/{module_id}.mp3" if audio_exists else None,
            "video": f"/api/videos/{module_id}/file" if video_exists else None
        }
    }

@api_router.post("/presentations/generate/{module_id}")
async def generate_presentation(module_id: str, background_tasks: BackgroundTasks):
    """Generate presentation and audio for a module"""
    from presentation_generator import generate_module_presentation
    from pymongo import MongoClient
    
    sync_client = MongoClient('mongodb://localhost:27017')
    sync_db = sync_client['test_database']
    
    # Check if module exists
    module = sync_db.modules.find_one({"module_id": module_id})
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    # Check if script exists
    script = sync_db.module_scripts.find_one({"module_id": module_id})
    if not script:
        raise HTTPException(status_code=400, detail="No script found for module")
    
    # Run generation
    import asyncio
    result = asyncio.get_event_loop().run_until_complete(
        generate_module_presentation(module_id, sync_db)
    )
    
    return result

@api_router.post("/presentations/generate-course/{course_id}")
async def generate_course_presentations(course_id: str):
    """Generate presentations and audio for all modules in a course"""
    from presentation_generator import generate_course_presentations as gen_course
    
    results = await gen_course(course_id)
    
    success_count = sum(1 for r in results if r.get("success"))
    
    return {
        "course_id": course_id,
        "total_modules": len(results),
        "successful": success_count,
        "results": results
    }

# ==================== 50/50 AVATAR PRESENTATION ROUTES ====================

@api_router.get("/presentations-50-50/{module_id}")
async def get_50_50_presentation(module_id: str):
    """Get 50/50 avatar presentation for a module"""
    from starlette.responses import HTMLResponse
    
    presentation_path = Path(f"/app/backend/presentations/{module_id}_50_50.html")
    
    if not presentation_path.exists():
        raise HTTPException(status_code=404, detail="50/50 Presentation not found")
    
    with open(presentation_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    return HTMLResponse(content=html_content, media_type="text/html")

@api_router.post("/presentations-50-50/generate/{module_id}")
async def generate_50_50_presentation(module_id: str, video_url: Optional[str] = None):
    """Generate 50/50 avatar presentation for a module"""
    from avatar_50_50_presentation import create_avatar_presentation_50_50
    from pymongo import MongoClient
    
    sync_client = MongoClient('mongodb://localhost:27017')
    sync_db = sync_client['test_database']
    
    module = sync_db.modules.find_one({"module_id": module_id})
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    script = sync_db.module_scripts.find_one({"module_id": module_id})
    if not script:
        raise HTTPException(status_code=400, detail="No script found for module")
    
    import asyncio
    result = asyncio.get_event_loop().run_until_complete(
        create_avatar_presentation_50_50(module_id, sync_db, video_url)
    )
    
    return result

@api_router.api_route("/avatar-videos/{module_id}", methods=["GET", "HEAD"])
async def serve_avatar_video(module_id: str, request: Request):
    """Serve avatar video file"""
    from starlette.responses import StreamingResponse
    
    video_paths = [
        Path(f"/app/backend/heygen_videos/{module_id}_avatar.mp4"),
        Path(f"/app/backend/heygen_videos/{module_id}.mp4"),
        Path(f"/app/backend/heygen_videos/{module_id}_5min.mp4"),
        Path(f"/app/backend/heygen_videos/{module_id}_full.mp4"),
    ]
    
    video_path = None
    for vp in video_paths:
        if vp.exists():
            video_path = vp
            break
    
    if not video_path:
        raise HTTPException(status_code=404, detail="Avatar video not found")
    
    file_size = video_path.stat().st_size
    range_header = request.headers.get("range")
    
    if range_header:
        range_match = range_header.replace("bytes=", "").split("-")
        start = int(range_match[0]) if range_match[0] else 0
        end = int(range_match[1]) if range_match[1] else file_size - 1
        
        if start >= file_size:
            raise HTTPException(status_code=416, detail="Range not satisfiable")
        if end >= file_size:
            end = file_size - 1
        
        content_length = end - start + 1
        
        def iter_file():
            with open(video_path, "rb") as f:
                f.seek(start)
                remaining = content_length
                while remaining > 0:
                    chunk_size = min(8192, remaining)
                    data = f.read(chunk_size)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data
        
        return StreamingResponse(
            iter_file(),
            status_code=206,
            media_type="video/mp4",
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
                "Content-Type": "video/mp4",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Expose-Headers": "Content-Range, Content-Length",
            }
        )
    
    # Return StreamingResponse to avoid Content-Disposition: attachment
    def iter_full_file():
        with open(video_path, "rb") as f:
            while chunk := f.read(65536):
                yield chunk
    
    return StreamingResponse(
        iter_full_file(),
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Content-Type": "video/mp4",
            "Access-Control-Allow-Origin": "*",
        }
    )

@api_router.post("/avatar-videos/generate/{module_id}")
async def generate_avatar_video(module_id: str, background_tasks: BackgroundTasks):
    """Generate HeyGen avatar video from existing audio file"""
    from avatar_50_50_presentation import generate_avatar_video_from_audio
    from pymongo import MongoClient
    
    audio_path = Path(f"/app/backend/audio/{module_id}.mp3")
    if not audio_path.exists():
        raise HTTPException(status_code=400, detail=f"No audio file found for {module_id}")
    
    sync_client = MongoClient('mongodb://localhost:27017')
    sync_db = sync_client['test_database']
    
    async def run_generation():
        result = await generate_avatar_video_from_audio(module_id, sync_db)
        await db.avatar_video_jobs.update_one(
            {"module_id": module_id},
            {"$set": {
                "module_id": module_id,
                "status": "completed" if result.get("success") else "failed",
                "result": result,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
    
    await db.avatar_video_jobs.update_one(
        {"module_id": module_id},
        {"$set": {
            "module_id": module_id,
            "status": "processing",
            "started_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    background_tasks.add_task(run_generation)
    
    return {
        "message": f"Avatar video generation started for {module_id}",
        "module_id": module_id,
        "status": "processing"
    }

@api_router.get("/avatar-videos/status/{module_id}")
async def get_avatar_video_status(module_id: str):
    """Get avatar video generation status"""
    job = await db.avatar_video_jobs.find_one({"module_id": module_id}, {"_id": 0})
    if not job:
        video_exists = (
            Path(f"/app/backend/heygen_videos/{module_id}_avatar.mp4").exists() or
            Path(f"/app/backend/heygen_videos/{module_id}.mp4").exists()
        )
        return {
            "module_id": module_id,
            "status": "completed" if video_exists else "not_started",
            "video_exists": video_exists
        }
    return job

@api_router.api_route("/videos/{module_id}/file", methods=["GET", "HEAD"])
async def serve_module_video_file(module_id: str, request: Request):
    """Serve video file for a module with range request support"""
    from starlette.responses import StreamingResponse
    import os as os_module
    
    # Check multiple video locations
    video_paths = [
        Path(f"/app/backend/heygen_videos/{module_id}.mp4"),
        Path(f"/app/generated_videos/{module_id}.mp4"),
    ]
    
    video_path = None
    for vp in video_paths:
        if vp.exists():
            video_path = vp
            break
    
    if not video_path:
        raise HTTPException(status_code=404, detail="Video file not found")
    
    file_size = video_path.stat().st_size
    range_header = request.headers.get("range")
    
    # Handle Range requests for video streaming
    if range_header:
        # Parse Range header: "bytes=0-1023" or "bytes=0-"
        range_match = range_header.replace("bytes=", "").split("-")
        start = int(range_match[0]) if range_match[0] else 0
        end = int(range_match[1]) if range_match[1] else file_size - 1
        
        # Ensure valid range
        if start >= file_size:
            raise HTTPException(status_code=416, detail="Range not satisfiable")
        if end >= file_size:
            end = file_size - 1
        
        content_length = end - start + 1
        
        def iter_file():
            with open(video_path, "rb") as f:
                f.seek(start)
                remaining = content_length
                while remaining > 0:
                    chunk_size = min(8192, remaining)
                    data = f.read(chunk_size)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data
        
        return StreamingResponse(
            iter_file(),
            status_code=206,
            media_type="video/mp4",
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
                "Content-Type": "video/mp4",
            }
        )
    
    # No Range header - return StreamingResponse for inline display
    def iter_full_file():
        with open(video_path, "rb") as f:
            while chunk := f.read(65536):
                yield chunk
    
    return StreamingResponse(
        iter_full_file(),
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Content-Type": "video/mp4",
            "Access-Control-Allow-Origin": "*",
        }
    )

@api_router.get("/video/queue-status")
async def get_video_queue_status():
    """Get video generation queue status"""
    from video_generator import VideoGenerationQueue
    queue = VideoGenerationQueue(db)
    return await queue.get_queue_status()

@api_router.post("/video/generate-course/{course_id}")
async def generate_course_videos(course_id: str, background_tasks: BackgroundTasks):
    """Generate videos for all modules in a course"""
    from video_generator import VideoGenerationQueue
    
    modules = await db.modules.find({"courseId": course_id}, {"_id": 0}).to_list(100)
    if not modules:
        raise HTTPException(status_code=404, detail="No modules found for course")
    
    queue = VideoGenerationQueue(db)
    queued = []
    
    for module in modules:
        module_id = module["module_id"]
        script = await db.module_scripts.find_one({"module_id": module_id})
        if script:
            await queue.enqueue(module_id)
            queued.append(module_id)
    
    if queued:
        background_tasks.add_task(queue.process_queue)
    
    return {"message": f"Queued {len(queued)} videos for generation", "modules": queued}

@api_router.post("/content/generate-all-mcq")
async def generate_all_mcq(count_per_course: int = 200):
    """
    Generate MCQ for all courses using non-blocking job runner.
    Uses ProcessPoolExecutor to prevent API blocking.
    """
    from job_runner import get_job_runner, JobConfig
    
    # Configure the job runner
    runner = get_job_runner(db)
    runner.config.questions_per_course = count_per_course
    
    # Start the bulk MCQ generation job
    job = await runner.start_mcq_generation()
    
    return {
        "message": "MCQ generation started for all courses",
        "job_id": job["job_id"],
        "status": job["status"],
        "created_at": job["created_at"]
    }

@api_router.post("/video/generate-all")
async def generate_all_videos(background_tasks: BackgroundTasks):
    """Generate videos for all modules in background"""
    from video_generator import VideoGenerationQueue
    
    modules = await db.modules.find({}, {"_id": 0, "module_id": 1}).to_list(300)
    
    task_id = f"bulk_video_{uuid.uuid4().hex[:8]}"
    await db.bulk_tasks.insert_one({
        "task_id": task_id,
        "type": "video_generation",
        "total_modules": len(modules),
        "queued": 0,
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat()
    })
    
    queue = VideoGenerationQueue(db)
    queued_count = 0
    
    for module in modules:
        module_id = module["module_id"]
        script = await db.module_scripts.find_one({"module_id": module_id})
        if script:
            await queue.enqueue(module_id)
            queued_count += 1
    
    await db.bulk_tasks.update_one(
        {"task_id": task_id},
        {"$set": {"queued": queued_count}}
    )
    
    background_tasks.add_task(queue.process_queue)
    
    return {"message": "Video generation started", "task_id": task_id, "queued": queued_count}

@api_router.get("/bulk-tasks/{task_id}")
async def get_bulk_task_status(task_id: str):
    """Get status of a bulk task"""
    task = await db.bulk_tasks.find_one({"task_id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

# ==================== JOB RUNNER ADMIN ROUTES ====================

@api_router.get("/admin/jobs")
async def get_all_jobs():
    """Get status of all jobs in the system"""
    from job_runner import get_job_runner
    runner = get_job_runner(db)
    return await runner.get_all_jobs_status()

@api_router.get("/admin/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get detailed status of a specific job"""
    from job_runner import get_job_runner
    runner = get_job_runner(db)
    job = await runner.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@api_router.post("/admin/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a running or queued job"""
    from job_runner import get_job_runner
    runner = get_job_runner(db)
    success = await runner.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot cancel job - either not found or already completed")
    return {"message": f"Job {job_id} cancelled", "job_id": job_id}

@api_router.post("/admin/mcq/start")
async def admin_start_mcq_generation(course_id: Optional[str] = None, questions_per_course: int = 200):
    """
    Admin endpoint to start MCQ generation.
    - If course_id provided: generates for single course
    - If no course_id: generates for all courses (bulk)
    """
    from job_runner import get_job_runner
    runner = get_job_runner(db)
    runner.config.questions_per_course = questions_per_course
    
    try:
        job = await runner.start_mcq_generation(course_id)
        return {
            "message": "MCQ generation started" + (f" for course {course_id}" if course_id else " for all courses"),
            "job": job
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@api_router.get("/admin/mcq/progress")
async def get_mcq_generation_progress():
    """Get detailed progress of MCQ generation jobs"""
    from job_runner import get_job_runner, JobType, JobStatus
    runner = get_job_runner(db)
    
    # Get all MCQ-related jobs
    bulk_jobs = await runner.get_jobs_by_type(JobType.BULK_MCQ)
    single_jobs = await runner.get_jobs_by_type(JobType.MCQ_GENERATION)
    
    # Get current running job
    running = [j for j in bulk_jobs + single_jobs if j["status"] == JobStatus.RUNNING]
    
    # Get overall MCQ stats
    total_courses = await db.courses.count_documents({})
    mcq_by_course = await db.mcq_questions.aggregate([
        {"$group": {"_id": "$course_id", "count": {"$sum": 1}}}
    ]).to_list(100)
    courses_with_mcq = len([c for c in mcq_by_course if c["count"] >= 200])
    total_mcq = sum(c["count"] for c in mcq_by_course)
    
    return {
        "overall": {
            "total_questions": total_mcq,
            "courses_complete": courses_with_mcq,
            "total_courses": total_courses,
            "target_questions": total_courses * 200,
            "percentage": (courses_with_mcq / total_courses * 100) if total_courses > 0 else 0
        },
        "current_job": running[0] if running else None,
        "recent_jobs": sorted(bulk_jobs + single_jobs, key=lambda x: x.get("updated_at", ""), reverse=True)[:10]
    }

@api_router.get("/admin/decisions")
async def get_decision_log(limit: int = 50, component: Optional[str] = None, job_id: Optional[str] = None):
    """Get decision log entries for audit/debugging"""
    from decision_logger import get_decision_logger
    dl = get_decision_logger(db)
    
    if job_id:
        decisions = await dl.get_by_job(job_id)
    else:
        decisions = await dl.get_recent(limit=limit, component=component)
    
    return {"decisions": decisions, "count": len(decisions)}

@api_router.post("/admin/scripts/start")
async def admin_start_script_generation(course_id: Optional[str] = None):
    """Start script generation for one or all courses"""
    from job_runner import get_job_runner
    runner = get_job_runner(db)
    
    try:
        job = await runner.start_script_generation(course_id)
        return {
            "message": "Script generation started" + (f" for course {course_id}" if course_id else " for all modules"),
            "job": job
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@api_router.get("/admin/scripts/progress")
async def get_script_generation_progress():
    """Get detailed progress of script generation"""
    from job_runner import get_job_runner, JobType, JobStatus
    runner = get_job_runner(db)
    
    bulk_jobs = await runner.get_jobs_by_type(JobType.BULK_SCRIPT)
    single_jobs = await runner.get_jobs_by_type(JobType.SCRIPT_GENERATION)
    
    running = [j for j in bulk_jobs + single_jobs if j["status"] == JobStatus.RUNNING]
    
    total_modules = await db.modules.count_documents({})
    scripts_count = await db.module_scripts.count_documents({})
    
    return {
        "overall": {
            "total_scripts": scripts_count,
            "total_modules": total_modules,
            "percentage": (scripts_count / total_modules * 100) if total_modules > 0 else 0
        },
        "current_job": running[0] if running else None,
        "recent_jobs": sorted(bulk_jobs + single_jobs, key=lambda x: x.get("updated_at", ""), reverse=True)[:10]
    }

# ==================== SEQUENTIAL MCQ GENERATOR (NEW) ====================

@api_router.post("/admin/simple-mcq/start")
async def start_simple_mcq(university: str = "UG"):
    """Start simple MCQ generation - ensures 200 per course before moving on.
    university: 'UG' for University of Georgia only, 'NVU' for NVU, or None for default (UG + NVU non-Medicine)
    """
    from simple_mcq_generator import get_simple_generator
    generator = get_simple_generator(db)
    
    # Stop any existing generation
    generator.stop()
    await asyncio.sleep(1)
    generator._stop = False
    
    # Run in background with filter
    asyncio.create_task(generator.generate_all_courses(university_filter=university if university != "ALL" else None))
    
    return {"status": "started", "message": f"Simple MCQ generator started for {university} courses"}

@api_router.post("/admin/simple-mcq/stop")
async def stop_simple_mcq():
    """Stop MCQ generation"""
    from simple_mcq_generator import get_simple_generator
    generator = get_simple_generator(db)
    generator.stop()
    
    # Update job status
    await db.jobs.update_many(
        {"job_type": "simple_mcq", "status": "running"},
        {"$set": {"status": "stopped", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"status": "stopped", "message": "MCQ generation stopped"}

@api_router.get("/admin/simple-mcq/status")
async def get_simple_mcq_status():
    """Get simple MCQ status"""
    # Find most recent job by started_at
    jobs = await db.jobs.find(
        {"job_type": "simple_mcq"}, 
        {"_id": 0}
    ).sort("started_at", -1).limit(1).to_list(1)
    job = jobs[0] if jobs else None
    
    # Count courses with 200+
    pipeline = [
        {"$group": {"_id": "$course_id", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gte": 200}}}
    ]
    completed = await db.mcq_questions.aggregate(pipeline).to_list(200)
    
    total_mcq = await db.mcq_questions.count_documents({})
    
    return {
        "job": job,
        "courses_with_200": len(completed),
        "total_mcq": total_mcq,
        "completed_courses": [c["_id"] for c in completed]
    }

@api_router.post("/admin/sequential-mcq/start")
async def start_sequential_mcq(send_emails: bool = True):
    """
    Start sequential MCQ generation - processes ONE course at a time:
    1. Generate all 200 questions for a course
    2. Verify quality (answer distribution balanced)
    3. Only after verification passes, move to next course
    """
    from sequential_mcq_generator import get_sequential_generator
    from email_notifier import get_email_scheduler
    
    generator = get_sequential_generator(db)
    result = await generator.start_sequential_generation()
    
    # Start email notifications if requested
    if send_emails:
        scheduler = get_email_scheduler(db)
        await scheduler.start()
        result["email_notifications"] = "enabled"
    
    return result

@api_router.get("/admin/sequential-mcq/status")
async def get_sequential_mcq_status():
    """Get status of sequential MCQ generation"""
    from sequential_mcq_generator import get_sequential_generator
    generator = get_sequential_generator(db)
    status = await generator.get_status()
    
    # Add distribution stats per course
    pipeline = [
        {"$group": {
            "_id": {"course": "$course_id", "answer": "$correct_answer"},
            "count": {"$sum": 1}
        }}
    ]
    dist_raw = await db.mcq_questions.aggregate(pipeline).to_list(500)
    
    # Organize by course
    course_stats = {}
    for item in dist_raw:
        course = item["_id"]["course"]
        answer = item["_id"]["answer"]
        if course not in course_stats:
            course_stats[course] = {"total": 0, "A": 0, "B": 0, "C": 0, "D": 0}
        course_stats[course][answer] = item["count"]
        course_stats[course]["total"] += item["count"]
    
    # Calculate percentages and verify status
    verified_courses = []
    unverified_courses = []
    
    for course_id, stats in course_stats.items():
        total = stats["total"]
        if total >= 200:
            dist = {
                "course_id": course_id,
                "total": total,
                "A": round(stats["A"] / total * 100, 1),
                "B": round(stats["B"] / total * 100, 1),
                "C": round(stats["C"] / total * 100, 1),
                "D": round(stats["D"] / total * 100, 1)
            }
            # Check if balanced (20-30% each)
            is_balanced = all(20 <= dist[l] <= 30 for l in ["A", "B", "C", "D"])
            dist["balanced"] = is_balanced
            if is_balanced:
                verified_courses.append(dist)
            else:
                unverified_courses.append(dist)
    
    status["verified_courses_detail"] = verified_courses
    status["unverified_courses_detail"] = unverified_courses
    
    return status

@api_router.post("/admin/sequential-mcq/cancel")
async def cancel_sequential_mcq():
    """Cancel sequential MCQ generation"""
    from sequential_mcq_generator import get_sequential_generator
    from email_notifier import get_email_scheduler
    
    generator = get_sequential_generator(db)
    generator.cancel()
    
    # Stop email notifications
    scheduler = get_email_scheduler(db)
    await scheduler.stop()
    
    # Also update job status
    await db.jobs.update_many(
        {"job_type": "sequential_mcq", "status": "running"},
        {"$set": {"status": "cancelled", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Sequential MCQ generation cancelled"}

@api_router.post("/admin/email/send-now")
async def send_progress_email_now():
    """Send a progress email immediately"""
    from email_notifier import send_progress_email
    success = await send_progress_email(db)
    if success:
        return {"message": "Email sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send email - check RESEND_API_KEY")

@api_router.post("/admin/email/start-notifications")
async def start_email_notifications():
    """Start email notifications every 2 hours"""
    from email_notifier import get_email_scheduler
    scheduler = get_email_scheduler(db)
    await scheduler.start()
    return {"message": "Email notifications started - sending every 2 hours to adnan232383@gmail.com"}

@api_router.post("/admin/email/stop-notifications")
async def stop_email_notifications():
    """Stop email notifications"""
    from email_notifier import get_email_scheduler
    scheduler = get_email_scheduler(db)
    await scheduler.stop()
    return {"message": "Email notifications stopped"}

@api_router.post("/admin/verify-course/{course_id}")
async def verify_single_course(course_id: str):
    """Verify and fix distribution for a single course"""
    from sequential_mcq_generator import get_sequential_generator
    generator = get_sequential_generator(db)
    
    course = await db.courses.find_one({"external_id": course_id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    is_valid = await generator._verify_course_quality(course_id, course["course_name"])
    
    return {
        "course_id": course_id,
        "verified": is_valid,
        "message": "Course verified and balanced" if is_valid else "Course needs more questions or redistribution"
    }

# ==================== FULL COURSE PIPELINE ====================

@api_router.post("/admin/full-course/{course_id}")
async def run_full_course_pipeline(course_id: str):
    """
    Run complete pipeline for a single course:
    1. Generate 200 MCQ questions
    2. Verify quality
    3. Generate avatar scripts
    4. Generate avatar videos with Sora 2
    """
    from full_course_pipeline import get_pipeline
    pipeline = get_pipeline(db)
    
    # Run in background
    async def run_pipeline():
        result = await pipeline.process_single_course(course_id)
        await db.pipeline_results.update_one(
            {"course_id": course_id},
            {"$set": result},
            upsert=True
        )
    
    asyncio.create_task(run_pipeline())
    
    return {
        "message": f"Full pipeline started for course {course_id}",
        "course_id": course_id,
        "steps": ["MCQ Generation", "Quality Verification", "Script Generation", "Video Generation"]
    }

@api_router.get("/admin/full-course/{course_id}/status")
async def get_full_course_status(course_id: str):
    """Get status of full course pipeline"""
    course = await db.courses.find_one({"external_id": course_id}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Get counts
    mcq_count = await db.mcq_questions.count_documents({"course_id": course_id})
    modules = await db.modules.find({"courseId": course_id}, {"_id": 0, "module_id": 1}).to_list(20)
    script_count = await db.module_scripts.count_documents({"course_id": course_id})
    video_count = await db.module_videos.count_documents({"course_id": course_id, "status": "completed"})
    
    # Get distribution
    dist = await db.mcq_questions.aggregate([
        {"$match": {"course_id": course_id}},
        {"$group": {"_id": "$correct_answer", "count": {"$sum": 1}}}
    ]).to_list(10)
    
    distribution = {}
    for d in dist:
        if mcq_count > 0:
            distribution[d["_id"]] = round((d["count"] / mcq_count) * 100, 1)
    
    return {
        "course_id": course_id,
        "course_name": course["course_name"],
        "mcq": {
            "count": mcq_count,
            "target": 200,
            "complete": mcq_count >= 200,
            "distribution": distribution
        },
        "scripts": {
            "count": script_count,
            "target": len(modules),
            "complete": script_count >= len(modules)
        },
        "videos": {
            "count": video_count,
            "target": len(modules),
            "complete": video_count >= len(modules)
        }
    }

@api_router.get("/generation-progress")
async def get_generation_progress():
    """Get overall generation progress"""
    total_courses = await db.courses.count_documents({})
    total_modules = await db.modules.count_documents({})
    
    # MCQ progress
    mcq_by_course = await db.mcq_questions.aggregate([
        {"$group": {"_id": "$course_id", "count": {"$sum": 1}}}
    ]).to_list(100)
    courses_with_mcq = len([c for c in mcq_by_course if c["count"] >= 200])
    total_mcq = sum(c["count"] for c in mcq_by_course)
    
    # Video progress
    videos_completed = await db.module_videos.count_documents({"status": "completed"})
    
    # Scripts progress
    scripts_count = await db.module_scripts.count_documents({})
    
    return {
        "mcq": {
            "total_questions": total_mcq,
            "courses_with_200_mcq": courses_with_mcq,
            "total_courses": total_courses,
            "target": total_courses * 200
        },
        "videos": {
            "completed": videos_completed,
            "total_modules": total_modules
        },
        "scripts": {
            "completed": scripts_count,
            "total_modules": total_modules
        }
    }

@api_router.get("/stats/dashboard")
async def get_dashboard_stats():
    """Get comprehensive dashboard statistics - optimized single query"""
    # Get all universities
    universities = await db.universities.find({}, {"_id": 0}).to_list(100)
    
    # Get MCQ counts grouped by course_id prefix (university)
    mcq_pipeline = [
        {"$group": {"_id": "$course_id", "count": {"$sum": 1}}},
    ]
    mcq_by_course = await db.mcq_questions.aggregate(mcq_pipeline).to_list(1000)
    
    # Create a dict for fast lookup
    course_mcq = {item["_id"]: item["count"] for item in mcq_by_course}
    
    # Get courses and their mcq_count
    courses = await db.courses.find({}, {"_id": 0, "external_id": 1, "course_name": 1, "university_id": 1, "mcq_count": 1}).to_list(1000)
    
    # Group courses by university
    uni_data = {}
    for uni in universities:
        uni_id = uni["external_id"]
        # Get prefix for this university
        prefix_map = {
            "UG_TBILISI": "UG_",
            "NVU": "NVU_",
            "IASI_ROMANIA": "IASI_",
            "AAU_AMMAN": "AAU_",
            "NAJAH": "NAJAH_"
        }
        prefix = prefix_map.get(uni_id, f"{uni_id}_")
        
        # Filter courses for this university
        uni_courses = [c for c in courses if c["external_id"].startswith(prefix)]
        
        # Calculate stats
        total_questions = 0
        courses_300 = 0
        courses_200 = 0
        courses_under = 0
        
        course_details = []
        for c in uni_courses:
            # Use actual count from questions collection
            actual_count = course_mcq.get(c["external_id"], 0)
            total_questions += actual_count
            
            if actual_count >= 300:
                courses_300 += 1
            elif actual_count >= 200:
                courses_200 += 1
            else:
                courses_under += 1
            
            course_details.append({
                "external_id": c["external_id"],
                "course_name": c["course_name"],
                "mcq_count": actual_count
            })
        
        completion_rate = (courses_300 / len(uni_courses) * 100) if uni_courses else 0
        
        uni_data[uni_id] = {
            **uni,
            "totalCourses": len(uni_courses),
            "totalQuestions": total_questions,
            "coursesWith300": courses_300,
            "coursesWith200": courses_200,
            "coursesUnder200": courses_under,
            "completionRate": completion_rate,
            "courses": course_details
        }
    
    # Calculate totals
    totals = {
        "totalUniversities": len(universities),
        "totalCourses": len(courses),
        "totalQuestions": sum(u["totalQuestions"] for u in uni_data.values()),
        "coursesWith300": sum(u["coursesWith300"] for u in uni_data.values()),
        "coursesWith200": sum(u["coursesWith200"] for u in uni_data.values()),
        "coursesUnder200": sum(u["coursesUnder200"] for u in uni_data.values()),
    }
    totals["overallCompletion"] = (totals["coursesWith300"] / totals["totalCourses"] * 100) if totals["totalCourses"] > 0 else 0
    
    return {
        "universities": list(uni_data.values()),
        "totals": totals
    }

@api_router.post("/content/generate-mcq/{course_id}")
async def generate_mcq_for_course(course_id: str, count: int = 200):
    """Generate MCQ questions for a course using AI"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    import json
    
    course = await db.courses.find_one({"external_id": course_id}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    course_name = course["course_name"]
    description = course.get("course_description", "")
    
    questions = []
    batch_size = 25
    batches = (count + batch_size - 1) // batch_size
    
    for batch_num in range(batches):
        remaining = min(batch_size, count - len(questions))
        if remaining <= 0:
            break
        
        try:
            chat = LlmChat(
                api_key=api_key,
                session_id=f"mcq_{uuid.uuid4().hex[:8]}",
                system_message="""You are a medical education expert creating high-quality MCQ questions.
Create questions suitable for medical/pharmacy board exam preparation.
Always return valid JSON array."""
            ).with_model("openai", "gpt-5.2")
            
            prompt = f"""Generate {remaining} multiple-choice questions for:
Course: {course_name}
Description: {description}
Batch: {batch_num + 1}/{batches}

For each question provide:
1. question: The question text
2. option_a, option_b, option_c, option_d: Four answer options
3. correct_answer: The correct option letter (A, B, C, or D)
4. explanation: Detailed explanation (2-3 sentences)
5. difficulty: easy, medium, or hard

Format as JSON array ONLY, no other text:
[{{"question": "...", "option_a": "...", "option_b": "...", "option_c": "...", "option_d": "...", "correct_answer": "A", "explanation": "...", "difficulty": "medium"}}]

Create clinically relevant questions. Vary difficulty: 30% easy, 50% medium, 20% hard.
Cover different aspects of {course_name}."""
            
            response = await chat.send_message(UserMessage(text=prompt))
            
            # Parse JSON response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                batch_questions = json.loads(response[json_start:json_end])
                for q in batch_questions:
                    q["question_id"] = f"q_{course_id}_{len(questions):03d}"
                    q["course_id"] = course_id
                    q["topic"] = course_name
                    q["created_at"] = datetime.now(timezone.utc).isoformat()
                    questions.append(q)
                    
            logger.info(f"Generated batch {batch_num + 1}/{batches} for {course_id}: {len(batch_questions)} questions")
            
        except Exception as e:
            logger.error(f"Failed to generate MCQ batch {batch_num}: {e}")
            continue
    
    if questions:
        # Save to database
        await db.mcq_questions.delete_many({"course_id": course_id})
        await db.mcq_questions.insert_many(questions)
        
        # Update content status
        await db.content_status.update_one(
            {"course_id": course_id},
            {"$set": {"has_mcq": True, "mcq_count": len(questions), "updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
    
    return {
        "message": f"Generated {len(questions)} MCQ questions for {course_name}",
        "course_id": course_id,
        "questions_count": len(questions)
    }

# ==================== AI CHAT ROUTES ====================

@api_router.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest, request: Request):
    """AI Study Assistant chat endpoint"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    # Get user for session tracking
    user = await get_current_user(request)
    session_id = user.user_id if user else f"anon_{uuid.uuid4().hex[:8]}"
    
    # Build context
    course_context = ""
    if chat_request.course_id:
        course = await db.courses.find_one({"external_id": chat_request.course_id}, {"_id": 0})
        content = await db.course_content.find_one({"course_id": chat_request.course_id}, {"_id": 0})
        if course:
            course_context = f"\nCurrent course: {course['course_name']}\nDescription: {course.get('course_description', 'N/A')}"
            if content and content.get("summary"):
                course_context += f"\nCourse Summary: {content['summary']}"
    
    system_message = f"""You are an AI Study Assistant for the University of Georgia (UG) in Tbilisi. 
You help students studying Dentistry and Pharmacy programs.
Be helpful, accurate, and supportive. Explain medical and pharmaceutical concepts clearly.
If asked about topics outside the curriculum, politely redirect to relevant course material.
{course_context}"""
    
    try:
        chat_instance = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message=system_message
        ).with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(text=chat_request.message)
        response = await chat_instance.send_message(user_message)
        
        return ChatResponse(response=response)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="AI service error")

# ==================== SEED DATA ROUTE ====================

@api_router.post("/seed")
async def seed_database():
    """Seed the database with initial data"""
    # University
    university = {
        "external_id": "UG_TBILISI",
        "name": "University of Georgia (UG)",
        "country": "Georgia",
        "city": "Tbilisi",
        "language": "English",
        "type": "Private",
        "description": "International private university in Tbilisi offering English-taught programs for international students, focused on health and applied sciences."
    }
    await db.universities.update_one(
        {"external_id": university["external_id"]},
        {"$set": university},
        upsert=True
    )
    
    # Faculties
    faculties = [
        {"external_id": "UG_F_DENT", "university_id": "UG_TBILISI", "name": "Faculty of Dentistry"},
        {"external_id": "UG_F_PHARM", "university_id": "UG_TBILISI", "name": "Faculty of Pharmacy"}
    ]
    for faculty in faculties:
        await db.faculties.update_one(
            {"external_id": faculty["external_id"]},
            {"$set": faculty},
            upsert=True
        )
    
    # Majors
    majors = [
        {
            "external_id": "UG_M_DENT",
            "faculty_id": "UG_F_DENT",
            "name": "Dentistry",
            "degree": "DMD",
            "years": 5,
            "image_url": "https://images.unsplash.com/photo-1643386106343-18d5d3c64d47?crop=entropy&cs=srgb&fm=jpg&q=85"
        },
        {
            "external_id": "UG_M_PHARM",
            "faculty_id": "UG_F_PHARM",
            "name": "Pharmacy",
            "degree": "BPharm",
            "years": 4,
            "image_url": "https://images.unsplash.com/photo-1766297248027-864589dbd336?crop=entropy&cs=srgb&fm=jpg&q=85"
        }
    ]
    for major in majors:
        await db.majors.update_one(
            {"external_id": major["external_id"]},
            {"$set": major},
            upsert=True
        )
    
    # Years
    years_data = [
        # Dentistry Years
        {"external_id": "UG_DENT_Y1", "major_id": "UG_M_DENT", "year_number": 1, "year_title": "Year 1"},
        {"external_id": "UG_DENT_Y2", "major_id": "UG_M_DENT", "year_number": 2, "year_title": "Year 2"},
        {"external_id": "UG_DENT_Y3", "major_id": "UG_M_DENT", "year_number": 3, "year_title": "Year 3"},
        {"external_id": "UG_DENT_Y4", "major_id": "UG_M_DENT", "year_number": 4, "year_title": "Year 4"},
        {"external_id": "UG_DENT_Y5", "major_id": "UG_M_DENT", "year_number": 5, "year_title": "Year 5"},
        # Pharmacy Years
        {"external_id": "UG_PHARM_Y1", "major_id": "UG_M_PHARM", "year_number": 1, "year_title": "Year 1"},
        {"external_id": "UG_PHARM_Y2", "major_id": "UG_M_PHARM", "year_number": 2, "year_title": "Year 2"},
        {"external_id": "UG_PHARM_Y3", "major_id": "UG_M_PHARM", "year_number": 3, "year_title": "Year 3"},
        {"external_id": "UG_PHARM_Y4", "major_id": "UG_M_PHARM", "year_number": 4, "year_title": "Year 4"},
    ]
    for year in years_data:
        await db.years.update_one(
            {"external_id": year["external_id"]},
            {"$set": year},
            upsert=True
        )
    
    # All Courses from the SQL schema
    courses_data = [
        # DENTISTRY YEAR 1
        {"external_id": "UG_DENT_Y1_S1_C01", "year_id": "UG_DENT_Y1", "semester": 1, "course_name": "General Biology", "course_description": "Foundations of cell biology and basic genetics for health sciences."},
        {"external_id": "UG_DENT_Y1_S1_C02", "year_id": "UG_DENT_Y1", "semester": 1, "course_name": "General Chemistry", "course_description": "Basic chemical principles relevant to biomedical sciences."},
        {"external_id": "UG_DENT_Y1_S1_C03", "year_id": "UG_DENT_Y1", "semester": 1, "course_name": "Medical Terminology", "course_description": "Core medical terms and language used in healthcare settings."},
        {"external_id": "UG_DENT_Y1_S1_C04", "year_id": "UG_DENT_Y1", "semester": 1, "course_name": "Human Anatomy I", "course_description": "Introduction to gross anatomy with focus on musculoskeletal system."},
        {"external_id": "UG_DENT_Y1_S1_C05", "year_id": "UG_DENT_Y1", "semester": 1, "course_name": "Physics for Health Sciences", "course_description": "Basic physics concepts relevant to medical and dental applications."},
        {"external_id": "UG_DENT_Y1_S2_C06", "year_id": "UG_DENT_Y1", "semester": 2, "course_name": "Organic Chemistry (Intro)", "course_description": "Introduction to organic chemistry and functional groups in biology."},
        {"external_id": "UG_DENT_Y1_S2_C07", "year_id": "UG_DENT_Y1", "semester": 2, "course_name": "Human Anatomy II", "course_description": "Continuation of anatomy: cardiovascular, respiratory, and nervous basics."},
        {"external_id": "UG_DENT_Y1_S2_C08", "year_id": "UG_DENT_Y1", "semester": 2, "course_name": "Histology & Embryology", "course_description": "Basic tissues and embryologic development with clinical relevance."},
        {"external_id": "UG_DENT_Y1_S2_C09", "year_id": "UG_DENT_Y1", "semester": 2, "course_name": "Biochemistry I", "course_description": "Macromolecules, enzymes, and metabolism fundamentals."},
        {"external_id": "UG_DENT_Y1_S2_C10", "year_id": "UG_DENT_Y1", "semester": 2, "course_name": "Dental Anatomy (Intro)", "course_description": "Tooth morphology, terminology, and basic occlusion concepts."},
        # DENTISTRY YEAR 2
        {"external_id": "UG_DENT_Y2_S1_C01", "year_id": "UG_DENT_Y2", "semester": 1, "course_name": "Physiology", "course_description": "Human organ systems function with emphasis on clinical correlation."},
        {"external_id": "UG_DENT_Y2_S1_C02", "year_id": "UG_DENT_Y2", "semester": 1, "course_name": "Microbiology", "course_description": "Bacteria, viruses, fungi and infection principles in healthcare."},
        {"external_id": "UG_DENT_Y2_S1_C03", "year_id": "UG_DENT_Y2", "semester": 1, "course_name": "Pathology (Intro)", "course_description": "Mechanisms of disease and core pathological processes."},
        {"external_id": "UG_DENT_Y2_S1_C04", "year_id": "UG_DENT_Y2", "semester": 1, "course_name": "Pharmacology (Basics)", "course_description": "Drug mechanisms, adverse effects, and safe use principles."},
        {"external_id": "UG_DENT_Y2_S1_C05", "year_id": "UG_DENT_Y2", "semester": 1, "course_name": "Oral Anatomy & Occlusion", "course_description": "Oral structures and occlusion for restorative foundations."},
        {"external_id": "UG_DENT_Y2_S2_C06", "year_id": "UG_DENT_Y2", "semester": 2, "course_name": "Immunology (Basics)", "course_description": "Immune system foundations and relevance to oral diseases."},
        {"external_id": "UG_DENT_Y2_S2_C07", "year_id": "UG_DENT_Y2", "semester": 2, "course_name": "Preclinical Operative Dentistry I", "course_description": "Intro preclinical restorative techniques and cavity preparation."},
        {"external_id": "UG_DENT_Y2_S2_C08", "year_id": "UG_DENT_Y2", "semester": 2, "course_name": "Dental Materials I", "course_description": "Properties and handling of restorative dental materials."},
        {"external_id": "UG_DENT_Y2_S2_C09", "year_id": "UG_DENT_Y2", "semester": 2, "course_name": "Radiology (Basics)", "course_description": "Dental imaging principles, safety, and interpretation basics."},
        {"external_id": "UG_DENT_Y2_S2_C10", "year_id": "UG_DENT_Y2", "semester": 2, "course_name": "Infection Control & Sterilization", "course_description": "Protocols for sterilization, disinfection, and clinical safety."},
        # DENTISTRY YEAR 3
        {"external_id": "UG_DENT_Y3_S1_C01", "year_id": "UG_DENT_Y3", "semester": 1, "course_name": "Oral Pathology", "course_description": "Oral lesions, diagnosis basics, and clinicopathologic correlation."},
        {"external_id": "UG_DENT_Y3_S1_C02", "year_id": "UG_DENT_Y3", "semester": 1, "course_name": "Periodontology I", "course_description": "Gingiva and periodontal tissues, inflammation, and basic therapy."},
        {"external_id": "UG_DENT_Y3_S1_C03", "year_id": "UG_DENT_Y3", "semester": 1, "course_name": "Endodontics I", "course_description": "Pulp biology, diagnosis, and root canal treatment fundamentals."},
        {"external_id": "UG_DENT_Y3_S1_C04", "year_id": "UG_DENT_Y3", "semester": 1, "course_name": "Prosthodontics I", "course_description": "Fixed/removable prosthodontics foundations and treatment planning."},
        {"external_id": "UG_DENT_Y3_S1_C05", "year_id": "UG_DENT_Y3", "semester": 1, "course_name": "Operative Dentistry II", "course_description": "Advanced restorative concepts and clinical techniques."},
        {"external_id": "UG_DENT_Y3_S2_C06", "year_id": "UG_DENT_Y3", "semester": 2, "course_name": "Pediatric Dentistry I", "course_description": "Child behavior management, prevention, and basic pediatric care."},
        {"external_id": "UG_DENT_Y3_S2_C07", "year_id": "UG_DENT_Y3", "semester": 2, "course_name": "Orthodontics I", "course_description": "Growth, development, malocclusion basics, and appliances introduction."},
        {"external_id": "UG_DENT_Y3_S2_C08", "year_id": "UG_DENT_Y3", "semester": 2, "course_name": "Oral Surgery I", "course_description": "Exodontia basics, surgical principles, and complications."},
        {"external_id": "UG_DENT_Y3_S2_C09", "year_id": "UG_DENT_Y3", "semester": 2, "course_name": "Dental Materials II", "course_description": "Advanced materials selection and clinical performance."},
        {"external_id": "UG_DENT_Y3_S2_C10", "year_id": "UG_DENT_Y3", "semester": 2, "course_name": "Clinical Skills Lab", "course_description": "Simulation-based clinical skills and integrated preclinical practice."},
        # DENTISTRY YEAR 4
        {"external_id": "UG_DENT_Y4_S1_C01", "year_id": "UG_DENT_Y4", "semester": 1, "course_name": "Periodontology II", "course_description": "Advanced periodontal therapy and maintenance planning."},
        {"external_id": "UG_DENT_Y4_S1_C02", "year_id": "UG_DENT_Y4", "semester": 1, "course_name": "Endodontics II", "course_description": "Complex endodontic cases and advanced techniques."},
        {"external_id": "UG_DENT_Y4_S1_C03", "year_id": "UG_DENT_Y4", "semester": 1, "course_name": "Prosthodontics II", "course_description": "Complex prosthodontic rehabilitation and case management."},
        {"external_id": "UG_DENT_Y4_S1_C04", "year_id": "UG_DENT_Y4", "semester": 1, "course_name": "Oral Medicine", "course_description": "Systemic conditions with oral manifestations and differential diagnosis."},
        {"external_id": "UG_DENT_Y4_S1_C05", "year_id": "UG_DENT_Y4", "semester": 1, "course_name": "Radiology (Advanced)", "course_description": "Advanced imaging interpretation and diagnostic decision-making."},
        {"external_id": "UG_DENT_Y4_S2_C06", "year_id": "UG_DENT_Y4", "semester": 2, "course_name": "Pediatric Dentistry II", "course_description": "Advanced pediatric care and interceptive approaches."},
        {"external_id": "UG_DENT_Y4_S2_C07", "year_id": "UG_DENT_Y4", "semester": 2, "course_name": "Orthodontics II", "course_description": "Diagnosis, treatment planning and appliance selection for cases."},
        {"external_id": "UG_DENT_Y4_S2_C08", "year_id": "UG_DENT_Y4", "semester": 2, "course_name": "Oral Surgery II", "course_description": "Advanced oral surgery topics and perioperative management."},
        {"external_id": "UG_DENT_Y4_S2_C09", "year_id": "UG_DENT_Y4", "semester": 2, "course_name": "Restorative Dentistry Clinic", "course_description": "Supervised clinical restorative practice and documentation."},
        {"external_id": "UG_DENT_Y4_S2_C10", "year_id": "UG_DENT_Y4", "semester": 2, "course_name": "Evidence-Based Dentistry", "course_description": "Critical appraisal, research interpretation, and clinical decision-making."},
        # DENTISTRY YEAR 5
        {"external_id": "UG_DENT_Y5_S1_C01", "year_id": "UG_DENT_Y5", "semester": 1, "course_name": "Comprehensive Care Clinic", "course_description": "Integrated patient care across disciplines with full treatment planning."},
        {"external_id": "UG_DENT_Y5_S1_C02", "year_id": "UG_DENT_Y5", "semester": 1, "course_name": "Complex Cases Seminar", "course_description": "Case-based discussions and multidisciplinary problem solving."},
        {"external_id": "UG_DENT_Y5_S1_C03", "year_id": "UG_DENT_Y5", "semester": 1, "course_name": "Implantology (Intro/Clinical)", "course_description": "Implant foundations, indications, and clinical workflow overview."},
        {"external_id": "UG_DENT_Y5_S1_C04", "year_id": "UG_DENT_Y5", "semester": 1, "course_name": "Emergency Dentistry", "course_description": "Management of dental emergencies and acute pain/infection."},
        {"external_id": "UG_DENT_Y5_S1_C05", "year_id": "UG_DENT_Y5", "semester": 1, "course_name": "Practice Management & Ethics", "course_description": "Clinical management, ethics, professionalism, and patient communication."},
        {"external_id": "UG_DENT_Y5_S2_C06", "year_id": "UG_DENT_Y5", "semester": 2, "course_name": "Aesthetic Dentistry", "course_description": "Esthetic principles and minimally invasive cosmetic procedures."},
        {"external_id": "UG_DENT_Y5_S2_C07", "year_id": "UG_DENT_Y5", "semester": 2, "course_name": "Public Health Dentistry", "course_description": "Community dentistry, prevention programs, and epidemiology basics."},
        {"external_id": "UG_DENT_Y5_S2_C08", "year_id": "UG_DENT_Y5", "semester": 2, "course_name": "Research Project / Case Report", "course_description": "Structured research or case report with academic writing."},
        {"external_id": "UG_DENT_Y5_S2_C09", "year_id": "UG_DENT_Y5", "semester": 2, "course_name": "Electives", "course_description": "Student-selected elective modules aligned with interests."},
        {"external_id": "UG_DENT_Y5_S2_C10", "year_id": "UG_DENT_Y5", "semester": 2, "course_name": "Final Review & Board Prep", "course_description": "High-yield review and exam preparation strategy and practice."},
        # PHARMACY YEAR 1
        {"external_id": "UG_PHARM_Y1_S1_C01", "year_id": "UG_PHARM_Y1", "semester": 1, "course_name": "General Chemistry", "course_description": "Basic chemical principles for biomedical and pharmaceutical sciences."},
        {"external_id": "UG_PHARM_Y1_S1_C02", "year_id": "UG_PHARM_Y1", "semester": 1, "course_name": "Biology / Cell Biology", "course_description": "Cell structure, genetics basics, and human biology foundations."},
        {"external_id": "UG_PHARM_Y1_S1_C03", "year_id": "UG_PHARM_Y1", "semester": 1, "course_name": "Mathematics / Biostatistics", "course_description": "Basic statistics and calculations used in health sciences."},
        {"external_id": "UG_PHARM_Y1_S1_C04", "year_id": "UG_PHARM_Y1", "semester": 1, "course_name": "Medical Terminology", "course_description": "Healthcare terminology used in clinical and pharmacy settings."},
        {"external_id": "UG_PHARM_Y1_S1_C05", "year_id": "UG_PHARM_Y1", "semester": 1, "course_name": "Introduction to Pharmacy", "course_description": "Pharmacy roles, workflow, dosage forms, and ethics overview."},
        {"external_id": "UG_PHARM_Y1_S2_C06", "year_id": "UG_PHARM_Y1", "semester": 2, "course_name": "Organic Chemistry I", "course_description": "Organic structures, reactions, and pharmaceutical relevance basics."},
        {"external_id": "UG_PHARM_Y1_S2_C07", "year_id": "UG_PHARM_Y1", "semester": 2, "course_name": "Anatomy & Physiology I", "course_description": "Organ systems foundations for understanding drug effects."},
        {"external_id": "UG_PHARM_Y1_S2_C08", "year_id": "UG_PHARM_Y1", "semester": 2, "course_name": "Anatomy & Physiology II", "course_description": "Continuation of physiology with clinical correlation."},
        {"external_id": "UG_PHARM_Y1_S2_C09", "year_id": "UG_PHARM_Y1", "semester": 2, "course_name": "Biochemistry I", "course_description": "Metabolism and biomolecules relevant to pharmacology."},
        {"external_id": "UG_PHARM_Y1_S2_C10", "year_id": "UG_PHARM_Y1", "semester": 2, "course_name": "Communication Skills for Healthcare", "course_description": "Patient-centered communication and professional documentation."},
        # PHARMACY YEAR 2
        {"external_id": "UG_PHARM_Y2_S1_C01", "year_id": "UG_PHARM_Y2", "semester": 1, "course_name": "Pharmaceutical Chemistry", "course_description": "Chemical basis of drugs, structure-activity, and quality concepts."},
        {"external_id": "UG_PHARM_Y2_S1_C02", "year_id": "UG_PHARM_Y2", "semester": 1, "course_name": "Pharmaceutics I", "course_description": "Dosage forms, formulations, stability, and basic compounding."},
        {"external_id": "UG_PHARM_Y2_S1_C03", "year_id": "UG_PHARM_Y2", "semester": 1, "course_name": "Microbiology", "course_description": "Microbial principles relevant to infection and antimicrobial therapy."},
        {"external_id": "UG_PHARM_Y2_S1_C04", "year_id": "UG_PHARM_Y2", "semester": 1, "course_name": "Pharmacology I", "course_description": "Core mechanisms of drug action and receptor principles."},
        {"external_id": "UG_PHARM_Y2_S1_C05", "year_id": "UG_PHARM_Y2", "semester": 1, "course_name": "Analytical Chemistry", "course_description": "Analytical methods used in drug testing and quality control."},
        {"external_id": "UG_PHARM_Y2_S2_C06", "year_id": "UG_PHARM_Y2", "semester": 2, "course_name": "Pharmaceutics II", "course_description": "Advanced formulations, manufacturing principles, and biopharmaceutics."},
        {"external_id": "UG_PHARM_Y2_S2_C07", "year_id": "UG_PHARM_Y2", "semester": 2, "course_name": "Immunology", "course_description": "Immune mechanisms and immunopharmacology foundations."},
        {"external_id": "UG_PHARM_Y2_S2_C08", "year_id": "UG_PHARM_Y2", "semester": 2, "course_name": "Pathophysiology", "course_description": "Disease processes and how they guide pharmacotherapy."},
        {"external_id": "UG_PHARM_Y2_S2_C09", "year_id": "UG_PHARM_Y2", "semester": 2, "course_name": "Pharmacognosy (Natural Products)", "course_description": "Medicinal plants, natural products, and safety/efficacy basics."},
        {"external_id": "UG_PHARM_Y2_S2_C10", "year_id": "UG_PHARM_Y2", "semester": 2, "course_name": "Pharmacy Law & Ethics", "course_description": "Basics, regulations and ethical principles for pharmacy practice."},
        # PHARMACY YEAR 3
        {"external_id": "UG_PHARM_Y3_S1_C01", "year_id": "UG_PHARM_Y3", "semester": 1, "course_name": "Pharmacology II", "course_description": "Advanced pharmacology across major therapeutic classes."},
        {"external_id": "UG_PHARM_Y3_S1_C02", "year_id": "UG_PHARM_Y3", "semester": 1, "course_name": "Clinical Pharmacokinetics", "course_description": "ADME, dosing, therapeutic drug monitoring, and calculations."},
        {"external_id": "UG_PHARM_Y3_S1_C03", "year_id": "UG_PHARM_Y3", "semester": 1, "course_name": "Therapeutics I (Cardio/Resp)", "course_description": "Evidence-based treatment of cardiovascular and respiratory disorders."},
        {"external_id": "UG_PHARM_Y3_S1_C04", "year_id": "UG_PHARM_Y3", "semester": 1, "course_name": "Hospital Pharmacy", "course_description": "Medication systems, safety, sterile products, and inpatient workflow."},
        {"external_id": "UG_PHARM_Y3_S1_C05", "year_id": "UG_PHARM_Y3", "semester": 1, "course_name": "Drug Information", "course_description": "Evaluating evidence, answering clinical questions, and resources."},
        {"external_id": "UG_PHARM_Y3_S2_C06", "year_id": "UG_PHARM_Y3", "semester": 2, "course_name": "Therapeutics II (Endocrine/GI)", "course_description": "Pharmacotherapy of endocrine and gastrointestinal conditions."},
        {"external_id": "UG_PHARM_Y3_S2_C07", "year_id": "UG_PHARM_Y3", "semester": 2, "course_name": "Clinical Microbiology & Antibiotics", "course_description": "Microbiology diagnostics and rational antibiotic selection."},
        {"external_id": "UG_PHARM_Y3_S2_C08", "year_id": "UG_PHARM_Y3", "semester": 2, "course_name": "Community Pharmacy Practice", "course_description": "OTC counseling, minor ailments, and workflow management."},
        {"external_id": "UG_PHARM_Y3_S2_C09", "year_id": "UG_PHARM_Y3", "semester": 2, "course_name": "Research Methods", "course_description": "Study design, statistics basics, and research interpretation."},
        {"external_id": "UG_PHARM_Y3_S2_C10", "year_id": "UG_PHARM_Y3", "semester": 2, "course_name": "Patient Counseling", "course_description": "Communication for adherence, safety, and shared decision-making."},
        # PHARMACY YEAR 4
        {"external_id": "UG_PHARM_Y4_S1_C01", "year_id": "UG_PHARM_Y4", "semester": 1, "course_name": "Therapeutics III (Neuro/Psych)", "course_description": "Pharmacotherapy for neurological and psychiatric disorders."},
        {"external_id": "UG_PHARM_Y4_S1_C02", "year_id": "UG_PHARM_Y4", "semester": 1, "course_name": "Therapeutics IV (Oncology/ID)", "course_description": "Cancer pharmacotherapy and complex infectious diseases treatment."},
        {"external_id": "UG_PHARM_Y4_S1_C03", "year_id": "UG_PHARM_Y4", "semester": 1, "course_name": "Advanced Pharmacy Practice", "course_description": "Advanced case management and interprofessional collaboration."},
        {"external_id": "UG_PHARM_Y4_S1_C04", "year_id": "UG_PHARM_Y4", "semester": 1, "course_name": "Pharmacy Management", "course_description": "Operations, leadership, finance basics, and service quality."},
        {"external_id": "UG_PHARM_Y4_S1_C05", "year_id": "UG_PHARM_Y4", "semester": 1, "course_name": "Pharmacovigilance", "course_description": "Adverse drug reactions, reporting systems, and risk management."},
        {"external_id": "UG_PHARM_Y4_S2_C06", "year_id": "UG_PHARM_Y4", "semester": 2, "course_name": "Clinical Case Studies", "course_description": "Case-based integrated pharmacotherapy with documentation."},
        {"external_id": "UG_PHARM_Y4_S2_C07", "year_id": "UG_PHARM_Y4", "semester": 2, "course_name": "Internship / Rotation (Hospital)", "course_description": "Supervised rotation in hospital pharmacy practice."},
        {"external_id": "UG_PHARM_Y4_S2_C08", "year_id": "UG_PHARM_Y4", "semester": 2, "course_name": "Internship / Rotation (Community)", "course_description": "Supervised rotation in community pharmacy practice."},
        {"external_id": "UG_PHARM_Y4_S2_C09", "year_id": "UG_PHARM_Y4", "semester": 2, "course_name": "Electives", "course_description": "Student-selected elective modules aligned with interests."},
        {"external_id": "UG_PHARM_Y4_S2_C10", "year_id": "UG_PHARM_Y4", "semester": 2, "course_name": "Final Review & Licensing Prep", "course_description": "High-yield review and practice for licensing-style exams."},
    ]
    
    for course in courses_data:
        await db.courses.update_one(
            {"external_id": course["external_id"]},
            {"$set": course},
            upsert=True
        )
    
    # Seed Modules for each course (2-3 modules per course)
    modules_templates = {
        "General Biology": [
            {"title": "Cell Structure & Function", "description": "Introduction to cell biology, organelles, and cellular processes.", "topics": ["Cell membrane", "Nucleus", "Mitochondria", "Cell division"], "duration_hours": 4},
            {"title": "Genetics Fundamentals", "description": "Basic genetics, DNA, RNA, and gene expression.", "topics": ["DNA structure", "Replication", "Transcription", "Translation"], "duration_hours": 5},
            {"title": "Evolution & Diversity", "description": "Principles of evolution and biological diversity.", "topics": ["Natural selection", "Adaptation", "Speciation"], "duration_hours": 3},
        ],
        "General Chemistry": [
            {"title": "Atomic Structure", "description": "Atoms, electrons, and periodic table fundamentals.", "topics": ["Atomic models", "Electron configuration", "Periodic trends"], "duration_hours": 4},
            {"title": "Chemical Bonding", "description": "Ionic, covalent, and metallic bonds.", "topics": ["Ionic bonds", "Covalent bonds", "Lewis structures"], "duration_hours": 4},
            {"title": "Stoichiometry", "description": "Chemical calculations and reactions.", "topics": ["Mole concept", "Balancing equations", "Limiting reagents"], "duration_hours": 5},
        ],
        "Human Anatomy I": [
            {"title": "Skeletal System", "description": "Bones, joints, and skeletal anatomy.", "topics": ["Bone structure", "Axial skeleton", "Appendicular skeleton"], "duration_hours": 6},
            {"title": "Muscular System", "description": "Muscle types, structure, and function.", "topics": ["Skeletal muscles", "Muscle contraction", "Major muscle groups"], "duration_hours": 5},
            {"title": "Integumentary System", "description": "Skin structure and functions.", "topics": ["Epidermis", "Dermis", "Skin appendages"], "duration_hours": 3},
        ],
        "Physiology": [
            {"title": "Cardiovascular Physiology", "description": "Heart function and blood circulation.", "topics": ["Cardiac cycle", "Blood pressure", "ECG basics"], "duration_hours": 6},
            {"title": "Respiratory Physiology", "description": "Breathing mechanics and gas exchange.", "topics": ["Ventilation", "Gas transport", "Respiratory control"], "duration_hours": 5},
            {"title": "Renal Physiology", "description": "Kidney function and fluid balance.", "topics": ["Nephron function", "Filtration", "Acid-base balance"], "duration_hours": 5},
        ],
        "Pharmacology I": [
            {"title": "Pharmacokinetics", "description": "Drug absorption, distribution, metabolism, and excretion.", "topics": ["ADME", "Bioavailability", "Half-life"], "duration_hours": 5},
            {"title": "Pharmacodynamics", "description": "Drug-receptor interactions and mechanisms.", "topics": ["Receptors", "Agonists/Antagonists", "Dose-response"], "duration_hours": 5},
            {"title": "Autonomic Pharmacology", "description": "Drugs affecting the autonomic nervous system.", "topics": ["Cholinergics", "Adrenergics", "Blockers"], "duration_hours": 6},
        ],
    }
    
    # Default module template for courses not in the templates
    default_modules = [
        {"title": "Introduction & Fundamentals", "description": "Core concepts and foundational principles.", "topics": ["Key terms", "Basic principles", "Overview"], "duration_hours": 4},
        {"title": "Clinical Applications", "description": "Practical applications and case studies.", "topics": ["Case studies", "Clinical scenarios", "Practice"], "duration_hours": 5},
        {"title": "Advanced Topics & Review", "description": "Advanced concepts and exam preparation.", "topics": ["Complex topics", "Integration", "Review"], "duration_hours": 4},
    ]
    
    modules_count = 0
    for course in courses_data:
        course_id = course["external_id"]
        course_name = course["course_name"]
        
        # Get modules template or use default
        course_modules = modules_templates.get(course_name, default_modules)
        
        for idx, mod in enumerate(course_modules):
            module_data = {
                "module_id": f"{course_id}_M{idx+1:02d}",
                "courseId": course_id,
                "title": mod["title"],
                "description": mod["description"],
                "order": idx + 1,
                "duration_hours": mod.get("duration_hours", 4),
                "topics": mod.get("topics", []),
            }
            await db.modules.update_one(
                {"module_id": module_data["module_id"]},
                {"$set": module_data},
                upsert=True
            )
            modules_count += 1
    
    # ==================== SEED MCQ QUESTIONS, SUMMARIES & SCRIPTS ====================
    
    # Sample MCQ questions for different subjects
    mcq_templates = {
        "General Biology": [
            {"question": "Which organelle is responsible for ATP production in eukaryotic cells?", "option_a": "Nucleus", "option_b": "Mitochondria", "option_c": "Ribosome", "option_d": "Golgi apparatus", "correct_answer": "B", "explanation": "Mitochondria are the 'powerhouse of the cell' where oxidative phosphorylation produces ATP through the electron transport chain.", "difficulty": "easy"},
            {"question": "What is the primary function of the rough endoplasmic reticulum?", "option_a": "Lipid synthesis", "option_b": "Protein synthesis and modification", "option_c": "DNA replication", "option_d": "Cell division", "correct_answer": "B", "explanation": "The rough ER is studded with ribosomes and is the site of protein synthesis for secreted and membrane proteins.", "difficulty": "easy"},
            {"question": "Which phase of the cell cycle is characterized by DNA replication?", "option_a": "G1 phase", "option_b": "S phase", "option_c": "G2 phase", "option_d": "M phase", "correct_answer": "B", "explanation": "The S (Synthesis) phase is when DNA replication occurs, resulting in chromosome duplication before cell division.", "difficulty": "medium"},
            {"question": "In Mendelian genetics, what ratio is expected in the F2 generation of a monohybrid cross?", "option_a": "1:1", "option_b": "2:1", "option_c": "3:1", "option_d": "1:2:1", "correct_answer": "C", "explanation": "The classic 3:1 phenotypic ratio in F2 results from self-crossing F1 heterozygotes (Aa x Aa → 3 dominant : 1 recessive).", "difficulty": "medium"},
            {"question": "Which type of RNA carries amino acids to the ribosome during translation?", "option_a": "mRNA", "option_b": "tRNA", "option_c": "rRNA", "option_d": "snRNA", "correct_answer": "B", "explanation": "Transfer RNA (tRNA) has an anticodon that pairs with mRNA codons and carries specific amino acids for protein synthesis.", "difficulty": "easy"},
            {"question": "What is the function of telomeres?", "option_a": "Initiate DNA replication", "option_b": "Protect chromosome ends from degradation", "option_c": "Control gene expression", "option_d": "Facilitate crossing over", "correct_answer": "B", "explanation": "Telomeres are repetitive DNA sequences at chromosome ends that protect against degradation and fusion with other chromosomes.", "difficulty": "medium"},
            {"question": "Which enzyme unwinds the DNA double helix during replication?", "option_a": "DNA polymerase", "option_b": "Helicase", "option_c": "Ligase", "option_d": "Primase", "correct_answer": "B", "explanation": "Helicase breaks hydrogen bonds between base pairs, separating the two DNA strands to create replication forks.", "difficulty": "medium"},
            {"question": "What is apoptosis?", "option_a": "Uncontrolled cell growth", "option_b": "Cell migration", "option_c": "Programmed cell death", "option_d": "Cell fusion", "correct_answer": "C", "explanation": "Apoptosis is controlled cell suicide, essential for development, tissue homeostasis, and eliminating damaged cells.", "difficulty": "easy"},
        ],
        "General Chemistry": [
            {"question": "What is the atomic number of carbon?", "option_a": "4", "option_b": "6", "option_c": "8", "option_d": "12", "correct_answer": "B", "explanation": "Carbon has 6 protons in its nucleus, giving it an atomic number of 6. The atomic mass of 12 includes both protons and neutrons.", "difficulty": "easy"},
            {"question": "Which type of bond involves the sharing of electrons?", "option_a": "Ionic bond", "option_b": "Covalent bond", "option_c": "Hydrogen bond", "option_d": "Van der Waals bond", "correct_answer": "B", "explanation": "Covalent bonds form when atoms share electron pairs, as opposed to ionic bonds where electrons are transferred.", "difficulty": "easy"},
            {"question": "What is the pH of a neutral solution at 25°C?", "option_a": "0", "option_b": "5", "option_c": "7", "option_d": "14", "correct_answer": "C", "explanation": "At 25°C, neutral pH is 7 where [H+] = [OH-] = 10^-7 M. Below 7 is acidic, above 7 is basic.", "difficulty": "easy"},
            {"question": "According to the octet rule, how many valence electrons does a stable atom typically have?", "option_a": "2", "option_b": "4", "option_c": "6", "option_d": "8", "correct_answer": "D", "explanation": "The octet rule states that atoms tend to gain, lose, or share electrons to achieve 8 valence electrons (like noble gases).", "difficulty": "easy"},
            {"question": "What type of reaction occurs when an acid reacts with a base?", "option_a": "Oxidation", "option_b": "Reduction", "option_c": "Neutralization", "option_d": "Hydrolysis", "correct_answer": "C", "explanation": "Neutralization reactions occur between acids and bases, producing water and a salt (e.g., HCl + NaOH → NaCl + H2O).", "difficulty": "medium"},
            {"question": "Which element has the highest electronegativity?", "option_a": "Oxygen", "option_b": "Fluorine", "option_c": "Chlorine", "option_d": "Nitrogen", "correct_answer": "B", "explanation": "Fluorine is the most electronegative element (4.0 on Pauling scale) due to its small size and high nuclear charge.", "difficulty": "medium"},
            {"question": "What is the molar mass of water (H2O)?", "option_a": "16 g/mol", "option_b": "18 g/mol", "option_c": "20 g/mol", "option_d": "32 g/mol", "correct_answer": "B", "explanation": "H2O = 2(1) + 16 = 18 g/mol. This is calculated from atomic masses: H=1, O=16.", "difficulty": "easy"},
            {"question": "In a redox reaction, what happens to a substance that is oxidized?", "option_a": "Gains electrons", "option_b": "Loses electrons", "option_c": "Gains protons", "option_d": "Loses protons", "correct_answer": "B", "explanation": "Oxidation Is Loss (OIL) - a substance being oxidized loses electrons and its oxidation state increases.", "difficulty": "medium"},
        ],
        "Physiology": [
            {"question": "What is the normal resting heart rate for adults?", "option_a": "40-50 bpm", "option_b": "60-100 bpm", "option_c": "100-120 bpm", "option_d": "120-140 bpm", "correct_answer": "B", "explanation": "Normal adult resting heart rate is 60-100 beats per minute. Athletes may have lower rates due to conditioning.", "difficulty": "easy"},
            {"question": "Which part of the brain controls breathing?", "option_a": "Cerebrum", "option_b": "Cerebellum", "option_c": "Medulla oblongata", "option_d": "Hypothalamus", "correct_answer": "C", "explanation": "The medulla oblongata contains respiratory centers that control the rate and depth of breathing.", "difficulty": "medium"},
            {"question": "What is the primary function of hemoglobin?", "option_a": "Blood clotting", "option_b": "Oxygen transport", "option_c": "Fighting infection", "option_d": "Nutrient absorption", "correct_answer": "B", "explanation": "Hemoglobin in red blood cells binds oxygen in the lungs and releases it in tissues, enabling aerobic metabolism.", "difficulty": "easy"},
            {"question": "Which hormone regulates blood glucose levels by promoting glucose uptake?", "option_a": "Glucagon", "option_b": "Insulin", "option_c": "Cortisol", "option_d": "Epinephrine", "correct_answer": "B", "explanation": "Insulin, secreted by pancreatic beta cells, lowers blood glucose by promoting cellular uptake and glycogen storage.", "difficulty": "easy"},
            {"question": "What is the functional unit of the kidney?", "option_a": "Alveolus", "option_b": "Nephron", "option_c": "Hepatocyte", "option_d": "Neuron", "correct_answer": "B", "explanation": "The nephron filters blood and produces urine. Each kidney contains about 1 million nephrons.", "difficulty": "easy"},
            {"question": "Which phase of the cardiac cycle represents ventricular contraction?", "option_a": "Diastole", "option_b": "Systole", "option_c": "Isovolumic relaxation", "option_d": "Atrial kick", "correct_answer": "B", "explanation": "Systole is the phase of ventricular contraction when blood is ejected into the aorta and pulmonary artery.", "difficulty": "medium"},
            {"question": "What neurotransmitter is released at the neuromuscular junction?", "option_a": "Dopamine", "option_b": "Serotonin", "option_c": "Acetylcholine", "option_d": "GABA", "correct_answer": "C", "explanation": "Acetylcholine is released from motor neurons and binds to nicotinic receptors on muscle fibers, causing contraction.", "difficulty": "medium"},
            {"question": "Where does gas exchange occur in the lungs?", "option_a": "Bronchi", "option_b": "Bronchioles", "option_c": "Alveoli", "option_d": "Trachea", "correct_answer": "C", "explanation": "Alveoli are thin-walled air sacs where O2 diffuses into blood and CO2 diffuses out, facilitated by surfactant.", "difficulty": "easy"},
        ],
        "Pharmacology I": [
            {"question": "What does the term 'bioavailability' refer to?", "option_a": "Drug potency", "option_b": "Fraction of drug reaching systemic circulation", "option_c": "Drug half-life", "option_d": "Drug toxicity", "correct_answer": "B", "explanation": "Bioavailability (F) is the fraction of administered drug that reaches systemic circulation unchanged. IV drugs have F=100%.", "difficulty": "medium"},
            {"question": "Which route of administration provides 100% bioavailability?", "option_a": "Oral", "option_b": "Subcutaneous", "option_c": "Intravenous", "option_d": "Intramuscular", "correct_answer": "C", "explanation": "Intravenous administration bypasses absorption barriers, delivering 100% of the drug directly to systemic circulation.", "difficulty": "easy"},
            {"question": "What is the primary organ responsible for drug metabolism?", "option_a": "Kidney", "option_b": "Liver", "option_c": "Lungs", "option_d": "Intestine", "correct_answer": "B", "explanation": "The liver is the primary site of drug metabolism, containing cytochrome P450 enzymes that biotransform drugs.", "difficulty": "easy"},
            {"question": "What does a drug's half-life (t½) represent?", "option_a": "Time to reach maximum effect", "option_b": "Time for plasma concentration to decrease by 50%", "option_c": "Duration of drug action", "option_d": "Time to complete elimination", "correct_answer": "B", "explanation": "Half-life is the time required for plasma drug concentration to decrease by 50%. It determines dosing frequency.", "difficulty": "medium"},
            {"question": "Which type of drug-receptor interaction produces no biological response?", "option_a": "Agonist", "option_b": "Partial agonist", "option_c": "Antagonist", "option_d": "Inverse agonist", "correct_answer": "C", "explanation": "Antagonists bind receptors without activating them, blocking the action of endogenous ligands or agonist drugs.", "difficulty": "medium"},
            {"question": "What is first-pass metabolism?", "option_a": "Drug absorption in stomach", "option_b": "Drug metabolism before reaching systemic circulation", "option_c": "Drug excretion by kidneys", "option_d": "Drug distribution to tissues", "correct_answer": "B", "explanation": "First-pass metabolism occurs when orally administered drugs are metabolized by liver/gut before reaching systemic circulation.", "difficulty": "medium"},
            {"question": "Which cytochrome P450 enzyme is responsible for metabolizing most drugs?", "option_a": "CYP1A2", "option_b": "CYP2D6", "option_c": "CYP3A4", "option_d": "CYP2C9", "correct_answer": "C", "explanation": "CYP3A4 metabolizes approximately 50% of all drugs. It's the most abundant CYP enzyme in liver and intestine.", "difficulty": "hard"},
            {"question": "What is an idiosyncratic drug reaction?", "option_a": "Dose-dependent toxicity", "option_b": "Predictable side effect", "option_c": "Unpredictable adverse reaction", "option_d": "Drug-drug interaction", "correct_answer": "C", "explanation": "Idiosyncratic reactions are unpredictable, not dose-dependent, and often due to genetic or immunological factors.", "difficulty": "hard"},
        ],
    }
    
    # Generate MCQ questions for courses
    mcq_count = 0
    for course in courses_data[:20]:  # First 20 courses get full MCQs
        course_id = course["external_id"]
        course_name = course["course_name"]
        
        # Find matching template or use generic
        template_questions = mcq_templates.get(course_name, mcq_templates.get("General Biology", []))
        
        questions_to_insert = []
        for idx in range(min(25, len(template_questions) * 3)):  # Up to 25 questions per course
            base_q = template_questions[idx % len(template_questions)].copy()
            base_q["question_id"] = f"q_{course_id}_{idx:03d}"
            base_q["course_id"] = course_id
            base_q["topic"] = course_name
            base_q["created_at"] = datetime.now(timezone.utc).isoformat()
            questions_to_insert.append(base_q)
        
        if questions_to_insert:
            await db.mcq_questions.delete_many({"course_id": course_id})
            await db.mcq_questions.insert_many(questions_to_insert)
            mcq_count += len(questions_to_insert)
    
    # Generate course summaries
    summaries = {
        "General Biology": """## Learning Objectives
By the end of this course, students will be able to:
- Understand the fundamental principles of cell biology
- Describe the structure and function of cellular organelles
- Explain the mechanisms of DNA replication and gene expression
- Apply knowledge of genetics to clinical scenarios

## Course Overview
This foundational course introduces students to the cellular and molecular basis of life. Beginning with cell structure and organelle function, we explore how cells maintain homeostasis, communicate with their environment, and reproduce.

### Cell Structure and Function
Cells are the basic units of life. Eukaryotic cells, found in animals and plants, contain membrane-bound organelles including the nucleus (genetic material), mitochondria (energy production), endoplasmic reticulum (protein/lipid synthesis), and Golgi apparatus (protein modification and sorting).

### Genetics and Heredity
The principles of Mendelian inheritance form the basis of understanding genetic disorders. DNA replication ensures faithful transmission of genetic information, while transcription and translation convert genetic code into functional proteins.

### Clinical Applications
Understanding cell biology is essential for comprehending disease mechanisms, drug actions, and diagnostic techniques in medicine and dentistry.

## Key Takeaways
- Cell structure determines function
- DNA → RNA → Protein (Central Dogma)
- Genetic principles explain inheritance patterns
- Cell biology underlies all medical sciences""",
        
        "Physiology": """## Learning Objectives
Upon completion, students will be able to:
- Describe the physiological basis of major organ system functions
- Explain homeostatic mechanisms and feedback loops
- Interpret physiological parameters in clinical contexts
- Apply physiological principles to patient care

## Course Overview
Human physiology examines how the body's systems work together to maintain homeostasis. This course covers cardiovascular, respiratory, renal, nervous, and endocrine physiology with emphasis on clinical correlations.

### Cardiovascular Physiology
The heart generates pressure to circulate blood, delivering oxygen and nutrients while removing waste. Understanding cardiac output, blood pressure regulation, and ECG interpretation is fundamental to clinical practice.

### Respiratory Physiology
Gas exchange in the alveoli depends on ventilation-perfusion matching. The respiratory system also plays crucial roles in acid-base balance and host defense.

### Renal Physiology
The kidneys regulate fluid balance, electrolytes, and blood pressure through filtration, reabsorption, and secretion. Understanding nephron function is essential for managing fluid therapy and medications.

## Key Takeaways
- Homeostasis maintains internal stability
- Feedback mechanisms regulate physiological parameters
- Organ systems are interconnected
- Physiological knowledge informs clinical decisions"""
    }
    
    for course in courses_data:
        course_id = course["external_id"]
        course_name = course["course_name"]
        
        summary = summaries.get(course_name)
        if not summary:
            # Generate generic summary
            summary = f"""## {course_name}

### Learning Objectives
- Master the fundamental concepts of {course_name.lower()}
- Apply theoretical knowledge to clinical scenarios
- Develop critical thinking skills in the subject area

### Course Overview
This course provides comprehensive coverage of {course_name.lower()}, establishing a strong foundation for advanced studies and clinical practice.

{course.get('course_description', '')}

### Key Takeaways
- Strong foundation in {course_name.lower()}
- Clinical relevance and applications
- Preparation for advanced courses"""
        
        content = {
            "course_id": course_id,
            "summary": summary,
            "sources": [
                {"topic": course_name, "type": "textbook", "concepts": ["Core concepts", "Clinical applications"]},
                {"topic": f"{course_name} research", "type": "literature", "concepts": ["Recent advances", "Evidence-based practice"]}
            ],
            "status": "published",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.course_content.update_one({"course_id": course_id}, {"$set": content}, upsert=True)
    
    # Generate module scripts
    script_template = """# {module_title}

[INTRODUCTION]
Welcome to this module on {module_title}. In the next 12 minutes, we'll explore the key concepts that will form the foundation of your understanding in this area.

[PAUSE]

## Learning Objectives
By the end of this session, you'll be able to:
- Define and explain core terminology related to {module_title}
- Identify key principles and their clinical applications
- Apply this knowledge to practical scenarios

[PAUSE]

## Section 1: Fundamentals

Let's begin with the basic concepts. {topic_1} is essential because it forms the foundation of our understanding.

[EMPHASIS] Remember: Understanding these fundamentals is crucial for clinical practice.

In clinical settings, you'll encounter these principles daily. For example, when assessing patients, knowledge of {topic_1} helps you interpret findings accurately.

[PAUSE]

## Section 2: Clinical Applications

Now let's explore how these concepts apply in practice. Consider a patient presenting with relevant symptoms - your understanding of {topic_2} guides your diagnostic approach.

The key steps in clinical application include:
1. Assessment based on foundational knowledge
2. Integration of findings
3. Evidence-based decision making

[EMPHASIS] Clinical reasoning depends on solid foundational understanding.

[PAUSE]

## Section 3: Advanced Concepts

Building on our foundation, let's examine {topic_3}. These advanced concepts connect what we've learned to more complex clinical scenarios.

Healthcare professionals must integrate multiple concepts when managing patient care. This requires:
- Strong foundational knowledge
- Critical thinking skills
- Continuous learning mindset

[PAUSE]

## Summary

Today we covered:
- Core concepts of {module_title}
- Clinical applications and relevance
- Advanced topics for deeper understanding

[EMPHASIS] Key takeaway: These fundamentals will serve you throughout your career.

In our next module, we'll build on these concepts as we explore more advanced topics.

Thank you for your attention. Keep reviewing these materials and don't hesitate to ask questions!

[END]"""

    scripts_count = 0
    for course in courses_data[:20]:  # First 20 courses get scripts
        course_id = course["external_id"]
        course_modules = await db.modules.find({"courseId": course_id}, {"_id": 0}).to_list(10)
        
        for module in course_modules:
            topics = module.get("topics", ["Core concepts", "Applications", "Advanced topics"])
            script_text = script_template.format(
                module_title=module["title"],
                topic_1=topics[0] if len(topics) > 0 else "fundamental concepts",
                topic_2=topics[1] if len(topics) > 1 else "clinical applications",
                topic_3=topics[2] if len(topics) > 2 else "advanced topics"
            )
            
            word_count = len(script_text.split())
            script = {
                "script_id": f"script_{module['module_id']}",
                "module_id": module["module_id"],
                "course_id": course_id,
                "script_text": script_text,
                "word_count": word_count,
                "estimated_duration_minutes": round(word_count / 150, 1),
                "status": "published",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.module_scripts.update_one({"module_id": module["module_id"]}, {"$set": script}, upsert=True)
            scripts_count += 1
    
    # Set content status for seeded courses
    for course in courses_data[:20]:
        await db.content_status.update_one(
            {"course_id": course["external_id"]},
            {"$set": {
                "course_id": course["external_id"],
                "status": "published",
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "published_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
    
    return {
        "message": "Database seeded successfully", 
        "courses_count": len(courses_data), 
        "modules_count": modules_count,
        "mcq_count": mcq_count,
        "scripts_count": scripts_count
    }

# ==================== ROOT AND STATUS ====================

@api_router.get("/")
async def root():
    return {"message": "UG University Assistant API", "version": "1.0.0"}

@api_router.get("/health")
async def health():
    return {"status": "healthy"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
