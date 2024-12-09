from ll.classifiers import *

class MetadataEnricher:
    def __init__(self, web_page_cache):
        self.web_page_cache = web_page_cache
    
    def enrich(self, serp_data):
        metadatas = []
        hit = 0
        total = 0
        for r in serp_data:
            metadata_part = {}
            metadata_part['url'] = url = r['url']
            title = r['title']
            description = r['description']
            content = self.web_page_cache.fetch_text(url) 
            if content:
              content = content[:5000]
              hit += 1
            else:
              fallback_content = f"Title: {title}\nDescription: {description}"
              content = fallback_content
            total += 1
            response = content_based_gpt_metadata_inference(content)
            metadata_part['assesses'] = response['assesses']
            metadata_part['teaches'] = response['teaches']
            metadata_part['educational_level'] = response['educational_level']
            metadata_part['educational_role'] = response['educational_role']
            metadata_part['educational_use'] = response['educational_use']
            metadata_part['learning_resource_type'] = response['learning_resource_type']
            metadatas.append(metadata_part)
        
        print("-----------")
        print(hit/total)
        print("-----------")
        return metadatas