# Medical Education E-Learning Platform PRD

## Original Problem Statement
Build a multi-university e-learning platform with auto-playing presentations featuring speaking avatars (HeyGen) in a 50/50 split-screen layout with synchronized narration, subtitles, and professional visual design.

## Target Users
- Medical and pharmacy students
- International students studying at Georgian universities
- Self-paced learners in health sciences

## Core Requirements
1. **Multi-University Support**: 5 universities (UG, NVU, IASI, AAU, NAJAH)
2. **Course Content**: 490+ courses across Dentistry, Pharmacy, Medicine
3. **MCQ System**: 150K+ multiple-choice questions
4. **Presentations**: Auto-playing with speaking avatar
5. **Subtitles**: English + Hebrew translation option
6. **Layout**: 50/50 split (avatar left, slides right)
7. **Audio Control**: Auto-play muted with unmute button

---

## What's Been Implemented

### Date: February 15, 2025

#### Backend APIs (100% functional)
- [x] `/api/universities` - Returns 5 universities
- [x] `/api/courses` - Returns 200 courses
- [x] `/api/courses/{id}/questions` - MCQ questions API
- [x] `/api/avatar-videos/{module_id}` - Video streaming (MP4)
- [x] `/api/audio/{filename}` - Audio streaming (MP3)
- [x] `/api/presentations-50-50/{module_id}` - 50/50 HTML presentation
- [x] `/api/auth/session` - Google OAuth authentication
- [x] `/api/chat` - AI Study Assistant (GPT-5.2)
- [x] Admin MCQ generation endpoints

#### Frontend Pages
- [x] Landing page with stats (490+ courses, 5 unis, 150K+ MCQs)
- [x] University catalog (/university/{id})
- [x] Course detail pages
- [x] Login with Google OAuth
- [x] Dashboard (authenticated users)
- [x] Stats dashboard (/admin/stats)
- [x] Video gallery

#### 50/50 Presentation Features
- [x] Split-screen layout (avatar left 50%, slides right 50%)
- [x] Virtual Instructor badge with live indicator
- [x] CC (Closed Captions) toggle button
- [x] Language selector (English/Hebrew)
- [x] Volume control with slider
- [x] Fullscreen button
- [x] Progress bar with slide indicator (e.g., "1/7")
- [x] Auto-play (muted by default for browser compliance)
- [x] Larger fonts for readability
- [x] Subtitle display synchronized with audio

#### Demo Presentations Available
1. `/api/presentations-50-50/UG_DENT_Y1_S1_C01_M01` - Cell Structure & Function
2. `/api/presentations-50-50/UG_DENT_Y3_S1_C03_M01` - Oral Pathology

#### Content Generated
- 94 courses for UG (University of Georgia)
- 24-300 MCQ questions per course
- Audio narrations for demo modules
- HeyGen avatar videos for demo modules

---

## Testing Status (February 15, 2025)
- **Backend**: 100% (18/18 tests passed)
- **Frontend**: 95% (all major features working)
- **Test report**: `/app/test_reports/iteration_4.json`

---

## Known Limitations
1. **Hebrew subtitles**: Currently placeholder text (not real translations)
2. **Video in Playwright**: Shows black in testing environment (works in real browser)

---

## Prioritized Backlog

### P0 - Critical (User Verification)
- [ ] User confirms demo presentations work in their browser

### P1 - High Priority
- [ ] Implement real Hebrew translation (Google Translate API or Gemini)
- [ ] Expand illustration/image library

### P2 - Medium Priority
- [ ] Generate presentations for all ~490 modules
- [ ] Complete MCQ generation to 200 per course
- [ ] Add more HeyGen avatar videos

### P3 - Future Enhancements
- [ ] Progress tracking per user
- [ ] Quiz mode for MCQ practice
- [ ] Certificate generation
- [ ] Mobile responsive design improvements

---

## Technical Architecture

### Stack
- **Backend**: FastAPI (Python 3.11)
- **Frontend**: React 18 with Tailwind CSS, Shadcn/UI
- **Database**: MongoDB
- **AI**: OpenAI GPT-5.2 via Emergent LLM Key
- **TTS**: OpenAI TTS
- **Avatar**: HeyGen API

### Key Files
```
/app/backend/
├── server.py                    # Main API server
├── presentations/               # Generated HTML presentations
├── audio/                       # MP3 narrations
├── heygen_videos/               # Avatar videos
└── scripts/                     # Generation scripts

/app/frontend/
├── src/pages/                   # React pages
├── src/components/              # Reusable components
└── src/context/                 # Auth, Theme contexts
```

### Environment Variables
- `REACT_APP_BACKEND_URL`: Frontend API base URL
- `MONGO_URL`: MongoDB connection string
- `EMERGENT_LLM_KEY`: Universal AI key
- `HEYGEN_API_KEY`: Avatar video generation

---

## 3rd Party Integrations
1. **OpenAI (GPT-5.2)**: MCQ generation, AI chat assistant
2. **OpenAI TTS**: Audio narration generation
3. **HeyGen**: Speaking avatar video generation
4. **Emergent Google Auth**: User authentication
5. **Potential**: Google Translate API for Hebrew subtitles

---

## Preview URLs
- **App**: https://ug-elearning-core.preview.emergentagent.com/
- **Demo 1**: https://ug-elearning-core.preview.emergentagent.com/api/presentations-50-50/UG_DENT_Y1_S1_C01_M01
- **Demo 2**: https://ug-elearning-core.preview.emergentagent.com/api/presentations-50-50/UG_DENT_Y3_S1_C03_M01
