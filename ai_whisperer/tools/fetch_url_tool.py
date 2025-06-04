"""
Module: ai_whisperer/tools/fetch_url_tool.py
Purpose: AI tool implementation for fetch url

This module implements an AI-usable tool that extends the AITool
base class. It provides structured input/output handling and
integrates with the OpenRouter API for AI model interactions.

Key Components:
- FetchURLTool: Tool for fetching and processing web page content.

Usage:
    tool = FetchURLTool()
    result = await tool.execute(**parameters)

Dependencies:
- logging
- time
- tempfile

Related:
- See PHASE_CONSOLIDATED_SUMMARY.md

"""

import logging
import re
import hashlib
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timedelta
import requests
from urllib.parse import urlparse, urljoin

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.utils.path import PathManager

logger = logging.getLogger(__name__)

class FetchURLTool(AITool):
    """Tool for fetching and processing web page content."""
    
    # Configuration
    REQUEST_TIMEOUT = 15  # seconds
    MAX_CONTENT_LENGTH = 500000  # 500KB max
    CACHE_DIR = "web_fetch_cache"
    CACHE_TTL_HOURS = 48  # Cache for 48 hours
    
    def __init__(self):
        """Initialize fetch URL tool."""
        super().__init__()
        self._init_cache()
    
    def _init_cache(self):
        """Initialize cache directory."""
        try:
            path_manager = PathManager.get_instance()
            if path_manager.output_path:
                self.cache_path = Path(path_manager.output_path) / self.CACHE_DIR
                self.cache_path.mkdir(exist_ok=True)
            else:
                # Fallback to temp directory
                import tempfile
                self.cache_path = Path(tempfile.gettempdir()) / "aiwhisperer_fetch_cache"
                self.cache_path.mkdir(exist_ok=True)
        except:
            self.cache_path = None
    
    @property
    def name(self) -> str:
        return "fetch_url"
    
    @property
    def description(self) -> str:
        return "Fetch and extract content from web URLs."
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to fetch"
                },
                "extract_mode": {
                    "type": "string",
                    "description": "Content extraction mode",
                    "enum": ["markdown", "text", "code_blocks"],
                    "default": "markdown"
                },
                "include_links": {
                    "type": "boolean",
                    "description": "Include hyperlinks in markdown mode",
                    "default": False
                }
            },
            "required": ["url"]
        }
    
    @property
    def category(self) -> Optional[str]:
        return "Research"
    
    @property
    def tags(self) -> List[str]:
        return ["research", "web", "external", "content"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the 'fetch_url' tool to fetch and extract content from web pages.
        Parameters:
        - url (string, required): The URL to fetch
        - extract_mode (string, optional): "markdown", "text", or "code_blocks" (default: "markdown")
        - include_links (boolean, optional): Include links in markdown (default: false)
        
        This tool converts HTML to readable format for analysis.
        Example usage:
        <tool_code>
        fetch_url(url="https://docs.python.org/3/library/functools.html")
        fetch_url(url="https://example.com/tutorial", extract_mode="code_blocks")
        </tool_code>
        """
    
    def _get_cache_key(self, url: str) -> str:
        """Generate cache key for URL."""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _get_cached_content(self, cache_key: str) -> Optional[str]:
        """Get cached content if available."""
        if not self.cache_path:
            return None
        
        cache_file = self.cache_path / f"{cache_key}.txt"
        if not cache_file.exists():
            return None
        
        try:
            # Check if cache is expired
            mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - mtime > timedelta(hours=self.CACHE_TTL_HOURS):
                cache_file.unlink()
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return None
    
    def _save_to_cache(self, cache_key: str, content: str):
        """Save content to cache."""
        if not self.cache_path:
            return
        
        cache_file = self.cache_path / f"{cache_key}.txt"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(content)
        except:
            pass
    
    def _html_to_markdown(self, html: str, base_url: str, include_links: bool) -> str:
        """Convert HTML to markdown format."""
        # Remove script and style elements
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<noscript[^>]*>.*?</noscript>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # Convert headers
        for i in range(6, 0, -1):
            html = re.sub(f'<h{i}[^>]*>(.*?)</h{i}>', f'\n\n{"#" * i} \\1\n\n', html, flags=re.IGNORECASE | re.DOTALL)
        
        # Convert paragraphs
        html = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\n\1\n\n', html, flags=re.IGNORECASE | re.DOTALL)
        
        # Convert lists
        html = re.sub(r'<li[^>]*>(.*?)</li>', r'\n- \1', html, flags=re.IGNORECASE | re.DOTALL)
        html = re.sub(r'<ul[^>]*>', '\n', html, flags=re.IGNORECASE)
        html = re.sub(r'</ul>', '\n', html, flags=re.IGNORECASE)
        html = re.sub(r'<ol[^>]*>', '\n', html, flags=re.IGNORECASE)
        html = re.sub(r'</ol>', '\n', html, flags=re.IGNORECASE)
        
        # Convert code blocks
        html = re.sub(r'<pre[^>]*><code[^>]*>(.*?)</code></pre>', r'\n```\n\1\n```\n', html, flags=re.IGNORECASE | re.DOTALL)
        html = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', html, flags=re.IGNORECASE | re.DOTALL)
        
        # Convert links
        if include_links:
            def replace_link(match):
                href = match.group(1)
                text = match.group(2)
                absolute_url = urljoin(base_url, href)
                return f'[{text}]({absolute_url})'
            
            html = re.sub(r'<a[^>]*href=["\'](.*?)["\'][^>]*>(.*?)</a>', replace_link, html, flags=re.IGNORECASE | re.DOTALL)
        else:
            html = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', html, flags=re.IGNORECASE | re.DOTALL)
        
        # Convert emphasis
        html = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', html, flags=re.IGNORECASE | re.DOTALL)
        html = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', html, flags=re.IGNORECASE | re.DOTALL)
        html = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', html, flags=re.IGNORECASE | re.DOTALL)
        html = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', html, flags=re.IGNORECASE | re.DOTALL)
        
        # Convert line breaks
        html = re.sub(r'<br[^>]*>', '\n', html, flags=re.IGNORECASE)
        html = re.sub(r'<hr[^>]*>', '\n---\n', html, flags=re.IGNORECASE)
        
        # Remove remaining HTML tags
        html = re.sub(r'<[^>]+>', '', html)
        
        # Clean up entities
        html = html.replace('&nbsp;', ' ')
        html = html.replace('&amp;', '&')
        html = html.replace('&lt;', '<')
        html = html.replace('&gt;', '>')
        html = html.replace('&quot;', '"')
        html = html.replace('&#39;', "'")
        html = html.replace('&mdash;', '—')
        html = html.replace('&ndash;', '–')
        
        # Clean up whitespace
        html = re.sub(r'\n\s*\n\s*\n', '\n\n', html)
        html = re.sub(r' +', ' ', html)
        
        return html.strip()
    
    def _extract_code_blocks(self, html: str) -> List[Dict[str, str]]:
        """Extract code blocks from HTML."""
        code_blocks = []
        
        # Find <pre><code> blocks
        pre_code_pattern = r'<pre[^>]*><code[^>]*class=["\'](.*?)["\'][^>]*>(.*?)</code></pre>'
        for match in re.finditer(pre_code_pattern, html, re.DOTALL | re.IGNORECASE):
            language = match.group(1).split()[-1] if match.group(1) else 'text'
            code = match.group(2)
            # Clean up code
            code = re.sub(r'<[^>]+>', '', code)
            code = code.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
            code_blocks.append({'language': language, 'code': code.strip()})
        
        # Also find standalone <code> blocks that look substantial
        code_pattern = r'<code[^>]*>(.*?)</code>'
        for match in re.finditer(code_pattern, html, re.DOTALL | re.IGNORECASE):
            code = match.group(1)
            if '\n' in code:  # Multi-line code blocks
                code = re.sub(r'<[^>]+>', '', code)
                code = code.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                code_blocks.append({'language': 'text', 'code': code.strip()})
        
        return code_blocks
    
    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute URL fetching."""
        url = arguments.get('url')
        extract_mode = arguments.get('extract_mode', 'markdown')
        include_links = arguments.get('include_links', False)
        
        if not url:
            return {
                "error": "'url' is required.",
                "url": None,
                "content": None
            }
        
        # Validate URL
        try:
            parsed = urlparse(url)
            if not parsed.scheme:
                url = 'https://' + url
                parsed = urlparse(url)
            
            if parsed.scheme not in ['http', 'https']:
                return {
                    "error": "Only HTTP(S) URLs are supported.",
                    "url": url,
                    "content": None
                }
        except:
            return {
                "error": "Invalid URL format.",
                "url": url,
                "content": None
            }
        
        try:
            # Check cache first
            cache_key = self._get_cache_key(url)
            cached_content = self._get_cached_content(cache_key)
            
            if cached_content:
                content = cached_content
                from_cache = True
            else:
                # Fetch the URL
                headers = {
                    'User-Agent': 'Mozilla/5.0 (compatible; AIWhisperer/1.0)'
                }
                
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=self.REQUEST_TIMEOUT,
                    stream=True
                )
                
                if response.status_code != 200:
                    return {
                        "error": f"HTTP {response.status_code} - {response.reason}",
                        "url": url,
                        "status_code": response.status_code,
                        "content": None
                    }
                
                # Check content length
                content_length = response.headers.get('Content-Length')
                if content_length and int(content_length) > self.MAX_CONTENT_LENGTH:
                    return {
                        "error": f"Content too large ({int(content_length)} bytes)",
                        "url": url,
                        "content_length": int(content_length),
                        "max_allowed": self.MAX_CONTENT_LENGTH,
                        "content": None
                    }
                
                # Read content with size limit
                content = ""
                size = 0
                for chunk in response.iter_content(chunk_size=8192, decode_unicode=True):
                    if chunk:
                        # Handle both string and bytes
                        if isinstance(chunk, bytes):
                            try:
                                chunk = chunk.decode('utf-8')
                            except UnicodeDecodeError:
                                chunk = chunk.decode('utf-8', errors='replace')
                        content += chunk
                        size += len(chunk)
                        if size > self.MAX_CONTENT_LENGTH:
                            return {
                                "error": f"Content too large (>{self.MAX_CONTENT_LENGTH} bytes)",
                                "url": url,
                                "size": size,
                                "max_allowed": self.MAX_CONTENT_LENGTH,
                                "content": None
                            }
                
                # Save to cache
                self._save_to_cache(cache_key, content)
                from_cache = False
            
            # Extract content based on mode
            extracted_content = None
            truncated = False
            
            if extract_mode == 'markdown':
                markdown_content = self._html_to_markdown(content, url, include_links)
                extracted_content = markdown_content[:10000]  # Limit output
                truncated = len(markdown_content) > 10000
                
            elif extract_mode == 'text':
                # Simple text extraction
                text_content = re.sub(r'<[^>]+>', '', content)
                text_content = text_content.replace('&nbsp;', ' ').replace('&amp;', '&')
                text_content = re.sub(r'\s+', ' ', text_content).strip()
                extracted_content = text_content[:10000]
                truncated = len(text_content) > 10000
                
            elif extract_mode == 'code_blocks':
                code_blocks = self._extract_code_blocks(content)
                # Return structured code blocks
                extracted_content = code_blocks[:20]  # Limit to 20 blocks
                truncated = len(code_blocks) > 20
            
            return {
                "url": url,
                "extract_mode": extract_mode,
                "from_cache": from_cache,
                "content": extracted_content,
                "content_length": len(content),
                "truncated": truncated,
                "include_links": include_links
            }
            
        except requests.Timeout:
            return {
                "error": f"Request timed out after {self.REQUEST_TIMEOUT} seconds.",
                "url": url,
                "timeout": self.REQUEST_TIMEOUT,
                "content": None
            }
        except requests.RequestException as e:
            return {
                "error": f"Error fetching URL: {str(e)}",
                "url": url,
                "content": None
            }
        except Exception as e:
            logger.error(f"Error fetching URL {url}: {e}")
            return {
                "error": f"Error processing content: {str(e)}",
                "url": url,
                "content": None
            }
