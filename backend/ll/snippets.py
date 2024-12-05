from ll.classifiers import learning_goals, resource_types

class SnippetEnhancer:
    def __init__(self, web_page_cache):
        self.web_page_cache = web_page_cache
        
    def enhance(self, serp_data):
        snippets = []
        for r in serp_data:
            summary_part = {}
            summary_part['url'] = url = r['url']
            summary_part['title'] = title = r['title']
            summary_part['description'] = description = r['description']
            summary_part['content'] = content = self.web_page_cache.fetch_text(url)
            summary_part['enhanced_snippet'] = learning_goals(content) + resource_types(content)
            snippets.append(summary_part)
        return snippets