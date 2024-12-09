from ll.classifiers import *

class MetadataEnricher:
    def __init__(self, web_page_cache):
        self.web_page_cache = web_page_cache
    
    def enrich(self, serp_data):
        summary = []
        for r in serp_data:
            summary_part = {}
            summary_part['url'] = url = r['url']
            summary_part['title'] = title = r['title']
            summary_part['description'] = description = r['description']
            summary_part['content'] = content = self.web_page_cache.fetch_text(url)
            summary_part['is_commercial'] = commercial_classifier(url, title, description, content)
            summary_part['educational_news_sales'] = page_classifier(url, title, description, content)
            summary_part['audience'] = audience_classifier(url, title, description, content)
            summary_part['source_institution_type'] = source_classifier(url, title, description, content)
            summary_part['education_level'] = content_based_ed_level_classifier(url)
            # summary_part['learning_goals'] = content_based_learning_goal_classifier(url)
            summary_part['educational_resource_types'] = content_based_learning_resource_classifier(url)
            summary.append(summary_part)
        return summary