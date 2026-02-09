import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

questions_data = [
  {
    "question": "A 55-year-old male is in cardiac arrest with Pulseless Electrical Activity (PEA). Which of the following is a reversible 'H' cause that should be immediately considered?",
    "option_a": "Hyperglycemia",
    "option_b": "Hypovolemia",
    "option_c": "Hypercalcemia",
    "option_d": "Hypomagnesemia",
    "correct_answer": "B",
    "explanation": "The 5 H's are Hypovolemia, Hypoxia, Hydrogen ion (acidosis), Hypo-/hyperkalemia, and Hypothermia. Hypovolemia is a leading cause of PEA."
  },
  {
    "question": "In a trauma patient with suspected urethral injury, which finding on physical examination is an absolute contraindication to blind Foley catheterization?",
    "option_a": "Pelvic pain",
    "option_b": "Blood at the urethral meatus",
    "option_c": "Hematuria on a voided sample",
    "option_d": "Inguinal ecchymosis",
    "correct_answer": "B",
    "explanation": "Blood at the meatus, high-riding prostate, or perineal hematoma suggests urethral disruption. A retrograde urethrogram (RUG) must be performed first."
  },
  {
    "question": "What is the most appropriate initial energy setting for synchronized cardioversion in a stable patient with monomorphic Ventricular Tachycardia?",
    "option_a": "20 Joules",
    "option_b": "100 Joules",
    "option_c": "200 Joules",
    "option_d": "360 Joules",
    "correct_answer": "B",
    "explanation": "ACLS guidelines recommend an initial dose of 100J for stable monomorphic VT requiring synchronized cardioversion."
  },
  {
    "question": "A 22-year-old female presents with a 'stiff neck' and high fever. Physical exam reveals a positive Brudzinski sign. What is the priority management step after stabilizing the ABCs?",
    "option_a": "Immediate Head CT",
    "option_b": "Prompt administration of IV antibiotics and dexamethasone",
    "option_c": "Lumbar puncture to confirm the diagnosis",
    "option_d": "Viral PCR testing",
    "correct_answer": "B",
    "explanation": "In suspected bacterial meningitis, early antibiotics are critical for survival and should not be delayed by imaging or procedures if the diagnosis is highly likely."
  },
  {
    "question": "A patient is brought to the ED with a suspected Beta-blocker overdose. He is bradycardic (HR 35) and hypotensive (BP 75/40). Atropine was ineffective. What is the preferred next-line pharmacological treatment?",
    "option_a": "Norepinephrine infusion",
    "option_b": "High-dose intravenous Glucagon",
    "option_c": "Intravenous Calcium Chloride",
    "option_d": "Amiodarone bolus",
    "correct_answer": "B",
    "explanation": "Glucagon bypasses blocked beta-receptors to increase intracellular cAMP, which improves heart rate and contractility in beta-blocker toxicity."
  },
  {
    "question": "Which of the following ECG changes is the most specific indicator of posterior wall myocardial infarction?",
    "option_a": "ST-elevation in lead aVR",
    "option_b": "ST-depression in leads V1–V3 with tall R waves",
    "option_c": "T-wave inversion in lead III",
    "option_d": "Pathologic Q waves in leads I and aVL",
    "correct_answer": "B",
    "explanation": "V1-V3 act as 'mirror leads' for the posterior wall; ST-depression there represents ST-elevation in the posterior leads."
  },
  {
    "question": "A patient with severe hyperkalemia (K+ = 7.2) has a widened QRS complex. What is the physiological purpose of administering Calcium Gluconate?",
    "option_a": "To drive potassium into the cells",
    "option_b": "To stabilize the cardiac myocyte membrane potential",
    "option_c": "To promote renal excretion of potassium",
    "option_d": "To neutralize metabolic acidosis",
    "correct_answer": "B",
    "explanation": "Calcium does not lower serum potassium levels; it antagonizes the membrane-excitability effect of potassium to prevent arrest."
  },
  {
    "question": "A victim of a house fire presents with carbonaceous sputum and singed nasal hairs. He is currently stable. What is the most appropriate next step?",
    "option_a": "Wait for a Chest X-ray",
    "option_b": "Prophylactic endotracheal intubation",
    "option_c": "Start nebulized albuterol",
    "option_d": "Discharge with follow-up",
    "correct_answer": "B",
    "explanation": "Signs of thermal injury to the airway (soot, singed hair) predict rapid upper airway edema; definitive airway control should be established early."
  },
  {
    "question": "A patient with 'pinpoint' pupils and a respiratory rate of 4 has failed to respond to a 2mg dose of Naloxone. What is the most appropriate next step?",
    "option_a": "Wait 10 minutes for the drug to work",
    "option_b": "Administer a second, higher dose of Naloxone (e.g., 4-10mg)",
    "option_c": "Give Flumazenil",
    "option_d": "Give Physostigmine",
    "correct_answer": "B",
    "explanation": "Some synthetic opioids (e.g., Fentanyl) require much higher doses of naloxone to reverse respiratory depression."
  },
  {
    "question": "What is the recommended compression depth for adult CPR?",
    "option_a": "At least 1 inch",
    "option_b": "At least 2 inches (5 cm)",
    "option_c": "At least 3 inches",
    "option_d": "No more than 1.5 inches",
    "correct_answer": "B",
    "explanation": "Adequate depth (2-2.4 inches) is necessary to ensure enough cardiac output during compressions."
  },
  {
    "question": "In the FAST exam, which window is used to evaluate for fluid in the 'Morison's Pouch'?",
    "option_a": "Subxiphoid window",
    "option_b": "Right Upper Quadrant (RUQ) window",
    "option_c": "Left Upper Quadrant (LUQ) window",
    "option_d": "Pelvic window",
    "correct_answer": "B",
    "explanation": "Morison's Pouch is the potential space between the liver and the right kidney, the most dependent area for fluid in the upper abdomen."
  },
  {
    "question": "A patient with severe metabolic acidosis (pH 7.10) after ingesting 'windshield wiper fluid' most likely has toxicity from which substance?",
    "option_a": "Isopropanol",
    "option_b": "Methanol",
    "option_c": "Ethanol",
    "option_d": "Acetaminophen",
    "correct_answer": "B",
    "explanation": "Methanol is a common component of windshield fluid and is metabolized to formic acid, causing profound high anion gap acidosis and optic nerve damage."
  },
  {
    "question": "Which of the following describes 'Neurogenic Shock' as opposed to 'Spinal Shock'?",
    "option_a": "Loss of reflexes below the level of injury",
    "option_b": "Hypotension and bradycardia due to loss of sympathetic tone",
    "option_c": "Hyperreflexia and spasticity",
    "option_d": "Tachycardia and hypertension",
    "correct_answer": "B",
    "explanation": "Neurogenic shock is a hemodynamic state; spinal shock is a neurological state involving loss of spinal cord reflexes."
  },
  {
    "question": "A patient with suspected carbon monoxide (CO) poisoning has an SpO2 of 100% on pulse oximetry. What does this indicate?",
    "option_a": "The patient is definitely not poisoned",
    "option_b": "The pulse oximeter is inaccurate as it cannot distinguish between oxyhemoglobin and carboxyhemoglobin",
    "option_c": "The oxygen levels are normal",
    "option_d": "The patient is hyperventilating",
    "correct_answer": "B",
    "explanation": "Standard pulse oximetry reads carboxyhemoglobin as oxyhemoglobin, leading to dangerously false normal results."
  },
  {
    "question": "What is the clinical definition of a 'Hypertensive Emergency'?",
    "option_a": "BP > 180/120 with no symptoms",
    "option_b": "BP > 180/120 with evidence of acute end-organ damage",
    "option_c": "BP > 140/90 in a young patient",
    "option_d": "BP > 200/100 during a panic attack",
    "correct_answer": "B",
    "explanation": "The presence of end-organ damage (e.g., encephalopathy, MI, renal failure) is what differentiates an emergency from hypertensive urgency."
  },
  {
    "question": "A 10-year-old presents with a 'strawberry tongue', fever, and a sandpaper-like rash. What is the diagnosis?",
    "option_a": "Measles",
    "option_b": "Scarlet Fever",
    "option_c": "Meningococcemia",
    "option_d": "Chickenpox",
    "correct_answer": "B",
    "explanation": "Scarlet fever (Group A Strep) is classic for the combination of fever, strawberry tongue, and a fine, rough rash."
  },
  {
    "question": "What is the 'lethal' triad of trauma that contributes to high mortality in bleeding patients?",
    "option_a": "Tachycardia, Hypotension, Fever",
    "option_b": "Acidosis, Coagulopathy, Hypothermia",
    "option_c": "Hypovolemia, Hypoxia, Hypoglycemia",
    "option_d": "Hyperkalemia, Hypernatremia, Acidosis",
    "correct_answer": "B",
    "explanation": "These three factors create a vicious cycle that impairs clot formation and worsens bleeding."
  },
  {
    "question": "A patient with an intentional Paracetamol (Acetaminophen) overdose presents 2 hours after ingestion. What is the primary management step?",
    "option_a": "Immediate N-acetylcysteine (NAC) administration",
    "option_b": "Administration of Activated Charcoal",
    "option_c": "Wait for the 4-hour levels before doing anything",
    "option_d": "Hemodialysis",
    "correct_answer": "B",
    "explanation": "Charcoal is effective if given within 1-2 hours of ingestion. NAC is started based on the level at 4 hours or if the time is unknown."
  },
  {
    "question": "Which of the following is a classic sign of 'Tension Pneumothorax'?",
    "option_a": "Muffled heart sounds",
    "option_b": "Tracheal deviation away from the affected side",
    "option_c": "Dullness to percussion",
    "option_d": "Hypertension",
    "correct_answer": "B",
    "explanation": "Air pressure builds up and pushes the mediastinum to the opposite side, compromising venous return and causing shock."
  },
  {
    "question": "A patient presents with 'pitting' lower extremity edema and severe dyspnea. Chest X-ray shows 'bat-wing' opacities. BP is 210/110. Which medication is first-line for rapid preload reduction?",
    "option_a": "Intravenous Metoprolol",
    "option_b": "Nitroglycerin (IV or Sublingual)",
    "option_c": "Intravenous Normal Saline",
    "option_d": "Dopamine",
    "correct_answer": "B",
    "explanation": "Nitrates cause rapid venodilation, reducing preload and improving pulmonary edema in hypertensive acute heart failure."
  },
  {
    "question": "A patient with severe hypothermia (core temp 28°C) is in cardiac arrest. According to ACLS guidelines, how should defibrillation and medications be handled?",
    "option_a": "Standard doses of Epinephrine every 3 minutes",
    "option_b": "Limit to one shock; withhold medications until core temperature is > 30°C",
    "option_c": "No shocks allowed until the patient is 37°C",
    "option_d": "Continuous CPR with no ACLS interventions",
    "correct_answer": "B",
    "explanation": "The cold heart is often resistant to drugs and shocks; ACLS recommends limiting interventions until some rewarming has occurred."
  },
  {
    "question": "Which physical sign helps differentiate an 'Incomplete' spinal cord injury from a 'Complete' one in the acute phase?",
    "option_a": "Presence of a motor response in the hands",
    "option_b": "Sacral sparing (e.g., anal sphincter contraction or sensation)",
    "option_c": "Ability to breathe without a ventilator",
    "option_d": "Normal blood pressure",
    "correct_answer": "B",
    "explanation": "Sacral sparing indicates that some fibers in the spinal cord are still intact, defining an incomplete injury."
  },
  {
    "question": "What is the primary treatment for Cyanide poisoning in a victim of smoke inhalation?",
    "option_a": "Sodium Thiosulfate",
    "option_b": "Hydroxocobalamin",
    "option_c": "Methylene Blue",
    "option_d": "Atropine",
    "correct_answer": "B",
    "explanation": "Hydroxocobalamin is the preferred antidote as it does not cause methemoglobinemia, which would be dangerous if CO poisoning is also present."
  },
  {
    "question": "A patient is brought in with 'frostbite' on the fingers. The fingers are white and hard. What is the most appropriate initial rewarming strategy?",
    "option_a": "Gradual rewarming in room air",
    "option_b": "Rapid rewarming in a warm water bath (37°C to 39°C)",
    "option_c": "Rubbing the hands together to generate friction",
    "option_d": "Application of a heating pad at 50°C",
    "correct_answer": "B",
    "explanation": "Rapid rewarming in circulating warm water is the standard of care for frostbite to minimize tissue loss."
  },
  {
    "question": "Which nerve is most likely to be injured in a 'Colles fracture' (distal radius)?",
    "option_a": "Radial nerve",
    "option_b": "Median nerve",
    "option_c": "Ulnar nerve",
    "option_d": "Axillary nerve",
    "correct_answer": "B",
    "explanation": "The median nerve travels through the carpal tunnel and can be compressed or damaged in distal radius fractures."
  },
  {
    "question": "A patient is in anaphylactic shock. Despite two IM doses of Epinephrine, the BP is 70/30. What is the next pharmacological step?",
    "option_a": "Give IM Diphenhydramine",
    "option_b": "Start an intravenous Epinephrine infusion",
    "option_c": "Give 100mg of IV Hydrocortisone",
    "option_d": "Give IV Albuterol",
    "correct_answer": "B",
    "explanation": "Refractory anaphylaxis requires transitioned to intravenous titration of epinephrine."
  },
  {
    "question": "What does a GCS score of 3 indicate?",
    "option_a": "The patient is awake and alert",
    "option_b": "Deepest coma or brain death (no response)",
    "option_c": "Confused but responsive",
    "option_d": "Mild concussion",
    "correct_answer": "B",
    "explanation": "The lowest possible GCS score is 3 (E1, V1, M1)."
  },
  {
    "question": "In a patient with 'Thyroid Storm', which of the following should be AVOIDED for fever control?",
    "option_a": "Acetaminophen",
    "option_b": "Aspirin (Salicylates)",
    "option_c": "Cooling blankets",
    "option_d": "Ice packs",
    "correct_answer": "B",
    "explanation": "Aspirin can displace thyroid hormone from binding proteins, increasing the levels of free T3/T4 and worsening the crisis."
  },
  {
    "question": "Which of the following is a symptom of 'Cushing's Triad', indicating increased ICP?",
    "option_a": "Hypotension",
    "option_b": "Bradycardia",
    "option_c": "Tachycardia",
    "option_d": "Tachypnea",
    "correct_answer": "B",
    "explanation": "Cushing's Triad: Hypertension, Bradycardia, and Irregular respirations."
  },
  {
    "question": "A patient with suspected organophosphate poisoning is drooling, wheezing, and has pinpoint pupils. What is the mechanism of this toxicity?",
    "option_a": "Blockade of muscarinic receptors",
    "option_b": "Irreversible inhibition of Acetylcholinesterase",
    "option_c": "Activation of Beta-2 receptors",
    "option_d": "Inhibition of calcium channels",
    "correct_answer": "B",
    "explanation": "Organophosphates prevent the breakdown of Acetylcholine, leading to a cholinergic crisis (SLUDGE syndrome)."
  },
  {
    "question": "What is the primary medication used to reverse the 'Muscarinic' effects of organophosphate poisoning (e.g., salivation, bradycardia)?",
    "option_a": "Pralidoxime (2-PAM)",
    "option_b": "Atropine",
    "option_c": "Naloxone",
    "option_d": "Sodium Bicarbonate",
    "correct_answer": "B",
    "explanation": "Atropine is a competitive muscarinic antagonist that addresses the immediate life-threatening secretions and bradycardia."
  },
  {
    "question": "A patient presents with a 'mid-shaft' fracture of the humerus. Which motor function should be tested to rule out nerve injury?",
    "option_a": "Wrist flexion",
    "option_b": "Wrist extension (Radial nerve)",
    "option_c": "Finger abduction",
    "option_d": "Thumb opposition",
    "correct_answer": "B",
    "explanation": "The radial nerve wraps around the humerus; injury leads to 'wrist drop' due to inability to extend the wrist."
  },
  {
    "question": "Which of the following is the 'Gold Standard' for verifying tube placement in a child in the ER?",
    "option_a": "Auscultation of breath sounds",
    "option_b": "Waveform capnography (EtCO2)",
    "option_c": "Observing chest rise",
    "option_d": "Presence of vapor in the tube",
    "correct_answer": "B",
    "explanation": "Capnography is the most reliable method for both adults and children to ensure tracheal placement."
  },
  {
    "question": "A patient with suspected acute stroke has a normal non-contrast Head CT. Does this rule out a stroke?",
    "option_a": "Yes, completely",
    "option_b": "No, early ischemic strokes often don't show up on CT for hours",
    "option_c": "Yes, if the patient has no symptoms",
    "option_d": "No, because the CT only shows old strokes",
    "correct_answer": "B",
    "explanation": "The primary role of the initial CT in stroke is to rule out hemorrhage, not to diagnose the ischemia itself."
  },
  {
    "question": "In the management of septic shock, what is the target 'Mean Arterial Pressure' (MAP) for most patients?",
    "option_a": "At least 50 mmHg",
    "option_b": "At least 65 mmHg",
    "option_c": "At least 90 mmHg",
    "option_d": "At least 120 mmHg",
    "correct_answer": "B",
    "explanation": "A MAP of 65 is generally considered sufficient to provide adequate tissue perfusion to vital organs."
  },
  {
    "question": "A 70-year-old male with atrial fibrillation presents with sudden onset of severe abdominal pain. His exam is relatively benign. What should you immediately suspect?",
    "option_a": "Appendicitis",
    "option_b": "Acute Mesenteric Ischemia",
    "option_c": "Gallbladder stones",
    "option_d": "Bowel obstruction",
    "correct_answer": "B",
    "explanation": "Sudden agonizing pain 'out of proportion' to exam findings in a patient with an embolic risk (AFib) is classic for mesenteric ischemia."
  },
  {
    "question": "What is the primary treatment for a symptomatic 'Brown Recluse' spider bite?",
    "option_a": "Immediate surgical excision",
    "option_b": "Wound care and observation",
    "option_c": "Routine broad-spectrum antibiotics",
    "option_d": "Antivenom",
    "correct_answer": "B",
    "explanation": "Most brown recluse bites are managed supportively; early excision is no longer recommended and can worsen scarring."
  },
  {
    "question": "In pediatric resuscitation, what is the preferred site for intraosseous (IO) access?",
    "option_a": "Proximal humerus",
    "option_b": "Proximal tibia",
    "option_c": "Distal radius",
    "option_d": "Sternum",
    "correct_answer": "B",
    "explanation": "The flat portion of the proximal tibia, 1-2cm distal to the tibial tuberosity, is the standard IO site in children."
  },
  {
    "question": "A patient presents with tachycardia, hypotension, and 'muffled' heart sounds after a blunt chest injury. What is the diagnosis?",
    "option_a": "Tension pneumothorax",
    "option_b": "Cardiac Tamponade",
    "option_c": "Massive hemothorax",
    "option_d": "Flail chest",
    "correct_answer": "B",
    "explanation": "These are the components of Beck's Triad, indicating fluid in the pericardial sac compressing the heart."
  },
  {
    "question": "A patient with 'mUDPILES' metabolic acidosis has an osmolar gap of 25. Which ingestion is most likely?",
    "option_a": "Salicylates",
    "option_b": "Ethylene Glycol",
    "option_c": "Iron",
    "option_d": "Lactic acid",
    "correct_answer": "B",
    "explanation": "Both methanol and ethylene glycol cause a high anion gap AND a high osmolar gap."
  },
  {
    "question": "Which of the following is a 'shockable' rhythm?",
    "option_a": "Asystole",
    "option_b": "Ventricular Fibrillation",
    "option_c": "Pulseless Electrical Activity (PEA)",
    "option_d": "Normal Sinus Rhythm",
    "correct_answer": "B",
    "explanation": "Shockable rhythms are VF and pulseless Ventricular Tachycardia (pVT)."
  },
  {
    "question": "A patient presents with a 'bull's-eye' (target) rash after a camping trip. What is the treatment of choice?",
    "option_a": "Ciprofloxacin",
    "option_b": "Doxycycline",
    "option_c": "Penicillin V",
    "option_d": "Topical steroids",
    "correct_answer": "B",
    "explanation": "Erythema migrans is the early stage of Lyme disease, which is treated with Doxycycline."
  },
  {
    "question": "In mass casualty triage (START system), what tag is given to a patient with no spontaneous respirations even after airway positioning?",
    "option_a": "Red",
    "option_b": "Black",
    "option_c": "Yellow",
    "option_d": "Green",
    "correct_answer": "B",
    "explanation": "Black tags are for the deceased or those whose injuries are unsurvivable in the field."
  },
  {
    "question": "What is the primary risk of using 'Fomepizole' in alcohol dehydrogenase inhibition?",
    "option_a": "Severe hypertension",
    "option_b": "It is generally safe and prevents toxic metabolite formation",
    "option_c": "Liver failure",
    "option_d": "Kidney stones",
    "correct_answer": "B",
    "explanation": "Fomepizole is the standard treatment for methanol/ethylene glycol poisoning with very few side effects."
  },
  {
    "question": "A patient presents with severe RUQ pain, fever, and jaundice. What is the most likely diagnosis?",
    "option_a": "Acute cholecystitis",
    "option_b": "Ascending Cholangitis",
    "option_c": "Hepatitis B",
    "option_d": "Pancreatitis",
    "correct_answer": "B",
    "explanation": "Charcot's triad (fever, jaundice, RUQ pain) is diagnostic for cholangitis."
  },
  {
    "question": "Which of the following is a component of 'Beck's Triad'?",
    "option_a": "Hypertension",
    "option_b": "Jugular Venous Distension (JVD)",
    "option_c": "Tachycardia",
    "option_d": "Fever",
    "correct_answer": "B",
    "explanation": "Beck's triad: Hypotension, JVD, and Muffled heart sounds."
  },
  {
    "question": "What is the medication of choice for an adult in status epilepticus (seizure > 5 mins)?",
    "option_a": "Phenytoin",
    "option_b": "Lorazepam (or Midazolam)",
    "option_c": "Levetiracetam",
    "option_d": "Valproic acid",
    "correct_answer": "B",
    "explanation": "Benzodiazepines are the first-line agents to terminate active seizures."
  },
  {
    "question": "A patient has a traumatic brain injury and a blown pupil (fixed and dilated). Which cranial nerve is affected?",
    "option_a": "CN II",
    "option_b": "CN III (Oculomotor)",
    "option_c": "CN IV",
    "option_d": "CN VI",
    "correct_answer": "B",
    "explanation": "Uncal herniation compresses the CN III, leading to loss of parasympathetic tone and a dilated pupil."
  },
  {
    "question": "What is the 'Parkland Formula' used for?",
    "option_a": "Calculating the risk of stroke",
    "option_b": "Fluid resuscitation in burn patients",
    "option_c": "Determining antibiotic dose",
    "option_d": "GCS calculation",
    "correct_answer": "B",
    "explanation": "4 mL x Weight (kg) x %BSA burned determines the fluid needed in the first 24 hours."
  },
  {
    "question": "Which heart rhythm shows 'sawtooth' waves on the ECG?",
    "option_a": "Atrial Fibrillation",
    "option_b": "Atrial Flutter",
    "option_c": "Ventricular Tachycardia",
    "option_d": "Sinus Rhythm",
    "correct_answer": "B",
    "explanation": "Atrial flutter is characterized by rapid, regular sawtooth-shaped F waves."
  }
]

COURSE_ID = "NVU_MD_Y4_S2_C39"

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
