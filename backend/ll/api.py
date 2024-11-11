from flask import Blueprint, request, jsonify

from ll.summary import classify_serp_results

api = Blueprint('api', __name__)

@api.route('/summary', methods=['POST', 'OPTIONS'])
def summary():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Accept')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response
    elif request.method == 'POST':
        print(request.json)
        return classify_serp_results(request.json)