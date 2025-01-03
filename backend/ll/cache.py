import hashlib
import json
import logging
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, Optional

import pypdf
import requests
import trafilatura
from docx import Document
from PIL import Image

log = logging.getLogger("cache")
logging.getLogger("trafilatura").setLevel(logging.FATAL)
logging.getLogger("urllib3").setLevel(logging.FATAL)

def hash(url):
    return hashlib.md5(str(url).encode()).hexdigest()
    

class WebPageCache:
    def __init__(self, cache_dir: str = 'data/webpage_cache', 
                 request_timeout: int = 30,
                 head_timeout: int = 10):
        """
        Initialize WebPageCache with configurable timeouts and cache directory.
        
        Args:
            cache_dir: Base directory for cached files
            request_timeout: Timeout for content download requests in seconds
            head_timeout: Timeout for HEAD requests in seconds
        """
        self.cache_path = Path(cache_dir)
        self.cache_path.mkdir(exist_ok=True, parents=True)
        self.request_timeout = request_timeout
        self.head_timeout = head_timeout
        self.hit = 0
        self.miss = 0
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        
    def _url_to_path(self, url: str) -> Path:
        """Generate a unique path for a URL using SHA-256 hashing."""
        hashed = hashlib.sha256(url.encode()).hexdigest()
        path = self.cache_path / hashed
        path.mkdir(exist_ok=True)
        return path
        
    def _get_content_type(self, url: str) -> Optional[str]:
        """Determine content type using HEAD request."""
        try:
            head_response = requests.head(url, timeout=self.head_timeout)
            return head_response.headers.get('content-type', '').split(';')[0]
        except requests.RequestException as e:
            self.logger.error(f"HEAD request failed for {url}: {e}")
            return None
            
    def _get_file_extension(self, content_type: str) -> str:
        """Map content type to file extension."""
        content_type_map = {
            'text/html': 'html',
            'application/pdf': 'pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx'
        }
        return content_type_map.get(content_type, 'html')
        
    def _read_if_exists(self, path: Path, read_as_image: bool = False) -> Optional[Any]:
        """Read file if it exists, with support for different file types."""
        if not path.exists():
            return None
            
        try:
            if read_as_image:
                return Image.open(path)
            elif path.suffix == '.pdf':
                with open(path, 'rb') as f:
                    reader = pypdf.PdfReader(f)
                    return ' '.join(page.extract_text() for page in reader.pages)
            elif path.suffix == '.docx':
                doc = Document(path)
                return ' '.join(paragraph.text for paragraph in doc.paragraphs)
            else:
                return path.read_text(encoding='utf-8')
        except Exception as e:
            self.logger.error(f"Error reading {path}: {e}")
            return None
            
    def _download_file(self, url: str, content_type: str) -> Optional[str]:
        """Download file from URL and save with appropriate extension."""
        try:
            response = requests.get(url, timeout=self.request_timeout)
            response.raise_for_status()
            
            ext = self._get_file_extension(content_type)
            path = self._url_to_path(url) / f'content.{ext}'
            
            # Write binary content for PDFs and DOCXs
            if ext in ['pdf', 'docx']:
                path.write_bytes(response.content)
            else:
                path.write_text(response.text, encoding='utf-8')
                
            return str(path)
        except requests.RequestException as e:
            self.logger.error(f"Failed to download {url}: {e}")
            return None
            
    def _extract_text(self, path: Path, content_type: str) -> Optional[str]:
        """Extract text content based on file type."""
        try:
            if content_type == 'text/html':
                html_content = path.read_text(encoding='utf-8')
                return trafilatura.extract(html_content) or ""
            else:
                return self._read_if_exists(path)
        except Exception as e:
            self.logger.error(f"Error extracting text from {path}: {e}")
            return None
            
    def fetch(self, url: str) -> Dict[str, Optional[str]]:
        """
        Fetch content from URL or cache, handling different file types.
        
        Returns:
            Dictionary containing original content and extracted text
        """
        content_type = self._get_content_type(url)
        if not content_type:
            return {'content': None, 'text': None}
            
        url_path = self._url_to_path(url)
        ext = self._get_file_extension(content_type)
        content_path = url_path / f'content.{ext}'
        text_path = url_path / 'extracted_text.txt'
        
        # Check if content exists in cache
        if not content_path.exists():
            self.miss += 1
            content_file = self._download_file(url, content_type)
            if not content_file:
                return {'content': None, 'text': None}
        else:
            self.hit += 1
            
        # Log cache hit rate every 10 requests
        if (self.hit + self.miss) % 10 == 0:
            self.logger.info(f"Cache hit rate: {self.hit / (self.hit + self.miss):.2%}")
            
        # Extract and cache text if needed
        if not text_path.exists():
            text_content = self._extract_text(content_path, content_type)
            if text_content:
                text_path.write_text(text_content, encoding='utf-8')
                
        return {
            'content': self._read_if_exists(content_path),
            'text': self._read_if_exists(text_path)
        }

class URLLevelCache:
    def __init__(self):
        self.cache_dir = Path(os.getenv("HOME")) / '.cache' / 'LessonLens' / 'url_cache'
        self.cache_dir.mkdir(exist_ok=True)

    def _get(self, key):
        path = self.cache_dir / hash(key) + '.json' 
        with open(path, 'r') as f:
            out = json.load(f)
        return out

    def _set(self, key, response):
        with open(self.cache_dir / hash(key) + '.json', 'w') as f:
            json.dump(response, f)

    def get_or_fetch(self, key, input, fetch_fn):
        if os.path.exists(self.cache_dir / hash(key) + '.json'):
            self._get(key)
        else:
            response = fetch_fn(input)
            self._set(key, response)
            return response