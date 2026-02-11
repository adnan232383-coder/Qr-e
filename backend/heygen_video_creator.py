"""
HeyGen Video Creator with Multiple Presentation Styles
Creates diverse avatar videos with different backgrounds and styles
"""

import os
import time
import requests
from typing import Dict, Optional, List
from enum import Enum

HEYGEN_API_KEY = os.environ.get("HEYGEN_API_KEY", "sk_V2_hgu_kXVuWJrQn74_2eBCQ3FvLT6LggmUwyoJOes2woHS61dM")

# Available presentation styles
class PresentationStyle(Enum):
    # Style 1: Classic avatar only (solid background)
    CLASSIC_AVATAR = "classic"
    # Style 2: Avatar with office background
    OFFICE_BACKGROUND = "office"
    # Style 3: Avatar on left side with content area on right
    AVATAR_SIDE_LEFT = "side_left"
    # Style 4: Medical/educational themed background
    MEDICAL_THEMED = "medical"
    # Style 5: Classroom/whiteboard style
    CLASSROOM = "classroom"
    # Style 6: Modern studio background
    MODERN_STUDIO = "modern_studio"

# Avatar configurations for variety
FEMALE_AVATARS = [
    {"id": "Adriana_Nurse_Front_public", "name": "Adriana Nurse Front", "style": "medical"},
    {"id": "Abigail_standing_office_front", "name": "Abigail Office Front", "style": "office"},
    {"id": "Adriana_Business_Front_public", "name": "Adriana Business Front", "style": "professional"},
    {"id": "Abigail_sitting_sofa_front", "name": "Abigail Sofa Front", "style": "casual"},
    {"id": "Adriana_BizTalk_Front_public", "name": "Adriana BizTalk", "style": "presenter"},
]

MALE_AVATARS = [
    {"id": "Adrian_public_2_20240312", "name": "Adrian Blue Suit", "style": "professional"},
    {"id": "Aditya_public_4", "name": "Aditya Brown Blazer", "style": "professional"},
    {"id": "Albert_public_1", "name": "Albert Blue Suit", "style": "professional"},
]

# English voices
ENGLISH_VOICES = [
    {"id": "42d00d4aac5441279d8536cd6b52c53c", "name": "Hope", "gender": "female"},
    {"id": "cef3bc4e0a84424cafcde6f2cf466c97", "name": "Ivy", "gender": "female"},
    {"id": "6be73833ef9a4eb0aeee399b8fe9d62b", "name": "Andrew", "gender": "male"},
    {"id": "d92994ae0de34b2e8659b456a2f388b8", "name": "John Doe", "gender": "male"},
]

# Background images for different styles (using public educational images)
BACKGROUND_CONFIGS = {
    PresentationStyle.CLASSIC_AVATAR: {
        "type": "color",
        "color": "#1a1a2e"  # Dark blue professional
    },
    PresentationStyle.OFFICE_BACKGROUND: {
        "type": "color",
        "color": "#f5f5f5"  # Light gray office
    },
    PresentationStyle.MEDICAL_THEMED: {
        "type": "color", 
        "color": "#e8f5e9"  # Light green medical
    },
    PresentationStyle.CLASSROOM: {
        "type": "color",
        "color": "#fff8e1"  # Warm cream classroom
    },
    PresentationStyle.MODERN_STUDIO: {
        "type": "color",
        "color": "#263238"  # Dark studio
    },
}


class HeyGenVideoCreator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or HEYGEN_API_KEY
        self.base_url = "https://api.heygen.com"
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Api-Key": self.api_key
        }
    
    def get_style_config(self, module_index: int) -> Dict:
        """
        Get presentation style configuration based on module index.
        Changes style every 2 modules for variety.
        """
        style_rotation = [
            {
                "style": PresentationStyle.CLASSIC_AVATAR,
                "avatar": FEMALE_AVATARS[0],  # Adriana Nurse
                "voice": ENGLISH_VOICES[0],   # Hope
            },
            {
                "style": PresentationStyle.OFFICE_BACKGROUND,
                "avatar": FEMALE_AVATARS[1],  # Abigail Office
                "voice": ENGLISH_VOICES[1],   # Ivy
            },
            {
                "style": PresentationStyle.MEDICAL_THEMED,
                "avatar": FEMALE_AVATARS[2],  # Adriana Business
                "voice": ENGLISH_VOICES[0],   # Hope
            },
            {
                "style": PresentationStyle.MODERN_STUDIO,
                "avatar": MALE_AVATARS[0],    # Adrian Blue Suit
                "voice": ENGLISH_VOICES[2],   # Andrew
            },
        ]
        
        # Change style every 2 modules
        style_index = (module_index // 2) % len(style_rotation)
        return style_rotation[style_index]
    
    def create_video_payload(
        self,
        script_text: str,
        avatar_id: str,
        voice_id: str,
        style: PresentationStyle,
        dimension: Dict = None
    ) -> Dict:
        """Create the video generation payload"""
        
        background_config = BACKGROUND_CONFIGS.get(style, BACKGROUND_CONFIGS[PresentationStyle.CLASSIC_AVATAR])
        
        payload = {
            "video_inputs": [
                {
                    "character": {
                        "type": "avatar",
                        "avatar_id": avatar_id,
                        "avatar_style": "normal"
                    },
                    "voice": {
                        "type": "text",
                        "input_text": script_text,
                        "voice_id": voice_id,
                        "speed": 1.0
                    },
                    "background": {
                        "type": background_config["type"],
                        "value": background_config.get("color", "#1a1a2e")
                    }
                }
            ],
            "dimension": dimension or {"width": 1920, "height": 1080},
            "test": False
        }
        
        return payload
    
    def generate_video(
        self,
        script_text: str,
        module_index: int = 0,
        custom_avatar_id: str = None,
        custom_voice_id: str = None
    ) -> Dict:
        """Generate a video with automatic style rotation"""
        
        # Get style configuration based on module index
        config = self.get_style_config(module_index)
        
        avatar_id = custom_avatar_id or config["avatar"]["id"]
        voice_id = custom_voice_id or config["voice"]["id"]
        style = config["style"]
        
        payload = self.create_video_payload(
            script_text=script_text,
            avatar_id=avatar_id,
            voice_id=voice_id,
            style=style
        )
        
        print(f"Generating video with style: {style.value}")
        print(f"Avatar: {config['avatar']['name']}, Voice: {config['voice']['name']}")
        
        response = requests.post(
            f"{self.base_url}/v2/video/generate",
            headers=self.headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            video_id = result.get("data", {}).get("video_id")
            return {
                "success": True,
                "video_id": video_id,
                "style": style.value,
                "avatar": config["avatar"]["name"],
                "voice": config["voice"]["name"]
            }
        else:
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }
    
    def check_video_status(self, video_id: str) -> Dict:
        """Check video generation status"""
        response = requests.get(
            f"{self.base_url}/v1/video_status.get",
            headers=self.headers,
            params={"video_id": video_id}
        )
        
        if response.status_code == 200:
            return response.json()
        return {"error": response.text}
    
    def wait_for_video(self, video_id: str, max_wait: int = 600) -> Dict:
        """Wait for video to complete and return result"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status = self.check_video_status(video_id)
            
            if "data" in status:
                video_status = status["data"].get("status")
                
                if video_status == "completed":
                    return {
                        "success": True,
                        "status": "completed",
                        "video_url": status["data"].get("video_url"),
                        "duration": status["data"].get("duration")
                    }
                elif video_status == "failed":
                    return {
                        "success": False,
                        "status": "failed",
                        "error": status["data"].get("error")
                    }
                
                print(f"Status: {video_status}...")
            
            time.sleep(10)
        
        return {"success": False, "status": "timeout"}
    
    def download_video(self, video_url: str, output_path: str) -> bool:
        """Download video to local path"""
        try:
            response = requests.get(video_url, stream=True)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
            return False
        except Exception as e:
            print(f"Download error: {e}")
            return False


def create_demo_videos():
    """Create demo videos showing different presentation styles"""
    creator = HeyGenVideoCreator()
    
    demo_scripts = [
        {
            "index": 0,
            "name": "style_classic",
            "script": "Welcome to this biology lecture. Today we will explore the fundamental concepts of cell biology. Let me guide you through this fascinating topic."
        },
        {
            "index": 2,
            "name": "style_office",
            "script": "In this module, we'll discuss cellular structures. Pay attention to the key components that make up every living cell in your body."
        },
        {
            "index": 4,
            "name": "style_medical",
            "script": "Medical education requires understanding complex biological processes. Let me explain how cellular respiration works step by step."
        },
        {
            "index": 6,
            "name": "style_studio",
            "script": "Today's presentation covers advanced genetics concepts. Understanding DNA replication is essential for your medical studies."
        },
    ]
    
    results = []
    for demo in demo_scripts:
        print(f"\n{'='*50}")
        print(f"Creating demo: {demo['name']}")
        print(f"{'='*50}")
        
        result = creator.generate_video(
            script_text=demo["script"],
            module_index=demo["index"]
        )
        
        if result["success"]:
            print(f"Video ID: {result['video_id']}")
            results.append({
                "name": demo["name"],
                "video_id": result["video_id"],
                "style": result["style"],
                "avatar": result["avatar"]
            })
        else:
            print(f"Error: {result.get('error')}")
    
    return results


if __name__ == "__main__":
    # Test creating demo videos
    results = create_demo_videos()
    print("\n\nResults:")
    for r in results:
        print(f"  - {r['name']}: {r['video_id']} (Style: {r['style']}, Avatar: {r['avatar']})")
