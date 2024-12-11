import json
from openai import OpenAI
import os
import numpy as np
import random
import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
import logging

log = logging.getLogger("classifiers")

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

def resource_types(content):
    return random.choices([''])

def learning_goals(content):
    return random.choices([''])

gdf = pd.read_pickle('data/metadata.pkl')

def content_based_ed_level_classifier(url):
  df = gdf[gdf.url == url]
  if df.shape[0] > 0:
    return df.iloc[0].educational_levels
  else:
    return "Unclear"

def content_based_learning_goal_classifier(url):
  df = gdf[gdf.url == url]
  if df.shape[0] > 0:
    return df.iloc[0].learning_goals
  else:
    return "Unclear"

def content_based_learning_resource_classifier(url):
  df = gdf[gdf.url == url]
  if df.shape[0] > 0:
    return df.iloc[0].learning_resource_types
  else:
    return "Unclear"

from ll.cache import URLLevelCache
url_cache = URLLevelCache()
client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
import json
import re

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

def content_based_gpt_metadata_inference(url, content):
  response_text = url_cache.get_or_fetch(url, content, fetch_content_based_gpt_metadata_inference)
  if response_text:
    return parse_json(response_text)
  else:
    return None

def get_gpt4_labels(prompt):
    response = client_openai.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    response_text = response.choices[0].message.content
    return response_text

def fetch_content_based_gpt_adaptive_snippet(content_dims):
  content, relevance_dimensions = content_dims
  prompt = f"""
  Respond to the following questions given the following content.
  
  Content:
  {content} 

  Questions:
  {relevance_dimensions}

  Repond in JSON format with a list of 3 answers. Keep the answers to one sentence each and brief.
  """
  try:
    response = get_gpt4_labels(prompt)
    summary_response = get_gpt4_labels(f"""
        Summarize this down to two sentences and use simlple html tags like bold, underline and italics to highlight the important parts for a teacher searching.
        Content: {response}
        Respond with a json object with the key: summary.""")
    return summary_response
  except Exception as e:
    print(e)
    return None
  
def content_based_adaptive_snippet(url, content, relevance_dimensions):
  response_text =url_cache.get_or_fetch((url,tuple(relevance_dimensions)), (content, relevance_dimensions), fetch_content_based_gpt_adaptive_snippet)
  if response_text:
    return parse_json(response_text).get('summary')
  else:
    return None

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
    """

    try:
        response = get_gpt4_labels(prompt)
        return response
    except Exception as e:
        print(e)
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
