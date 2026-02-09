import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from datetime import datetime, timezone

questions_data = [
  {"question": "A 74-year-old male is admitted for suspected sepsis. Despite adequate fluid resuscitation with 30 mL/kg of crystalloids, his mean arterial pressure (MAP) remains 60 mmHg and his serum lactate is 4 mmol/L. What is the most appropriate diagnosis?", "option_a": "Sepsis", "option_b": "Septic Shock", "option_c": "Systemic Inflammatory Response Syndrome (SIRS)", "option_d": "Refractory Hypotension", "correct_answer": "B", "explanation": "Septic shock is defined as sepsis with persistent hypotension requiring vasopressors to maintain MAP >= 65 mmHg and having a serum lactate level > 2 mmol/L despite adequate fluid resuscitation."},
  {"question": "A 35-year-old patient with HIV (CD4 count 45 cells/uL) presents with a severe headache, low-grade fever, and neck stiffness. A lumbar puncture is performed, and India Ink staining of the CSF reveals encapsulated yeast. What is the treatment of choice?", "option_a": "Fluconazole alone", "option_b": "Amphotericin B plus Flucytosine", "option_c": "Trimethoprim-Sulfamethoxazole", "option_d": "Ceftriaxone and Vancomycin", "correct_answer": "B", "explanation": "The findings are diagnostic for Cryptococcal meningitis. Induction therapy with Amphotericin B and Flucytosine is the standard of care for patients with HIV."},
  {"question": "A 48-year-old obese female presents with dark, velvety, hyperpigmented plaques on the back of her neck and in the axillae. Which of the following is most strongly associated with this skin finding?", "option_a": "Hypothyroidism", "option_b": "Insulin resistance/Diabetes Mellitus", "option_c": "Adrenal insufficiency", "option_d": "Systemic Lupus Erythematosus", "correct_answer": "B", "explanation": "Acanthosis nigricans is a common cutaneous manifestation of systemic insulin resistance and is frequently seen in patients with Type 2 Diabetes or metabolic syndrome."},
  {"question": "A 22-year-old male is brought to the ER after an intentional overdose of an unknown substance. He is found to have a high anion gap metabolic acidosis and crystals are seen on urinalysis. He is complaining of visual changes (looking through a snowstorm). Which substance did he likely ingest?", "option_a": "Ethanol", "option_b": "Methanol", "option_c": "Ethylene glycol", "option_d": "Isopropyl alcohol", "correct_answer": "B", "explanation": "Methanol poisoning causes high anion gap acidosis and is specifically known for causing optic papillitis and visual disturbances (snowstorm vision). Ethylene glycol more commonly causes renal failure with calcium oxalate crystals."},
  {"question": "A 78-year-old female is brought in by her family due to acute confusion and fluctuating levels of consciousness that started 2 days ago. She has no previous history of cognitive impairment. She is currently seeing insects in the room. What is the most likely diagnosis?", "option_a": "Alzheimer's Dementia", "option_b": "Delirium", "option_c": "Schizophrenia", "option_d": "Vascular Dementia", "correct_answer": "B", "explanation": "Acute onset, fluctuating course, and visual hallucinations in an elderly patient are hallmarks of delirium, which is often triggered by an underlying medical issue like infection or medication changes."},
  {"question": "A 65-year-old male with a 50-pack-year smoking history asks about lung cancer screening. According to current preventive guidelines, what is the recommended screening method?", "option_a": "Annual Chest X-ray", "option_b": "Annual Low-Dose Computed Tomography (LDCT)", "option_c": "Sputum cytology every 6 months", "option_d": "CEA biomarker testing annually", "correct_answer": "B", "explanation": "Annual LDCT is recommended for adults aged 50-80 with a 20-pack-year smoking history who currently smoke or quit within the last 15 years."},
  {"question": "Which of the following medications should be avoided in elderly patients according to the Beers Criteria due to a high risk of causing confusion, falls, and orthostatic hypotension?", "option_a": "Amlodipine", "option_b": "Amitriptyline", "option_c": "Metformin", "option_d": "Atorvastatin", "correct_answer": "B", "explanation": "Amitriptyline is a tricyclic antidepressant with strong anticholinergic properties, which significantly increases the risk of delirium, sedation, and falls in the geriatric population."},
  {"question": "A 40-year-old female presents with painful, red, inflammatory nodules on her shins. A chest X-ray shows bilateral hilar adenopathy. What is the most likely systemic diagnosis?", "option_a": "Tuberculosis", "option_b": "Sarcoidosis", "option_c": "Ulcerative Colitis", "option_d": "Coccidioidomycosis", "correct_answer": "B", "explanation": "The combination of Erythema Nodosum and bilateral hilar lymphadenopathy (Lofgren syndrome) is a classic and highly suggestive presentation of Sarcoidosis."},
  {"question": "A 19-year-old college student presents with a high fever, petechial rash on the trunk, and severe neck stiffness. What is the most appropriate empirical antibiotic regimen while waiting for CSF cultures?", "option_a": "Vancomycin and Penicillin", "option_b": "Ceftriaxone and Vancomycin", "option_c": "Gentamicin and Ampicillin", "option_d": "Ciprofloxacin and Doxycycline", "correct_answer": "B", "explanation": "Empiric treatment for suspected bacterial meningitis in young adults focuses on Neisseria meningitidis and Streptococcus pneumoniae, covered by a 3rd generation cephalosporin and vancomycin."},
  {"question": "A 65-year-old woman is evaluated for preventive care. She has already received her flu shot this year. Which of the following vaccines is also routinely recommended starting at age 65?", "option_a": "HPV vaccine", "option_b": "Pneumococcal vaccine (e.g., PCV20 or PCV15 followed by PPSV23)", "option_c": "MMR booster", "option_d": "Hepatitis A vaccine", "correct_answer": "B", "explanation": "Pneumococcal vaccination is routinely recommended for all adults aged 65 and older to prevent invasive pneumococcal disease."}
]

COURSE_ID = "NVU_MD_Y3_S1_C24"

async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    
    current_count = await db.mcq_questions.count_documents({"course_id": COURSE_ID})
    print(f"Current questions: {current_count}")
    
    questions_to_insert = []
    for q in questions_data:
        question_doc = {
            "question_id": f"q_{uuid.uuid4().hex[:12]}",
            "course_id": COURSE_ID,
            "question": q["question"],
            "option_a": q["option_a"],
            "option_b": q["option_b"],
            "option_c": q["option_c"],
            "option_d": q["option_d"],
            "correct_answer": q["correct_answer"],
            "explanation": q["explanation"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        questions_to_insert.append(question_doc)
    
    result = await db.mcq_questions.insert_many(questions_to_insert)
    print(f"Inserted: {len(result.inserted_ids)} questions")
    
    new_count = await db.mcq_questions.count_documents({"course_id": COURSE_ID})
    await db.courses.update_one(
        {"external_id": COURSE_ID},
        {"$set": {"mcq_count": new_count, "mcq_verified": True}}
    )
    print(f"Total now: {new_count}")

if __name__ == "__main__":
    asyncio.run(main())
