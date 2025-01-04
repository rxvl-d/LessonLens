import json
from pathlib import Path
from flask import Blueprint, request, jsonify, Response

from ll.summary import Summarizer
from ll.metadata import MetadataEnricher
from ll.snippets import SnippetEnhancer
from ll.cache import WebPageCache
import logging

log = logging.getLogger(__name__)
api = Blueprint('api', __name__)
pages = WebPageCache()
summarizer = Summarizer()
metadata = MetadataEnricher(pages)
snippets = SnippetEnhancer(pages)

class Config:
    TEXT_LIMIT = 1000

def handle_options_request():
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Accept')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

@api.route('/ping', methods=['GET'])
def ping():
  return jsonify({'status': 'ok'})

@api.route('/summary', methods=['POST', 'OPTIONS'])
def summary():
    if request.method == 'OPTIONS':
        return handle_options_request()
    elif request.method == 'POST':
        response = summarizer.summarize_fast(request.json['results'])
        try:
            response_str = json.dumps(response, indent=2)
            jresponse = Response(response_str, mimetype='application/json')
        except Exception as e:
            log.error(f"Error in summarization", exc_info=e)
            jresponse = jsonify({'error': 'Error in summarization'})
        return jresponse
        
@api.route('/metadata', methods=['POST', 'OPTIONS'])
def metadata_endpoint():
    if request.method == 'OPTIONS':
        return handle_options_request()
    elif request.method == 'POST':
        response = metadata.enrich(request.json['results'])
        response = jsonify(response)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

@api.route('/enhanced-snippets', methods=['POST', 'OPTIONS'])
def enhanced_snippets():
    if request.method == 'OPTIONS':
        return handle_options_request()
    elif request.method == 'POST':
        response = snippets.enhance(request.json['results'], request.json['query'])
        response = jsonify(response)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

@api.route('/study-settings', methods=['OPTIONS', 'POST'])
def study_settings():
    if request.method == 'OPTIONS':
        return handle_options_request()
        
    profile_id = request.json.get('profile_id')
    if not profile_id:
        return jsonify({'error': 'Profile ID is required'}), 400
        
    settings_path = Path(__file__).parent.parent / 'data' / 'profiles' / f'{profile_id}.json'
    
    try:
        with open(settings_path, 'r') as f:
            settings = json.load(f)
            
        return jsonify(settings)
        
    except FileNotFoundError:
        return jsonify({'error': 'Profile not found'}), 404
    except json.JSONDecodeError as e:
        return jsonify({'error': 'Invalid settings file'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
