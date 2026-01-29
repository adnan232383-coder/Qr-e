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

## User Personas
1. **International Medical Students** - Primary users browsing Dentistry curriculum
2. **International Pharmacy Students** - Primary users browsing Pharmacy curriculum
3. **Prospective Students** - Exploring programs before enrollment

## Core Requirements (Static)
- [x] Browse courses by Major → Year → Semester
- [x] View course details and descriptions
- [x] AI-powered study assistant
- [x] Google OAuth authentication
- [x] Light/dark theme toggle
- [x] Responsive design for mobile students
- [x] Auto-generated course content via RAG + AI
- [x] MCQ Quiz functionality
- [x] Module scripts for avatar videos

## What's Been Implemented

### Phase 1 MVP (Jan 2025)
- FastAPI server with MongoDB
- 90 courses seeded (50 Dentistry + 40 Pharmacy)
- 270 modules with topic breakdown
- Emergent Google OAuth integration
- GPT-5.2 AI chat endpoint

### Phase 2 - Content Generation (Jan 2025)
- **Content Generator Service**: RAG-based content generation
- **MCQ Questions**: 480 questions with explanations (24/course for first 20 courses)
- **Course Summaries**: AI-generated or template summaries for all courses
- **Module Scripts**: 60 avatar video scripts (~12 min each)
- **Content Status Workflow**: pending → generating → reviewed → published
- **Quiz Interface**: Start quiz, select answer, submit, see explanation, track score
- **Scripts Display**: Full avatar scripts with word count and duration

### Frontend Features
- Course detail page with 4 tabs: Overview, Modules, Quiz, Scripts
- Content status badge (Published/Pending/Generating)
- Generate Content CTA for courses without content
- Real-time status polling during generation
- Quiz with difficulty breakdown (Easy/Medium/Hard)
- Module scripts with expandable view

## Content Generation System
- **Sources**: AI-generated topic research
- **Summary**: 800-1200 words with learning objectives
- **MCQ**: 25 questions per course batch, varied difficulty
- **Scripts**: ~300 words per module (~2-12 min duration)
- **Status Tracking**: All content has status workflow
- **Logs**: Generation events logged per course

## Prioritized Backlog

### P0 (Critical) - Complete
- [x] Course catalog browsing
- [x] AI Study Assistant
- [x] Authentication
- [x] Content generation system
- [x] MCQ quiz functionality
- [x] Module scripts

### P1 (High Priority) - Phase 3
- [ ] Scale MCQ to 200 questions per course
- [ ] Video generation from scripts
- [ ] Student progress tracking
- [ ] Exam practice mode with timer

### P2 (Medium Priority) - Future
- [ ] Study groups/collaboration
- [ ] Note-taking per course
- [ ] Calendar integration
- [ ] Push notifications

## Tech Stack
- **Frontend**: React 19, Tailwind CSS, Shadcn UI
- **Backend**: FastAPI, Python 3.11
- **Database**: MongoDB
- **AI**: GPT-5.2 via Emergent LLM Key
- **Auth**: Emergent Google OAuth

## Next Tasks
1. Scale MCQ generation to 200 questions per course
2. Integrate video avatar generation for scripts
3. Add student progress tracking dashboard
4. Implement exam mode with timer and scoring
