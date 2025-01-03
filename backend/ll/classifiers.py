from inspect import signature
import json
import re
from ll.cache import URLLevelCache
from pathlib import Path
import spacy
import json
from openai import OpenAI
import os
import numpy as np
import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
import logging

log = logging.getLogger("classifiers")

# SVM Classifiers for various metadata fields

# Training
def train():
    df = pd.read_pickle('../../tins/data/jupyter-caches/04-training-data.pkl')
    
    # Remove low frequency labels
    for col in ['commercial', 'source', 'type', 'audience', 'educational_level']:
        counts = df[col].value_counts()
        df = df[~df[col].isin(counts[counts < 5].index)]
    
    # Train source classifier separately with subword features
    train_source_classifier(df)
    
    # Train other classifiers with text features
    for col in ['commercial', 'type', 'audience', 'educational_level']:
        train_other_classifier(df, col)

def train_source_classifier(df):
    domains = df['url'].str.extract(r'https?://([^/]+)')[0]
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(analyzer='char', ngram_range=(3,5), max_features=5000)),
        ('svc', SVC(kernel='linear', C=10))
    ])
    pipeline.fit(domains[domains.notna()], df['source'][domains.notna()])
    with open('models/source_classifier.pkl', 'wb') as f:
        pickle.dump(pipeline, f)

def train_other_classifier(df, target_column):
    df['text'] = df['title'] + ' ' + df['description']
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=5000)),
        ('svc', SVC(kernel='linear'))
    ])
    pipeline.fit(df['text'], df[target_column])
    with open(f'models/{target_column}_classifier.pkl', 'wb') as f:
        pickle.dump(pipeline, f)

# Prediction
def predict_with_threshold(model, input_data, threshold=0.5):
    confidence_scores = model.decision_function(input_data)[0]
    max_confidence = confidence_scores if type(confidence_scores) is np.float64 else max(abs(confidence_scores))
    prediction = model.predict(input_data)[0]
    return 'Other' if max_confidence < threshold else prediction

def commercial_classifier(url, title, description, content=None):
    with open('models/commercial_classifier.pkl', 'rb') as f:
        model = pickle.load(f)
    text = f"{title} {description}"
    return predict_with_threshold(model, [text], threshold=0.7)

def source_classifier(url, title, description, content=None):
    with open('models/source_classifier.pkl', 'rb') as f:
        model = pickle.load(f)
    try:
        domain = url.split('//')[1].split('/')[0]
    except:
        log.error(f"Malformed URL: {url}")
        domain = "None"
    return predict_with_threshold(model, [domain], threshold=0.6)

def page_classifier(url, title, description, content=None):
    with open('models/type_classifier.pkl', 'rb') as f:
        model = pickle.load(f)
    text = f"{title} {description}"
    return predict_with_threshold(model, [text], threshold=0.7)

def audience_classifier(url, title, description, content=None):
    with open('models/audience_classifier.pkl', 'rb') as f:
        model = pickle.load(f)
    text = f"{title} {description}"
    return predict_with_threshold(model, [text], threshold=0.6)

def ed_level_classifier(url, title, description, content=None):
    with open('models/educational_level_classifier.pkl', 'rb') as f:
        model = pickle.load(f)
    text = f"{title} {description}"
    return predict_with_threshold(model, [text], threshold=0.5)

# GPT Based Classifiers

url_cache = URLLevelCache()
client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_gpt4_labels(prompt, fast=False):
    response = client_openai.chat.completions.create(
        model="gpt-3.5-turbo-0125" if fast else "gpt-4o-2024-08-06",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    response_text = response.choices[0].message.content
    return response_text

def parse_json(response_text):
    # Try to find JSON content between triple backticks
    code_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    code_matches = re.findall(code_pattern, response_text)
    
    # Try direct JSON pattern matching if no code blocks found
    json_pattern = r"\{[\s\S]*\}"
    
    for match in code_matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    # Try to find JSON directly in the text
    json_matches = re.findall(json_pattern, response_text)
    
    for match in json_matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
            
    # Clean up common LLM JSON formatting issues
    def clean_json_text(text):
        # Remove any leading/trailing whitespace and quotes
        text = text.strip().strip('"\'')
        # Replace unicode quotes with standard quotes
        text = text.replace('"', '"').replace('"', '"')
        # Replace single quotes with double quotes
        text = text.replace("'", '"')
        # Fix common boolean and null formatting
        text = re.sub(r'\bTrue\b', 'true', text)
        text = re.sub(r'\bFalse\b', 'false', text)
        text = re.sub(r'\bNone\b', 'null', text)
        return text
    
    # Try one more time with cleaned text
    try:
        cleaned_text = clean_json_text(response_text)
        if '{' in cleaned_text and '}' in cleaned_text:
            return json.loads(cleaned_text)
    except json.JSONDecodeError:
        pass
        
    return {}

# Metadata Snippet

def fetch_content_based_gpt_metadata_inference(content):
    prompt = """
    Extract educational metadata from the following content based on LRMI definitions. 
    Use these fields:
    1. assesses (string): What skills or knowledge does this resource evaluate?
    2. teaches (string): What skills or knowledge does this resource impart?
    3. educational_level (list): Relevant levels from [Grundschule, Sek. I, Sek. II, Higher Education].
    4. educational_role (list): Applicable roles from [student, teacher, administrator, mentor, instructional_designer, parent_guardian, researcher, support_staff].
    5. educational_use (list): Applicable uses are [""" + ','.join([u['use'] for u in EDUCATIONAL_USES])+ f"""].
    6. learning_resource_type (list): Applicable types such as [exercise, simulation, questionnaire, diagram, etc.].

    Content:
    {content}

    Respond only in JSON format with the fields: "assesses", "teaches", "educational_level", "educational_role", "educational_use", and "learning_resource_type".
    Respond in the same language as the content.
    """

    try:
        response = get_gpt4_labels(prompt)
        return parse_json(response)
    except Exception as e:
        print(e)
        return None

def content_based_gpt_metadata_inference(url, content):
  response_text = url_cache.get_or_fetch(url, content, fetch_content_based_gpt_metadata_inference)
  if response_text:
    return parse_json(response_text)
  else:
    return None


# Task Snippet
## Based on questions
def fetch_content_question_based_gpt_adaptive_snippet(content_questions):
  content, questions = content_questions
  prompt = f"""
  Respond to the following questions given the following content. 
  Respond in keywords and not full sentences.
  Respond in same language as the content. 
  Translate and paraphrase the question if needed.
  
  Content:
  {content} 

  Questions:
  {questions}

  Repond in JSON format with a list of objects with keys: question and answer. 
  Keep the answers to one sentence each and brief.
  """
  try:
    response = get_gpt4_labels(prompt)
    return parse_json(response)
  except Exception as e:
    return None

## Based on relevance dimensions
def fetch_content_relevance_dimension_based_gpt_adaptive_snippet(content_relevance_dimensions):
  content, relevance_dimensions = content_relevance_dimensions
  prompt = f"""
  Generate 3 questions and answers about the following content based on the relevance dimensions provided.
  i.e. given a relevance dimension like "Contains keywords/terms from the information need.", 
  generate a question and answer that would help a teacher understand if the content is relevant along that dimension.
  Keep the questions and answers short and use education specific terms.
  The answers should be in keywords and not full sentences.
  Questions and answers should be in the same language as the content.
  
  Content:
  {content} 

  Questions:
  {relevance_dimensions}

  Repond in JSON format with a list of objects with keys: question and answer. 
  Keep the answers to one sentence each and brief.
  """
  try:
    response = get_gpt4_labels(prompt)
    return parse_json(response)
  except Exception as e:
    return None

## Based on Queries
  
def fetch_content_queries_based_gpt_adaptive_snippet(content_queries):
  content, relevance_dimensions = content_queries
  prompt = f"""
  Generate 3 questions and answers about the following content based on the sequence of search queries.
  Use the search queries to infer the teachers' information need and generate questions based on that.
  Keep the questions and answers short and use education specific terms.
  The answers should be in keywords and not full sentences.
  Questions and answers should be in the same language as the content.
  
  Content:
  {content} 

  Questions:
  {relevance_dimensions}

  Repond in JSON format with a list of objects with keys: question and answer. 
  Keep the answers to one sentence each and brief.
  """
  try:
    response = get_gpt4_labels(prompt)
    return parse_json(response)
  except Exception as e:
    return None

def content_based_adaptive_snippet(url, content, questions):
  response_text = url_cache.get_or_fetch((url,tuple(questions)), 
                                        (content,questions), 
                                        fetch_content_question_based_gpt_adaptive_snippet)
  if response_text:
    return parse_json(response_text)
  else:
    return None

EDUCATIONAL_USES = [
    {
        "use": "assessment",
        "description": "For tests, quizzes, and evaluation purposes",
        "examples": ["tests", "quizzes", "exams", "evaluations", "self-assessment"]
    },
    {
        "use": "practice",
        "description": "For reinforcing skills through repetition",
        "examples": ["exercises", "drills", "practice problems", "worksheets"]
    },
    {
        "use": "tutorial",
        "description": "For direct instruction and guided learning",
        "examples": ["lessons", "guides", "walkthroughs", "demonstrations"]
    },
    {
        "use": "research",
        "description": "For investigation and inquiry-based learning",
        "examples": ["research projects", "investigations", "data analysis"]
    },
    {
        "use": "discussion",
        "description": "For promoting dialogue and critical thinking",
        "examples": ["debate topics", "discussion prompts", "conversation starters"]
    },
    {
        "use": "case_study",
        "description": "For analyzing real-world examples",
        "examples": ["case studies", "real-world scenarios", "practical examples"]
    },
    {
        "use": "laboratory",
        "description": "For hands-on experimentation",
        "examples": ["lab work", "experiments", "practical exercises"]
    },
    {
        "use": "presentation",
        "description": "For presenting information",
        "examples": ["slides", "demonstrations", "visual aids"]
    },
    {
        "use": "reference",
        "description": "For looking up information",
        "examples": ["reference materials", "glossaries", "guides"]
    },
    {
        "use": "simulation",
        "description": "For practicing in simulated environments",
        "examples": ["simulations", "virtual labs", "role-playing scenarios"]
    },
    {
        "use": "collaborative",
        "description": "For group learning activities",
        "examples": ["group projects", "team activities", "peer learning"]
    },
    {
        "use": "flipped_learning",
        "description": "For self-paced pre-class preparation",
        "examples": ["pre-class materials", "self-study resources", "preparatory content"]
    }
]

LEARNING_RESOURCE_TYPES = ["exercise", "simulation", "questionnaire", "diagram", "figure", "graph", 
                           "index", "slide", "table", "descriptive_text", "article", "exam", 
                           "experiment", "hands on activity" "example", "equation", "worksheet", 
                           "problem_statement", "assessment", "lecture", "case study", "definition", 
                           "illustration", "demonstration", "simulation", "interactive activity", "video"]

def load_query_term_model():
    model_path = 'models/query_term_classification'
    if not Path(model_path).exists():
        raise ValueError(f"Model path {model_path} does not exist")
    nlp = spacy.load(model_path)
    return nlp

ner_model = load_query_term_model()


def classify_query_type(query):
    return [(e.text, e.label_) for e in ner_model(query).ents]



class QuestionGenerator:
    def __init__(self):
        self.question_templates = {
            'Motivation': [
                lambda topic: f"How does the material engage and motivate students in learning about {topic}?"
            ],
            'Concepts': [
                lambda topic: f"What key concepts and terms related to {topic} are covered in the material?"
            ],
            'Background': [
                lambda topic: f"What background information or foundational concepts about {topic} are provided?"
            ],
            'Grade level': [
                lambda context: f"How well does the content's complexity align with {context} requirements?"
            ],
            'Non-textuals': [
                lambda topic: f"What visual aids, diagrams, or other non-textual elements are used to explain {topic}?"
            ],
            'Examples': [
                lambda topic: f"What real-world examples or applications of {topic} are included?"
            ],
            'Hands-on': [
                lambda topic: f"What hands-on activities or interactive exercises about {topic} are provided?"
            ],
            'Attachments': [
                lambda topic: f"What supplementary materials (worksheets, rubrics, assessments) are included for teaching {topic}?"
            ],
            'References': [
                lambda topic: f"What additional resources or references are provided for further exploration of {topic}?"
            ],
            'Learning Goals': [
                lambda topic: f"What specific learning objectives or skills are students expected to master regarding {topic}?"
            ],
            'Learning Organization': [
                lambda topic: f"How is the content structured to achieve the learning objectives for {topic}?"
            ],
            'Publisher Prestige': [
                lambda publisher: f"What is {publisher}'s reputation and track record in producing educational materials?"
            ]
        }
        
    def generate_questions(self, typed_terms, top_dimensions):
        questions = []
        entity_dict = {term_type: term for (term, term_type) in typed_terms}
        
        for dimension in top_dimensions:
            if dimension in self.question_templates:
                template = self.question_templates[dimension][0]  # Take first template
                params = signature(template).parameters
                try:
                    if len(params) == 2:  # Template needs both topic and context
                        question = template(
                            entity_dict.get('topic', 'the subject'),
                            entity_dict.get('context', 'this grade level')
                        )
                    elif 'topic' in params:
                        question = template(entity_dict.get('topic', 'the subject'))
                    elif 'context' in params:
                        question = template(entity_dict.get('context', 'this grade level'))
                    elif 'publisher' in params:
                        question = template(entity_dict.get('publisher', 'this publisher'))
                    else:
                        question = template()
                        
                    questions.append(question)
                except Exception as e:
                    continue
                    
        return questions

class RelevanceMatcher:
    def __init__(self):
        # Define dimension descriptions
        self.dimension_descriptions = {
            'Motivation': 'Materials that are motivating or stimulating to students.',
            'Concepts': 'Contains keywords/terms from the information need.',
            'Background': 'Provides relevant background material.',
            'Grade level': 'Is appropriate for the grade level in the information need.',
            'Non-textuals': 'Has non-textual items pertaining to the information need.',
            'Examples': 'Has real-world examples pertaining to the information need.',
            'Hands-on': 'Has hands-on activities pertaining to the information need.',
            'Attachments': 'Has attachments; e.g. score sheets, rubrics, test questions, etc.',
            'References': 'Has references or internet links to relevant material elsewhere.',
            'Learning Goals': 'Mentions the knowledge and skills a student is expected to acquire over the course of using it.',
            'Learning Organization': 'The document is structured according to its learning goals.',
            'Publisher Prestige': 'The document\'s publisher is recognizable and is prestigious and trustworthy.'
        }
        
        # Define dimension weights and mappings
        self.dimension_weights = {
            'publisher': {
                'Publisher Prestige': 0.8
            },
            'topic': {
                'Concepts': 1.0,
                'Background': 0.7,
                'Examples': 0.8,
                'Learning Goals': 0.9,
                'Learning Organization': 0.7
            },
            'material_type': {
                'Non-textuals': 0.7,
                'Examples': 0.7,
                'Hands-on': 0.8,
                'Attachments': 0.6,
                'References': 0.5
            },
            'context': {
                'Grade level': 1.0,
                'Motivation': 0.9
            }
        }
        
    def score_dimensions(self, terms):
        # Initialize scores for all dimensions
        dimension_scores = {
            'Motivation': 0,
            'Concepts': 0,
            'Background': 0,
            'Grade level': 0,
            'Non-textuals': 0,
            'Examples': 0,
            'Hands-on': 0,
            'Attachments': 0,
            'References': 0,
            'Learning Goals': 0,
            'Learning Organization': 0,
            'Publisher Prestige': 0
        }
        
        # Calculate scores based on entities
        for (term, term_type) in terms:
            if term_type in self.dimension_weights:
                for dimension, weight in self.dimension_weights[term_type].items():
                    dimension_scores[dimension] += weight
                    
        # Normalize scores
        max_score = max(dimension_scores.values())
        if max_score > 0:
            dimension_scores = {k: v/max_score for k, v in dimension_scores.items()}
            
        return dimension_scores
    
    def get_top_dimensions(self, typed_terms, n = 4):
        # Get scores and sort by value
        scores = self.score_dimensions(typed_terms)
        sorted_dimensions = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return top n dimensions with descriptions
        return [(dim, self.dimension_descriptions[dim]) for dim, score in sorted_dimensions[:n]]
