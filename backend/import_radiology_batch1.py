import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

questions_data = [
  {
    "question": "What is the standard unit of measurement for radio-density in CT scans?",
    "option_a": "Tesla",
    "option_b": "Hounsfield Units (HU)",
    "option_c": "Decibels",
    "option_d": "Sieverts",
    "correct_answer": "B",
    "explanation": "Hounsfield Units (HU) provide a quantitative scale for describing radiodensity, where water is 0 HU and air is -1000 HU."
  },
  {
    "question": "On a standard non-contrast Head CT, how does acute blood appear compared to brain parenchyma?",
    "option_a": "Hypodense (darker)",
    "option_b": "Hyperdense (brighter)",
    "option_c": "Isodense (same color)",
    "option_d": "Anechoic",
    "correct_answer": "B",
    "explanation": "Acute hemorrhage contains high concentrations of hemoglobin/protein, making it appear white (hyperdense) on CT, typically measuring 60-80 HU."
  },
  {
    "question": "Which of the following is the imaging modality of choice for suspected acute cholecystitis?",
    "option_a": "Abdominal X-ray",
    "option_b": "Ultrasound",
    "option_c": "MRI",
    "option_d": "Non-contrast CT",
    "correct_answer": "B",
    "explanation": "Ultrasound is highly sensitive for detecting gallstones, gallbladder wall thickening, and pericholecystic fluid, which are hallmarks of cholecystitis."
  },
  {
    "question": "On a T2-weighted MRI sequence, how does stationary fluid (such as CSF) appear?",
    "option_a": "Dark (hypointense)",
    "option_b": "Bright (hyperintense)",
    "option_c": "Grey (isointense)",
    "option_d": "Black (void signal)",
    "correct_answer": "B",
    "explanation": "T2-weighted images are 'water bright'. CSF and edema appear white, helping identify pathology like inflammation or tumors."
  },
  {
    "question": "Which Chest X-ray view is most sensitive for detecting a small amount of pleural effusion in a bedridden patient?",
    "option_a": "Supine AP",
    "option_b": "Lateral Decubitus",
    "option_c": "PA Upright",
    "option_d": "Apical Lordotic",
    "correct_answer": "B",
    "explanation": "The lateral decubitus view allows fluid to layer along the dependent chest wall, making even small amounts (5-10 mL) visible."
  },
  {
    "question": "What is the characteristic CT appearance of an epidural hematoma?",
    "option_a": "Crescent-shaped and crosses sutures",
    "option_b": "Biconvex (lens-shaped) and limited by sutures",
    "option_c": "Diffuse blurring of the sulci",
    "option_d": "Black (hypodense) area in the parenchyma",
    "correct_answer": "B",
    "explanation": "Epidural hematomas occur between the skull and dura; the dura's tight adherence to sutures creates the convex shape."
  },
  {
    "question": "In pulmonary imaging, what does 'silhouette sign' refer to?",
    "option_a": "A shadow of a tumor on the lung",
    "option_b": "The loss of a normal border between two structures of similar density",
    "option_c": "The appearance of air in the pleural space",
    "option_d": "A calcified lymph node",
    "correct_answer": "B",
    "explanation": "If a lung opacity touches the heart border and the border disappears, the opacity is in the same anatomical plane (e.g., middle lobe pneumonia)."
  },
  {
    "question": "Which of the following is an absolute contraindication for a patient undergoing an MRI?",
    "option_a": "Pregnancy",
    "option_b": "A non-compatible cardiac pacemaker",
    "option_c": "A broken arm with a plaster cast",
    "option_d": "Previous IV contrast reaction",
    "correct_answer": "B",
    "explanation": "The strong magnetic field can move, heat, or reprogram metallic implants like older pacemakers, leading to fatal complications."
  },
  {
    "question": "What is the 'Gold Standard' imaging for the diagnosis of pulmonary embolism in a stable patient?",
    "option_a": "Ventilation-Perfusion (V/Q) scan",
    "option_b": "CT Pulmonary Angiography (CTPA)",
    "option_c": "Chest X-ray",
    "option_d": "Transthoracic Echocardiogram",
    "correct_answer": "B",
    "explanation": "CTPA allows direct visualization of thrombi within the pulmonary arteries and has become the primary diagnostic tool."
  },
  {
    "question": "A Hounsfield Unit (HU) measurement of -100 is most consistent with which tissue type?",
    "option_a": "Water",
    "option_b": "Fat",
    "option_c": "Bone",
    "option_d": "Muscle",
    "correct_answer": "B",
    "explanation": "Fat typically measures between -50 and -150 HU. Muscle is ~40 HU, and bone is >400 HU."
  },
  {
    "question": "Which of the following describes 'pneumatosis intestinalis' on a CT scan?",
    "option_a": "Free air under the diaphragm",
    "option_b": "Gas within the wall of the bowel",
    "option_c": "Dilated loops of small bowel",
    "option_d": "Fluid in the peritoneal cavity",
    "correct_answer": "B",
    "explanation": "Gas in the bowel wall is a worrisome sign often associated with bowel ischemia or necrotizing enterocolitis."
  },
  {
    "question": "In musculoskeletal radiology, what does the term 'Sail Sign' on an elbow X-ray indicate?",
    "option_a": "Normal anatomy",
    "option_b": "An occult fracture causing displacement of the fat pad",
    "option_c": "A dislocation of the shoulder",
    "option_d": "Osteoporosis",
    "correct_answer": "B",
    "explanation": "An elevated anterior fat pad (resembling a sail) indicates a joint effusion, which in the setting of trauma suggests a radial head fracture in adults."
  },
  {
    "question": "Which of the following MRI sequences is most sensitive for detecting early acute ischemic stroke (within minutes)?",
    "option_a": "T1-weighted",
    "option_b": "Diffusion-Weighted Imaging (DWI)",
    "option_c": "FLAIR",
    "option_d": "T2-weighted",
    "correct_answer": "B",
    "explanation": "DWI detects the restriction of water movement (cytotoxic edema) that occurs immediately after ischemia, long before other sequences show changes."
  },
  {
    "question": "On a chest X-ray, what is the 'deep sulcus sign' indicative of?",
    "option_a": "Pleural effusion in a supine patient",
    "option_b": "Pneumothorax in a supine patient",
    "option_c": "Lower lobe pneumonia",
    "option_d": "Diaphragmatic hernia",
    "correct_answer": "B",
    "explanation": "In a supine patient, air in the pleural space collects anteriorly and inferiorly, deepening the costophrenic angle."
  },
  {
    "question": "Which of the following contrast agents is most commonly used in MRI?",
    "option_a": "Iodinated contrast",
    "option_b": "Gadolinium-based contrast",
    "option_c": "Barium sulfate",
    "option_d": "Technetium-99m",
    "correct_answer": "B",
    "explanation": "Gadolinium is a paramagnetic metal that shortens T1 relaxation times, making structures brighter on T1-weighted images."
  },
  {
    "question": "A 'Lead Pipe' appearance on a barium enema is classic for which condition?",
    "option_a": "Crohn's Disease",
    "option_b": "Ulcerative Colitis",
    "option_c": "Colon Cancer",
    "option_d": "Diverticulosis",
    "correct_answer": "B",
    "explanation": "Chronic inflammation in UC leads to the loss of haustral markings, resulting in a smooth, rigid tube-like colon."
  },
  {
    "question": "Which imaging sign consists of air outlining both sides of the bowel wall, indicating pneumoperitoneum?",
    "option_a": "Rigler sign",
    "option_b": "Football sign",
    "option_c": "Double bubble sign",
    "option_d": "Target sign",
    "correct_answer": "A",
    "explanation": "Rigler's sign is seen on an abdominal X-ray when free gas is present in the peritoneal cavity, allowing visualization of the outer serosal wall."
  },
  {
    "question": "The 'Apple Core' lesion seen on a barium study of the colon is highly suggestive of:",
    "option_a": "Intussusception",
    "option_b": "Annular carcinoma (colon cancer)",
    "option_c": "Volvulus",
    "option_d": "Stricture from Crohn's",
    "correct_answer": "B",
    "explanation": "Irregular, circumferential narrowing of the lumen with 'overhanging edges' is a classic sign of malignancy."
  },
  {
    "question": "In ultrasound, a structure that produces no echoes and appears completely black is described as:",
    "option_a": "Hyperechoic",
    "option_b": "Anechoic",
    "option_c": "Isoechoic",
    "option_d": "Hypoechoic",
    "correct_answer": "B",
    "explanation": "Simple cysts or blood vessels are typically anechoic because sound waves pass through them without reflecting back."
  },
  {
    "question": "What is the primary risk associated with the use of gadolinium contrast in patients with severe renal failure?",
    "option_a": "Anaphylaxis",
    "option_b": "Nephrogenic Systemic Fibrosis (NSF)",
    "option_c": "Acute Tubular Necrosis",
    "option_d": "Hypocalcemia",
    "correct_answer": "B",
    "explanation": "NSF is a rare, debilitating condition involving skin and organ fibrosis; it is strongly linked to gadolinium use in patients with eGFR < 30."
  },
  {
    "question": "On a Chest X-ray, 'Kerley B lines' are short horizontal lines at the lung bases. They indicate:",
    "option_a": "Airway obstruction",
    "option_b": "Interstitial pulmonary edema",
    "option_c": "Old healed tuberculosis",
    "option_d": "Asbestos exposure",
    "correct_answer": "B",
    "explanation": "Kerley B lines represent thickened interlobular septa, most commonly due to pulmonary venous congestion in CHF."
  },
  {
    "question": "Which anatomical structure is most easily evaluated by a Doppler ultrasound?",
    "option_a": "Lung parenchyma",
    "option_b": "Moving blood within vessels",
    "option_c": "Cortical bone",
    "option_d": "The skull",
    "correct_answer": "B",
    "explanation": "The Doppler effect measures the change in frequency of sound reflecting off moving red blood cells to determine flow direction and velocity."
  },
  {
    "question": "In Neuroimaging, a 'crescent-shaped' hyperdensity that crosses suture lines is most likely a:",
    "option_a": "Epidural hematoma",
    "option_b": "Subdural hematoma",
    "option_c": "Subarachnoid hemorrhage",
    "option_d": "Intracerebral hemorrhage",
    "correct_answer": "B",
    "explanation": "Subdural hematomas occur between the dura and arachnoid; the blood can spread widely along the hemisphere as it is not restricted by sutures."
  },
  {
    "question": "Which of the following is the best initial screening test for a patient with a suspected AAA (Abdominal Aortic Aneurysm)?",
    "option_a": "Abdominal X-ray",
    "option_b": "Ultrasound",
    "option_c": "CT Angiography",
    "option_d": "Aortography",
    "correct_answer": "B",
    "explanation": "Ultrasound is inexpensive, portable, and has nearly 100% sensitivity for detecting and measuring an AAA."
  },
  {
    "question": "What does the 'Double Bubble' sign on a neonatal abdominal X-ray indicate?",
    "option_a": "Pyloric stenosis",
    "option_b": "Duodenal atresia",
    "option_c": "Necrotizing enterocolitis",
    "option_d": "Malrotation",
    "correct_answer": "B",
    "explanation": "The 'bubbles' are the gas-filled stomach and proximal duodenum, separated by the pylorus, with no gas distal to the obstruction."
  },
  {
    "question": "Which of the following imaging features is most characteristic of a benign lung nodule?",
    "option_a": "Spiculated margins",
    "option_b": "Popcorn-like calcification",
    "option_c": "Rapid growth over 1 month",
    "option_d": "Size > 3 cm",
    "correct_answer": "B",
    "explanation": "Popcorn calcification is pathognomonic for a hamartoma, a common benign lung tumor."
  },
  {
    "question": "What is the primary advantage of CT over MRI for emergency trauma imaging?",
    "option_a": "Better soft tissue contrast",
    "option_b": "Speed and availability",
    "option_c": "No ionizing radiation",
    "option_d": "Better imaging of the spinal cord",
    "correct_answer": "B",
    "explanation": "CT is much faster and more accessible in trauma bays, allowing rapid screening of the head, chest, and abdomen."
  },
  {
    "question": "In a patient with a suspected 'scaphoid fracture' and normal X-rays, what is the most appropriate next imaging step?",
    "option_a": "Repeat X-ray in 6 months",
    "option_b": "MRI of the wrist",
    "option_c": "Ultrasound",
    "option_d": "Fluoroscopy",
    "correct_answer": "B",
    "explanation": "MRI is the most sensitive test for identifying occult scaphoid fractures that are not visible on initial plain films."
  },
  {
    "question": "The 'Peeled-Orange' or 'Peau d'orange' sign on a mammogram is suggestive of:",
    "option_a": "Benign cyst",
    "option_b": "Inflammatory breast cancer",
    "option_c": "Fibroadenoma",
    "option_d": "Fat necrosis",
    "correct_answer": "B",
    "explanation": "Skin thickening and edema caused by lymphatic obstruction by tumor cells give the skin an orange-peel texture."
  },
  {
    "question": "On a Chest X-ray, which chamber of the heart forms the right heart border?",
    "option_a": "Right Ventricle",
    "option_b": "Right Atrium",
    "option_c": "Left Ventricle",
    "option_d": "Left Atrium",
    "correct_answer": "B",
    "explanation": "The right atrium forms the majority of the right heart border on a standard frontal projection."
  },
  {
    "question": "What is the 'Golden Rule' of radiological imaging for trauma?",
    "option_a": "Always use contrast",
    "option_b": "Get at least two views, perpendicular to each other",
    "option_c": "Never image children",
    "option_d": "MRI is always better than X-ray",
    "correct_answer": "B",
    "explanation": "A single view can miss a fracture or dislocation; orthogonal views are essential for accurate diagnosis."
  },
  {
    "question": "Which of the following appear 'Bright' on a T1-weighted MRI?",
    "option_a": "Water",
    "option_b": "Fat",
    "option_c": "Air",
    "option_d": "Cortical bone",
    "correct_answer": "B",
    "explanation": "Fat has a short T1 relaxation time, making it appear bright (hyperintense) on T1-weighted images."
  },
  {
    "question": "Which finding is most diagnostic of a 'Pneumoperitoneum' on an upright Chest X-ray?",
    "option_a": "Air in the stomach",
    "option_b": "Crescentic air beneath the diaphragm",
    "option_c": "Pleural effusion",
    "option_d": "Dilated esophagus",
    "correct_answer": "B",
    "explanation": "Free air rises to the highest point in the abdomen, appearing as a thin lucency under the diaphragmatic domes."
  },
  {
    "question": "What is the typical Hounsfield Unit (HU) for air?",
    "option_a": "0",
    "option_b": "-1000",
    "option_c": "+1000",
    "option_d": "-100",
    "correct_answer": "B",
    "explanation": "Air is the least dense substance on the scale, assigned a value of -1000 HU."
  },
  {
    "question": "A patient with acute flank pain and hematuria is suspected of having a kidney stone. Which imaging is most appropriate?",
    "option_a": "IV Pyelogram",
    "option_b": "Non-contrast CT of the Abdomen/Pelvis",
    "option_c": "MRI",
    "option_d": "Nuclear Renal Scan",
    "correct_answer": "B",
    "explanation": "Non-contrast CT (the 'stone protocol') is the standard for detecting ureteral calculi due to its high speed and sensitivity."
  },
  {
    "question": "Which of the following is a classic radiological sign of 'Scurvy' in children?",
    "option_a": "Codfish vertebrae",
    "option_b": "Wimberger sign (ring-like epiphyses)",
    "option_c": "Bowing of the legs",
    "option_d": "Osteophyte formation",
    "correct_answer": "B",
    "explanation": "Wimberger sign, along with the 'white line of Frankel', are classic indicators of infantile vitamin C deficiency."
  },
  {
    "question": "What is 'Fluoroscopy' primarily used for?",
    "option_a": "Static bone imaging",
    "option_b": "Real-time imaging of motion (e.g., swallowing, cardiac motion)",
    "option_c": "Measuring bone density",
    "option_d": "High-resolution brain mapping",
    "correct_answer": "B",
    "explanation": "Fluoroscopy uses continuous X-rays to provide a live movie-like image of internal structures."
  },
  {
    "question": "In interventional radiology, what is a 'TIPS' procedure used for?",
    "option_a": "Treating lung cancer",
    "option_b": "Reducing portal hypertension",
    "option_c": "Fixing a broken hip",
    "option_d": "Removing a kidney stone",
    "correct_answer": "B",
    "explanation": "TIPS (Transjugular Intrahepatic Portosystemic Shunt) creates a pathway between the portal and hepatic veins to lower portal pressure."
  },
  {
    "question": "On a Chest X-ray, 'Eggshell calcification' of hilar lymph nodes is most classic for:",
    "option_a": "Sarcoidosis",
    "option_b": "Silicosis",
    "option_c": "Tuberculosis",
    "option_d": "Lymphoma",
    "correct_answer": "B",
    "explanation": "While it can rarely be seen in sarcoidosis, eggshell calcification is a hallmark of occupational silica exposure."
  },
  {
    "question": "Which of the following is true for an 'Air Bronchogram'?",
    "option_a": "It indicates a pneumothorax",
    "option_b": "It is the visualization of air-filled bronchi against a consolidated lung",
    "option_c": "It is a sign of lung collapse",
    "option_d": "It only occurs in patients with asthma",
    "correct_answer": "B",
    "explanation": "When the surrounding alveoli are filled with fluid (pneumonia/edema), the air in the tubes remains dark, making them visible."
  },
  {
    "question": "Which of the following is a 'Hard Sign' of arterial injury requiring immediate angiography or surgery?",
    "option_a": "Small stable hematoma",
    "option_b": "Pulsatile hemorrhage or bruit",
    "option_c": "Proximity of injury to a major vessel",
    "option_d": "Moderate pain",
    "correct_answer": "B",
    "explanation": "Hard signs like pulsatile bleeding or thrills indicate a definitive vascular emergency."
  },
  {
    "question": "In Pediatric Radiology, a 'Crescent Sign' on an abdominal X-ray is indicative of:",
    "option_a": "Pyloric stenosis",
    "option_b": "Intussusception",
    "option_c": "Hirschsprung disease",
    "option_d": "Duodenal atresia",
    "correct_answer": "B",
    "explanation": "The sign is formed by the leading edge of the intussusceptum protruding into an air-filled pocket in the colon."
  },
  {
    "question": "Which of the following is a common symptom of 'Contrast-Induced Nephropathy' (CIN)?",
    "option_a": "Sudden deafness",
    "option_b": "Transient rise in serum creatinine within 48-72 hours",
    "option_c": "Permanent liver failure",
    "option_d": "Hives and itching only",
    "correct_answer": "B",
    "explanation": "CIN is an acute decline in renal function following iodinated contrast administration, usually peaking at 3-5 days."
  },
  {
    "question": "The 'Sunburst' periosteal reaction seen on bone X-ray is highly suspicious for:",
    "option_a": "Osteomyelitis",
    "option_b": "Osteosarcoma",
    "option_c": "Stress fracture",
    "option_d": "Osteoarthritis",
    "correct_answer": "B",
    "explanation": "Aggressive bone tumors cause rapid periosteal elevation and perpendicular bone growth, appearing like rays of a sun."
  },
  {
    "question": "On a Chest X-ray, 'Snowstorm appearance' is characteristic of:",
    "option_a": "Pulmonary embolism",
    "option_b": "Miliary tuberculosis",
    "option_c": "Lobar pneumonia",
    "option_d": "Pleural thickening",
    "correct_answer": "B",
    "explanation": "The term describes the diffuse, tiny (1-3mm) nodules scattered throughout both lungs in miliary TB."
  },
  {
    "question": "Which view is part of the standard 'Shoulder Series' to look for posterior dislocation?",
    "option_a": "AP only",
    "option_b": "Axillary or Scapular Y view",
    "option_c": "Internal rotation only",
    "option_d": "Lateral decubitus",
    "correct_answer": "B",
    "explanation": "AP views can miss posterior dislocations; axillary or Y views provide the necessary lateral perspective."
  },
  {
    "question": "In Brain CT, the 'hyperdense middle cerebral artery' sign indicates:",
    "option_a": "Chronic aneurysm",
    "option_b": "Acute thrombus/embolus in the MCA",
    "option_c": "Normal variant in elderly",
    "option_d": "High blood pressure",
    "correct_answer": "B",
    "explanation": "A fresh clot within the vessel appears white (hyperdense), often being the earliest sign of an ischemic stroke."
  },
  {
    "question": "What is the primary use of a 'DEXA' scan?",
    "option_a": "Detecting bone cancer",
    "option_b": "Measuring Bone Mineral Density (BMD)",
    "option_c": "Evaluating joint cartilage",
    "option_d": "Identifying ligament tears",
    "correct_answer": "B",
    "explanation": "Dual-Energy X-ray Absorptiometry is the gold standard for diagnosing osteoporosis."
  },
  {
    "question": "Which of the following describes 'Acoustic Shadowing' in ultrasound?",
    "option_a": "Increased brightness behind a cyst",
    "option_b": "A dark band behind a dense structure like a gallstone",
    "option_c": "Blurring of the image",
    "option_d": "Ringing sound during the exam",
    "correct_answer": "B",
    "explanation": "Dense structures reflect all sound waves, leaving a 'shadow' where no sound can penetrate."
  },
  {
    "question": "A 'Bumper' or 'Segond' fracture of the lateral tibial plateau is highly associated with injury to which ligament?",
    "option_a": "MCL",
    "option_b": "ACL",
    "option_c": "PCL",
    "option_d": "Patellar tendon",
    "correct_answer": "B",
    "explanation": "The Segond fracture is an avulsion of the lateral tibial condyle, which is a key sign of an ACL tear."
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
