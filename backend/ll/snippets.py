from ll.classifiers import content_based_adaptive_snippet

class SnippetEnhancer:
    def __init__(self, web_page_cache):
        self.web_page_cache = web_page_cache
        
    def enhance(self, serp_data, relevance_dimensions):
        snippets = []
        for r in serp_data:
            summary_part = {}
            summary_part['url'] = url = r['url']
            summary_part['title'] = title = r['title']
            summary_part['description'] = description = r['description']
            content = self.web_page_cache.fetch_text(url) 
            if content:
              content = content[:5000]
            else:
              fallback_content = f"Title: {title}\nDescription: {description}"
              content = fallback_content
            snippet = content_based_adaptive_snippet(content, relevance_dimensions)
            if snippet:
              summary_part['enhanced_snippet'] = ". ".join(snippet)
              snippets.append(summary_part)
        return snippets