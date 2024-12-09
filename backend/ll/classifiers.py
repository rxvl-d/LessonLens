import json
import openai
import os
import numpy as np
import random
import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC

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
    domain = url.split('//')[1].split('/')[0]
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

from ll.cache import PromptLevelCache
prompt_cache = PromptLevelCache()

def content_based_gpt_metadata_inference(content):
  return prompt_cache.get_or_fetch(content, fetch_content_based_gpt_metadata_inference)

def fetch_content_based_gpt_metadata_inference(content):
    openai.api_key = os.getenv("OPENAI_API_KEY")

    prompt = f"""
    Extract educational metadata from the following content based on LRMI definitions. 
    Use these fields:
    1. assesses (string): What skills or knowledge does this resource evaluate?
    2. teaches (string): What skills or knowledge does this resource impart?
    3. educational_level (list): Relevant levels from [Grundschule, Sek. I, Sek. II, Higher Education].
    4. educational_role (list): Applicable roles from [student, teacher, administrator, mentor, instructional_designer, parent_guardian, researcher, support_staff].
    5. educational_use (list): Applicable uses are [""" + ','.join([u['use'] for u in EDUCATIONAL_USES])+ """].
    6. learning_resource_type (list): Applicable types such as [exercise, simulation, questionnaire, diagram, etc.].

    Content:
    {content}

    Respond only in JSON format with the fields: "assesses", "teaches", "educational_level", "educational_role", "educational_use", and "learning_resource_type".
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an educational metadata extractor."},
                {"role": "user", "content": prompt}
            ]
        )

        # Parse and return the JSON response
        metadata = json.loads(response["choices"][0]["message"]["content"])
        return metadata

    except Exception as e:
        print(e)
        return None

def content_based_educational_use_classifier(url):
  random.choice([u['use'] for u in EDUCATIONAL_USES])
  
# Predefined list of educational uses
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

# Prompt template for LLM
EDUCATIONAL_USE_PROMPT = """
Given the following content, identify the most appropriate educational use(s) from the predefined list below. Consider the content's purpose, structure, and intended learning outcomes.

Content to analyze:
{content}

Predefined educational uses:
{uses}

Please return a list of the most appropriate educational uses that apply to this content, ranked by relevance. For each identified use, provide a brief explanation of why it fits.

Format your response as:
1. [Educational Use]: [Explanation]
2. [Educational Use]: [Explanation]
(etc.)
"""

def get_educational_use_prompt(content):
    """
    Generate a formatted prompt for identifying educational uses in given content
    
    Args:
        content (str): The educational content to analyze
        
    Returns:
        str: Formatted prompt for LLM
    """
    # Format the uses list for the prompt
    uses_list = "\n".join([f"- {use['use']}: {use['description']}" 
                          for use in EDUCATIONAL_USES])
    
    # Format the complete prompt
    return EDUCATIONAL_USE_PROMPT.format(
        content=content,
        uses=uses_list
    )