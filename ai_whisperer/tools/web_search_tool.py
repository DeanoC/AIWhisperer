"""
Module: ai_whisperer/tools/web_search_tool.py
Purpose: AI tool implementation for web search

This module implements an AI-usable tool that extends the AITool
base class. It provides structured input/output handling and
integrates with the OpenRouter API for AI model interactions.

Key Components:
- WebSearchTool: Tool for searching the web for technical information and best practices.

Usage:
    tool = WebSearchTool()
    result = await tool.execute(**parameters)

Dependencies:
- logging
- time
- tempfile

Related:
- See PHASE_CONSOLIDATED_SUMMARY.md

"""

import logging
import json
import hashlib
import urllib.parse
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timedelta
import requests

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.utils.path import PathManager

logger = logging.getLogger(__name__)

class WebSearchTool(AITool):
    """Tool for searching the web for technical information and best practices."""
    
    # Cache configuration
    CACHE_DIR = "web_search_cache"
    CACHE_TTL_HOURS = 24  # Cache results for 24 hours
    MAX_RESULTS = 10
    REQUEST_TIMEOUT = 10  # seconds
    
    # Using DuckDuckGo HTML API (no API key required)
    SEARCH_URL = "https://html.duckduckgo.com/html/"
    
    def __init__(self):
        """Initialize web search tool."""
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
                self.cache_path = Path(tempfile.gettempdir()) / "aiwhisperer_web_cache"
                self.cache_path.mkdir(exist_ok=True)
        except:
            # If all else fails, disable caching
            self.cache_path = None
    
    @property
    def name(self) -> str:
        return "web_search"
    
    @property
    def description(self) -> str:
        return "Search the web for technical information, best practices, and documentation."
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 10
                },
                "focus": {
                    "type": "string",
                    "description": "Focus area for search",
                    "enum": ["general", "documentation", "tutorial", "best_practices", "github"],
                    "default": "general"
                }
            },
            "required": ["query"]
        }
    
    @property
    def category(self) -> Optional[str]:
        return "Research"
    
    @property
    def tags(self) -> List[str]:
        return ["research", "web", "external", "documentation"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the 'web_search' tool to search for technical information and best practices.
        Parameters:
        - query (string, required): Search query
        - max_results (integer, optional): Max results (1-10, default: 5)
        - focus (string, optional): Focus area (general, documentation, tutorial, best_practices, github)
        
        This tool helps find external information about technologies and implementations.
        Example usage:
        <tool_code>
        web_search(query="Python caching best practices")
        web_search(query="React authentication tutorial", focus="tutorial")
        web_search(query="FastAPI project structure", max_results=3)
        </tool_code>
        """
    
    def _get_cache_key(self, query: str, focus: str) -> str:
        """Generate cache key for query."""
        key_string = f"{query.lower()}_{focus}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cached_results(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached results if available and not expired."""
        if not self.cache_path:
            return None
        
        cache_file = self.cache_path / f"{cache_key}.json"
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            
            # Check if cache is expired
            cached_time = datetime.fromisoformat(cached_data['timestamp'])
            if datetime.now() - cached_time > timedelta(hours=self.CACHE_TTL_HOURS):
                cache_file.unlink()  # Delete expired cache
                return None
            
            return cached_data['results']
        except:
            return None
    
    def _save_to_cache(self, cache_key: str, results: Dict[str, Any]):
        """Save results to cache."""
        if not self.cache_path:
            return
        
        cache_file = self.cache_path / f"{cache_key}.json"
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'results': results
        }
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except:
            pass
    
    def _enhance_query(self, query: str, focus: str) -> str:
        """Enhance query based on focus area."""
        enhancements = {
            'documentation': f'{query} documentation official docs',
            'tutorial': f'{query} tutorial guide how to',
            'best_practices': f'{query} best practices patterns recommended',
            'github': f'{query} github repository example implementation'
        }
        
        return enhancements.get(focus, query)
    
    def _parse_duckduckgo_html(self, html_content: str) -> List[Dict[str, str]]:
        """Parse DuckDuckGo HTML results."""
        results = []
        
        # Simple HTML parsing without BeautifulSoup
        # Look for result snippets
        import re
        
        # Pattern to find result blocks
        result_pattern = r'<div class="result__body">(.*?)</div>'
        title_pattern = r'<a[^>]*class="result__a"[^>]*>(.*?)</a>'
        url_pattern = r'<a[^>]*class="result__a"[^>]*href="([^"]*)"'
        snippet_pattern = r'<a class="result__snippet"[^>]*>(.*?)</a>'
        
        # Find all result blocks
        result_blocks = re.findall(result_pattern, html_content, re.DOTALL)
        
        for i, block in enumerate(result_blocks[:self.MAX_RESULTS]):
            try:
                # Extract title
                title_match = re.search(title_pattern, block)
                title = title_match.group(1) if title_match else f"Result {i+1}"
                title = re.sub(r'<[^>]+>', '', title)  # Remove HTML tags
                
                # Extract URL
                url_match = re.search(url_pattern, block)
                url = url_match.group(1) if url_match else ""
                url = urllib.parse.unquote(url)
                
                # Extract snippet
                snippet_match = re.search(snippet_pattern, block)
                snippet = snippet_match.group(1) if snippet_match else "No description available"
                snippet = re.sub(r'<[^>]+>', '', snippet)  # Remove HTML tags
                snippet = snippet.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                
                if url:  # Only add if we have a URL
                    results.append({
                        'title': title.strip(),
                        'url': url,
                        'snippet': snippet.strip()
                    })
            except:
                continue
        
        return results
    
    def _search_duckduckgo(self, query: str) -> List[Dict[str, str]]:
        """Perform search using DuckDuckGo HTML interface."""
        try:
            # Prepare request
            params = {
                'q': query,
                'ia': 'web'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Make request
            response = requests.post(
                self.SEARCH_URL,
                data=params,
                headers=headers,
                timeout=self.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                return self._parse_duckduckgo_html(response.text)
            else:
                logger.error(f"Search failed with status {response.status_code}")
                return []
                
        except requests.Timeout:
            logger.error("Search request timed out")
            return []
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute web search."""
        query = arguments.get('query')
        max_results = arguments.get('max_results', 5)
        focus = arguments.get('focus', 'general')
        
        if not query:
            return {
                "error": "'query' is required.",
                "query": None,
                "results": []
            }
        
        # Limit max results
        max_results = min(max_results, self.MAX_RESULTS)
        
        try:
            # Check cache first
            cache_key = self._get_cache_key(query, focus)
            cached_results = self._get_cached_results(cache_key)
            
            if cached_results:
                results = cached_results
                from_cache = True
            else:
                # Enhance query based on focus
                enhanced_query = self._enhance_query(query, focus)
                
                # Perform search
                results = self._search_duckduckgo(enhanced_query)
                
                # Save to cache
                self._save_to_cache(cache_key, results)
                from_cache = False
            
            # Limit to requested number
            limited_results = results[:max_results] if results else []
            
            return {
                "query": query,
                "enhanced_query": enhanced_query if not from_cache else query,
                "focus": focus,
                "from_cache": from_cache,
                "total_results": len(limited_results),
                "max_results": max_results,
                "results": limited_results
            }
            
        except Exception as e:
            logger.error(f"Error executing web search: {e}")
            return {
                "error": f"Error performing web search: {str(e)}",
                "query": query,
                "results": []
            }
