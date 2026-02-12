# Multi-University E-Learning Platform - PRD

## Overview
A comprehensive e-learning platform supporting 5 universities with MCQ questions and educational videos.

## Universities Supported
1. **UG** - University of Georgia (Tbilisi)
2. **NVU** - New Vision University
3. **IASI** - University of Medicine and Pharmacy Iași (Romania)
4. **AAU** - Al-Ahliyya Amman University (Jordan)
5. **NAJAH** - An-Najah National University (Palestine)

## Current Status (Feb 12, 2026)

### Content Statistics
- **Total Universities**: 5
- **Total Courses**: 486
- **Total MCQ Questions**: ~148,000+
- **Courses with 300+ MCQs**: 466+ (96%)
- **Videos Generated**: 1 (test video)
- **HeyGen API Credits**: 39,600 available

### Completed Features
- ✅ University and course catalog
- ✅ MCQ quiz system with explanations
- ✅ Statistics dashboard with charts
- ✅ Module scripts for educational content
- ✅ Video streaming infrastructure (HTTP 206 Range support)
- ✅ HeyGen video generation integration

### In Progress
- 🔄 MCQ generation for remaining 20 UG courses (~5,500 questions)
- 🔄 Video generation for all modules

### Known Limitations
- Playwright headless browser cannot play videos (codec limitation - not a bug)
- Some courses still under 300 MCQ target

## Technical Architecture

### Backend (FastAPI)
- `/api/universities` - List all universities
- `/api/courses` - List all courses
- `/api/courses/{id}/questions` - Get MCQ questions
- `/api/videos/{module_id}/file` - Stream video with Range support (HTTP 206)
- `/api/stats/dashboard` - Dashboard statistics

### Frontend (React)
- Homepage with dynamic stats
- University catalog
- Course detail with tabs (Overview, Modules, Quiz, Scripts)
- Statistics dashboard with Recharts

### Database (MongoDB)
- universities
- courses
- mcq_questions
- modules
- module_scripts
- module_videos

### External Integrations
- **HeyGen API** - Video generation with avatars
- **Emergent LLM** - MCQ question generation

## API Keys
- HeyGen: Configured in backend/.env
- Emergent LLM: Available for AI generation

## Files of Reference
- `/app/backend/server.py` - Main API server
- `/app/backend/heygen_video_creator.py` - HeyGen integration
- `/app/frontend/src/pages/CourseDetail.jsx` - Course view
- `/app/frontend/src/pages/StatsDashboard.jsx` - Dashboard

## Next Steps
1. Complete MCQ generation for remaining courses
2. Generate videos for all modules using HeyGen
3. Add subtitles/captions to videos
4. Multi-language support (Hebrew, Arabic)
