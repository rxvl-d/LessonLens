from typing import Dict, List, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import json
import os
from pathlib import Path
import pickle
import nltk
from nltk.corpus import stopwords
from guidance import guidance, models, select, gen

# Download German stop words from NLTK
nltk.download('stopwords')
german_stop_words = stopwords.words('german')
custom_stop_words = ['dass', 'dabei']
german_stop_words.extend(custom_stop_words)

# Initialize the model once at file level
MODEL_PATH = Path.home() / ".cache/huggingface/hub/models--lmstudio-community--Meta-Llama-3-8B-Instruct-GGUF/snapshots/0910a3e69201d274d4fd68e89448114cd78e4c82/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf"
llm = models.LlamaCpp(str(MODEL_PATH), n_gpu_layers=-1, n_ctx=1024)

class GuidanceClassifiers:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # Use the global model instance
        self.lm = llm
        self.cache_dir = Path(".cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # Load caches
        self.edu_level_cache = self._load_cache('education_levels.pkl')
        self.resource_type_cache = self._load_cache('resource_types.pkl')
        
        # Load curriculum
        curr_path = Path(__file__).parent / 'phy.txt'
        with open(curr_path) as f:
            self.curriculum = f.read()
        
        # Initialize topic modeling
        self.vectorizer = TfidfVectorizer(
            stop_words=german_stop_words,
            token_pattern=r'(?u)\b[\w\äöüßÄÖÜ]+\b',
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

    @guidance
    def education_level_classify(lm, title: str, description: str, curriculum: str):
        """Guidance program for education level classification."""
        lm += f"""Given this educational resource, determine which grade levels (5-10) it is appropriate for.
    Analyze based on this curriculum:
    {curriculum}

    Resource:
    Title: {title}
    Description: {description}

    Respond with ONLY the grade numbers separated by commas or UNSURE if you cannot determine.
    Answer: """
        
        # Use select for basic UNSURE vs grade selection
        response_type = select(['UNSURE', 'GRADES'], name='response_type')
        lm += response_type
        
        if lm['response_type'] == 'GRADES':
            # Use regex to enforce valid grade format (numbers 5-10 separated by commas)
            lm += ' ' + gen(regex='([5-9]|10)(,\s*([5-9]|10))*', name='grade_nums')
            grades = [g.strip() for g in lm['grade_nums'].split(',')]
        else:
            grades = ['unknown']
        
        lm += f"\ngrades = {grades}"
        return lm

    @guidance
    def resource_type_classify(lm, title: str, description: str, valid_resource_types: List[str]):
        """Guidance program for resource type classification."""
        lm += f"""Classify this educational resource into up to 2 categories.

    Resource:
    Title: {title}
    Description: {description}

    Select the most appropriate categories from this list:
    {', '.join(valid_resource_types)}

    Answer with ONLY the category names, separated by comma if more than one.
    Categories: """
        
        # First select how many categories (1 or 2)
        num_categories = select(['1', '2'], name='num_cats')
        lm += num_categories
        
        # Then select the categories themselves
        if lm['num_cats'] == '1':
            lm += ' ' + select(valid_resource_types, name='cat1')
            resource_types = [lm['cat1']]
        else:
            lm += ' ' + select(valid_resource_types, name='cat1') + ', ' + select(valid_resource_types, name='cat2')
            resource_types = [lm['cat1'], lm['cat2']]
        
        lm += f"\nresource_types = {resource_types}"
        return lm

classifiers = GuidanceClassifiers()

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
            
            # Use cache if available
            if url in classifiers.edu_level_cache:
                levels = classifiers.edu_level_cache[url]
            else:
                # Execute the guidance program
                lm_edu = classifiers.education_level_classify(classifiers.lm, title, description, classifiers.curriculum)
                levels = lm_edu['grades'] if 'grades' in lm_edu else ['unknown']
                classifiers.edu_level_cache[url] = levels
                classifiers._save_cache(classifiers.edu_level_cache, 'education_levels.pkl')

            if url in classifiers.resource_type_cache:
                types = classifiers.resource_type_cache[url]
            else:
                # Execute the guidance program
                lm_type = classifiers.resource_type_classify(classifiers.lm, title, description, classifiers.valid_resource_types)
                types = lm_type['resource_types'] if 'resource_types' in lm_type else ['unknown']
                classifiers.resource_type_cache[url] = types
                classifiers._save_cache(classifiers.resource_type_cache, 'resource_types.pkl')
            
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