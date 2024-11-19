from functools import partial
import json
import os
from anthropic import Anthropic
from pathlib import Path
import pickle
import logging

from ll.cache import PromptLevelCache, URLContentLevelCache

log = logging.getLogger(__name__)

class Claude:
    
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
        self.RESPONSE_LENGTH = 1024
        self.cache = PromptLevelCache()
        
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
        return self.cache.get_or_fetch(prompt, self._send_prompt)

class Personas:
    default = "You are a curator of educational resources who assigns educational metadata "+\
            "based on the content of those resources."


class EducationalLevel:
    def __init__(self, subject='chem'):
        self.claude = Claude()
        self.persona = Personas.default 
        self.task=  "Your task is to clasify which educational levels a given resource is" +\
            " appropriate for given the content of the resource and the given curriculum."
        self.response_instructions = "Respond with ONLY a JSON list of objects"+ \
            "where the keys are 'url' and 'response'. 'response' should be one of the following: "+ \
            "If the resource can be identified according to the curriculum "+ \
            "as being appropriate for a particular grade or grades label the URL with a list of grades (integers)." + \
            "If not, and you can tell from general knowledge that the resource is appropriate " +\
            "for HIGHER_EDUCATION, PRIMARY_EDUCATION or is NOT_FOR_EDUCATIONAL_PURPOSES, "+\
            "label the URL with that string. If you're usure, label it UNSURE."

        self.curriculum = self._load_curriculum(subject)
        self.url_level_cache = URLContentLevelCache('educational_level')
        
    def _load_curriculum(self, subject):
        Path(__file__).parent.parent / 'data'/ 'curricula' / f'{subject}.txt'
    
    def classify_fresh(self, url_content_batch):
        prompt = f"""{self.persona}
        {self.task}
        Resource content by URL: {url_content_batch}
        Curriculum:
        {self.curriculum}
        
        {self.response_instructions}"""
        response = self.claude.ask(prompt)
        response = json.loads(response)
        return response

    def classify(self, url_content_batch):
        return self.url_level_cache.get_or_fetch_batch(url_content_batch, self.classify_fresh)

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
        self.response_instructions = "Respond with ONLY a JSON list of objects"+ \
            "where the keys are 'url' and 'response'. 'response' should be one of the following: "+ \
            f"If the resource can be identified as one of  {self.valid_resource_types},"+ \
            "label the URL with a list of the resource types that apply." + \
            "If not, label it UNSURE."
        self.url_level_cache = URLContentLevelCache('resource_type')

    def classify_fresh(self, url_content_batch):
        prompt = f"""{self.persona}
        {self.task}
        Resource content by URL: {url_content_batch}
        {self.response_instructions}"""
        response = self.claude.ask(prompt)
        response = json.loads(response)
        return response

    def classify(self,url_content_batch):
        return self.url_level_cache.get_or_fetch_batch(url_content_batch, self.classify_fresh)

class Subject:
    def __init__(self):
        self.claude = Claude()
        self.persona =  Personas.default
        self.valid_subjects = [
            'Physics', 'Chemistry', 'Mathematics'
        ]
        self.valid_subjects_str = ', '.join(self.valid_subjects)
        self.task=  "Your task is to clasify the subject of each resource."
        self.response_instructions = "Respond with ONLY a JSON list of objects"+ \
            "where the keys are 'url' and 'response'. 'response' should be one of the following: "+ \
            f"If the resource can be identified as one of  {self.valid_subjects_str},"+ \
            "label the URL with a list of the subjects that apply." + \
            "If not, label it UNSURE."
        self.url_level_cache = URLContentLevelCache('subject')

    def classify_fresh(self, url_content_batch):
        prompt = f"""{self.persona}
        {self.task}
        Resource content by URL: {url_content_batch}
        {self.response_instructions}"""
        response = self.claude.ask(prompt)
        response = json.loads(response)
        return response

    def classify(self, url_content_batch):
        return self.url_level_cache.get_or_fetch_batch(url_content_batch, self.classify_fresh)

class Snippets:
    def __init__(self):
        self.claude = Claude()
        self.persona =  Personas.default
        self.task=  "Your task is to pick one or two sentences or fragments "+\
            "of sentences ONLY from the resource content and compose a search snippet "+\
            "that will best indicate the relevance of the resource "+\
            "to the information need of the teacher. Do not paraphrase. Only quote the text."
        self.response_instructions = "Respond with ONLY a JSON list of objects"+ \
            "where the keys are 'url' and 'response'. 'response' should be a string"+ \
            f"of text containing the search snippet."
        self.url_level_cache = URLContentLevelCache('enhanced_snippets')

    def classify_fresh(self, task_desc, url_content_batch):
        prompt = f"""{self.persona}
        {self.task}
        Information Need:
        {task_desc}
        Resource content by URL: {url_content_batch}
        {self.response_instructions}"""
        response = self.claude.ask(prompt)
        response = json.loads(response)
        return response

    def enhance(self, url_content_batch, task_desc):
        return self.url_level_cache.get_or_fetch_batch(url_content_batch, 
                                                       partial(self.classify_fresh, task_desc))