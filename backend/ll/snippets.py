from ll.classifiers import content_based_learning_goal_classifier

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
            x = content_based_learning_goal_classifier(url)
            if (type(x) == str):
              summary_part['enhanced_snippet'] = x
            else:
              summary_part['enhanced_snippet'] = ','.join(x)
            snippets.append(summary_part)
        return snippets