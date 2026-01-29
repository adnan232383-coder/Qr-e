"""
Video Generation Service
Generates avatar videos from module scripts using Sora 2
"""

import os
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from pathlib import Path

logger = logging.getLogger(__name__)

class VideoGenerator:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.api_key = os.environ.get("EMERGENT_LLM_KEY")
        self.output_dir = Path("/app/generated_videos")
        self.output_dir.mkdir(exist_ok=True)
    
    async def generate_module_video(self, module_id: str) -> Optional[Dict]:
        """Generate video for a module script"""
        try:
            # Get module script
            script = await self.db.module_scripts.find_one({"module_id": module_id}, {"_id": 0})
            if not script:
                logger.error(f"Script not found for module: {module_id}")
                return None
            
            # Get module info
            module = await self.db.modules.find_one({"module_id": module_id}, {"_id": 0})
            module_title = module.get("title", "Module") if module else "Module"
            
            # Update status to generating
            await self._update_video_status(module_id, "generating")
            
            # Create video prompt from script
            script_text = script.get("script_text", "")
            video_prompt = self._create_video_prompt(module_title, script_text)
            
            # Generate video
            video_path = await self._generate_video(module_id, video_prompt)
            
            if video_path:
                # Save video info to database
                video_info = {
                    "video_id": f"vid_{uuid.uuid4().hex[:12]}",
                    "module_id": module_id,
                    "course_id": script.get("course_id"),
                    "video_path": str(video_path),
                    "video_url": f"/api/videos/{module_id}",
                    "duration_seconds": 12,  # Sora 2 duration
                    "status": "completed",
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
                
                await self.db.module_videos.update_one(
                    {"module_id": module_id},
                    {"$set": video_info},
                    upsert=True
                )
                
                await self._update_video_status(module_id, "completed")
                logger.info(f"Video generated for module: {module_id}")
                
                return video_info
            else:
                await self._update_video_status(module_id, "failed")
                return None
                
        except Exception as e:
            logger.error(f"Video generation failed for {module_id}: {e}")
            await self._update_video_status(module_id, "failed")
            return None
    
    def _create_video_prompt(self, title: str, script_text: str) -> str:
        """Create a video generation prompt from script"""
        # Extract key points for video visualization
        # Sora 2 works better with visual descriptions
        prompt = f"""A professional educational video lecture scene:
- A friendly medical professor or doctor avatar standing in front of a modern university classroom
- Clean, professional setting with medical/educational visual elements in background
- The avatar is explaining: "{title}"
- Warm, welcoming atmosphere suitable for medical students
- High quality, realistic rendering
- Professional lighting and composition
"""
        return prompt
    
    async def _generate_video(self, module_id: str, prompt: str) -> Optional[Path]:
        """Generate video using Sora 2"""
        from emergentintegrations.llm.openai.video_generation import OpenAIVideoGeneration
        
        try:
            output_path = self.output_dir / f"{module_id}.mp4"
            
            video_gen = OpenAIVideoGeneration(api_key=self.api_key)
            
            # Generate 12-second video at standard HD
            video_bytes = video_gen.text_to_video(
                prompt=prompt,
                model="sora-2",
                size="1280x720",
                duration=12,
                max_wait_time=600
            )
            
            if video_bytes:
                video_gen.save_video(video_bytes, str(output_path))
                return output_path
            
            return None
            
        except Exception as e:
            logger.error(f"Sora 2 video generation error: {e}")
            return None
    
    async def _update_video_status(self, module_id: str, status: str):
        """Update video generation status"""
        await self.db.video_status.update_one(
            {"module_id": module_id},
            {
                "$set": {
                    "module_id": module_id,
                    "status": status,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            },
            upsert=True
        )
    
    async def get_video_status(self, module_id: str) -> Dict:
        """Get video generation status"""
        status = await self.db.video_status.find_one({"module_id": module_id}, {"_id": 0})
        if not status:
            return {"module_id": module_id, "status": "pending"}
        return status
    
    async def get_module_video(self, module_id: str) -> Optional[Dict]:
        """Get video info for a module"""
        video = await self.db.module_videos.find_one({"module_id": module_id}, {"_id": 0})
        return video


class VideoGenerationQueue:
    """Background queue for video generation"""
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.generator = VideoGenerator(db)
        self.is_running = False
    
    async def enqueue(self, module_id: str) -> Dict:
        """Add module to video generation queue"""
        task = {
            "task_id": f"vtask_{uuid.uuid4().hex[:12]}",
            "module_id": module_id,
            "status": "queued",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await self.db.video_queue.update_one(
            {"module_id": module_id},
            {"$set": task},
            upsert=True
        )
        return task
    
    async def process_queue(self):
        """Process queued video generation tasks"""
        if self.is_running:
            return
        
        self.is_running = True
        try:
            while True:
                task = await self.db.video_queue.find_one_and_update(
                    {"status": "queued"},
                    {"$set": {"status": "processing", "started_at": datetime.now(timezone.utc).isoformat()}},
                    sort=[("created_at", 1)]
                )
                
                if not task:
                    break
                
                module_id = task["module_id"]
                try:
                    await self.generator.generate_module_video(module_id)
                    await self.db.video_queue.update_one(
                        {"module_id": module_id},
                        {"$set": {"status": "completed", "completed_at": datetime.now(timezone.utc).isoformat()}}
                    )
                except Exception as e:
                    await self.db.video_queue.update_one(
                        {"module_id": module_id},
                        {"$set": {"status": "failed", "error": str(e)}}
                    )
        finally:
            self.is_running = False
    
    async def get_queue_status(self) -> Dict:
        """Get video queue status"""
        queued = await self.db.video_queue.count_documents({"status": "queued"})
        processing = await self.db.video_queue.count_documents({"status": "processing"})
        completed = await self.db.video_queue.count_documents({"status": "completed"})
        failed = await self.db.video_queue.count_documents({"status": "failed"})
        
        return {
            "queued": queued,
            "processing": processing,
            "completed": completed,
            "failed": failed,
            "is_running": self.is_running
        }
