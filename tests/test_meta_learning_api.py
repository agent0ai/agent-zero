"""
Test Suite for Meta-Learning Dashboard API

Tests the meta-learning endpoints for listing analyses, managing suggestions,
and controlling prompt versions.

Run with: python -m pytest tests/test_meta_learning_api.py -v
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from python.api.meta_learning import MetaLearning
from python.helpers.memory import Memory
from langchain_core.documents import Document


class TestMetaLearningAPI:
    """Test suite for MetaLearning API handler"""

    @pytest.fixture
    def mock_request(self):
        """Create mock Flask request"""
        request = Mock()
        request.is_json = True
        request.get_json = Mock(return_value={})
        request.content_type = "application/json"
        return request

    @pytest.fixture
    def mock_app(self):
        """Create mock Flask app"""
        return Mock()

    @pytest.fixture
    def mock_lock(self):
        """Create mock thread lock"""
        import threading
        return threading.Lock()

    @pytest.fixture
    def api_handler(self, mock_app, mock_lock):
        """Create MetaLearning API handler instance"""
        return MetaLearning(mock_app, mock_lock)

    @pytest.mark.asyncio
    async def test_list_analyses_success(self, api_handler):
        """Test listing meta-analyses successfully"""
        # Mock memory with sample analysis document
        mock_doc = Document(
            page_content='{"prompt_refinements": [], "tool_suggestions": [], "meta": {}}',
            metadata={
                "id": "test_analysis_1",
                "area": "solutions",
                "timestamp": "2026-01-05T12:00:00",
                "meta_learning": True
            }
        )

        with patch('python.helpers.memory.Memory.get_by_subdir') as mock_get_memory:
            mock_memory = AsyncMock()
            mock_memory.db.get_all_docs.return_value = {
                "test_analysis_1": mock_doc
            }
            mock_get_memory.return_value = mock_memory

            result = await api_handler._list_analyses({
                "memory_subdir": "default",
                "limit": 10
            })

            assert result["success"] is True
            assert "analyses" in result
            assert result["total_count"] >= 0
            assert result["memory_subdir"] == "default"

    @pytest.mark.asyncio
    async def test_list_analyses_with_search(self, api_handler):
        """Test listing analyses with semantic search"""
        with patch('python.helpers.memory.Memory.get_by_subdir') as mock_get_memory:
            mock_memory = AsyncMock()
            mock_memory.search_similarity_threshold = AsyncMock(return_value=[])
            mock_get_memory.return_value = mock_memory

            result = await api_handler._list_analyses({
                "memory_subdir": "default",
                "search": "error handling",
                "limit": 5
            })

            assert result["success"] is True
            assert "analyses" in result

    @pytest.mark.asyncio
    async def test_get_analysis_success(self, api_handler):
        """Test getting specific analysis by ID"""
        mock_doc = Document(
            page_content='Test analysis content',
            metadata={
                "id": "test_id",
                "timestamp": "2026-01-05T12:00:00",
                "area": "solutions"
            }
        )

        with patch('python.helpers.memory.Memory.get_by_subdir') as mock_get_memory:
            mock_memory = Mock()
            mock_memory.get_document_by_id = Mock(return_value=mock_doc)
            mock_get_memory.return_value = mock_memory

            result = await api_handler._get_analysis({
                "analysis_id": "test_id",
                "memory_subdir": "default"
            })

            assert result["success"] is True
            assert result["analysis"]["id"] == "test_id"
            assert "content" in result["analysis"]

    @pytest.mark.asyncio
    async def test_get_analysis_not_found(self, api_handler):
        """Test getting non-existent analysis"""
        with patch('python.helpers.memory.Memory.get_by_subdir') as mock_get_memory:
            mock_memory = Mock()
            mock_memory.get_document_by_id = Mock(return_value=None)
            mock_get_memory.return_value = mock_memory

            result = await api_handler._get_analysis({
                "analysis_id": "nonexistent",
                "memory_subdir": "default"
            })

            assert result["success"] is False
            assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_get_analysis_missing_id(self, api_handler):
        """Test getting analysis without ID"""
        result = await api_handler._get_analysis({
            "memory_subdir": "default"
        })

        assert result["success"] is False
        assert "required" in result["error"]

    @pytest.mark.asyncio
    async def test_list_suggestions_success(self, api_handler):
        """Test listing suggestions from analyses"""
        # Mock analysis with suggestions
        mock_analysis = {
            "id": "test_analysis",
            "timestamp": "2026-01-05T12:00:00",
            "structured": {
                "prompt_refinements": [
                    {
                        "target_file": "agent.system.main.md",
                        "description": "Test refinement",
                        "confidence": 0.8,
                        "status": "pending"
                    }
                ],
                "tool_suggestions": []
            }
        }

        with patch.object(api_handler, '_list_analyses') as mock_list:
            mock_list.return_value = {
                "success": True,
                "analyses": [mock_analysis]
            }

            result = await api_handler._list_suggestions({
                "memory_subdir": "default",
                "status": "pending",
                "limit": 50
            })

            assert result["success"] is True
            assert "suggestions" in result
            assert len(result["suggestions"]) > 0
            assert result["suggestions"][0]["type"] == "prompt_refinement"

    @pytest.mark.asyncio
    async def test_list_suggestions_filter_by_status(self, api_handler):
        """Test filtering suggestions by status"""
        mock_analysis = {
            "id": "test",
            "timestamp": "2026-01-05T12:00:00",
            "structured": {
                "prompt_refinements": [
                    {
                        "target_file": "test.md",
                        "description": "Test",
                        "confidence": 0.8,
                        "status": "pending"
                    },
                    {
                        "target_file": "test2.md",
                        "description": "Test 2",
                        "confidence": 0.9,
                        "status": "applied"
                    }
                ]
            }
        }

        with patch.object(api_handler, '_list_analyses') as mock_list:
            mock_list.return_value = {
                "success": True,
                "analyses": [mock_analysis]
            }

            # Test pending filter
            result = await api_handler._list_suggestions({
                "status": "pending"
            })

            assert result["success"] is True
            assert all(s["status"] == "pending" for s in result["suggestions"])

    @pytest.mark.asyncio
    async def test_apply_suggestion_missing_approval(self, api_handler):
        """Test applying suggestion without approval"""
        result = await api_handler._apply_suggestion({
            "suggestion_id": "test_id",
            "analysis_id": "test_analysis",
            "approved": False
        })

        assert result["success"] is False
        assert "approval required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_apply_suggestion_missing_params(self, api_handler):
        """Test applying suggestion with missing parameters"""
        result = await api_handler._apply_suggestion({
            "approved": True
        })

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_trigger_analysis_success(self, api_handler):
        """Test triggering meta-analysis"""
        with patch.object(api_handler, 'use_context') as mock_context:
            mock_ctx = Mock()
            mock_ctx.id = "test_context"
            mock_ctx.agent0 = Mock()
            mock_context.return_value = mock_ctx

            with patch('python.tools.prompt_evolution.PromptEvolution') as mock_tool:
                mock_tool_instance = AsyncMock()
                mock_tool_instance.execute = AsyncMock(
                    return_value=Mock(message="Analysis complete")
                )
                mock_tool.return_value = mock_tool_instance

                result = await api_handler._trigger_analysis({
                    "background": False
                })

                assert result["success"] is True
                assert "context_id" in result

    @pytest.mark.asyncio
    async def test_trigger_analysis_background(self, api_handler):
        """Test triggering background meta-analysis"""
        with patch.object(api_handler, 'use_context') as mock_context:
            mock_ctx = Mock()
            mock_ctx.id = "test_context"
            mock_ctx.agent0 = Mock()
            mock_context.return_value = mock_ctx

            with patch('python.tools.prompt_evolution.PromptEvolution') as mock_tool:
                with patch('asyncio.create_task') as mock_create_task:
                    result = await api_handler._trigger_analysis({
                        "background": True
                    })

                    assert result["success"] is True
                    assert "background" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_list_versions_success(self, api_handler):
        """Test listing prompt versions"""
        mock_versions = [
            {
                "version_id": "20260105_120000",
                "timestamp": "2026-01-05T12:00:00",
                "label": None,
                "file_count": 95,
                "changes": [],
                "created_by": "meta_learning"
            }
        ]

        with patch('python.helpers.prompt_versioning.PromptVersionManager') as mock_manager:
            mock_instance = Mock()
            mock_instance.list_versions = Mock(return_value=mock_versions)
            mock_manager.return_value = mock_instance

            result = await api_handler._list_versions({
                "limit": 20
            })

            assert result["success"] is True
            assert "versions" in result
            assert len(result["versions"]) > 0

    @pytest.mark.asyncio
    async def test_rollback_version_success(self, api_handler):
        """Test rolling back to previous version"""
        with patch('python.helpers.prompt_versioning.PromptVersionManager') as mock_manager:
            mock_instance = Mock()
            mock_instance.rollback = Mock(return_value=True)
            mock_manager.return_value = mock_instance

            result = await api_handler._rollback_version({
                "version_id": "20260105_120000",
                "create_backup": True
            })

            assert result["success"] is True
            assert "version_id" in result

    @pytest.mark.asyncio
    async def test_rollback_version_missing_id(self, api_handler):
        """Test rollback without version ID"""
        result = await api_handler._rollback_version({
            "create_backup": True
        })

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_process_routing(self, api_handler, mock_request):
        """Test that process() routes to correct handlers"""
        test_cases = [
            ("list_analyses", "_list_analyses"),
            ("get_analysis", "_get_analysis"),
            ("list_suggestions", "_list_suggestions"),
            ("apply_suggestion", "_apply_suggestion"),
            ("trigger_analysis", "_trigger_analysis"),
            ("list_versions", "_list_versions"),
            ("rollback_version", "_rollback_version"),
        ]

        for action, method_name in test_cases:
            with patch.object(api_handler, method_name) as mock_method:
                mock_method.return_value = {"success": True}

                result = await api_handler.process(
                    {"action": action},
                    mock_request
                )

                mock_method.assert_called_once()
                assert result["success"] is True

    @pytest.mark.asyncio
    async def test_process_unknown_action(self, api_handler, mock_request):
        """Test handling of unknown action"""
        result = await api_handler.process(
            {"action": "unknown_action"},
            mock_request
        )

        assert result["success"] is False
        assert "unknown action" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_is_meta_analysis(self, api_handler):
        """Test meta-analysis detection"""
        # Document with meta-learning keywords
        doc1 = Document(
            page_content="This is a meta-analysis of prompt refinements",
            metadata={"area": "solutions"}
        )
        assert api_handler._is_meta_analysis(doc1) is True

        # Document with meta tags
        doc2 = Document(
            page_content="Regular content",
            metadata={"meta_learning": True}
        )
        assert api_handler._is_meta_analysis(doc2) is True

        # Regular document
        doc3 = Document(
            page_content="Regular solution content",
            metadata={"area": "solutions"}
        )
        assert api_handler._is_meta_analysis(doc3) is False

    def test_parse_analysis_content(self, api_handler):
        """Test parsing structured data from analysis content"""
        # JSON content
        json_content = '{"prompt_refinements": [], "tool_suggestions": []}'
        result = api_handler._parse_analysis_content(json_content)
        assert result is not None
        assert "prompt_refinements" in result

        # JSON in markdown code block
        markdown_content = '''
        Some text
        ```json
        {"prompt_refinements": []}
        ```
        More text
        '''
        result = api_handler._parse_analysis_content(markdown_content)
        assert result is not None

        # Invalid content
        result = api_handler._parse_analysis_content("Not JSON at all")
        assert result is None

    def test_get_methods(self, api_handler):
        """Test HTTP methods configuration"""
        methods = MetaLearning.get_methods()
        assert "GET" in methods
        assert "POST" in methods


class TestMetaLearningIntegration:
    """Integration tests (require actual components)"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_end_to_end_analysis_flow(self):
        """
        Test complete flow: trigger analysis -> list analyses -> get suggestions -> list versions

        Note: Requires actual memory and versioning systems
        """
        # This would be an integration test requiring actual setup
        # Skipped in unit tests
        pytest.skip("Integration test - requires full setup")


# Test helper functions
def create_mock_analysis_doc(analysis_id: str, with_suggestions: bool = True):
    """Helper to create mock analysis document"""
    content = {
        "meta": {
            "timestamp": "2026-01-05T12:00:00",
            "monologue_count": 5
        }
    }

    if with_suggestions:
        content["prompt_refinements"] = [
            {
                "target_file": "agent.system.main.md",
                "description": "Test refinement",
                "confidence": 0.8,
                "status": "pending"
            }
        ]
        content["tool_suggestions"] = []

    import json
    return Document(
        page_content=json.dumps(content),
        metadata={
            "id": analysis_id,
            "area": "solutions",
            "timestamp": "2026-01-05T12:00:00",
            "meta_learning": True
        }
    )


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
