# MCQ Generation Platform - PRD

## Original Problem Statement
Generate 200+ MCQ questions for courses across two universities:
- **University of Georgia (UG)**: 92 courses (Dentistry + Pharmacy)
- **New Vision University (NVU)**: 71 courses (50 Medicine, 12 Dentistry, 9 Pharmacy)

## Key Requirements
1. Each course must have at least 200 MCQs
2. No duplicate questions within a course
3. Balanced answer distribution (20-30% each for A, B, C, D)
4. NVU Medicine: User provides JSON files manually (2 courses/day)

## Current Status (Dec 2025)

### Completed ✅
- [x] NVU Pharmacy: 9/9 courses (3,474 MCQs)
- [x] NVU Dentistry: 12/12 courses 
- [x] Import mechanism for user-provided JSON files
- [x] Multi-university frontend support

### In Progress 🔄
- [ ] UG courses: 24/92 complete (68 remaining)
- [ ] NVU Medicine: 16/50 complete (user provides manually)

### Backlog 📋
- [ ] Avatar/Video generation with Sora 2 (postponed until MCQ complete)

## Architecture

### Backend (FastAPI)
- `/api/admin/simple-mcq/start?university=UG` - Start MCQ generation
- `/api/admin/simple-mcq/stop` - Stop generation
- `/api/admin/simple-mcq/status` - Get generation status
- `/api/courses/{id}/questions` - Get course MCQs

### Database (MongoDB)
- `universities`: University info
- `courses`: Course catalog
- `mcq_questions`: All MCQ questions
- `jobs`: Background job tracking

### Frontend (React)
- Admin dashboard at `/admin/progress`
- University catalog pages
- Course quiz pages

## Import Format for NVU Medicine
```json
[
  {
    "question": "Question text",
    "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
    "correct_answer": "A",
    "difficulty": "easy|medium|hard",
    "explanation": "..."
  }
]
```

## Tech Stack
- Backend: FastAPI + Motor (async MongoDB)
- Frontend: React
- LLM: OpenAI GPT-4o-mini via Emergent LLM Key
