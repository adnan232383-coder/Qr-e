import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

questions_data = [
  {
    "question": "Which antibiotic class inhibits bacterial cell wall synthesis by binding to penicillin-binding proteins (PBPs)?",
    "option_a": "Aminoglycosides",
    "option_b": "Beta-lactams",
    "option_c": "Fluoroquinolones",
    "option_d": "Macrolides",
    "correct_answer": "B",
    "explanation": "Beta-lactams (penicillins, cephalosporins, carbapenems) inhibit cell wall synthesis by binding to PBPs."
  },
  {
    "question": "Which organism is the most common cause of Uncomplicated Urinary Tract Infection (UTI)?",
    "option_a": "Escherichia coli",
    "option_b": "Pseudomonas aeruginosa",
    "option_c": "Staphylococcus aureus",
    "option_d": "Proteus mirabilis",
    "correct_answer": "A",
    "explanation": "E. coli is responsible for 80-90% of community-acquired uncomplicated UTIs."
  },
  {
    "question": "What is the primary mechanism of action of Vancomycin?",
    "option_a": "Inhibits protein synthesis at 30S subunit",
    "option_b": "Inhibits cell wall synthesis by binding D-Ala-D-Ala",
    "option_c": "Inhibits DNA gyrase",
    "option_d": "Damages cell membrane",
    "correct_answer": "B",
    "explanation": "Vancomycin binds to the D-Ala-D-Ala terminal of the peptidoglycan precursor, blocking cell wall cross-linking."
  },
  {
    "question": "A 24-year-old female presents with dysuria and frequency. Which drug is a first-line agent for uncomplicated cystitis?",
    "option_a": "Nitrofurantoin",
    "option_b": "Moxifloxacin",
    "option_c": "Vancomycin",
    "option_d": "Clindamycin",
    "correct_answer": "A",
    "explanation": "Nitrofurantoin (or TMP-SMX) is first-line for uncomplicated cystitis due to high urinary concentration."
  },
  {
    "question": "Which adverse effect is classically associated with Vancomycin infusion?",
    "option_a": "Red Man Syndrome",
    "option_b": "Tendinopathy",
    "option_c": "Gray Baby Syndrome",
    "option_d": "Discolored teeth",
    "correct_answer": "A",
    "explanation": "Red Man Syndrome is a histamine-mediated reaction to rapid Vancomycin infusion."
  },
  {
    "question": "Methicillin-Resistant Staphylococcus aureus (MRSA) is resistant to beta-lactams due to:",
    "option_a": "Production of Beta-lactamase",
    "option_b": "Alteration of PBP to PBP2a",
    "option_c": "Efflux pumps",
    "option_d": "Thickened cell wall",
    "correct_answer": "B",
    "explanation": "The mecA gene encodes PBP2a, which has low affinity for beta-lactams."
  },
  {
    "question": "Which antibiotic is active against Pseudomonas aeruginosa?",
    "option_a": "Ceftriaxone",
    "option_b": "Cefepime",
    "option_c": "Amoxicillin",
    "option_d": "Erythromycin",
    "correct_answer": "B",
    "explanation": "Cefepime (4th gen cephalosporin) has potent anti-pseudomonal activity."
  },
  {
    "question": "Which biochemical test differentiates Staphylococcus aureus (positive) from Coagulase-Negative Staphylococci (negative)?",
    "option_a": "Catalase test",
    "option_b": "Coagulase test",
    "option_c": "Oxidase test",
    "option_d": "Urease test",
    "correct_answer": "B",
    "explanation": "The coagulase test is the definitive test to identify S. aureus."
  },
  {
    "question": "Which antifungal agent targets Ergosterol synthesis?",
    "option_a": "Fluconazole",
    "option_b": "Caspofungin",
    "option_c": "Flucytosine",
    "option_d": "Amphotericin B",
    "correct_answer": "A",
    "explanation": "Azoles (Fluconazole) inhibit 14-alpha-demethylase, preventing ergosterol synthesis."
  },
  {
    "question": "Which drug is the treatment of choice for Syphilis (Treponema pallidum)?",
    "option_a": "Penicillin G",
    "option_b": "Ciprofloxacin",
    "option_c": "Gentamicin",
    "option_d": "Trimethoprim",
    "correct_answer": "A",
    "explanation": "Penicillin G is the gold standard for all stages of Syphilis."
  },
  {
    "question": "Aminoglycosides (e.g., Gentamicin) are known for which toxicities?",
    "option_a": "Nephrotoxicity and Ototoxicity",
    "option_b": "Hepatotoxicity",
    "option_c": "Pulmonary fibrosis",
    "option_d": "Bone marrow suppression",
    "correct_answer": "A",
    "explanation": "Aminoglycosides can cause kidney damage (ATN) and hearing loss/vestibular damage."
  },
  {
    "question": "Clostridium difficile infection is most commonly associated with prior use of:",
    "option_a": "Clindamycin",
    "option_b": "Gentamicin",
    "option_c": "Doxycycline",
    "option_d": "Metronidazole",
    "correct_answer": "A",
    "explanation": "Clindamycin (and fluoroquinolones/cephalosporins) suppresses gut flora, allowing C. diff overgrowth."
  },
  {
    "question": "Which bacteria is an acid-fast bacillus?",
    "option_a": "Mycobacterium tuberculosis",
    "option_b": "Staphylococcus epidermidis",
    "option_c": "E. coli",
    "option_d": "Streptococcus pneumoniae",
    "correct_answer": "A",
    "explanation": "Mycobacteria have mycolic acid in their cell walls, retaining the acid-fast stain."
  },
  {
    "question": "Metronidazole is effective against:",
    "option_a": "Aerobic Gram-negatives",
    "option_b": "Anaerobes and Protozoa",
    "option_c": "Fungi",
    "option_d": "Viruses",
    "correct_answer": "B",
    "explanation": "Metronidazole targets anaerobes (Bacteroides, Clostridium) and protozoa (Giardia, Trichomonas)."
  },
  {
    "question": "Tetracyclines should be avoided in children and pregnant women because:",
    "option_a": "They cause cartilage damage",
    "option_b": "They deposit in teeth and bones",
    "option_c": "They cause gray baby syndrome",
    "option_d": "They cause hemolysis",
    "correct_answer": "B",
    "explanation": "Tetracyclines chelate calcium and cause permanent tooth discoloration and bone growth inhibition."
  },
  {
    "question": "Which antibiotic inhibits DNA gyrase and Topoisomerase IV?",
    "option_a": "Ciprofloxacin (Fluoroquinolones)",
    "option_b": "Azithromycin (Macrolides)",
    "option_c": "Doxycycline (Tetracyclines)",
    "option_d": "Rifampin",
    "correct_answer": "A",
    "explanation": "Fluoroquinolones inhibit bacterial DNA replication by targeting DNA gyrase."
  },
  {
    "question": "Which organism causes 'Lyme Disease'?",
    "option_a": "Borrelia burgdorferi",
    "option_b": "Rickettsia rickettsii",
    "option_c": "Treponema pallidum",
    "option_d": "Leptospira interrogans",
    "correct_answer": "A",
    "explanation": "Borrelia burgdorferi, a spirochete transmitted by Ixodes ticks, causes Lyme disease."
  },
  {
    "question": "Which test is used to confirm the presence of Inducible Clindamycin Resistance in Staph aureus?",
    "option_a": "D-test",
    "option_b": "E-test",
    "option_c": "Catalase test",
    "option_d": "Coagulase test",
    "correct_answer": "A",
    "explanation": "The D-test detects inducible resistance to clindamycin in erythromycin-resistant strains."
  },
  {
    "question": "Which antiviral is a neuraminidase inhibitor used for Influenza?",
    "option_a": "Oseltamivir",
    "option_b": "Acyclovir",
    "option_c": "Ribavirin",
    "option_d": "Sofosbuvir",
    "correct_answer": "A",
    "explanation": "Oseltamivir (Tamiflu) inhibits viral neuraminidase, preventing release of new virions."
  },
  {
    "question": "Which of the following is a Carbapenem?",
    "option_a": "Meropenem",
    "option_b": "Ceftazidime",
    "option_c": "Piperacillin",
    "option_d": "Aztreonam",
    "correct_answer": "A",
    "explanation": "Meropenem, Imipenem, and Ertapenem are Carbapenems."
  },
  {
    "question": "Linezolid is active against which resistant pathogens?",
    "option_a": "MRSA and VRE",
    "option_b": "Pseudomonas and Acinetobacter",
    "option_c": "ESBL E. coli",
    "option_d": "Anaerobes only",
    "correct_answer": "A",
    "explanation": "Linezolid is an oxazolidinone used for resistant Gram-positives like MRSA and VRE."
  },
  {
    "question": "What is the vector for Plasmodium (Malaria)?",
    "option_a": "Anopheles mosquito",
    "option_b": "Aedes mosquito",
    "option_c": "Culex mosquito",
    "option_d": "Tick",
    "correct_answer": "A",
    "explanation": "Female Anopheles mosquitoes transmit the malaria parasite."
  },
  {
    "question": "Which antibiotic causes 'Gray Baby Syndrome' in neonates?",
    "option_a": "Chloramphenicol",
    "option_b": "Gentamicin",
    "option_c": "Sulfonamides",
    "option_d": "Tetracycline",
    "correct_answer": "A",
    "explanation": "Neonates lack the enzyme to metabolize Chloramphenicol, leading to toxicity."
  },
  {
    "question": "Macrolides (e.g., Erythromycin) bind to which ribosomal subunit?",
    "option_a": "50S",
    "option_b": "30S",
    "option_c": "40S",
    "option_d": "60S",
    "correct_answer": "A",
    "explanation": "Macrolides inhibit protein synthesis by binding to the 50S ribosomal subunit."
  },
  {
    "question": "Which bacterium is the most common cause of 'Traveler's Diarrhea'?",
    "option_a": "Enterotoxigenic E. coli (ETEC)",
    "option_b": "Shigella",
    "option_c": "Salmonella",
    "option_d": "Vibrio cholerae",
    "correct_answer": "A",
    "explanation": "ETEC is the leading cause of traveler's diarrhea."
  },
  {
    "question": "A patient with a Penicillin allergy (anaphylaxis) requires treatment for Syphilis. What is the alternative?",
    "option_a": "Doxycycline",
    "option_b": "Amoxicillin",
    "option_c": "Cephalexin",
    "option_d": "Meropenem",
    "correct_answer": "A",
    "explanation": "Doxycycline is the preferred alternative for Syphilis in penicillin-allergic patients."
  },
  {
    "question": "Which drug interaction is a major concern with Warfarin and Ciprofloxacin?",
    "option_a": "Increased INR (Bleeding)",
    "option_b": "Decreased INR (Clotting)",
    "option_c": "Hyperkalemia",
    "option_d": "Seizures",
    "correct_answer": "A",
    "explanation": "Ciprofloxacin inhibits CYP enzymes and kills gut flora, significantly increasing Warfarin effect (INR)."
  },
  {
    "question": "Which organism causes 'Whooping Cough'?",
    "option_a": "Bordetella pertussis",
    "option_b": "Haemophilus influenzae",
    "option_c": "Legionella pneumophila",
    "option_d": "Streptococcus pneumoniae",
    "correct_answer": "A",
    "explanation": "Bordetella pertussis is the causative agent of Pertussis."
  },
  {
    "question": "Amphotericin B is known for which dose-limiting toxicity?",
    "option_a": "Nephrotoxicity",
    "option_b": "Hepatotoxicity",
    "option_c": "Ototoxicity",
    "option_d": "Cardiotoxicity",
    "correct_answer": "A",
    "explanation": "Amphotericin B causes renal vasoconstriction and tubular damage (Nephrotoxicity)."
  },
  {
    "question": "Which Hepatitis virus is a DNA virus?",
    "option_a": "Hepatitis B",
    "option_b": "Hepatitis A",
    "option_c": "Hepatitis C",
    "option_d": "Hepatitis E",
    "correct_answer": "A",
    "explanation": "HBV is a DNA virus; HAV, HCV, HDV, HEV are RNA viruses."
  },
  {
    "question": "Which Gram-positive rod causes Anthrax?",
    "option_a": "Bacillus anthracis",
    "option_b": "Clostridium tetani",
    "option_c": "Listeria monocytogenes",
    "option_d": "Corynebacterium diphtheriae",
    "correct_answer": "A",
    "explanation": "Bacillus anthracis is the spore-forming rod that causes Anthrax."
  },
  {
    "question": "Trimethoprim inhibits which enzyme in the folate pathway?",
    "option_a": "Dihydrofolate reductase (DHFR)",
    "option_b": "Dihydropteroate synthase",
    "option_c": "DNA gyrase",
    "option_d": "Beta-lactamase",
    "correct_answer": "A",
    "explanation": "Trimethoprim inhibits DHFR, preventing folate reduction."
  },
  {
    "question": "Which antibiotic is inactivated by lung surfactant (cannot use for pneumonia)?",
    "option_a": "Daptomycin",
    "option_b": "Vancomycin",
    "option_c": "Linezolid",
    "option_d": "Levofloxacin",
    "correct_answer": "A",
    "explanation": "Daptomycin binds to pulmonary surfactant, making it ineffective for lung infections."
  },
  {
    "question": "Which class of drugs covers 'Atypical' bacteria (Legionella, Mycoplasma, Chlamydia)?",
    "option_a": "Macrolides and Fluoroquinolones",
    "option_b": "Beta-lactams",
    "option_c": "Aminoglycosides",
    "option_d": "Glycopeptides",
    "correct_answer": "A",
    "explanation": "Atypicals lack a cell wall or are intracellular; Macrolides/Quinolones are effective."
  },
  {
    "question": "Extended-Spectrum Beta-Lactamases (ESBLs) are typically treated with:",
    "option_a": "Carbapenems",
    "option_b": "Cephalosporins",
    "option_c": "Penicillin",
    "option_d": "Azithromycin",
    "correct_answer": "A",
    "explanation": "Carbapenems are the drug of choice for serious ESBL infections."
  },
  {
    "question": "Which worm infection is diagnosed by the 'Scotch tape test'?",
    "option_a": "Enterobius vermicularis (Pinworm)",
    "option_b": "Ascaris lumbricoides",
    "option_c": "Taenia solium",
    "option_d": "Hookworm",
    "correct_answer": "A",
    "explanation": "Pinworm eggs are collected from the perianal area using tape."
  },
  {
    "question": "Which bacteria appears as 'Gram-negative diplococci'?",
    "option_a": "Neisseria meningitidis",
    "option_b": "Streptococcus pneumoniae",
    "option_c": "E. coli",
    "option_d": "Staphylococcus aureus",
    "correct_answer": "A",
    "explanation": "Neisseria species are characteristic Gram-negative diplococci."
  },
  {
    "question": "Which drug is used for prophylaxis of close contacts of Meningococcal Meningitis?",
    "option_a": "Rifampin",
    "option_b": "Amoxicillin",
    "option_c": "Gentamicin",
    "option_d": "Clindamycin",
    "correct_answer": "A",
    "explanation": "Rifampin (or Ciprofloxacin/Ceftriaxone) clears nasopharyngeal carriage."
  },
  {
    "question": "What is the mechanism of resistance in Vancomycin-Resistant Enterococcus (VRE)?",
    "option_a": "D-Ala-D-Ala changed to D-Ala-D-Lac",
    "option_b": "Beta-lactamase production",
    "option_c": "Porin loss",
    "option_d": "Ribosomal methylation",
    "correct_answer": "A",
    "explanation": "Alteration of the target site from D-Ala-D-Ala to D-Ala-D-Lac prevents Vancomycin binding."
  },
  {
    "question": "Fidaxomicin is primarily used to treat:",
    "option_a": "Clostridium difficile infection",
    "option_b": "MRSA pneumonia",
    "option_c": "VRE bacteremia",
    "option_d": "Pseudomonas UTI",
    "correct_answer": "A",
    "explanation": "Fidaxomicin is a macrocyclic antibiotic with a narrow spectrum for C. diff."
  },
  {
    "question": "Which antibiotic can cause tendon rupture (black box warning)?",
    "option_a": "Ciprofloxacin",
    "option_b": "Amoxicillin",
    "option_c": "Doxycycline",
    "option_d": "Azithromycin",
    "correct_answer": "A",
    "explanation": "Fluoroquinolones carry a risk of tendonitis and tendon rupture."
  },
  {
    "question": "Which organism is associated with 'Hot Tub Folliculitis'?",
    "option_a": "Pseudomonas aeruginosa",
    "option_b": "Staphylococcus aureus",
    "option_c": "Streptococcus pyogenes",
    "option_d": "E. coli",
    "correct_answer": "A",
    "explanation": "Pseudomonas survives in hot water and causes skin infections."
  },
  {
    "question": "Which antifungal is an Echinocandin (inhibits glucan synthase)?",
    "option_a": "Caspofungin",
    "option_b": "Fluconazole",
    "option_c": "Amphotericin B",
    "option_d": "Flucytosine",
    "correct_answer": "A",
    "explanation": "Caspofungin inhibits the synthesis of beta-(1,3)-D-glucan in the fungal cell wall."
  },
  {
    "question": "Which organism causes 'Gas Gangrene'?",
    "option_a": "Clostridium perfringens",
    "option_b": "Staphylococcus aureus",
    "option_c": "Pseudomonas aeruginosa",
    "option_d": "Bacteroides fragilis",
    "correct_answer": "A",
    "explanation": "C. perfringens produces toxins that cause myonecrosis and gas production."
  },
  {
    "question": "Aztreonam is a Monobactam active primarily against:",
    "option_a": "Gram-negative aerobes",
    "option_b": "Gram-positives",
    "option_c": "Anaerobes",
    "option_d": "Fungi",
    "correct_answer": "A",
    "explanation": "Aztreonam has activity only against Gram-negative aerobic bacteria."
  },
  {
    "question": "Which drug is effective for Methicillin-Sensitive Staph Aureus (MSSA) but not MRSA?",
    "option_a": "Nafcillin",
    "option_b": "Vancomycin",
    "option_c": "Linezolid",
    "option_d": "Daptomycin",
    "correct_answer": "A",
    "explanation": "Nafcillin/Oxacillin are anti-staphylococcal penicillins active against MSSA."
  },
  {
    "question": "Which parasite causes Chagas Disease?",
    "option_a": "Trypanosoma cruzi",
    "option_b": "Trypanosoma brucei",
    "option_c": "Leishmania donovani",
    "option_d": "Plasmodium falciparum",
    "correct_answer": "A",
    "explanation": "Trypanosoma cruzi causes American Trypanosomiasis (Chagas)."
  },
  {
    "question": "Which antibiotic is associated with 'Red-Orange' discoloration of tears and urine?",
    "option_a": "Rifampin",
    "option_b": "Isoniazid",
    "option_c": "Ethambutol",
    "option_d": "Pyrazinamide",
    "correct_answer": "A",
    "explanation": "Rifampin is a dye-like drug that colors body fluids red-orange."
  },
  {
    "question": "Helicobacter pylori treatment typically involves:",
    "option_a": "PPI + Clarithromycin + Amoxicillin",
    "option_b": "Vancomycin alone",
    "option_c": "Ciprofloxacin alone",
    "option_d": "Doxycycline alone",
    "correct_answer": "A",
    "explanation": "Triple therapy (PPI + 2 antibiotics) is standard for H. pylori eradication."
  },
  {
    "question": "Which class of antibiotics works by inhibiting protein synthesis at the 30S subunit?",
    "option_a": "Tetracyclines",
    "option_b": "Macrolides",
    "option_c": "Cephalosporins",
    "option_d": "Fluoroquinolones",
    "correct_answer": "A",
    "explanation": "Tetracyclines (and Aminoglycosides) target the 30S ribosomal subunit."
  }
]

COURSE_ID = "UG_PHARM_Y3_S2_C07"

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
