from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_subprocess_run(mocker):
    """Mock subprocess.run for claude-code execution"""
    # Also mock shutil.which to return a valid path
    mocker.patch("shutil.which", return_value="/usr/local/bin/claude")
    
    mock = mocker.patch("subprocess.run")
    result_mock = MagicMock()
    result_mock.stdout = "Hello from claude-code!"
    result_mock.stderr = ""
    result_mock.returncode = 0
    mock.return_value = result_mock
    return mock


@pytest.fixture
def mock_claude_response():
    """Sample claude-code response"""
    return "This is a test response from claude-code"


@pytest.fixture
def sample_messages():
    """Sample OpenAI format messages"""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, Claude!"},
    ]


@pytest.fixture
def sample_openai_request():
    """Sample OpenAI API request"""
    return {
        "model": "claude-sonnet-4",
        "messages": [{"role": "user", "content": "Tell me a joke"}],
        "temperature": 0.7,
        "max_tokens": 100,
    }
