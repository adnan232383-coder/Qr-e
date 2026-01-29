"""
Content Generation Service
Generates course content using RAG (Retrieval Augmented Generation)
- Course summaries
- MCQ questions (200 per course)
- Module avatar scripts (~12 min each)
"""

import os
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# Content status workflow
class ContentStatus:
    PENDING = "pending"
    GENERATING = "generating"
    REVIEWED = "reviewed"
    PUBLISHED = "published"
    FAILED = "failed"


class ContentGenerator:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.api_key = os.environ.get("EMERGENT_LLM_KEY")
    
    async def generate_course_content(self, course_id: str) -> Dict[str, Any]:
        """Main entry point to generate all content for a course"""
        try:
            # Get course info
            course = await self.db.courses.find_one({"external_id": course_id}, {"_id": 0})
            if not course:
                raise ValueError(f"Course not found: {course_id}")
            
            # Update status to generating
            await self._update_content_status(course_id, ContentStatus.GENERATING)
            
            # Log start
            await self._log_generation(course_id, "started", f"Starting content generation for {course['course_name']}")
            
            # Step 1: Research and gather sources
            sources = await self._gather_sources(course)
            await self._log_generation(course_id, "sources", f"Gathered {len(sources)} sources")
            
            # Step 2: Generate summary
            summary = await self._generate_summary(course, sources)
            await self._log_generation(course_id, "summary", "Generated course summary")
            
            # Step 3: Generate MCQ questions (200)
            questions = await self._generate_mcq_questions(course, sources, count=200)
            await self._log_generation(course_id, "questions", f"Generated {len(questions)} MCQ questions")
            
            # Step 4: Generate module scripts
            modules = await self.db.modules.find({"courseId": course_id}, {"_id": 0}).to_list(100)
            for module in modules:
                script = await self._generate_module_script(course, module, sources)
                await self._save_module_script(module["module_id"], script)
                await self._log_generation(course_id, "script", f"Generated script for module: {module['title']}")
            
            # Save all content
            await self._save_course_content(course_id, summary, sources)
            await self._save_questions(course_id, questions)
            
            # Update status to reviewed (auto-review for now)
            await self._update_content_status(course_id, ContentStatus.REVIEWED)
            
            await self._log_generation(course_id, "completed", "Content generation completed successfully")
            
            return {
                "status": "success",
                "course_id": course_id,
                "summary_length": len(summary),
                "questions_count": len(questions),
                "modules_with_scripts": len(modules)
            }
            
        except Exception as e:
            logger.error(f"Content generation failed for {course_id}: {e}")
            await self._update_content_status(course_id, ContentStatus.FAILED)
            await self._log_generation(course_id, "error", str(e))
            raise
    
    async def _gather_sources(self, course: Dict) -> List[Dict]:
        """Gather educational sources for the course topic"""
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        sources = []
        course_name = course["course_name"]
        description = course.get("course_description", "")
        
        # Use AI to identify key topics and generate search queries
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"sources_{uuid.uuid4().hex[:8]}",
            system_message="You are an educational content researcher. Generate search queries for medical/pharmacy education content."
        ).with_model("openai", "gpt-5.2")
        
        prompt = f"""For the course "{course_name}" ({description}), identify 5 key educational topics that should be covered.
For each topic, provide:
1. Topic name
2. A search query to find reliable educational content
3. Key concepts to cover

Format as JSON array: [{{"topic": "...", "query": "...", "concepts": ["...", "..."]}}]"""
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        # Parse topics and create source entries
        try:
            import json
            # Extract JSON from response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                topics = json.loads(response[json_start:json_end])
                for topic in topics:
                    sources.append({
                        "source_id": f"src_{uuid.uuid4().hex[:8]}",
                        "topic": topic.get("topic", ""),
                        "query": topic.get("query", ""),
                        "concepts": topic.get("concepts", []),
                        "type": "ai_research",
                        "retrieved_at": datetime.now(timezone.utc).isoformat()
                    })
        except Exception as e:
            logger.warning(f"Failed to parse sources: {e}")
            # Fallback to basic topics
            sources.append({
                "source_id": f"src_{uuid.uuid4().hex[:8]}",
                "topic": course_name,
                "query": f"{course_name} medical education",
                "concepts": [],
                "type": "fallback",
                "retrieved_at": datetime.now(timezone.utc).isoformat()
            })
        
        return sources
    
    async def _generate_summary(self, course: Dict, sources: List[Dict]) -> str:
        """Generate comprehensive course summary"""
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"summary_{uuid.uuid4().hex[:8]}",
            system_message="""You are an expert medical educator creating course summaries for university students.
Write clear, comprehensive, academically rigorous content suitable for medical/pharmacy students."""
        ).with_model("openai", "gpt-5.2")
        
        topics_context = "\n".join([f"- {s['topic']}: {', '.join(s.get('concepts', []))}" for s in sources])
        
        prompt = f"""Create a comprehensive course summary for:
Course: {course['course_name']}
Description: {course.get('course_description', 'N/A')}

Key Topics to Cover:
{topics_context}

Requirements:
1. Write 800-1200 words
2. Include learning objectives at the start
3. Cover all key concepts with clinical relevance
4. Use clear medical terminology with explanations
5. Include a brief section on clinical applications
6. End with key takeaways for exam preparation

Write in a professional academic tone suitable for medical students."""
        
        response = await chat.send_message(UserMessage(text=prompt))
        return response
    
    async def _generate_mcq_questions(self, course: Dict, sources: List[Dict], count: int = 200) -> List[Dict]:
        """Generate MCQ questions with answers and explanations"""
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        questions = []
        batch_size = 25  # Generate in batches
        batches = (count + batch_size - 1) // batch_size
        
        topics = [s["topic"] for s in sources]
        
        for batch_num in range(batches):
            remaining = min(batch_size, count - len(questions))
            if remaining <= 0:
                break
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"mcq_{uuid.uuid4().hex[:8]}",
                system_message="""You are a medical education expert creating high-quality MCQ questions.
Create questions suitable for medical/pharmacy board exam preparation."""
            ).with_model("openai", "gpt-5.2")
            
            topic_focus = topics[batch_num % len(topics)] if topics else course["course_name"]
            
            prompt = f"""Generate {remaining} multiple-choice questions for:
Course: {course['course_name']}
Topic Focus: {topic_focus}

For each question provide:
1. question: The question text
2. option_a, option_b, option_c, option_d: Four answer options
3. correct_answer: The correct option letter (A, B, C, or D)
4. explanation: Detailed explanation of why the answer is correct (2-3 sentences)
5. difficulty: easy, medium, or hard

Format as JSON array:
[{{"question": "...", "option_a": "...", "option_b": "...", "option_c": "...", "option_d": "...", "correct_answer": "A", "explanation": "...", "difficulty": "medium"}}]

Create clinically relevant questions testing understanding, not just memorization.
Vary difficulty: 30% easy, 50% medium, 20% hard."""
            
            try:
                response = await chat.send_message(UserMessage(text=prompt))
                
                # Parse JSON response
                import json
                json_start = response.find('[')
                json_end = response.rfind(']') + 1
                if json_start >= 0 and json_end > json_start:
                    batch_questions = json.loads(response[json_start:json_end])
                    for q in batch_questions:
                        q["question_id"] = f"q_{uuid.uuid4().hex[:12]}"
                        q["course_id"] = course["external_id"]
                        q["topic"] = topic_focus
                        q["created_at"] = datetime.now(timezone.utc).isoformat()
                        questions.append(q)
            except Exception as e:
                logger.warning(f"Failed to parse MCQ batch {batch_num}: {e}")
                continue
            
            # Small delay between batches
            await asyncio.sleep(0.5)
        
        return questions
    
    async def _generate_module_script(self, course: Dict, module: Dict, sources: List[Dict]) -> Dict:
        """Generate avatar script for a module (~12 minutes)"""
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"script_{uuid.uuid4().hex[:8]}",
            system_message="""You are an expert medical educator creating video lecture scripts.
Write engaging, educational scripts that explain complex concepts clearly.
Scripts should be suitable for text-to-speech avatar presentation."""
        ).with_model("openai", "gpt-5.2")
        
        topics_str = ", ".join(module.get("topics", []))
        
        prompt = f"""Create a video lecture script for:
Course: {course['course_name']}
Module: {module['title']}
Description: {module.get('description', 'N/A')}
Topics: {topics_str}
Target Duration: 12 minutes (approximately 1800 words)

Script Requirements:
1. Start with a brief introduction and learning objectives
2. Present content in logical sections with clear transitions
3. Include clinical examples and case scenarios
4. Use conversational but professional tone
5. Add periodic summaries and key points
6. End with a conclusion and preview of next topics
7. Include [PAUSE] markers for visual transitions
8. Include [EMPHASIS] markers for key terms

Format the script with clear section headers and speaking notes."""
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        # Calculate approximate duration (150 words per minute)
        word_count = len(response.split())
        duration_minutes = round(word_count / 150, 1)
        
        return {
            "script_id": f"script_{uuid.uuid4().hex[:12]}",
            "module_id": module["module_id"],
            "course_id": course["external_id"],
            "script_text": response,
            "word_count": word_count,
            "estimated_duration_minutes": duration_minutes,
            "status": ContentStatus.REVIEWED,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def _save_course_content(self, course_id: str, summary: str, sources: List[Dict]):
        """Save course content to database"""
        content = {
            "course_id": course_id,
            "summary": summary,
            "sources": sources,
            "status": ContentStatus.REVIEWED,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await self.db.course_content.update_one(
            {"course_id": course_id},
            {"$set": content},
            upsert=True
        )
    
    async def _save_questions(self, course_id: str, questions: List[Dict]):
        """Save MCQ questions to database"""
        if not questions:
            return
        
        # Delete existing questions for this course
        await self.db.mcq_questions.delete_many({"course_id": course_id})
        
        # Insert new questions
        await self.db.mcq_questions.insert_many(questions)
    
    async def _save_module_script(self, module_id: str, script: Dict):
        """Save module script to database"""
        await self.db.module_scripts.update_one(
            {"module_id": module_id},
            {"$set": script},
            upsert=True
        )
    
    async def _update_content_status(self, course_id: str, status: str):
        """Update content generation status"""
        await self.db.content_status.update_one(
            {"course_id": course_id},
            {
                "$set": {
                    "course_id": course_id,
                    "status": status,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            },
            upsert=True
        )
    
    async def _log_generation(self, course_id: str, event: str, message: str):
        """Log generation events"""
        log_entry = {
            "log_id": f"log_{uuid.uuid4().hex[:12]}",
            "course_id": course_id,
            "event": event,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.db.generation_logs.insert_one(log_entry)
        logger.info(f"[{course_id}] {event}: {message}")
    
    async def get_content_status(self, course_id: str) -> Dict:
        """Get current content status for a course"""
        status = await self.db.content_status.find_one({"course_id": course_id}, {"_id": 0})
        if not status:
            return {"course_id": course_id, "status": ContentStatus.PENDING}
        return status
    
    async def get_generation_logs(self, course_id: str) -> List[Dict]:
        """Get generation logs for a course"""
        logs = await self.db.generation_logs.find(
            {"course_id": course_id},
            {"_id": 0}
        ).sort("timestamp", -1).to_list(100)
        return logs
    
    async def publish_content(self, course_id: str) -> bool:
        """Publish reviewed content"""
        result = await self.db.content_status.update_one(
            {"course_id": course_id, "status": ContentStatus.REVIEWED},
            {"$set": {"status": ContentStatus.PUBLISHED, "published_at": datetime.now(timezone.utc).isoformat()}}
        )
        return result.modified_count > 0


# Background task queue for content generation
class ContentGenerationQueue:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.generator = ContentGenerator(db)
        self.is_running = False
        self.current_task = None
    
    async def enqueue(self, course_id: str) -> Dict:
        """Add course to generation queue"""
        task = {
            "task_id": f"task_{uuid.uuid4().hex[:12]}",
            "course_id": course_id,
            "status": "queued",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await self.db.generation_queue.update_one(
            {"course_id": course_id},
            {"$set": task},
            upsert=True
        )
        return task
    
    async def process_queue(self):
        """Process queued generation tasks"""
        if self.is_running:
            return
        
        self.is_running = True
        try:
            while True:
                # Get next queued task
                task = await self.db.generation_queue.find_one_and_update(
                    {"status": "queued"},
                    {"$set": {"status": "processing", "started_at": datetime.now(timezone.utc).isoformat()}},
                    sort=[("created_at", 1)]
                )
                
                if not task:
                    break
                
                course_id = task["course_id"]
                try:
                    await self.generator.generate_course_content(course_id)
                    await self.db.generation_queue.update_one(
                        {"course_id": course_id},
                        {"$set": {"status": "completed", "completed_at": datetime.now(timezone.utc).isoformat()}}
                    )
                except Exception as e:
                    await self.db.generation_queue.update_one(
                        {"course_id": course_id},
                        {"$set": {"status": "failed", "error": str(e)}}
                    )
        finally:
            self.is_running = False
    
    async def get_queue_status(self) -> Dict:
        """Get queue status"""
        queued = await self.db.generation_queue.count_documents({"status": "queued"})
        processing = await self.db.generation_queue.count_documents({"status": "processing"})
        completed = await self.db.generation_queue.count_documents({"status": "completed"})
        failed = await self.db.generation_queue.count_documents({"status": "failed"})
        
        return {
            "queued": queued,
            "processing": processing,
            "completed": completed,
            "failed": failed,
            "is_running": self.is_running
        }
