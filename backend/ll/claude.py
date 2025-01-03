from anthropic import Anthropic
import logging

from ll.cache import URLLevelCache

log = logging.getLogger(__name__)

class Claude:
    
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
        self.RESPONSE_LENGTH = 1024
        self.cache = URLLevelCache()
        
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
        return self.cache.get_or_fetch(prompt, prompt, self._send_prompt)
