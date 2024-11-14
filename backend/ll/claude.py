import json
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


class Personas:
    default = "You are a curator of educational resources who assigns educational metadata "+\
            "based on the content of those resources."

class EducationalLevel:
    def __init__(self, subject='chem'):
        self.claude = Claude()
        self.persona = Personas.default 
        self.task=  "Your task is to clasify which educational levels a given resource is" +\
            " appropriate for given the content of the resource and the given curriculum."
        self.response_instructions = "Respond with ONLY a JSON object "+ \
            "where the keys are the URLs and the labels are the following: "+ \
            "If the resource can be identified according to the curriculum "+ \
            "as being appropriate for a particular grade or grades label the URL with a list of grades (integers)." + \
            "If not, and you can tell from general knowledge that the resource is appropriate " +\
            "for HIGHER_EDUCATION, PRIMARY_EDUCATION or is NOT_FOR_EDUCATIONAL_PURPOSES, "+\
            "label the URL with that string. If you're usure, label it UNSURE."

        self.curriculum = self._load_curriculum(subject)

        
    def _load_curriculum(self, subject):
        Path(__file__).parent.parent / 'data'/ 'curricula' / f'{subject}.txt'
    
    def classify(self, url_to_text):
        prompt = f"""{self.persona}
        {self.task}
        Resource content by URL: {url_to_text}
        Curriculum:
        {self.curriculum}
        
        {self.response_instructions}"""
        response = self.claude.ask(prompt)
        response = json.loads(response)
        response = {k: None if v == "UNSURE" else v for k, v in response.items()}
        return response

class ResourceType:
    def __init__(self):
        self.claude = Claude()
        self.persona =  Personas.default
        self.valid_resource_types = [
            'course', 'tutorial', 'lecture_notes', 'textbook',
            'practice_problems', 'quiz', 'video', 'podcast', 'software', 
            'image', 'simulation', 'lesson plan', 'presentation', 
            'professional development', 'interactive_tool', 
            'reference_material', 'lab_exercise', 'assessment', 
            'worksheet', 'study_guide'
        ]
        self.valid_resource_types_str = ', '.join(self.valid_resource_types)
        self.task=  "Your task is to clasify the resource type of each resource."
        self.response_instructions = "Respond with ONLY a JSON object "+ \
            "where the keys are the URLs and the labels are the following: "+ \
            f"If the resource can be identified as one of  {self.valid_resource_types},"+ \
            "label the URL with a list of the resource types that apply." + \
            "If not, label it UNSURE."

    def classify(self, url_to_text):
        prompt = f"""{self.persona}
        {self.task}
        Resource content by URL: {url_to_text}
        {self.response_instructions}"""
        response = self.claude.ask(prompt)
        response = json.loads(response)
        response = {k: None if v == "UNSURE" else v for k, v in response.items()}
        return response

class Subject:
    def __init__(self):
        self.claude = Claude()
        self.persona =  Personas.default
        self.valid_subjects = [
            'Physics', 'Chemistry', 'Mathematics'
        ]
        self.valid_subjects_str = ', '.join(self.valid_subjects)
        self.task=  "Your task is to clasify the subject of each resource."
        self.response_instructions = "Respond with ONLY a JSON object "+ \
            "where the keys are the URLs and the labels are the following: "+ \
            f"If the resource can be identified as one of  {self.valid_subjects_str},"+ \
            "label the URL with a list of the subjects that apply." + \
            "If not, label it UNSURE."

    def classify(self, url_to_text):
        prompt = f"""{self.persona}
        {self.task}
        Resource content by URL: {url_to_text}
        {self.response_instructions}"""
        response = self.claude.ask(prompt)
        response = json.loads(response)
        response = {k: None if v == "UNSURE" else v for k, v in response.items()}
        return response