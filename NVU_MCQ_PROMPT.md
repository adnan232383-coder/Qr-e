# MCQ Generation Prompt for NVU Courses

## Format Required
Each course needs MCQs in JSON format:

```json
{
  "course_name": "Course Name",
  "course_code": "COURSE_CODE",
  "questions": [
    {
      "question": "Question text here?",
      "option_a": "First option",
      "option_b": "Second option", 
      "option_c": "Third option",
      "option_d": "Fourth option",
      "correct_answer": "A",
      "explanation": "Brief explanation."
    }
  ]
}
```

## 20 NVU Courses Needing Content

| # | Course Code | Course Name | File Name |
|---|-------------|-------------|-----------|
| 1 | NVU_DENT_Y1_S1_C01 | General Anatomy | Emergent_NVU_DENT_Y1_S1_C01.zip |
| 2 | NVU_DENT_Y1_S1_C02 | Dental Morphology | Emergent_NVU_DENT_Y1_S1_C02.zip |
| 3 | NVU_DENT_Y1_S2_C03 | Biochemistry | Emergent_NVU_DENT_Y1_S2_C03.zip |
| 4 | NVU_DENT_Y1_S2_C04 | Physiology | Emergent_NVU_DENT_Y1_S2_C04.zip |
| 5 | NVU_DENT_Y2_S1_C05 | Preclinical Operative Dentistry | Emergent_NVU_DENT_Y2_S1_C05.zip |
| 6 | NVU_DENT_Y2_S2_C06 | Endodontics I | Emergent_NVU_DENT_Y2_S2_C06.zip |
| 7 | NVU_DENT_Y3_S1_C07 | Prosthodontics I | Emergent_NVU_DENT_Y3_S1_C07.zip |
| 8 | NVU_DENT_Y3_S2_C08 | Orthodontics I | Emergent_NVU_DENT_Y3_S2_C08.zip |
| 9 | NVU_DENT_Y4_S1_C09 | Oral Surgery I | Emergent_NVU_DENT_Y4_S1_C09.zip |
| 10 | NVU_DENT_Y4_S2_C10 | Periodontology I | Emergent_NVU_DENT_Y4_S2_C10.zip |
| 11 | NVU_DENT_Y5_S1_C11 | Clinical Dentistry Rotation | Emergent_NVU_DENT_Y5_S1_C11.zip |
| 12 | NVU_DENT_Y5_S2_C12 | Elective Dentistry | Emergent_NVU_DENT_Y5_S2_C12.zip |
| 13 | NVU_MD_Y1_S1_C01 | Medical Biology and Genetics | Emergent_NVU_MD_Y1_S1_C01.zip |
| 14 | NVU_MD_Y1_S1_C02 | Human Anatomy I | Emergent_NVU_MD_Y1_S1_C02.zip |
| 15 | NVU_MD_Y1_S1_C03 | Histology and Embryology | Emergent_NVU_MD_Y1_S1_C03.zip |
| 16 | NVU_MD_Y1_S1_C04 | Biochemistry I | Emergent_NVU_MD_Y1_S1_C04.zip |
| 17 | NVU_MD_Y1_S1_C05 | Medical Terminology | Emergent_NVU_MD_Y1_S1_C05.zip |
| 18 | NVU_MD_Y1_S1_C06 | Introduction to Clinical Skills | Emergent_NVU_MD_Y1_S1_C06.zip |
| 19 | NVU_MD_Y1_S2_C07 | Human Anatomy II | Emergent_NVU_MD_Y1_S2_C07.zip |
| 20 | NVU_MD_Y1_S2_C08 | Physiology I | Emergent_NVU_MD_Y1_S2_C08.zip |

## Guidelines
1. 50 MCQs per course minimum
2. Questions should be clinically relevant and exam-appropriate
3. Mix of difficulty levels (easy, medium, hard)
4. Cover key topics from the course syllabus
5. Explanations should be educational and concise
6. Options should be plausible (avoid obviously wrong answers)
7. Use standard medical terminology

## File Structure
```
Emergent_COURSE_CODE.zip
└── NVU/
    └── Program/
        └── Year_X/
            └── Semester_X/
                └── COURSE_CODE/
                    └── mcq.json (or mcq_part1.json, mcq_part2.json, etc.)
```
