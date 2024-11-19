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
            print(resource_types)
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
                for typ in response:
                    resource_types_count[typ] = resource_types_count.get(typ, 0) + 1
            
            
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