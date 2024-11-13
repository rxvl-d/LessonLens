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
        return classify_serp_results(request.json)

        
@api.route('/metadata', methods=['POST', 'OPTIONS'])
def metadata():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Accept')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response
    elif request.method == 'POST':
        urls = request.json.get('urls', [])
        
        # Generate dummy metadata for each URL
        metadata_list = []
        for url in urls:
            # Create varying dummy data based on the URL to simulate different results
            url_hash = hash(url) % 4  # Use URL to deterministically vary the response
            
            metadata = {
                'url': url,
                'data': {
                    'educationalLevel': [
                        # Vary educational levels based on URL
                        *(['9', '10'] if url_hash in [0, 2] else []),
                        *(['11', '12'] if url_hash in [1, 3] else []),
                        *(['Higher Education'] if url_hash == 2 else [])
                    ],
                    'resourceType': [
                        # Vary resource types based on URL
                        *(['Lesson Plan'] if url_hash in [0, 3] else []),
                        *(['Course'] if url_hash in [1, 2] else []),
                        *(['Activity'] if url_hash == 0 else []),
                        *(['Assessment'] if url_hash == 2 else [])
                    ],
                    'subject': [
                        # Vary subjects based on URL
                        *(['Mathematics'] if url_hash in [0, 2] else []),
                        *(['Physics'] if url_hash in [1, 3] else []),
                        *(['Computer Science'] if url_hash == 2 else []),
                        *(['Chemistry'] if url_hash == 0 else [])
                    ]
                }
            }
            metadata_list.append(metadata)

        response = jsonify({'results': metadata_list})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

        
@api.route('/enhanced-snippets', methods=['POST', 'OPTIONS'])
def enhanced_snippets():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Accept')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response
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