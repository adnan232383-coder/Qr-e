#!/usr/bin/env python3
"""
Script to wait for HeyGen videos and download them
Run in background: python3 wait_and_download_videos.py &
"""

import requests
import os
import time
import sys

HEYGEN_API_KEY = "sk_V2_hgu_kXVuWJrQn74_2eBCQ3FvLT6LggmUwyoJOes2woHS61dM"

VIDEO_IDS = {
    "UG_DENT_Y3_S1_C03_M01": "50648114d488404d820acb3c7ad7f0b3",  # Endodontics
    "UG_DENT_Y1_S1_C01_M01": "82b60985e861448b9cd554e8a74ee871"   # Cell Structure
}

OUTPUT_DIR = "/app/backend/heygen_videos"
MAX_WAIT = 600  # 10 minutes

def check_and_download(module_id, video_id):
    """Check video status and download if complete"""
    response = requests.get(
        "https://api.heygen.com/v1/video_status.get",
        headers={"X-Api-Key": HEYGEN_API_KEY, "Accept": "application/json"},
        params={"video_id": video_id}
    )
    
    if response.status_code != 200:
        return False, "API error"
    
    data = response.json().get("data", {})
    status = data.get("status")
    
    if status == "processing" or status == "pending":
        return False, "processing"
    
    if status == "failed":
        error = data.get("error", "Unknown error")
        return False, f"failed: {error}"
    
    if status == "completed":
        video_url = data.get("video_url")
        if not video_url:
            return False, "no URL"
        
        # Download
        output_path = f"{OUTPUT_DIR}/{module_id}_avatar.mp4"
        print(f"[{module_id}] Downloading from {video_url[:50]}...")
        
        video_response = requests.get(video_url, stream=True)
        with open(output_path, 'wb') as f:
            for chunk in video_response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = os.path.getsize(output_path)
        print(f"[{module_id}] Downloaded: {file_size/1024/1024:.1f} MB")
        return True, output_path
    
    return False, f"unknown status: {status}"

def main():
    print(f"🎬 Waiting for {len(VIDEO_IDS)} videos...")
    
    pending = dict(VIDEO_IDS)
    start_time = time.time()
    
    while pending and (time.time() - start_time) < MAX_WAIT:
        completed = []
        
        for module_id, video_id in pending.items():
            success, result = check_and_download(module_id, video_id)
            
            if success:
                print(f"✅ {module_id}: {result}")
                completed.append(module_id)
            elif "failed" in result:
                print(f"❌ {module_id}: {result}")
                completed.append(module_id)
            else:
                print(f"⏳ {module_id}: {result}")
        
        for module_id in completed:
            del pending[module_id]
        
        if pending:
            print(f"\n... waiting 30 seconds ({len(pending)} remaining) ...\n")
            time.sleep(30)
    
    if pending:
        print(f"\n⚠️ Timeout! Still pending: {list(pending.keys())}")
    else:
        print(f"\n🎉 All videos downloaded!")
    
    # List downloaded files
    print("\n📁 Avatar videos in directory:")
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith(".mp4"):
            size = os.path.getsize(f"{OUTPUT_DIR}/{f}")
            print(f"   {f}: {size/1024/1024:.1f} MB")

if __name__ == "__main__":
    main()
