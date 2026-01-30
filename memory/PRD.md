# UG University Assistant - PRD

## Original Problem Statement
Build a University Assistant platform for University of Georgia (UG) in Tbilisi with:
- Dentistry program (5 years, DMD)
- Pharmacy program (4 years, BPharm)
- Course catalog browsing (Major → Year → Semester)
- AI Study Assistant with GPT-5.2
- Emergent Google OAuth authentication
- Light/dark theme toggle
- Auto-generated content: Summaries, MCQ Questions (200/course), Module Scripts (~12 min)
- Avatar video generation from scripts using Sora 2

## User Personas
1. **International Medical Students** - Primary users browsing Dentistry curriculum
2. **International Pharmacy Students** - Primary users browsing Pharmacy curriculum
3. **Prospective Students** - Exploring programs before enrollment

## Core Requirements
- [x] Browse courses by Major → Year → Semester
- [x] View course details and descriptions
- [x] AI-powered study assistant
- [x] Google OAuth authentication
- [x] Light/dark theme toggle
- [x] Responsive design for mobile students
- [x] Auto-generated course content via RAG + AI
- [x] MCQ Quiz functionality (200 questions/course)
- [x] Module scripts for avatar videos
- [x] Video generation with Sora 2
- [x] **Non-blocking background job system** (Jan 30, 2025)

## What's Been Implemented

### Phase 1 MVP (Jan 2025)
- FastAPI server with MongoDB
- 90 courses seeded (50 Dentistry + 40 Pharmacy)
- 270 modules with topic breakdown
- Emergent Google OAuth integration
- GPT-5.2 AI chat endpoint

### Phase 2 - Content Generation (Jan 2025)
- **Content Generator Service**: RAG-based content generation with GPT-5.2
- **MCQ Questions**: Bulk generation endpoint for 200 questions/course
- **Course Summaries**: AI-generated summaries for all courses
- **Module Scripts**: 270 avatar video scripts (~12 min each)
- **Content Status Workflow**: pending → generating → reviewed → published
- **Progress Tracking**: `/admin/progress` page for monitoring

### Phase 3 - Video Generation (Jan 2025)
- **Video Generator Service**: Sora 2 integration for avatar videos
- **Bulk Generation**: Background task queue for all modules
- **Video API Endpoints**: Generate, status, retrieve videos

### Phase 4 - Job Runner System (Jan 30, 2025) ✅ NEW
- **Non-Blocking Architecture**: Implemented `asyncio.to_thread()` to run LLM calls in separate thread pool
- **Job Status Tracking**: queued → running → done → failed states
- **Progress Updates**: Real-time progress tracking with course names
- **Idempotency Checks**: Prevents duplicate jobs for same resource
- **Per-Course Locks**: Prevents concurrent runs on same course
- **Job Resume on Restart**: Automatically resumes interrupted jobs on server restart
- **Admin UI Controls**: Start/Progress/Cancel buttons in `/admin/progress`
- **Rate Limiting**: 30 API calls per minute
- **Modular Design**: Ready for Celery/ARQ swap later

## API Endpoints

### Content Generation
- `POST /api/content/generate-all-mcq` - Generate MCQ for all courses (uses job runner)
- `POST /api/content/generate-mcq/{course_id}` - Generate MCQ for single course
- `GET /api/generation-progress` - Get overall progress

### Job Management (NEW)
- `GET /api/admin/jobs` - Get all jobs status
- `GET /api/admin/jobs/{job_id}` - Get specific job details
- `POST /api/admin/jobs/{job_id}/cancel` - Cancel a job
- `POST /api/admin/mcq/start` - Start MCQ generation (single or bulk)
- `GET /api/admin/mcq/progress` - Get detailed MCQ progress

### Video Generation
- `POST /api/video/generate-all` - Generate videos for all modules
- `POST /api/video/generate-course/{course_id}` - Generate videos for course
- `GET /api/video/{module_id}` - Get video info

## Tech Stack
- **Frontend**: React 19, Tailwind CSS, Shadcn UI
- **Backend**: FastAPI, Python 3.11
- **Database**: MongoDB
- **AI**: GPT-5.2 via Emergent LLM Key
- **Video**: Sora 2 via Emergent LLM Key
- **Auth**: Emergent Google OAuth
- **Background Jobs**: Custom JobRunner with `asyncio.to_thread()` (swappable to Celery/ARQ)

## Architecture

### Job Runner System
```
/app/backend/
├── job_runner.py        # Non-blocking job runner with ProcessPoolExecutor
│   ├── JobRunner        # Main runner class
│   ├── JobLockManager   # Per-resource locking
│   ├── RateLimiter      # API rate limiting
│   └── JobStatus        # queued/running/done/failed/cancelled
└── server.py            # FastAPI with lifespan events for job resumption
```

### Key Design Decisions
1. **Thread-based LLM calls**: Uses `asyncio.to_thread()` to run LLM calls without blocking event loop
2. **Database-backed state**: All job state stored in MongoDB for persistence across restarts
3. **Automatic resumption**: Server startup resumes any interrupted running/queued jobs
4. **Modular architecture**: JobRunner interface designed for easy swap to Celery/ARQ

## Upcoming Tasks
1. **(P1) Complete Bulk MCQ Generation**: Currently running, generating ~18,000 questions
2. **(P1) Generate All Avatar Scripts**: After MCQ completion
3. **(P1) Generate All Avatar Videos**: Using Sora 2 after scripts

## Future Tasks
- **(P2) Build Full Admin Panel**: Content review/approval workflow
- **(P2) Student Progress Tracking**: Track module/quiz completion
- **(P3) Migrate to Celery/ARQ**: For production scaling (after first university complete)

## Cost Estimate
- MCQ (18,000 questions): ~$150-200
- Videos (270 modules): ~$80-100
- Total: ~$250-300
