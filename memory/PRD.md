# Educational Video Platform - PRD

## Original Problem Statement
Build a comprehensive educational video platform with AI-generated avatar videos for medical/pharmacy courses.

### Initial Requirements
1. Build courses based on existing MCQ database
2. Each course should have multiple video modules with talking avatars (HeyGen)
3. Videos in English with multi-language subtitles (Hebrew, Arabic, Russian, Romanian)
4. **Visual diversity**: Different avatar styles and presentation formats every 2 modules

## Current Status (Feb 2026)

### Completed ✅
- [x] **Course 1: General Biology (UG_DENT_Y1_S1_C01)** - 8 modules with diverse styles
  - Modules 1-2: Adriana Nurse (Medical Dark)
  - Modules 3-4: Abigail Office (Office Light)
  - Modules 5-6: Adrian Male (Studio Dark)
  - Modules 7-8: Adriana Business (Business Modern)
- [x] Multi-language subtitles (Hebrew, Arabic, Russian, Romanian)
- [x] Video player with subtitle selection
- [x] Style demonstration page (`/styles`)
- [x] Autonomous video generation system

### In Progress 🔄
- [ ] **Course 2: General Chemistry (UG_PHARM_Y1_S1_C01)** - 8 modules generating

### Backlog 📋
- [ ] Internal Medicine I (NVU_MD_Y3_S1_C24) - 500 MCQs
- [ ] Practice Management & Ethics (UG_DENT_Y5_S1_C05) - 452 MCQs
- [ ] Aesthetic Dentistry (UG_DENT_Y5_S2_C06) - 400 MCQs
- [ ] Evidence Based Medicine (NVU_MD_Y2_S2_C23) - 320 MCQs

## Architecture

### Video Generation Pipeline
```
MCQ Questions → Script Generation → HeyGen API → Video Download → Frontend Display
```

### Style Rotation System (APPROVED - Feb 2026)
**Only 2 styles approved by user:**

| Module | Style | Avatar | Description |
|--------|-------|--------|-------------|
| 1-4 | Medical Dark | Adriana Nurse | Standard center position, dark background |
| 5-8 | Presentation | Adriana Nurse (Side) | Avatar on left, room for slides on right |

**Rejected styles:** Office Light, Studio Dark (male), Business Modern

### Backend Files
- `/app/backend/auto_course_builder.py` - Autonomous course builder
- `/app/backend/generate_diverse_videos.py` - Video generation with styles
- `/app/backend/heygen_video_creator.py` - HeyGen API integration

### Frontend Pages
- `/videos` - Video gallery with module list
- `/styles` - Style demonstration page
- `/` - Landing page with course catalog

### Video Storage
- `/app/frontend/public/videos/diverse/` - First course videos
- `/app/frontend/public/videos/{course_id}/` - Additional course videos
- `/app/frontend/public/videos/subtitles/` - VTT subtitle files

## Database (MongoDB)
- `courses`: 325 courses
- `mcq_questions`: 36,412 questions
- Total content available for video generation

## 3rd Party Integrations
- **HeyGen API** - Avatar video generation
- API Key: Configured in environment

## Key Links
- Video Gallery: https://practical-banach-1.preview.emergentagent.com/videos
- Style Demos: https://practical-banach-1.preview.emergentagent.com/styles

## User Language
Hebrew (עברית)
