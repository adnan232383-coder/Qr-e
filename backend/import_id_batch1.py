import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

questions_data = [
  {
    "question": "A 30-year-old male presents with a high fever, hypotension, and a diffuse 'sunburn-like' rash that involves the palms and soles. He recently had a nasal packing for a severe nosebleed. What is the most likely causative organism?",
    "option_a": "Streptococcus pyogenes",
    "option_b": "Staphylococcus aureus",
    "option_c": "Neisseria meningitidis",
    "option_d": "Rickettsia rickettsii",
    "correct_answer": "B",
    "explanation": "This describes Toxic Shock Syndrome (TSS), typically caused by TSS-toxin 1 (TSST-1) produced by S. aureus, often associated with absorbent packing or tampons."
  },
  {
    "question": "Which of the following describes the mechanism of action of Beta-lactam antibiotics (e.g., Penicillins)?",
    "option_a": "Inhibition of the 30S ribosomal subunit",
    "option_b": "Inhibition of the 50S ribosomal subunit",
    "option_c": "Inhibition of peptidoglycan cross-linking (transpeptidation)",
    "option_d": "Inhibition of DNA gyrase",
    "correct_answer": "C",
    "explanation": "Beta-lactams bind to Penicillin-Binding Proteins (PBPs), preventing the formation of cross-links in the bacterial cell wall."
  },
  {
    "question": "A 65-year-old patient on POD 10 following bowel surgery develops watery diarrhea and abdominal cramping. Stool tests are positive for Clostridioides difficile toxin. Which antibiotic is the first-line oral treatment for a first episode?",
    "option_a": "Metronidazole",
    "option_b": "Vancomycin",
    "option_c": "Ciprofloxacin",
    "option_d": "Amoxicillin",
    "correct_answer": "B",
    "explanation": "Current guidelines recommend oral Vancomycin or Fidaxomicin as first-line therapy for C. difficile infection (CDI)."
  },
  {
    "question": "Which of the following is a component of the qSOFA (quick Sepsis-related Organ Failure Assessment) score?",
    "option_a": "Temperature > 38°C",
    "option_b": "Altered mental status (GCS < 15)",
    "option_c": "White blood cell count > 12,000",
    "option_d": "Heart rate > 90 bpm",
    "correct_answer": "B",
    "explanation": "The qSOFA criteria are: Altered mental status, Respiratory rate ≥ 22, and Systolic BP ≤ 100 mmHg."
  },
  {
    "question": "A patient with fever and a new heart murmur has blood cultures positive for Streptococcus bovis (S. gallolyticus). What is the next most important diagnostic step?",
    "option_a": "Transthoracic echocardiogram only",
    "option_b": "Colonoscopy",
    "option_c": "Bone marrow biopsy",
    "option_d": "Repeat blood cultures in 48 hours",
    "correct_answer": "B",
    "explanation": "Streptococcus bovis bacteremia and endocarditis are highly associated with underlying colonic malignancies or polyps."
  },
  {
    "question": "Which CSF finding is most characteristic of acute Bacterial Meningitis?",
    "option_a": "High glucose, low protein, low WBCs",
    "option_b": "Low glucose, high protein, high neutrophils",
    "option_c": "Low glucose, low protein, high lymphocytes",
    "option_d": "Normal glucose, high protein, high lymphocytes",
    "correct_answer": "B",
    "explanation": "Bacteria consume glucose and produce inflammatory markers; neutrophils are the primary responders in bacterial infections."
  },
  {
    "question": "A 25-year-old male presents with a painless, indurated ulcer (chancre) on his penis. What is the treatment of choice?",
    "option_a": "Oral Azithromycin",
    "option_b": "Intramuscular Penicillin G Benzathine",
    "option_c": "Intravenous Ceftriaxone",
    "option_d": "Oral Doxycycline for 30 days",
    "correct_answer": "B",
    "explanation": "Primary syphilis is caused by Treponema pallidum and is treated with a single dose of IM Benzathine Penicillin G."
  },
  {
    "question": "Which of the following is the 'Major' Duke criterion for the diagnosis of Infective Endocarditis?",
    "option_a": "Fever > 38°C",
    "option_b": "Positive blood cultures with typical organisms (e.g., S. viridans)",
    "option_c": "Immunologic phenomena (e.g., Roth spots)",
    "option_d": "Vascular phenomena (e.g., Janeway lesions)",
    "correct_answer": "B",
    "explanation": "The two major criteria are persistent positive blood cultures and evidence of endocardial involvement (e.g., vegetation on echo)."
  },
  {
    "question": "What is the primary reservoir for Salmonella Typhi?",
    "option_a": "Poultry and eggs",
    "option_b": "Humans",
    "option_c": "Reptiles",
    "option_d": "Cattle",
    "correct_answer": "B",
    "explanation": "Salmonella Typhi (causing typhoid fever) is strictly human-adapted; it is transmitted via the fecal-oral route from cases or chronic carriers."
  },
  {
    "question": "A patient with suspected primary Tuberculosis has a chest X-ray showing a calcified lung nodule and a calcified hilar lymph node. This is known as:",
    "option_a": "Ghon complex",
    "option_b": "Ranke complex",
    "option_c": "Ghon focus",
    "option_d": "Miliary TB",
    "correct_answer": "B",
    "explanation": "A Ghon focus is the initial lesion; a Ghon complex includes the focus + lymph node. When these calcify, they are called a Ranke complex."
  },
  {
    "question": "Which antibiotic class is associated with the side effect of 'Gray Baby Syndrome' in neonates?",
    "option_a": "Aminoglycosides",
    "option_b": "Chloramphenicol",
    "option_c": "Tetracyclines",
    "option_d": "Macrolides",
    "correct_answer": "B",
    "explanation": "Neonates lack the enzyme (UDP-glucuronyltransferase) to metabolize chloramphenicol, leading to toxic accumulation and circulatory collapse."
  },
  {
    "question": "A patient presents with a 'bull's-eye' rash (Erythema Migrans) after a tick bite in a wooded area. What is the causative agent?",
    "option_a": "Rickettsia rickettsii",
    "option_b": "Borrelia burgdorferi",
    "option_c": "Ehrlichia chaffeensis",
    "option_d": "Francisella tularensis",
    "correct_answer": "B",
    "explanation": "Lyme disease is caused by the spirochete Borrelia burgdorferi, transmitted by Ixodes ticks."
  },
  {
    "question": "Which of the following is true regarding 'Empiric Therapy'?",
    "option_a": "It is based on the definitive identification of the pathogen",
    "option_b": "It is based on the most likely pathogens given the clinical scenario before culture results are available",
    "option_c": "It always uses a single narrow-spectrum antibiotic",
    "option_d": "It is only used for viral infections",
    "correct_answer": "B",
    "explanation": "Empiric therapy is 'best guess' treatment started immediately while waiting for diagnostic confirmation."
  },
  {
    "question": "Which organism is the most common cause of Community-Acquired Pneumonia (CAP)?",
    "option_a": "Mycoplasma pneumoniae",
    "option_b": "Streptococcus pneumoniae",
    "option_c": "Haemophilus influenzae",
    "option_d": "Legionella pneumophila",
    "correct_answer": "B",
    "explanation": "S. pneumoniae (Pneumococcus) remains the leading cause of CAP worldwide."
  },
  {
    "question": "A patient presents with 'lockjaw' (trismus) and generalized muscle spasms after a puncture wound from a rusty nail. What is the mechanism of the toxin involved?",
    "option_a": "Inhibition of Acetylcholine release",
    "option_b": "Inhibition of inhibitory neurotransmitters (GABA and Glycine)",
    "option_c": "Activation of the parasympathetic nervous system",
    "option_d": "Destruction of motor neurons",
    "correct_answer": "B",
    "explanation": "Tetanospasmin, produced by Clostridium tetani, prevents the release of inhibitory signals, leading to over-excitation of muscles."
  },
  {
    "question": "Which of the following is a classic clinical finding in 'Secondary Syphilis'?",
    "option_a": "Tabes dorsalis",
    "option_b": "A maculopapular rash on the palms and soles",
    "option_c": "Gummas (painless granulomas)",
    "option_d": "Aortitis",
    "correct_answer": "B",
    "explanation": "Secondary syphilis occurs weeks to months after the chancre heals and is characterized by a generalized rash, lymphadenopathy, and condyloma lata."
  },
  {
    "question": "What is the drug of choice for treating 'Listeriosis' in an elderly or immunocompromised patient?",
    "option_a": "Ceftriaxone",
    "option_b": "Ampicillin",
    "option_c": "Vancomycin",
    "option_d": "Ciprofloxacin",
    "correct_answer": "B",
    "explanation": "Listeria monocytogenes is naturally resistant to cephalosporins; Ampicillin (often with Gentamicin) is the standard treatment."
  },
  {
    "question": "A 20-year-old student presents with sudden onset of fever, headache, and a petechial rash. CSF Gram stain shows Gram-negative diplococci. Diagnosis?",
    "option_a": "Haemophilus influenzae meningitis",
    "option_b": "Neisseria meningitidis meningitis",
    "option_c": "Streptococcus pneumoniae meningitis",
    "option_d": "Listeria meningitis",
    "correct_answer": "B",
    "explanation": "Meningococcal meningitis is known for its rapid progression and the characteristic non-blanching petechial or purpural rash."
  },
  {
    "question": "Which of the following describes the mechanism of action of 'Aminoglycosides'?",
    "option_a": "Inhibition of cell wall synthesis",
    "option_b": "Inhibition of the 30S ribosomal subunit causing misreading of mRNA",
    "option_c": "Inhibition of the 50S ribosomal subunit",
    "option_d": "Disruption of the cell membrane",
    "correct_answer": "B",
    "explanation": "Aminoglycosides (e.g., Gentamicin) target the 30S subunit and are bactericidal."
  },
  {
    "question": "A patient with a positive Tuberculin Skin Test (TST) but a normal chest X-ray and no symptoms has:",
    "option_a": "Active Tuberculosis",
    "option_b": "Latent Tuberculosis Infection (LTBI)",
    "option_c": "Natural immunity only",
    "option_d": "Extrapulmonary TB",
    "correct_answer": "B",
    "explanation": "LTBI means the patient is infected with M. tuberculosis but the immune system is containing it; they are not contagious."
  },
  {
    "question": "Which antibiotic is most specifically associated with the risk of 'Tendon Rupture', especially in the elderly?",
    "option_a": "Macrolides",
    "option_b": "Fluoroquinolones (e.g., Ciprofloxacin)",
    "option_c": "Tetracyclines",
    "option_d": "Sulfonamides",
    "correct_answer": "B",
    "explanation": "Fluoroquinolones carry a black box warning for tendinitis and tendon rupture."
  },
  {
    "question": "What is the characteristic 'Toxidrome' of Botulism?",
    "option_a": "Spastic paralysis and fever",
    "option_b": "Descending symmetric flaccid paralysis",
    "option_c": "Ascending symmetric flaccid paralysis",
    "option_d": "High fever and jaundice",
    "correct_answer": "B",
    "explanation": "Botulinum toxin prevents ACh release at the neuromuscular junction, starting with the cranial nerves (diplopia, dysphagia)."
  },
  {
    "question": "Which organism is the leading cause of 'Prosthetic Valve Endocarditis' occurring within the first year of surgery?",
    "option_a": "Streptococcus viridans",
    "option_b": "Staphylococcus epidermidis",
    "option_c": "Staphylococcus aureus",
    "option_d": "Enterococcus faecalis",
    "correct_answer": "B",
    "explanation": "Coagulase-negative staphylococci (like S. epidermidis) form biofilms on prosthetic material and are the most common early-onset cause."
  },
  {
    "question": "A patient develops a high fever, cough, and confusion after staying at a hotel with a large fountain. Sputum Gram stain shows few neutrophils and no organisms. Hyponatremia is present. Diagnosis?",
    "option_a": "Pneumococcal pneumonia",
    "option_b": "Legionnaires' Disease",
    "option_c": "Mycoplasma pneumonia",
    "option_d": "Viral influenza",
    "correct_answer": "B",
    "explanation": "Legionella is associated with contaminated water systems. It causes atypical pneumonia with GI symptoms, confusion, and hyponatremia."
  },
  {
    "question": "Which of the following is true for 'Gram-negative' bacteria?",
    "option_a": "They have a thick layer of peptidoglycan",
    "option_b": "They have an outer membrane containing Lipopolysaccharide (LPS/Endotoxin)",
    "option_c": "They stain purple with Gram stain",
    "option_d": "They lack a periplasmic space",
    "correct_answer": "B",
    "explanation": "The outer membrane and LPS are unique to Gram-negatives, contributing to their pathogenicity and resistance."
  },
  {
    "question": "What is the first-line antibiotic for 'Uncomplicated Urinary Tract Infection' (Cystitis) in a non-pregnant woman?",
    "option_a": "Ciprofloxacin",
    "option_b": "Nitrofurantoin or TMP-SMX",
    "option_c": "Ceftriaxone",
    "option_d": "Doxycycline",
    "correct_answer": "B",
    "explanation": "Nitrofurantoin and TMP-SMX are preferred to minimize resistance, reserving fluoroquinolones for more severe infections."
  },
  {
    "question": "A patient with advanced HIV (CD4 < 50) presents with fever, weight loss, and anemia. Blood cultures show acid-fast bacilli. Most likely diagnosis?",
    "option_a": "Miliary TB",
    "option_b": "Mycobacterium avium complex (MAC)",
    "option_c": "Leprosy",
    "option_d": "Nocardiosis",
    "correct_answer": "B",
    "explanation": "MAC is a common opportunistic infection in very low CD4 counts, presenting with disseminated disease."
  },
  {
    "question": "Which bacterial infection is characterized by 'Whooping' cough and post-tussive emesis?",
    "option_a": "Corynebacterium diphtheriae",
    "option_b": "Bordetella pertussis",
    "option_c": "Haemophilus influenzae",
    "option_d": "Klebsiella pneumoniae",
    "correct_answer": "B",
    "explanation": "Pertussis involves paroxysmal coughing fits ending with an inspiratory whoop."
  },
  {
    "question": "What is the standard treatment duration for latent TB with Isoniazid (INH)?",
    "option_a": "2 weeks",
    "option_b": "9 months",
    "option_c": "2 years",
    "option_d": "5 days",
    "correct_answer": "B",
    "explanation": "A 6-9 month course of INH is the traditional regimen for LTBI."
  },
  {
    "question": "Which of the following is a symptom of 'Diphtheria' caused by Corynebacterium diphtheriae?",
    "option_a": "Diffuse maculopapular rash",
    "option_b": "A gray, leathery pseudomembrane on the pharynx",
    "option_c": "Bloody diarrhea",
    "option_d": "Polyarthritis",
    "correct_answer": "B",
    "explanation": "The toxin causes tissue necrosis and the formation of a membrane that can obstruct the airway."
  },
  {
    "question": "Which antibiotic is the drug of choice for 'Methicillin-Resistant Staphylococcus aureus' (MRSA) infections?",
    "option_a": "Oxacillin",
    "option_b": "Vancomycin",
    "option_c": "Cefazolin",
    "option_d": "Azithromycin",
    "correct_answer": "B",
    "explanation": "Vancomycin is a glycopeptide used for serious Gram-positive infections resistant to beta-lactams."
  },
  {
    "question": "A 10-year-old presents with a 'honey-colored' crusted rash on the face. Diagnosis?",
    "option_a": "Cellulitis",
    "option_b": "Impetigo",
    "option_c": "Erysipelas",
    "option_d": "Folliculitis",
    "correct_answer": "B",
    "explanation": "Impetigo is a superficial skin infection most commonly caused by S. aureus or S. pyogenes."
  },
  {
    "question": "Which of the following is true for 'Bactericidal' antibiotics?",
    "option_a": "They only inhibit the growth of bacteria",
    "option_b": "They directly kill the bacteria",
    "option_c": "They rely heavily on the host immune system to clear the infection",
    "option_d": "They are only effective against viruses",
    "correct_answer": "B",
    "explanation": "Bactericidal agents are preferred in life-threatening infections or immunocompromised patients."
  },
  {
    "question": "Which organism is most commonly responsible for 'Erysipelas' (bright red, well-demarcated skin infection)?",
    "option_a": "Staphylococcus aureus",
    "option_b": "Streptococcus pyogenes (Group A Strep)",
    "option_c": "Pseudomonas aeruginosa",
    "option_d": "Bacteroides fragilis",
    "correct_answer": "B",
    "explanation": "Erysipelas is a more superficial form of cellulitis with lymphatic involvement, classically caused by Group A Strep."
  },
  {
    "question": "Which antibiotic class works by inhibiting folate synthesis?",
    "option_a": "Fluoroquinolones",
    "option_b": "Sulfonamides and Trimethoprim",
    "option_c": "Aminoglycosides",
    "option_d": "Penicillins",
    "correct_answer": "B",
    "explanation": "They act sequentially to prevent the production of tetrahydrofolic acid, which is essential for DNA synthesis."
  },
  {
    "question": "A patient with untreated HIV presents with a high fever and a stiff neck. Cryptococcus neoformans is suspected. What is the classic initial test for the CSF?",
    "option_a": "Gram stain",
    "option_b": "India Ink stain",
    "option_c": "Acid-fast stain",
    "option_d": "Giemsa stain",
    "correct_answer": "B",
    "explanation": "India ink highlights the thick capsule of this yeast as a clear halo."
  },
  {
    "question": "What is the most common cause of 'Gas Gangrene'?",
    "option_a": "Staphylococcus aureus",
    "option_b": "Clostridium perfringens",
    "option_c": "Streptococcus pyogenes",
    "option_d": "Bacillus anthracis",
    "correct_answer": "B",
    "explanation": "C. perfringens produces alpha-toxin, causing tissue necrosis and gas production in muscle (myonecrosis)."
  },
  {
    "question": "Which of the following is the 'Jarisch-Herxheimer' reaction?",
    "option_a": "An allergic reaction to penicillin",
    "option_b": "An acute febrile response due to the rapid death of spirochetes (e.g., in Syphilis) after antibiotic treatment",
    "option_c": "A type of antibiotic-associated diarrhea",
    "option_d": "A chronic liver disease",
    "correct_answer": "B",
    "explanation": "The release of toxins from dying bacteria (usually Treponema) causes systemic symptoms shortly after starting treatment."
  },
  {
    "question": "A child presents with a 'sandpaper' rash, sore throat, and a 'strawberry' tongue. Diagnosis?",
    "option_a": "Kawasaki Disease",
    "option_b": "Scarlet Fever",
    "option_c": "Measles",
    "option_d": "Rubella",
    "correct_answer": "B",
    "explanation": "Scarlet fever is caused by erythrogenic toxins from S. pyogenes."
  },
  {
    "question": "Which of the following is a classic clinical finding in 'Rheumatic Fever'?",
    "option_a": "Joint space narrowing on X-ray",
    "option_b": "Migratory polyarthritis, Carditis, and Erythema marginatum",
    "option_c": "Chronic kidney failure",
    "option_d": "Hyperthyroidism",
    "correct_answer": "B",
    "explanation": "The Jones Criteria define the diagnosis after a Group A Strep pharyngitis."
  },
  {
    "question": "What is the drug of choice for 'Rocky Mountain Spotted Fever'?",
    "option_a": "Ciprofloxacin",
    "option_b": "Doxycycline",
    "option_c": "Penicillin V",
    "option_d": "Vancomycin",
    "correct_answer": "B",
    "explanation": "Doxycycline is effective against Rickettsia and is the first-line treatment for both adults and children."
  },
  {
    "question": "Which organism is the most common cause of 'Osteomyelitis' overall?",
    "option_a": "Salmonella",
    "option_b": "Staphylococcus aureus",
    "option_c": "Pseudomonas",
    "option_d": "Neisseria",
    "correct_answer": "B",
    "explanation": "S. aureus is the most common cause across almost all age groups and risk categories."
  },
  {
    "question": "A patient with Sickle Cell Disease is specifically prone to 'Osteomyelitis' caused by which organism?",
    "option_a": "S. aureus",
    "option_b": "Salmonella species",
    "option_c": "S. pyogenes",
    "option_d": "E. coli",
    "correct_answer": "B",
    "explanation": "While S. aureus is still common, the association with Salmonella is unique to Sickle Cell patients."
  },
  {
    "question": "What is the primary mechanism of action of 'Macrolides' (e.g., Erythromycin, Azithromycin)?",
    "option_a": "Inhibition of the 30S ribosomal subunit",
    "option_b": "Inhibition of the 50S ribosomal subunit (blocks translocation)",
    "option_c": "Disruption of cell wall synthesis",
    "option_d": "Inhibition of RNA polymerase",
    "correct_answer": "B",
    "explanation": "Macrolides prevent bacterial protein synthesis by targeting the 50S subunit."
  },
  {
    "question": "Which of the following is true for 'Anaerobic' bacteria?",
    "option_a": "They require high oxygen levels for growth",
    "option_b": "They often cause foul-smelling infections and abscesses",
    "option_c": "They are easily treated with Aminoglycosides",
    "option_d": "They only infect the skin",
    "correct_answer": "B",
    "explanation": "Aminoglycosides are ineffective against anaerobes because they require oxygen for uptake into the cell."
  },
  {
    "question": "A patient with a positive PPD test has a chest X-ray showing upper lobe cavities. Diagnosis?",
    "option_a": "Primary TB",
    "option_b": "Reactivation (Post-primary) TB",
    "option_c": "Sarcoidosis",
    "option_d": "Latent TB",
    "correct_answer": "B",
    "explanation": "Cavitation in the upper lobes is a hallmark of active, secondary TB."
  },
  {
    "question": "Which antibiotic is notorious for causing 'Pseudomembranous Colitis'?",
    "option_a": "Clindamycin",
    "option_b": "Metronidazole",
    "option_c": "Linezolid",
    "option_d": "Doxycycline",
    "correct_answer": "A",
    "explanation": "While many antibiotics can cause CDI, Clindamycin is one of the highest-risk agents historically."
  },
  {
    "question": "What is the mechanism of 'Vancomycin Resistance' in VRSA?",
    "option_a": "Production of beta-lactamases",
    "option_b": "Alteration of the cell wall target from D-Ala-D-Ala to D-Ala-D-Lac",
    "option_c": "Efflux pumps",
    "option_d": "Mutations in RNA polymerase",
    "correct_answer": "B",
    "explanation": "By changing the binding site, the bacteria prevent the glycopeptide from attaching to the cell wall precursors."
  },
  {
    "question": "A patient with a history of IV drug use presents with fever and a new heart murmur. Triscuspid valve vegetation is seen. Diagnosis?",
    "option_a": "Left-sided endocarditis",
    "option_b": "Right-sided endocarditis",
    "option_c": "Myocarditis",
    "option_d": "Pericarditis",
    "correct_answer": "B",
    "explanation": "IV drug users are prone to right-sided endocarditis, often involving S. aureus."
  },
  {
    "question": "Which antibiotic is a first-line agent for the treatment of 'Lyme Disease' in a pregnant woman?",
    "option_a": "Doxycycline",
    "option_b": "Amoxicillin",
    "option_c": "Ciprofloxacin",
    "option_d": "Gentamicin",
    "correct_answer": "B",
    "explanation": "Tetracyclines are generally avoided in pregnancy due to risks to fetal bone and teeth; Amoxicillin is a safe and effective alternative."
  }
]

COURSE_ID = "NVU_MD_Y3_S2_C32"

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
