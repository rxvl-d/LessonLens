import os
from anthropic import Anthropic
from pathlib import Path
import pickle
import logging

log = logging.getLogger(__name__)

class Claude:
    
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
        self.RESPONSE_LENGTH = 1024
        self.cache_dir = Path(os.getenv("HOME")) / '.cache' / 'LessonLens'
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_path = self.cache_dir / 'claude_cache.pkl'
        self.cache = dict()
        self._load_cache()
        
    def _load_cache(self):
        if self.cache_path.exists():
            with open(self.cache_path, 'rb') as f:
                self.cache = pickle.load(f)

    def _save_cache(self):
        with open(self.cache_path, 'wb') as f:
            pickle.dump(self.cache, f)

    def _send_prompt(self, prompt):
        try:
            response = self.client.messages.create(
                model=self.CLAUDE_MODEL,
                max_tokens=self.RESPONSE_LENGTH,
                messages=[{'role': 'user', 'content': [{'type': 'text', 'text': prompt}]}]
            )
            return response.content[0].text
        except Exception as e:
            log.warning(f"Error calling Claude API: {e}")
            return None

    def ask(self, prompt):
        self._load_cache()
        if prompt in self.cache:
            return self.cache[prompt]
        else:
            response = self._send_prompt(prompt)
            if response:
                self.cache[prompt] = response
                self._save_cache()
                return response
            else:
                return None