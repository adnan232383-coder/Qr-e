"""
Approved Avatar Styles Configuration
Only these 2 styles should be used for all future video generation
Updated: Feb 2026
"""

# APPROVED STYLES - Use only these for all courses
APPROVED_STYLES = [
    {
        "id": "medical_dark",
        "name": "Medical Dark",
        "name_he": "רפואי כהה",
        "avatar_id": "Adriana_Nurse_Front_public",
        "avatar_name": "Adriana Nurse",
        "voice_id": "42d00d4aac5441279d8536cd6b52c53c",
        "voice_name": "Hope",
        "background": {"type": "color", "value": "#1a1a2e"},
        "avatar_style": "normal",
        "scale": None,  # Standard size
        "offset": None,  # Center position
    },
    {
        "id": "presentation",
        "name": "Presentation",
        "name_he": "פרזנטציה",
        "avatar_id": "Adriana_Nurse_Front_public", 
        "avatar_name": "Adriana Nurse (Side)",
        "voice_id": "42d00d4aac5441279d8536cd6b52c53c",
        "voice_name": "Hope",
        "background": {"type": "color", "value": "#1a1a2e"},
        "avatar_style": "normal",
        "scale": 0.8,  # Slightly smaller
        "offset": {"x": -0.3, "y": 0},  # Positioned on left side
    }
]

# Style rotation plan for courses
# Modules 1-4: Medical Dark
# Modules 5-8: Presentation
def get_style_for_module(module_index: int) -> dict:
    """
    Get the approved style for a module.
    Modules 0-3 (1-4): Medical Dark
    Modules 4-7 (5-8): Presentation
    """
    if module_index < 4:
        return APPROVED_STYLES[0]  # Medical Dark
    else:
        return APPROVED_STYLES[1]  # Presentation


# Video generation payload builder
def build_video_payload(script_text: str, style: dict) -> dict:
    """Build HeyGen API payload with approved style"""
    character = {
        "type": "avatar",
        "avatar_id": style["avatar_id"],
        "avatar_style": style["avatar_style"]
    }
    
    # Add scale and offset only if specified
    if style.get("scale"):
        character["scale"] = style["scale"]
    if style.get("offset"):
        character["offset"] = style["offset"]
    
    payload = {
        "video_inputs": [{
            "character": character,
            "voice": {
                "type": "text",
                "input_text": script_text,
                "voice_id": style["voice_id"],
                "speed": 1.0
            },
            "background": style["background"]
        }],
        "dimension": {"width": 1920, "height": 1080},
        "test": False
    }
    
    return payload


# Example usage
if __name__ == "__main__":
    print("Approved Styles Configuration")
    print("=" * 40)
    for i, style in enumerate(APPROVED_STYLES):
        print(f"\nStyle {i+1}: {style['name']} ({style['name_he']})")
        print(f"  Avatar: {style['avatar_name']}")
        print(f"  Voice: {style['voice_name']}")
        print(f"  Position: {'Side (left)' if style.get('offset') else 'Center'}")
