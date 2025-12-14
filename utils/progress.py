from pyrogram.types import Message
import time
from config import Config

class Progress:
    def __init__(self, client, chat_id, message_id, index, total):
        self.client = client
        self.chat_id = chat_id
        self.message_id = message_id
        self.index = index
        self.total = total
        self.start_time = time.time()
        self.last_update_time = 0
    
    def progress_callback(self, current, total):
        now = time.time()
        if now - self.last_update_time < 1:  # Update every 1 second
            return
        
        percentage = (current / total) * 100
        speed = current / (now - self.start_time)
        time_left = (total - current) / speed if speed > 0 else 0
        
        # Convert to readable format
        def human_readable_size(size):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024:
                    return f"{size:.2f} {unit}"
                size /= 1024
        
        current_str = human_readable_size(current)
        total_str = human_readable_size(total)
        speed_str = human_readable_size(speed)
        
        # Progress bar
        bar_length = 20
        filled_length = int(bar_length * current // total)
        bar = '█' * filled_length + '○' * (bar_length - filled_length)
        
        # Format time
        minutes, seconds = divmod(int(time_left), 60)
        hours, minutes = divmod(minutes, 60)
        time_str = f"{hours}h, {minutes}m, {seconds}s" if hours > 0 else f"{minutes}m, {seconds}s"
        
        progress_text = f"""
➵⋆🪐{Config.BRAND_NAME}𓂃

**Progress:** [{bar}] 
◌Progress😉:〘 {percentage:.2f}% 〙
Done: 〘{current_str} of {total_str}〙
◌Speed🚀:〘 {speed_str}/s 〙
◌Time Left⏳:〘 {time_str} 〙

File {self.index + 1}/{self.total}
        """
        
        try:
            self.client.edit_message_text(
                self.chat_id,
                self.message_id,
                progress_text
            )
        except:
            pass
        
        self.last_update_time = now
