import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

import json

# Load questions from JSON file
with open('/app/psychiatry_batch_2.json', 'r', encoding='utf-8') as f:
    questions_data = json.load(f)

_old_data = [
  {
    "question": "A 52-year-old female presents with a 2 cm firm breast mass. Mammography shows a spiculed lesion with microcalcifications. What is the next most appropriate step in diagnosis?",
    "option_a": "Repeat mammography in 6 months",
    "option_b": "Fine needle aspiration (FNA)",
    "option_c": "Core needle biopsy",
    "option_d": "Excisional biopsy",
    "correct_answer": "C",
    "explanation": "Core needle biopsy is preferred over FNA for solid breast masses as it provides histological architecture, allowing differentiation between invasive and in-situ carcinoma."
  },
  {
    "question": "Which of the following thyroid cancers is associated with the RET proto-oncogene and part of Multiple Endocrine Neoplasia (MEN) type 2?",
    "option_a": "Papillary carcinoma",
    "option_b": "Follicular carcinoma",
    "option_c": "Medullary carcinoma",
    "option_d": "Anaplastic carcinoma",
    "correct_answer": "C",
    "explanation": "Medullary thyroid carcinoma arises from parafollicular C-cells and is a hallmark component of MEN 2A and 2B syndromes."
  },
  {
    "question": "A 65-year-old male with a history of multiple abdominal surgeries presents with vomiting, abdominal distension, and inability to pass flatus. Which X-ray finding best supports a diagnosis of small bowel obstruction?",
    "option_a": "Air in the rectum",
    "option_b": "Dilated small bowel loops (>3 cm) with multiple air-fluid levels",
    "option_c": "Distended cecum with a 'coffee bean' appearance",
    "option_d": "Blurred psoas shadow",
    "correct_answer": "B",
    "explanation": "Dilated small bowel loops without gas in the colon are characteristic of mechanical small bowel obstruction, often due to adhesions."
  },
  {
    "question": "In a patient with suspected necrotizing fasciitis, which clinical finding is the most sensitive early indicator?",
    "option_a": "Crepitus on palpation",
    "option_b": "Pain out of proportion to physical exam findings",
    "option_c": "Skin necrosis and bullae",
    "option_d": "High-grade fever",
    "correct_answer": "B",
    "explanation": "Pain out of proportion is a classic early sign of necrotizing soft tissue infection, often occurring before visible skin changes like necrosis or crepitus."
  },
  {
    "question": "Which molecular marker is targeted by the drug Trastuzumab (Herceptin) in the treatment of breast cancer?",
    "option_a": "Estrogen receptor (ER)",
    "option_b": "Progesterone receptor (PR)",
    "option_c": "HER2/neu receptor",
    "option_d": "BRCA1 mutation",
    "correct_answer": "C",
    "explanation": "Trastuzumab is a monoclonal antibody specifically designed to target and inhibit the HER2/neu receptor in overexpressing breast cancers."
  },
  {
    "question": "A 40-year-old patient presents with a solitary 1.5 cm thyroid nodule. TSH is normal. FNA shows 'follicular neoplasm'. What is the most appropriate surgical management?",
    "option_a": "Total thyroidectomy",
    "option_b": "Thyroid lobectomy (Hemithyroidectomy)",
    "option_c": "Radioactive iodine ablation",
    "option_d": "Observation only",
    "correct_answer": "B",
    "explanation": "Since FNA cannot distinguish between follicular adenoma and carcinoma, a lobectomy is performed for definitive histological diagnosis of the capsule."
  },
  {
    "question": "What is the primary cause of 'Hungry Bone Syndrome' following a parathyroidectomy for primary hyperparathyroidism?",
    "option_a": "Persistent high PTH levels",
    "option_b": "Rapid uptake of calcium by bones after the removal of the PTH source",
    "option_c": "Renal failure",
    "option_d": "Vitamin D toxicity",
    "correct_answer": "B",
    "explanation": "The sudden drop in PTH causes a shift of calcium and phosphate into 'starved' bones, leading to profound postoperative hypocalcemia."
  },
  {
    "question": "A 25-year-old female presents with a painless, highly mobile, rubbery breast mass. What is the most likely diagnosis?",
    "option_a": "Fibroadenoma",
    "option_b": "Breast cyst",
    "option_c": "Phyllodes tumor",
    "option_d": "Fat necrosis",
    "correct_answer": "A",
    "explanation": "Fibroadenoma is the most common benign breast tumor in young women, classically described as a 'breast mouse' due to its mobility."
  },
  {
    "question": "Which of the following defines an 'R1' resection in surgical oncology?",
    "option_a": "No residual tumor (microscopic or macroscopic)",
    "option_b": "Microscopic residual tumor at the margins",
    "option_c": "Macroscopic residual tumor left behind",
    "option_d": "Metastatic disease present",
    "correct_answer": "B",
    "explanation": "R0 is a clean margin, R1 is microscopic residual disease, and R2 is macroscopic residual disease."
  },
  {
    "question": "A patient with a large bowel obstruction shows a massive, dilated loop of colon in the RLQ pointing toward the LUQ, resembling an 'inverted U'. This is suggestive of:",
    "option_a": "Sigmoid volvulus",
    "option_b": "Cecal volvulus",
    "option_c": "Ogilvie's syndrome",
    "option_d": "Intussusception",
    "correct_answer": "B",
    "explanation": "Cecal volvulus classically presents as a dilated loop of colon in the mid-abdomen or LUQ, whereas sigmoid volvulus is more common in the LLQ."
  },
  {
    "question": "Which of the following is a classic clinical sign of 'Inflammatory Breast Cancer'?",
    "option_a": "A small, mobile nodule",
    "option_b": "Peau d'orange (skin thickening and pitting)",
    "option_c": "Bloody nipple discharge",
    "option_d": "Cyclic breast pain",
    "correct_answer": "B",
    "explanation": "Peau d'orange skin changes are caused by tumor emboli blocking the dermal lymphatics, characteristic of inflammatory breast cancer."
  },
  {
    "question": "During a thyroidectomy, a surgeon accidentally ligates the superior laryngeal nerve. What is the expected clinical consequence?",
    "option_a": "Total loss of voice",
    "option_b": "Inability to reach high-pitched notes (voice fatigue)",
    "option_c": "Stridor and airway obstruction",
    "option_d": "Difficulty swallowing liquids",
    "correct_answer": "B",
    "explanation": "The external branch of the superior laryngeal nerve innervates the cricothyroid muscle; its loss affects vocal cord tension."
  },
  {
    "question": "What is the most common cause of 'Large Bowel Obstruction' in an adult population?",
    "option_a": "Volvulus",
    "option_b": "Diverticulitis",
    "option_c": "Colorectal carcinoma",
    "option_d": "Incarcerated hernia",
    "correct_answer": "C",
    "explanation": "Malignancy (adenocarcinoma) is the leading cause of large bowel obstruction, followed by diverticulitis and sigmoid volvulus."
  },
  {
    "question": "Which electrolyte abnormality is typically seen in a patient with significant 'Third-Space' fluid loss following major abdominal surgery?",
    "option_a": "Hypernatremia",
    "option_b": "Hyponatremia",
    "option_c": "Hyperkalemia",
    "option_d": "Hypocalcemia",
    "correct_answer": "B",
    "explanation": "Fluid sequestration and subsequent ADH release often lead to dilutional hyponatremia in the postoperative setting."
  },
  {
    "question": "A 'Sentinel Lymph Node' in breast cancer refers to:",
    "option_a": "The largest node in the axilla",
    "option_b": "The first node(s) to receive lymphatic drainage from the primary tumor",
    "option_c": "Nodes that are fixed and hard on exam",
    "option_d": "Supraclavicular nodes",
    "correct_answer": "B",
    "explanation": "The sentinel node biopsy is used to determine if the cancer has spread to the axilla without performing a full dissection."
  },
  {
    "question": "A 45-year-old male presents with sudden abdominal pain and 'currant jelly' stools. This presentation is most classic for:",
    "option_a": "Appendicitis",
    "option_b": "Intussusception",
    "option_c": "Perforated ulcer",
    "option_d": "Mesenteric ischemia",
    "correct_answer": "B",
    "explanation": "In adults, intussusception is often associated with a lead point (like a tumor) and presents with colicky pain and bloody stools."
  },
  {
    "question": "Which of the following is true regarding 'Phyllodes Tumors' of the breast?",
    "option_a": "They are always benign",
    "option_b": "They can be benign, borderline, or malignant and require wide local excision",
    "option_c": "They are treated with axillary lymph node dissection",
    "option_d": "They respond very well to radiotherapy",
    "correct_answer": "B",
    "explanation": "Phyllodes tumors are stromal tumors that can recur locally if not excised with clear margins of at least 1 cm."
  },
  {
    "question": "What is the management of choice for a sigmoid volvulus in a stable patient without signs of gangrene?",
    "option_a": "Emergency laparotomy and resection",
    "option_b": "Endoscopic detorsion (Sigmoidoscopy) and rectal tube placement",
    "option_c": "Oral laxatives",
    "option_d": "Observation only",
    "correct_answer": "B",
    "explanation": "Stable patients can often be decompressed endoscopically, allowing for a planned elective resection later to prevent recurrence."
  },
  {
    "question": "Which of the following describes 'Courvoisier's Sign' in a patient with jaundice?",
    "option_a": "Painful gallbladder and fever",
    "option_b": "Palpable, non-tender gallbladder",
    "option_c": "Spleen enlargement",
    "option_d": "Ascites",
    "correct_answer": "B",
    "explanation": "A palpable, non-tender gallbladder in a jaundiced patient suggests malignant obstruction of the common bile duct (e.g., pancreatic cancer)."
  },
  {
    "question": "A 70-year-old male with chronic atrial fibrillation presents with sudden, severe abdominal pain and a relatively normal physical exam. Diagnosis?",
    "option_a": "Perforated ulcer",
    "option_b": "Acute mesenteric ischemia",
    "option_c": "Biliary colic",
    "option_d": "Sigmoid volvulus",
    "correct_answer": "B",
    "explanation": "The classic 'pain out of proportion to exam' in a patient with AFib is highly suspicious for an embolic event in the superior mesenteric artery."
  },
  {
    "question": "What is the primary treatment for 'Ductal Carcinoma In Situ' (DCIS) discovered on screening mammography?",
    "option_a": "Chemotherapy only",
    "option_b": "Surgical excision (Lumpectomy or Mastectomy) with clear margins",
    "option_c": "Annual observation",
    "option_d": "Hormone replacement therapy",
    "correct_answer": "B",
    "explanation": "DCIS is a non-invasive cancer but is a precursor to invasive disease; therefore, surgical removal is necessary."
  },
  {
    "question": "Which of the following is a classic symptom of 'Toxic Megacolon'?",
    "option_a": "Severe constipation with no pain",
    "option_b": "Bloody diarrhea, high fever, and abdominal distension >6 cm",
    "option_c": "Painless jaundice",
    "option_d": "Normal bowel habits",
    "correct_answer": "B",
    "explanation": "Toxic megacolon is a life-threatening complication of IBD or C. diff infection characterized by massive colonic dilation and systemic toxicity."
  },
  {
    "question": "Which suture technique is best for closing a contaminated wound if primary closure is decided?",
    "option_a": "Continuous running suture",
    "option_b": "Interrupted simple sutures",
    "option_c": "Subcuticular closure",
    "option_d": "Steel staples",
    "correct_answer": "B",
    "explanation": "Interrupted sutures allow for the drainage of fluid and the removal of individual sutures if an infection develops, unlike continuous sutures."
  },
  {
    "question": "A patient undergoes total parathyroidectomy and develops carpopedal spasms. What is the treatment?",
    "option_a": "IV Potassium",
    "option_b": "IV Calcium gluconate",
    "option_c": "IV Magnesium",
    "option_d": "IV Normal Saline",
    "correct_answer": "B",
    "explanation": "Trousseau's and Chvostek's signs are indicators of acute hypocalcemia, treated with intravenous calcium."
  },
  {
    "question": "Which type of hernia contains only a portion of the bowel wall (the antimesenteric border) and may not show signs of obstruction?",
    "option_a": "Richter's hernia",
    "option_b": "Littre's hernia",
    "option_c": "Amyand's hernia",
    "option_d": "Petit's hernia",
    "correct_answer": "A",
    "explanation": "Richter's hernias can lead to localized necrosis and perforation without causing a complete mechanical obstruction."
  },
  {
    "question": "In surgical oncology, 'Neoadjuvant' therapy is administered:",
    "option_a": "After the main surgical procedure",
    "option_b": "Before the main surgical procedure to shrink the tumor",
    "option_c": "Only when surgery is impossible",
    "option_d": "During the operation itself",
    "correct_answer": "B",
    "explanation": "Neoadjuvant therapy aims to improve the likelihood of a successful R0 resection."
  },
  {
    "question": "What is the clinical definition of 'Acalculous Cholecystitis'?",
    "option_a": "Chronic gallstones with no pain",
    "option_b": "Gallbladder inflammation in the absence of stones, typically in critically ill patients",
    "option_c": "Multiple small cholesterol stones",
    "option_d": "Obstruction of the common bile duct only",
    "correct_answer": "B",
    "explanation": "Acalculous cholecystitis is common in ICU, trauma, or burn patients due to gallbladder stasis and ischemia."
  },
  {
    "question": "What is the most common cause of 'Postoperative Ileus'?",
    "option_a": "Excessive IV fluids",
    "option_b": "Normal response to surgical handling of the bowel and anesthetics",
    "option_c": "Internal hernia",
    "option_d": "Wound infection",
    "correct_answer": "B",
    "explanation": "Postoperative ileus is a temporary paralysis of bowel motility that typically resolves within 3-5 days."
  },
  {
    "question": "Which factor is the most important prognostic indicator in a patient with early-stage breast cancer?",
    "option_a": "Patient age",
    "option_b": "Axillary lymph node status",
    "option_c": "Tumor grade",
    "option_d": "Size of the breast",
    "correct_answer": "B",
    "explanation": "The presence or absence of lymph node metastasis remains the most significant predictor of overall survival."
  },
  {
    "question": "A 'Hürthle cell' neoplasm is a variant of which type of thyroid cancer?",
    "option_a": "Papillary",
    "option_b": "Follicular",
    "option_c": "Medullary",
    "option_d": "Anaplastic",
    "correct_answer": "B",
    "explanation": "Hürthle cell cancer is often considered a more aggressive subtype of follicular thyroid carcinoma."
  },
  {
    "question": "Which of the following is true about 'Ogilvie's Syndrome'?",
    "option_a": "It always requires immediate surgical resection",
    "option_b": "It is a pseudo-obstruction of the colon, often responding to neostigmine",
    "option_c": "It is caused by a mechanical tumor",
    "option_d": "It only occurs in children",
    "correct_answer": "B",
    "explanation": "Ogilvie's is a functional dilation of the colon. Neostigmine can be used to stimulate bowel contraction."
  },
  {
    "question": "What is the primary treatment for 'Paget's Disease of the Nipple'?",
    "option_a": "Topical antifungal cream",
    "option_b": "Surgical treatment (Mastectomy or Lumpectomy) including the nipple-areolar complex",
    "option_c": "Oral antibiotics",
    "option_d": "Observation",
    "correct_answer": "B",
    "explanation": "Paget's disease is highly associated with an underlying breast malignancy (DCIS or invasive) and requires oncologic surgical management."
  },
  {
    "question": "During surgery for a strangulated hernia, if the bowel segment appears dusky but improves in color after warming with saline, the surgeon should:",
    "option_a": "Resect the segment immediately",
    "option_b": "Re-evaluate viability and potentially return it to the abdomen",
    "option_c": "Apply local antibiotics and close",
    "option_d": "Remove the mesh only",
    "correct_answer": "B",
    "explanation": "The decision to resect depends on whether perfusion returns; warming can help identify viable tissue."
  },
  {
    "question": "Which of the following is an absolute contraindication to the laparoscopic approach in abdominal surgery?",
    "option_a": "Obesity",
    "option_b": "Previous abdominal surgeries with extensive adhesions",
    "option_c": "Inability to tolerate pneumoperitoneum due to severe cardiopulmonary disease",
    "option_d": "Advanced age",
    "correct_answer": "C",
    "explanation": "Pneumoperitoneum increases intra-abdominal pressure, which can significantly compromise cardiac output and ventilation in fragile patients."
  },
  {
    "question": "What is the purpose of 'Delayed Primary Closure'?",
    "option_a": "To make the scar look better",
    "option_b": "To allow a contaminated wound to begin healing before final closure to reduce infection risk",
    "option_c": "To wait for a specific surgeon to arrive",
    "option_d": "To avoid using sutures",
    "correct_answer": "B",
    "explanation": "Typically used in 'dirty' wounds where immediate closure would likely result in an abscess."
  },
  {
    "question": "A 'Third-degree burn' is best described as:",
    "option_a": "Painful with blisters",
    "option_b": "Full-thickness, painless, with a leathery or charred appearance",
    "option_c": "Red and blanching",
    "option_d": "Only involving the epidermis",
    "correct_answer": "B",
    "explanation": "Third-degree burns destroy the dermis and sensory nerves, making the area anesthetic (painless) initially."
  },
  {
    "question": "Which hormone is the primary tumor marker used for surveillance after treatment of Medullary Thyroid Carcinoma?",
    "option_a": "Thyroglobulin",
    "option_b": "Calcitonin",
    "option_c": "PTH",
    "option_d": "TSH",
    "correct_answer": "B",
    "explanation": "Calcitonin (and CEA) are produced by medullary thyroid cancer cells and reflect the tumor burden."
  },
  {
    "question": "A 'Sistrunk Procedure' is used for the removal of which congenital neck mass?",
    "option_a": "Branchial cleft cyst",
    "option_b": "Thyroglossal duct cyst",
    "option_c": "Cystic hygroma",
    "option_d": "Dermoid cyst",
    "correct_answer": "B",
    "explanation": "It involves removing the cyst and the middle part of the hyoid bone to reduce the high rate of recurrence."
  },
  {
    "question": "Which of the following is a classic finding in 'Gallstone Ileus'?",
    "option_a": "Air in the biliary tree (pneumobilia) on X-ray",
    "option_b": "High fever and jaundice",
    "option_c": "Diarrhea",
    "option_d": "Low white blood cell count",
    "correct_answer": "A",
    "explanation": "Gallstone ileus occurs when a stone erodes into the duodenum; Rigler's triad includes pneumobilia, SBO, and a gallstone in an unusual location."
  },
  {
    "question": "A patient with a retrosternal goiter most commonly presents with:",
    "option_a": "Cardiac arrhythmias",
    "option_b": "Dyspnea and cough due to tracheal compression",
    "option_c": "Bone pain",
    "option_d": "Skin rash",
    "correct_answer": "B",
    "explanation": "The limited space in the thoracic inlet means enlarging thyroid tissue will often compress the trachea or esophagus."
  },
  {
    "question": "What is the primary management for a simple breast cyst that is causing pain?",
    "option_a": "Total mastectomy",
    "option_b": "Fine needle aspiration (therapeutic drainage)",
    "option_c": "Course of antibiotics",
    "option_d": "Hormone therapy",
    "correct_answer": "B",
    "explanation": "Aspiration usually resolves the pain and confirms the diagnosis; if the fluid is non-bloody and the cyst disappears, no further workup is needed."
  },
  {
    "question": "Which of the following is an early sign of local anesthetic toxicity (systemic absorption)?",
    "option_a": "Cardiac arrest",
    "option_b": "Metallic taste or perioral numbness",
    "option_c": "Hypercalcemia",
    "option_d": "Severe hypertension",
    "correct_answer": "B",
    "explanation": "Neurological symptoms like tinnitus, metallic taste, and numbness often precede major CNS or cardiac events in LAST (Local Anesthetic Systemic Toxicity)."
  },
  {
    "question": "What is the 'Gold Standard' for diagnosing a suspected thyroid nodule?",
    "option_a": "CT Neck with contrast",
    "option_b": "Fine Needle Aspiration (FNA)",
    "option_c": "Thyroid Ultrasound only",
    "option_d": "Serum Thyroglobulin",
    "correct_answer": "B",
    "explanation": "FNA is the most accurate and cost-effective method to determine if a nodule is malignant."
  },
  {
    "question": "In surgical nutrition, a patient whose gut is not functional should receive:",
    "option_a": "Enteral nutrition",
    "option_b": "Total Parenteral Nutrition (TPN)",
    "option_c": "Dextrose 5% only",
    "option_d": "Clear liquid diet",
    "correct_answer": "B",
    "explanation": "TPN provides all nutrients intravenously when the gastrointestinal tract cannot be used."
  },
  {
    "question": "Which of the following is true regarding 'Anaplastic Thyroid Cancer'?",
    "option_a": "It has an excellent prognosis",
    "option_b": "It is a highly aggressive cancer with a very poor prognosis, often presenting with rapid neck growth",
    "option_c": "It only occurs in young children",
    "option_d": "It is treated exclusively with radioactive iodine",
    "correct_answer": "B",
    "explanation": "Anaplastic cancer is one of the most lethal malignancies, often incurable at the time of diagnosis."
  },
  {
    "question": "What is the surgical landmark used during cholecystectomy to avoid common bile duct injury?",
    "option_a": "Ligament of Treitz",
    "option_b": "Triangle of Calot",
    "option_c": "Foramen of Winslow",
    "option_d": "Hesselbach's Triangle",
    "correct_answer": "B",
    "explanation": "Proper identification of Calot's triangle (cystic duct, common hepatic duct, liver edge) is essential for safe surgery."
  },
  {
    "question": "The 'Rule of 2s' is associated with which surgical condition?",
    "option_a": "Appendicitis",
    "option_b": "Meckel's Diverticulum",
    "option_c": "Hernias",
    "option_d": "Cholecystitis",
    "correct_answer": "B",
    "explanation": "Meckel's: 2% of population, 2 feet from ileocecal valve, 2 inches long, 2 types of ectopic tissue, presents by age 2."
  },
  {
    "question": "Which of the following is a symptom of 'Dumping Syndrome' after gastric surgery?",
    "option_a": "Constipation",
    "option_b": "Palpitations, sweating, and diarrhea shortly after eating",
    "option_c": "Jaundice",
    "option_d": "Normal digestion",
    "correct_answer": "B",
    "explanation": "Caused by rapid transit of hyperosmolar food into the small bowel, leading to fluid shifts and hormonal responses."
  },
  {
    "question": "A patient on post-op day 5 has a temperature of 38.8°C and a red, tender surgical wound with purulent drainage. Diagnosis?",
    "option_a": "Atelectasis",
    "option_b": "Surgical Site Infection (SSI)",
    "option_c": "DVT",
    "option_d": "Drug fever",
    "correct_answer": "B",
    "explanation": "Fever starting after POD 3 with local wound signs is typical for a surgical site infection."
  },
  {
    "question": "What is the definitive treatment for 'Secondary Peritonitis' due to a perforated viscus?",
    "option_a": "Long-term antibiotics alone",
    "option_b": "Surgical control of the source and peritoneal washout",
    "option_c": "Percutaneous drainage only",
    "option_d": "High-dose steroids",
    "correct_answer": "B",
    "explanation": "Secondary peritonitis requires operative intervention to fix the source of contamination and clean the peritoneal cavity."
  },
  {
    "question": "A patient presents with colicky abdominal pain, distension, and high-pitched 'tinkling' bowel sounds. An X-ray shows dilated loops of small bowel with a 'step-ladder' appearance. What is the most likely diagnosis?",
    "option_a": "Paralytic ileus",
    "option_b": "Mechanical small bowel obstruction",
    "option_c": "Acute pancreatitis",
    "option_d": "Large bowel obstruction",
    "correct_answer": "B",
    "explanation": "Colicky pain, distension, and specific X-ray findings are classic for mechanical SBO; ileus usually presents with absent bowel sounds."
  },
  {
    "question": "What is the most common cause of large bowel obstruction (LBO)?",
    "option_a": "Volvulus",
    "option_b": "Colorectal cancer",
    "option_c": "Diverticulitis",
    "option_d": "Fecal impaction",
    "correct_answer": "B",
    "explanation": "Malignancy is the leading cause of LBO in adults, followed by diverticulitis and volvulus."
  },
  {
    "question": "A 70-year-old male presents with sudden, massive abdominal distension. X-ray shows a 'coffee bean' sign. What is the most likely diagnosis?",
    "option_a": "Cecal volvulus",
    "option_b": "Sigmoid volvulus",
    "option_c": "Small bowel obstruction",
    "option_d": "Intussusception",
    "correct_answer": "B",
    "explanation": "Sigmoid volvulus classically appears as a massive, smooth, bent inner-tube or 'coffee bean' shape on plain film."
  },
  {
    "question": "What is the initial management for a patient with a non-strangulated small bowel obstruction?",
    "option_a": "Immediate laparotomy",
    "option_b": "Nasogastric (NG) tube decompression, IV fluids, and observation",
    "option_c": "Barium enema",
    "option_d": "Oral laxatives",
    "correct_answer": "B",
    "explanation": "Many simple SBOs (especially due to adhesions) resolve with 'drip and suck' conservative management."
  },
  {
    "question": "Which of the following is a sign of strangulated bowel obstruction requiring urgent surgery?",
    "option_a": "Tinkling bowel sounds",
    "option_b": "Fever, leukocytosis, and localized tenderness",
    "option_c": "History of prior surgery",
    "option_d": "Minimal abdominal distension",
    "correct_answer": "B",
    "explanation": "Systemic inflammatory signs (fever, high WBC) and peritoneal signs suggest ischemia or infarction of the trapped bowel segment."
  },
  {
    "question": "Ogilvie's syndrome (acute colonic pseudo-obstruction) is most commonly seen in:",
    "option_a": "Young healthy athletes",
    "option_b": "Elderly, hospitalized, or severely ill patients",
    "option_c": "Pregnant women in the first trimester",
    "option_d": "Infants with Hirschsprung's disease",
    "correct_answer": "B",
    "explanation": "It is a functional obstruction caused by autonomic imbalance, often triggered by surgery, trauma, or severe infection."
  },
  {
    "question": "What is the most common benign breast mass in women under the age of 30?",
    "option_a": "Breast cyst",
    "option_b": "Fibroadenoma",
    "option_c": "Intraductal papilloma",
    "option_d": "Fat necrosis",
    "correct_answer": "B",
    "explanation": "Fibroadenomas are highly mobile, rubbery, firm, and non-tender masses common in young women."
  },
  {
    "question": "A 45-year-old female presents with spontaneous, bloody nipple discharge from a single duct. There is no palpable mass. What is the most likely diagnosis?",
    "option_a": "Fibrocystic change",
    "option_b": "Intraductal papilloma",
    "option_c": "Invasive ductal carcinoma",
    "option_d": "Mastitis",
    "correct_answer": "B",
    "explanation": "Intraductal papilloma is the most common cause of spontaneous bloody nipple discharge."
  },
  {
    "question": "Which of the following is the 'Triple Assessment' used for evaluating a breast lump?",
    "option_a": "Clinical exam, Mammography/Ultrasound, and Biopsy (FNA/Core)",
    "option_b": "Mammography, CT scan, and MRI",
    "option_c": "Blood tests, Clinical exam, and Ultrasound",
    "option_d": "Clinical exam, Breast self-exam, and Genetic testing",
    "correct_answer": "A",
    "explanation": "The combination of these three modalities ensures near 100% diagnostic accuracy for breast cancer."
  },
  {
    "question": "A 50-year-old female has a mammogram showing clustered microcalcifications. Biopsy reveals malignant cells that have not invaded the basement membrane. Diagnosis?",
    "option_a": "Invasive ductal carcinoma",
    "option_b": "Ductal carcinoma in situ (DCIS)",
    "option_c": "Lobular carcinoma in situ (LCIS)",
    "option_d": "Phyllodes tumor",
    "correct_answer": "B",
    "explanation": "DCIS is a non-invasive cancer confined to the ducts, often detected by calcifications on mammography."
  },
  {
    "question": "Which molecular subtype of breast cancer is known for being the most aggressive and lacking ER, PR, and HER2 expression?",
    "option_a": "Luminal A",
    "option_b": "Triple-Negative Breast Cancer",
    "option_c": "HER2-enriched",
    "option_d": "Luminal B",
    "correct_answer": "B",
    "explanation": "Triple-negative cancers do not respond to hormonal therapy or Trastuzumab and have a higher risk of recurrence."
  },
  {
    "question": "What is the primary management for a lactational breast abscess?",
    "option_a": "Stop breastfeeding immediately",
    "option_b": "Incision and drainage (or needle aspiration) plus antibiotics",
    "option_c": "Antibiotics alone",
    "option_d": "Mastectomy",
    "correct_answer": "B",
    "explanation": "Abscesses require drainage; patients are encouraged to continue breastfeeding or pumping to prevent further stasis."
  },
  {
    "question": "Which of the following describes Paget's disease of the breast?",
    "option_a": "A benign fungal infection of the nipple",
    "option_b": "Eczematous changes of the nipple associated with underlying DCIS or invasive cancer",
    "option_c": "A type of benign cyst",
    "option_d": "Fat necrosis after trauma",
    "correct_answer": "B",
    "explanation": "Any 'eczema' of the nipple that does not respond to topical steroids must be biopsied to rule out Paget's disease."
  },
  {
    "question": "Sentinel lymph node biopsy is performed in breast cancer to:",
    "option_a": "Cure the cancer",
    "option_b": "Identify the first node(s) draining the tumor to determine if full axillary dissection is needed",
    "option_c": "Remove all infected tissue",
    "option_d": "Inject chemotherapy directly into the arm",
    "correct_answer": "B",
    "explanation": "If the sentinel node is negative, the rest of the axillary nodes are likely negative, sparing the patient from lymphedema."
  },
  {
    "question": "What is the most common histological type of thyroid cancer?",
    "option_a": "Follicular carcinoma",
    "option_b": "Papillary carcinoma",
    "option_c": "Medullary carcinoma",
    "option_d": "Anaplastic carcinoma",
    "correct_answer": "B",
    "explanation": "Papillary thyroid cancer accounts for over 80% of cases and generally has an excellent prognosis."
  },
  {
    "question": "Psammoma bodies are a characteristic microscopic finding in which thyroid malignancy?",
    "option_a": "Follicular",
    "option_b": "Papillary",
    "option_c": "Medullary",
    "option_d": "Anaplastic",
    "correct_answer": "B",
    "explanation": "These are laminated calcium deposits typically seen in papillary thyroid cancer."
  },
  {
    "question": "Which thyroid cancer arises from the parafollicular C-cells and secretes calcitonin?",
    "option_a": "Papillary",
    "option_b": "Medullary",
    "option_c": "Follicular",
    "option_d": "Hürthle cell",
    "correct_answer": "B",
    "explanation": "Medullary thyroid cancer can be sporadic or part of MEN 2A/2B syndromes; calcitonin is used as a tumor marker."
  },
  {
    "question": "A patient undergoes a total thyroidectomy and develops a 'hoarse voice' postoperatively. Damage to which nerve is suspected?",
    "option_a": "Superior laryngeal nerve",
    "option_b": "Recurrent laryngeal nerve",
    "option_c": "Vagus nerve",
    "option_d": "Hypoglossal nerve",
    "correct_answer": "B",
    "explanation": "The recurrent laryngeal nerve innervates the intrinsic muscles of the larynx; injury causes vocal cord paralysis."
  },
  {
    "question": "What is the most common cause of 'Primary' Hyperparathyroidism?",
    "option_a": "Parathyroid hyperplasia",
    "option_b": "Solitary parathyroid adenoma",
    "option_c": "Parathyroid carcinoma",
    "option_d": "Vitamin D deficiency",
    "correct_answer": "B",
    "explanation": "A single benign adenoma is responsible for about 85-90% of cases of primary hyperparathyroidism."
  },
  {
    "question": "In the postoperative period following total thyroidectomy, a patient complains of tingling around the mouth (perioral paresthesia). What is the likely cause?",
    "option_a": "Hypokalemia",
    "option_b": "Hypocalcemia due to accidental parathyroid removal or injury",
    "option_c": "Hypercalcemia",
    "option_d": "Nerve damage only",
    "correct_answer": "B",
    "explanation": "Hypocalcemia is a common temporary or permanent complication after thyroid surgery due to parathyroid gland dysfunction."
  },
  {
    "question": "Which of the following is true regarding Follicular Thyroid Carcinoma?",
    "option_a": "It is easily diagnosed by Fine Needle Aspiration (FNA)",
    "option_b": "It requires histological evidence of capsular or vascular invasion for diagnosis",
    "option_c": "It always spreads via lymphatics",
    "option_d": "It is the most aggressive thyroid cancer",
    "correct_answer": "B",
    "explanation": "FNA cannot distinguish between follicular adenoma and carcinoma because it only looks at individual cells, not the capsule."
  },
  {
    "question": "What is the 'Gold Standard' diagnostic test for a thyroid nodule?",
    "option_a": "CT scan",
    "option_b": "Fine Needle Aspiration Biopsy (FNAB)",
    "option_c": "Thyroid Ultrasound",
    "option_d": "Serum Thyroglobulin",
    "correct_answer": "B",
    "explanation": "FNAB is the most cost-effective and accurate way to determine if a nodule is malignant."
  },
  {
    "question": "Anaplastic thyroid carcinoma is characterized by:",
    "option_a": "Slow growth and excellent prognosis",
    "option_b": "Rapid growth, local invasion, and very poor prognosis",
    "option_c": "Occurring primarily in teenagers",
    "option_d": "Responding well to radioactive iodine",
    "correct_answer": "B",
    "explanation": "Anaplastic cancer is one of the most lethal malignancies in humans, often presenting as a rapidly enlarging neck mass."
  },
  {
    "question": "A patient with MEN 2A syndrome will likely have which combination of conditions?",
    "option_a": "Pituitary adenoma, Parathyroid hyperplasia, Pancreatic tumors",
    "option_b": "Medullary thyroid cancer, Pheochromocytoma, Parathyroid hyperplasia",
    "option_c": "Papillary thyroid cancer, Adrenal adenoma",
    "option_d": "Thyroid storm and hypertension",
    "correct_answer": "B",
    "explanation": "MEN 2A is an autosomal dominant syndrome linked to the RET proto-oncogene."
  },
  {
    "question": "What is the primary role of the 'Frozen Section' during surgery?",
    "option_a": "To replace the final pathology report",
    "option_b": "To provide immediate intraoperative diagnosis and guide the extent of surgery",
    "option_c": "To check for the presence of bacteria",
    "option_d": "To store the tissue for years",
    "correct_answer": "B",
    "explanation": "Frozen sections allow the surgeon to know if margins are clear or if a mass is malignant while the patient is still on the table."
  },
  {
    "question": "In oncology, 'Adjuvant' therapy refers to:",
    "option_a": "Treatment given before surgery to shrink a tumor",
    "option_b": "Treatment given after the primary surgical resection to eliminate micro-metastases",
    "option_c": "Treatment for end-stage patients only",
    "option_d": "Surgical removal of the tumor",
    "correct_answer": "B",
    "explanation": "Adjuvant therapy (chemo, radiation, or hormone therapy) aims to reduce the risk of recurrence."
  },
  {
    "question": "What does 'Neoadjuvant' therapy mean?",
    "option_a": "Treatment after surgery",
    "option_b": "Treatment given before the main treatment (usually surgery) to reduce tumor size",
    "option_c": "Palliative care",
    "option_d": "Immunotherapy only",
    "correct_answer": "B",
    "explanation": "Commonly used in breast and rectal cancers to make the tumor more amenable to complete resection."
  },
  {
    "question": "A 'curative' resection in surgical oncology requires:",
    "option_a": "Leaving some tumor behind to avoid bleeding",
    "option_b": "Negative margins (R0 resection) and appropriate lymphadenectomy",
    "option_c": "Only removing the visible part of the tumor",
    "option_d": "Chemotherapy during the operation",
    "correct_answer": "B",
    "explanation": "R0 resection means no microscopic tumor remains at the surgical margins."
  },
  {
    "question": "What is the purpose of 'Palliative Surgery'?",
    "option_a": "To cure the patient of cancer",
    "option_b": "To relieve symptoms (e.g., bypass an obstruction) and improve quality of life in incurable patients",
    "option_c": "To perform a full transplant",
    "option_d": "To lower the cost of treatment",
    "correct_answer": "B",
    "explanation": "Palliative surgery focuses on comfort and function rather than longevity or cure."
  },
  {
    "question": "Which of the following is a classic sign of 'Thyroid Storm'?",
    "option_a": "Bradycardia and hypothermia",
    "option_b": "Tachycardia, high fever, and agitation",
    "option_c": "Weight gain and lethargy",
    "option_d": "Normal vital signs with a large goiter",
    "correct_answer": "B",
    "explanation": "Thyroid storm is a life-threatening hypermetabolic state caused by excessive thyroid hormones, often triggered by stress or surgery."
  },
  {
    "question": "During surgery, the 'Ligation' of a vessel means:",
    "option_a": "Cutting the vessel",
    "option_b": "Tying off the vessel to stop blood flow",
    "option_c": "Repairing a hole in the vessel",
    "option_d": "Inserting a stent",
    "correct_answer": "B",
    "explanation": "Ligation with sutures or clips is a fundamental surgical technique for hemostasis."
  },
  {
    "question": "What is the most common electrolyte complication of a massive blood transfusion?",
    "option_a": "Hypercalcemia",
    "option_b": "Hypocalcemia (due to citrate binding)",
    "option_c": "Hypernatremia",
    "option_d": "Hypokalemia",
    "correct_answer": "B",
    "explanation": "Citrate used as an anticoagulant in stored blood binds to the patient's ionized calcium."
  },
  {
    "question": "A patient with a retrosternal goiter is most likely to complain of:",
    "option_a": "Pain in the feet",
    "option_b": "Dyspnea and dysphagia due to tracheal and esophageal compression",
    "option_c": "Diarrhea",
    "option_d": "Loss of hearing",
    "correct_answer": "B",
    "explanation": "Retrosternal goiters grow into the narrow thoracic inlet, compressing nearby structures."
  },
  {
    "question": "What is the management of choice for a 'Toxic Multinodular Goiter'?",
    "option_a": "Wait and watch",
    "option_b": "Total or near-total thyroidectomy or Radioactive Iodine",
    "option_c": "Antibiotics",
    "option_d": "Beta-blockers only",
    "correct_answer": "B",
    "explanation": "Definitive treatment is required to resolve the hyperthyroidism caused by multiple autonomous nodules."
  },
  {
    "question": "In a patient with small bowel obstruction, what does the finding of 'pneumatosis intestinalis' (gas in the bowel wall) on CT indicate?",
    "option_a": "Early healing",
    "option_b": "Intestinal ischemia or necrosis",
    "option_c": "Normal bowel gas",
    "option_d": "Good response to NG tube",
    "correct_answer": "B",
    "explanation": "Pneumatosis is a worrisome sign of bowel wall compromise and often leads to emergent surgery."
  },
  {
    "question": "What is a 'Sistrunk Procedure' used for?",
    "option_a": "Appendectomy",
    "option_b": "Excision of a thyroglossal duct cyst",
    "option_c": "Hernia repair",
    "option_d": "Gallbladder removal",
    "correct_answer": "B",
    "explanation": "This procedure involves removing the cyst along with the mid-portion of the hyoid bone to prevent recurrence."
  },
  {
    "question": "A patient with high serum calcium and high PTH has a Sestamibi scan showing a 'hot spot' in the neck. Diagnosis?",
    "option_a": "Thyroid cancer",
    "option_b": "Parathyroid adenoma",
    "option_c": "Lymph node metastasis",
    "option_d": "Salivary gland tumor",
    "correct_answer": "B",
    "explanation": "Sestamibi is a specialized nuclear medicine scan used to localize hyperfunctioning parathyroid tissue."
  },
  {
    "question": "Which of the following is true about 'Phyllodes tumors' of the breast?",
    "option_a": "They are always benign",
    "option_b": "They are leaf-like stromal tumors that can be benign, borderline, or malignant",
    "option_c": "They are treated with hormonal therapy",
    "option_d": "They occur only in men",
    "correct_answer": "B",
    "explanation": "Phyllodes tumors grow rapidly and require wide local excision with clear margins to prevent recurrence."
  },
  {
    "question": "What is the most common cause of 'Mastitis' in breastfeeding women?",
    "option_a": "E. coli",
    "option_b": "Staphylococcus aureus",
    "option_c": "Streptococcus pyogenes",
    "option_d": "Candida",
    "correct_answer": "B",
    "explanation": "Bacteria from the infant's oropharynx enter through nipple cracks/fissures."
  },
  {
    "question": "In the TNM staging for cancer, what does the 'M' represent?",
    "option_a": "Margins",
    "option_b": "Distant metastasis",
    "option_c": "Muscle invasion",
    "option_d": "Malignancy grade",
    "correct_answer": "B",
    "explanation": "M0 means no distant spread, M1 means distant metastases are present."
  },
  {
    "question": "Which of the following is an absolute contraindication to 'Breast-Conserving Surgery' (Lumpectomy)?",
    "option_a": "Patient age over 60",
    "option_b": "Multicentric disease in different quadrants of the breast",
    "option_c": "Tumor size of 1 cm",
    "option_d": "History of hypertension",
    "correct_answer": "B",
    "explanation": "Multiple primary tumors in different areas of the breast generally require a mastectomy."
  },
  {
    "question": "A patient with breast cancer has a biopsy showing cells in a 'single-file' (indian file) pattern. What is the histological type?",
    "option_a": "Invasive Ductal Carcinoma",
    "option_b": "Invasive Lobular Carcinoma",
    "option_c": "Medullary Carcinoma",
    "option_d": "Mucinous Carcinoma",
    "correct_answer": "B",
    "explanation": "The loss of E-cadherin in lobular carcinoma causes cells to lose adhesion and form single-file lines."
  },
  {
    "question": "Which clinical sign involves retraction of the breast skin, suggesting an underlying malignancy?",
    "option_a": "Peau d'orange",
    "option_b": "Skin dimpling (tethering to Cooper's ligaments)",
    "option_c": "Erythema",
    "option_d": "Ulceration",
    "correct_answer": "B",
    "explanation": "Infiltration of the suspensory ligaments (Cooper's) by a tumor leads to skin retraction or dimpling."
  },
  {
    "question": "What is the significance of the 'BI-RADS' system in mammography?",
    "option_a": "It calculates the cost of the exam",
    "option_b": "It provides a standardized score for the risk of malignancy (0 to 6)",
    "option_c": "It identifies the patient's blood type",
    "option_d": "It is a type of ultrasound probe",
    "correct_answer": "B",
    "explanation": "BI-RADS 4 and 5 indicate a high suspicion of cancer and usually require a biopsy."
  },
  {
    "question": "During a thyroidectomy, damage to the External Branch of the Superior Laryngeal Nerve results in:",
    "option_a": "Total loss of voice",
    "option_b": "Inability to create high-pitched sounds (voice fatigue)",
    "option_c": "Aspiration",
    "option_d": "Difficulty swallowing only",
    "correct_answer": "B",
    "explanation": "This nerve supplies the cricothyroid muscle, which tenses the vocal cords; damage is common in professional singers."
  },
  {
    "question": "Which of the following is a symptom of 'Hypercalcemia'?",
    "option_a": "Diarrhea",
    "option_b": "Constipation, kidney stones, and bone pain",
    "option_c": "Muscle twitching",
    "option_d": "Hypotension",
    "correct_answer": "B",
    "explanation": "Mnemonic: 'Stones, Bones, Abdominal Groans, and Psychic Moans'."
  },
  {
    "question": "Which surgical procedure is used for a patient with 'Toxic Diffuse Goiter' (Graves') who fails medical therapy?",
    "option_a": "Isthmusectomy",
    "option_b": "Total or Subtotal thyroidectomy",
    "option_c": "Parathyroidectomy",
    "option_d": "Whipple procedure",
    "correct_answer": "B",
    "explanation": "Surgery provides a rapid and definitive cure for the hyperthyroid state."
  },
  {
    "question": "What is the most common cause of 'Lower GI Bleeding' in an adult over 60?",
    "option_a": "Hemorrhoids",
    "option_b": "Diverticulosis",
    "option_c": "Angiodysplasia",
    "option_d": "Colon cancer",
    "correct_answer": "B",
    "explanation": "Diverticulosis causes painless, often brisk hematochezia in the elderly."
  },
  {
    "question": "Which procedure involves removing the entire breast, axillary lymph nodes, and the pectoral fascia, but spares the pectoral muscles?",
    "option_a": "Radical Mastectomy",
    "option_b": "Modified Radical Mastectomy",
    "option_c": "Simple Mastectomy",
    "option_d": "Lumpectomy",
    "correct_answer": "B",
    "explanation": "The Modified Radical Mastectomy is the standard oncologic procedure when breast conservation is not feasible."
  }
]

COURSE_ID = "NVU_MD_Y3_S1_C25"

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
