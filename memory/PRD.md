# UG University Assistant - PRD

## Original Problem Statement
Build a University Assistant platform for University of Georgia (UG) in Tbilisi with:
- Dentistry program (5 years, DMD)
- Pharmacy program (4 years, BPharm)
- Course catalog browsing (Major → Year → Semester)
- AI Study Assistant with GPT-5.2
- Emergent Google OAuth authentication
- Auto-generated content: Summaries, MCQ Questions (200/course), Module Scripts (~12 min)
- Avatar video generation from scripts using Sora 2

## Architecture

### Backend (`/app/backend/`)
```
server.py              # FastAPI app, routes
job_runner.py          # Non-blocking background job system
decision_logger.py     # Autonomous decision audit logging
content_generator.py   # Content generation logic
video_generator.py     # Sora 2 video generation
```

### Job Runner System
- **Non-blocking**: Uses `asyncio.to_thread()` for LLM calls
- **Status tracking**: queued → running → done → failed
- **Progress updates**: Real-time with current item
- **Idempotency**: Prevents duplicate jobs
- **Per-resource locking**: Prevents concurrent runs
- **Auto-resume**: Resumes interrupted jobs on restart
- **Decision logging**: All autonomous choices logged

### Content Generation Pipeline
1. **MCQ Generation** (200 questions/course × 90 courses = 18,000)
2. **Summary Generation** (800-1200 words per course)
3. **Script Generation** (~1800 words/~12 min per module × 270 modules)
4. **Video Generation** (Sora 2, after scripts complete)

## API Endpoints

### Job Management
- `GET /api/admin/jobs` - All jobs status
- `GET /api/admin/jobs/{job_id}` - Job details
- `POST /api/admin/jobs/{job_id}/cancel` - Cancel job
- `GET /api/admin/decisions` - Decision audit log

### MCQ Generation
- `POST /api/admin/mcq/start` - Start bulk MCQ
- `GET /api/admin/mcq/progress` - MCQ progress

### Script Generation
- `POST /api/admin/scripts/start` - Start bulk scripts
- `GET /api/admin/scripts/progress` - Script progress

### Video Generation
- `POST /api/video/generate-all` - Start bulk videos

## Current Status (Jan 30, 2025)

### In Progress
- MCQ generation running: 480/18,000 (2.7%)
- API responsive during generation (~80ms)

### Completed
- ✅ Non-blocking job runner
- ✅ Decision logging system
- ✅ Admin UI with controls
- ✅ Script generation endpoint
- ✅ Course pages handle all statuses

### Pending
- [ ] Complete MCQ generation
- [ ] Generate all module scripts (210 remaining)
- [ ] Generate avatar videos with Sora 2

## Database Collections
- `courses` - 90 courses
- `modules` - 270 modules
- `mcq_questions` - Generated MCQs
- `module_scripts` - Generated scripts
- `module_videos` - Video metadata
- `jobs` - Job tracking
- `job_locks` - Resource locks
- `decision_log` - Autonomous decision audit
- `content_status` - Per-course content status

## Tech Stack
- **Frontend**: React 19, Tailwind CSS, Shadcn UI
- **Backend**: FastAPI, Python 3.11
- **Database**: MongoDB
- **AI**: GPT-5.2 (Emergent LLM Key)
- **Video**: Sora 2 (Emergent LLM Key)
- **Auth**: Emergent Google OAuth
