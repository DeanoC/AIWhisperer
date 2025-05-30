"""Unit tests for web research tools."""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
from datetime import datetime, timedelta

from ai_whisperer.tools.web_search_tool import WebSearchTool
from ai_whisperer.tools.fetch_url_tool import FetchURLTool
from ai_whisperer.path_management import PathManager


class TestWebSearchTool:
    """Test WebSearchTool functionality."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def search_tool(self, temp_cache_dir):
        """Create tool instance with mocked PathManager."""
        with patch('ai_whisperer.path_management.PathManager.get_instance') as mock_pm:
            mock_instance = Mock()
            mock_instance.output_path = temp_cache_dir
            mock_pm.return_value = mock_instance
            
            tool = WebSearchTool()
            yield tool
    
    def test_tool_properties(self, search_tool):
        """Test tool properties."""
        assert search_tool.name == "web_search"
        assert "Search the web" in search_tool.description
        assert search_tool.category == "Research"
        assert "research" in search_tool.tags
        assert "web" in search_tool.tags
    
    @patch('requests.post')
    def test_basic_search(self, mock_post, search_tool):
        """Test basic web search functionality."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
        <div class="result__body">
            <a class="result__a" href="https://example.com/python-caching">Python Caching Guide</a>
            <a class="result__snippet">Learn about caching in Python with examples</a>
        </div>
        <div class="result__body">
            <a class="result__a" href="https://docs.python.org/3/library/functools.html">functools Documentation</a>
            <a class="result__snippet">The functools module includes lru_cache decorator</a>
        </div>
        '''
        mock_post.return_value = mock_response
        
        result = search_tool.execute({"query": "Python caching"})
        
        assert "Python Caching Guide" in result
        assert "https://example.com/python-caching" in result
        assert "Learn about caching" in result
        assert "functools Documentation" in result
        
        # Verify request was made
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]['data']['q'] == "Python caching"
    
    @patch('requests.post')
    def test_search_with_focus(self, mock_post, search_tool):
        """Test search with focus parameter."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<div class="result__body"></div>'
        mock_post.return_value = mock_response
        
        search_tool.execute({
            "query": "FastAPI",
            "focus": "documentation"
        })
        
        # Should enhance query for documentation
        call_args = mock_post.call_args
        assert "documentation" in call_args[1]['data']['q']
        assert "official docs" in call_args[1]['data']['q']
    
    def test_cache_functionality(self, search_tool, temp_cache_dir):
        """Test caching of search results."""
        # First search - should hit network
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '''
            <div class="result__body">
                <a class="result__a" href="https://example.com">Test Result</a>
                <a class="result__snippet">Test snippet</a>
            </div>
            '''
            mock_post.return_value = mock_response
            
            result1 = search_tool.execute({"query": "test query"})
            assert "Test Result" in result1
            assert "(Results from cache)" not in result1
            mock_post.assert_called_once()
        
        # Second search - should use cache
        with patch('requests.post') as mock_post:
            result2 = search_tool.execute({"query": "test query"})
            assert "Test Result" in result2
            assert "(Results from cache)" in result2
            mock_post.assert_not_called()
    
    @patch('requests.post')
    def test_search_error_handling(self, mock_post, search_tool):
        """Test error handling in search."""
        # Test timeout - should return empty results, not error message
        mock_post.side_effect = Exception("Connection timeout")
        
        result = search_tool.execute({"query": "test"})
        assert "No results found" in result  # Empty results returned on error
    
    @patch('requests.post')
    def test_no_results(self, mock_post, search_tool):
        """Test handling of no results."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<html><body>No results</body></html>'
        mock_post.return_value = mock_response
        
        result = search_tool.execute({"query": "very obscure query"})
        assert "No results found" in result
        assert "Simplifying your query" in result
    
    def test_max_results_limit(self, search_tool):
        """Test max results parameter."""
        with patch('requests.post') as mock_post:
            # Create many results
            results_html = ""
            for i in range(20):
                results_html += f'''
                <div class="result__body">
                    <a class="result__a" href="https://example.com/{i}">Result {i}</a>
                    <a class="result__snippet">Snippet {i}</a>
                </div>
                '''
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = results_html
            mock_post.return_value = mock_response
            
            # Request only 3 results
            result = search_tool.execute({
                "query": "test",
                "max_results": 3
            })
            
            # Should only show 3 results
            assert "1. Result 0" in result
            assert "2. Result 1" in result
            assert "3. Result 2" in result
            assert "4. Result 3" not in result


class TestFetchURLTool:
    """Test FetchURLTool functionality."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def fetch_tool(self, temp_cache_dir):
        """Create tool instance."""
        with patch('ai_whisperer.path_management.PathManager.get_instance') as mock_pm:
            mock_instance = Mock()
            mock_instance.output_path = temp_cache_dir
            mock_pm.return_value = mock_instance
            
            tool = FetchURLTool()
            yield tool
    
    def test_tool_properties(self, fetch_tool):
        """Test tool properties."""
        assert fetch_tool.name == "fetch_url"
        assert "Fetch and extract content" in fetch_tool.description
        assert fetch_tool.category == "Research"
        assert "content" in fetch_tool.tags
    
    @patch('requests.get')
    def test_fetch_markdown(self, mock_get, fetch_tool):
        """Test fetching and converting to markdown."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Length': '1000'}
        mock_response.iter_content = lambda chunk_size, decode_unicode: [
            '''<html>
            <body>
                <h1>Test Page</h1>
                <p>This is a <strong>test</strong> paragraph.</p>
                <ul>
                    <li>Item 1</li>
                    <li>Item 2</li>
                </ul>
                <pre><code>def hello():
    print("Hello")</code></pre>
            </body>
            </html>'''.encode()
        ]
        mock_get.return_value = mock_response
        
        result = fetch_tool.execute({
            "url": "https://example.com",
            "extract_mode": "markdown"
        })
        
        assert "# Test Page" in result
        assert "This is a **test** paragraph" in result
        assert "- Item 1" in result
        assert "- Item 2" in result
        assert "```" in result
        assert 'def hello():' in result
    
    @patch('requests.get')
    def test_fetch_code_blocks(self, mock_get, fetch_tool):
        """Test extracting code blocks."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Length': '500'}
        mock_response.iter_content = lambda chunk_size, decode_unicode: [
            '''<html>
            <body>
                <pre><code class="language-python">
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)
                </code></pre>
                <pre><code class="language-javascript">
function hello() {
    console.log("Hello");
}
                </code></pre>
            </body>
            </html>'''.encode()
        ]
        mock_get.return_value = mock_response
        
        result = fetch_tool.execute({
            "url": "https://example.com",
            "extract_mode": "code_blocks"
        })
        
        assert "Code Blocks Found:" in result
        assert "def factorial(n):" in result
        assert "function hello()" in result
        # Should find the language classes
        assert "language-python" in result or "python" in result
        assert "language-javascript" in result or "javascript" in result
    
    @patch('requests.get')
    def test_url_validation(self, mock_get, fetch_tool):
        """Test URL validation and normalization."""
        # Test adding https://
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.iter_content = lambda chunk_size, decode_unicode: [b"content"]
        mock_get.return_value = mock_response
        
        result = fetch_tool.execute({"url": "example.com"})
        
        # Should add https://
        mock_get.assert_called()
        call_url = mock_get.call_args[0][0]
        assert call_url == "https://example.com"
    
    def test_cache_functionality(self, fetch_tool, temp_cache_dir):
        """Test content caching."""
        # First fetch
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.iter_content = lambda chunk_size, decode_unicode: [b"<p>Test content</p>"]
            mock_get.return_value = mock_response
            
            result1 = fetch_tool.execute({"url": "https://example.com"})
            assert "Test content" in result1
            assert "(Content from cache)" not in result1
            mock_get.assert_called_once()
        
        # Second fetch - should use cache
        with patch('requests.get') as mock_get:
            result2 = fetch_tool.execute({"url": "https://example.com"})
            assert "Test content" in result2
            assert "(Content from cache)" in result2
            mock_get.assert_not_called()
    
    @patch('requests.get')
    def test_error_handling(self, mock_get, fetch_tool):
        """Test error handling."""
        # Test 404
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_get.return_value = mock_response
        
        result = fetch_tool.execute({"url": "https://example.com/notfound"})
        assert "Error: HTTP 404 - Not Found" in result
        
        # Test timeout
        mock_get.side_effect = Exception("Connection timeout")
        result = fetch_tool.execute({"url": "https://example.com"})
        assert "Error processing content" in result
    
    @patch('requests.get')
    def test_content_size_limit(self, mock_get, fetch_tool):
        """Test content size limiting."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Length': '1000000'}  # 1MB
        mock_get.return_value = mock_response
        
        result = fetch_tool.execute({"url": "https://example.com"})
        assert "Error: Content too large" in result
    
    @patch('requests.get')
    def test_include_links_option(self, mock_get, fetch_tool):
        """Test include_links option."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.iter_content = lambda chunk_size, decode_unicode: [
            b'<a href="/page">Link Text</a>'
        ]
        mock_get.return_value = mock_response
        
        # Without include_links
        result = fetch_tool.execute({
            "url": "https://example.com",
            "include_links": False
        })
        assert "Link Text" in result
        assert "[Link Text]" not in result
        
        # With include_links
        result = fetch_tool.execute({
            "url": "https://example.com",
            "include_links": True
        })
        assert "[Link Text](https://example.com/page)" in result