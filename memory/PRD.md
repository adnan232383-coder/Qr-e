# Educational Video Platform - PRD

## Original Problem Statement
Build a comprehensive educational video platform with AI-generated avatar videos for medical/pharmacy courses across multiple universities.

### Initial Requirements
1. Build courses based on existing MCQ database
2. Each course should have multiple video modules with talking avatars (HeyGen)
3. Videos in English with multi-language subtitles (Hebrew, Arabic, Russian, Romanian)
4. **Visual diversity**: Different avatar styles and presentation formats every 2 modules

## Current Status (Dec 2025)

### ✅ MCQ Content Population - COMPLETED

| University | Courses | Courses with 300+ MCQs | Total Questions |
|------------|---------|------------------------|-----------------|
| **An-Najah National University (NAJAH)** | 160 | **160** ✅ | **48,000** |
| Al-Ahliyya Amman University (AAU) | 100 | 100 ✅ | 30,000 |
| New Vision University (NVU) | 76 | 72 | 26,315 |
| University of Georgia (UG) | 94 | 74 | 22,882 |
| University of Medicine Iași (IASI) | 60 | 60 ✅ | 18,000 |
| **TOTAL** | **490** | **466** | **145,197** |

### ✅ University Structure - COMPLETED
- [x] UG (University of Georgia) - 94 courses
- [x] NVU (New Vision University) - 76 courses  
- [x] IASI (University of Medicine Iași) - 60 courses
- [x] AAU (Al-Ahliyya Amman University) - 100 courses
- [x] NAJAH (An-Najah National University) - 160 courses (MED: 60, DENT: 50, PHARM: 50)

### 🔴 BLOCKED - Video Generation
- HeyGen API credits insufficient
- User is handling with HeyGen support
- Video generation for all 490+ courses pending resolution

### Backlog 📋
- [ ] Generate videos for all courses (pending HeyGen credits)
- [ ] Complete MCQ population for remaining UG/NVU courses to 300

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
- Video Gallery: https://edcontent-multi.preview.emergentagent.com/videos
- Style Demos: https://edcontent-multi.preview.emergentagent.com/styles

## User Language
Hebrew (עברית)
