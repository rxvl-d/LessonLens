import json
from pathlib import Path
from flask import Blueprint, request, jsonify, Response

from ll.summary import Summarizer
from ll.metadata import MetadataEnricher
from ll.snippets import SnippetEnhancer
from ll.cache import WebPageCache
from ll.claude import EducationalLevel, Subject, ResourceType, Snippets
import logging

log = logging.getLogger(__name__)
api = Blueprint('api', __name__)
pages = WebPageCache()
educational_levels = EducationalLevel()
subjects = Subject()
resource_types = ResourceType()
snippets = Snippets()
summarizer = Summarizer(educational_levels, resource_types)
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

@api.route('/summary', methods=['POST', 'OPTIONS'])
def summary():
    if request.method == 'OPTIONS':
        return handle_options_request()
    elif request.method == 'POST':
        # response = summarizer.summarize(request.json)
        response = summarizer.summarize_v2(request.json['results'])
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
        response = snippets.enhance(request.json['results'])
        response = jsonify(response)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

@api.route('/metadata_v1', methods=['POST', 'OPTIONS'])
def metadata_v1():
    if request.method == 'OPTIONS':
        return handle_options_request()
    elif request.method == 'POST':
        urls = request.json.get('urls', [])
        urls_to_text = [{
            "url": url, 
            "content_type": "text", 
            "content": pages.cache(url)['text'][:Config.TEXT_LIMIT]} 
                        for url in urls]
        def to_map(data):
            return {d['url']: d['response'] for d in data}
        urls_to_educational_level = to_map(educational_levels.classify(urls_to_text))
        urls_to_resource_type = to_map(resource_types.classify(urls_to_text))
        urls_to_subject = to_map(subjects.classify(urls_to_text))
        results = [
            {'url': url, 
             'data': {
                 'educationalLevel': urls_to_educational_level[url],
                 'resourceType': urls_to_resource_type[url],
                 'subject': urls_to_subject[url]
                 }} for url in urls]
        response = jsonify({'results':results})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

        
@api.route('/enhanced-snippets_v1', methods=['POST', 'OPTIONS'])
def enhanced_snippets_v1():
    if request.method == 'OPTIONS':
        return handle_options_request()
    elif request.method == 'POST':
        urls = request.json.get('urls', [])
        task_desc = request.json.get('task_desc')
        assert task_desc is not None
        urls_to_text = [{
            "url": url, 
            "content_type": "text", 
            "content": pages.cache(url)['text'][:Config.TEXT_LIMIT],
            "facet": task_desc} 
                        for url in urls]
        def to_map(data):
            return {d['url']: d['response'] for d in data}
        urls_to_enhanced_snippet = to_map(snippets.enhance(urls_to_text, task_desc))
        results = [
            {'url': url, 
             'data': {
                 'enhancedSnippet': urls_to_enhanced_snippet.get(url),
                 }} for url in urls]
        response = jsonify({'results':results})
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
