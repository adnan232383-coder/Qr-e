import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

questions_data = [
  {
    "question": "A 55-year-old male with a history of chronic productive cough has a chest CT showing the 'signet ring sign'. What does this finding indicate?",
    "option_a": "Lobar pneumonia",
    "option_b": "Bronchiectasis",
    "option_c": "Pulmonary embolism",
    "option_d": "Congestive heart failure",
    "correct_answer": "B",
    "explanation": "The signet ring sign occurs in bronchiectasis when the diameter of the bronchus is larger than its accompanying pulmonary artery."
  },
  {
    "question": "On a T2-weighted MRI, a large mass in the cerebral hemisphere crosses the corpus callosum, creating a 'butterfly' appearance. What is the most likely diagnosis?",
    "option_a": "Meningioma",
    "option_b": "Glioblastoma Multiforme (GBM)",
    "option_c": "Multiple Sclerosis",
    "option_d": "Brain abscess",
    "correct_answer": "B",
    "explanation": "GBM is a high-grade glioma known for its aggressive growth across the white matter tracts of the corpus callosum."
  },
  {
    "question": "What is the most sensitive imaging modality for the early detection of osteomyelitis, often showing changes within 3 to 5 days of infection?",
    "option_a": "Plain X-ray",
    "option_b": "MRI",
    "option_c": "Ultrasound",
    "option_d": "CT scan",
    "correct_answer": "B",
    "explanation": "MRI is highly sensitive to bone marrow edema, which is the earliest sign of osteomyelitis, long before cortical destruction is visible on X-ray."
  },
  {
    "question": "In a patient with suspected mesenteric ischemia, the presence of 'portal venous gas' on CT is considered:",
    "option_a": "A benign finding in elderly patients",
    "option_b": "A late and ominous sign suggesting bowel infarction",
    "option_c": "An indicator of early-stage gastritis",
    "option_d": "A result of recent colonoscopy",
    "correct_answer": "B",
    "explanation": "Portal venous gas usually results from air escaping the lumen of necrotic bowel, indicating a surgical emergency."
  },
  {
    "question": "A 40-year-old female presents with bilateral hilar lymphadenopathy on a chest X-ray but is asymptomatic. Which condition is most classically associated with this finding?",
    "option_a": "Primary Tuberculosis",
    "option_b": "Sarcoidosis",
    "option_c": "Small cell lung cancer",
    "option_d": "Silicosis",
    "correct_answer": "B",
    "explanation": "Symmetric, bilateral hilar adenopathy is the hallmark of Stage I Sarcoidosis."
  },
  {
    "question": "On an abdominal CT, a solid liver mass demonstrates a 'spoke-wheel' enhancement pattern with a central scar. What is the most likely diagnosis?",
    "option_a": "Hepatocellular carcinoma",
    "option_b": "Focal Nodular Hyperplasia (FNH)",
    "option_c": "Cavernous Hemangioma",
    "option_d": "Liver abscess",
    "correct_answer": "B",
    "explanation": "FNH typically features a central fibrous scar and radiating arteries, creating the spoke-wheel appearance on arterial phase imaging."
  },
  {
    "question": "Which type of brain herniation involves the displacement of the cerebellar tonsils through the foramen magnum?",
    "option_a": "Uncal herniation",
    "option_b": "Tonsillar herniation",
    "option_c": "Subfalcine herniation",
    "option_d": "Transtentorial herniation",
    "correct_answer": "B",
    "explanation": "Tonsillar herniation is life-threatening as it compresses the medulla oblongata, which controls respiratory and cardiac centers."
  },
  {
    "question": "A 'Cobra Head' sign on an Intravenous Pyelogram (IVP) is characteristic of which condition?",
    "option_a": "Renal stone",
    "option_b": "Ureterocele",
    "option_c": "Bladder cancer",
    "option_d": "Polycystic kidney disease",
    "correct_answer": "B",
    "explanation": "A ureterocele is a cystic dilation of the distal ureter; when filled with contrast, it resembles a cobra's head within the bladder."
  },
  {
    "question": "On a non-contrast Head CT, how does a 'chronic' subdural hematoma (over 3 weeks old) typically appear?",
    "option_a": "Hyperdense (white)",
    "option_b": "Hypodense (dark/black)",
    "option_c": "Isodense (grey)",
    "option_d": "Bright red",
    "correct_answer": "B",
    "explanation": "As the blood breaks down over weeks, its density decreases on CT, eventually appearing darker than the brain tissue."
  },
  {
    "question": "Which imaging feature helps differentiate a 'Lung Abscess' from an 'Empyema' on a CT scan?",
    "option_a": "The abscess is lenticular (lens-shaped)",
    "option_b": "The empyema has the 'split pleura sign'",
    "option_c": "The empyema is always spherical",
    "option_d": "Abscesses never have air-fluid levels",
    "correct_answer": "B",
    "explanation": "The split pleura sign (thickened visceral and parietal pleura separated by fluid) is highly suggestive of an empyema."
  },
  {
    "question": "The 'Terry-Thomas' sign on a wrist X-ray refers to a widened gap between which two bones, indicating ligamentous injury?",
    "option_a": "Radius and Ulna",
    "option_b": "Scaphoid and Lunate",
    "option_c": "Lunate and Triquetrum",
    "option_d": "Capitate and Hamate",
    "correct_answer": "B",
    "explanation": "A gap >3 mm between the scaphoid and lunate indicates a scapholunate ligament dissociation."
  },
  {
    "question": "On a T2-weighted MRI of the spine, 'CSF' appears:",
    "option_a": "Dark (hypointense)",
    "option_b": "Bright (hyperintense)",
    "option_c": "Grey",
    "option_d": "Void of signal",
    "correct_answer": "B",
    "explanation": "T2 sequences are 'water-bright', making fluid-filled spaces like the thecal sac appear white."
  },
  {
    "question": "A 'Sunburst' periosteal reaction in the distal femur of a teenager is most characteristic of:",
    "option_a": "Ewing sarcoma",
    "option_b": "Osteosarcoma",
    "option_c": "Osteoid osteoma",
    "option_d": "Stress fracture",
    "correct_answer": "B",
    "explanation": "Aggressive malignant bone growth in osteosarcoma lifts the periosteum and creates spicules of bone perpendicular to the cortex."
  },
  {
    "question": "In Interventional Radiology, what is the primary purpose of a 'TIPS' procedure?",
    "option_a": "To treat lung cancer",
    "option_b": "To reduce portal hypertension and its complications (e.g., variceal bleeding)",
    "option_c": "To stabilize a vertebral fracture",
    "option_d": "To drain a kidney infection",
    "correct_answer": "B",
    "explanation": "TIPS (Transjugular Intrahepatic Portosystemic Shunt) creates a bypass between the portal and hepatic veins."
  },
  {
    "question": "What does a 'negative' Hounsfield Unit (HU) measurement always indicate on a CT scan?",
    "option_a": "Bone",
    "option_b": "The substance is less dense than water (e.g., fat or air)",
    "option_c": "Acute hemorrhage",
    "option_d": "Intravenous contrast",
    "correct_answer": "B",
    "explanation": "Water is 0 HU; substances like fat (~ -100 HU) and air (~ -1000 HU) have negative values."
  },
  {
    "question": "On a Chest X-ray, the 'Double Density Sign' seen through the right atrium is an indicator of:",
    "option_a": "Right ventricular hypertrophy",
    "option_b": "Left atrial enlargement",
    "option_c": "Pericardial effusion",
    "option_d": "Aortic dissection",
    "correct_answer": "B",
    "explanation": "The enlarged left atrium creates an extra shadow that overlaps the right atrium border."
  },
  {
    "question": "Which of the following is true for 'Magnetic Resonance Cholangiopancreatography' (MRCP)?",
    "option_a": "It is a therapeutic procedure like ERCP",
    "option_b": "It is a non-invasive diagnostic tool that uses heavily T2-weighted images",
    "option_c": "It uses iodinated contrast",
    "option_d": "It is the gold standard for removing gallstones",
    "correct_answer": "B",
    "explanation": "MRCP is diagnostic only; it makes stationary fluid (bile/pancreatic juice) very bright without needing contrast."
  },
  {
    "question": "The 'Target Sign' on a pediatric abdominal ultrasound is pathognomonic for:",
    "option_a": "Appendicitis",
    "option_b": "Intussusception",
    "option_c": "Pyloric stenosis",
    "option_d": "Meckel's diverticulum",
    "correct_answer": "B",
    "explanation": "The sign represents the telescoping of one bowel segment into another, seen in cross-section."
  },
  {
    "question": "Which finding on a mammogram is most concerning for 'Invasive Ductal Carcinoma'?",
    "option_a": "A smooth, round, well-circumscribed mass",
    "option_b": "A high-density stellate or spiculated mass",
    "option_c": "A large mass with a fatty center",
    "option_d": "Uniformly dispersed skin thickening",
    "correct_answer": "B",
    "explanation": "Spiculated margins indicate infiltration into the surrounding tissue, a classic sign of malignancy."
  },
  {
    "question": "On a Head CT, 'Subarachnoid Hemorrhage' is best visualized as hyperdensity in the:",
    "option_a": "Brain parenchyma (white matter)",
    "option_b": "Basal cisterns and cortical sulci",
    "option_c": "Potential space between the skull and dura",
    "option_d": "Orbit",
    "correct_answer": "B",
    "explanation": "Blood in the subarachnoid space mixes with CSF in the cisterns and grooves of the brain surface."
  },
  {
    "question": "What does 'Acoustic Shadowing' on an ultrasound signify?",
    "option_a": "The presence of a fluid-filled cyst",
    "option_b": "A dense structure (like a stone) that reflects or absorbs all sound waves",
    "option_c": "High-velocity blood flow",
    "option_d": "Normal muscle tissue",
    "correct_answer": "B",
    "explanation": "Dense objects like gallstones block sound, leaving a dark 'shadow' behind them on the image."
  },
  {
    "question": "In chest imaging, 'Kerley B lines' are typically associated with:",
    "option_a": "Pneumothorax",
    "option_b": "Congestive Heart Failure (Pulmonary edema)",
    "option_c": "Lung cancer",
    "option_d": "Asbestosis",
    "correct_answer": "B",
    "explanation": "These are short horizontal lines at the lung bases representing thickened interlobular septa due to fluid."
  },
  {
    "question": "Which radiological sign involves 'air outlining both the inner and outer walls of the bowel'?",
    "option_a": "Target sign",
    "option_b": "Rigler's sign",
    "option_c": "Double bubble sign",
    "option_d": "Sail sign",
    "correct_answer": "B",
    "explanation": "Rigler's sign is seen in pneumoperitoneum, where free air in the cavity allows the outer bowel wall to be seen."
  },
  {
    "question": "A 'Hampton's Hump' on a chest X-ray is a peripheral wedge-shaped opacity suggestive of:",
    "option_a": "Lobar pneumonia",
    "option_b": "Pulmonary infarction (often from PE)",
    "option_c": "Pleural effusion",
    "option_d": "Pneumothorax",
    "correct_answer": "B",
    "explanation": "It represents lung tissue that has died due to the loss of blood supply from a pulmonary embolism."
  },
  {
    "question": "On a non-contrast Head CT, 'Acute Ischemic Stroke' often appears normal for the first few hours. What is one of the earliest subtle signs?",
    "option_a": "Bright white blood in the sulci",
    "option_b": "Loss of grey-white matter differentiation (insular ribbon sign)",
    "option_c": "A large dark hole in the brain",
    "option_d": "A shifted midline",
    "correct_answer": "B",
    "explanation": "Cytotoxic edema causes the grey matter to lose its density, making it look like white matter on early CT."
  },
  {
    "question": "The 'Apple Core' lesion on a barium enema is the classic description for:",
    "option_a": "Ulcerative Colitis",
    "option_b": "Annular colorectal carcinoma",
    "option_c": "Intussusception",
    "option_d": "Sigmoid volvulus",
    "correct_answer": "B",
    "explanation": "The circumferential narrowing of the colon by a tumor resembles a half-eaten apple core."
  },
  {
    "question": "Which of the following describes the 'Steeple Sign' on a frontal neck X-ray?",
    "option_a": "Epiglottic swelling",
    "option_b": "Subglottic narrowing in Croup",
    "option_c": "Tracheal deviation",
    "option_d": "Foreign body in the esophagus",
    "correct_answer": "B",
    "explanation": "Laryngotracheobronchitis (Croup) causes mucosal edema that tapers the airway below the vocal cords."
  },
  {
    "question": "What is the primary risk of using 'Gadolinium' contrast in a patient with an eGFR < 30?",
    "option_a": "Thyroid storm",
    "option_b": "Nephrogenic Systemic Fibrosis (NSF)",
    "option_c": "Anaphylactic shock",
    "option_d": "Hepatotoxicity",
    "correct_answer": "B",
    "explanation": "NSF is a rare, severe condition involving skin and organ fibrosis linked to gadolinium in renal failure."
  },
  {
    "question": "A 'Hot Spot' on a Technetium-99m bone scan represents areas of:",
    "option_a": "Decreased blood flow",
    "option_b": "Increased osteoblastic activity",
    "option_c": "Fat deposition",
    "option_d": "Simple cysts",
    "correct_answer": "B",
    "explanation": "The tracer accumulates where bone is actively being formed or remodeled (e.g., fractures or metastases)."
  },
  {
    "question": "The 'Bamboo Spine' appearance on X-ray is the classic hallmark of:",
    "option_a": "Osteoporosis",
    "option_b": "Ankylosing Spondylitis",
    "option_c": "Rheumatoid Arthritis",
    "option_d": "Spondylolisthesis",
    "correct_answer": "B",
    "explanation": "Fusion of the vertebrae by syndesmophytes gives the spine a rigid, bamboo-like appearance."
  },
  {
    "question": "In Neuroimaging, a 'Crescent-shaped' hyperdensity that crosses suture lines is most likely a:",
    "option_a": "Epidural hematoma",
    "option_b": "Subdural hematoma",
    "option_c": "Intracerebral hemorrhage",
    "option_d": "Subarachnoid hemorrhage",
    "correct_answer": "B",
    "explanation": "Subdural hematomas are not restricted by sutures and can spread along the entire hemisphere."
  },
  {
    "question": "A 'Biconvex' (lens-shaped) hyperdensity on CT that does NOT cross suture lines is a:",
    "option_a": "Subdural hematoma",
    "option_b": "Epidural hematoma",
    "option_c": "Brain tumor",
    "option_d": "Normal variant",
    "correct_answer": "B",
    "explanation": "Epidural hematomas are arterial bleeds restricted by the dural attachments at the skull sutures."
  },
  {
    "question": "On a T1-weighted MRI, 'Fat' appears ______ and 'Water/CSF' appears ______.",
    "option_a": "Bright; Dark",
    "option_b": "Dark; Bright",
    "option_c": "Bright; Bright",
    "option_d": "Dark; Dark",
    "correct_answer": "A",
    "explanation": "T1 is 'fat-bright'. T2 is 'water-bright'."
  },
  {
    "question": "The 'Double Bubble' sign on a neonatal X-ray indicates:",
    "option_a": "Pyloric stenosis",
    "option_b": "Duodenal atresia",
    "option_c": "Malrotation",
    "option_d": "Necrotizing enterocolitis",
    "correct_answer": "B",
    "explanation": "The bubbles represent the gas-filled stomach and the dilated proximal duodenum."
  },
  {
    "question": "In Interventional Radiology, an 'IVC Filter' is used to:",
    "option_a": "Drain an abscess",
    "option_b": "Prevent Pulmonary Embolism in patients who cannot take anticoagulants",
    "option_c": "Treat a kidney stone",
    "option_d": "Open a blocked artery",
    "correct_answer": "B",
    "explanation": "The filter is placed in the inferior vena cava to catch clots migrating from the legs."
  },
  {
    "question": "Which view is the 'Gold Standard' for diagnosing a small 'Pneumothorax'?",
    "option_a": "Supine AP X-ray",
    "option_b": "Upright PA Expiratory X-ray",
    "option_c": "Abdominal Ultrasound",
    "option_d": "Lateral decubitus with the affected side up",
    "correct_answer": "B",
    "explanation": "Expiration makes the lung smaller, making the air in the pleura more obvious."
  },
  {
    "question": "A 'Thumbprint Sign' on a lateral neck X-ray is classic for:",
    "option_a": "Croup",
    "option_b": "Epiglottitis",
    "option_c": "Foreign body aspiration",
    "option_d": "Tonsillitis",
    "correct_answer": "B",
    "explanation": "The swollen epiglottis looks like a thumb protruding into the airway, which is a life-threatening emergency."
  },
  {
    "question": "What is the typical radiological sign of 'Scurvy' in the long bones of a child?",
    "option_a": "Bamboo spine",
    "option_b": "Wimberger sign (ring-like epiphyses)",
    "option_c": "Codman's triangle",
    "option_d": "Osteophytes",
    "correct_answer": "B",
    "explanation": "Wimberger sign and the Pelkan spur are classic skeletal indicators of Vitamin C deficiency."
  },
  {
    "question": "The 'Golden S Sign' of Golden on a Chest X-ray indicates collapse of which lobe?",
    "option_a": "Left lower lobe",
    "option_b": "Right upper lobe (due to a central mass)",
    "option_c": "Middle lobe",
    "option_d": "Left upper lobe",
    "correct_answer": "B",
    "explanation": "The mass and the shifted fissure create an 'S' shape, often signaling lung cancer."
  },
  {
    "question": "In a patient with 'Ankylosing Spondylitis', what is the earliest joint change seen on X-ray?",
    "option_a": "Bowing of the femur",
    "option_b": "Sacroiliitis (blurring/erosion of the SI joints)",
    "option_c": "Shoulder dislocation",
    "option_d": "Wrist joint narrowing",
    "correct_answer": "B",
    "explanation": "Inflammation of the SI joints is the earliest radiographic feature of this disease."
  },
  {
    "question": "Which imaging modality uses 'Tesla' as a unit of strength?",
    "option_a": "CT",
    "option_b": "MRI",
    "option_c": "Ultrasound",
    "option_d": "Nuclear Medicine",
    "correct_answer": "B",
    "explanation": "Tesla (T) measures the strength of the magnetic field in an MRI scanner."
  },
  {
    "question": "A 'Sail Sign' on a pediatric chest X-ray typically represents:",
    "option_a": "A pneumothorax",
    "option_b": "The normal thymus gland in an infant",
    "option_c": "Lobar pneumonia",
    "option_d": "Pleural effusion",
    "correct_answer": "B",
    "explanation": "The thymus is large in children and can overlap the heart, often resembling a boat sail."
  },
  {
    "question": "Which finding is most diagnostic of 'Pneumoperitoneum' on an upright chest X-ray?",
    "option_a": "Dilated stomach",
    "option_b": "Free air beneath the diaphragmatic domes",
    "option_c": "Air in the esophagus",
    "option_d": "Fluid in the lungs",
    "correct_answer": "B",
    "explanation": "Free air rises to the highest point under the diaphragm, appearing as a lucent crescent."
  },
  {
    "question": "On a T2-weighted MRI, stationary fluid (like CSF or urine) appears:",
    "option_a": "Dark",
    "option_b": "Bright (White)",
    "option_c": "Invisible",
    "option_d": "Same as bone",
    "correct_answer": "B",
    "explanation": "T2 is 'water-bright'. This helps in identifying edema, inflammation, and CSF spaces."
  },
  {
    "question": "The 'Whirlpool Sign' on an abdominal CT indicates:",
    "option_a": "Acute cholecystitis",
    "option_b": "Volvulus (twisting of the mesentery)",
    "option_c": "Colon cancer",
    "option_d": "Diverticulitis",
    "correct_answer": "B",
    "explanation": "The swirling appearance of mesenteric vessels is diagnostic for intestinal volvulus."
  },
  {
    "question": "In Interventional Radiology, 'Uterine Artery Embolization' is a treatment for:",
    "option_a": "Uterine cancer",
    "option_b": "Symptomatic uterine fibroids",
    "option_c": "Pregnancy prevention",
    "option_d": "Endometriosis",
    "correct_answer": "B",
    "explanation": "The procedure cuts off blood supply to the fibroids, causing them to shrink."
  },
  {
    "question": "A 'Lead Pipe' colon on a barium study is classic for:",
    "option_a": "Crohn's Disease",
    "option_b": "Chronic Ulcerative Colitis",
    "option_c": "Appendicitis",
    "option_d": "Diverticulosis",
    "correct_answer": "B",
    "explanation": "Loss of haustral markings due to chronic inflammation leads to a smooth, pipe-like appearance."
  },
  {
    "question": "Which of the following is true for a 'DEXA' scan?",
    "option_a": "It is used to image brain tumors",
    "option_b": "It is the gold standard for measuring bone mineral density (BMD)",
    "option_c": "It uses high doses of ultrasound",
    "option_d": "It requires general anesthesia",
    "correct_answer": "B",
    "explanation": "DEXA is used to diagnose osteoporosis and assess fracture risk."
  },
  {
    "question": "In ultrasound, a structure that appears 'whiter' than the surrounding tissue is described as:",
    "option_a": "Hypoechoic",
    "option_b": "Hyperechoic",
    "option_c": "Anechoic",
    "option_d": "Isoechoic",
    "correct_answer": "B",
    "explanation": "Hyperechoic structures reflect more sound waves (e.g., bone, stones, or fat)."
  },
  {
    "question": "The 'Boot-shaped' heart on a chest X-ray is classic for which congenital condition?",
    "option_a": "Atrial Septal Defect",
    "option_b": "Tetralogy of Fallot",
    "option_c": "Transposition of the Great Arteries",
    "option_d": "Coarctation of the aorta",
    "correct_answer": "B",
    "explanation": "Right ventricular hypertrophy lifts the cardiac apex, giving the heart a boot-like (coeur en sabot) shape."
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
