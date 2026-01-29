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

### Current Generation Status (In Progress)
- MCQ Generation: Running in background for all 90 courses
- Target: 18,000 MCQ questions (200 × 90 courses)
- Video Generation: Ready to start after MCQ completion

## API Endpoints

### Content Generation
- `POST /api/content/generate-all-mcq` - Generate MCQ for all courses
- `POST /api/content/generate-mcq/{course_id}` - Generate MCQ for single course
- `GET /api/generation-progress` - Get overall progress

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

## Cost Estimate
- MCQ (18,000 questions): ~$150-200
- Videos (270 modules): ~$80-100
- Total: ~$250-300
