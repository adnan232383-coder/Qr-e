import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

questions_data = [
  {
    "question": "A 42-year-old female presents with episodic hypertension, palpitations, and diaphoresis. Biochemical testing confirms elevated plasma metanephrines. Imaging shows a 4 cm right adrenal mass. What is the most important pharmacological intervention before surgical resection?",
    "option_a": "High-dose Beta-blockers",
    "option_b": "Alpha-adrenergic blockade (e.g., Phenoxybenzamine)",
    "option_c": "Intravenous Calcium channel blockers",
    "option_d": "Glucocorticoid replacement",
    "correct_answer": "B",
    "explanation": "Alpha-blockade must be established first to prevent hypertensive crisis. Beta-blockers are only added after adequate alpha-blockade to control tachycardia, as unopposed alpha-stimulation can be fatal."
  },
  {
    "question": "Which of the following is true regarding 'Type II Endoleaks' following Endovascular Aneurysm Repair (EVAR)?",
    "option_a": "They are caused by a poor seal at the proximal or distal attachment sites",
    "option_b": "They result from retrograde flow through collateral vessels like the lumbar or inferior mesenteric arteries",
    "option_c": "They represent a structural failure or tear in the graft fabric",
    "option_d": "They always require immediate surgical conversion to open repair",
    "correct_answer": "B",
    "explanation": "Type II endoleaks are the most common type and involve persistent flow into the aneurysm sac from branch vessels; most are observed unless the sac continues to expand."
  },
  {
    "question": "A patient with suspected primary hyperaldosteronism (Conn's Syndrome) has a CT showing bilateral adrenal thickening rather than a solitary nodule. What is the most reliable test to differentiate between a unilateral adenoma and bilateral hyperplasia?",
    "option_a": "Adrenal venous sampling (AVS)",
    "option_b": "Repeat CT with fine-cut sections",
    "option_c": "MRI with gadolinium",
    "option_d": "Dexamethasone suppression test",
    "correct_answer": "A",
    "explanation": "AVS is the gold standard for lateralizing the source of aldosterone production when imaging is equivocal or shows bilateral disease."
  },
  {
    "question": "A 70-year-old male presents with a pulsatile mass in the popliteal fossa. What is the most likely associated vascular abnormality in this patient?",
    "option_a": "Carotid artery stenosis",
    "option_b": "Abdominal aortic aneurysm (AAA)",
    "option_c": "Renal artery stenosis",
    "option_d": "Subclavian steal syndrome",
    "correct_answer": "B",
    "explanation": "Approximately 50% of patients with a popliteal artery aneurysm will have a concomitant AAA; finding one should prompt screening for the other."
  },
  {
    "question": "During a carotid endarterectomy, the surgeon notes a bradycardic response upon manipulating the carotid bulb. This is mediated by which nerve?",
    "option_a": "Vagus nerve (CN X)",
    "option_b": "Glossopharyngeal nerve (CN IX) via the Hering nerve",
    "option_c": "Hypoglossal nerve (CN XII)",
    "option_d": "Ansa cervicalis",
    "correct_answer": "B",
    "explanation": "The carotid sinus baroreceptors send signals via the Hering nerve (a branch of CN IX) to the brainstem, triggering a vagal response (bradycardia)."
  },
  {
    "question": "Which of the following is an absolute indication for 'Total Proctocolectomy' in a patient with Ulcerative Colitis?",
    "option_a": "Mild symptoms controlled by Mesalamine",
    "option_b": "Toxic megacolon refractory to medical management",
    "option_c": "Occurrence of erythema nodosum",
    "option_d": "One episode of bloody diarrhea",
    "correct_answer": "B",
    "explanation": "Emergent complications like toxic megacolon, perforation, or massive hemorrhage are absolute indications for surgery."
  },
  {
    "question": "A 'Frey's Syndrome' (auriculotemporal syndrome) is a complication of parotid surgery characterized by sweating while eating. What is the underlying mechanism?",
    "option_a": "Damage to the facial nerve",
    "option_b": "Misdirected regrowth of parasympathetic fibers to sympathetic sweat glands",
    "option_c": "Chronic infection of the parotid duct",
    "option_d": "Hyperthyroidism",
    "correct_answer": "B",
    "explanation": "Post-parotidectomy, parasympathetic fibers intended for the parotid gland mistakenly innervate sweat glands in the overlying skin."
  },
  {
    "question": "A 50-year-old male with a history of a 5 cm AAA undergoes open repair. On POD 2, he develops bloody diarrhea and leukocytosis. What is the most likely diagnosis?",
    "option_a": "C. difficile colitis",
    "option_b": "Ischemic colitis (IMA ligation)",
    "option_c": "Perforated diverticulitis",
    "option_d": "Internal hemorrhoids",
    "correct_answer": "B",
    "explanation": "Ischemic colitis is a known risk after AAA repair if the inferior mesenteric artery is ligated and collateral flow (e.g., from the SMA via the Griffith's point) is insufficient."
  },
  {
    "question": "What is the most common site of a 'Carcinoid Tumor' in the gastrointestinal tract?",
    "option_a": "Stomach",
    "option_b": "Small Bowel (specifically the terminal ileum)",
    "option_c": "Esophagus",
    "option_d": "Sigmoid colon",
    "correct_answer": "B",
    "explanation": "Carcinoid tumors (neuroendocrine tumors) are most frequently found in the small intestine, followed by the rectum and appendix."
  },
  {
    "question": "In the management of 'Venous Stasis Ulcers', what is the most important component of long-term therapy to prevent recurrence?",
    "option_a": "Long-term oral antibiotics",
    "option_b": "Compression therapy (e.g., stockings or Unna boots)",
    "option_c": "Daily topical steroid application",
    "option_d": "Bed rest with legs dependent",
    "correct_answer": "B",
    "explanation": "Compression therapy addresses the underlying venous hypertension, which is essential for healing and preventing recurrence of venous ulcers."
  },
  {
    "question": "Which of the following describes a 'Marjolin's Ulcer'?",
    "option_a": "A peptic ulcer in the duodenum",
    "option_b": "A squamous cell carcinoma arising in a chronic wound or burn scar",
    "option_c": "A venous ulcer on the medial malleolus",
    "option_d": "An ulcer caused by tuberculosis",
    "correct_answer": "B",
    "explanation": "Marjolin's ulcers are aggressive malignancies that develop in areas of chronic inflammation or previous skin trauma."
  },
  {
    "question": "What is the primary treatment for a 'Splenic Abscess' in a patient with multiple small collections?",
    "option_a": "Observation only",
    "option_b": "Splenectomy or percutaneous drainage plus antibiotics",
    "option_c": "Oral antifungal therapy alone",
    "option_d": "Massive IV fluid resuscitation only",
    "correct_answer": "B",
    "explanation": "Splenic abscesses carry high mortality; management requires drainage (if possible) or splenectomy along with broad-spectrum antibiotics."
  },
  {
    "question": "Which of the following is a classic clinical feature of 'Gastrinoma' (Zollinger-Ellison Syndrome) that helps distinguish it from simple PUD?",
    "option_a": "Low serum gastrin levels",
    "option_b": "Ulcers in distal/unusual locations and prominent gastric folds on endoscopy",
    "option_c": "Improvement with antacids only",
    "option_d": "Weight gain",
    "correct_answer": "B",
    "explanation": "ZE syndrome presents with multiple refractory ulcers, sometimes in the jejunum, and thickened gastric rugae due to trophic effects of gastrin."
  },
  {
    "question": "A patient presents with a neck mass that moves upward with swallowing and tongue protrusion. What is the most likely diagnosis?",
    "option_a": "Branchial cleft cyst",
    "option_b": "Thyroglossal duct cyst",
    "option_c": "Carotid body tumor",
    "option_d": "Thyroid adenoma",
    "correct_answer": "B",
    "explanation": "Thyroglossal duct cysts are midline structures attached to the hyoid bone, explaining their characteristic movement with the tongue."
  },
  {
    "question": "What is the most common cause of 'Secondary' Hyperparathyroidism?",
    "option_a": "Solitary parathyroid adenoma",
    "option_b": "Chronic Kidney Disease (CKD)",
    "option_c": "Vitamin D toxicity",
    "option_d": "Head and neck radiation",
    "correct_answer": "B",
    "explanation": "CKD leads to phosphate retention and low 1,25-dihydroxyvitamin D, which chronically stimulates the parathyroid glands to produce PTH."
  },
  {
    "question": "In a patient with 'Familial Adenomatous Polyposis' (FAP), what is the recommended age to begin screening colonoscopy?",
    "option_a": "Age 50",
    "option_b": "Age 10-12",
    "option_c": "At birth",
    "option_d": "Age 40",
    "correct_answer": "B",
    "explanation": "Screening for FAP begins in early puberty because the risk of developing polyps and subsequent cancer is extremely high and occurs at a young age."
  },
  {
    "question": "A 'Lyre Sign' on a carotid angiogram, where the internal and external carotid arteries are splayed apart, is characteristic of which tumor?",
    "option_a": "Thyroid carcinoma",
    "option_b": "Carotid body tumor (Paraganglioma)",
    "option_c": "Cystic hygroma",
    "option_d": "Lipoma",
    "correct_answer": "B",
    "explanation": "Carotid body tumors arise at the bifurcation and push the internal and external carotid arteries apart, creating the Lyre sign."
  },
  {
    "question": "Which bariatric surgery is associated with the highest risk of 'Malabsorption' and nutritional deficiencies?",
    "option_a": "Laparoscopic Adjustable Gastric Band",
    "option_b": "Biliopancreatic Diversion with Duodenal Switch (BPD/DS)",
    "option_c": "Sleeve Gastrectomy",
    "option_d": "Nissen Fundoplication",
    "correct_answer": "B",
    "explanation": "BPD/DS involves significant bypass of the small intestine, leading to profound malabsorption of fats and fat-soluble vitamins."
  },
  {
    "question": "A patient with 'Short Bowel Syndrome' after extensive resection is at increased risk for which type of kidney stone?",
    "option_a": "Struvite stones",
    "option_b": "Calcium oxalate stones",
    "option_c": "Uric acid stones",
    "option_d": "Cystine stones",
    "correct_answer": "B",
    "explanation": "Malabsorption of fats allows calcium to bind to fats (saponification) instead of oxalate, leaving free oxalate to be absorbed and excreted in the urine."
  },
  {
    "question": "What is the primary surgical treatment for 'Primary Hyperparathyroidism' due to four-gland hyperplasia?",
    "option_a": "Excision of only the largest gland",
    "option_b": "Subtotal parathyroidectomy (3.5 glands) or total parathyroidectomy with autotransplantation",
    "option_c": "Total thyroidectomy",
    "option_d": "Wait and watch",
    "correct_answer": "B",
    "explanation": "When all four glands are involved, most of the parathyroid tissue is removed, leaving a small remnant to maintain calcium homeostasis."
  },
  {
    "question": "Which of the following is the most common cause of 'Appendiceal Carcinoid'?",
    "option_a": "Smoking",
    "option_b": "Incidental finding during appendectomy for appendicitis",
    "option_c": "Chronic diarrhea",
    "option_d": "High fiber diet",
    "correct_answer": "B",
    "explanation": "Most appendiceal neuroendocrine tumors are asymptomatic and discovered incidentally after an appendectomy performed for other reasons."
  },
  {
    "question": "A 60-year-old female presents with chronic 'anal pruritus'. Exam reveals a well-demarcated, eczematous red plaque. Biopsy shows 'Paget cells'. What is the most important next step?",
    "option_a": "Apply topical antifungal",
    "option_b": "Workup for synchronous internal malignancy (e.g., colorectal or GYN cancer)",
    "option_c": "Cryotherapy",
    "option_d": "Reassurance only",
    "correct_answer": "B",
    "explanation": "Extramammary Paget's disease of the anus is highly associated with an underlying visceral malignancy in up to 40% of cases."
  },
  {
    "question": "Which bariatric procedure involves a 'gastric sleeve' but also carries a risk of severe bile reflux?",
    "option_a": "Roux-en-Y Gastric Bypass",
    "option_b": "Sleeve Gastrectomy",
    "option_c": "Mini-Gastric Bypass (One anastomosis)",
    "option_d": "Gastric Balloon",
    "correct_answer": "C",
    "explanation": "The mini-gastric bypass creates a loop anastomosis which can lead to alkaline (bile) reflux into the stomach and esophagus."
  },
  {
    "question": "In a patient with 'Phyllodes Tumor', how is the tumor differentiated from a fibroadenoma?",
    "option_a": "By the patient's age only",
    "option_b": "By the increased stromal cellularity and leaf-like growth pattern on histology",
    "option_c": "By the presence of microcalcifications only",
    "option_d": "They are the same thing",
    "correct_answer": "B",
    "explanation": "Phyllodes tumors are distinguished histologically by their leaf-like architecture and higher cellularity of the stroma compared to the glandular fibroadenoma."
  },
  {
    "question": "What is the most sensitive lab test for the diagnosis of a 'Medullary Thyroid Carcinoma' (MTC) recurrence?",
    "option_a": "Serum Thyroglobulin",
    "option_b": "Serum Calcitonin and CEA",
    "option_c": "TSH",
    "option_d": "Alkaline Phosphatase",
    "correct_answer": "B",
    "explanation": "MTC arises from C-cells; calcitonin and CEA are secreted by the tumor and serve as highly specific tumor markers."
  },
  {
    "question": "A patient on POD 3 after a major abdominal surgery has a bladder pressure of 25 mmHg and a new-onset oliguria. What is the diagnosis?",
    "option_a": "Dehydration",
    "option_b": "Abdominal Compartment Syndrome",
    "option_c": "Urinary Tract Infection",
    "option_d": "Normal postoperative recovery",
    "correct_answer": "B",
    "explanation": "Intra-abdominal pressure > 20 mmHg with associated organ dysfunction (like renal failure) defines Abdominal Compartment Syndrome."
  },
  {
    "question": "Which of the following 'Thyroid' procedures is associated with the lowest risk of permanent hypocalcemia?",
    "option_a": "Total thyroidectomy",
    "option_b": "Thyroid lobectomy (hemithyroidectomy)",
    "option_c": "Subtotal thyroidectomy",
    "option_d": "Near-total thyroidectomy",
    "correct_answer": "B",
    "explanation": "Removing only one lobe leaves the contralateral parathyroid glands undisturbed, making permanent hypocalcemia virtually impossible."
  },
  {
    "question": "What is the characteristic appearance of 'Gallbladder Sludge' on ultrasound?",
    "option_a": "Shadowing white stones",
    "option_b": "Low-level echoes that shift with gravity but do not shadow",
    "option_c": "Gas bubbles in the wall",
    "option_d": "Clear black fluid",
    "correct_answer": "B",
    "explanation": "Sludge consists of calcium bilirubinate and cholesterol crystals; it is echogenic (grey/white) but lacks the acoustic shadowing of solid stones."
  },
  {
    "question": "Which 'Suture' material is most appropriate for the anastomosis of a vascular graft?",
    "option_a": "Silk",
    "option_b": "Prolene (Polypropylene)",
    "option_c": "Vicryl (Polyglactin)",
    "option_d": "Chromic Gut",
    "correct_answer": "B",
    "explanation": "Prolene is a non-absorbable monofilament that has low thrombogenicity and maintains strength indefinitely, which is required for vascular repairs."
  },
  {
    "question": "A 'Meckel's Diverticulum' that causes bleeding in a child usually contains which type of ectopic tissue?",
    "option_a": "Pancreatic",
    "option_b": "Gastric",
    "option_c": "Colonic",
    "option_d": "Thyroid",
    "correct_answer": "B",
    "explanation": "Ectopic gastric mucosa secretes acid, which causes ulceration of the adjacent normal ileal mucosa, leading to painless bleeding."
  },
  {
    "question": "What is the primary risk of an 'Incarcerated' hernia compared to a reducible one?",
    "option_a": "It is always malignant",
    "option_b": "It can lead to strangulation and bowel ischemia",
    "option_c": "It causes weight gain",
    "option_d": "It causes high fever immediately",
    "correct_answer": "B",
    "explanation": "An incarcerated hernia is irreducible; if the blood supply is compromised by the tight hernia neck, it becomes strangulated (an emergency)."
  },
  {
    "question": "Which of the following is a classic clinical triad of 'Biliary Ileus'?",
    "option_a": "Fever, jaundice, RUQ pain",
    "option_b": "Pneumobilia, small bowel obstruction, and ectopic gallstone (Rigler's triad)",
    "option_c": "Tachycardia, hypotension, muffled heart sounds",
    "option_d": "Vomiting, distension, constipation",
    "correct_answer": "B",
    "explanation": "Rigler's triad is pathognomonic for gallstone ileus on imaging (usually CT or X-ray)."
  },
  {
    "question": "A patient with 'Crohn's Disease' has multiple strictures in the small bowel. What is the surgical technique used to widen the lumen without resecting bowel?",
    "option_a": "Stricturoplasty (e.g., Heineke-Mikulicz)",
    "option_b": "Wedge resection",
    "option_c": "Total colectomy",
    "option_d": "Vagotomy",
    "correct_answer": "A",
    "explanation": "Stricturoplasty is a bowel-sparing technique essential in Crohn's to prevent Short Bowel Syndrome."
  },
  {
    "question": "What is the most common cause of 'Pseudo-obstruction' (Ogilvie Syndrome)?",
    "option_a": "A large tumor in the rectum",
    "option_b": "Autonomic imbalance in severely ill or postoperative patients",
    "option_c": "Ingestion of a magnet",
    "option_d": "Twisting of the sigmoid colon",
    "correct_answer": "B",
    "explanation": "Ogilvie's is a functional dilation of the colon, often triggered by metabolic derangements, trauma, or non-abdominal surgery."
  },
  {
    "question": "A 'Sentinel Loop' on an abdominal X-ray is a localized ileus that often points toward:",
    "option_a": "The liver",
    "option_b": "An underlying inflammatory process (e.g., pancreatitis or cholecystitis)",
    "option_c": "A normal finding",
    "option_d": "Colon cancer",
    "correct_answer": "B",
    "explanation": "Inflammation of a nearby organ causes localized paralysis of a segment of small bowel, which dilates and traps gas."
  },
  {
    "question": "Which of the following is an early symptom of 'Acute Mesenteric Ischemia'?",
    "option_a": "Profuse hematochezia",
    "option_b": "Severe abdominal pain out of proportion to physical exam findings",
    "option_c": "Board-like abdominal rigidity",
    "option_d": "Painless jaundice",
    "correct_answer": "B",
    "explanation": "The lack of peritoneal signs (soft abdomen) despite agonizing pain is the hallmark of early mesenteric ischemia."
  },
  {
    "question": "In the 'TNM' staging of Gastric Cancer, 'T3' refers to a tumor that invades:",
    "option_a": "Only the mucosa",
    "option_b": "The muscularis propria",
    "option_c": "The subserosa",
    "option_d": "The visceral peritoneum (serosa)",
    "correct_answer": "C",
    "explanation": "T1 (mucosa/submucosa), T2 (muscularis propria), T3 (subserosa), T4 (serosa/adjacent organs)."
  },
  {
    "question": "What is the primary treatment for a 'Differentiated Thyroid Cancer' (Papillary or Follicular) that is >4 cm?",
    "option_a": "Observation",
    "option_b": "Total thyroidectomy followed by Radioactive Iodine (RAI) ablation",
    "option_c": "Chemotherapy and external beam radiation",
    "option_d": "Antibiotics",
    "correct_answer": "B",
    "explanation": "Larger differentiated thyroid cancers require total removal and RAI to eliminate any microscopic residual tissue or metastases."
  },
  {
    "question": "Which of the following is true about 'Incisional Hernias'?",
    "option_a": "They have the lowest recurrence rate of all hernias",
    "option_b": "They are caused by a failure of the fascial closure to heal properly",
    "option_c": "They only occur after laparoscopic surgery",
    "option_d": "They never require mesh for repair",
    "correct_answer": "B",
    "explanation": "Incisional hernias result from technical failure of the closure or patient factors (like infection/obesity) that impair wound healing."
  },
  {
    "question": "A patient has a 'porcelain gallbladder' on CT. Why is this finding clinically concerning?",
    "option_a": "It indicates a high risk of rupture",
    "option_b": "It is associated with an increased risk of gallbladder adenocarcinoma",
    "option_c": "It means the patient has a parasitic infection",
    "option_d": "It causes severe hypercalcemia",
    "correct_answer": "B",
    "explanation": "Calcification of the gallbladder wall (porcelain) is a known precursor or indicator of malignancy."
  },
  {
    "question": "What is the surgical landmark used for a 'Nissen Fundoplication'?",
    "option_a": "The pylorus",
    "option_b": "The gastroesophageal junction and the short gastric vessels",
    "option_c": "The ligament of Treitz",
    "option_d": "The common bile duct",
    "correct_answer": "B",
    "explanation": "The procedure involves mobilizing the fundus (often by dividing the short gastric vessels) and wrapping it around the distal esophagus."
  },
  {
    "question": "A 'Heller Myotomy' is the surgical treatment for which motility disorder?",
    "option_a": "GERD",
    "option_b": "Achalasia",
    "option_c": "Diffuse esophageal spasm",
    "option_d": "Gastroparesis",
    "correct_answer": "B",
    "explanation": "The myotomy cuts the lower esophageal sphincter muscle fibers to allow passage of food."
  },
  {
    "question": "Which of the following describes 'Cullen's sign'?",
    "option_a": "Flank ecchymosis",
    "option_b": "Periumbilical ecchymosis",
    "option_c": "Pain in the RUQ",
    "option_d": "Drooping of the eyelid",
    "correct_answer": "B",
    "explanation": "Both Cullen's and Grey Turner's (flank) signs indicate retroperitoneal bleeding, typically from severe pancreatitis."
  },
  {
    "question": "What is the primary electrolyte disturbance in 'Adrenal Insufficiency' (Addisonian Crisis)?",
    "option_a": "Hypernatremia and hypokalemia",
    "option_b": "Hyponatremia and hyperkalemia",
    "option_c": "Hypercalcemia",
    "option_d": "Hypomagnesemia",
    "correct_answer": "B",
    "explanation": "Lack of aldosterone leads to renal sodium wasting and potassium retention."
  },
  {
    "question": "In vascular surgery, an 'ABI' (Ankle-Brachial Index) of 0.3 indicates:",
    "option_a": "Normal circulation",
    "option_b": "Severe peripheral arterial disease (often with rest pain)",
    "option_c": "Mild claudication",
    "option_d": "Venous insufficiency",
    "correct_answer": "B",
    "explanation": "ABI < 0.9 is abnormal; < 0.4 indicates severe ischemia."
  },
  {
    "question": "Which 'Polyp' type is NOT considered a precursor to colon cancer?",
    "option_a": "Tubular adenoma",
    "option_b": "Serrated adenoma",
    "option_c": "Hyperplastic polyp (usually)",
    "option_d": "Villous adenoma",
    "correct_answer": "C",
    "explanation": "Most small hyperplastic polyps are considered benign with no malignant potential, unlike adenomatous polyps."
  },
  {
    "question": "What is the treatment of choice for a 'Pilonidal Abscess'?",
    "option_a": "Long-term antibiotics alone",
    "option_b": "Incision and drainage",
    "option_c": "Total colectomy",
    "option_d": "Steroid injection",
    "correct_answer": "B",
    "explanation": "Acute abscesses in the pilonidal sinus require surgical drainage for relief of pain and control of infection."
  },
  {
    "question": "Which anatomical structure is divided during a 'Lateral Internal Sphincterotomy'?",
    "option_a": "The external anal sphincter",
    "option_b": "The internal anal sphincter",
    "option_c": "The levator ani muscle",
    "option_d": "The rectum",
    "correct_answer": "B",
    "explanation": "This procedure is used for chronic anal fissures to reduce high sphincter resting pressure."
  },
  {
    "question": "A patient with 'Secondary Peritonitis' due to a perforated colon should undergo which primary surgical priority?",
    "option_a": "Long-term TPN only",
    "option_b": "Control of the source (resection/closure) and peritoneal washout",
    "option_c": "High-dose aspirin",
    "option_d": "Observation",
    "correct_answer": "B",
    "explanation": "Surgical management of secondary peritonitis focuses on eliminating the source of contamination and cleaning the abdominal cavity."
  },
  {
    "question": "Which tumor marker is primarily used to monitor patients with 'Hepatocellular Carcinoma'?",
    "option_a": "CEA",
    "option_b": "Alpha-fetoprotein (AFP)",
    "option_c": "CA 125",
    "option_d": "PSA",
    "correct_answer": "B",
    "explanation": "AFP is the standard serum marker for HCC screening and surveillance."
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
