import re

class LinkParser:
    def __init__(self, link: str):
        self.link = link.strip()
        self.channel_id = None
        self.post_id = None
        self.is_public = False
        
    def is_valid(self):
        patterns = [
            r"https://t\.me/(c/)?(\d+)/(\d+)",
            r"https://t\.me/([a-zA-Z0-9_]+)/(\d+)"
        ]
        
        for pattern in patterns:
            match = re.match(pattern, self.link)
            if match:
                if 'c/' in self.link:
                    # Private channel link
                    self.channel_id = int(f"-100{match.group(2)}")
                    self.post_id = int(match.group(3))
                else:
                    # Public channel link
                    self.channel_id = match.group(1)
                    self.post_id = int(match.group(2))
                    self.is_public = True
                return True
        
        return False
    
    def get_chat_id(self):
        return self.channel_id
    
    def get_message_id(self):
        return self.post_id
