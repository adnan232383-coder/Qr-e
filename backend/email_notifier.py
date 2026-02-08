"""
Email Notification System for MCQ Generation Progress
Sends email updates every 2 hours with progress stats.
"""

import os
import asyncio
import logging
import resend
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# Configuration
RECIPIENT_EMAIL = "adnan232383@gmail.com"
SENDER_EMAIL = "onboarding@resend.dev"
NOTIFICATION_INTERVAL_HOURS = 2

# Initialize Resend
resend.api_key = os.environ.get("RESEND_API_KEY", "")


async def get_progress_stats(db: AsyncIOMotorDatabase) -> dict:
    """Get current progress statistics"""
    total_mcq = await db.mcq_questions.count_documents({})
    total_courses = await db.courses.count_documents({})
    total_scripts = await db.module_scripts.count_documents({})
    
    # Courses with 200+ questions
    pipeline = [
        {"$group": {"_id": "$course_id", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gte": 200}}}
    ]
    completed_courses = len(await db.mcq_questions.aggregate(pipeline).to_list(100))
    
    # Get current job info
    job = await db.jobs.find_one(
        {"job_type": "sequential_mcq"},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    
    # Distribution check
    dist_pipeline = [
        {"$group": {"_id": "$correct_answer", "count": {"$sum": 1}}}
    ]
    distribution = await db.mcq_questions.aggregate(dist_pipeline).to_list(10)
    dist_map = {d["_id"]: d["count"] for d in distribution}
    
    return {
        "total_mcq": total_mcq,
        "total_courses": total_courses,
        "completed_courses": completed_courses,
        "total_scripts": total_scripts,
        "current_course": job.get("current_course") if job else None,
        "job_status": job.get("status") if job else None,
        "distribution": dist_map,
        "target_mcq": total_courses * 200,
        "percentage": round((completed_courses / total_courses) * 100, 1) if total_courses > 0 else 0
    }


def generate_email_html(stats: dict) -> str:
    """Generate HTML email with progress stats"""
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    
    # Calculate distribution percentages
    total = stats["total_mcq"]
    dist = stats.get("distribution", {})
    dist_html = ""
    if total > 0:
        for letter in ["A", "B", "C", "D"]:
            count = dist.get(letter, 0)
            pct = round((count / total) * 100, 1) if total > 0 else 0
            color = "#22c55e" if 20 <= pct <= 30 else "#ef4444"
            dist_html += f'<td style="text-align:center;padding:8px;"><span style="color:{color};font-weight:bold;">{letter}: {pct}%</span></td>'
    
    remaining = stats["total_courses"] - stats["completed_courses"]
    est_hours = round(remaining * 12 / 60, 1)
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
    <div style="background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
        <h1 style="margin: 0; font-size: 24px;">UG University Assistant</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">דוח התקדמות - {now}</p>
    </div>
    
    <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        
        <h2 style="color: #1e3a5f; border-bottom: 2px solid #2563eb; padding-bottom: 10px;">📊 סטטוס כללי</h2>
        
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <tr>
                <td style="padding: 15px; background: #f0f9ff; border-radius: 8px;">
                    <div style="font-size: 32px; font-weight: bold; color: #2563eb;">{stats['completed_courses']}/{stats['total_courses']}</div>
                    <div style="color: #64748b;">קורסים הושלמו</div>
                </td>
                <td style="width: 20px;"></td>
                <td style="padding: 15px; background: #f0fdf4; border-radius: 8px;">
                    <div style="font-size: 32px; font-weight: bold; color: #22c55e;">{stats['total_mcq']:,}</div>
                    <div style="color: #64748b;">שאלות MCQ</div>
                </td>
            </tr>
        </table>
        
        <div style="background: #f8fafc; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span>התקדמות</span>
                <span style="font-weight: bold;">{stats['percentage']}%</span>
            </div>
            <div style="background: #e2e8f0; border-radius: 10px; height: 20px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, #22c55e, #2563eb); height: 100%; width: {stats['percentage']}%; border-radius: 10px;"></div>
            </div>
        </div>
        
        <h2 style="color: #1e3a5f; border-bottom: 2px solid #2563eb; padding-bottom: 10px; margin-top: 30px;">🔄 סטטוס נוכחי</h2>
        
        <table style="width: 100%; margin: 15px 0;">
            <tr>
                <td style="padding: 8px 0; color: #64748b;">קורס נוכחי:</td>
                <td style="padding: 8px 0; font-weight: bold; text-align: right;">{stats['current_course'] or 'N/A'}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; color: #64748b;">סטטוס:</td>
                <td style="padding: 8px 0; text-align: right;">
                    <span style="background: {'#22c55e' if stats['job_status'] == 'running' else '#94a3b8'}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px;">
                        {stats['job_status'] or 'N/A'}
                    </span>
                </td>
            </tr>
            <tr>
                <td style="padding: 8px 0; color: #64748b;">קורסים שנותרו:</td>
                <td style="padding: 8px 0; font-weight: bold; text-align: right;">{remaining}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; color: #64748b;">זמן משוער לסיום:</td>
                <td style="padding: 8px 0; font-weight: bold; text-align: right;">~{est_hours} שעות</td>
            </tr>
        </table>
        
        <h2 style="color: #1e3a5f; border-bottom: 2px solid #2563eb; padding-bottom: 10px; margin-top: 30px;">📈 פיזור תשובות</h2>
        
        <table style="width: 100%; margin: 15px 0; background: #f8fafc; border-radius: 8px;">
            <tr>
                {dist_html}
            </tr>
        </table>
        <p style="font-size: 12px; color: #64748b; text-align: center;">
            (טווח תקין: 20%-30% לכל תשובה)
        </p>
        
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0; text-align: center; color: #94a3b8; font-size: 12px;">
            <p>העדכון הבא יישלח בעוד שעתיים</p>
            <p>UG University Assistant - Powered by Emergent</p>
        </div>
    </div>
</body>
</html>
"""
    return html


async def send_progress_email(db: AsyncIOMotorDatabase) -> bool:
    """Send progress email"""
    if not resend.api_key:
        logger.warning("RESEND_API_KEY not configured, skipping email")
        return False
    
    try:
        stats = await get_progress_stats(db)
        html = generate_email_html(stats)
        
        params = {
            "from": SENDER_EMAIL,
            "to": [RECIPIENT_EMAIL],
            "subject": f"📊 UG Assistant - עדכון התקדמות ({stats['completed_courses']}/{stats['total_courses']} קורסים)",
            "html": html
        }
        
        # Send email in thread to not block
        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Progress email sent to {RECIPIENT_EMAIL}, ID: {result.get('id')}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send progress email: {e}")
        return False


class EmailNotificationScheduler:
    """Scheduler for periodic email notifications"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self._running = False
        self._task = None
    
    async def start(self):
        """Start the notification scheduler"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_scheduler())
        logger.info(f"Email notification scheduler started - sending to {RECIPIENT_EMAIL} every {NOTIFICATION_INTERVAL_HOURS} hours")
    
    async def stop(self):
        """Stop the scheduler"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Email notification scheduler stopped")
    
    async def _run_scheduler(self):
        """Main scheduler loop"""
        # Send initial email
        await send_progress_email(self.db)
        
        while self._running:
            # Wait for interval
            await asyncio.sleep(NOTIFICATION_INTERVAL_HOURS * 60 * 60)
            
            if self._running:
                # Check if job is still running
                job = await self.db.jobs.find_one(
                    {"job_type": "sequential_mcq", "status": "running"}
                )
                
                if job:
                    await send_progress_email(self.db)
                else:
                    # Job completed - send final email and stop
                    await send_progress_email(self.db)
                    logger.info("MCQ generation completed - stopping email notifications")
                    self._running = False


# Singleton
_scheduler = None

def get_email_scheduler(db: AsyncIOMotorDatabase) -> EmailNotificationScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = EmailNotificationScheduler(db)
    return _scheduler
