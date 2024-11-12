from typing import Dict, List, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import json
import os
from anthropic import Anthropic
from pathlib import Path
import pickle
import nltk
from nltk.corpus import stopwords

# Download German stop words from NLTK
nltk.download('stopwords')
german_stop_words = stopwords.words('german')
custom_stop_words = ['dass', 'dabei']
german_stop_words.extend(custom_stop_words)

class ResultClassifiers:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.CLAUDE_MODEL = "claude-3-5-sonnet-20240620"
        self.cache_dir = Path(".cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # Load caches
        self.edu_level_cache = self._load_cache('education_levels.pkl')
        self.resource_type_cache = self._load_cache('resource_types.pkl')
        
        # Load curriculum
        curr_path = Path(__file__).parent.parent / 'data'/ 'curricula' / 'chem.txt'
        with open(curr_path) as f:
            self.curriculum = f.read()
        
        # Initialize topic modeling
        self.vectorizer = TfidfVectorizer(
            stop_words=german_stop_words,
            # Common German characters included in token pattern
            token_pattern=r'(?u)\b[\w\äöüßÄÖÜ]+\b',
            # Include German-specific preprocessing
            lowercase=True,
            strip_accents='unicode'
        )
        self.lda = LatentDirichletAllocation(n_components=5, random_state=42)
        
        # Define valid resource types
        self.valid_resource_types = [
            'course', 'tutorial', 'lecture_notes', 'textbook',
            'practice_problems', 'quiz', 'video', 'podcast', 'software', 
            'image', 'simulation', 'lesson plan', 'presentation', 
            'professional development', 'interactive_tool', 
            'reference_material', 'lab_exercise', 'assessment', 
            'worksheet', 'study_guide'
        ]
        
        self._initialized = True

    def _load_cache(self, filename: str) -> Dict:
        cache_file = self.cache_dir / filename
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        return {}

    def _save_cache(self, cache: Dict, filename: str):
        with open(self.cache_dir / filename, 'wb') as f:
            pickle.dump(cache, f)

    def _ask_claude(self, prompt: str) -> str:
        try:
            response = self.client.messages.create(
                model=self.CLAUDE_MODEL,
                max_tokens=1024,
                messages=[{'role': 'user', 'content': [{'type': 'text', 'text': prompt}]}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return "unknown"

    def topic_classifier(self, titles: List[str], descriptions: List[str]) -> Dict[str, float]:
        """Performs topic modeling on the documents and returns topic distributions."""
        try:
            # Combine titles and descriptions
            documents = [f"{title} {desc}" for title, desc in zip(titles, descriptions)]
            
            # Create document-term matrix
            dtm = self.vectorizer.fit_transform(documents)
            
            # Fit LDA model
            doc_topics = self.lda.fit_transform(dtm)
            
            # Get feature names for interpretation
            feature_names = self.vectorizer.get_feature_names_out()
            
            # Get top words for each topic
            topic_words = {}
            for topic_idx, topic in enumerate(self.lda.components_):
                top_words = [feature_names[i] for i in topic.argsort()[:-10:-1]]
                topic_words[f'topic_{topic_idx}'] = tuple(top_words)
            
            # Calculate percentage of documents in each topic
            topic_percentages = (doc_topics > 0.3).sum(axis=0) / len(documents) * 100
            
            return {topic_words[f'topic_{i}']: percentage 
                    for i, percentage in enumerate(topic_percentages)}
        except Exception as e:
            print(f"Error in topic classification: {e}")
            return {"unknown": 100.0}

    def education_level_classifier(self, title: str, description: str, url: str) -> List[str]:
        """Classifies education level using Claude, with caching."""
        try:
            if url in self.edu_level_cache:
                return self.edu_level_cache[url]
            
            prompt = f"""Given the search result snippet of an educational resource on the web, tell me which grade it is appropriate for?
Use the curriculum to answer.
Answer with a grade level (number between 5 and 10 (inclusive)) OR comma separated list of grade levels OR with the keyword UNSURE.
Curriculum: {self.curriculum}
Snippet: 
Title: {title}
Description: {description}
URL: {url}"""
            
            response = self._ask_claude(prompt)
            
            # Parse response into list of grade levels
            if response.strip().upper() == 'UNSURE':
                grades = ['unknown']
            else:
                grades = [g.strip() for g in response.split(',')]
                
            self.edu_level_cache[url] = grades
            self._save_cache(self.edu_level_cache, 'education_levels.pkl')
            
            return grades
        except Exception as e:
            print(f"Error in education level classification: {e}")
            return ['unknown']

    def resource_type_classifier(self, title: str, description: str, url: str) -> List[str]:
        """Classifies resource type using Claude, with caching."""
        try:
            if url in self.resource_type_cache:
                return self.resource_type_cache[url]
            
            prompt = f"""Given this educational resource, what type of resource is it?
Choose from these categories: {', '.join(self.valid_resource_types)}
You can select up to 2 categories. Answer with just the category names separated by comma.

Title: {title}
Description: {description}
URL: {url}"""
            
            response = self._ask_claude(prompt)
            resource_types = [rt.strip() for rt in response.split(',')]
            
            self.resource_type_cache[url] = resource_types
            self._save_cache(self.resource_type_cache, 'resource_types.pkl')
            
            return resource_types
        except Exception as e:
            print(f"Error in resource type classification: {e}")
            return ['unknown']

# Create a global instance
classifiers = ResultClassifiers()

def classify_serp_results(serp_data: Dict) -> Dict:
    """Process SERP results and return classification statistics."""
    try:
        total_results = len(serp_data['results'])
        
        # Extract titles and descriptions for topic modeling
        titles = [r['title'] for r in serp_data['results']]
        descriptions = [r['description'] for r in serp_data['results']]
        
        # Get topic distributions
        topics_percent = classifiers.topic_classifier(titles, descriptions)
        
        # Initialize counters for other classifications
        educational_levels_count = {}
        resource_types_count = {}
        
        # Process each result
        for result in serp_data['results']:
            title = result['title']
            description = result['description']
            url = result['url']
            
            # Get classifications
            levels = classifiers.education_level_classifier(title, description, url)
            types = classifiers.resource_type_classifier(title, description, url)
            
            # Update counters
            for level in levels:
                educational_levels_count[level] = educational_levels_count.get(level, 0) + 1
                
            for res_type in types:
                resource_types_count[res_type] = resource_types_count.get(res_type, 0) + 1
        
        # Convert counts to percentages
        levels_percent = {k: (v / total_results) * 100 for k, v in educational_levels_count.items()}
        types_percent = {k: (v / total_results) * 100 for k, v in resource_types_count.items()}
        
        return {
            'topics': {','.join(k[:3]): v for (k, v) in topics_percent.items()},
            'educational_levels': levels_percent,
            'resource_types': types_percent
        }
    except Exception as e:
        print(f"Error in classify_serp_results: {e}")
        return {
            'topics': {"unknown": 100.0},
            'educational_levels': {"unknown": 100.0},
            'resource_types': {"unknown": 100.0}
        }