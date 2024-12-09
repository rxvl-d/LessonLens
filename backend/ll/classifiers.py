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
  