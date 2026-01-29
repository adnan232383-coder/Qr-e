from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="UG University Assistant API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
async def get_courses(year_id: str, semester: Optional[int] = None):
    """Get all courses for a year, optionally filtered by semester"""
    query = {"year_id": year_id}
    if semester:
        query["semester"] = semester
    
    courses = await db.courses.find(query, {"_id": 0}).to_list(100)
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
    
    return {"message": "Database seeded successfully", "courses_count": len(courses_data), "modules_count": modules_count}

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
