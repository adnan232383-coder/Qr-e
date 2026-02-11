"""
Generate all 8 course module videos with diverse styles
Style rotation every 2 modules
"""

import os
import time
import json
import requests
from datetime import datetime

HEYGEN_API_KEY = "sk_V2_hgu_kXVuWJrQn74_2eBCQ3FvLT6LggmUwyoJOes2woHS61dM"
BASE_URL = "https://api.heygen.com"
OUTPUT_DIR = "/app/frontend/public/videos/diverse"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "X-Api-Key": HEYGEN_API_KEY
}

# Style configurations for each pair of modules
STYLE_CONFIGS = [
    # Modules 1-2: Adriana Nurse + Dark background
    {
        "avatar_id": "Adriana_Nurse_Front_public",
        "avatar_name": "Adriana Nurse",
        "voice_id": "42d00d4aac5441279d8536cd6b52c53c",  # Hope
        "voice_name": "Hope",
        "background": {"type": "color", "value": "#1a1a2e"},
        "style_name": "Medical Dark"
    },
    # Modules 3-4: Abigail Office + Light background
    {
        "avatar_id": "Abigail_standing_office_front",
        "avatar_name": "Abigail Office",
        "voice_id": "cef3bc4e0a84424cafcde6f2cf466c97",  # Ivy
        "voice_name": "Ivy",
        "background": {"type": "color", "value": "#f5f5f5"},
        "style_name": "Office Light"
    },
    # Modules 5-6: Adrian Male + Studio background
    {
        "avatar_id": "Adrian_public_2_20240312",
        "avatar_name": "Adrian Blue Suit",
        "voice_id": "6be73833ef9a4eb0aeee399b8fe9d62b",  # Andrew
        "voice_name": "Andrew",
        "background": {"type": "color", "value": "#263238"},
        "style_name": "Studio Dark"
    },
    # Modules 7-8: Adriana Business + Modern background
    {
        "avatar_id": "Adriana_Business_Front_public",
        "avatar_name": "Adriana Business",
        "voice_id": "42d00d4aac5441279d8536cd6b52c53c",  # Hope
        "voice_name": "Hope",
        "background": {"type": "color", "value": "#1e3a5f"},
        "style_name": "Business Modern"
    }
]

# Module scripts (educational content in English)
MODULE_SCRIPTS = [
    {
        "module_id": "module1",
        "title": "Introduction to Cell Biology",
        "script": """Welcome to Module 1: Introduction to Cell Biology. 
In this lecture, we will explore the fundamental concepts of cell theory and the basic organization of cells. 
Cells are the basic building blocks of all living organisms. There are two main types: prokaryotic cells, found in bacteria, and eukaryotic cells, found in plants and animals. 
Understanding cell biology is essential for your medical studies. Let's begin this fascinating journey into the microscopic world of life."""
    },
    {
        "module_id": "module2", 
        "title": "Cell Membrane and Transport",
        "script": """Welcome to Module 2: Cell Membrane and Transport.
Today we will discuss the structure of the plasma membrane and how substances move in and out of cells.
The cell membrane is made of a phospholipid bilayer with embedded proteins. It controls what enters and exits the cell through passive transport like diffusion, and active transport which requires energy.
Understanding membrane transport is crucial for understanding how drugs and nutrients enter cells."""
    },
    {
        "module_id": "module3",
        "title": "Cellular Organelles",
        "script": """Welcome to Module 3: Cellular Organelles.
In this module, we will examine the structure and function of major cellular organelles.
The nucleus contains our DNA and controls cell activities. Mitochondria are the powerhouses producing ATP. The endoplasmic reticulum synthesizes proteins and lipids, while the Golgi apparatus packages and ships cellular products.
Each organelle plays a vital role in maintaining cell function and health."""
    },
    {
        "module_id": "module4",
        "title": "Cellular Respiration and ATP",
        "script": """Welcome to Module 4: Cellular Respiration and ATP Production.
Today we explore how cells convert nutrients into usable energy in the form of ATP.
Cellular respiration occurs in three stages: glycolysis in the cytoplasm, the Krebs cycle, and the electron transport chain in mitochondria.
This process is fundamental to understanding metabolism and how our bodies generate the energy needed for all life processes."""
    },
    {
        "module_id": "module5",
        "title": "Cell Cycle and Division",
        "script": """Welcome to Module 5: The Cell Cycle and Cell Division.
In this lecture, we examine how cells grow and divide through the cell cycle.
The cell cycle includes interphase, where cells grow and replicate DNA, and mitosis, where cells divide into two identical daughter cells.
Understanding cell division is critical for comprehending both normal development and diseases like cancer where this process goes wrong."""
    },
    {
        "module_id": "module6",
        "title": "DNA Structure and Replication",
        "script": """Welcome to Module 6: DNA Structure and Replication.
Today we will study the molecular structure of DNA and how it copies itself.
DNA is a double helix made of nucleotides containing bases adenine, thymine, guanine, and cytosine. During replication, the DNA unwinds at the replication fork and DNA polymerase builds new strands.
This process ensures genetic information is passed accurately to new cells."""
    },
    {
        "module_id": "module7",
        "title": "Gene Expression: Transcription and Translation",
        "script": """Welcome to Module 7: Gene Expression.
In this module, we explore how genetic information flows from DNA to protein.
Transcription copies DNA into messenger RNA in the nucleus. Translation then uses ribosomes to read the mRNA and build proteins using the genetic code.
This central dogma of molecular biology explains how our genes determine our traits and how our cells function."""
    },
    {
        "module_id": "module8",
        "title": "Basic Genetics and Inheritance",
        "script": """Welcome to Module 8: Basic Genetics and Inheritance.
Our final module covers Mendelian genetics and patterns of inheritance.
Gregor Mendel discovered that traits are passed through genes with dominant and recessive alleles. We use Punnett squares to predict inheritance patterns.
Understanding genetics helps us comprehend hereditary diseases and forms the foundation for modern medical genetics."""
    }
]

def get_style_for_module(module_index):
    """Get style config based on module index (0-7)"""
    style_index = module_index // 2  # Changes every 2 modules
    return STYLE_CONFIGS[style_index]

def generate_video(module_data, style_config):
    """Generate a video for a module with specified style"""
    payload = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": style_config["avatar_id"],
                    "avatar_style": "normal"
                },
                "voice": {
                    "type": "text",
                    "input_text": module_data["script"],
                    "voice_id": style_config["voice_id"],
                    "speed": 1.0
                },
                "background": style_config["background"]
            }
        ],
        "dimension": {"width": 1920, "height": 1080},
        "test": False
    }
    
    response = requests.post(
        f"{BASE_URL}/v2/video/generate",
        headers=HEADERS,
        json=payload
    )
    
    if response.status_code == 200:
        return response.json().get("data", {}).get("video_id")
    else:
        print(f"Error: {response.text}")
        return None

def check_video_status(video_id):
    """Check video generation status"""
    response = requests.get(
        f"{BASE_URL}/v1/video_status.get",
        headers=HEADERS,
        params={"video_id": video_id}
    )
    
    if response.status_code == 200:
        data = response.json().get("data", {})
        return {
            "status": data.get("status"),
            "video_url": data.get("video_url"),
            "duration": data.get("duration")
        }
    return {"status": "error"}

def download_video(video_url, output_path):
    """Download video to local path"""
    response = requests.get(video_url, stream=True)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    return False

def main():
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Track all video jobs
    jobs = []
    
    print("=" * 60)
    print("Starting video generation for all 8 modules")
    print("=" * 60)
    
    # Start all video generations
    for i, module in enumerate(MODULE_SCRIPTS):
        style = get_style_for_module(i)
        print(f"\n[{i+1}/8] Generating: {module['title']}")
        print(f"  Style: {style['style_name']} | Avatar: {style['avatar_name']} | Voice: {style['voice_name']}")
        
        video_id = generate_video(module, style)
        
        if video_id:
            jobs.append({
                "module_id": module["module_id"],
                "title": module["title"],
                "video_id": video_id,
                "style": style["style_name"],
                "status": "pending",
                "output_file": f"{module['module_id']}_diverse.mp4"
            })
            print(f"  ✓ Video ID: {video_id}")
        else:
            print(f"  ✗ Failed to start generation")
        
        # Small delay to avoid rate limiting
        time.sleep(2)
    
    # Save jobs to file for tracking
    jobs_file = f"{OUTPUT_DIR}/generation_jobs.json"
    with open(jobs_file, 'w') as f:
        json.dump(jobs, f, indent=2)
    print(f"\nJobs saved to: {jobs_file}")
    
    # Monitor and download completed videos
    print("\n" + "=" * 60)
    print("Monitoring video generation progress...")
    print("=" * 60)
    
    completed = 0
    max_wait = 1800  # 30 minutes max
    start_time = time.time()
    
    while completed < len(jobs) and (time.time() - start_time) < max_wait:
        for job in jobs:
            if job["status"] == "completed":
                continue
            
            status = check_video_status(job["video_id"])
            
            if status["status"] == "completed":
                print(f"\n✓ {job['title']} - COMPLETED")
                
                # Download video
                output_path = f"{OUTPUT_DIR}/{job['output_file']}"
                if download_video(status["video_url"], output_path):
                    job["status"] = "completed"
                    job["duration"] = status["duration"]
                    job["local_path"] = output_path
                    completed += 1
                    print(f"  Downloaded to: {output_path}")
                else:
                    job["status"] = "download_failed"
                    print(f"  Download failed!")
                    
            elif status["status"] == "failed":
                job["status"] = "failed"
                completed += 1
                print(f"\n✗ {job['title']} - FAILED")
        
        # Save progress
        with open(jobs_file, 'w') as f:
            json.dump(jobs, f, indent=2)
        
        pending = len([j for j in jobs if j["status"] == "pending"])
        if pending > 0:
            print(f"\rPending: {pending} | Completed: {completed}/{len(jobs)} | Elapsed: {int(time.time() - start_time)}s", end="", flush=True)
            time.sleep(15)
    
    # Final summary
    print("\n\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)
    
    for job in jobs:
        status_icon = "✓" if job["status"] == "completed" else "✗"
        print(f"{status_icon} {job['title']} [{job['style']}] - {job['status']}")
    
    # Save final results
    with open(jobs_file, 'w') as f:
        json.dump(jobs, f, indent=2)
    
    return jobs

if __name__ == "__main__":
    main()
