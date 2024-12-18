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

    def summarize_v4(self, query, search_task, serp_data):
        query_type, summary = process_search_results(query, search_task, serp_data)
        attr_importances = calculate_attribute_importance(summary)
        out = {'query_type': query_type, 'tagged_urls': summary, 'attribute_importances': attr_importances}
        return out

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
        out = {'tagged_urls': summary, 'attribute_importances': attr_importances}
        return out

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

    
def classify_query_type(query: str, search_task: str) -> str:
    """Determines the learning resource type based on query keywords"""
    
    # Dictionary mapping resource types to their identifying keywords
    type_keywords = {
        "worksheet": ["Arbeitsblatt", "Übungsblatt", "Aufgabenblatt", "Worksheet"],
        "experiment": ["Experiment", "Versuch", "Demonstration", "Laborversuch"],
        "teaching_method": ["Unterrichtsmethode", "didaktisch", "Methodik", "Lerntyp"],
        "assessment": ["Test", "Lernstandserhebung", "Diagnose", "Prüfung"],
        "didactic_concept": ["didaktische Konzepte", "Analogie", "Modell", "Konzeption"],
        "modeling_activity": ["Modellierung", "Aktivität", "Modell"]
    }
    
    # Count matches for each type
    type_matches = {
        type_name: sum(1 for keyword in keywords 
                      if keyword.lower() in (query + search_task).lower())
        for type_name, keywords in type_keywords.items()
    }
    
    # Return type with most matches, defaulting to "general" if no matches
    best_match = max(type_matches.items(), key=lambda x: x[1])
    return best_match[0] if best_match[1] > 0 else "general"

def determine_source_type(url: str) -> str:
    """Determine the source type from URL patterns"""
    url = url.lower()
    
    # University patterns
    if any(pattern in url for pattern in [
        '.edu', '.ac.', 'uni-', 'universitaet', 'universität', 
        'hochschule', '.tu-', 'fh-'
    ]):
        return "university"
        
    # Publisher patterns
    if any(pattern in url for pattern in [
        'verlag', 'persen.de', 'cornelsen', 'klett',
        'westermann', 'schulbuchzentrum', 'bildungsverlag'
    ]):
        return "publisher"
        
    # Educational portal patterns
    if any(pattern in url for pattern in [
        'leifiphysik', 'bildungsserver', 'schule', 
        'lehrerfortbildung', 'bildung-', '-bildung',
        'unterricht', 'lernportal', 'education'
    ]):
        return "educational_portal"
    
    # Default case
    return "other"

def process_search_results(query: str, search_task: str, results: list) -> dict:
    """Main function to process search results based on query type"""
    
    query_type = classify_query_type(query, search_task)
    
    # Dispatch to appropriate processor based on type
    processors = {
        "worksheet": extract_worksheet_attributes,
        "experiment": extract_experiment_attributes,
        "teaching_method": extract_teaching_method_attributes,
        "assessment": extract_assessment_attributes,
        "didactic_concept": extract_didactic_concept_attributes,
        "modeling_activity": extract_modeling_activity_attributes
    }
    
    processor = processors.get(query_type, extract_general_attributes)
    processor = extract_general_attributes
    
    tagged_urls = [processor(result) for result in results]
    return query_type, tagged_urls

def extract_experiment_attributes(result: dict) -> dict:
    """Extract attributes specific to experiment resources"""
    url = result.get("url", "")
    title = result.get("title", "")
    description = result.get("description", "")
    
    # Combined text for analysis
    text = f"{title} {description}".lower()
    
    return {
        "url": url,
        "is_experiment": 'Is Experiment' if any(term in text for term in ["experiment", "versuch", "demonstration"]) else 'Not Experiment',
        "contains_demonstration_terms": 'Is Demonstration' if any(term in text for term in ["demonstrieren", "demonstration", "vorführung"]) else 'Not Demonstration',
        "contains_hands_on_terms": 'Is Hands-On' if any(term in text for term in ["selber machen", "durchführen", "selbst"]) else 'Not Hands-On',
        "contains_equipment_mentions": extract_equipment_mentions(text),
        "source_type": determine_source_type(url)
    }


def extract_worksheet_attributes(result: dict) -> dict:
    """Extract attributes specific to worksheet resources"""
    url = result.get("url", "")
    title = result.get("title", "")
    description = result.get("description", "")
    text = f"{title} {description}".lower()
    
    return {
        "url": url,
        "is_worksheet": 'Is Worksheet' if any(term in text for term in ["arbeitsblatt", "übungsblatt", "aufgabenblatt"]) else 'Not Worksheet',
        "has_step_instructions": 'Scaffolded' if any(term in text for term in ["schritt", "anleitung", "schrittweise"]) else 'Not Scaffolded',
        "includes_solutions": 'Includes Solutions' if any(term in text for term in ["lösung", "musterlösung", "lösungsblatt"]) else 'No Solutions',
    }

def extract_teaching_method_attributes(result: dict) -> dict:
    """Extract attributes specific to teaching method resources"""
    url = result.get("url", "")
    title = result.get("title", "")
    description = result.get("description", "")
    text = f"{title} {description}".lower()
    
    return {
        "url": url,
        "differentiation_level": "Is Differentiated" if any(term in text for term in ["vereinfachung", "grundlegend", "angepasst", "differenziert", "leistungsschwach", "förderung"]) else "Not Differentiated",
        "includes_visual_aids": "Has Visual Aids" if any(term in text for term in ["visualisierung", "modell", "grafik"]) else "No Visual Aids",
        "teaching_method_type": extract_teaching_methods(text),
    }

def extract_assessment_attributes(result: dict) -> dict:
    """Extract attributes specific to assessment resources"""
    url = result.get("url", "")
    title = result.get("title", "")
    description = result.get("description", "")
    text = f"{title} {description}".lower()
    
    return {
        "url": url,
        "assessment_type": determine_assessment_type(text),
        "scoring_guide_included": "Scoring Guide Included" if any(term in text for term in ["bewertung", "auswertung", "punkteverteilung"]) else "No Scoring Guide",
        "question_types": extract_question_types(text),
    }

def extract_question_types(text: str) -> list:
   """Extract types of questions/problems mentioned in the text"""
   
   question_types = []
   
   type_patterns = {
       "multiple_choice": ["multiple choice", "mehrfachauswahl", "ankreuzaufgabe", "auswahlaufgabe"],
       "open_ended": ["offene frage", "freitext", "essay", "aufsatz", "beschreibung"],
       "calculation": ["berechnung", "rechenaufgabe", "berechne", "bestimme"],
       "matching": ["zuordnung", "verbinde", "ordne zu", "matching"],
       "fill_in": ["lückentext", "ergänze", "lückenfüllen", "vervollständige"],
       "diagram": ["zeichne", "skizziere", "diagramm", "grafik"],
       "true_false": ["richtig falsch", "wahr falsch", "ja nein", "stimmt nicht stimmt"]
   }
   
   text = text.lower()
   
   for qtype, patterns in type_patterns.items():
       if any(pattern in text for pattern in patterns):
           question_types.append(qtype)
           
   return question_types if question_types else ["unspecified"]

def extract_didactic_concept_attributes(result: dict) -> dict:
    """Extract attributes specific to didactic concept resources"""
    url = result.get("url", "")
    title = result.get("title", "")
    description = result.get("description", "")
    text = f"{title} {description}".lower()
    
    return {
        "url": url,
        "includes_analogies": "Includes Analogies" if any(term in text for term in ["analogie", "vergleich", "modell"]) else "No Analogies",
        "visualization_tools": "Includes Visualization Tools" if any(term in text for term in ["visualisierung", "darstellung", "veranschaulichung"]) else "No Visualization Tools",
        "curriculum_alignment": "Mentions Curriculum Alignment" if any(term in text for term in ["lehrplan", "bildungsstandard", "curriculum"]) else "No Curriculum Alignment",
    }

def extract_modeling_activity_attributes(result: dict) -> dict:
    """Extract attributes specific to modeling activity resources"""
    url = result.get("url", "")
    title = result.get("title", "")
    description = result.get("description", "")
    text = f"{title} {description}".lower()
    
    return {
        "url": url,
        "model_type": extract_model_types(text),
        "materials_required": "Materials Required" if any(term in text for term in ["material", "benötigt", "ausstattung"]) else "No Materials Required",
        "student_interaction_level": determine_interaction_level(text),
    }

def extract_teaching_methods(text: str) -> list:
    methods = []
    method_keywords = {
        "gruppenarbeit": ["gruppe", "gruppenarbeit"],
        "einzelarbeit": ["einzelarbeit", "individuell"],
        "stationenlernen": ["station", "lernstation"],
        "experiment": ["experiment", "versuch"]
    }
    for method, keywords in method_keywords.items():
        if any(keyword in text for keyword in keywords):
            methods.append(method)
    return methods

def determine_assessment_type(text: str) -> str:
    if any(term in text for term in ["diagnose", "eingangstest"]):
        return "diagnostic"
    elif any(term in text for term in ["formativ", "zwischentest"]):
        return "formative"
    elif any(term in text for term in ["abschlusstest", "klausur"]):
        return "summative"
    return "unspecified"

def determine_interaction_level(text: str) -> str:
    if any(term in text for term in ["gruppe", "team", "partner"]):
        return "group"
    elif any(term in text for term in ["klasse", "plenum"]):
        return "class"
    else:
        return "individual"

def extract_model_types(text: str) -> list:
    model_types = []
    type_keywords = {
        "physical": ["physisch", "haptisch"],
        "digital": ["digital", "simulation"],
        "conceptual": ["konzeptuell", "theoretisch"]
    }
    for model_type, keywords in type_keywords.items():
        if any(keyword in text for keyword in keywords):
            model_types.append(model_type)
    return model_types

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

def extract_equipment_mentions(text: str) -> list:
    """Extract mentions of scientific equipment from text"""
    
    # Common lab/experiment equipment in German
    equipment_terms = [
        # Basic lab equipment
        "reagenzglas", "becherglas", "erlenmeyerkolben", "messkolben", "pipette", 
        "bunsenbrenner", "stativ", "waage", "thermometer",
        
        # Electrical/physics equipment
        "batterie", "kabel", "stromquelle", "magnet", "kompass",
        "voltmeter", "amperemeter", "elektroskop", "elektrometer",
        "kondensator", "spule", "widerstand", "schalter",
        
        # Common household items often used in experiments
        "luftballon", "kerze", "spiegel", "linse", "glas",
        "plastikflasche", "alufolie", "papier", "gummiband",
        
        # Materials
        "kupferdraht", "eisendraht", "metallplatte", "glasstab", "kunststoffstab"
    ]
    
    # Find all equipment mentions in the text
    found_equipment = []
    for term in equipment_terms:
        if term in text.lower():
            found_equipment.append(term)
            
    return found_equipment