# UG University Assistant - PRD

## Original Problem Statement
Build a University Assistant platform for University of Georgia (UG) in Tbilisi with:
- Dentistry program (5 years, DMD)
- Pharmacy program (4 years, BPharm)
- Course catalog browsing (Major → Year → Semester)
- AI Study Assistant with GPT-5.2
- Emergent Google OAuth authentication
- Light/dark theme toggle

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

## What's Been Implemented (Phase 1 MVP - Jan 2025)

### Backend
- FastAPI server with MongoDB
- 90 courses seeded (50 Dentistry + 40 Pharmacy)
- RESTful API endpoints: `/api/majors`, `/api/years`, `/api/courses`
- Emergent Google OAuth integration
- GPT-5.2 AI chat endpoint via Emergent LLM key
- Session management with 7-day tokens

### Frontend
- Landing page with hero, stats, program cards
- Course catalog with year sidebar and semester tabs
- Course detail page with summary section
- Floating AI chat widget
- Dashboard for authenticated users
- Login page with Google OAuth
- Light/dark theme toggle

### Design
- Typography: Libre Baskerville (headings) + Manrope (body)
- Colors: Deep Teal primary (#0F766E), warm slate accents
- Professional medical aesthetic
- Glassmorphism for overlays

## Prioritized Backlog

### P0 (Critical) - Complete
- [x] Course catalog browsing
- [x] AI Study Assistant
- [x] Authentication

### P1 (High Priority) - Phase 2
- [ ] Course summaries content (AI-generated)
- [ ] Exam question bank
- [ ] Video lessons integration
- [ ] Student progress tracking

### P2 (Medium Priority) - Future
- [ ] Study groups/collaboration
- [ ] Note-taking per course
- [ ] Calendar integration for schedules
- [ ] Push notifications for updates

## Next Tasks
1. Populate course summaries using AI
2. Add exam question bank with MCQ practice
3. Implement video lessons with progress tracking
4. Build student dashboard with progress analytics

## Tech Stack
- **Frontend**: React 19, Tailwind CSS, Shadcn UI
- **Backend**: FastAPI, Python 3.11
- **Database**: MongoDB
- **AI**: GPT-5.2 via Emergent LLM Key
- **Auth**: Emergent Google OAuth
