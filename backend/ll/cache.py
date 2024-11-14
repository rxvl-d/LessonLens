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
