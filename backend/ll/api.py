from flask import Blueprint, request, jsonify

api = Blueprint('api', __name__)

@api.route('/summary', methods=['POST', 'OPTIONS'])
def summary():
    print(request.method)
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Accept')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response
    return {'topics': {'topic1': 1, 'topic2': 2, 'topic3': 3}, 
            'educational_levels': {'level1': 1, 'level2': 2, 'level3': 3},
            'resource_types': {'type1': 1, 'type2': 2, 'type3': 3}}