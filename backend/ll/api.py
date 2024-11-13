from flask import Blueprint, request, jsonify

from ll.summary import classify_serp_results
from ll.cache import WebPageCache
from ll.claude import EducationalLevel, Subject, ResourceType

api = Blueprint('api', __name__)
pages = WebPageCache()
educational_levels = EducationalLevel()
subjects = Subject()
resource_types = ResourceType()

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
        return classify_serp_results(request.json)

        
@api.route('/metadata', methods=['POST', 'OPTIONS'])
def metadata():
    if request.method == 'OPTIONS':
        return handle_options_request()
    elif request.method == 'POST':
        urls = request.json.get('urls', [])
        urls_to_text = {url: pages.cache(url)['text'][:Config.TEXT_LIMIT] for url in urls}
        urls_to_educational_level = educational_levels.classify(urls_to_text)
        urls_to_resource_type = resource_types.classify(urls_to_text)
        urls_to_subject = subjects.classify(urls_to_text)
        assert set(urls) == set(urls_to_educational_level.keys())
        assert set(urls) == set(urls_to_resource_type.keys())
        assert set(urls) == set(urls_to_subject.keys())
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

        
@api.route('/enhanced-snippets', methods=['POST', 'OPTIONS'])
def enhanced_snippets():
    if request.method == 'OPTIONS':
        return handle_options_request()
    elif request.method == 'POST':
        urls = request.json.get('urls', [])
        
        # Generate simple enhanced snippets for each URL
        snippets_list = []
        for url in urls:
            snippet_data = {
                'url': url,
                'data': {
                    'enhancedSnippet': "This is an enhanced search result snippet that provides a better description of the page content. It should be more informative than the original snippet."
                }
            }
            snippets_list.append(snippet_data)

        response = jsonify({'results': snippets_list})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response