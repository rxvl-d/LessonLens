import random

def commercial_classifier(url, title, description, content=None):
    return random.choice([True, False])
            
def page_classifier(url, title, description, content=None):
    return random.choice(['Educational', 'News', 'e-Commerce', 'Other'])
            
def audience_classifier(url, title, description, content=None):
    return random.choice(['Teachers', 'Students', 'Other'])
            
def source_classifier(url, title, description, content=None):
    return random.choice(['School', 'University', 'Publisher', 'Teacher', 
                          'Non-Profit Foundation', 'For-Profit Company', 'Other'])
            
def ed_level_classifier(url, title, description, content=None):
    return random.choice(['Grundschule', 'Sek. I', 'Sek. II', 'Higher Education'])

def resource_types(content):
    return random.choices([''])

def learning_goals(content):
    return random.choices([''])