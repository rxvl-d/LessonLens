import logging
import math
from collections import Counter

from ll.classifiers import *

log = logging.getLogger(__name__)
            
class Summarizer:
    def summarize_gpt(self, search_query_history, serp_data):
        prompt = f"""
        Given a list of URLs, titles and summaries, 
        return the list of URLs tagged with various educational attributes.
        Also rate the importance of attributes given a search task.

        Search Task: {search_query_history}
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

    def summarize_v4(self, query, serp_data):
        summary = [extract_general_attributes(result) for result in serp_data]
        attr_importances = calculate_attribute_importance(summary)
        out = {'query_type': None, 
               'tagged_urls': summary, 
               'attribute_importances': attr_importances}
        return out

def calculate_attribute_importance(data):
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


def extract_general_attributes(result: dict) -> dict:
    """Extract general attributes that apply to all educational resources"""
    url = result.get("url", "")
    title = result.get("title", "")
    description = result.get("description", "")
    
    return {
        'url': url,
        'is_commercial': commercial_classifier(url, title, description),
        'is_educational': page_classifier(url, title, description),
        'educational_level': ed_level_classifier(url, title, description),
        'audience': audience_classifier(url, title, description),
        'source_institution_type': source_classifier(url, title, description)
    }
