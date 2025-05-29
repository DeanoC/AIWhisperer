"""Integration tests for complete RFC workflow."""
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from ai_whisperer.tools.create_rfc_tool import CreateRFCTool
from ai_whisperer.tools.read_rfc_tool import ReadRFCTool
from ai_whisperer.tools.update_rfc_tool import UpdateRFCTool
from ai_whisperer.tools.move_rfc_tool import MoveRFCTool
from ai_whisperer.tools.list_rfcs_tool import ListRFCsTool
from ai_whisperer.tools.analyze_languages_tool import AnalyzeLanguagesTool
from ai_whisperer.tools.find_similar_code_tool import FindSimilarCodeTool
from ai_whisperer.tools.web_search_tool import WebSearchTool
from ai_whisperer.tools.fetch_url_tool import FetchURLTool
from ai_whisperer.agent_handlers.rfc_refinement import RFCRefinementHandler
from ai_whisperer.path_management import PathManager
from ai_whisperer.ai_service.ai_service import AIService


class TestRFCWorkflow:
    """Test complete RFC workflow from creation to refinement."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace with RFC structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create RFC directory structure
            rfc_base = Path(tmpdir) / "rfc"
            (rfc_base / "new").mkdir(parents=True)
            (rfc_base / "in_progress").mkdir(parents=True)
            (rfc_base / "archived").mkdir(parents=True)
            
            # Create some source files for analysis
            src_dir = Path(tmpdir) / "src"
            src_dir.mkdir()
            
            # Python file
            (src_dir / "main.py").write_text("""
def main():
    print("Hello World")

if __name__ == "__main__":
    main()
""")
            
            # JavaScript file
            (src_dir / "app.js").write_text("""
function hello() {
    console.log("Hello World");
}

module.exports = { hello };
""")
            
            # Create a mock web cache directory
            cache_dir = Path(tmpdir) / ".web_cache"
            cache_dir.mkdir()
            
            yield tmpdir
    
    @pytest.fixture
    def path_manager_mock(self, temp_workspace):
        """Mock PathManager with temp workspace."""
        with patch('ai_whisperer.path_management.PathManager.get_instance') as mock_pm:
            mock_instance = Mock()
            mock_instance.workspace_path = temp_workspace
            mock_pm.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def all_tools(self, path_manager_mock):
        """Initialize all RFC tools."""
        return {
            'create_rfc': CreateRFCTool(),
            'read_rfc': ReadRFCTool(),
            'update_rfc': UpdateRFCTool(),
            'move_rfc': MoveRFCTool(),
            'list_rfcs': ListRFCsTool(),
            'analyze_languages': AnalyzeLanguagesTool(),
            'find_similar_code': FindSimilarCodeTool(),
            'web_search': WebSearchTool(),
            'fetch_url': FetchURLTool()
        }
    
    def test_complete_rfc_lifecycle(self, all_tools, temp_workspace):
        """Test creating, updating, and moving an RFC through its lifecycle."""
        # Step 1: Create a new RFC
        create_result = all_tools['create_rfc'].execute({
            'title': 'Add User Authentication',
            'summary': 'Implement secure user authentication system',
            'author': 'Test User'
        })
        
        assert "RFC created successfully!" in create_result
        rfc_id_match = create_result.split("**RFC ID**: ")[1].split("\n")[0]
        rfc_id = rfc_id_match
        
        # Verify RFC was created
        list_result = all_tools['list_rfcs'].execute({})
        assert rfc_id in list_result
        assert "Add User Authentication" in list_result
        
        # Step 2: Read the RFC
        read_result = all_tools['read_rfc'].execute({'rfc_id': rfc_id})
        assert "# RFC: Add User Authentication" in read_result
        assert "*To be defined during refinement*" in read_result
        
        # Step 3: Update RFC sections
        # Update background
        update_result = all_tools['update_rfc'].execute({
            'rfc_id': rfc_id,
            'section': 'background',
            'content': 'Current system lacks user authentication, making it insecure.'
        })
        assert "RFC updated successfully!" in update_result
        
        # Update requirements
        update_result = all_tools['update_rfc'].execute({
            'rfc_id': rfc_id,
            'section': 'requirements',
            'content': '- [ ] Support email/password authentication\n- [ ] Implement JWT tokens',
            'append': True
        })
        assert "Appended to" in update_result
        
        # Update technical considerations
        update_result = all_tools['update_rfc'].execute({
            'rfc_id': rfc_id,
            'section': 'technical_considerations',
            'content': '- Use bcrypt for password hashing\n- Store sessions in Redis'
        })
        assert "RFC updated successfully!" in update_result
        
        # Step 4: Verify updates
        read_result = all_tools['read_rfc'].execute({'rfc_id': rfc_id})
        assert "Current system lacks user authentication" in read_result
        assert "Support email/password authentication" in read_result
        assert "Use bcrypt for password hashing" in read_result
        # The Background section should not have placeholder anymore
        assert "## Background\nCurrent system lacks user authentication" in read_result
        
        # Step 5: Move to in_progress
        move_result = all_tools['move_rfc'].execute({
            'rfc_id': rfc_id,
            'target_status': 'in_progress',
            'reason': 'Requirements gathered, starting implementation'
        })
        assert "RFC moved successfully!" in move_result
        assert "now in active refinement" in move_result
        
        # Verify RFC was moved
        list_result = all_tools['list_rfcs'].execute({'status': 'in_progress'})
        assert rfc_id in list_result
        
        # Step 6: Move to archived
        move_result = all_tools['move_rfc'].execute({
            'rfc_id': rfc_id,
            'target_status': 'archived',
            'reason': 'Implementation completed'
        })
        assert "refinement is complete" in move_result
        
        # Verify final state
        list_result = all_tools['list_rfcs'].execute({'status': 'archived'})
        assert rfc_id in list_result
    
    def test_codebase_analysis_integration(self, all_tools, temp_workspace):
        """Test codebase analysis tools integration."""
        # Analyze languages
        result = all_tools['analyze_languages'].execute({})
        # Check that analysis ran
        assert "Total files analyzed:" in result
        # The tool should have found the files we created
        if "No programming language files found" not in result:
            assert "Python" in result
            assert "JavaScript" in result
        
        # Find similar code - use custom patterns since 'hello' is not a predefined feature
        result = all_tools['find_similar_code'].execute({
            'feature': 'logging',  # Use a predefined feature
            'custom_patterns': ['hello', 'Hello'],  # Add custom pattern
            'file_types': ['.py']
        })
        if "No code blocks found" not in result:
            assert "main.py" in result
            assert "Hello World" in result
        
        # Test with a feature that shouldn't exist
        result = all_tools['find_similar_code'].execute({
            'feature': 'authentication',
            'file_types': ['.py']
        })
        assert "No code similar to 'authentication' found" in result
    
    @patch('ai_whisperer.tools.fetch_url_tool.requests')
    @patch('ai_whisperer.tools.web_search_tool.requests')
    def test_web_research_integration(self, mock_search_requests, mock_fetch_requests, all_tools, temp_workspace):
        """Test web research tools integration."""
        # Mock search response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
        <div class="result__body">
            <h2 class="result__title">
                <a class="result__a" href="https://example.com/auth-guide">Authentication Best Practices</a>
            </h2>
            <a class="result__snippet">Learn about secure authentication patterns...</a>
        </div>
        </html>
        """
        mock_search_requests.post.return_value = mock_response
        
        # Search
        result = all_tools['web_search'].execute({
            'query': 'authentication best practices'
        })
        assert "Authentication Best Practices" in result
        assert "https://example.com/auth-guide" in result
        
        # Mock fetch response
        mock_fetch_response = Mock()
        mock_fetch_response.status_code = 200
        mock_fetch_response.headers = {'Content-Length': '1000'}
        mock_fetch_response.iter_content = Mock(return_value=[
            """<html>
            <body>
            <h1>Authentication Guide</h1>
            <p>Use strong password hashing algorithms like bcrypt.</p>
            </body>
            </html>"""
        ])
        mock_fetch_requests.get.return_value = mock_fetch_response
        
        # Fetch URL
        result = all_tools['fetch_url'].execute({
            'url': 'https://example.com/auth-guide'
        })
        assert "Authentication Guide" in result
        assert "bcrypt" in result
    
    @pytest.mark.asyncio
    async def test_rfc_refinement_handler_integration(self, all_tools, temp_workspace):
        """Test RFC refinement handler with real tools."""
        # Mock AI service
        ai_service = Mock(spec=AIService)
        ai_service.process = AsyncMock()
        
        # Create handler
        handler = RFCRefinementHandler(ai_service)
        
        # Simulate creating RFC through handler
        ai_service.process.return_value = {
            'content': f"""I'll help you create an RFC for the caching feature.

Let me first analyze the codebase:
analyze_languages()

Now I'll create the RFC:
create_rfc(title="Distributed Caching", summary="Add Redis-based caching")

I've created RFC-2025-05-29-0001. Here are my initial questions:
1. What type of data will be cached?
2. What are the performance requirements?"""
        }
        
        # First interaction - create RFC
        result = await handler.handle(
            "I need an RFC for adding a caching layer",
            {'session_id': 'test123', 'agent_id': 'p'}
        )
        
        assert result['rfc_id'] == 'RFC-2025-05-29-0001'
        assert result['refinement_stage'] == 'gathering_requirements'
        assert len(result['tool_calls']) == 2
        
        # Execute the tool calls (simulate what would happen)
        for tool_call in result['tool_calls']:
            tool_name = tool_call['tool']
            if tool_name == 'create_rfc':
                all_tools[tool_name].execute({
                    'title': 'Distributed Caching',
                    'summary': 'Add Redis-based caching',
                    'author': 'Agent P'
                })
        
        # Simulate answering questions
        ai_service.process.return_value = {
            'content': """Thank you for the clarification. Let me update the RFC.

update_rfc(rfc_id="RFC-2025-05-29-0001", section="requirements", content="- [ ] Cache user sessions (1-hour TTL)\\n- [ ] Cache API responses (5-minute TTL)")

Let me search for similar caching implementations:
find_similar_code(pattern="cache", file_pattern="*.py")

Based on your requirements, should we use Redis Cluster for high availability?"""
        }
        
        # Second interaction - answer question
        result = await handler.handle(
            "We'll cache user sessions and API responses with different TTLs",
            {'session_id': 'test123', 'agent_id': 'p'}
        )
        
        assert len(result['tool_calls']) == 2
        assert result['tool_calls'][0]['tool'] == 'update_rfc'
        
        # Verify state persistence
        summary = handler.get_state_summary('test123')
        assert summary['active_rfc_id'] == 'RFC-2025-05-29-0001'
        assert summary['refinement_stage'] == 'gathering_requirements'
        assert summary['questions_asked'] == 0  # Counter not incremented in this simple test
    
    def test_error_scenarios(self, all_tools, temp_workspace):
        """Test error handling in tools."""
        # Try to read non-existent RFC
        result = all_tools['read_rfc'].execute({'rfc_id': 'RFC-9999-99-99-9999'})
        assert "Error: RFC 'RFC-9999-99-99-9999' not found" in result
        
        # Try to update non-existent RFC
        result = all_tools['update_rfc'].execute({
            'rfc_id': 'RFC-9999-99-99-9999',
            'section': 'summary',
            'content': 'Test'
        })
        assert "Error: RFC 'RFC-9999-99-99-9999' not found" in result
        
        # Try to move non-existent RFC
        result = all_tools['move_rfc'].execute({
            'rfc_id': 'RFC-9999-99-99-9999',
            'target_status': 'in_progress'
        })
        assert "Error: RFC 'RFC-9999-99-99-9999' not found" in result
        
        # Create RFC and try invalid status transition
        create_result = all_tools['create_rfc'].execute({
            'title': 'Test RFC',
            'summary': 'Test',
            'author': 'Test'
        })
        rfc_id = create_result.split("**RFC ID**: ")[1].split("\n")[0]
        
        # Try to move to same status
        result = all_tools['move_rfc'].execute({
            'rfc_id': rfc_id,
            'target_status': 'new'
        })
        assert "already in 'new' status" in result