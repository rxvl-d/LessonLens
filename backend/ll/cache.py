import json
import pickle
from pathlib import Path
import os
import hashlib
from PIL import Image
import trafilatura
import logging

log = logging.getLogger(__name__)
logging.getLogger("trafilatura").setLevel(logging.WARNING)

def hash(url):
    return hashlib.md5(url.encode()).hexdigest()
    

class WebPageCache:

    def __init__(self):
        self.cache_path = Path(os.getenv("HOME")) / '.cache' / 'LessonLens' / 'webpage_cache'
        self.cache_path.mkdir(exist_ok=True, parents=True)
    
    def _read_if_exists(self, path, read_as_image=False):
        if os.path.exists(path):    
            if read_as_image:
                return Image.open(path)
            else:   
                with open(path, 'r') as f:
                    return f.read()
        else:
            return None

    def _url_path(self, url):
        hashed = hash(url)
        path = self.cache_path / hashed
        path.mkdir(exist_ok=True)
        return path

    def _html_path(self, url):
        return self._url_path(url) / 'index.html'

    def _text_path(self, url):
        return self._url_path(url) / 'trafilatura.txt'
    
    def _screenshot_path(self, url):
        return self._url_path(url) / 'screenshot.png'

    def fetch(self, url):
        return {
            'html': self._read_if_exists(self._html_path(url)),
            'text': self._read_if_exists(self._text_path(url)),
            'screenshot': self._read_if_exists(self._screenshot_path(url), read_as_image=True),
        }

    def fetch_html(self, url):
        html_path = self._html_path(url)
        if not os.path.exists(html_path):
            html =trafilatura.fetch_url(url) or ""
            with open(html_path, 'w') as f:
                f.write(html)
        with open(html_path, 'r') as f:
            return f.read()

    def fetch_text(self, url):
        html_path = self._html_path(url)
        text_path = self._text_path(url)
        if not os.path.exists(html_path):
            log.warning(f"HTML not found for {url}")
            return None
        elif not os.path.exists(text_path):
            text=trafilatura.extract(self.fetch_html(url)) or ""
            with open(text_path, 'w') as f:
                f.write(text)
        with open(text_path, 'r') as f:
            return f.read()
            

    def cache(self, url):
        html = self.fetch_html(url)
        text = self.fetch_text(url)
        return {'html': html, 'text': text}

class PromptLevelCache:
    def __init__(self):
        self.cache_dir = Path(os.getenv("HOME")) / '.cache' / 'LessonLens'
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_path = self.cache_dir / 'claude_cache.pkl'
        self.cache = self._load_cache()

    def _load_cache(self):
        if self.cache_path.exists():
            with open(self.cache_path, 'rb') as f:
                self.cache = pickle.load(f)

    def _save_cache(self):
        with open(self.cache_path, 'wb') as f:
            pickle.dump(self.cache, f)

    def get(self, prompt):
        self._load_cache()
        return self.cache.get(prompt)

    def set(self, prompt, response):
        self.cache[prompt] = response
        self._save_cache()

    def get_or_fetch(self, prompt, fetch_fn):
        response = self.get(prompt)
        if response is None:
            response = fetch_fn(prompt)
            self.set(prompt, response)
        else:
            log.info(f"Cache hit for prompt: {prompt}")
        return response

class URLContentLevelCache:
    def __init__(self, label):
       self.label = label 
       self.cache_dir = Path(os.getenv("HOME")) / '.cache' / 'LessonLens' / label
       self.cache_dir.mkdir(exist_ok=True, parents=True)

    def _path(self, url, content_type):
        return self.cache_dir / hash(url+':'+content_type)

    def _load_cache(self, url, content_type):
        path = self._path(url, content_type)
        if path.exists():
            with open(path, 'r') as f:
                is_empty = f.read().strip() == ''
            if not is_empty:
                with open(path, 'r') as f:
                    return json.load(f)
            else:
                return None
        else:
            return None

    def _save_cache(self, url, content_type, data):
        path = self._path(url, content_type)
        with open(path, 'w') as f:
            json.dump(data, f)
    
    def get(self, url, content_type):
        return self._load_cache(url, content_type)
    
    def set(self, url, content_type, data):
        self._save_cache(url, content_type, data)

    def get_or_fetch_batch(self, batch, fetch_fn):
        to_fetch = list()
        from_cache = list()
        for url_data in batch:
            url = url_data['url']
            content_type = url_data['content_type']
            cached = self.get(url, content_type)
            if cached is not None:
                from_cache.append(cached)
                log.info(f"Cache hit for {url} {content_type}")
            else:
                to_fetch.append(url_data)
        if len(to_fetch) == 0:
            return from_cache
        classified = fetch_fn(to_fetch)
        def find_content_type(url):
            for url_data in to_fetch:
                if url_data['url'] == url:
                    return url_data['content_type']
        for url_data in classified:
            url = url_data['url']
            content_type = find_content_type(url)
            assert content_type is not None
            url_data['content_type'] = content_type
            self.set(url, content_type, url_data)
        return from_cache + classified 
