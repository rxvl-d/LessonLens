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
import logging
import random
from ll.classifiers import *

log = logging.getLogger(__name__)
            
class Summarizer:
    def __init__(self, educational_levels_classifier, resource_types_classifier):
        nltk.download('stopwords')
        german_stop_words = stopwords.words('german')
        custom_stop_words = ['dass', 'dabei']
        german_stop_words.extend(custom_stop_words)
        self.education_level_classifier = educational_levels_classifier
        self.resource_type_classifier = resource_types_classifier
        self.vectorizer = TfidfVectorizer(
            stop_words=german_stop_words,
            # Common German characters included in token pattern
            token_pattern=r'(?u)\b[\w\äöüßÄÖÜ]+\b',
            # Include German-specific preprocessing
            lowercase=True,
            strip_accents='unicode'
        )
        self.lda = LatentDirichletAllocation(n_components=5, random_state=42)

    def topic_classifier(self, titles, descriptions):
        """Performs topic modeling on the documents and returns topic distributions."""
        try:
            documents = [f"{title} {desc}" for title, desc in zip(titles, descriptions)]
            dtm = self.vectorizer.fit_transform(documents)
            doc_topics = self.lda.fit_transform(dtm)
            feature_names = self.vectorizer.get_feature_names_out()
            topic_words = {}
            for topic_idx, topic in enumerate(self.lda.components_):
                top_words = [feature_names[i] for i in topic.argsort()[:-10:-1]]
                topic_words[f'topic_{topic_idx}'] = tuple(top_words)
            topic_percentages = (doc_topics > 0.3).sum(axis=0) / len(documents) * 100
            
            return {topic_words[f'topic_{i}']: percentage 
                    for i, percentage in enumerate(topic_percentages)}
        except Exception as e:
            log.error(f"Error in topic classification: {e}")
            return {"unknown": 100.0}

    def summarize_v3(self, search_task, serp_data):
        prompt = f"""
        Given a list of URLs, titles and summaries, 
        return the list of URLs tagged with various educational attributes.
        Also rate the importance of attributes given a search task.

        Search Task: {search_task}
        Input: {serp_data}
        Output should be in JSON in the form:
        {{
          "tagged_urls": [
            {{
              "url": "url1",
              "is_commercial": true/false,
              "is_educational": true/false, // not educational if it is news or sales
              "source_institution": ["university", "school", "non-profit foundation", "private teacher", "private company"] // pick all that apply
              "educational_level": ["Grundschule", "Sekundarstufe I", "Sekundarstufe II", "Higher Education"] // Pick the lowest applicable level
              "subject": ["Physics", "Chemistry", "Maths"] // Pick one
              "learning_resource_type": {LEARNING_RESOURCE_TYPES} // Pick all that apply
            }},
            {{"url": "url2",
              "is_commercial": ...}},
            ... 
          ],
          "attribute_importances": [
            {{ 
              "attribute": "is_commercial", 
              "importance" : 1 // on a scale of 1-5
            }},
            {{ 
              "attribute": "is_educational", 
              "importance" : 1 // on a scale of 1-5
            }},
            ...
          ]
        }}
        """
        response = parse_json(get_gpt4_labels(prompt, fast=True))
        if (type(response) == dict) and (set(response.keys()) == {'attribute_importances', 'tagged_urls'}):
          return response
        else:
          return None

    def summarize_v3_fast(self, search_task, serp_data):
        summary = []
        for r in serp_data:
            summary_part = {}
            summary_part['url'] = url = r['url']
            title = r['title']
            description = r['description']
            summary_part['is_commercial'] = 'Non-Commercial' not in commercial_classifier(url, title, description)
            summary_part['is_educational'] = 'Educational' in page_classifier(url, title, description)
            summary_part['source_institution'] = source_classifier(url, title, description)
            summary_part['educational_level'] = ed_level_classifier(url, title, description)
            summary_part['audience'] = audience_classifier(url, title, description)
            summary_part['source_institution_type'] = source_classifier(url, title, description)
            summary.append(summary_part)
        attr_importances = calculate_attribute_importance(summary)
        return {'tagged_urls': summary, 'attribute_importances': attr_importances}

    def summarize_v2(self, serp_data):
        summary = []
        for r in serp_data:
            summary_part = {}
            summary_part['url'] = url = r['url']
            summary_part['title'] = title = r['title']
            summary_part['description'] = description = r['description']
            summary_part['is_commercial'] = commercial_classifier(url, title, description)
            summary_part['educational_news_sales'] = page_classifier(url, title, description)
            summary_part['audience'] = audience_classifier(url, title, description)
            summary_part['source_institution_type'] = source_classifier(url, title, description)
            summary_part['education_level'] = ed_level_classifier(url, title, description)
            summary.append(summary_part)
        return summary


    def summarize(self, serp_data):
        try:
            total_results = len(serp_data['results'])
            
            # Extract titles and descriptions for topic modeling
            titles = [r['title'] for r in serp_data['results']]
            descriptions = [r['description'] for r in serp_data['results']]
            
            # Get topic distributions
            topics_percent = self.topic_classifier(titles, descriptions)
            
            input_data = [{
                "url": r['url'], 
                "content_type": 'snippet', 
                "content": f"URL: {r['url']}\nTitle: {r['title']}\nDescription: {r['description']}"}
                          for r in serp_data['results']]
            educational_levels = self.education_level_classifier.classify(input_data)
            resource_types = self.resource_type_classifier.classify(input_data)
            # Initialize counters for other classifications
            educational_levels_count = {}
            resource_types_count = {}
            
            # Process each result
            for result in educational_levels:
                response = result['response']
                if type(response) == list:
                    for level in response:
                        educational_levels_count[level] = educational_levels_count.get(level, 0) + 1
                elif type(response) == str:
                    educational_levels_count[response] = educational_levels_count.get(response, 0) + 1

            for result in resource_types:
                response = result['response']
                if type(response) == list:
                    for typ in response:
                        resource_types_count[typ] = resource_types_count.get(typ, 0) + 1
                elif type(response) == str:
                    resource_types_count[response] = resource_types_count.get(response, 0) + 1
            
            
            # Convert counts to percentages
            levels_percent = {k: (v / total_results) * 100 for k, v in educational_levels_count.items()}
            types_percent = {k: (v / total_results) * 100 for k, v in resource_types_count.items()}
            
            response = {
                'topics': {','.join(k[:3]): v for (k, v) in topics_percent.items()},
                'educational_levels': levels_percent,
                'resource_types': types_percent
            }
            return response
        except Exception as e:
            raise e

            
from collections import Counter
from typing import List, Dict, Union
import math

def calculate_attribute_importance(data: List[Dict[str, Union[str, List[str]]]]) -> List[Dict[str, Union[str, float]]]:
    """
    Calculate importance scores for attributes based on how well they split the dataset.
    
    Args:
        data: List of dictionaries with 'url' and various attributes that can be either
              single categorical values or lists of categorical values
    
    Returns:
        List of dictionaries containing attribute names and their importance scores (1-5)
    """
    def calculate_entropy(values: List[str]) -> float:
        """Calculate entropy for a list of values."""
        counts = Counter(values)
        total = len(values)
        entropy = 0
        
        for count in counts.values():
            prob = count / total
            entropy -= prob * math.log2(prob)
            
        return entropy
    
    def normalize_to_range(value: float, min_val: float, max_val: float) -> float:
        """Normalize a value to a 1-5 range."""
        if max_val == min_val:
            return 3  # Return middle value if all attributes have same entropy
        
        normalized = 1 + ((value - min_val) / (max_val - min_val)) * 4
        return round(normalized, 2)
    
    # Get all attributes except 'url'
    attributes = [key for key in data[0].keys() if key != 'url']
    
    # Calculate entropy for each attribute
    entropy_scores = {}
    for attr in attributes:
        # Flatten lists if attribute value is a list
        all_values = []
        for item in data:
            value = item[attr]
            if isinstance(value, list):
                all_values.extend(value)
            else:
                all_values.append(value)
        
        entropy_scores[attr] = calculate_entropy(all_values)
    
    # Normalize entropy scores to 1-5 range
    min_entropy = min(entropy_scores.values())
    max_entropy = max(entropy_scores.values())
    
    # Create final result
    result = [
        {
            'attribute': attr,
            'importance': normalize_to_range(score, min_entropy, max_entropy)
        }
        for attr, score in entropy_scores.items()
    ]
    
    # Sort by importance score in descending order
    result.sort(key=lambda x: x['importance'], reverse=True)
    
    return result