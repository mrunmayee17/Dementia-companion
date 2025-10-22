"""
NeMo Reminder Tool for scheduling and managing reminders
"""
from typing import Dict, Any
import re
from datetime import datetime, timedelta
from src.core.logging import get_logger

logger = get_logger(__name__)

class NeMoReminderTool:
    """Real NeMo reminder management tool"""
    
    def __init__(self, memory_manager):
        """Initialize with memory manager"""
        self.memory_manager = memory_manager
        logger.info("NeMo Reminder Tool initialized")
        
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute reminder creation"""
        text = input_data.get("text", "")
        
        if not text:
            return {"success": False, "error": "No reminder text provided"}
            
        try:
            # Parse reminder details
            reminder_details = self._parse_reminder(text)
            
            logger.info(f"Creating reminder: {reminder_details['title']}")
            
            # Store as memory with reminder metadata
            result = self.memory_manager.store_memory(
                content=reminder_details["description"],
                metadata={
                    "type": "reminder",
                    "title": reminder_details["title"],
                    "scheduled_time": reminder_details["time"],
                    "created_at": datetime.now().isoformat(),
                    "active": True
                }
            )
            
            if result:
                return {
                    "success": True,
                    "title": reminder_details["title"],
                    "scheduled_time": reminder_details["time"],
                    "message": f"Reminder set: {reminder_details['title']}"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create reminder"
                }
                
        except Exception as e:
            logger.error(f"Reminder creation failed: {e}")
            return {
                "success": False,
                "error": f"Reminder creation failed: {str(e)}"
            }
            
    def _parse_reminder(self, text: str) -> Dict[str, Any]:
        """Parse reminder text to extract details"""
        # Simple parsing - can be enhanced with NLP
        
        # Extract time patterns
        time_patterns = [
            r"(\d{1,2})\s*(am|pm)",  # 8pm, 10am
            r"(\d{1,2}):(\d{2})\s*(am|pm)",  # 8:30pm
            r"at\s+(\d{1,2})\s*(am|pm)",  # at 8pm
            r"(\d{1,2})\s*o'?clock",  # 8 o'clock
        ]
        
        # Extract day patterns
        day_patterns = [
            r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)s?",
            r"(tomorrow|today)",
            r"next\s+(week|month)",
        ]
        
        # Default values
        title = "Reminder"
        description = text
        scheduled_time = (datetime.now() + timedelta(hours=1)).isoformat()
        
        # Extract title/action
        if "remind me to" in text.lower():
            parts = text.lower().split("remind me to", 1)
            if len(parts) > 1:
                title = parts[1].strip()
                description = f"Reminder: {title}"
                
        # Extract time
        for pattern in time_patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    if len(match.groups()) == 2:  # hour and am/pm
                        hour = int(match.group(1))
                        ampm = match.group(2)
                        if ampm == "pm" and hour != 12:
                            hour += 12
                        elif ampm == "am" and hour == 12:
                            hour = 0
                            
                        # Set for today at that time
                        target_time = datetime.now().replace(
                            hour=hour, minute=0, second=0, microsecond=0
                        )
                        
                        # If time has passed today, set for tomorrow
                        if target_time < datetime.now():
                            target_time += timedelta(days=1)
                            
                        scheduled_time = target_time.isoformat()
                        break
                        
                except ValueError:
                    pass
                    
        return {
            "title": title,
            "description": description,
            "time": scheduled_time
        }