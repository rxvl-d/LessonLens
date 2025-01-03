from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import logging
from ll.classifiers import content_based_adaptive_snippet, QuestionGenerator, RelevanceMatcher, classify_query_type

class SnippetEnhancer:
    def __init__(self, web_page_cache):
        self.relevance_matcher = RelevanceMatcher()
        self.question_generator = QuestionGenerator()
        self.web_page_cache = web_page_cache
        

    def enhance(self, serp_data: List[Dict], query: str) -> List[Dict]:
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
                    
                typed_terms = classify_query_type(query)
                dimensions = self.relevance_matcher.get_top_dimensions(typed_terms)
                questions = self.question_generator.\
                    generate_questions(typed_terms, [d[0] for d in dimensions])
                snippet = content_based_adaptive_snippet(url, content, questions)
                if snippet:
                    summary_part['enhanced_snippet'] = \
                      "<br/> ".join([qna(s) for s in snippet]) if type(snippet) == list else snippet
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
                for result in serp_data[:2]
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

def qna(a):
  if type(a) == dict and (set(a.keys()) == {'question', 'answer'}):
    return f"Q: {a['question']}<br/>A: <i>{a['answer']}</i>"
  else:
    return str(a)
    