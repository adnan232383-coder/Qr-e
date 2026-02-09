import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

questions_data = [
  {
    "question": "Which of the following CT findings is most suggestive of an 'Aortic Dissection' (Stanford Type A)?",
    "option_a": "A dilated aorta with a single lumen and mural thrombus",
    "option_b": "An intimal flap within the ascending aorta",
    "option_c": "A crescentic hyperdensity within the wall of the descending aorta",
    "option_d": "Extravasation of contrast into the mediastinum only",
    "correct_answer": "B",
    "explanation": "Type A dissections involve the ascending aorta; the pathognomonic finding is an intimal flap dividing the aorta into true and false lumens."
  },
  {
    "question": "What is the characteristic radiographic finding of 'Pneumatosis Intestinalis' on an abdominal X-ray?",
    "option_a": "A large air-fluid level in the stomach",
    "option_b": "Linear or curvilinear lucencies within the bowel wall",
    "option_c": "Air under the right hemidiaphragm",
    "option_d": "Dilated loops of colon with no gas in the rectum",
    "correct_answer": "B",
    "explanation": "Pneumatosis intestinalis is the presence of gas within the wall of the bowel, often indicating ischemia or necrotizing enterocolitis."
  },
  {
    "question": "In Neuroimaging, which MRI sequence is specifically designed to detect 'Microhemorrhages' or 'Mineral Deposition' (like iron or calcium)?",
    "option_a": "T1-weighted",
    "option_b": "Susceptibility-Weighted Imaging (SWI) or T2*",
    "option_c": "Diffusion-Weighted Imaging (DWI)",
    "option_d": "FLAIR",
    "correct_answer": "B",
    "explanation": "SWI is highly sensitive to substances that cause local magnetic field distortions, such as deoxygenated blood, ferritin, and calcium."
  },
  {
    "question": "A 'Tree-in-bud' pattern on high-resolution CT (HRCT) of the chest is most commonly associated with:",
    "option_a": "Pulmonary edema",
    "option_b": "Infectious bronchiolitis (e.g., Tuberculosis spread)",
    "option_c": "Idiopathic pulmonary fibrosis",
    "option_d": "Lung adenocarcinoma",
    "correct_answer": "B",
    "explanation": "The tree-in-bud sign represents small airway impaction with mucus, pus, or fluid, classic for endobronchial spread of infection."
  },
  {
    "question": "Which of the following is an absolute contraindication to the administration of 'Iodinated' intravenous contrast?",
    "option_a": "History of shellfish allergy",
    "option_b": "History of a prior anaphylactic reaction to iodinated contrast",
    "option_c": "Age over 80 years",
    "option_d": "Mild nausea during a previous scan",
    "correct_answer": "B",
    "explanation": "A true previous anaphylactic reaction is a strict contraindication unless the scan is life-saving and pre-medication is administered, but usually, an alternative (like MRI) is sought."
  },
  {
    "question": "On an ultrasound of the biliary tree, 'Posterior Acoustic Enhancement' is typically seen behind which structure?",
    "option_a": "A calcified gallstone",
    "option_b": "A simple fluid-filled cyst",
    "option_c": "A solid liver mass",
    "option_d": "The diaphragm",
    "correct_answer": "B",
    "explanation": "Fluid attenuates sound less than solid tissue, making the area behind a fluid collection appear brighter than surrounding tissues."
  },
  {
    "question": "The 'Whirlpool Sign' on an abdominal CT scan is the hallmark of:",
    "option_a": "Acute appendicitis",
    "option_b": "Midgut volvulus or internal hernia",
    "option_c": "Small bowel obstruction due to adhesions",
    "option_d": "Intussusception",
    "correct_answer": "B",
    "explanation": "The sign represents the twisting of the mesentery and vessels around the point of rotation in a volvulus."
  },
  {
    "question": "Which imaging modality is most sensitive for detecting early 'Osteomyelitis' (bone infection)?",
    "option_a": "Plain X-ray",
    "option_b": "MRI",
    "option_c": "Ultrasound",
    "option_d": "Bone mineral density scan",
    "correct_answer": "B",
    "explanation": "MRI can detect bone marrow edema and inflammation within days of infection, whereas X-ray changes often take 2-3 weeks to appear."
  },
  {
    "question": "A 'Ground-glass opacity' (GGO) on a chest CT is defined as:",
    "option_a": "An area of dense whiteness that obscures underlying vessels",
    "option_b": "A hazy increase in lung density where vessels can still be seen through it",
    "option_c": "A thick-walled cavity with an air-fluid level",
    "option_d": "Air within the pleural space",
    "correct_answer": "B",
    "explanation": "GGO represents partial filling of alveoli or interstitial thickening; unlike consolidation, the underlying lung structures remain visible."
  },
  {
    "question": "In a patient with 'Subarachnoid Hemorrhage', what is the most common cause of the bleeding seen on a Head CT?",
    "option_a": "Trauma",
    "option_b": "Ruptured 'Berry' aneurysm",
    "option_c": "Arteriovenous malformation (AVM)",
    "option_d": "Hypertensive crisis",
    "correct_answer": "B",
    "explanation": "While trauma is the most common cause overall, a ruptured saccular (berry) aneurysm is the most common cause of non-traumatic SAH."
  },
  {
    "question": "What does a 'Hot Spot' on a Technetium-99m bone scan typically represent?",
    "option_a": "Areas of decreased blood flow",
    "option_b": "Areas of increased osteoblastic activity (bone formation)",
    "option_c": "Dead bone tissue",
    "option_d": "A simple bone cyst",
    "correct_answer": "B",
    "explanation": "The tracer accumulates in areas where bone is actively remodeling, such as fractures, metastases, or infections."
  },
  {
    "question": "Which of the following is true for 'Magnetic Resonance Cholangiopancreatography' (MRCP)?",
    "option_a": "It requires the use of intravenous gadolinium contrast",
    "option_b": "It is a non-invasive, T2-weighted sequence that makes stationary fluid bright",
    "option_c": "It allows for therapeutic stone extraction like ERCP",
    "option_d": "It is an X-ray based procedure",
    "correct_answer": "B",
    "explanation": "MRCP is purely diagnostic; it uses the high signal of bile and pancreatic juice on T2 sequences to create images without contrast or intervention."
  },
  {
    "question": "A 'Bat's Wing' or 'Butterfly' distribution of perihilar opacities on a Chest X-ray is classic for:",
    "option_a": "Pneumothorax",
    "option_b": "Acute alveolar pulmonary edema",
    "option_c": "Pulmonary embolism",
    "option_d": "Tuberculosis",
    "correct_answer": "B",
    "explanation": "Fluid leakage into the alveolar spaces in CHF often starts in the central perihilar regions, sparing the periphery."
  },
  {
    "question": "Which radiological sign involves the 'displacement of the trachea' and 'flattening of the heart' in a newborn?",
    "option_a": "Congenital Diaphragmatic Hernia",
    "option_b": "Pneumopericardium",
    "option_c": "Thymic sail sign",
    "option_d": "Meconium aspiration",
    "correct_answer": "A",
    "explanation": "Abdominal contents in the chest cause a significant mass effect, shifting the mediastinum to the contralateral side."
  },
  {
    "question": "On a non-contrast CT, 'Fat' is distinguished from 'Fluid' by its:",
    "option_a": "Brighter appearance",
    "option_b": "Negative Hounsfield Units (-50 to -150 HU)",
    "option_c": "Higher Hounsfield Units (+50 HU)",
    "option_d": "Same appearance as bone",
    "correct_answer": "B",
    "explanation": "Fat is less dense than water (0 HU), giving it a characteristic dark (black) appearance on CT scans."
  },
  {
    "question": "Which imaging feature helps distinguish 'Large Bowel Obstruction' (LBO) from 'Small Bowel Obstruction' (SBO)?",
    "option_a": "Presence of air-fluid levels",
    "option_b": "Peripheral location of the dilated loops and presence of haustral markings",
    "option_c": "Absence of rectal gas",
    "option_d": "High-pitched bowel sounds",
    "correct_answer": "B",
    "explanation": "Large bowel loops are usually around the periphery of the abdomen and have haustra (incomplete folds), while small bowel is central and has valvulae conniventes (complete folds)."
  },
  {
    "question": "What is the primary risk of using 'Gadolinium' in a patient with a glomerular filtration rate (eGFR) below 30?",
    "option_a": "Thyroid storm",
    "option_b": "Nephrogenic Systemic Fibrosis (NSF)",
    "option_c": "Acute tubular necrosis",
    "option_d": "Ototoxicity",
    "correct_answer": "B",
    "explanation": "NSF is a rare but severe systemic fibrosing condition linked specifically to gadolinium exposure in patients with advanced renal failure."
  },
  {
    "question": "On a T2-weighted MRI of the brain, 'White Matter' appears ______ compared to 'Grey Matter'.",
    "option_a": "Brighter",
    "option_b": "Darker",
    "option_c": "Same color",
    "option_d": "Water-like",
    "correct_answer": "B",
    "explanation": "T2 sequences are 'water bright'. Grey matter has more water than white matter, so grey matter is brighter than white matter."
  },
  {
    "question": "The 'Cupola Sign' on a supine abdominal X-ray refers to air located:",
    "option_a": "Under the diaphragm in an upright patient",
    "option_b": "Under the central tendon of the diaphragm in a supine patient",
    "option_c": "Inside the stomach",
    "option_d": "In the scrotum",
    "correct_answer": "B",
    "explanation": "This is a sign of pneumoperitoneum on a supine film, where air accumulates under the central diaphragm, forming a dome-shaped lucency."
  },
  {
    "question": "In Interventional Radiology, an 'IVC Filter' is primarily placed to prevent:",
    "option_a": "Renal failure",
    "option_b": "Pulmonary Embolism in patients who cannot take anticoagulants",
    "option_c": "Deep vein thrombosis",
    "option_d": "Aortic aneurysm rupture",
    "correct_answer": "B",
    "explanation": "IVC filters trap large clots migrating from the lower extremities to the lungs when anticoagulation is contraindicated or has failed."
  },
  {
    "question": "The 'Hampton's Hump' on a Chest X-ray is a sign of:",
    "option_a": "Pulmonary edema",
    "option_b": "Pulmonary infarction distal to an embolism",
    "option_c": "Pneumothorax",
    "option_d": "Lung cancer",
    "correct_answer": "B",
    "explanation": "It is a peripheral, wedge-shaped opacity with its base against the pleura, representing lung tissue death due to loss of blood supply."
  },
  {
    "question": "Which of the following is a classic radiological feature of 'Osteoarthritis' on X-ray?",
    "option_a": "Periarticular osteopenia",
    "option_b": "Joint space narrowing, osteophytes, and subchondral sclerosis",
    "option_c": "Uniform joint space loss and erosions",
    "option_d": "Bone destruction with no new bone formation",
    "correct_answer": "B",
    "explanation": "Osteoarthritis is a 'productive' process with bone spurs (osteophytes) and hardening (sclerosis) of the bone ends."
  },
  {
    "question": "In a patient with suspected 'Appendicitis', what is the significance of seeing an 'Appendicolith' on a CT scan?",
    "option_a": "It rules out appendicitis",
    "option_b": "It is a calcified stone that often obstructs the lumen and supports the diagnosis",
    "option_c": "It is a sign of chronic constipation only",
    "option_d": "It means the patient needs a colonoscopy",
    "correct_answer": "B",
    "explanation": "An appendicolith (fecalith) is found in about 25-30% of cases and is a strong indicator of inflammation when combined with other signs."
  },
  {
    "question": "The 'Terry-Thomas' sign on a wrist X-ray (widened gap between scaphoid and lunate) indicates:",
    "option_a": "Scaphoid fracture",
    "option_b": "Scapholunate ligament dissociation",
    "option_c": "Radial head fracture",
    "option_d": "Carpal tunnel syndrome",
    "correct_answer": "B",
    "explanation": "A gap of >3mm suggests a ligamentous tear, named after a famous British actor with a gap between his front teeth."
  },
  {
    "question": "On a Head CT, 'Vasogenic Edema' (associated with tumors or abscesses) typically involves:",
    "option_a": "Grey matter only",
    "option_b": "White matter, sparing the grey matter",
    "option_c": "Both grey and white matter equally",
    "option_d": "The ventricles",
    "correct_answer": "B",
    "explanation": "Vasogenic edema occurs due to blood-brain barrier breakdown and spreads through the extracellular spaces of the white matter, often in a finger-like pattern."
  },
  {
    "question": "Which imaging procedure involves injecting contrast into the subarachnoid space to evaluate the spinal cord?",
    "option_a": "Arteriography",
    "option_b": "Myelography",
    "option_c": "Cystography",
    "option_d": "Pyelography",
    "correct_answer": "B",
    "explanation": "Myelography uses X-ray/fluoroscopy and contrast to visualize the cord, nerves, and spinal canal."
  },
  {
    "question": "The 'Crescent Sign' on an abdominal X-ray is classic for which pediatric emergency?",
    "option_a": "Pyloric stenosis",
    "option_b": "Intussusception",
    "option_c": "Hirschsprung disease",
    "option_d": "Duodenal atresia",
    "correct_answer": "B",
    "explanation": "The crescent sign represents the head of the intussusceptum protruding into an air-filled pocket in the colon."
  },
  {
    "question": "Which feature is more characteristic of a 'Benign' than a 'Malignant' bone lesion on X-ray?",
    "option_a": "Wide zone of transition",
    "option_b": "Narrow zone of transition (geographic destruction)",
    "option_c": "Cortical destruction",
    "option_d": "Sunburst periosteal reaction",
    "correct_answer": "B",
    "explanation": "A sharp, well-defined border (narrow zone of transition) suggests a slow-growing, likely benign process."
  },
  {
    "question": "A 'Pneumobilia' (air in the biliary tree) on a CT scan is a classic component of which condition?",
    "option_a": "Acute cholecystitis",
    "option_b": "Gallstone ileus",
    "option_c": "Ascending cholangitis",
    "option_d": "Hepatocellular carcinoma",
    "correct_answer": "B",
    "explanation": "Air enters the bile ducts via a cholecystoenteric fistula, allowing a large stone to pass into the bowel and cause obstruction."
  },
  {
    "question": "In chest radiology, what does 'Consolidation' refer to?",
    "option_a": "A collapsed lung",
    "option_b": "Replacement of alveolar air by fluid, pus, blood, or cells",
    "option_c": "A large mass in the mediastinum",
    "option_d": "A hole in the lung",
    "correct_answer": "B",
    "explanation": "Consolidation is the hallmark of pneumonia, where the air spaces are completely filled with inflammatory exudate."
  },
  {
    "question": "On an MRI, 'Flow Void' describes the appearance of:",
    "option_a": "A blood clot",
    "option_b": "Rapidly moving blood (appearing black)",
    "option_c": "Bone marrow",
    "option_d": "Muscle",
    "correct_answer": "B",
    "explanation": "In standard spin-echo sequences, protons in fast-moving blood leave the slice before they can provide a signal, resulting in a black area."
  },
  {
    "question": "The 'Snowman Sign' on a pediatric chest X-ray is characteristic of:",
    "option_a": "Tetralogy of Fallot",
    "option_b": "Total Anomalous Pulmonary Venous Return (TAPVR) - Supracardiac type",
    "option_c": "Transposition of the Great Arteries",
    "option_d": "Coarctation of the aorta",
    "correct_answer": "B",
    "explanation": "The wide superior mediastinum (dilated veins) and the heart base create a figure-of-eight or snowman shape."
  },
  {
    "question": "Which view is the most appropriate to look for a small 'Pneumothorax' in an upright patient?",
    "option_a": "Supine AP",
    "option_b": "PA Expiratory film",
    "option_c": "Lateral only",
    "option_d": "Prone",
    "correct_answer": "B",
    "explanation": "Expiration reduces lung volume while the air in the pleura remains constant, making the pneumothorax appear larger and easier to see."
  },
  {
    "question": "The 'Steeple Sign' of the subglottic airway is seen in which condition?",
    "option_a": "Epiglottitis",
    "option_b": "Croup (Laryngotracheobronchitis)",
    "option_c": "Foreign body aspiration",
    "option_d": "Retropharyngeal abscess",
    "correct_answer": "B",
    "explanation": "Edema of the subglottic mucosa leads to a tapered narrowing of the airway on a frontal neck X-ray."
  },
  {
    "question": "In the setting of 'Acute Stroke', which imaging find is most concerning for impending 'Hemorrhagic Transformation'?",
    "option_a": "A dense MCA sign",
    "option_b": "Extensive hypodensity involving >1/3 of the MCA territory",
    "option_c": "A normal CT scan",
    "option_d": "Mild sulcal effacement",
    "correct_answer": "B",
    "explanation": "Large areas of infarcted brain have higher vessel fragility and a significantly higher risk of bleeding if reperfused or treated with tPA."
  },
  {
    "question": "What is the primary use of 'Fluoroscopy' in the GI tract?",
    "option_a": "Measuring liver size",
    "option_b": "Evaluating swallowing (Barium Swallow) and bowel transit in real-time",
    "option_c": "Detecting colon cancer screening",
    "option_d": "Identifying gallstones",
    "correct_answer": "B",
    "explanation": "Fluoroscopy allows the radiologist to watch the dynamic movement of contrast through the esophagus, stomach, and intestines."
  },
  {
    "question": "A 'Sunburst' periosteal reaction in a child's distal femur is most suspicious for:",
    "option_a": "Ewing sarcoma",
    "option_b": "Osteosarcoma",
    "option_c": "Osteoid osteoma",
    "option_d": "Greenstick fracture",
    "correct_answer": "B",
    "explanation": "This aggressive reaction occurs when the tumor grows rapidly and lifts the periosteum, forming spicules of bone."
  },
  {
    "question": "Which finding on a mammogram is highly suspicious for 'Malignancy'?",
    "option_a": "A well-circumscribed, round, smooth mass",
    "option_b": "Pleomorphic microcalcifications in a clustered distribution",
    "option_c": "A large mass with a fatty center",
    "option_d": "Uniformly dispersed skin thickening",
    "correct_answer": "B",
    "explanation": "Clustered, irregular, and varying-sized calcifications (pleomorphic) are a hallmark sign of ductal carcinoma in situ or invasive cancer."
  },
  {
    "question": "On a Chest X-ray, the 'Double Density' sign behind the right atrium indicates:",
    "option_a": "Right ventricular hypertrophy",
    "option_b": "Left atrial enlargement",
    "option_c": "Pericardial effusion",
    "option_d": "Aortic aneurysm",
    "correct_answer": "B",
    "explanation": "The enlarging left atrium projects over the right atrium, creating two distinct borders in the right heart region."
  },
  {
    "question": "In Interventional Radiology, what is the purpose of 'Uterine Artery Embolization' (UAE)?",
    "option_a": "To treat uterine cancer",
    "option_b": "To treat symptomatic uterine fibroids non-surgically",
    "option_c": "To prevent pregnancy",
    "option_d": "To treat endometriosis",
    "correct_answer": "B",
    "explanation": "Embolization cuts off the blood supply to the fibroids, causing them to shrink and symptoms to improve."
  },
  {
    "question": "Which of the following is true regarding 'Nuclear Medicine' imaging (e.g., PET Scan)?",
    "option_a": "It provides the best anatomical resolution of all modalities",
    "option_b": "It provides functional information based on the metabolic activity of tissues",
    "option_c": "It uses magnetic fields rather than radiation",
    "option_d": "It is only used for bone fractures",
    "correct_answer": "B",
    "explanation": "Nuclear medicine, specifically PET with FDG, measures glucose uptake to identify areas of high metabolism like tumors or inflammation."
  },
  {
    "question": "A 'Thumbprint sign' on a lateral neck X-ray is characteristic of:",
    "option_a": "Croup",
    "option_b": "Acute Epiglottitis",
    "option_c": "Pharyngeal abscess",
    "option_d": "Vocal cord palsy",
    "correct_answer": "B",
    "explanation": "The swollen, rounded epiglottis resembles a thumb tip protruding into the laryngeal inlet."
  },
  {
    "question": "In CT, a 'Hyperdense MCA Sign' is an early indicator of:",
    "option_a": "MCA aneurysm",
    "option_b": "Acute embolic or thrombotic occlusion of the Middle Cerebral Artery",
    "option_c": "Chronic stroke",
    "option_d": "High intracranial pressure",
    "correct_answer": "B",
    "explanation": "Fresh clot is more dense (whiter) than moving blood and brain tissue on a non-contrast CT."
  },
  {
    "question": "The 'Golden S-sign' of Golden is seen when which lobe of the lung collapses?",
    "option_a": "Right Lower Lobe",
    "option_b": "Right Upper Lobe",
    "option_c": "Left Lower Lobe",
    "option_d": "Left Upper Lobe",
    "correct_answer": "B",
    "explanation": "Collapse of the RUL against a central hilar mass creates an S-shaped fissure border."
  },
  {
    "question": "Which imaging feature is the hallmark of 'Subdural Hematoma' (SDH)?",
    "option_a": "Convex shape that does not cross sutures",
    "option_b": "Crescentic shape that can cross suture lines",
    "option_c": "Hyperdensity within the sulci",
    "option_d": "Midline shift without a visible collection",
    "correct_answer": "B",
    "explanation": "SDHs occur in the potential space between the dura and arachnoid; blood can spread across the entire hemisphere until it reaches dural reflections."
  },
  {
    "question": "What is the primary radiological finding in 'Ankylosing Spondylitis'?",
    "option_a": "Vertebral body compression fractures",
    "option_b": "Sacroiliitis (blurring and fusion of the SI joints)",
    "option_c": "Osteophytes at the hip joints",
    "option_d": "Symmetrical hand joint erosions",
    "correct_answer": "B",
    "explanation": "SI joint involvement is the earliest and most consistent feature of ankylosing spondylitis."
  },
  {
    "question": "In musculoskeletal imaging, a 'Segond Fracture' is a sign of an injury to the:",
    "option_a": "MCL",
    "option_b": "ACL (Anterior Cruciate Ligament)",
    "option_c": "PCL",
    "option_d": "Achilles tendon",
    "correct_answer": "B",
    "explanation": "A Segond fracture is an avulsion fracture of the lateral tibial plateau, highly specific for an ACL tear."
  },
  {
    "question": "Which radiological sign involves 'dilated loops of small bowel in a step-ladder pattern' and 'no gas in the rectum'?",
    "option_a": "Paralytic ileus",
    "option_b": "Mechanical small bowel obstruction",
    "option_c": "Sigmoid volvulus",
    "option_d": "Diverticulitis",
    "correct_answer": "B",
    "explanation": "The step-ladder appearance reflects the fluid-filled loops of small bowel attempting to overcome a physical obstruction."
  },
  {
    "question": "On an ultrasound, 'Posterior Acoustic Shadowing' is classic for:",
    "option_a": "A simple cyst",
    "option_b": "A gallstone or kidney stone",
    "option_c": "An abscess",
    "option_d": "Normal muscle",
    "correct_answer": "B",
    "explanation": "Sound is completely reflected or absorbed by the dense stone, leaving a black void behind it."
  },
  {
    "question": "Which imaging modality is the 'Gold Standard' for diagnosing 'Pulmonary Embolism' in a hemodynamically stable patient?",
    "option_a": "D-dimer blood test",
    "option_b": "CT Pulmonary Angiography (CTPA)",
    "option_c": "Chest X-ray",
    "option_d": "Transthoracic Echo",
    "correct_answer": "B",
    "explanation": "CTPA provides direct visualization of the clot within the pulmonary arteries with high sensitivity and specificity."
  }
]

COURSE_ID = "NVU_MD_Y3_S1_C26"

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
