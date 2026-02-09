import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

questions_data = [
  {
    "question": "What is the most common cause of small bowel obstruction (SBO) in developed countries?",
    "option_a": "Hernias",
    "option_b": "Postoperative adhesions",
    "option_c": "Malignancy",
    "option_d": "Crohn's disease",
    "correct_answer": "B",
    "explanation": "Adhesions from prior abdominal surgeries account for approximately 60-70% of SBO cases."
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
