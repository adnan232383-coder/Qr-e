"""
🏫 University MCQ Auto-Generator
Generates questions for all courses using Gemini AI
"""

import asyncio
import json
import os
from datetime import datetime, timezone
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# Course definitions with topics
COURSES = [
    # Medicine Year 5-6
    {"id": "NVU_MD_Y5_S1_C43", "name": "Clinical Clerkship - Internal Medicine", "needed": 200,
     "topics": "Case-based internal medicine, differential diagnosis, workup, management plans"},
    {"id": "NVU_MD_Y5_S1_C44", "name": "Clinical Clerkship - Surgery", "needed": 200,
     "topics": "Surgical emergencies, pre/post-op care, wound healing, common procedures"},
    {"id": "NVU_MD_Y5_S2_C45", "name": "Clinical Clerkship - Pediatrics", "needed": 200,
     "topics": "Well-child care, developmental milestones, pediatric emergencies"},
    {"id": "NVU_MD_Y5_S2_C46", "name": "Clinical Clerkship - OB/GYN", "needed": 200,
     "topics": "Prenatal care, labor management, gynecologic emergencies"},
    {"id": "NVU_MD_Y5_S2_C47", "name": "Clinical Clerkship - Psychiatry", "needed": 200,
     "topics": "Psychiatric emergencies, psychopharmacology, therapeutic communication"},
    {"id": "NVU_MD_Y5_S2_C48", "name": "Clinical Clerkship - Family Medicine", "needed": 200,
     "topics": "Preventive care, chronic disease management, outpatient procedures"},
    {"id": "NVU_MD_Y6_S1_C49", "name": "Advanced Clinical Medicine", "needed": 200,
     "topics": "Rheumatology, nephrology, hematology/oncology, endocrinology"},
    {"id": "NVU_MD_Y6_S2_C50", "name": "Internship Preparation", "needed": 200,
     "topics": "Comprehensive clinical review, emergency protocols, ethics"},
    
    # Dentistry Year 1
    {"id": "UG_DENT_Y1_S1_C01", "name": "Dental Anatomy", "needed": 176,
     "topics": "Tooth morphology, numbering systems, occlusion, TMJ anatomy"},
    {"id": "UG_DENT_Y1_S1_C02", "name": "Oral Histology", "needed": 176,
     "topics": "Enamel, dentin, pulp, periodontal ligament, cementum"},
    {"id": "UG_DENT_Y1_S1_C03", "name": "Dental Materials I", "needed": 176,
     "topics": "Impression materials, gypsum products, polymers, adhesives"},
    {"id": "UG_DENT_Y1_S1_C04", "name": "Preclinical Operative Dentistry", "needed": 176,
     "topics": "Cavity preparation, instrumentation, isolation techniques"},
    {"id": "UG_DENT_Y1_S1_C05", "name": "Oral Biology", "needed": 176,
     "topics": "Saliva, biofilm, caries etiology, demineralization"},
    {"id": "UG_DENT_Y1_S2_C06", "name": "Dental Radiology I", "needed": 176,
     "topics": "X-ray physics, periapical techniques, interpretation"},
    {"id": "UG_DENT_Y1_S2_C07", "name": "Periodontology I", "needed": 176,
     "topics": "Gingival anatomy, periodontal assessment, plaque control"},
    {"id": "UG_DENT_Y1_S2_C08", "name": "Oral Pathology I", "needed": 176,
     "topics": "Developmental anomalies, cysts, odontogenic tumors"},
    {"id": "UG_DENT_Y1_S2_C09", "name": "Dental Pharmacology", "needed": 176,
     "topics": "Local anesthetics, analgesics, antibiotics in dentistry"},
    {"id": "UG_DENT_Y1_S2_C10", "name": "Preventive Dentistry", "needed": 176,
     "topics": "Fluoride, sealants, diet counseling, caries risk"},
    
    # Dentistry Year 2
    {"id": "UG_DENT_Y2_S1_C01", "name": "Operative Dentistry I", "needed": 176,
     "topics": "Direct restorations, amalgam, composite, GIC"},
    {"id": "UG_DENT_Y2_S1_C02", "name": "Endodontics I", "needed": 176,
     "topics": "Pulp biology, diagnosis, access preparation, instrumentation"},
    {"id": "UG_DENT_Y2_S1_C03", "name": "Fixed Prosthodontics I", "needed": 176,
     "topics": "Crown preparation, impressions, temporization, cementation"},
    {"id": "UG_DENT_Y2_S1_C04", "name": "Removable Prosthodontics I", "needed": 176,
     "topics": "Complete dentures, impression techniques, jaw relations"},
    {"id": "UG_DENT_Y2_S1_C05", "name": "Oral Surgery I", "needed": 176,
     "topics": "Extraction techniques, impactions, surgical instruments"},
    {"id": "UG_DENT_Y2_S2_C06", "name": "Periodontology II", "needed": 176,
     "topics": "Periodontal diseases, scaling/root planing, surgical techniques"},
    {"id": "UG_DENT_Y2_S2_C07", "name": "Pediatric Dentistry I", "needed": 176,
     "topics": "Child behavior, pulp therapy, space maintenance, trauma"},
    {"id": "UG_DENT_Y2_S2_C08", "name": "Orthodontics I", "needed": 176,
     "topics": "Growth & development, cephalometrics, malocclusion"},
    {"id": "UG_DENT_Y2_S2_C09", "name": "Oral Medicine", "needed": 176,
     "topics": "Mucosal diseases, systemic manifestations, oral cancer"},
    {"id": "UG_DENT_Y2_S2_C10", "name": "Dental Ethics & Practice Management", "needed": 176,
     "topics": "Informed consent, record keeping, infection control"},
    
    # Dentistry Year 5
    {"id": "UG_DENT_Y5_S1_C05", "name": "Advanced Clinical Dentistry", "needed": 48,
     "topics": "Complex restorative cases, treatment planning"},
    {"id": "UG_DENT_Y5_S2_C06", "name": "Implant Dentistry", "needed": 200,
     "topics": "Implant systems, surgical protocols, prosthetic options"},
    {"id": "UG_DENT_Y5_S2_C07", "name": "Advanced Oral Surgery", "needed": 200,
     "topics": "Complex extractions, preprosthetic surgery, TMJ disorders"},
    {"id": "UG_DENT_Y5_S2_C08", "name": "Advanced Prosthodontics", "needed": 200,
     "topics": "Full mouth rehabilitation, implant prosthodontics"},
    {"id": "UG_DENT_Y5_S2_C09", "name": "Oral & Maxillofacial Pathology", "needed": 200,
     "topics": "Advanced pathology, malignancies, systemic diseases"},
    {"id": "UG_DENT_Y5_S2_C10", "name": "Practice Management", "needed": 200,
     "topics": "Dental practice setup, legal issues, professional conduct"},
    
    # Pharmacy Year 1
    {"id": "UG_PHARM_Y1_S1_C01", "name": "General Chemistry", "needed": 200,
     "topics": "Atomic structure, bonding, solutions, acids/bases, buffers"},
    {"id": "UG_PHARM_Y1_S1_C02", "name": "Organic Chemistry I", "needed": 200,
     "topics": "Functional groups, nomenclature, stereochemistry, reactions"},
    {"id": "UG_PHARM_Y1_S1_C03", "name": "Anatomy & Physiology I", "needed": 200,
     "topics": "Cell biology, tissues, skeletal, muscular systems"},
    {"id": "UG_PHARM_Y1_S1_C04", "name": "Pharmacy Mathematics", "needed": 200,
     "topics": "Pharmaceutical calculations, dosage, concentrations"},
    {"id": "UG_PHARM_Y1_S1_C05", "name": "Introduction to Pharmacy", "needed": 200,
     "topics": "History, pharmacy law, ethics, professional roles"},
    {"id": "UG_PHARM_Y1_S2_C06", "name": "Organic Chemistry II", "needed": 200,
     "topics": "Carbonyl chemistry, amines, carbohydrates, amino acids"},
    {"id": "UG_PHARM_Y1_S2_C07", "name": "Anatomy & Physiology II", "needed": 200,
     "topics": "Cardiovascular, respiratory, digestive, urinary systems"},
    {"id": "UG_PHARM_Y1_S2_C08", "name": "Biochemistry I", "needed": 200,
     "topics": "Proteins, enzymes, carbohydrate metabolism"},
    {"id": "UG_PHARM_Y1_S2_C09", "name": "Microbiology", "needed": 200,
     "topics": "Bacteria, viruses, fungi, antimicrobial agents"},
    {"id": "UG_PHARM_Y1_S2_C10", "name": "Physical Pharmacy I", "needed": 200,
     "topics": "States of matter, solubility, dissolution"},
    
    # Pharmacy Year 2
    {"id": "UG_PHARM_Y2_S1_C01", "name": "Medicinal Chemistry I", "needed": 200,
     "topics": "Drug structure-activity relationships, drug design"},
    {"id": "UG_PHARM_Y2_S1_C02", "name": "Pharmacology I", "needed": 200,
     "topics": "Autonomic pharmacology, cardiovascular drugs"},
    {"id": "UG_PHARM_Y2_S1_C03", "name": "Pharmaceutics I", "needed": 200,
     "topics": "Solid dosage forms, tablets, capsules"},
    {"id": "UG_PHARM_Y2_S1_C04", "name": "Biochemistry II", "needed": 200,
     "topics": "Nucleic acids, molecular biology, biotechnology"},
    {"id": "UG_PHARM_Y2_S1_C05", "name": "Pathophysiology I", "needed": 200,
     "topics": "Cardiovascular, respiratory, renal pathophysiology"},
    {"id": "UG_PHARM_Y2_S2_C06", "name": "Pharmacology II", "needed": 200,
     "topics": "CNS drugs, endocrine drugs, chemotherapy"},
    {"id": "UG_PHARM_Y2_S2_C07", "name": "Pharmaceutics II", "needed": 200,
     "topics": "Liquid dosage forms, parenteral products"},
    {"id": "UG_PHARM_Y2_S2_C08", "name": "Medicinal Chemistry II", "needed": 200,
     "topics": "Antibiotics, antivirals, anticancer agents"},
    {"id": "UG_PHARM_Y2_S2_C09", "name": "Pathophysiology II", "needed": 200,
     "topics": "GI, endocrine, neurological pathophysiology"},
    {"id": "UG_PHARM_Y2_S2_C10", "name": "Pharmacognosy I", "needed": 200,
     "topics": "Natural products, alkaloids, herbal medicines"},
    
    # Pharmacy Year 3-4
    {"id": "UG_PHARM_Y3_S1_C01", "name": "Clinical Pharmacy I", "needed": 200,
     "topics": "Drug therapy optimization, patient assessment"},
    {"id": "UG_PHARM_Y3_S1_C02", "name": "Pharmacokinetics", "needed": 200,
     "topics": "ADME, compartment models, dosing calculations"},
    {"id": "UG_PHARM_Y3_S1_C03", "name": "Biopharmaceutics", "needed": 200,
     "topics": "Drug absorption, bioavailability, bioequivalence"},
    {"id": "UG_PHARM_Y3_S1_C04", "name": "Pharmaceutical Analysis", "needed": 200,
     "topics": "Spectroscopy, chromatography, quality control"},
    {"id": "UG_PHARM_Y3_S1_C05", "name": "Pharmacognosy II", "needed": 200,
     "topics": "Phytochemistry, extraction, standardization"},
    {"id": "UG_PHARM_Y3_S2_C06", "name": "Clinical Pharmacy II", "needed": 200,
     "topics": "Disease state management, therapeutics"},
    {"id": "UG_PHARM_Y3_S2_C08", "name": "Toxicology", "needed": 200,
     "topics": "Mechanisms of toxicity, antidotes, overdose"},
    {"id": "UG_PHARM_Y3_S2_C09", "name": "Pharmaceutical Biotechnology", "needed": 200,
     "topics": "Recombinant proteins, antibodies, vaccines"},
    {"id": "UG_PHARM_Y3_S2_C10", "name": "Pharmacy Law", "needed": 200,
     "topics": "Drug regulations, controlled substances, ethics"},
    {"id": "UG_PHARM_Y4_S1_C01", "name": "Advanced Pharmacotherapy I", "needed": 200,
     "topics": "Oncology, transplant, critical care pharmacy"},
    {"id": "UG_PHARM_Y4_S1_C02", "name": "Drug Information", "needed": 200,
     "topics": "Evidence-based medicine, clinical trials"},
    {"id": "UG_PHARM_Y4_S1_C03", "name": "Pharmacy Management", "needed": 200,
     "topics": "Inventory, workflow, quality improvement"},
    {"id": "UG_PHARM_Y4_S1_C04", "name": "Patient Counseling", "needed": 200,
     "topics": "Medication counseling, health literacy, adherence"},
    {"id": "UG_PHARM_Y4_S1_C05", "name": "Advanced Pharmacotherapy II", "needed": 200,
     "topics": "Psychiatry, neurology, pain management"},
    {"id": "UG_PHARM_Y4_S2_C06", "name": "Community Pharmacy", "needed": 200,
     "topics": "OTC medications, immunizations, MTM"},
    {"id": "UG_PHARM_Y4_S2_C07", "name": "Hospital Pharmacy", "needed": 200,
     "topics": "IV admixture, clinical services, formulary"},
    {"id": "UG_PHARM_Y4_S2_C08", "name": "Specialty Pharmacy", "needed": 200,
     "topics": "Specialty medications, patient assistance"},
    {"id": "UG_PHARM_Y4_S2_C09", "name": "Pharmacovigilance", "needed": 200,
     "topics": "ADR reporting, risk management, drug safety"},
    {"id": "UG_PHARM_Y4_S2_C10", "name": "Board Preparation", "needed": 200,
     "topics": "Comprehensive review, calculations, clinical scenarios"},
    {"id": "UG_PHARM_PHARMACOKINETICS", "name": "Advanced Pharmacokinetics", "needed": 200,
     "topics": "Population PK, TDM, special populations"},
    {"id": "UG_PHARM_PHARMACEUTICAL_CHEMISTRY", "name": "Pharmaceutical Chemistry", "needed": 200,
     "topics": "Drug synthesis, prodrugs, metabolism, SAR"},
]

PROMPT_TEMPLATE = """Generate {count} high-quality MCQs for "{course_name}".

Topics: {topics}

Output as JSON array:
[{{"question": "...", "option_a": "...", "option_b": "...", "option_c": "...", "option_d": "...", "correct_answer": "A/B/C/D", "explanation": "..."}}]

Rules:
- Clinical/academic vignette style
- 4 options each
- Educational explanations
- No duplicates
- Difficulty: 60% medium, 25% hard, 15% easy

Generate exactly {count} questions in valid JSON."""


async def generate_questions_for_course(course, gemini_client):
    """Generate questions for a single course using Gemini"""
    prompt = PROMPT_TEMPLATE.format(
        count=min(course["needed"], 50),  # Generate in batches of 50
        course_name=course["name"],
        topics=course["topics"]
    )
    
    try:
        response = await gemini_client.generate_content(prompt)
        questions = json.loads(response.text)
        return questions
    except Exception as e:
        print(f"Error generating for {course['id']}: {e}")
        return []


async def import_to_db(questions, course_id):
    """Import questions to MongoDB"""
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    
    questions_to_insert = []
    for q in questions:
        doc = {
            "question_id": f"q_{uuid.uuid4().hex[:12]}",
            "course_id": course_id,
            "question": q["question"],
            "option_a": q["option_a"],
            "option_b": q["option_b"],
            "option_c": q["option_c"],
            "option_d": q["option_d"],
            "correct_answer": q["correct_answer"],
            "explanation": q.get("explanation", ""),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        questions_to_insert.append(doc)
    
    if questions_to_insert:
        await db.mcq_questions.insert_many(questions_to_insert)
        new_count = await db.mcq_questions.count_documents({"course_id": course_id})
        await db.courses.update_one(
            {"external_id": course_id},
            {"$set": {"mcq_count": new_count}}
        )
        return new_count
    return 0


async def main():
    print("="*60)
    print("🏫 University MCQ Auto-Generator")
    print("="*60)
    
    total_needed = sum(c["needed"] for c in COURSES)
    print(f"Total courses: {len(COURSES)}")
    print(f"Total questions needed: {total_needed:,}")
    print()
    
    # This would need Gemini API integration
    # For now, print the status
    for course in COURSES:
        print(f"📚 {course['id']}: {course['name']} - Need {course['needed']} questions")
    
    print()
    print("="*60)
    print("To run this generator, you need to integrate Gemini API")
    print("Use: pip install google-generativeai")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
