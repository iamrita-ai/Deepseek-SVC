import re
from datetime import datetime

class TextRules:
    @staticmethod
    def process_filename(filename: str, user_data: dict = None):
        """Process filename with custom rules"""
        if not user_data or 'replace_words' not in user_data:
            return filename
        
        replace_rules = user_data.get('replace_words', [])
        if isinstance(replace_rules, str):
            try:
                replace_rules = eval(replace_rules)
            except:
                replace_rules = []
        
        for old_word, new_word in replace_rules:
            filename = filename.replace(old_word, new_word)
        
        return filename
    
    @staticmethod
    def generate_caption(filename: str, user_data: dict = None):
        """Generate caption based on user settings"""
        if not user_data or not user_data.get('caption'):
            return None
        
        caption_template = user_data['caption']
        
        # Replace placeholders
        placeholders = {
            '{filename}': filename,
            '{date}': datetime.now().strftime('%Y-%m-%d'),
            '{time}': datetime.now().strftime('%H:%M:%S'),
            '{bot_name}': 'TECHNICAL_SERENA'
        }
        
        for placeholder, value in placeholders.items():
            caption_template = caption_template.replace(placeholder, value)
        
        return caption_template
    
    @staticmethod
    def process_rename_pattern(filename: str, user_data: dict = None):
        """Apply rename pattern to filename"""
        if not user_data or not user_data.get('rename'):
            return filename
        
        rename_pattern = user_data['rename']
        
        # Extract file extension
        if '.' in filename:
            name, ext = filename.rsplit('.', 1)
        else:
            name, ext = filename, ''
        
        # Replace placeholders in rename pattern
        placeholders = {
            '{filename}': name,
            '{ext}': ext,
            '{date}': datetime.now().strftime('%Y-%m-%d'),
            '{time}': datetime.now().strftime('%H%M%S'),
            '{timestamp}': str(int(datetime.now().timestamp()))
        }
        
        for placeholder, value in placeholders.items():
            rename_pattern = rename_pattern.replace(placeholder, value)
        
        if ext:
            return f"{rename_pattern}.{ext}"
        return rename_pattern
