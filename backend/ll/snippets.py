from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import logging
from ll.classifiers import content_based_adaptive_snippet

class SnippetEnhancer:
    def __init__(self, web_page_cache):
        self.web_page_cache = web_page_cache
        

    def enhance(self, serp_data: List[Dict], relevance_dimensions: List[str]) -> List[Dict]:
        """
        Enhance search results by fetching and processing web pages in parallel.
        
        Args:
            serp_data: List of search result dictionaries containing url, title, and description
            relevance_dimensions: List of dimensions to consider for snippet generation
            
        Returns:
            List of enhanced snippets with additional context
        """
        def process_single_result(result: Dict) -> Dict:
            """Process a single search result and generate enhanced snippet."""
            summary_part = {
                'url': (url := result['url']),
                'title': (title := result['title']),
                'description': (description := result['description'])
            }
            
            try:
                content = self.web_page_cache.fetch_text(url)
                if content:
                    content = content[:5000]
                else:
                    content = f"Title: {title}\nDescription: {description}"
                    
                snippet = content_based_adaptive_snippet(url, content, relevance_dimensions)
                if snippet:
                    summary_part['enhanced_snippet'] = ". ".join([read_answer(s) for s in snippet])
                    return summary_part
                
            except Exception as e:
                logging.error(f"Error processing {url}: {str(e)}")
                return None
                
            return None

        # Use ThreadPoolExecutor since this is I/O bound
        snippets = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(process_single_result, result): result['url']
                for result in serp_data
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    snippet = future.result()
                    if snippet:
                        snippets.append(snippet)
                except Exception as e:
                    logging.error(f"Error processing future for {url}: {str(e)}")
                    continue

        return snippets

def read_answer(a):
  if type(a) == dict:
    return list(a.values())[0]
  elif type(a) == str:
    return a
  else:
    return str(a)