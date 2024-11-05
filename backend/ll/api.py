from flask import Blueprint

api = Blueprint('api', __name__)

@api.route('/summary')
def summary():
    return {'topics': {'topic1': 1, 'topic2': 2, 'topic3': 3}, 
            'educational_levels': {'level1': 1, 'level2': 2, 'level3': 3},
            'resource_types': {'type1': 1, 'type2': 2, 'type3': 3}}