import json
from unittest.mock import patch, MagicMock
import pytest
from promptwatch.models import TestCase
from promptwatch.adapters import OpenAIAdapter, OpenRouterAdapter, GroqAdapter, HttpAdapter, get_adapter

@patch("urllib.request.urlopen")
def test_openai_adapter(mock_urlopen):
    # Mock response
    mock_res = MagicMock()
    mock_res.read.return_value = json.dumps({
        "choices": [{
            "message": {
                "content": "OpenAI Response content"
            }
        }]
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_res

    adapter = OpenAIAdapter(api_key="test-key")
    case = TestCase(id="c1", input="Hello")
    res = adapter.generate(case)
    
    assert res.output == "OpenAI Response content"
    mock_urlopen.assert_called_once()


@patch("urllib.request.urlopen")
def test_openrouter_adapter(mock_urlopen):
    mock_res = MagicMock()
    mock_res.read.return_value = json.dumps({
        "choices": [{
            "message": {
                "content": "OpenRouter Response content"
            }
        }]
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_res

    adapter = OpenRouterAdapter(api_key="test-key")
    case = TestCase(id="c2", input="Hello")
    res = adapter.generate(case)
    
    assert res.output == "OpenRouter Response content"


@patch("urllib.request.urlopen")
def test_groq_adapter(mock_urlopen):
    mock_res = MagicMock()
    mock_res.read.return_value = json.dumps({
        "choices": [{
            "message": {
                "content": "Groq Response content"
            }
        }]
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_res

    adapter = GroqAdapter(api_key="test-key")
    case = TestCase(id="c3", input="Hello")
    res = adapter.generate(case)
    
    assert res.output == "Groq Response content"


@patch("urllib.request.urlopen")
def test_http_adapter(mock_urlopen):
    mock_res = MagicMock()
    mock_res.read.return_value = json.dumps({
        "output": "HTTP Response content",
        "citations": ["doc1"],
        "metadata": {"time": 123}
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_res

    adapter = HttpAdapter(url="http://test.com/api", json_path="output")
    case = TestCase(id="c4", input="Hello")
    res = adapter.generate(case)
    
    assert res.output == "HTTP Response content"
    assert res.citations == ["doc1"]
    assert res.metadata == {"time": 123}


def test_get_adapter():
    with patch.dict("os.environ", {"OPENAI_API_KEY": "dummy"}):
        adapter = get_adapter("openai")
        assert isinstance(adapter, OpenAIAdapter)
        assert adapter.model == "gpt-4o-mini"
        
    with patch.dict("os.environ", {"GROQ_API_KEY": "dummy"}):
        adapter = get_adapter("groq")
        assert isinstance(adapter, GroqAdapter)
        assert adapter.model == "llama-3.3-70b-versatile"
