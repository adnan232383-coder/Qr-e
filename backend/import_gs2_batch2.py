import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

questions_data = [
  {
    "question": "A patient presents with a 'blowout' fracture of the inferior orbital wall. Which of the following is the most likely clinical finding on physical examination?",
    "option_a": "Inability to look downward",
    "option_b": "Diplopia on upward gaze due to entrapment of the inferior rectus muscle",
    "option_c": "Exophthalmos",
    "option_d": "Numbness of the forehead",
    "correct_answer": "B",
    "explanation": "Orbital floor fractures often result in entrapment of the inferior rectus muscle or orbital fat, which mechanically restricts the eye from rotating upward, causing double vision."
  },
  {
    "question": "Which of the following findings on an ECG is pathognomonic for a massive pulmonary embolism causing acute cor pulmonale?",
    "option_a": "T-wave inversions in leads V1-V4",
    "option_b": "S1Q3T3 pattern (Deep S in I, Q wave and inverted T in III)",
    "option_c": "Right bundle branch block",
    "option_d": "Sinus tachycardia",
    "correct_answer": "B",
    "explanation": "While rare and found in only 10-20% of cases, the S1Q3T3 pattern is the classic 'textbook' sign of right heart strain associated with PE."
  },
  {
    "question": "A patient is brought to the ED after being found in a closed garage with a car engine running. His carboxyhemoglobin level is 35%. What is the most appropriate definitive treatment?",
    "option_a": "Nebulized saline",
    "option_b": "100% high-flow oxygen and consideration for Hyperbaric Oxygen Therapy",
    "option_c": "Intravenous methylene blue",
    "option_d": "Observation in room air",
    "correct_answer": "B",
    "explanation": "Carboxyhemoglobin levels >25% (or >15% in pregnancy) or signs of neurotoxicity are standard indications for hyperbaric oxygen to accelerate CO clearance."
  },
  {
    "question": "A 3-year-old child presents after ingesting an unknown amount of 'Wintergreen oil' (Methyl salicylate). He is hyperventilating and vomiting. Which acid-base disturbance is most expected early on?",
    "option_a": "Pure metabolic acidosis",
    "option_b": "Mixed respiratory alkalosis and high-anion gap metabolic acidosis",
    "option_c": "Pure respiratory acidosis",
    "option_d": "Metabolic alkalosis",
    "correct_answer": "B",
    "explanation": "Salicylates stimulate the respiratory center directly (alkalosis) while also uncoupling oxidative phosphorylation and producing organic acids (acidosis)."
  },
  {
    "question": "During Rapid Sequence Intubation (RSI), which of the following is an absolute contraindication to the use of Succinylcholine?",
    "option_a": "Asthma history",
    "option_b": "Major burns or crush injuries sustained >72 hours ago",
    "option_c": "Recent meal (full stomach)",
    "option_d": "Obesity",
    "correct_answer": "B",
    "explanation": "Succinylcholine can cause life-threatening hyperkalemia in patients with up-regulation of extrajunctional ACh receptors, common in subacute burns, denervation, or crush injuries."
  },
  {
    "question": "A patient presents with a core temperature of 31°C (87.8°F). Which of the following is a classic EKG finding in this stage of hypothermia?",
    "option_a": "Delta waves",
    "option_b": "Osborn (J) waves",
    "option_c": "U waves",
    "option_d": "Peaked T waves",
    "correct_answer": "B",
    "explanation": "Osborn waves are positive deflections at the J-junction, typically seen when the core temperature drops below 32°C."
  },
  {
    "question": "A victim of a lightning strike is found in 'Keraunoparalysis'. What does this term describe?",
    "option_a": "Permanent spinal cord injury",
    "option_b": "Transient limb paralysis and blue/mottled skin due to autonomic vasospasm",
    "option_c": "Brain death",
    "option_d": "Total body third-degree burns",
    "correct_answer": "B",
    "explanation": "Keraunoparalysis is a transient state of limb paralysis and pulselessness following a lightning strike, usually resolving within hours."
  },
  {
    "question": "What is the primary medication used to treat life-threatening 'Serotonin Syndrome' that is refractory to benzodiazepines and supportive care?",
    "option_a": "Naloxone",
    "option_b": "Cyproheptadine",
    "option_c": "Physostigmine",
    "option_d": "Bromocriptine",
    "correct_answer": "B",
    "explanation": "Cyproheptadine is an oral serotonin antagonist used in moderate-to-severe cases of serotonin syndrome."
  },
  {
    "question": "A patient presents with a 'Jefferson Fracture'. What is the anatomical location of this injury?",
    "option_a": "The C2 pedicle (Hangman's fracture)",
    "option_b": "The C1 ring (Atlas burst fracture)",
    "option_c": "The odontoid process",
    "option_d": "The T12 vertebral body",
    "correct_answer": "B",
    "explanation": "A Jefferson fracture is a burst fracture of the first cervical vertebra (C1), usually caused by an axial load to the head."
  },
  {
    "question": "In a patient with a 'High-Pressure Injection Injury' to the finger from a paint gun, what is the most appropriate management?",
    "option_a": "Oral antibiotics and warm soaks",
    "option_b": "Immediate surgical consultation for wide debridement",
    "option_c": "Ice packs and elevation",
    "option_d": "Application of a digital block and simple suturing",
    "correct_answer": "B",
    "explanation": "These injuries are surgical emergencies. The small entry wound masks extensive internal tissue damage and chemical necrosis that requires immediate operative exploration."
  },
  {
    "question": "A 50-year-old male presents with sudden onset 'shades coming down' over his right eye, lasting 5 minutes before resolving completely. This is most suggestive of:",
    "option_a": "Retinal detachment",
    "option_b": "Amaurosis Fugax (Transient Ischemic Attack)",
    "option_c": "Glaucoma",
    "option_d": "Cataracts",
    "correct_answer": "B",
    "explanation": "Amaurosis fugax is a painless, transient monocular vision loss often caused by an embolus from the carotid artery, acting as a warning sign for a future stroke."
  },
  {
    "question": "Which of the following is the first-line vasopressor for a patient in 'Septic Shock' who remains hypotensive after fluid resuscitation?",
    "option_a": "Dopamine",
    "option_b": "Norepinephrine",
    "option_c": "Epinephrine",
    "option_d": "Phenylephrine",
    "correct_answer": "B",
    "explanation": "Current Sepsis guidelines recommend norepinephrine as the first-choice vasopressor to maintain a Mean Arterial Pressure (MAP) of ≥65 mmHg."
  },
  {
    "question": "A patient presents with 'painless' hematuria and flank pain after a blunt trauma to the back. A CT scan shows a 'shattered kidney'. What is the Grade of this renal injury?",
    "option_a": "Grade I",
    "option_b": "Grade V",
    "option_c": "Grade III",
    "option_d": "Grade II",
    "correct_answer": "B",
    "explanation": "Grade V renal injury is the most severe, involving a shattered kidney or avulsion of the renal hilum."
  },
  {
    "question": "In the management of a patient with suspected 'Cardiac Tamponade' who is crashing, what is the immediate life-saving procedure?",
    "option_a": "Chest tube insertion",
    "option_b": "Pericardiocentesis",
    "option_c": "Endotracheal intubation",
    "option_d": "Aspirin 325 mg",
    "correct_answer": "B",
    "explanation": "Removal of even a small amount of fluid (15-20 mL) from the pericardial sac via needle can significantly improve cardiac output in tamponade."
  },
  {
    "question": "Which of the following defines 'Exertional Heat Stroke' compared to Non-exertional (Classic) Heat Stroke?",
    "option_a": "It only occurs in elderly patients",
    "option_b": "It is often associated with Rhabdomyolysis and Disseminated Intravascular Coagulation (DIC)",
    "option_c": "It does not involve mental status changes",
    "option_d": "The skin is always dry",
    "correct_answer": "B",
    "explanation": "Exertional heat stroke occurs in young, active individuals. Because of the intense muscle activity, rhabdomyolysis and coagulopathies are much more common than in classic heat stroke."
  },
  {
    "question": "A patient with an intraocular foreign body composed of which material requires the most urgent surgical removal due to rapid toxicity?",
    "option_a": "Glass",
    "option_b": "Copper",
    "option_c": "Plastic",
    "option_d": "Gold",
    "correct_answer": "B",
    "explanation": "Copper (chalcosis) and Iron (siderosis) are chemically reactive and cause rapid, irreversible damage to the intraocular structures."
  },
  {
    "question": "In pediatric resuscitation, what is the correct compression rate per minute?",
    "option_a": "60–80",
    "option_b": "100–120",
    "option_c": "140–160",
    "option_d": "Exactly 100",
    "correct_answer": "B",
    "explanation": "Consistent with adult guidelines, the recommended compression rate for children and infants is 100 to 120 per minute."
  },
  {
    "question": "A patient presents with 'muffled heart sounds', 'JVD', and 'hypotension'. On inspiration, the systolic blood pressure drops by 15 mmHg. This blood pressure finding is called:",
    "option_a": "Electrical alternans",
    "option_b": "Pulsus paradoxus",
    "option_c": "Widened pulse pressure",
    "option_d": "Kussmaul's sign",
    "correct_answer": "B",
    "explanation": "Pulsus paradoxus (drop in SBP > 10 mmHg on inspiration) is a key clinical indicator of cardiac tamponade."
  },
  {
    "question": "What is the 'Rule of 9s' estimate for a patient with burns involving the entire right arm and the entire chest (anterior trunk)?",
    "option_a": "18%",
    "option_b": "27%",
    "option_c": "36%",
    "option_d": "9%",
    "correct_answer": "B",
    "explanation": "Right arm (9%) + Anterior trunk (18%) = 27% Total Body Surface Area (TBSA)."
  },
  {
    "question": "A patient presents with a 'boxer's fracture'. Where is this fracture located?",
    "option_a": "The scaphoid bone",
    "option_b": "The neck of the 5th metacarpal",
    "option_c": "The distal radius",
    "option_d": "The base of the thumb",
    "correct_answer": "B",
    "explanation": "A boxer's fracture is a common injury occurring at the neck of the 5th metacarpal, usually after punching a hard object."
  },
  {
    "question": "Which of the following is an antidote for 'Methanol' poisoning that works by inhibiting alcohol dehydrogenase?",
    "option_a": "N-acetylcysteine",
    "option_b": "Fomepizole",
    "option_c": "Atropine",
    "option_d": "Sodium Thiosulfate",
    "correct_answer": "B",
    "explanation": "Fomepizole is the preferred agent because it has a higher affinity for alcohol dehydrogenase than ethanol and does not cause intoxication."
  },
  {
    "question": "A patient with a traumatic head injury has a 'lucid interval' followed by rapid neurological decline. A CT scan shows a convex (lens-shaped) hematoma. Which vessel is most likely ruptured?",
    "option_a": "Bridging veins",
    "option_b": "Middle meningeal artery",
    "option_c": "Basilar artery",
    "option_d": "Internal carotid",
    "correct_answer": "B",
    "explanation": "This describes an epidural hematoma, which is classically caused by an arterial bleed (middle meningeal) often associated with a temporal bone fracture."
  },
  {
    "question": "In the 'START' mass casualty triage system, a patient who is not walking, but has a radial pulse and follows simple commands, should be tagged:",
    "option_a": "Red (Immediate)",
    "option_b": "Yellow (Delayed)",
    "option_c": "Green (Minor)",
    "option_d": "Black (Deceased)",
    "correct_answer": "B",
    "explanation": "If the patient's RPM (Respirations, Perfusion, Mental status) are all within normal limits (RR <30, Pulse present, Follows commands) but they cannot walk, they are 'Yellow'."
  },
  {
    "question": "What is the primary purpose of 'Permissive Hypotension' in the management of a trauma patient with active intra-abdominal hemorrhage?",
    "option_a": "To protect the brain from swelling",
    "option_b": "To avoid 'popping the clot' and worsening bleeding before surgical control",
    "option_c": "To reduce the risk of acute kidney injury",
    "option_d": "To make the surgery easier for the surgeon",
    "correct_answer": "B",
    "explanation": "Maintaining a lower-than-normal blood pressure (SBP ~80-90) prevents aggressive fluid resuscitation from dislodging early blood clots before a surgeon can stop the bleeding."
  },
  {
    "question": "A patient presents with severe bradycardia and 'slurring' of the QRS into the T-wave (Sine wave pattern). What is the immediate treatment?",
    "option_a": "Lidocaine",
    "option_b": "Intravenous Calcium (Gluconate or Chloride)",
    "option_c": "Amiodarone",
    "option_d": "Synchronized cardioversion",
    "correct_answer": "B",
    "explanation": "A sine wave pattern on ECG is a pre-terminal sign of severe hyperkalemia. Calcium must be given immediately to stabilize the cardiac membrane."
  },
  {
    "question": "Which finding on a chest X-ray is classic for 'Aortic Disruption' after a high-speed deceleration injury?",
    "option_a": "Pneumothorax",
    "option_b": "Widened mediastinum (>8cm)",
    "option_c": "Rib fractures",
    "option_d": "Infiltrate in the lower lobe",
    "correct_answer": "B",
    "explanation": "Deceleration trauma can tear the aorta near the ligamentum arteriosum; a widened mediastinum on X-ray is the classic screening sign."
  },
  {
    "question": "A patient presents with a 'painful' eye and 'dendritic' lesions on the cornea after staining with fluorescein. Diagnosis?",
    "option_a": "Bacterial conjunctivitis",
    "option_b": "Herpes Simplex Keratitis",
    "option_c": "Corneal abrasion",
    "option_d": "Fungal infection",
    "correct_answer": "B",
    "explanation": "Dendritic (branching) ulcers are pathognomonic for Herpes Simplex virus infection of the cornea."
  },
  {
    "question": "In ACLS, what is the first-line medication for a patient in 'Asystole'?",
    "option_a": "Amiodarone",
    "option_b": "Epinephrine",
    "option_c": "Atropine",
    "option_d": "Vasopressin",
    "correct_answer": "B",
    "explanation": "Epinephrine is the only vasopressor recommended in the ACLS algorithm for non-shockable rhythms (Asystole/PEA)."
  },
  {
    "question": "Which of the following is the most common cause of 'Lower GI Bleeding' in an infant?",
    "option_a": "Colon cancer",
    "option_b": "Anal fissures",
    "option_c": "Intussusception",
    "option_d": "Diverticulitis",
    "correct_answer": "B",
    "explanation": "While intussusception (currant jelly stool) is serious, simple anal fissures are the most frequent cause of small amounts of bright red blood in infants."
  },
  {
    "question": "A patient presents with 'hypotension', 'muffled heart sounds', and 'electrical alternans' on ECG. What is the most likely diagnosis?",
    "option_a": "Tension pneumothorax",
    "option_b": "Pericardial Tamponade",
    "option_c": "Myocardial Infarction",
    "option_d": "Septic shock",
    "correct_answer": "B",
    "explanation": "Electrical alternans (alternating QRS height) occurs as the heart swings rhythmically within a large pericardial effusion."
  },
  {
    "question": "What is the 'Gold Standard' for diagnosing a 'Mid-gut Volvulus' in an infant?",
    "option_a": "Abdominal Ultrasound",
    "option_b": "Upper GI series (contrast study showing 'corkscrew' appearance)",
    "option_c": "Stool culture",
    "option_d": "MRI",
    "correct_answer": "B",
    "explanation": "An Upper GI series is the definitive test to identify the malrotation and twisting of the small bowel."
  },
  {
    "question": "A patient presents with a 'priapism' following a high-speed car accident. This should alert the clinician to which type of injury?",
    "option_a": "Pelvic fracture",
    "option_b": "Complete spinal cord injury (loss of sympathetic tone)",
    "option_c": "Bladder rupture",
    "option_d": "Femur fracture",
    "correct_answer": "B",
    "explanation": "Reflexic priapism is a clinical sign of high-level spinal cord injury due to unopposed parasympathetic activity."
  },
  {
    "question": "In the setting of 'Acute Angle-Closure Glaucoma', which of the following medications should be AVOIDED?",
    "option_a": "Timolol drops",
    "option_b": "Atropine (Mydriatics)",
    "option_c": "Acetazolamide",
    "option_d": "Pilocarpine",
    "correct_answer": "B",
    "explanation": "Mydriatics (pupil dilators) like atropine can further crowd the drainage angle and worsen the pressure in acute glaucoma."
  },
  {
    "question": "What is the recommended treatment for a 'Scaphoid fracture' with no visible displacement on X-ray but tenderness in the 'anatomic snuffbox'?",
    "option_a": "Reassurance and no treatment",
    "option_b": "Thumb spica splint and repeat X-ray in 10-14 days",
    "option_c": "Immediate surgery",
    "option_d": "Ace wrap only",
    "correct_answer": "B",
    "explanation": "Scaphoid fractures often don't show up on initial X-rays; because of the risk of avascular necrosis, they must be treated as a fracture until proven otherwise."
  },
  {
    "question": "Which of the following is a symptom of 'Cushing's Triad'?",
    "option_a": "Tachycardia, hypotension, and tachypnea",
    "option_b": "Bradycardia, hypertension, and irregular respirations",
    "option_c": "Fever, jaundice, and RUQ pain",
    "option_d": "Hypotension, JVD, and muffled heart sounds",
    "correct_answer": "B",
    "explanation": "Cushing's Triad is a physiological response to increased intracranial pressure."
  },
  {
    "question": "A patient presents with 'petechiae' and 'confusion' 24 hours after a femur fracture. What is the most likely diagnosis?",
    "option_a": "Pulmonary embolism",
    "option_b": "Fat Embolism Syndrome",
    "option_c": "Sepsis",
    "option_d": "Stroke",
    "correct_answer": "B",
    "explanation": "The triad of hypoxemia, neurological changes, and a petechial rash (often in the axilla/chest) after a long-bone fracture is classic for fat embolism."
  },
  {
    "question": "What is the primary treatment for a patient with 'Methemoglobinemia' (e.g., after exposure to benzocaine) whose levels are >20%?",
    "option_a": "Hydroxocobalamin",
    "option_b": "Methylene Blue",
    "option_c": "Fomepizole",
    "option_d": "N-acetylcysteine",
    "correct_answer": "B",
    "explanation": "Methylene blue acts as a cofactor for the enzyme that reduces methemoglobin back to functional hemoglobin."
  },
  {
    "question": "Which heart valve is most commonly injured in 'Blunt Chest Trauma'?",
    "option_a": "Mitral valve",
    "option_b": "Aortic valve",
    "option_c": "Tricuspid valve",
    "option_d": "Pulmonic valve",
    "correct_answer": "B",
    "explanation": "The aortic valve is the most frequently damaged valve due to the high pressures in the left heart during a sudden impact."
  },
  {
    "question": "A patient with a 'broken neck' is hypotensive (80/40) but has a heart rate of 55 bpm. This is characteristic of:",
    "option_a": "Hypovolemic shock",
    "option_b": "Neurogenic shock",
    "option_c": "Septic shock",
    "option_d": "Cardiogenic shock",
    "correct_answer": "B",
    "explanation": "Loss of sympathetic tone prevents the heart from beating faster to compensate for low blood pressure."
  },
  {
    "question": "In the management of 'Tricyclic Antidepressant' (TCA) overdose, what is the primary indication for starting a Sodium Bicarbonate infusion?",
    "option_a": "The patient is sleepy",
    "option_b": "QRS duration > 100 ms on ECG",
    "option_c": "The patient has a headache",
    "option_d": "Low blood sugar",
    "correct_answer": "B",
    "explanation": "TCAs block fast sodium channels in the heart; alkalinization and high sodium loads help overcome this blockade to prevent arrhythmias."
  },
  {
    "question": "A patient presents with 'painless' vision loss and 'flashing lights'. Fundoscopy shows a 'wrinkled' or 'billowing' retina. Diagnosis?",
    "option_a": "Central retinal artery occlusion",
    "option_b": "Retinal Detachment",
    "option_c": "Vitreous hemorrhage",
    "option_d": "Macular degeneration",
    "correct_answer": "B",
    "explanation": "Flashing lights (photopsia) and floaters often precede the actual detachment of the retina."
  },
  {
    "question": "Which of the following is a 'Hard Sign' of an arterial injury in an extremity?",
    "option_a": "Small hematoma",
    "option_b": "Pulsatile hemorrhage or bruit/thrill over the injury",
    "option_c": "Proximity to a nerve",
    "option_d": "Moderate pain",
    "correct_answer": "B",
    "explanation": "Hard signs indicate a definite vascular injury requiring immediate surgical exploration or repair."
  },
  {
    "question": "What is the first-line treatment for 'Hypoglycemia' in an unconscious patient with NO intravenous access?",
    "option_a": "Oral glucose gel",
    "option_b": "Glucagon (IM or SC)",
    "option_c": "Normal Saline infusion",
    "option_d": "Insulin injection",
    "correct_answer": "B",
    "explanation": "If IV access is unavailable, glucagon can be given to mobilize liver glucose stores quickly."
  },
  {
    "question": "A 10-year-old child presents with a 'barking' cough and inspiratory stridor. What is the most appropriate initial treatment for severe symptoms?",
    "option_a": "Antibiotics",
    "option_b": "Nebulized Epinephrine and Dexamethasone",
    "option_c": "Albuterol",
    "option_d": "Codeine syrup",
    "correct_answer": "B",
    "explanation": "Croup is managed with steroids to reduce inflammation and racemic epinephrine to rapidly reduce airway edema."
  },
  {
    "question": "Which of the following describes the 'Lichtenberg figure' seen on a lightning strike victim's skin?",
    "option_a": "A deep third-degree burn",
    "option_b": "A transient ferning or 'feathering' pattern",
    "option_c": "A circular exit wound",
    "option_d": "A bruise",
    "correct_answer": "B",
    "explanation": "These are not true burns but rather inflammatory responses to the electrical discharge on the skin surface."
  },
  {
    "question": "In a patient with 'Septic Shock', what is the recommended volume for the initial crystalloid fluid bolus?",
    "option_a": "10 mL/kg",
    "option_b": "30 mL/kg",
    "option_c": "50 mL/kg",
    "option_d": "1 Liter for everyone",
    "correct_answer": "B",
    "explanation": "Sepsis bundles recommend an initial aggressive fluid resuscitation of 30 mL/kg within the first 3 hours."
  },
  {
    "question": "A patient presents with 'mUDPILES' metabolic acidosis and an elevated 'Osmolar Gap'. Which of the following is a possible cause?",
    "option_a": "Salicylates",
    "option_b": "Ethylene Glycol",
    "option_c": "Iron",
    "option_d": "Lactic acid",
    "correct_answer": "B",
    "explanation": "Toxic alcohols like ethylene glycol and methanol cause both an anion gap and an osmolar gap because they are small, unmeasured molecules."
  },
  {
    "question": "What is the primary landmark for performing an 'Emergency Needle Thoracostomy' (Decompression)?",
    "option_a": "2nd intercostal space at the midclavicular line",
    "option_b": "4th or 5th intercostal space at the anterior axillary line",
    "option_c": "1st intercostal space",
    "option_d": "The mid-sternum",
    "correct_answer": "B",
    "explanation": "Updated ATLS guidelines prefer the 4th/5th intercostal space (anterior axillary line) because the chest wall is thinner there, increasing the success rate."
  },
  {
    "question": "Which of the following is the hallmark of 'Anaphylaxis' that necessitates the use of Epinephrine?",
    "option_a": "Urticaria (hives) alone",
    "option_b": "Systemic involvement (respiratory distress or hypotension)",
    "option_c": "A local mosquito bite",
    "option_d": "Nausea only",
    "correct_answer": "B",
    "explanation": "Epinephrine is indicated when there are signs of airway compromise or cardiovascular collapse."
  },
  {
    "question": "A patient presents with a 'fixed and dilated' pupil after a head injury. This indicates compression of which cranial nerve?",
    "option_a": "CN II",
    "option_b": "CN III (Oculomotor)",
    "option_c": "CN IV",
    "option_d": "CN VI",
    "correct_answer": "B",
    "explanation": "Uncal herniation pushes the temporal lobe against the 3rd cranial nerve, paralyzing the parasympathetic fibers that constrict the pupil."
  }
]

COURSE_ID = "NVU_MD_Y3_S2_C30"

async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    
    # Get current count
    current_count = await db.mcq_questions.count_documents({"course_id": COURSE_ID})
    print(f"Current questions in course: {current_count}")
    
    # Prepare questions for insertion
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
    
    # Insert questions
    result = await db.mcq_questions.insert_many(questions_to_insert)
    print(f"Inserted {len(result.inserted_ids)} questions")
    
    # Update course mcq_count
    new_count = await db.mcq_questions.count_documents({"course_id": COURSE_ID})
    await db.courses.update_one(
        {"external_id": COURSE_ID},
        {"$set": {"mcq_count": new_count, "mcq_verified": True}}
    )
    print(f"Updated course mcq_count to {new_count}")

if __name__ == "__main__":
    asyncio.run(main())
